"""Pure, bounded quotation-integrity receipts and lexical edit candidates.

Only literal equality (or explicitly requested ASCII-whitespace collapse) can
produce a source-match state. Scores never establish semantic support, source
truth, source authority, malicious intent, or permission to deploy. This module
does not fetch sources, execute quoted text, decode payloads, or perform I/O.
"""

import hashlib
import math
import re
import unicodedata
from typing import List, Dict, Any, Tuple

MAX_SOURCE_BYTES = 2_000_000
MAX_QUOTE_CHARS = 20_000
MAX_APPROXIMATE_CELLS = 250_000
MAX_ALIGNMENT_TOKENS = 1000
MAX_ALIGNMENT_CELLS = 250_000
_ASCII_WS = re.compile(r'[ \t\r\n]+')


class _AlignmentBudgetExceeded(ValueError):
    """A bounded comparison was not performed, rather than prefix-truncated."""


def _validate_scores(match, mismatch, gap):
    for value in (match, mismatch, gap):
        if (type(value) not in (int, float) or not -1_000_000 <= value <= 1_000_000
                or not math.isfinite(value)):
            raise ValueError('alignment scores must be finite bounded numbers')
    if match <= 0 or mismatch > 0 or gap >= 0:
        raise ValueError('require positive match, nonpositive mismatch, negative gap')


def _validate_sequences(seq1, seq2):
    for sequence in (seq1, seq2):
        if type(sequence) not in (list, tuple):
            raise ValueError('alignment requires token lists or tuples')
        if len(sequence) > MAX_ALIGNMENT_TOKENS:
            raise _AlignmentBudgetExceeded('alignment token budget exceeded')
        size = 0
        for token in sequence:
            size += len(_text_bytes(token, MAX_QUOTE_CHARS, 'token'))
            if not token:
                raise ValueError('alignment tokens must be nonempty')
            if size > MAX_SOURCE_BYTES:
                raise _AlignmentBudgetExceeded('alignment text budget exceeded')
    if len(seq1) * len(seq2) > MAX_ALIGNMENT_CELLS:
        raise _AlignmentBudgetExceeded('alignment cell budget exceeded')


def _character_similarity(left, right):
    """Global Levenshtein similarity; lexical only, never a truth judgment."""
    if len(right) > len(left):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[-1] + 1,
                               previous[j - 1] + (a != b)))
        previous = current
    return 1.0 - previous[-1] / max(len(left), len(right))


def _raw_normalized_span(text, start, end):
    """Map a nonempty collapsed span back without storing a per-character map."""
    position, raw_start = 0, None
    for run in re.finditer(r'[ \t\r\n]+|[^ \t\r\n]+', text):
        whitespace = text[run.start()] in ' \t\r\n'
        width = 1 if whitespace else run.end() - run.start()
        if raw_start is None and position <= start < position + width:
            raw_start = run.start() if whitespace else run.start() + start - position
        if position < end <= position + width:
            raw_end = run.end() if whitespace else run.start() + end - position
            return raw_start, raw_end
        position += width
    raise ValueError('invalid normalized span')


def _text_bytes(text, max_chars, label):
    if type(text) is not str or len(text) > max_chars:
        raise ValueError(label + ' must be a bounded string')
    try:
        return text.encode('utf-8', errors='strict')
    except UnicodeError:
        raise ValueError(label + ' must contain valid Unicode') from None


def _token_spans(text):
    """Unicode words (including combining marks), plus each punctuation/symbol."""
    spans, start = [], None
    for i, char in enumerate(text):
        word = char.isalnum() or char == '_' or unicodedata.category(char).startswith('M')
        if word:
            if start is None:
                start = i
        else:
            if start is not None:
                spans.append((start, i))
                start = None
            if not char.isspace():
                spans.append((i, i + 1))
    if start is not None:
        spans.append((start, len(text)))
    return spans


class QuotationVerifier:
    """Report-only comparisons with explicit input and computation bounds."""

    def verify_source_quote(self, quoted_claim: str, source_bytes: bytes, *,
                            expected_sha256: str, source_ref: str, source_version: str,
                            normalization='none', source_span=None) -> Dict[str, Any]:
        """Return a JSON-compatible receipt for caller-pinned, strict UTF-8 bytes.

        ``expected_sha256`` is exact lowercase 64-hex, never repaired. Strings
        and bytes must be exact built-in types; malformed/beyond-limit inputs
        raise a bounded ValueError without echoing their contents. References
        and versions are unmodified, nonblank strings of at most 512 codepoints
        without control/format characters or line/paragraph separators.

        Without ``source_span``, return the first literal occurrence anywhere
        in the full decoded source. With a list/tuple of [start, end) integer
        codepoint bounds (not booleans), compare the entire selected span.
        ``ascii_whitespace`` additionally collapses only space/tab/CR/LF runs
        to one ASCII space, without trimming. Matched raw offsets plus the
        declared policy make that transformation replayable against the pin.

        States: exact_source_match, normalized_source_match,
        approximate_candidate, not_found, insufficient_data. After no match,
        global raw-character Levenshtein similarity >= 0.8 suggests only a
        candidate for the entire selected scope, not a fuzzy substring match.
        Beyond MAX_APPROXIMATE_CELLS, abstain; no prefix is substituted.
        Empty quote/source/selection also abstains. ``coverage.complete`` means
        completion of these declared strategies, not exhaustive fuzzy search.

        ``source_spans`` contains only precise, full-quote matches; approximate
        offsets use ``candidate_spans`` instead. No quote/source/edit text is
        returned. Caller-supplied metadata identifies a pin, not source trust.
        All receipts require human review and authorize no deployment.
        """
        quote_bytes = _text_bytes(quoted_claim, MAX_QUOTE_CHARS, 'quoted_claim')
        if type(source_bytes) is not bytes or len(source_bytes) > MAX_SOURCE_BYTES:
            raise ValueError('source_bytes must be bounded bytes')
        for label, value in (('source_ref', source_ref), ('source_version', source_version)):
            _text_bytes(value, 512, label)
            if not value.strip() or any(unicodedata.category(c) in ('Cc', 'Cf', 'Zl', 'Zp') for c in value):
                raise ValueError(label + ' must be nonblank without controls')
        if type(normalization) is not str or normalization not in ('none', 'ascii_whitespace'):
            raise ValueError('unsupported normalization')
        if (type(expected_sha256) is not str or
                re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None):
            raise ValueError('expected_sha256 must be lowercase SHA-256 hex')
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        if source_digest != expected_sha256:
            raise ValueError('source digest mismatch')
        try:
            source = source_bytes.decode('utf-8', errors='strict')
        except UnicodeError:
            raise ValueError('source_bytes must be strict UTF-8') from None
        if source_span is not None:
            if (type(source_span) not in (list, tuple) or len(source_span) != 2 or
                    any(type(x) is not int for x in source_span) or
                    not 0 <= source_span[0] <= source_span[1] <= len(source)):
                raise ValueError('source_span must be valid codepoint bounds')
            lower, upper = source_span
            selected = source[lower:upper]
            start = lower if selected == quoted_claim else -1
        else:
            lower, upper = 0, len(source)
            selected = source
            start = source.find(quoted_claim)
        empty = not quoted_claim or not selected
        if empty:
            start = -1
        receipt = {
            'status': 'insufficient_data' if empty else ('exact_source_match' if start >= 0 else 'not_found'),
            'source_ref': source_ref, 'source_version': source_version,
            'source_sha256': source_digest,
            'quote_sha256': hashlib.sha256(quote_bytes).hexdigest(),
            'normalization': normalization,
            'source_spans': [{'start': start, 'end': start + len(quoted_claim)}] if start >= 0 else [],
            'offset_unit': 'unicode_codepoint', 'verifier_version': 'quotation-verifier/0.2',
            'coverage': {'source_bytes_hashed': len(source_bytes),
                         'source_chars_decoded': len(source),
                         'quote_chars': len(quoted_claim),
                         'quote_fully_matched': start >= 0,
                         'truncated': False, 'complete': not empty,
                         'occurrence_policy': 'first_match_only',
                         'approximate_strategy': 'global_raw_codepoint_levenshtein',
                         'approximate_substring_search': 'not_performed',
                         'limits': {'max_source_bytes': MAX_SOURCE_BYTES,
                                    'max_quote_chars': MAX_QUOTE_CHARS,
                                    'max_approximate_cells': MAX_APPROXIMATE_CELLS},
                         'scope': 'full_source' if source_span is None else 'selected_span',
                         'selected_span': {'start': lower, 'end': upper},
                         'reason': 'empty_input' if empty else None,
                         'normalization_search': 'not_requested' if normalization == 'none' else 'not_run',
                         'normalization_policy': 'none' if normalization == 'none' else 'ascii_whitespace_runs_to_space_no_trim',
                         'exact_search': 'not_run' if empty else ('first_match' if start >= 0 else 'complete_no_match')},
            'semantic_support': 'not_assessed', 'source_truth': 'not_assessed',
            'deployment_authorized': False, 'requires_human_review': True,
        }
        if not empty and start < 0 and normalization == 'ascii_whitespace':
            normalized_quote = _ASCII_WS.sub(' ', quoted_claim)
            normalized_source = _ASCII_WS.sub(' ', selected)
            if source_span is None:
                position = normalized_source.find(normalized_quote)
            else:
                position = 0 if normalized_source == normalized_quote else -1
            receipt['coverage']['normalization_search'] = 'first_match' if position >= 0 else 'complete_no_match'
            if position >= 0:
                raw_start, raw_end = _raw_normalized_span(selected, position, position + len(normalized_quote))
                receipt['status'] = 'normalized_source_match'
                receipt['coverage']['quote_fully_matched'] = True
                receipt['source_spans'] = [{'start': lower + raw_start, 'end': lower + raw_end}]
        receipt['coverage']['approximate_search'] = 'not_run'
        if receipt['status'] == 'not_found':
            cells = len(quoted_claim) * len(selected)
            receipt['coverage']['approximate_cells_required'] = cells
            if cells > MAX_APPROXIMATE_CELLS:
                receipt['status'] = 'insufficient_data'
                receipt['coverage'].update(approximate_search='skipped_budget', complete=False,
                                           reason='approximate_budget_exceeded')
                return receipt
            similarity = _character_similarity(quoted_claim, selected)
            receipt['coverage']['approximate_search'] = 'complete_selected_span'
            receipt['candidate_similarity'] = similarity
            receipt['candidate_spans'] = []
            if similarity >= 0.8:
                receipt['status'] = 'approximate_candidate'
                receipt['candidate_spans'] = [{'start': lower, 'end': upper}]
        return receipt

    def __init__(self, match_score: float = 2, mismatch_penalty: float = -1, gap_penalty: float = -1):
        """Finite scores <= 1e6 in magnitude; match > 0, mismatch <= 0, gap < 0."""
        _validate_scores(match_score, mismatch_penalty, gap_penalty)
        self.match = match_score
        self.mismatch = mismatch_penalty
        self.gap = gap_penalty

    def tokenize_words(self, text: str) -> List[str]:
        """Preserve Unicode, case, marks and punctuation; discard whitespace only."""
        if len(_text_bytes(text, MAX_SOURCE_BYTES, 'text')) > MAX_SOURCE_BYTES:
            raise ValueError('text exceeds UTF-8 byte budget')
        return [text[start:end] for start, end in _token_spans(text)]

    def needleman_wunsch(self, seq1: List[str], seq2: List[str]) -> Tuple[float, float]:
        """Return full-token raw score and lexical similarity, not verification.

        Empty sequences return (0, 0.0). Over-budget alignment raises ValueError
        instead of silently truncating. Even similarity 1.0 is not proof of
        raw-text equality: tokenization excludes whitespace and scores round.
        """
        raw, similarity, _ = self._align(seq1, seq2)
        return raw, similarity

    def _align(self, seq1, seq2, traceback=False):
        _validate_scores(self.match, self.mismatch, self.gap)
        _validate_sequences(seq1, seq2)
        n, m = len(seq1), len(seq2)
        if n == 0 or m == 0:
            return 0, 0.0, []

        dp = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(n + 1):
            dp[i][0] = i * self.gap
        for j in range(m + 1):
            dp[0][j] = j * self.gap

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                match_val = dp[i - 1][j - 1] + (self.match if seq1[i - 1] == seq2[j - 1] else self.mismatch)
                delete_val = dp[i - 1][j] + self.gap
                insert_val = dp[i][j - 1] + self.gap
                dp[i][j] = max(match_val, delete_val, insert_val)

        raw_score = dp[n][m]
        max_possible = max(n, m) * self.match
        min_possible = max(n, m) * self.gap
        norm_score = max(0.0, min(1.0, (raw_score - min_possible) / (max_possible - min_possible)))

        edits = []
        if traceback:
            i, j = n, m
            while i or j:
                if i and j and dp[i][j] == dp[i - 1][j - 1] + (
                        self.match if seq1[i - 1] == seq2[j - 1] else self.mismatch):
                    if seq1[i - 1] != seq2[j - 1]:
                        edits.append(('replace', i - 1, i, j - 1, j))
                    i, j = i - 1, j - 1
                elif i and (j == 0 or dp[i][j] == dp[i - 1][j] + self.gap):
                    # Boundary multiplication can round differently from addition.
                    edits.append(('insert', i - 1, i, j, j))
                    i -= 1
                else:
                    edits.append(('delete', i, i, j - 1, j))
                    j -= 1
            edits.reverse()
        return raw_score, round(norm_score, 4), edits

    def detect_interpolated_carrier(self, suspect_text: str, canonical_carrier: str) -> Dict[str, Any]:
        """Describe one bounded lexical edit path, never a confirmed covert payload.

        Insert/delete/replace are relative to the carrier, with token and raw
        codepoint bounds. Ties select one path, not necessarily a unique edit
        history; whitespace is not assessed. Empty or excessive alignment work
        abstains. Legacy payload/risk conclusions are deliberately null/empty.
        """
        suspect_tokens = self.tokenize_words(suspect_text)
        carrier_tokens = self.tokenize_words(canonical_carrier)
        reason, similarity, edits = None, None, []
        if not suspect_tokens or not carrier_tokens:
            reason = 'empty_tokens'
        else:
            try:
                _, similarity, edits = self._align(suspect_tokens, carrier_tokens, traceback=True)
            except _AlignmentBudgetExceeded:
                reason = 'alignment_budget_exceeded'
        suspect_spans = _token_spans(suspect_text)
        carrier_spans = _token_spans(canonical_carrier)

        def bounds(spans, start, end, length):
            if start == end:
                point = spans[start][0] if start < len(spans) else length
                return {'start': point, 'end': point}
            return {'start': spans[start][0], 'end': spans[end - 1][1]}

        candidates = [
            {'operation': operation, 'start_token': i, 'end_token': j,
             'carrier_start_token': k, 'carrier_end_token': l,
             'suspect_span': bounds(suspect_spans, i, j, len(suspect_text)),
             'carrier_span': bounds(carrier_spans, k, l, len(canonical_carrier))}
            for operation, i, j, k, l in edits]
        return {
            'status': 'insufficient_data' if reason else ('edit_candidates' if candidates else 'no_edit_candidates'),
            'global_carrier_similarity': similarity,
            'has_edit_candidates': None if reason else bool(candidates), 'edit_candidates': candidates,
            'has_foreign_interpolation': None, 'interpolation_risk': None,
            'flagged_payload_spans': [], 'payload_assessment': 'not_assessed',
            'semantic_support': 'not_assessed', 'source_truth': 'not_assessed',
            'deployment_authorized': False, 'requires_human_review': True,
            'offset_unit': 'unicode_codepoint',
            'coverage': {'complete': reason is None, 'reason': reason,
                         'truncated': False, 'whitespace_assessed': False,
                         'suspect_tokens': len(suspect_tokens), 'carrier_tokens': len(carrier_tokens),
                         'alignment_path': 'not_run' if reason else 'one_deterministic_optimum_not_unique',
                         'limits': {'max_tokens': MAX_ALIGNMENT_TOKENS,
                                    'max_cells': MAX_ALIGNMENT_CELLS}},
        }

    def verify_quotation_fidelity(self, quoted_claim: str, source_text: str) -> Dict[str, Any]:
        """Unpinned compatibility wrapper; no lexical score assesses truth/faithfulness."""
        source_bytes = _text_bytes(source_text, MAX_SOURCE_BYTES, 'source_text')
        receipt = self.verify_source_quote(
            quoted_claim, source_bytes, expected_sha256=hashlib.sha256(source_bytes).hexdigest(),
            source_ref='legacy:caller-supplied-text', source_version='unversioned')
        literal = receipt['status'] == 'exact_source_match'
        receipt.update(
            quotation_fidelity_score=1.0 if literal else receipt.get('candidate_similarity'),
            verdict=receipt['status'].upper(), is_faithful=None, is_literal_match=literal,
            score_kind='lexical_only_not_semantic',
            source_pin_provenance='computed_from_supplied_text_not_independently_pinned')
        return receipt

