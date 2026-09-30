import urllib.request
import os
import re
from pathlib import Path

# URLs for public domain texts
BEOWULF_URL = "https://gutenberg.org/cache/epub/9701/pg9701.txt"
ARTHUR_URL = "https://gutenberg.org/cache/epub/1251/pg1251.txt"

CORPUS_DIR = Path(r"c:\Users\Vivian\Desktop\Synoptics\data\raw\medieval_corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

def download_text(url, filename):
    filepath = CORPUS_DIR / filename
    if not filepath.exists():
        print(f"Downloading {filename}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
    return filepath

def chunk_beowulf(filepath):
    """
    Beowulf is split into fitts (sections) often marked by Roman numerals (e.g. I. THE PASSING OF SCYLD or just I., II., etc.)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Regex to match Roman numerals alone or with titles: I. THE PASSING OF SCYLD.
    fitt_pattern = re.compile(r"^(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}(?:IX|IV|V?I{0,3})?|XL|L)\.(?:\s+.*)?$", re.MULTILINE)
    
    chunks = []
    matches = list(fitt_pattern.finditer(text))
    
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
    print(f"Beowulf chunked into {len(chunks)} fitts/sections.")
    if chunks:
        print("First Beowulf chunk preview:")
        preview = chunks[0][:100]
        print(preview.encode("ascii", "ignore").decode("ascii") + "...\n")
    return chunks

def chunk_arthurian(filepath):
    """
    Le Morte d'Arthur is split into Books and Chapters.
    e.g. BOOK I.
         CHAPTER I.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Split by BOOK
    book_pattern = re.compile(r"^BOOK\s+(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}(?:IX|IV|V?I{0,3})?|XL|L)\.?$", re.MULTILINE)
    chapter_pattern = re.compile(r"^CHAPTER\s+(I{1,3}|IV|V|VI{1,3}|IX|X{1,3}(?:IX|IV|V?I{0,3})?|XL|L|C|D|M|L[XVI]+|XC|CX[XVI]+|C[XVI]+|CC[XVI]+)\.?\s*", re.MULTILINE | re.IGNORECASE)
    
    books = []
    b_matches = list(book_pattern.finditer(text))
    for i in range(len(b_matches)):
        b_start = b_matches[i].start()
        b_end = b_matches[i+1].start() if i + 1 < len(b_matches) else len(text)
        book_text = text[b_start:b_end].strip()
        
        # Now chunk book into chapters
        c_matches = list(chapter_pattern.finditer(book_text))
        chapters = []
        for j in range(len(c_matches)):
            c_start = c_matches[j].start()
            c_end = c_matches[j+1].start() if j + 1 < len(c_matches) else len(book_text)
            chapter_text = book_text[c_start:c_end].strip()
            if chapter_text:
                chapters.append(chapter_text)
                
        books.append({
            'book_title': book_text.split('\n')[0].strip(),
            'chapters': chapters
        })
        
    print(f"Arthurian legend chunked into {len(books)} books.")
    total_chapters = sum(len(b['chapters']) for b in books)
    print(f"Total chapters: {total_chapters}")
    if books and books[0]['chapters']:
        print("First chapter preview:")
        preview = books[0]['chapters'][0][:100]
        print(preview.encode("ascii", "ignore").decode("ascii") + "...\n")
    return books

if __name__ == "__main__":
    beowulf_path = download_text(BEOWULF_URL, "beowulf.txt")
    arthur_path = download_text(ARTHUR_URL, "morte_d_arthur.txt")
    
    chunk_beowulf(beowulf_path)
    chunk_arthurian(arthur_path)
