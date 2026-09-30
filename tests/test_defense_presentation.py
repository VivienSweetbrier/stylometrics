"""Report/UI regressions using synthetic fixtures, never importing cyber_app."""
import ast
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.models.stegoprobe_engine import StegoProbeEngine
from src.pipeline import defense_review


def bundle(*texts):
    records = [{'message_id': f'm{i}', 'swarm_id': 'fixture', 'agent_id': f'a{i}',
                'event_type': 'message', 'text': text} for i, text in enumerate(texts)]
    data = json.dumps(records, ensure_ascii=True).encode('utf-8')
    manifest = {'schema_version': 1, 'source_ref': 'fixture:presentation',
                'scope': 'synthetic', 'evidence_kind': 'synthetic',
                'authorization_ref': 'test-only', 'analysis_allowed': True,
                'input_sha256': hashlib.sha256(data).hexdigest(), 'allowed_actions': []}
    return data, manifest


@pytest.mark.parametrize('text', ['PRIVATE_SHORT_FIXTURE', 'use utilize ' * 20])
def test_report_preserves_detector_abstention_and_unconfirmed_metadata(text):
    detector = StegoProbeEngine().analyze_message(text)
    report = defense_review.analyze_bundle(*bundle(text))
    message = report['analysis']['messages'][0]
    assert message.get('score_type') == detector['score_type'] == 'heuristic'
    assert message['evidence_status'] == detector['evidence_status'] == 'unconfirmed'
    assert message['insufficient_data'] == detector['insufficient_data']
    assert message['calibrated_probability'] is False  # Existing report convention.
    for name in ('unicode_stego', 'whitespace_stego', 'synonym_distribution', 'rank_entropy'):
        metadata = message['detector_metadata'][name]
        for key in ('score_type', 'evidence_status', 'calibrated_probability', 'analysis_status'):
            if key in detector[name]:
                assert metadata[key] == detector[name][key]
    encoded = json.dumps(report, allow_nan=False)
    assert text not in encoded
    assert 'decoded_payload' not in encoded
    assert report['producer'] == 'synoptics-defense/0.1'
    assert report['mode'] == 'report_only'


@pytest.mark.parametrize('text, candidate', [
    ('Family: \U0001f468\u200d\U0001f469\u200d\U0001f467.', False),
    ('Hello ' + ''.join('\u200b' if b == '0' else '\u200c' for b in '0100100001001001'), True),
])
def test_report_separates_unicode_presence_from_unconfirmed_decoding(text, candidate):
    report = defense_review.analyze_bundle(*bundle(text))
    findings = report['analysis']['findings']
    assert any(f['type'] == 'unicode_format_indicator' for f in findings)
    metadata = report['analysis']['messages'][0]['detector_metadata']['unicode_stego']
    assert metadata['has_format_characters'] is True
    assert metadata['has_unicode_stego'] is candidate  # Legacy candidate flag, not confirmation.
    assert metadata['evidence_status'] == 'unconfirmed'
    finding = next(f for f in findings if f['type'] == 'unicode_format_indicator')
    assert finding['confirmed_covert_channel'] is False
    assert finding['requires_human_review'] is True
    assert 'decoded_payload' not in json.dumps(report)
    assert 'HI' not in json.dumps(report)


@pytest.mark.parametrize('texts, used_style', [
    (['short'], False),
    (['the plan is clear and we review the work. ' * 12,
      'Behold, thou traveller! Wherefore art thou? Thy passage shall cease. ' * 12], True),
    (['the same uninformative profile. ' * 20] * 2, True),
])
def test_report_hashes_style_source_only_when_used_without_execution_attestation(texts, used_style):
    from pathlib import Path
    from src.models import stegoprobe_engine, swarm_delta

    report = defense_review.analyze_bundle(*bundle(*texts))
    sources = report['analysis']['analyzer_sources']
    expected = [defense_review, stegoprobe_engine] + ([swarm_delta] if used_style else [])
    assert set(sources) == {Path(module.__file__).name for module in expected}
    for module in expected:
        assert sources[Path(module.__file__).name] == hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    assert 'not authenticate execution' in ' '.join(report['limitations'])


@pytest.mark.parametrize('raw', [b'1e309', b'-1e309', b'{"score": 1e999}'])
def test_strict_json_rejects_finite_literal_overflow(raw):
    with pytest.raises(ValueError, match='Nonfinite'):
        defense_review.strict_json(raw)
    assert defense_review.strict_json(b'1e308') == 1e308
    assert defense_review.strict_json(b'{"score": -0.125}') == {'score': -0.125}


def test_strict_json_bounds_container_depth_before_decode(monkeypatch):
    at_limit = b'[' * 32 + b'0' + b']' * 32
    assert defense_review.strict_json(at_limit) == json.loads(at_limit)
    literal = {'text': '[{' * 100 + '\\"' + '}]' * 100}
    assert defense_review.strict_json(json.dumps(literal).encode('utf-8')) == literal
    # Instrument the parser seam: too-deep input must not reach json.loads.
    def forbidden_decode(*args, **kwargs):
        pytest.fail('Over-depth JSON reached the decoder')
    monkeypatch.setattr(defense_review.json, 'loads', forbidden_decode)
    for raw in (b'[' * 33 + b'0' + b']' * 33,
                b'{"a":' * 33 + b'0' + b'}' * 33):
        with pytest.raises(ValueError, match='depth'):
            defense_review.strict_json(raw)


def presentation_api():
    name = 'src.visualization.defense_presentation'
    assert importlib.util.find_spec(name) is not None, 'Pure presentation boundary missing'
    return importlib.import_module(name)


def dashboard_section(tab):
    source = (Path(__file__).resolve().parents[1] / 'cyber_app.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    section = next(node for node in ast.walk(tree) if isinstance(node, ast.With)
                   and any(isinstance(item.context_expr, ast.Name) and item.context_expr.id == tab
                           for item in node.items))
    return section, ast.get_source_segment(source, section)


@pytest.mark.parametrize('text', [
    'Acknowledged.', 'Family: \U0001f468\u200d\U0001f469.',
    'alpha beta gamma delta epsilon ' * 6,
    ''.join('\u200b' if bit == '0' else '\u200c'
            for char in '`[fixture](https://invalid) <tag>`'
            for bit in format(ord(char), '08b')),
], ids=['abstention', 'formatting', 'evaluated-rank', 'inert-decoding'])
def test_stego_view_shows_unconfirmed_status_and_uses_literal_candidate_rendering(text):
    analysis = StegoProbeEngine().analyze_message(text)
    view = presentation_api().stego_presentation(analysis)
    assert 'not a probability' in view['score_label']
    assert '%' not in view['score_text']
    assert 'unconfirmed' in view['notice'].lower()
    assert 'not established' in view['notice'].lower()
    assert view['insufficient_data'] == analysis['insufficient_data']
    assert view['unicode_present'] == analysis['unicode_stego']['has_format_characters']
    assert view['candidate'] == analysis['unicode_stego']['decoded_payload']
    assert 'untrusted' in view['candidate_notice'].lower()
    rank = analysis['rank_entropy']
    if rank['analysis_status'] == 'insufficient_data':
        assert 'insufficient data' in view['rank_summary'].lower()
    else:
        assert str(rank['type_token_ratio']) in view['rank_summary']
    if analysis['synonym_distribution']['analysis_status'] == 'insufficient_data':
        assert 'insufficient data' in view['lexical_summary'].lower()
    section, source = dashboard_section('stego_tab')
    assert 'stego_presentation(analysis)' in source
    assert 'has_unicode_stego' not in source  # Presence uses the distinct format flag.
    assert 'CRITICAL' not in source
    assert 'lexical_diversity_ttr' not in source
    assert 'st.success' not in source
    assert "st.code(view['candidate'], language='text')" in source
    for node in ast.walk(section):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('markdown', 'success', 'error'):
            assert 'candidate' not in ast.unparse(node)


@pytest.mark.parametrize('corpus', [
    {'only': 'the same fixture'},
    {'a': 'the same fixture', 'b': 'the same fixture'},
    {'a': 'the the and', 'b': 'of in in!', 'c': 'we can go?'},
])
def test_swarm_view_is_similarity_not_attribution_and_retains_abstention(corpus):
    from src.models.swarm_delta import SwarmDeltaEngine

    engine = SwarmDeltaEngine()
    try:
        distances, _ = engine.compute_burrows_delta(corpus)
    except ValueError:
        clustering = None
    else:
        clustering = engine.cluster_swarm_identities(distances)
    module = presentation_api()
    assert hasattr(module, 'swarm_presentation'), 'Similarity presentation missing'
    view = module.swarm_presentation(clustering)
    assert 'not evidence of shared identity' in view['notice'].lower()
    assert 'uncalibrated' in view['notice'].lower()
    assert view['available'] is (clustering is not None)
    if clustering is None:
        assert view['groups'] == []
        assert 'insufficient' in view['summary'].lower()
    else:
        assert view['groups'] == clustering['similarity_groups']
        assert str(clustering['num_clusters']) in view['summary']
    _, source = dashboard_section('swarm_tab')
    assert 'swarm_presentation(clustering)' in source
    assert 'except ValueError' in source
    for claim in ('Sybil Unmasker', 'Attribution', 'Shared Controller / Sybil',
                  'Detected Sybil', 'Coordinated Swarm', 'Forensic Verdict',
                  'controlled by the same', 'No Sybil groups detected', 'st.success'):
        assert claim not in source
    assert "view['notice']" in source


@pytest.mark.parametrize('count', [0, 1, 2, 3, 6])
def test_trajectory_view_preserves_warmup_and_causal_thresholds_without_attack_claims(count):
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    turns = [{'text': 'the and of in.'} for _ in range(count)]
    if turns:
        turns[-1]['text'] += ''.join('\u200b' if b == '0' else '\u200c' for b in '0100100001001001')
    result = TrajectoryDriftDetector(window_size=2).analyze_agent_trajectory(turns)
    module = presentation_api()
    assert hasattr(module, 'trajectory_presentation'), 'Warmup-aware presentation missing'
    view = module.trajectory_presentation(result)
    assert view['style_available'] is (count > 2)
    assert 'uncalibrated' in view['notice'].lower()
    assert 'not evidence' in view['notice'].lower()
    assert str(count) in view['scan_summary']
    assert [r['stylometric_drift'] for r in view['timeline']] == [r['stylometric_drift'] for r in result['timeline']]
    assert [r['drift_threshold'] for r in view['timeline']] == [r['drift_threshold'] for r in result['timeline']]
    assert all(r['stylometric_drift'] is None for r in view['timeline'][:2])
    assert all('preview' not in r for r in view['timeline'])
    for key in ('mean_drift', 'std_drift', 'drift_threshold'):
        assert '%' not in view['metrics'][key]
        if result[key] is None:
            assert 'Unavailable' in view['metrics'][key]
        else:
            assert view['metrics'][key] == f"{result[key]:.3f}"
    assert len(view['alerts']) == len(result['alerts'])
    for shown, original in zip(view['alerts'], result['alerts']):
        assert shown['label'] in ('Message indicator review', 'Style shift review')
        assert shown['turn_text'] == original['turn_text']
    _, source = dashboard_section('drift_tab')
    assert 'trajectory_presentation(results)' in source
    assert "if view['style_available']:" in source
    assert 'connectgaps=False' in source
    assert 'add_hline' not in source  # Never apply the final threshold to earlier turns.
    assert "y=['stylometric_drift', 'drift_threshold']" in source
    assert 'Injection Alert' not in source
    assert 'st.error' not in source
    assert "st.code(alert['turn_text'], language='text')" in source


def test_dashboard_entry_labels_describe_synthetic_report_only_review():
    source = (Path(__file__).resolve().parents[1] / 'cyber_app.py').read_text(encoding='utf-8')
    for claim in ('unmask shared prompt controllers', 'Sybil Unmasker', 'Hijack Monitor',
                  'Covert Channel Scanner', 'Load Verification Scenario:',
                  'Clean Organic Agent Response', 'token entropy'):
        assert claim not in source
    assert 'Report-only review of authorized or synthetic traces' in source
    section, _ = dashboard_section('stego_tab')
    samples = next(node.value for node in ast.walk(section)
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'sample_texts' for t in node.targets))
    options = next(node.args[1] for node in ast.walk(section)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'selectbox')
    assert set(ast.literal_eval(options)) == set(ast.literal_eval(samples))
    assert all('Synthetic' in label for label in ast.literal_eval(options))
