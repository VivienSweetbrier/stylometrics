"""Bounded direct public retrieval. Writes only to this research track."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import json, re, shutil, subprocess, sys
ROOT = Path(__file__).resolve().parent
S = Path('C:/Users/Vivian/AppData/Local/hermes/skills/research/grounded-citations/scripts/sources.py')
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.skip=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'): self.skip.append(tag)
        if not self.skip and tag in ('p','div','br','h1','h2','h3','h4','tr','li','hr'): self.parts.append('\n')
        if tag == 'a':
            a=dict(attrs)
            if a.get('href'): self.links.append(a['href'])
    def handle_endtag(self, tag):
        if self.skip and tag == self.skip[-1]: self.skip.pop()
        if not self.skip and tag in ('p','div','h1','h2','h3','h4','tr','li'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)
def ledger(*args):
    r=subprocess.run([sys.executable,'-B',str(S),'--ledger',str(ROOT/'sources-ledger.json'),*map(str,args)],capture_output=True,text=True,encoding='utf-8')
    if r.returncode: raise RuntimeError(r.stdout+r.stderr)
    return r.stdout.strip()
def fetch(item):
    label,url=item
    rec={'source_id':label,'requested_url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'method':'urllib.request direct public HTTPS GET; stdlib HTMLParser; collapse horizontal whitespace; preserve paragraph line breaks; UTF-8 LF text; not an edition collation'}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (bounded historical source verification)'}),timeout=45) as resp:
            raw=resp.read(5_000_001)
            if len(raw)>5_000_000: raise ValueError('5 MB acquisition bound exceeded')
            charset=resp.headers.get_content_charset(); rec.update(url=resp.geturl(),http_status=resp.status)
        if not charset:
            m=re.search(br'charset\s*=\s*["\']?([a-zA-Z0-9_-]+)',raw[:10000],re.I)
            charset=m.group(1).decode('ascii') if m else 'utf-8'
        html=raw.decode(charset,errors='strict'); p=Parser(); p.feed(html)
        text='\n'.join(re.sub(r'[ \t\r\f\v]+',' ',line).strip() for line in ''.join(p.parts).split('\n'))
        text=re.sub(r'\n{3,}','\n\n',text).strip()+'\n'
        folder=ROOT/'sources'; folder.mkdir(exist_ok=True)
        rp=folder/(label+'.html'); tp=folder/(label+'.txt')
        rp.write_bytes(raw); tp.write_bytes(text.encode('utf-8'))
        title=re.search(r'<title[^>]*>(.*?)</title>',html,re.S|re.I)
        rec.update(title=re.sub(r'\s+',' ',title.group(1)).strip() if title else label,encoding=charset,raw_path=rp.relative_to(ROOT).as_posix(),text_path=tp.relative_to(ROOT).as_posix(),raw_sha256=sha256(raw).hexdigest(),text_sha256=sha256(tp.read_bytes()).hexdigest(),raw_bytes=len(raw),text_codepoints=len(text),links=[urljoin(rec['url'],h) for h in p.links],error=None)
    except Exception as e: rec['error']=type(e).__name__+': '+str(e)
    return rec
def save(recs):
    path=ROOT/'acquisition-manifest.json'; prior=json.loads(path.read_text('utf-8')) if path.exists() else []
    existing={r['source_id'] for r in prior}
    for r in recs:
        if r['source_id'] in existing: raise ValueError('Do not overwrite frozen acquisition: '+r['source_id'])
        if r.get('error') is None: r['citation_registration']=ledger('add',r['url'],'--title',r['title'])
        prior.append(r)
    path.write_bytes((json.dumps(prior,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps([{k:v for k,v in r.items() if k not in ('links','method')} for r in recs],ensure_ascii=False,indent=2))
def copy_planning():
    manifest=Path('C:/Users/Vivian/AppData/Local/hermes/research/newman-synoptics-planning/live-source-manifest.json')
    data=json.loads(manifest.read_text('utf-8')); recs=[]
    for r in data['records']:
        if r['label'] not in ('roman-catechism-fordham','dignitatis-humanae'): continue
        out={'source_id':r['label'],'url':r['final_url'],'title':r['title'],'retrieved_at_utc':r['retrieved_at_utc'],'copied_at_utc':datetime.now(timezone.utc).isoformat(),'method':r['method']+'; hash-verified copy of planning snapshot; original CRLF bytes retained','encoding':r['encoding'],'error':None,'copy_origin_manifest':str(manifest),'copy_origin_manifest_sha256':sha256(manifest.read_bytes()).hexdigest()}
        (ROOT/'sources').mkdir(exist_ok=True)
        for typ in ('raw','text'):
            orig=Path(r[typ+'_path']); raw=orig.read_bytes()
            assert sha256(raw).hexdigest()==r[typ+'_sha256'], 'Planning pin mismatch'
            dest=ROOT/'sources'/orig.name; dest.write_bytes(raw)
            out[typ+'_path']=dest.relative_to(ROOT).as_posix();out[typ+'_sha256']=r[typ+'_sha256']
        recs.append(out)
    save(recs)
if __name__=='__main__':
    if sys.argv[1]=='copy': copy_planning()
    else:
        items=json.loads(Path(sys.argv[1]).read_text('utf-8'))
        with ThreadPoolExecutor(max_workers=4) as pool: save(list(pool.map(fetch,items)))
