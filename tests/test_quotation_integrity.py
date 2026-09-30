"""Local pure-core tests: no databases, network, or orchestrator imports."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / 'src/models/quotation_verifier.py'
spec = importlib.util.spec_from_file_location('quotation_integrity_core', MODULE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
QuotationVerifier = core.QuotationVerifier


def pinned(quote, source, **kwargs):
    data = source.encode('utf-8') if isinstance(source, str) else source
    defaults = dict(expected_sha256=hashlib.sha256(data).hexdigest(),
                    source_ref='local:fixture', source_version='v1')
    defaults.update(kwargs)
    return QuotationVerifier().verify_source_quote(quote, data, **defaults)


def test_pinned_exact_excerpt_uses_full_unicode_source_without_text_leaks():
    quote = '道可道 — café e\u0301 😀 42.'
    prefix = 'background material ' * 1500
    source = prefix + quote + '\n終'
    receipt = pinned(quote, source)
    assert receipt['status'] == 'exact_source_match'
    assert receipt['source_ref'] == 'local:fixture'
    assert receipt['source_version'] == 'v1'
    assert receipt['source_sha256'] == hashlib.sha256(source.encode()).hexdigest()
    assert receipt['quote_sha256'] == hashlib.sha256(quote.encode()).hexdigest()
    assert receipt['normalization'] == 'none'
    assert receipt['source_spans'] == [{'start': len(prefix), 'end': len(prefix) + len(quote)}]
    assert receipt['offset_unit'] == 'unicode_codepoint'
    assert receipt['verifier_version'] == 'quotation-verifier/0.2'
    assert receipt['semantic_support'] == receipt['source_truth'] == 'not_assessed'
    assert receipt['deployment_authorized'] is False
    assert receipt['requires_human_review'] is True
    assert receipt['coverage']['source_bytes_hashed'] == len(source.encode())
    assert receipt['coverage']['source_chars_decoded'] == len(source)
    assert receipt['coverage']['scope'] == 'full_source'
    serialized = json.dumps(receipt, ensure_ascii=False, allow_nan=False)
    assert quote not in serialized and source not in serialized


@pytest.mark.parametrize('digest', ['0' * 64, 'A' * 64, 'a' * 63, 'a' * 65,
                                    ' ' + 'a' * 64, None, 123, b'a' * 64])
def test_digest_pin_is_exact_lowercase_hex_and_matches_all_bytes(digest):
    with pytest.raises(ValueError) as exc:
        pinned('safe', b'safe\nSECRET-TAMPERED-TAIL', expected_sha256=digest)
    assert len(str(exc.value)) <= 120
    assert 'SECRET' not in str(exc.value)
    original = b'safe'
    with pytest.raises(ValueError):
        pinned('safe', original + b'!', expected_sha256=hashlib.sha256(original).hexdigest())


def test_source_and_quote_bounds_types_and_strict_utf8_reject_without_echo():
    verifier = QuotationVerifier()
    base = dict(quoted_claim='good', source_bytes=b'good',
                expected_sha256=hashlib.sha256(b'good').hexdigest(),
                source_ref='local:fixture', source_version='v1')
    for field, invalid in [
        ('quoted_claim', None), ('quoted_claim', b'good'), ('quoted_claim', True),
        ('quoted_claim', 'SECRET' + '\ud800'), ('quoted_claim', 'x' * 20_001),
        ('source_bytes', 'good'), ('source_bytes', None),
        ('source_bytes', bytearray(b'good')), ('source_bytes', memoryview(b'good')),
        ('source_bytes', b'x' * 2_000_001), ('source_bytes', b'SECRET\xff'),
        ('source_bytes', b'\xed\xa0\x80'),
    ]:
        args = dict(base, **{field: invalid})
        if type(invalid) is bytes:
            args['expected_sha256'] = hashlib.sha256(invalid).hexdigest()
        with pytest.raises(ValueError) as exc:
            verifier.verify_source_quote(**args)
        assert type(exc.value) is ValueError
        assert len(str(exc.value)) <= 120 and 'SECRET' not in str(exc.value)
    assert core.MAX_SOURCE_BYTES == 2_000_000
    assert core.MAX_QUOTE_CHARS == 20_000
    assert pinned('x' * 20_000, 'x' * 20_000)['status'] == 'exact_source_match'
    assert pinned('END', b'x' * 1_999_997 + b'END')['source_spans'] == [
        {'start': 1_999_997, 'end': 2_000_000}]


def test_metadata_and_normalization_are_validated_without_identifier_repair():
    for field in ('source_ref', 'source_version'):
        for value in ('', '  ', '\u00a0', 'SECRET\nvalue', '\x7f', '\u0085',
                      'bidirectional\u202e', '\udfff', 'x' * 513, None, 4, [], b'id'):
            with pytest.raises(ValueError) as exc:
                pinned('good', b'good', **{field: value})
            assert type(exc.value) is ValueError
            assert len(str(exc.value)) <= 120 and 'SECRET' not in str(exc.value)
    for mode in ('NFKC', 'NONE', ' none', '', None, True, [], {}):
        with pytest.raises(ValueError):
            pinned('good', b'good', normalization=mode)
    ref, version = ' Local:é/../Untrusted ', ' V1 '
    receipt = pinned('good', b'good', source_ref=ref, source_version=version)
    assert receipt['source_ref'] == ref and receipt['source_version'] == version
    assert pinned('good', b'good', source_ref='r' * 512)['source_ref'] == 'r' * 512


def test_selected_span_compares_whole_selection_using_codepoint_offsets():
    source = '😀 bad good good'
    first = source.index('good')
    receipt = pinned('good', source, source_span=[0, len(source)])
    assert receipt['status'] not in {'exact_source_match', 'normalized_source_match'}
    assert receipt['source_spans'] == []
    receipt = pinned('good', source, source_span=[first, first + 4])
    assert receipt['status'] == 'exact_source_match'
    assert receipt['source_spans'] == [{'start': first, 'end': first + 4}]
    assert receipt['coverage']['scope'] == 'selected_span'
    assert pinned('good', source, source_span=(first + 5, first + 9))['source_spans'] == [
        {'start': first + 5, 'end': first + 9}]
    for bad_span in ([True, 4], [0, False], [0., 4], [-1, 4], [4, 3], [0, 100],
                     [1], [0, 1, 2], '0:4', {'start': 0, 'end': 4}):
        with pytest.raises(ValueError) as exc:
            pinned('good', source, source_span=bad_span)
        assert len(str(exc.value)) <= 120


@pytest.mark.parametrize('quote,source,span', [('', '', None), ('', 'x', None),
                                             ('x', '', None), ('x', 'abc', [1, 1])])
def test_empty_input_abstains_instead_of_certifying_empty_substrings(quote, source, span):
    receipt = pinned(quote, source, source_span=span)
    assert receipt['status'] == 'insufficient_data'
    assert receipt['source_spans'] == []
    assert receipt['coverage']['reason'] == 'empty_input'
    assert receipt['coverage']['exact_search'] == 'not_run'


def test_explicit_ascii_whitespace_normalization_has_replayable_raw_spans():
    import re
    collapse = lambda text: re.sub(r'[ \t\r\n]+', ' ', text)
    quote = '道 e\u0301\tZ'
    source = '😀前:道\r\n  e\u0301 \tZ:後'
    assert pinned(quote, source)['status'] != 'exact_source_match'
    receipt = pinned(quote, source, normalization='ascii_whitespace')
    assert receipt['status'] == 'normalized_source_match'
    span = receipt['source_spans'][0]
    assert span == {'start': source.index('道'), 'end': source.index(':後')}
    assert collapse(source[span['start']:span['end']]) == collapse(quote)
    assert receipt['coverage']['normalization_search'] == 'first_match'
    assert receipt['coverage']['normalization_policy'] == 'ascii_whitespace_runs_to_space_no_trim'
    assert receipt['quote_sha256'] == hashlib.sha256(quote.encode()).hexdigest()
    selected = pinned(quote, source, normalization='ascii_whitespace',
                      source_span=[span['start'], span['end']])
    assert selected['status'] == 'normalized_source_match'
    assert selected['source_spans'] == [span]
    for a, b in [('é', 'e\u0301'), ('Ａ', 'A'), ('Hello', 'hello'), ('x y', 'x\u00a0y'),
                 ('x y', 'x\vy'), ('x y', 'x\fy'), ('x y', 'x\u2003y'), ('42.', '42!')]:
        assert pinned(a, b, normalization='ascii_whitespace')['status'] not in {
            'exact_source_match', 'normalized_source_match'}
    assert pinned('x  y', ' x\ty ', normalization='ascii_whitespace', source_span=[0, 5])[
        'status'] not in {'exact_source_match', 'normalized_source_match'}


def test_approximate_character_edits_are_candidates_never_verified():
    source = 'The valve is open at 42 psi.'
    for quote in ('The valve is not open at 42 psi.', 'The valve is open at 43 psi.',
                  'The valve is open at 42 psi!', 'the valve is open at 42 psi.'):
        receipt = pinned(quote, source)
        assert receipt['status'] == 'approximate_candidate'
        assert receipt['source_spans'] == []
        assert receipt['candidate_spans'] == [{'start': 0, 'end': len(source)}]
        assert 0 <= receipt['candidate_similarity'] < 1
        assert receipt['semantic_support'] == receipt['source_truth'] == 'not_assessed'
        assert receipt['coverage']['approximate_search'] == 'complete_selected_span'
        assert receipt['coverage']['exact_search'] == 'complete_no_match'
        encoded = json.dumps(receipt, ensure_ascii=False, allow_nan=False)
        assert 'VERIFIED' not in encoded and quote not in encoded and source not in encoded
    assert pinned('甲乙丙', 'abc')['status'] == 'not_found'


def test_approximation_budget_abstains_without_prefix_matching_or_hidden_coverage():
    quote, source = 'x' * 500 + 'a', 'x' * 500 + 'b'
    receipt = pinned(quote, source)
    assert receipt['status'] == 'insufficient_data'
    assert receipt['source_spans'] == []
    assert receipt.get('candidate_similarity') is None
    coverage = receipt['coverage']
    assert coverage['reason'] == 'approximate_budget_exceeded'
    assert coverage['exact_search'] == 'complete_no_match'
    assert coverage['approximate_search'] == 'skipped_budget'
    assert coverage['complete'] is False and coverage['truncated'] is False
    assert coverage['limits']['max_approximate_cells'] == core.MAX_APPROXIMATE_CELLS
    assert coverage['limits']['max_source_bytes'] == core.MAX_SOURCE_BYTES
    assert coverage['limits']['max_quote_chars'] == core.MAX_QUOTE_CHARS
    assert coverage['approximate_cells_required'] == len(quote) * len(source)
    long_source = 'word ' * 400 + 'final.'
    changed = 'word ' * 400 + 'final!'
    assert pinned(changed, long_source)['status'] == 'insufficient_data'
    assert pinned('final.', long_source)['status'] == 'exact_source_match'
    assert pinned('absent', 'x' * 2_000_000)['coverage']['exact_search'] == 'complete_no_match'
    at_limit = pinned('a' * 499 + 'b', 'a' * 500)
    assert at_limit['status'] == 'approximate_candidate'
    assert at_limit['coverage']['complete'] is True


def test_legacy_tokenization_preserves_unicode_case_marks_and_punctuation():
    verifier = QuotationVerifier()
    assert verifier.tokenize_words('道可道 café e\u0301 😀 42. NOT foo_bar') == [
        '道可道', 'café', 'e\u0301', '😀', '42', '.', 'NOT', 'foo_bar']
    assert verifier.tokenize_words('é') != verifier.tokenize_words('e\u0301')
    for invalid in (None, 4, b'text', '\ud800', 'x' * 2_000_001, '😀' * 500_001):
        with pytest.raises(ValueError) as exc:
            verifier.tokenize_words(invalid)
        assert type(exc.value) is ValueError and len(str(exc.value)) <= 120


def test_token_alignment_never_silently_truncates_suffixes_or_exceeds_budget():
    verifier = QuotationVerifier()
    source = ['word'] * 300 + ['allow']
    changed = ['word'] * 300 + ['deny']
    exact_raw, exact_similarity = verifier.needleman_wunsch(source, source)
    changed_raw, changed_similarity = verifier.needleman_wunsch(changed, source)
    assert changed_raw < exact_raw and changed_similarity < exact_similarity
    for left, right in [(['a'] * 501, ['a'] * 501), (['a'] * 1001, []),
                        ([], ['a'] * 1001)]:
        with pytest.raises(ValueError, match='budget'):
            verifier.needleman_wunsch(left, right)
    for invalid in (None, 'word', {'word'}, [None], [True], ['\ud800'], [''], ['x' * 20_001]):
        with pytest.raises(ValueError) as exc:
            verifier.needleman_wunsch(invalid, ['valid'])
        assert len(str(exc.value)) <= 120
    assert verifier.needleman_wunsch([], ['valid']) == (0, 0.0)
    assert core.MAX_ALIGNMENT_TOKENS == 1000
    assert core.MAX_ALIGNMENT_CELLS == 250_000


def test_alignment_scoring_rejects_nonfinite_unsafe_and_nonnumeric_parameters():
    import math
    for field in ('match_score', 'mismatch_penalty', 'gap_penalty'):
        for invalid in (float('nan'), float('inf'), -float('inf'), True, None, '2',
                        10 ** 1000, -10 ** 1000, 1_000_001):
            with pytest.raises(ValueError) as exc:
                QuotationVerifier(**{field: invalid})
            assert type(exc.value) is ValueError and len(str(exc.value)) <= 120
    for kwargs in ({'match_score': 0}, {'match_score': -1},
                   {'gap_penalty': 0}, {'gap_penalty': 1}, {'mismatch_penalty': 1}):
        with pytest.raises(ValueError):
            QuotationVerifier(**kwargs)
    verifier = QuotationVerifier(0.5, -2.0, -0.25)
    score, similarity = verifier.needleman_wunsch(['a', 'b'], ['a', 'c'])
    assert math.isfinite(score) and 0 <= similarity <= 1
    tiny = QuotationVerifier(5e-324, -5e-324, -5e-324)
    assert tiny.needleman_wunsch(['x'], ['x'])[1] == 1.0
    verifier.match = float('nan')
    with pytest.raises(ValueError):
        verifier.needleman_wunsch(['a'], ['b'])


def test_legacy_fidelity_reports_lexical_receipts_not_semantic_certainty():
    verifier = QuotationVerifier()
    source = 'The valve is open at 42 psi.'
    for quote in ('The valve is not open at 42 psi.', 'The valve is open at 43 psi.',
                  'The valve is open at 42 psi!', 'the valve is open at 42 psi.'):
        result = verifier.verify_quotation_fidelity(quote, source)
        assert result['is_faithful'] is None
        assert result['is_literal_match'] is False
        assert result['status'] == 'approximate_candidate'
        assert not any(word in result['verdict'].lower() for word in (
            'verified', 'verbatim', 'paraphrase', 'tampered', 'hallucinated'))
        assert result['semantic_support'] == result['source_truth'] == 'not_assessed'
        assert result['source_pin_provenance'] == 'computed_from_supplied_text_not_independently_pinned'
        assert result['deployment_authorized'] is False and result['requires_human_review'] is True
    literal = verifier.verify_quotation_fidelity('道 e\u0301!', 'prefix ' * 400 + '道 e\u0301!')
    assert literal['is_literal_match'] is True and literal['status'] == 'exact_source_match'
    assert literal['is_faithful'] is None
    assert verifier.verify_quotation_fidelity('', '')['status'] == 'insufficient_data'
    long_result = verifier.verify_quotation_fidelity('word ' * 400 + '!', 'word ' * 400 + '.')
    assert long_result['status'] == 'insufficient_data'
    assert long_result['quotation_fidelity_score'] is None
    for a, b in [(None, 'ok'), ('ok', b'ok'), ('\ud800', 'ok'), ('ok', '\udfff')]:
        with pytest.raises(ValueError):
            verifier.verify_quotation_fidelity(a, b)


@pytest.mark.parametrize('suspect,carrier,operation,count', [
    ('red green red green blue', 'red green blue', 'insert', 2),
    ('red blue', 'red green blue', 'delete', 1),
    ('red yellow blue', 'red green blue', 'replace', 1),
    ('道 e\u0301 😀!', '道 e\u0301 😀.', 'replace', 1),
    ('word ' * 300 + 'allow', 'word ' * 300 + 'deny', 'replace', 1),
])
def test_interpolation_uses_bounded_traceback_for_edit_candidates(suspect, carrier, operation, count):
    verifier = QuotationVerifier()
    result = verifier.detect_interpolated_carrier(suspect, carrier)
    assert result['status'] == 'edit_candidates'
    assert result['has_edit_candidates'] is True
    assert result['has_foreign_interpolation'] is None
    assert result['interpolation_risk'] is None
    assert result['flagged_payload_spans'] == []
    assert result['payload_assessment'] == 'not_assessed'
    assert result['semantic_support'] == result['source_truth'] == 'not_assessed'
    assert result['deployment_authorized'] is False and result['requires_human_review'] is True
    assert result['coverage']['complete'] is True
    assert result['coverage']['truncated'] is False
    assert result['coverage']['whitespace_assessed'] is False
    edits = result['edit_candidates']
    assert {edit['operation'] for edit in edits} == {operation}
    dimension = ('carrier_start_token', 'carrier_end_token') if operation == 'delete' else ('start_token', 'end_token')
    assert sum(edit[dimension[1]] - edit[dimension[0]] for edit in edits) == count
    for edit in edits:
        assert 0 <= edit['suspect_span']['start'] <= edit['suspect_span']['end'] <= len(suspect)
        assert 0 <= edit['carrier_span']['start'] <= edit['carrier_span']['end'] <= len(carrier)
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
    assert 'text_snippet' not in encoded and suspect not in encoded and carrier not in encoded


def test_interpolation_abstains_for_empty_or_overbudget_input():
    verifier = QuotationVerifier()
    for a, b, reason in [('', '', 'empty_tokens'), ('', 'word', 'empty_tokens'),
                          ('word', '\t ', 'empty_tokens'),
                          ('a ' * 501, 'a ' * 501, 'alignment_budget_exceeded'),
                          ('a ' * 1001, 'a', 'alignment_budget_exceeded')]:
        result = verifier.detect_interpolated_carrier(a, b)
        assert result['status'] == 'insufficient_data'
        assert result['global_carrier_similarity'] is None
        assert result['has_edit_candidates'] is None
        assert result['has_foreign_interpolation'] is None
        assert result['edit_candidates'] == result['flagged_payload_spans'] == []
        assert result['coverage']['complete'] is False
        assert result['coverage']['truncated'] is False
        assert result['coverage']['reason'] == reason
    equal = verifier.detect_interpolated_carrier('a b', 'a\tb')
    assert equal['status'] == 'no_edit_candidates'
    assert equal['has_foreign_interpolation'] is None
    assert equal['coverage']['whitespace_assessed'] is False
    for a, b in [(None, 'word'), ('word', b'word'), ('\udfff', 'word')]:
        with pytest.raises(ValueError):
            verifier.detect_interpolated_carrier(a, b)


def test_untrusted_strings_get_explicit_full_quote_coverage_without_execution(tmp_path):
    sentinel = tmp_path / 'must-not-exist'
    quote = '__import__("pathlib").Path(' + repr(str(sentinel)) + ').write_text("EXECUTED")'
    receipt = pinned(quote, 'header\n' + quote + '\nfooter')
    assert not sentinel.exists()
    assert receipt['coverage']['quote_fully_matched'] is True
    assert receipt['coverage']['quote_chars'] == len(quote)
    assert receipt['status'] == 'exact_source_match'
    normalized = pinned(quote.replace('.Path', '.\tPath'), quote.replace('.Path', '.  Path'),
                        normalization='ascii_whitespace')
    assert normalized['coverage']['quote_fully_matched'] is True
    changed = pinned(quote + '!', quote)
    assert changed['coverage']['quote_fully_matched'] is False
    empty = pinned('', quote)
    assert empty['coverage']['quote_fully_matched'] is False
    QuotationVerifier().verify_quotation_fidelity(quote, quote)
    QuotationVerifier().detect_interpolated_carrier('SAFE ' + quote, 'SAFE')
    assert not sentinel.exists()
    assert quote not in json.dumps(receipt, ensure_ascii=False)
    # The pure core must not gain an I/O or orchestration dependency.
    import ast
    tree = ast.parse(MODULE.read_text(encoding='utf-8'))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= {'hashlib', 'math', 're', 'unicodedata', 'typing'}
    dangerous = {'eval', 'exec', 'compile', '__import__', 'open'}
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in dangerous for node in ast.walk(tree))


def test_fractional_alignment_scores_keep_traceback_inside_matrix_boundaries():
    verifier = QuotationVerifier(gap_penalty=-0.1)
    for suspect, carrier, expected in [('red ' * 6 + 'blue', 'blue', 'insert'),
                                       ('blue', 'red ' * 6 + 'blue', 'delete')]:
        result = verifier.detect_interpolated_carrier(suspect, carrier)
        assert result['status'] == 'edit_candidates'
        assert len(result['edit_candidates']) == 6
        for candidate in result['edit_candidates']:
            assert candidate['operation'] == expected
            assert candidate['start_token'] >= 0 and candidate['carrier_start_token'] >= 0
            assert candidate['suspect_span']['start'] >= 0 and candidate['carrier_span']['start'] >= 0
