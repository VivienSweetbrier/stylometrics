import urllib.request
import json
import urllib.parse
headers = {'User-Agent': 'Mozilla/5.0'}
titles = ['Edward III', 'The Revenger''s Tragedy', 'The Woman''s Prize', 'The Two Noble Kinsmen']
for t in titles:
    try:
        url = 'https://gutendex.com/books/?search=' + urllib.parse.quote(t)
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        print(f"{t}: {[(r['id'], r['title']) for r in data['results'][:3]]}")
    except Exception as e:
        print(f"Error {t}: {e}")
