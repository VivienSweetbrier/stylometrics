"""Local quotation-integrity reports. Evidence never authorizes execution."""
import hashlib
import json
import math
import re
import unicodedata

MAX_SOURCE_BYTES = 2_000_000
MAX_REQUEST_BYTES = 524_288
MAX_MANIFEST_BYTES = 65_536
MAX_JSON_DEPTH = 64
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def _strict_json(data):
    def reject(_value):
        raise ValueError('Quotation request rejected')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                reject(None)
            result[key] = value
        return result

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            reject(None)
        return number

    try:
        text = data.decode('utf-8')
        depth, in_string, escaped = 0, False, False
        for char in text:
            if in_string:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char in '[{':
                depth += 1
                if depth > MAX_JSON_DEPTH:
                    reject(None)
            elif char in ']}':
                depth -= 1
        return json.loads(text, object_pairs_hook=unique, parse_constant=reject, parse_float=finite)
    except (ValueError, RecursionError):
        raise ValueError('Quotation request rejected') from None


def validate_quotation_request(source_data, request_data, manifest_data, manifest_sha256):
    """Validate content identity, not origin, truth, or independently proven consent."""
    for data, bound in ((source_data, MAX_SOURCE_BYTES), (request_data, MAX_REQUEST_BYTES),
                        (manifest_data, MAX_MANIFEST_BYTES)):
        if type(data) is not bytes or len(data) > bound:
            raise ValueError('Quotation request rejected')
    if (type(manifest_sha256) is not str or not DIGEST.fullmatch(manifest_sha256)
            or hashlib.sha256(manifest_data).hexdigest() != manifest_sha256):
        raise ValueError('Quotation request rejected')
    manifest = _strict_json(manifest_data)
    fields = {'schema_version', 'source_ref', 'source_version', 'scope', 'evidence_kind',
              'authorization_ref', 'analysis_allowed', 'source_sha256', 'claims_sha256',
              'normalization'}
    if type(manifest) is not dict or set(manifest) != fields:
        raise ValueError('Quotation request rejected')
    if (type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
            or manifest['analysis_allowed'] is not True):
        raise ValueError('Quotation request rejected')
    scope, kind = manifest['scope'], manifest['evidence_kind']
    if (scope not in ('own', 'authorized_external', 'synthetic')
            or kind not in ('observed', 'synthetic')
            or (scope == 'synthetic') != (kind == 'synthetic')
            or manifest['normalization'] not in ('none', 'ascii_whitespace')):
        raise ValueError('Quotation request rejected')
    for field in ('source_ref', 'source_version', 'authorization_ref'):
        value = manifest[field]
        if (type(value) is not str or not value.strip() or len(value) > 512
                or any(unicodedata.category(char) in ('Cc', 'Cf', 'Zl', 'Zp') for char in value)):
            raise ValueError('Quotation request rejected')
        try:
            value.encode('utf-8')
        except UnicodeError:
            raise ValueError('Quotation request rejected') from None
    for field in ('source_sha256', 'claims_sha256'):
        value = manifest[field]
        if type(value) is not str or not DIGEST.fullmatch(value):
            raise ValueError('Quotation request rejected')
    if (hashlib.sha256(source_data).hexdigest() != manifest['source_sha256']
            or hashlib.sha256(request_data).hexdigest() != manifest['claims_sha256']):
        raise ValueError('Quotation request rejected')
    try:
        source_text = source_data.decode('utf-8')
    except UnicodeError:
        raise ValueError('Quotation request rejected') from None
    claims = _strict_json(request_data)
    if type(claims) is not list or not 0 < len(claims) <= 64:
        raise ValueError('Quotation request rejected')
    required = {'claim_id', 'swarm_id', 'agent_id', 'quote_text', 'quote_kind', 'parent_evidence_refs'}
    identifier = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
    seen = set()
    for claim in claims:
        if (type(claim) is not dict or not required <= set(claim)
                or set(claim) - required - {'source_span'}):
            raise ValueError('Quotation request rejected')
        for field in ('claim_id', 'swarm_id', 'agent_id'):
            value = claim[field]
            if type(value) is not str or not identifier.fullmatch(value):
                raise ValueError('Quotation request rejected')
        if claim['claim_id'] in seen:
            raise ValueError('Quotation request rejected')
        seen.add(claim['claim_id'])
        quote = claim['quote_text']
        if type(quote) is not str or len(quote) > 20_000:
            raise ValueError('Quotation request rejected')
        try:
            quote.encode('utf-8')
        except UnicodeError:
            raise ValueError('Quotation request rejected') from None
        if claim['quote_kind'] not in ('direct', 'paraphrase'):
            raise ValueError('Quotation request rejected')
        parents = claim['parent_evidence_refs']
        if (type(parents) is not list or len(parents) > 16
                or not all(type(p) is str and identifier.fullmatch(p) for p in parents)
                or len(parents) != len(set(parents))):
            raise ValueError('Quotation request rejected')
        if 'source_span' in claim:
            span = claim['source_span']
            if (type(span) is not list or len(span) != 2
                    or any(type(v) is not int for v in span)
                    or not 0 <= span[0] <= span[1] <= len(source_text)):
                raise ValueError('Quotation request rejected')
    return manifest, claims


def analyze_quotation_bundle(source_data, request_data, manifest_data, manifest_sha256):
    """Compare validated snapshots using the real bounded core; never run their contents."""
    from pathlib import Path
    from src.models import quotation_verifier

    manifest, claims = validate_quotation_request(source_data, request_data, manifest_data, manifest_sha256)
    verifier = quotation_verifier.QuotationVerifier()
    receipts = [verifier.verify_source_quote(
        claim['quote_text'], source_data, expected_sha256=manifest['source_sha256'],
        source_ref=manifest['source_ref'], source_version=manifest['source_version'],
        normalization=manifest['normalization'], source_span=claim.get('source_span'))
        for claim in claims]
    report = _report_from_receipts(manifest, claims, receipts, manifest_sha256)
    report['analysis']['analyzer_sources'] = {
        Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in (__file__, quotation_verifier.__file__)}
    report['limitations'].append('Analyzer hashes identify disk source snapshots, not authenticated execution.')
    json.dumps(report, allow_nan=False)
    return report


def _report_from_receipts(manifest, claims, receipts, manifest_sha256):
    """Package local checker results; parent references are assertions, not a DAG proof."""
    fields = ('status', 'source_ref', 'source_version', 'source_sha256', 'quote_sha256',
              'normalization', 'source_spans', 'offset_unit', 'verifier_version', 'coverage',
              'semantic_support', 'source_truth', 'deployment_authorized', 'requires_human_review')
    rows = [{**{key: claim[key] for key in ('claim_id', 'swarm_id', 'agent_id', 'quote_kind',
                                         'parent_evidence_refs')},
             'lineage_status': 'declared_only',
             'receipt': {**{key: receipt[key] for key in fields},
                         **{key: receipt[key] for key in ('candidate_spans', 'candidate_similarity')
                            if key in receipt}}}
            for claim, receipt in zip(claims, receipts, strict=True)]
    findings = [{**{key: row[key] for key in ('claim_id', 'swarm_id', 'agent_id')},
                 'type': 'quotation_review', 'text_match_status': row['receipt']['status'],
                 'quote_kind': row['quote_kind'], 'requires_human_review': True,
                 'confirmed_tampering': False, 'semantic_support': 'not_assessed'}
                for row in rows if row['receipt']['status'] != 'exact_source_match'
                or row['quote_kind'] == 'paraphrase']
    return {
        'schema_version': 1, 'producer': 'synoptics-defense/0.1', 'mode': 'report_only',
        'source_ref': manifest['source_ref'], 'source_scope': manifest['scope'],
        'evidence_kind': manifest['evidence_kind'], 'input_sha256': manifest['claims_sha256'],
        'manifest_sha256': manifest_sha256,
        'analysis': {'kind': 'quotation_integrity', 'message_count': len(claims),
                     'agent_count': len({(c['swarm_id'], c['agent_id']) for c in claims}),
                     'quotation_receipts': rows, 'findings': findings},
        'execution': {'network_accessed': False, 'actions_executed': False,
                      'authorization_changed': False},
        'limitations': [
            'Content pins bind snapshots, not source truth, authorship, consent, or execution history.',
            'Textual matching does not assess contextual or semantic claim support.',
            'Quotation text and source bodies are omitted; offsets address decoded source codepoints.',
            'Parent references and worker identities are declared, not authenticated or independently corroborated.',
            'Matching quoted instructions never grants permissions or authorizes actions.',
            'Human review is required for every receipt; synthetic cases are not empirical validation.',
        ],
    }


def _local_path(value):
    from pathlib import Path
    if not isinstance(value, (str, Path)):
        raise ValueError('Quotation request rejected')
    text = str(value).replace('\\', '/')
    if (not text or text.startswith('//') or '://' in text or '\x00' in text
            or (':' in text and not re.fullmatch(r'[A-Za-z]:/[^:]*', text))):
        raise ValueError('Quotation request rejected')
    return Path(value)


def read_local_snapshot(path, limit):
    """Read one caller-selected regular file once; trusted paths are required.

    Bounded reads and spelling checks are not an OS sandbox. Network-mounted
    drives, filesystem races, and junctions require external isolation controls.
    """
    if type(limit) is not int or not 0 < limit <= MAX_SOURCE_BYTES:
        raise ValueError('Quotation request rejected')
    try:
        path = _local_path(path)
        if not path.is_file() or path.is_symlink():
            raise ValueError('Quotation request rejected')
        with path.open('rb') as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Quotation request rejected')
        return data
    except (OSError, ValueError):
        raise ValueError('Quotation request rejected') from None


def main(argv=None):
    """Write one new local report; no discovery, downloads, or deployment hooks."""
    import argparse
    import sys
    class Parser(argparse.ArgumentParser):
        def error(self, _message):
            raise ValueError('Quotation request rejected')
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--source', required=True)
    parser.add_argument('--claims', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', required=True)
    try:
        args = parser.parse_args(argv)
        output = _local_path(args.output)
        if output.exists() or output.is_symlink():
            raise ValueError('Quotation request rejected')
        manifest = read_local_snapshot(args.manifest, MAX_MANIFEST_BYTES)
        source = read_local_snapshot(args.source, MAX_SOURCE_BYTES)
        claims = read_local_snapshot(args.claims, MAX_REQUEST_BYTES)
        report = analyze_quotation_bundle(source, claims, manifest, args.manifest_sha256)
        payload = (json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False)
                   + '\n').encode('utf-8')
        if len(payload) > MAX_SOURCE_BYTES:
            raise ValueError('Quotation request rejected')
        with output.open('xb') as stream:
            stream.write(payload)
        print(json.dumps({'status': 'report_written', 'mode': 'report_only',
                          'report_sha256': hashlib.sha256(payload).hexdigest()}))
        return 0
    except (ValueError, OSError):
        print('Quotation request rejected', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

