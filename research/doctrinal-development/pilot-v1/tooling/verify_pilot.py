"""Offline pilot integrity checks; no semantic, historical, or truth adjudication.

Invoke with Python -B. Load only an explicitly supplied trusted standalone core,
not Synoptics packages. Historical input is read-only; receipts go to a NEW
output directory. See README.md for the supported contract and limits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
TRACKS = {'newman': ['N1', 'N2', 'N3', 'N4'],
          'eucharist': ['E1', 'E2', 'E3', 'E4'],
          'religious-freedom': ['R1', 'R2', 'R3', 'R4']}
CAUTION = {'semantic_support': 'not_assessed', 'source_truth': 'not_assessed',
           'requires_human_review': True, 'deployment_authorized': False}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify(pilot_root, core_path):
    root = Path(pilot_root).resolve()
    core_bytes = Path(core_path).read_bytes()
    core = types.ModuleType('pilot_standalone_quotation_core')
    exec(compile(core_bytes, str(core_path), 'exec'), core.__dict__)
    verifier = core.QuotationVerifier()
    manifest, receipts, cases = {}, [], {}
    source_count = dossier_count = passage_count = 0

    def read(path):
        data = path.read_bytes()
        manifest[path.relative_to(root).as_posix()] = {'sha256': sha256(data), 'bytes': len(data)}
        return data

    for track in TRACKS:
        folder = root / track
        doc = json.loads(read(folder / 'dossiers.json'))
        read(folder / 'REPORT.md')
        read(folder / 'sources-ledger.json')
        sources = {}
        for source in doc['sources']:
            read(folder / source['raw_path'])
            text_bytes = read(folder / source['text_path'])
            sources[source['source_id']] = (source, text_bytes)
            source_count += 1
        cases[track] = []
        for dossier in doc['dossiers']:
            cases[track].append(dossier['case_id'])
            dossier_count += 1
            for passage in dossier['passages']:
                source, data = sources[passage['source_id']]
                receipt = verifier.verify_source_quote(
                    passage['quote'], data, expected_sha256=source['text_sha256'],
                    source_ref=source['source_id'], source_version=source['source_version'],
                    normalization='none', source_span=[passage['start'], passage['end']])
                receipts.append({'track': track, 'case_id': dossier['case_id'],
                                 'passage_id': passage['passage_id'], 'receipt': receipt})
                passage_count += 1
    return dict(schema_version=1, status='pilot_integrity_verified',
                verification_scope='offline_literal_and_contract_only', **CAUTION,
                counts=dict(tracks=len(cases), sources=source_count, dossiers=dossier_count,
                            passages=passage_count, core_receipts=len(receipts)),
                case_ids=cases, receipts=receipts,
                hashes=dict(verifier_sha256=sha256(Path(__file__).read_bytes()),
                            core_sha256=sha256(core_bytes),
                            protocol_sha256=sha256((root / 'PROTOCOL.md').read_bytes()),
                            artifact_contract_sha256=sha256((root / 'ARTIFACT-CONTRACT.md').read_bytes()),
                            data=[dict(path=path, **entry) for path, entry in sorted(manifest.items())]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot-root', required=True, type=Path)
    parser.add_argument('--core', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='NEW output directory; never an existing path')
    args = parser.parse_args()
    report = verify(args.pilot_root, args.core)
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / 'receipt.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'output': str(args.output / 'receipt.json'), 'counts': report['counts']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
