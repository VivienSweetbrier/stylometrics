"""Synthetic local-only source/claim intake tests, not effectiveness evidence."""
import hashlib
import importlib
import importlib.util
import json

import pytest


def api():
    spec = importlib.util.find_spec('src.pipeline.quotation_review')
    assert spec is not None, 'Quotation report producer is not implemented'
    return importlib.import_module('src.pipeline.quotation_review')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bundle(claims=None, **changes):
    source = 'The observed dose was 10 mg. The result is not established.'.encode('utf-8')
    records = claims if claims is not None else [{'claim_id': 'c1', 'swarm_id': 'local',
        'agent_id': 'a1', 'quote_text': 'The observed dose was 10 mg.', 'quote_kind': 'direct',
        'parent_evidence_refs': ['source:fixture-v1']}]
    request = json.dumps(records, ensure_ascii=True).encode('utf-8')
    manifest = {'schema_version': 1, 'source_ref': 'fixture:source', 'source_version': 'v1',
        'scope': 'synthetic', 'evidence_kind': 'synthetic', 'authorization_ref': 'fixture:operator',
        'analysis_allowed': True, 'source_sha256': sha(source), 'claims_sha256': sha(request),
        'normalization': 'none'}
    manifest.update(changes)
    raw_manifest = json.dumps(manifest).encode('utf-8')
    return source, request, raw_manifest, sha(raw_manifest)


def test_changed_source_is_rejected_before_any_analysis():
    source, request, manifest, pin = bundle()
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(source + b' altered', request, manifest, pin)


@pytest.mark.parametrize('change', ['manifest_bytes', 'manifest_pin', 'claim_bytes', 'pin_case', 'pin_type'])
def test_every_input_snapshot_is_bound_to_the_caller_manifest_pin(change):
    source, request, manifest, pin = bundle()
    if change == 'manifest_bytes': manifest += b' '
    if change == 'manifest_pin': pin = '0' * 64
    if change == 'claim_bytes': request += b' '
    if change == 'pin_case': pin = pin.upper()
    if change == 'pin_type': pin = True
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(source, request, manifest, pin)


@pytest.mark.parametrize('change', [
    {'schema_version': True}, {'schema_version': 2}, {'analysis_allowed': 1},
    {'analysis_allowed': False}, {'source_ref': ''}, {'source_version': ''},
    {'authorization_ref': ' '}, {'source_version': 'x'*513}, {'source_ref': 'bad\nref'},
    {'scope': 'external'}, {'scope': 'own'}, {'evidence_kind': 'observed'},
    {'normalization': 'casefold'}, {'extra': True}, {'claims_sha256': 'BAD'}])
def test_manifest_is_explicit_consistent_and_bounded(change):
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(*bundle(**change))


def test_missing_manifest_fields_fail_closed():
    source, request, manifest, _pin = bundle()
    value = json.loads(manifest)
    del value['source_version']
    raw = json.dumps(value).encode()
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(source, request, raw, sha(raw))


@pytest.mark.parametrize('field', ['source', 'request', 'manifest'])
@pytest.mark.parametrize('kind', ['type', 'over_budget', 'invalid_utf8'])
def test_input_byte_and_encoding_budgets(field, kind):
    values = list(bundle())
    index = {'source': 0, 'request': 1, 'manifest': 2}[field]
    limits = [2_000_000, 524_288, 65_536]
    values[index] = 'not bytes' if kind == 'type' else (b' '*(limits[index]+1) if kind == 'over_budget' else b'\xff')
    if type(values[index]) is bytes:
        metadata = json.loads(values[2]) if field != 'manifest' else None
        if metadata is not None:
            metadata['source_sha256' if field == 'source' else 'claims_sha256'] = sha(values[index])
            values[2] = json.dumps(metadata).encode()
        values[3] = sha(values[2])
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(*values)


@pytest.mark.parametrize('payload', [b'{"a":1,"a":2}', b'[NaN]', b'[1e999]',
    b'not json', b'['*65+b'0'+b']'*65], ids=['duplicate','nan','overflow','malformed','depth'])
def test_strict_bounded_json_rejects_ambiguous_requests(payload):
    source, _request, raw, _pin = bundle()
    metadata = json.loads(raw)
    metadata['claims_sha256'] = sha(payload)
    raw = json.dumps(metadata).encode()
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(source, payload, raw, sha(raw))


@pytest.mark.parametrize('change', [
    {'claim_id': True}, {'claim_id': ''}, {'swarm_id': 'bad/id'}, {'agent_id': 'x'*129},
    {'quote_text': 7}, {'quote_text': 'x'*20001}, {'quote_text': '\ud800'},
    {'quote_kind': 'command'}, {'parent_evidence_refs': 'source:1'},
    {'parent_evidence_refs': ['same','same']}, {'parent_evidence_refs': ['bad\nref']},
    {'parent_evidence_refs': ['e'+str(i) for i in range(17)]}, {'unknown': True},
    {'source_span': [True, 2]}, {'source_span': [10, 2]}, {'source_span': [0, 9999]}])
def test_claim_schema_keeps_instructions_inert_and_offsets_bounded(change):
    source, request, _raw, _pin = bundle()
    records = json.loads(request)
    records[0].update(change)
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(*bundle(records))


@pytest.mark.parametrize('records', [[], {}, [None], [{'claim_id':'only'}],
    [{'claim_id':'repeat','swarm_id':'s','agent_id':'a','quote_text':'q','quote_kind':'direct',
      'parent_evidence_refs':[]}]*2,
    [{'claim_id':str(i),'swarm_id':'s','agent_id':'a','quote_text':'q','quote_kind':'direct',
      'parent_evidence_refs':[]} for i in range(65)]], ids=['empty','object','null','missing','duplicate','budget'])
def test_claim_collection_is_bounded_unique_and_not_silently_filtered(records):
    with pytest.raises(ValueError, match='rejected'):
        api().validate_quotation_request(*bundle(records))


def test_validated_claims_preserve_text_and_declared_lineage_without_promotion():
    values = bundle()
    manifest, claims = api().validate_quotation_request(*values)
    assert manifest == json.loads(values[2])
    assert claims == json.loads(values[1])


@pytest.mark.parametrize('field', ['source_ref', 'source_version', 'authorization_ref'])
def test_metadata_surrogates_are_rejected_without_echo(field):
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        api().validate_quotation_request(*bundle(**{field: '\ud800'}))


@pytest.mark.parametrize('field', ['source_ref', 'source_version'])
@pytest.mark.parametrize('character', ['\u0085', '\u202e', '\u2028', '\u2029', '\u200b'],
                         ids=['U+0085', 'U+202E', 'U+2028', 'U+2029', 'U+200B'])
def test_intake_and_core_reject_forbidden_unicode_labels(field, character):
    from src.models.quotation_verifier import QuotationVerifier

    values = bundle(**{field: 'operator' + character + 'suffix'})
    manifest, claims = json.loads(values[2]), json.loads(values[1])
    with pytest.raises(ValueError, match=f'^{field} must be nonblank without controls$'):
        QuotationVerifier().verify_source_quote(
            claims[0]['quote_text'], values[0], expected_sha256=manifest['source_sha256'],
            source_ref=manifest['source_ref'], source_version=manifest['source_version'])
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        api().validate_quotation_request(*values)
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        api().analyze_quotation_bundle(*values)


@pytest.mark.parametrize('character', ['\u0085', '\u202e', '\u2028', '\u2029', '\u200b'],
                         ids=['U+0085', 'U+202E', 'U+2028', 'U+2029', 'U+200B'])
def test_authorization_ref_uses_the_same_unicode_label_rule(character):
    values = bundle(authorization_ref='operator' + character + 'suffix')
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        api().validate_quotation_request(*values)


@pytest.mark.parametrize('field', ['source_ref', 'source_version', 'authorization_ref'])
@pytest.mark.parametrize('label', [' 本文:É e\u0301 Ελληνικά العربية 😀\u00a0', '😀' * 512],
                         ids=['multilingual-unmodified', '512-codepoints'])
def test_ordinary_unicode_labels_reach_the_core_without_repair(field, label):
    values = bundle(**{field: label})
    manifest, claims = api().validate_quotation_request(*values)
    assert manifest == json.loads(values[2])
    assert manifest[field].encode('utf-8') == label.encode('utf-8')
    assert claims == json.loads(values[1])
    report = api().analyze_quotation_bundle(*values)
    receipt = report['analysis']['quotation_receipts'][0]['receipt']
    assert receipt['status'] == 'exact_source_match'
    for key in ('source_ref', 'source_version'):
        assert receipt[key].encode('utf-8') == manifest[key].encode('utf-8')


def test_unicode_label_restrictions_do_not_apply_to_quote_bodies():
    quote = 'literal\u0085\u202e\u2028\u2029\u200bend'
    source = quote.encode('utf-8')
    records = json.loads(bundle()[1])
    records[0]['quote_text'] = quote
    _source, request, manifest, pin = bundle(records, source_sha256=sha(source))
    values = source, request, manifest, pin
    _manifest, claims = api().validate_quotation_request(*values)
    assert claims[0]['quote_text'].encode('utf-8') == source
    report = api().analyze_quotation_bundle(*values)
    receipt = report['analysis']['quotation_receipts'][0]['receipt']
    assert receipt['status'] == 'exact_source_match'
    assert receipt['quote_sha256'] == sha(source)
    assert receipt['source_spans'] == [{'start': 0, 'end': len(quote)}]


def test_every_manifest_key_is_required_and_json_is_strict():
    source, request, manifest, _pin = bundle()
    for key in json.loads(manifest):
        value = json.loads(manifest)
        del value[key]
        raw = json.dumps(value).encode()
        with pytest.raises(ValueError, match='^Quotation request rejected$'):
            api().validate_quotation_request(source, request, raw, sha(raw))
    raw = manifest[:-1] + b',"analysis_allowed":true}'
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        api().validate_quotation_request(source, request, raw, sha(raw))



def test_local_snapshot_reader_is_bounded_and_rejects_nonlocal_spellings(tmp_path):
    module = api()
    assert hasattr(module, 'read_local_snapshot'), 'Bounded local reader missing'
    file = tmp_path/'source.txt'
    file.write_bytes(b'local')
    assert module.read_local_snapshot(file, 5) == b'local'
    for path in ('https://example.invalid/source', '//server/share/source',
                 r'\\server\share\source', '//?/C:/source', 'C:relative',
                 'source.txt:stream', tmp_path, tmp_path/'missing'):
        with pytest.raises(ValueError, match='^Quotation request rejected$'):
            module.read_local_snapshot(path, 5)
    with pytest.raises(ValueError, match='^Quotation request rejected$'):
        module.read_local_snapshot(file, 4)
    for limit in (True, 0, -1, 2_000_001):
        with pytest.raises(ValueError, match='^Quotation request rejected$'):
            module.read_local_snapshot(file, limit)



def receipt_fixture():
    return {'status': 'exact_source_match', 'source_ref': 'fixture:source', 'source_version': 'v1',
        'source_sha256': '0'*64, 'quote_sha256': '1'*64, 'normalization': 'none',
        'source_spans': [{'start':0,'end':12}], 'offset_unit':'unicode_codepoint',
        'verifier_version':'quotation-verifier/0.2', 'coverage': {'complete':True},
        'semantic_support':'not_assessed', 'source_truth':'not_assessed',
        'deployment_authorized':False, 'requires_human_review':True}


def test_report_assembly_preserves_receipts_and_declared_lineage_without_quote_text():
    module=api()
    assert hasattr(module, '_report_from_receipts'), 'Report assembly missing'
    _source, request, raw, pin=bundle()
    manifest, claims=json.loads(raw), json.loads(request)
    receipt=receipt_fixture()
    receipt.update(source_sha256=manifest['source_sha256'], quote_sha256=sha(claims[0]['quote_text'].encode()))
    report=module._report_from_receipts(manifest, claims, [receipt], pin)
    assert set(report)=={'schema_version','producer','mode','evidence_kind','source_scope',
        'source_ref','input_sha256','manifest_sha256','analysis','execution','limitations'}
    assert report['producer']=='synoptics-defense/0.1'
    assert report['mode']=='report_only'
    assert report['input_sha256']==manifest['claims_sha256']
    assert report['manifest_sha256']==pin
    row=report['analysis']['quotation_receipts'][0]
    assert row['receipt']==receipt
    assert row['parent_evidence_refs']==claims[0]['parent_evidence_refs']
    assert row['lineage_status']=='declared_only'
    assert row['quote_kind']=='direct'
    assert report['analysis']['message_count']==1
    assert report['analysis']['agent_count']==1
    assert report['execution']=={'network_accessed':False,'actions_executed':False,'authorization_changed':False}
    assert claims[0]['quote_text'] not in json.dumps(report)
    assert 'quote_text' not in json.dumps(report)


@pytest.mark.parametrize('status,kind,flagged', [('exact_source_match','direct',False),
    ('normalized_source_match','direct',True), ('approximate_candidate','direct',True),
    ('not_found','direct',True), ('insufficient_data','direct',True),
    ('exact_source_match','paraphrase',True)])
def test_nonverbatim_and_semantic_reviews_are_visible_not_permission_changes(status,kind,flagged):
    _source, request, raw, pin=bundle()
    manifest, claims=json.loads(raw), json.loads(request)
    claims[0]['quote_kind']=kind
    receipt=receipt_fixture()
    receipt['status']=status
    receipt.update(source_sha256=manifest['source_sha256'],quote_sha256=sha(claims[0]['quote_text'].encode()))
    report=api()._report_from_receipts(manifest,claims,[receipt],pin)
    assert bool(report['analysis']['findings']) is flagged
    assert all(f['requires_human_review'] is True for f in report['analysis']['findings'])
    assert all(f['confirmed_tampering'] is False for f in report['analysis']['findings'])
    assert not any(report['execution'].values())



def test_report_drops_uncontracted_raw_receipt_fields():
    _source, request, raw, pin=bundle()
    manifest, claims=json.loads(raw),json.loads(request)
    receipt=receipt_fixture()
    receipt.update(source_sha256=manifest['source_sha256'],quote_sha256=sha(claims[0]['quote_text'].encode()))
    receipt['raw_candidate']='PRIVATE_RAW_FIXTURE'
    report=api()._report_from_receipts(manifest,claims,[receipt],pin)
    assert 'PRIVATE_RAW_FIXTURE' not in json.dumps(report)
    assert 'raw_candidate' not in json.dumps(report)



def test_real_core_produces_pinned_receipts_and_changed_quote_review():
    module=api()
    assert hasattr(module, 'analyze_quotation_bundle'), 'Core integration missing'
    original=json.loads(bundle()[1])[0]
    altered=dict(original, claim_id='c2', quote_text='The observed dose was 100 mg.')
    values=bundle([original,altered])
    report=module.analyze_quotation_bundle(*values)
    rows=report['analysis']['quotation_receipts']
    assert rows[0]['receipt']['status']=='exact_source_match'
    assert rows[1]['receipt']['status'] not in ('exact_source_match','normalized_source_match')
    assert rows[0]['receipt']['source_sha256']==sha(values[0])
    assert rows[0]['receipt']['quote_sha256']==sha(original['quote_text'].encode())
    assert rows[0]['receipt']['coverage']['truncated'] is False
    assert len(report['analysis']['findings'])==1
    assert report['analysis']['analyzer_sources'].keys()=={'quotation_review.py','quotation_verifier.py'}
    assert report==module.analyze_quotation_bundle(*values)
    assert not any(report['execution'].values())
    assert original['quote_text'] not in json.dumps(report)
    assert altered['quote_text'] not in json.dumps(report)



def cli_args(tmp_path):
    source, request, manifest, pin=bundle()
    paths={name:tmp_path/name for name in ('paper.txt','claims.json','manifest.json','report.json')}
    paths['paper.txt'].write_bytes(source)
    paths['claims.json'].write_bytes(request)
    paths['manifest.json'].write_bytes(manifest)
    return ['--source',str(paths['paper.txt']),'--claims',str(paths['claims.json']),
            '--manifest',str(paths['manifest.json']),'--manifest-sha256',pin,
            '--output',str(paths['report.json'])],paths


def test_cli_runs_real_core_writes_one_report_and_refuses_overwrite(tmp_path):
    import subprocess
    import sys
    arguments,paths=cli_args(tmp_path)
    command=[sys.executable,'-B','-m','src.pipeline.quotation_review',*arguments]
    run=subprocess.run(command,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr
    assert paths['report.json'].is_file(),'Quotation CLI did not write report'
    payload=paths['report.json'].read_bytes()
    receipt=json.loads(run.stdout)
    assert receipt['report_sha256']==sha(payload)
    assert receipt['mode']=='report_only'
    assert json.loads(payload)['analysis']['quotation_receipts'][0]['receipt']['status']=='exact_source_match'
    again=subprocess.run(command,capture_output=True,text=True,timeout=30)
    assert again.returncode==2
    assert paths['report.json'].read_bytes()==payload


@pytest.mark.parametrize('change', ['source','manifest','claims','pin','abbreviation','extra','missing'])
def test_cli_rejection_is_bounded_and_creates_no_output(tmp_path,change):
    import subprocess
    import sys
    arguments,paths=cli_args(tmp_path)
    if change in ('source','manifest','claims'):
        name={'source':'paper.txt','manifest':'manifest.json','claims':'claims.json'}[change]
        paths[name].write_bytes(paths[name].read_bytes()+b' changed')
    elif change=='pin': arguments[7]='0'*64
    elif change=='abbreviation': arguments[0]='--sour'
    elif change=='extra': arguments+=['--private-secret', 'DO_NOT_ECHO_THIS_ARGUMENT'*100]
    elif change=='missing': arguments=[]
    run=subprocess.run([sys.executable,'-B','-m','src.pipeline.quotation_review',*arguments],
                       capture_output=True,text=True,timeout=30)
    assert run.returncode==2
    assert run.stderr=='Quotation request rejected\n'
    assert run.stdout==''
    assert not paths['report.json'].exists()



def test_approximate_candidate_retains_only_numeric_review_metadata():
    source,request,_raw,_pin=bundle()
    records=json.loads(request)
    records[0]['quote_text']=source.decode().replace('10 mg','100 mg')
    report=api().analyze_quotation_bundle(*bundle(records))
    receipt=report['analysis']['quotation_receipts'][0]['receipt']
    assert receipt['status']=='approximate_candidate'
    assert receipt['candidate_spans']==[{'start':0,'end':len(source.decode())}]
    assert 0 <= receipt['candidate_similarity'] <= 1
    assert receipt['source_spans']==[]
    assert receipt['semantic_support']=='not_assessed'
