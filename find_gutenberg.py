import urllib.request
import json
import urllib.parse

titles = [
    'Hamlet', 
    'A Midsummer Night''s Dream', 
    'Richard III', 
    'The Woman''s Prize', 
    'The Revenger''s Tragedy', 
    'Doctor Faustus', 
    'Essays of Francis Bacon', 
    'Henry VIII', 
    'The Two Noble Kinsmen', 
    'Edward III', 
    'Timon of Athens'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for t in titles:
    try:
        url = f'https://gutendex.com/books/?search={urllib.parse.quote(t)}'
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        found = False
        for r in data['results']:
            if r['id']:
                print(f"{t}: {r['id']} - {r['title']}")
                found = True
                break
        if not found:
            print(f"{t}: Not found")
    except Exception as e:
        print(f"{t}: Error {e}")
