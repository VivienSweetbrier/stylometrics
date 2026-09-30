from acquire import *
if __name__=='__main__':
 target=ROOT/'source-manifest.v2.json'
 if target.exists(): raise SystemExit('v2 already exists')
 jobs=[('ccc-sacrifice-en','https://www.vatican.va/archive/ENG0015/__P41.HTM'),('ccc-reception-en','https://www.vatican.va/archive/ENG0015/__P42.HTM'),('rc-latin-catalog','https://opendigi.ub.uni-tuebingen.de/opendigi/Gc195'),('rc-latin-ocr','https://opendigi.ub.uni-tuebingen.de/opendigi/Gc195/ocr')]
 with ThreadPoolExecutor(max_workers=4) as pool: records=list(pool.map(fetch,jobs))
 for r in records:
  if r.get('error') is None:
   r['ledger_registration']=subprocess.check_output([sys.executable,'-B',str(S),'--ledger',str(LEDGER),'add',r['url'],'--title',r['title']],text=True,encoding='utf-8').strip()
 old=json.loads((ROOT/'source-manifest.v1.json').read_bytes())
 payload=dict(old,manifest_version=2,previous_manifest_sha256=sha256((ROOT/'source-manifest.v1.json').read_bytes()).hexdigest(),records=old['records']+records,created_at_utc=datetime.now(timezone.utc).isoformat())
 target.write_bytes((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 print(json.dumps(records,ensure_ascii=False,indent=2))
