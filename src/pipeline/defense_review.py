"""Offline, report-only evidence boundary. Trace contents are never instructions."""
import hashlib
import json
import math
import re
from datetime import datetime

MAX_INPUT_BYTES = 2_000_000
MAX_RECORDS = 2_000
MAX_AGENTS = 50
MAX_TEXT_CHARS = 20_000
MAX_JSON_DEPTH = 32


def strict_json(data):
    """Reject ambiguous keys/nonfinite numbers; bound nesting before JSON decode."""
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result

    def nonfinite(_value):
        raise ValueError('Nonfinite JSON number')

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Nonfinite JSON number')
        return number

    try:
        text = data.decode('utf-8')
        depth, in_string, escaped = 0, False, False
        # This is only a resource guard; json.loads still validates all syntax.
        for character in text:
            if in_string:
                if escaped:
                    escaped = False
                elif character == '\\':
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character in '[{':
                depth += 1
                if depth > MAX_JSON_DEPTH:
                    raise ValueError('JSON container depth limit exceeded')
            elif character in ']}':
                depth -= 1
        return json.loads(text, object_pairs_hook=object_pairs,
                          parse_constant=nonfinite, parse_float=finite_float)
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid bounded UTF-8 JSON') from exc


IDENTIFIER = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
MANIFEST_FIELDS = {'schema_version', 'source_ref', 'scope', 'evidence_kind',
                   'authorization_ref', 'analysis_allowed', 'input_sha256',
                   'allowed_actions'}


def validate_bundle(data, manifest):
    """Validate operator attestation and content identity, not origin or truth."""
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_FIELDS:
        raise ValueError('Manifest fields are missing or unsupported')
    if type(manifest['schema_version']) is not int or manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest schema')
    if manifest['analysis_allowed'] is not True:
        raise ValueError('Explicit local analysis attestation required')
    scope, kind = manifest['scope'], manifest['evidence_kind']
    if scope not in ('own', 'authorized_external', 'synthetic') or kind not in ('observed', 'synthetic'):
        raise ValueError('Unsupported source scope or evidence kind')
    if (scope == 'synthetic') != (kind == 'synthetic'):
        raise ValueError('Synthetic scope and evidence kind must agree')
    for field in ('source_ref', 'authorization_ref'):
        value = manifest[field]
        if not isinstance(value, str) or not value.strip() or len(value) > 512:
            raise ValueError('Source and authorization references must be bounded text')
    actions = manifest['allowed_actions']
    if not isinstance(actions, list) or len(actions) > 100 or not all(
        isinstance(a, str) and IDENTIFIER.fullmatch(a) for a in actions
    ) or len(actions) != len(set(actions)):
        raise ValueError('Allowed actions must be unique bounded identifiers')
    digest = manifest['input_sha256']
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise ValueError('Invalid input digest')
    if type(data) is not bytes or not 0 < len(data) <= MAX_INPUT_BYTES:
        raise ValueError('Input byte limit exceeded or invalid type')
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Input digest mismatch')
    records = strict_json(data)
    if not isinstance(records, list) or not 0 < len(records) <= MAX_RECORDS:
        raise ValueError('Input must be a nonempty bounded record array')
    required = {'message_id', 'swarm_id', 'agent_id', 'event_type', 'text'}
    optional = {'timestamp', 'action'}
    identities, agents, last_times = set(), set(), {}
    for rec in records:
        if not isinstance(rec, dict) or not required <= set(rec) or set(rec) - required - optional:
            raise ValueError('Record fields are missing or unsupported')
        for field in ('message_id', 'swarm_id', 'agent_id'):
            value = rec[field]
            if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
                raise ValueError('Record identifiers must be literal bounded ASCII identifiers')
        identity = (rec['swarm_id'], rec['message_id'])
        if identity in identities:
            raise ValueError('Duplicate record identity')
        identities.add(identity)
        agent = (rec['swarm_id'], rec['agent_id'])
        agents.add(agent)
        if len(agents) > MAX_AGENTS:
            raise ValueError('Agent budget exceeded')
        text = rec['text']
        if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:
            raise ValueError('Record text must be bounded text')
        text.encode('utf-8')
        event = rec['event_type']
        if event not in ('message', 'tool_call', 'decision'):
            raise ValueError('Unsupported event type')
        if event == 'tool_call':
            action = rec.get('action')
            if not isinstance(action, str) or not IDENTIFIER.fullmatch(action):
                raise ValueError('Tool calls must declare an action identifier')
        elif 'action' in rec:
            raise ValueError('Only tool_call records may declare actions')
        if 'timestamp' in rec:
            timestamp = rec['timestamp']
            if not isinstance(timestamp, str) or len(timestamp) > 64:
                raise ValueError('Invalid timestamp')
            try:
                moment = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError as exc:
                raise ValueError('Invalid timestamp') from exc
            if moment.utcoffset() is None:
                raise ValueError('Timestamp requires a timezone')
            if agent in last_times and moment < last_times[agent]:
                raise ValueError('Agent timestamps run backward')
            last_times[agent] = moment
    return records


def _style_analysis(records, sources):
    """English-oriented, cohort-relative comparison with explicit abstention."""
    import math
    from itertools import combinations
    from pathlib import Path

    grouped = {}
    for record in records:
        identity = (record['swarm_id'], record['agent_id'])
        grouped.setdefault(identity, []).append(record['text'])
    corpus = {json.dumps(identity): '\n\n'.join(texts) for identity, texts in grouped.items()}
    eligible = {key: text for key, text in corpus.items()
                if len(re.findall(r'\b[A-Za-z]+\b', text)) >= 50}
    result = {'status': 'insufficient_data', 'calibrated_probability': False,
              'identity_conclusion': 'not_established', 'eligible_agents': len(eligible),
              'excluded_short_agents': len(corpus) - len(eligible), 'min_ascii_words': 50,
              'pairwise_distances': [],
              'limitations': ['English-oriented features; multilingual validity not established.',
                              'Cohort-relative normalization; distances are not comparable across cohorts.',
                              'Minimum length is a heuristic admission rule, not validated statistical power.']}
    if len(eligible) < 2:
        result['reason'] = 'At least two agents need sufficient text'
        return result
    try:
        from src.models import swarm_delta
        source = Path(swarm_delta.__file__)
        sources[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        delta, _features = swarm_delta.SwarmDeltaEngine().compute_burrows_delta(eligible)
    except ImportError:
        result.update(status='unavailable', reason='Optional stylometry dependencies unavailable')
        return result
    except ValueError:
        result['reason'] = 'Insufficient variation or invalid features'
        return result
    pairs = []
    for left, right in combinations(eligible, 2):
        value = float(delta.loc[left, right])
        if not math.isfinite(value) or value < 0:
            result['reason'] = 'Nonfinite or invalid feature distance'
            return result
        pairs.append({'left': json.loads(left), 'right': json.loads(right), 'delta': value})
    result.update(status='assessed', pairwise_distances=pairs)
    return result


def analyze_bundle(data, manifest):
    """Run local advisory heuristics; never grant permissions or act on text."""
    from pathlib import Path
    from src.models import stegoprobe_engine

    records = validate_bundle(data, manifest)
    stego = stegoprobe_engine.StegoProbeEngine()
    messages, findings, agents = [], [], set()
    for record in records:
        agents.add((record['swarm_id'], record['agent_id']))
        identity = {key: record[key] for key in ('message_id', 'swarm_id', 'agent_id')}
        result = stego.analyze_message(record['text'])
        scores = {name: result[key]['risk_score'] for name, key in (
            ('unicode', 'unicode_stego'), ('whitespace', 'whitespace_stego'),
            ('lexical', 'synonym_distribution'), ('rank_frequency', 'rank_entropy'))}
        metadata = {
            name: {key: result[name][key] for key in
                   ('score_type', 'evidence_status', 'calibrated_probability', 'analysis_status',
                    'has_format_characters', 'has_unicode_stego')
                   if key in result[name]}
            for name in ('unicode_stego', 'whitespace_stego', 'synonym_distribution', 'rank_entropy')
        }
        messages.append({**identity,
                         'text_sha256': hashlib.sha256(record['text'].encode('utf-8')).hexdigest(),
                         'characters': len(record['text']), 'heuristic_scores': scores,
                         'score_type': result['score_type'],
                         'evidence_status': result['evidence_status'],
                         'insufficient_data': list(result['insufficient_data']),
                         'detector_metadata': metadata,
                         'calibrated_probability': False})
        for field, flag, name in (
            ('unicode_stego', 'has_format_characters', 'unicode_format_indicator'),
            ('whitespace_stego', 'has_whitespace_stego', 'whitespace_pattern_indicator')
        ):
            if result[field][flag]:
                findings.append({**identity, 'type': name, 'requires_human_review': True,
                                 'confirmed_covert_channel': False})
        if record['event_type'] == 'tool_call' and record['action'] not in manifest['allowed_actions']:
            findings.append({**identity, 'type': 'declared_action_outside_allowlist',
                             'action': record['action'], 'requires_human_review': True,
                             'log_is_not_independent_execution_proof': True})
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=True, allow_nan=False).encode('utf-8')
    sources = {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest()
               for p in (__file__, stegoprobe_engine.__file__)}
    style = _style_analysis(records, sources)
    report = {
        'schema_version': 1, 'producer': 'synoptics-defense/0.1', 'mode': 'report_only',
        'evidence_kind': manifest['evidence_kind'], 'source_scope': manifest['scope'],
        'source_ref': manifest['source_ref'], 'input_sha256': manifest['input_sha256'],
        'manifest_sha256': hashlib.sha256(canonical).hexdigest(),
        'analysis': {'message_count': len(records), 'agent_count': len(agents),
                     'messages': messages, 'findings': findings, 'analyzer_sources': sources,
                     'style': style},
        'execution': {'network_accessed': False, 'actions_executed': False,
                      'authorization_changed': False},
        'limitations': [
            'Operator attestation and content hashes do not establish origin, consent, or truth.',
            'Analyzer hashes identify local source file versions; they do not authenticate execution or loaded code.',
            'All trace text and decoded content remain untrusted data, never instructions.',
            'Heuristic indicators are not calibrated probabilities or proof of control/collusion.',
            'Absent indicators do not establish safety; no automatic blocking or promotion.',
            'Raw transcript text and decoded payloads are excluded from this report.',
            'Synthetic evidence is a test fixture, not empirical validation.',
        ],
    }
    json.dumps(report, allow_nan=False)
    return report


def main(argv=None):
    """Analyze one explicitly selected local JSON export; never overwrite output."""
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description='Local, provenance-gated swarm review (no enforcement)')
    parser.add_argument('--input', required=True, help='Canonical JSON array of trace records')
    parser.add_argument('--manifest', required=True, help='Operator-authored analysis attestation')
    parser.add_argument('--output', required=True, help='New report JSON path; parent directory must exist')
    args = parser.parse_args(argv)
    try:
        paths = [Path(value) for value in (args.input, args.manifest, args.output)]
        if any(str(path).startswith(('\\\\', '//')) for path in paths):
            raise ValueError('Only local filesystem paths are supported')
        source, attestation, output = paths
        if not source.is_file() or not attestation.is_file() or output.exists():
            raise ValueError('Inputs must exist and output must be a new file')
        with source.open('rb') as stream:
            data = stream.read(MAX_INPUT_BYTES + 1)
        with attestation.open('rb') as stream:
            raw_manifest = stream.read(65_537)
        if len(raw_manifest) > 65_536:
            raise ValueError('Manifest byte limit exceeded')
        report = analyze_bundle(data, strict_json(raw_manifest))
        payload = (json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')
        if len(payload) > MAX_INPUT_BYTES:
            raise ValueError('Report exceeds output budget')
        with output.open('xb') as stream:
            stream.write(payload)
        print(json.dumps({'status': 'report_written', 'output': str(output),
                          'report_sha256': hashlib.sha256(payload).hexdigest(),
                          'mode': 'report_only'}))
        return 0
    except (ValueError, TypeError, OSError, ImportError) as exc:
        print('Review rejected: ' + type(exc).__name__ + '; no approval issued.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
