"""Focused, explicitly SYNTHETIC offline fixtures; never edit historical data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
CORE = PILOT.parents[2] / 'src' / 'models' / 'quotation_verifier.py'
TOOL = HERE / 'verify_pilot.py'
TRACKS = {'newman': ['N1', 'N2', 'N3', 'N4'],
          'eucharist': ['E1', 'E2', 'E3', 'E4'],
          'religious-freedom': ['R1', 'R2', 'R3', 'R4']}
NOTES = ['preservation_of_type', 'continuity_of_principles', 'power_of_assimilation',
         'logical_sequence', 'anticipation_of_future', 'conservative_action', 'chronic_vigour']
TEXT = 'SYNTHETIC ONLY — α😀 before.\r\nNo person shall be compelled.\r\nAfter. Another synthetic sentence. End.'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def fixture(root):
    root.mkdir()
    for name in ('PROTOCOL.md', 'ARTIFACT-CONTRACT.md'):
        (root / name).write_bytes((PILOT / name).read_bytes())
    for track, case_ids in TRACKS.items():
        folder = root / track
        (folder / 'sources').mkdir(parents=True)
        raw = b'SYNTHETIC RAW, NOT A HISTORICAL WITNESS\n' + TEXT.encode('utf-8')
        text = TEXT.encode('utf-8')
        (folder / 'sources' / 'synthetic.raw').write_bytes(raw)
        (folder / 'sources' / 'synthetic.txt').write_bytes(text)
        source = {key: 'SYNTHETIC ONLY' for key in (
            'title', 'document_kind', 'language', 'source_version', 'work_date',
            'witness_edition', 'edition_status', 'translator', 'publisher_or_host',
            'rights_status', 'extraction_notes')}
        source.update(source_id='synthetic:one', url='https://example.invalid/synthetic',
                      retrieved_at_utc='2026-01-01T00:00:00Z',
                      raw_path='sources/synthetic.raw', raw_sha256=digest(raw),
                      text_path='sources/synthetic.txt', text_sha256=digest(text),
                      provenance_limitations=['Explicitly synthetic test fixture; no historical claims.'])
        dossiers = []
        for case_id in case_ids:
            passages = []
            for number, quote in enumerate(('No person shall be compelled.', 'Another synthetic sentence.'), 1):
                start = TEXT.index(quote)
                end = start + len(quote)
                passages.append(dict(
                    passage_id=f'{case_id}:p{number}', source_id=source['source_id'],
                    locator=f'SYNTHETIC paragraph {number}', quote=quote, start=start, end=end,
                    context_before=TEXT[max(0, start - 300):start],
                    context_after=TEXT[end:end + 300], context_note='SYNTHETIC ONLY',
                    normative_context={key: 'SYNTHETIC ONLY' for key in (
                        'speaker_or_issuer', 'audience', 'subject', 'modality', 'scope', 'conditions')}))
            refs = [p['passage_id'] for p in passages]
            reading = dict(statement='SYNTHETIC reading', evidence_passage_ids=refs,
                           assumptions=['SYNTHETIC assumption'], strongest_objection='SYNTHETIC objection')
            dossiers.append(dict(
                case_id=case_id, title='SYNTHETIC title', question='SYNTHETIC question?', passages=passages,
                propositions=[dict(statement='SYNTHETIC proposition', evidence_passage_ids=refs,
                                   qualifications=['SYNTHETIC qualification'])],
                inference_chain=['SYNTHETIC premise and inference; not history.'],
                continuity_reading=copy.deepcopy(reading), rupture_reading=copy.deepcopy(reading),
                newman_profile={note: dict(status='undetermined', evidence_passage_ids=refs,
                                          rationale='Synthetic fixture only.') for note in NOTES},
                provisional_assessment=dict(label='insufficient_evidence', rationale='Synthetic fixture only.'),
                human_review_status='pending', gaps=['SYNTHETIC, no historical evidence'],
                next_evidence=['Replace only in real research; never count this as history.']))
        save_json(folder / 'dossiers.json', dict(schema_version=1, track=track, sources=[source],
                                                dossiers=dossiers, acquisition_gaps=['SYNTHETIC ONLY']))
        save_json(folder / 'sources-ledger.json', {'synthetic': True, 'sources': []})
        (folder / 'REPORT.md').write_text('# SYNTHETIC TEST REPORT\nNo historical findings.\n', encoding='utf-8')


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'pilot'
        fixture(self.root)
        self.output = self.base / 'new-receipts'

    def document(self, track='newman'):
        return json.loads((self.root / track / 'dossiers.json').read_bytes())

    def save(self, doc, track='newman'):
        save_json(self.root / track / 'dossiers.json', doc)

    def run_cli(self, output=None, core=None):
        self.assertTrue(TOOL.is_file(), 'offline verifier CLI has not been implemented')
        return subprocess.run([sys.executable, '-B', str(TOOL), '--pilot-root', str(self.root),
                               '--core', str(core or CORE), '--output', str(output or self.output)],
                              capture_output=True, text=True, encoding='utf-8', cwd=HERE)

    def assert_rejected(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(self.output.exists(), 'invalid input must not create an output directory')
        self.assertNotIn('Traceback', result.stderr)

    def test_valid_pilot_retains_actual_core_receipts(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((self.output / 'receipt.json').read_bytes())
        self.assertEqual(report['counts'], dict(tracks=3, sources=3, dossiers=12, passages=24, core_receipts=24))
        self.assertEqual(report['case_ids'], TRACKS)
        self.assertEqual(report['hashes']['core_sha256'], digest(CORE.read_bytes()))
        self.assertEqual(report['hashes']['verifier_sha256'], digest(TOOL.read_bytes()))
        for filename, key in [('PROTOCOL.md', 'protocol_sha256'),
                              ('ARTIFACT-CONTRACT.md', 'artifact_contract_sha256')]:
            self.assertEqual(report['hashes'][key], digest((self.root / filename).read_bytes()))
        paths = [f['path'] for f in report['hashes']['data']]
        self.assertEqual(len(paths), len(set(paths)))
        for entry in report['hashes']['data']:
            actual = (self.root / entry['path']).read_bytes()
            self.assertEqual(entry['sha256'], digest(actual))
            self.assertEqual(entry['bytes'], len(actual))
        spec = importlib.util.spec_from_file_location('synthetic_receipt_comparison_core', CORE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        verifier = module.QuotationVerifier()
        self.assertEqual(len(report['receipts']), 24)
        for item in report['receipts']:
            doc = self.document(item['track'])
            dossier = next(d for d in doc['dossiers'] if d['case_id'] == item['case_id'])
            passage = next(p for p in dossier['passages'] if p['passage_id'] == item['passage_id'])
            source = doc['sources'][0]
            expected = verifier.verify_source_quote(
                passage['quote'], (self.root / item['track'] / source['text_path']).read_bytes(),
                expected_sha256=source['text_sha256'], source_ref=source['source_id'],
                source_version=source['source_version'], normalization='none',
                source_span=[passage['start'], passage['end']])
            self.assertEqual(item['receipt'], expected)
            self.assertEqual(expected['semantic_support'], 'not_assessed')
            self.assertEqual(expected['source_truth'], 'not_assessed')
            self.assertIs(expected['requires_human_review'], True)
            self.assertIs(expected['deployment_authorized'], False)
        self.assertEqual(report['semantic_support'], 'not_assessed')
        self.assertEqual(report['source_truth'], 'not_assessed')
        self.assertIs(report['requires_human_review'], True)
        self.assertIs(report['deployment_authorized'], False)


if __name__ == '__main__':
    unittest.main()
