"""Bounded public retrieval. Writes only this track; no corpus packages."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json, re, shutil, subprocess, sys
ROOT = Path(__file__).resolve().parent
OUT = ROOT/'sources'
S = Path('C:/Users/Vivian/AppData/Local/hermes/skills/research/grounded-citations/scripts/sources.py')
LEDGER = ROOT/'sources-ledger.json'
JOBS = [
 ('trent13-en','https://www.papalencyclicals.net/councils/trent/thirteenth-session.htm'),
 ('trent21-en','https://www.papalencyclicals.net/councils/trent/twenty-first-session.htm'),
 ('trent22-en','https://www.papalencyclicals.net/councils/trent/twenty-second-session.htm'),
 ('trent-la','https://la.wikisource.org/wiki/Concilium_Tridentinum'),
 ('sc-en','https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19631204_sacrosanctum-concilium_en.html'),
 ('sc-la','https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/vat-ii_const_19631204_sacrosanctum-concilium_lt.html'),
 ('ccc-en','https://www.vatican.va/archive/ENG0015/__P3W.HTM'),
 ('ccc-article-en','https://www.vatican.va/archive/ccc_css/archive/catechism/p2s2c1a3.htm'),
 ('ccc-la','https://www.vatican.va/archive/catechism_lt/p2s2c1a3_lt.htm'),
]
class Parser(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True); self.parts=[]; self.skips=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript'): self.skips.append(tag)
  if not self.skips and tag in ('p','div','br','h1','h2','h3','h4','tr','li','hr'): self.parts.append('\n')
 def handle_endtag(self,tag):
  if self.skips and self.skips[-1]==tag: self.skips.pop()
  if not self.skips and tag in ('p','div','h1','h2','h3','h4','tr','li'): self.parts.append('\n')
 def handle_data(self,data):
  if not self.skips: self.parts.append(data)
def fetch(job):
 sid,url=job
 r=dict(source_id=sid,requested_url=url,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),method='bounded public HTTPS GET; stdlib HTMLParser; block breaks, inline horizontal whitespace collapsed, LF UTF-8 extraction v1')
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (historical source verification)'}),timeout=45) as response:
   raw=response.read(4_000_001)
   if len(raw)>4_000_000: raise ValueError('4 MB response bound exceeded')
   r.update(url=response.geturl(),http_status=response.status,content_type=response.headers.get('Content-Type'))
   charset=response.headers.get_content_charset()
  if not charset:
   m=re.search(br'charset\s*=\s*[\"\x27]?([a-zA-Z0-9_-]+)',raw[:10000],re.I)
   charset=m.group(1).decode('ascii') if m else 'utf-8'
  html=raw.decode(charset,errors='strict'); p=Parser(); p.feed(html)
  text='\n'.join(re.sub(r'[ \t\r\f\v]+',' ',x).strip() for x in ''.join(p.parts).split('\n'))
  text=re.sub(r'\n{3,}','\n\n',text).strip()+'\n'
  tb=text.encode('utf-8'); rp=OUT/(sid+'.html'); tp=OUT/(sid+'.txt')
  rp.write_bytes(raw); tp.write_bytes(tb)
  title=re.search(r'<title[^>]*>(.*?)</title>',html,re.S|re.I)
  r.update(title=re.sub(r'\s+',' ',title.group(1)).strip() if title else sid,encoding=charset,raw_path=rp.relative_to(ROOT).as_posix(),text_path=tp.relative_to(ROOT).as_posix(),raw_sha256=sha256(raw).hexdigest(),text_sha256=sha256(tb).hexdigest(),raw_bytes=len(raw),text_bytes=len(tb),text_codepoints=len(text),error=None)
 except Exception as exc: r['error']=type(exc).__name__+': '+str(exc)
 return r
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 if (ROOT/'source-manifest.v1.json').exists(): raise SystemExit('Immutable v1 manifest exists; do not overwrite acquisition')
 original=Path('C:/Users/Vivian/AppData/Local/hermes/research/newman-synoptics-planning/live-source-manifest.json')
 manifest=json.loads(original.read_bytes().decode('utf-8'))
 old=next(r for r in manifest['records'] if r['label']=='roman-catechism-fordham')
 r=dict(source_id='rc-en',url=old['final_url'],requested_url=old['requested_url'],retrieved_at_utc=old['retrieved_at_utc'],copied_at_utc=datetime.now(timezone.utc).isoformat(),method=old['method']+'; copied byte-for-byte from read-only planning witness; original manifest pins independently rehashed before and after copy',title=old['title'],encoding=old['encoding'],error=None,upstream_manifest_path=str(original),upstream_manifest_sha256=sha256(original.read_bytes()).hexdigest())
 for kind,ext in [('raw','html'),('text','txt')]:
  data=Path(old[kind+'_path']).read_bytes()
  assert sha256(data).hexdigest()==old[kind+'_sha256'], 'upstream pin changed'
  target=OUT/('rc-en.'+ext); target.write_bytes(data)
  assert sha256(target.read_bytes()).hexdigest()==old[kind+'_sha256']
  r[kind+'_path']=target.relative_to(ROOT).as_posix(); r[kind+'_sha256']=old[kind+'_sha256']; r[kind+'_bytes']=len(data)
 r['text_codepoints']=len((ROOT/r['text_path']).read_bytes().decode('utf-8'))
 with ThreadPoolExecutor(max_workers=4) as pool: records=[r]+list(pool.map(fetch,JOBS))
 for record in records:
  if record.get('error') is None:
   result=subprocess.run([sys.executable,'-B',str(S),'--ledger',str(LEDGER),'add',record['url'],'--title',record['title']],capture_output=True,text=True,encoding='utf-8')
   if result.returncode: raise RuntimeError(result.stderr)
   record['ledger_registration']=result.stdout.strip()
 payload=dict(manifest_version=1,track='eucharist',created_at_utc=datetime.now(timezone.utc).isoformat(),scope='Research snapshots, not authenticated first editions or semantic adjudication.',records=records)
 (ROOT/'source-manifest.v1.json').write_bytes((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 print(json.dumps([dict(source_id=x['source_id'],url=x.get('url'),bytes=x.get('text_bytes'),error=x.get('error'),citation=x.get('ledger_registration')) for x in records],indent=2))
