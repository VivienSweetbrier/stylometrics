import os
import urllib.request
import re
import time

corpus_dir = r"c:\Users\Vivian\Desktop\Synoptics\data\raw\early_modern_corpus"
os.makedirs(corpus_dir, exist_ok=True)

# IDs for the texts
texts = {
    "Hamlet": 1524,
    "A Midsummer Night's Dream": 1514,
    "Richard III": 1506,
    "Doctor Faustus": 811,
    "Essays of Francis Bacon": 575,
    "Henry VIII": 1533,
    "The Two Noble Kinsmen": 1542,
    "Edward III": 1770,
    "Timon of Athens": 1530,
    "The Woman's Prize": 35303,
    "The Revenger's Tragedy": 55625
}

def strip_gutenberg_boilerplate(text):
    start_match = re.search(r'\*\*\*\s*START OF TH(?:E|IS) PROJECT GUTENBERG EBOOK.*?\*\*\*', text, re.IGNORECASE)
    if start_match:
        text = text[start_match.end():]
    
    end_match = re.search(r'\*\*\*\s*END OF TH(?:E|IS) PROJECT GUTENBERG EBOOK.*?\*\*\*', text, re.IGNORECASE)
    if end_match:
        text = text[:end_match.start()]
        
    return text.strip()

for title, gid in texts.items():
    print(f"Downloading {title}...")
    url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            clean_content = strip_gutenberg_boilerplate(content)
            filename = title.replace(" ", "_").replace("'", "").lower() + ".txt"
            filepath = os.path.join(corpus_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            print(f"Saved {title} to {filename}")
    except Exception as e:
        print(f"Error downloading {title} from {url}: {e}")
        try:
            url2 = f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt"
            req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2) as response:
                content = response.read().decode('utf-8')
                clean_content = strip_gutenberg_boilerplate(content)
                filename = title.replace(" ", "_").replace("'", "").lower() + ".txt"
                filepath = os.path.join(corpus_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(clean_content)
                print(f"Saved {title} to {filename} (via fallback URL)")
        except Exception as e2:
            print(f"Error downloading {title} via fallback {url2}: {e2}")
    time.sleep(1) # Be polite to Gutenberg servers
