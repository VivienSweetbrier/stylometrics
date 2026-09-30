"""Bounded public retrieval; files restricted to this track. Not corpus certification.
Run --seed once for verified planning copies, then pass label|URL|kind requests.
Kinds: html, json, text, binary. Text decoding keeps byte-derived newlines.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources'
LEDGER = ROOT / 'sources-ledger.json'
CITER = Path('C:/Users/Vivian/AppData/Local/hermes/skills/research/grounded-citations/scripts/sources.py')
LOG = ROOT / 'acquisition-log.json'

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skips = [], []
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'):
            self.skips.append(tag)
        if not self.skips and tag in ('p','div','br','h1','h2','h3','h4','tr','li','hr'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if self.skips and tag == self.skips[-1]:
            self.skips.pop()
        if not self.skips and tag in ('p','div','h1','h2','h3','h4','tr','li'):
            self.parts.append('\n')
    def handle_data(self, data):
        if not self.skips:
            self.parts.append(data)

def record_bytes(rec, raw, text=None, extension='html'):
    rp = SOURCES / (rec['label'] + '.' + extension)
    if rp.exists():
        raise FileExistsError('Do not overwrite frozen acquisition: ' + str(rp))
    rp.write_bytes(raw)
    rec.update(raw_path=rp.relative_to(ROOT).as_posix(), raw_sha256=sha256(raw).hexdigest(), raw_bytes=len(raw))
    if text is not None:
        tp = SOURCES / (rec['label'] + '.txt')
        if tp == rp:
            tp = SOURCES / (rec['label'] + '.extracted.txt')
        data = text.encode('utf-8')
        tp.write_bytes(data)
        rec.update(text_path=tp.relative_to(ROOT).as_posix(), text_sha256=sha256(data).hexdigest(), text_codepoints=len(text), text_bytes=len(data))
    rec['error'] = None
    return rec

def fetch(item):
    label, url, kind = item
    rec = dict(label=label, requested_url=url, retrieved_at_utc=datetime.now(timezone.utc).isoformat(), kind=kind, corpus_certified=False)
    try:
        req = Request(url, headers={'User-Agent':'Mozilla/5.0 (bounded public historical research)'})
        with urlopen(req, timeout=55) as r:
            raw = r.read(45_000_001)
            if len(raw)>45_000_000:
                raise ValueError('45 MB bounded retrieval exceeded')
            rec.update(final_url=r.geturl(), http_status=r.status, headers=dict(r.headers.items()))
            charset = r.headers.get_content_charset()
        if kind == 'binary':
            ext = 'jpg' if raw.startswith(b'\xff\xd8') else 'pdf' if raw.startswith(b'%PDF') else 'bin'
            return record_bytes(rec,raw,extension=ext)
        if not charset:
            m = re.search(br'charset\s*=\s*["\']?([a-zA-Z0-9_-]+)', raw[:10000], re.I)
            charset = m.group(1).decode('ascii') if m else 'utf-8'
        decoded = raw.decode(charset,errors='strict')
        rec['encoding'] = charset
        if kind == 'html':
            p=TextParser(); p.feed(decoded)
            text='\n'.join(re.sub(r'[ \t\r\f\v]+',' ',line).strip() for line in ''.join(p.parts).split('\n'))
            text=re.sub(r'\n{3,}','\n\n',text).strip()+'\n'
            title=re.search(r'<title[^>]*>(.*?)</title>',decoded,re.I|re.S)
            rec['title']=re.sub(r'\s+',' ',title.group(1)).strip() if title else label
            rec['method']='urllib HTTPS GET, stdlib HTMLParser; tags removed, scripts/styles/noscript excluded, horizontal whitespace collapsed and blank runs limited; no OCR or semantic correction'
        else:
            text=decoded
            rec['title']=label
            rec['method']='urllib HTTPS GET; strict '+charset+' decode; no whitespace normalization; provider text/metadata retained'
        return record_bytes(rec,raw,text,extension=kind if kind in ('html','json') else 'raw.txt')
    except Exception as e:
        rec['error']=type(e).__name__+': '+str(e)
        return rec

def seed():
    base=Path('C:/Users/Vivian/AppData/Local/hermes/research/newman-synoptics-planning')
    manifest=json.loads((base/'live-source-manifest.json').read_bytes())
    out=[]
    for src in manifest['records']:
        if src['label'] not in ('newman-ch5','newman-editions'):
            continue
        raw=Path(src['raw_path']).read_bytes()
        txt=Path(src['text_path']).read_bytes()
        assert sha256(raw).hexdigest()==src['raw_sha256'], src['label']+' raw planning pin mismatch'
        assert sha256(txt).hexdigest()==src['text_sha256'], src['label']+' text planning pin mismatch'
        rec={k:v for k,v in src.items() if k not in ('raw_path','text_path')}
        rec.update(copied_at_utc=datetime.now(timezone.utc).isoformat(), copied_from='read-only planning live-evidence snapshot; compared against live-source-manifest.json', independent_pin_check=True)
        record_bytes(rec,raw,txt.decode('utf-8'),extension='html')
        assert rec['raw_sha256']==src['raw_sha256'] and rec['text_sha256']==src['text_sha256']
        out.append(rec)
    return out

if __name__=='__main__':
    SOURCES.mkdir(exist_ok=True)
    items=[arg.split('|',2) for arg in sys.argv[1:] if arg!='--seed']
    records=seed() if '--seed' in sys.argv else []
    if items:
        with ThreadPoolExecutor(max_workers=4) as pool:
            records += list(pool.map(fetch,items))
    previous=json.loads(LOG.read_bytes()) if LOG.exists() else []
    previous.extend(records)
    LOG.write_bytes((json.dumps(previous,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    for rec in records:
        if rec.get('error') is None:
            proc=subprocess.run([sys.executable,str(CITER),'--ledger',str(LEDGER),'add',rec['final_url'],'--title',rec.get('title',rec['label'])],capture_output=True,text=True,encoding='utf-8')
            print(proc.stdout.strip()); assert proc.returncode==0, proc.stderr
        print(json.dumps({k:v for k,v in rec.items() if k!='headers'},ensure_ascii=True))
