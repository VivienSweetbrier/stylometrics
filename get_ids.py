import urllib.request
import re
import urllib.parse
def get_id(query):
    url = 'https://www.gutenberg.org/ebooks/search/?query=' + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        matches = re.findall(r'href="/ebooks/(\d+)".*?title="(.*?)"', html, re.IGNORECASE)
        return [(m[0], m[1]) for m in matches[:5]]
    except Exception as e:
        return str(e)

for q in ['The Two Noble Kinsmen', 'Webster & Tourneur', 'Beaumont and Fletcher Works 8']:
    print(q, get_id(q))
