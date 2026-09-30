import sqlite3
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from abc import ABC, abstractmethod

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class ParserStrategy(ABC):
    @abstractmethod
    def parse(self, text_content: str) -> list:
        """Parse raw text/content into a list of tuples: (verse_id, text_source, form, lemma, pos)"""
        pass

class TeiXmlParser(ParserStrategy):
    """
    Parses TEI XML formats typical of the Perseus Digital Library.
    Extracts words and lemmas from <w> tags.
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        words = []
        try:
            root = ET.fromstring(text_content)
            # Find all word tags. TEI often uses TEI namespace, but we'll use a broad search.
            # In Perseus, words are often <w lemma="abc" pos="def">form</w>
            for w in root.findall('.//w') + root.findall('.//{http://www.tei-c.org/ns/1.0}w'):
                form = w.text.strip() if w.text else ""
                lemma = w.get('lemma', form)
                pos = w.get('pos', 'U') # U for unknown
                
                if form:
                    words.append(("unknown", self.source_name, form, lemma, pos))
        except ET.ParseError as e:
            print(f"TEI XML Parse Error: {e}")
        return words

class CalTextParser(ParserStrategy):
    """
    Parses Comprehensive Aramaic Lexicon (CAL) style or raw text formats.
    Often used for Dead Sea Scrolls or Aramaic/Mandaic texts without XML formatting.
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        words = []
        # Mocking CAL parser logic - a simple whitespace tokenizer for now.
        # CAL format often looks like: (verse) word1 word2
        lines = text_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            for token in tokens:
                # Without deep morphology, form=lemma, pos='U'
                words.append(("unknown", self.source_name, token, token, "U"))
        return words

class ConlluParser(ParserStrategy):
    """
    Parses CONLL-U dependency trees (e.g. Coptic Scriptorium / Nag Hammadi).
    Extracts columns 1 (form), 2 (lemma), and 3 (pos).
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        words = []
        for line in text_content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 4 and '-' not in parts[0]:
                form, lemma, pos = parts[1], parts[2], parts[3]
                words.append(("unknown", self.source_name, form, lemma, pos))
        return words

class MandaicTextParser(ParserStrategy):
    """
    Parses Mandaic texts (e.g. Ginza Rabba). Mandaic text is often provided in a 
    transliterated or raw Aramaic script format.
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        words = []
        # Basic tokenization for raw Mandaic texts
        for line in text_content.strip().split('\n'):
            tokens = line.strip().split()
            for token in tokens:
                words.append(("unknown", self.source_name, token, token, "U"))
        return words

class TitusHtmlParser(ParserStrategy):
    """
    Parses TITUS project HTML format for texts like the Zend Avesta.
    Extracts words from structural HTML tags.
    """
    def __init__(self, source_name):
        self.source_name = source_name

    def parse(self, text_content: str) -> list:
        words = []
        # Uses standard regex to strip HTML tags from TITUS documents
        import re
        clean_text = re.sub(r'<[^>]+>', ' ', text_content)
        tokens = clean_text.strip().split()
        for token in tokens:
            if token.strip():
                words.append(("unknown", self.source_name, token, token, "U"))
        return words

class CorpusIngestionEngine:
    """
    Unified System Intelligence for importing Antiquity Corpora.
    Handles fetching, strategy-based parsing, and DB ingestion.
    """
    def __init__(self, db_name: str):
        self.db_path = BASE_DIR / "data" / "processed" / db_name
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id TEXT,
                text_source TEXT,
                form TEXT,
                lemma TEXT,
                pos TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def ingest(self, source_url: str, strategy: ParserStrategy, source_name: str, fallback_data: str = None):
        print(f"Ingesting {source_name} into {self.db_path.name}...")
        
        # 1. Fetch Data
        text_content = ""
        try:
            print(f"  -> Fetching data from: {source_url}")
            import warnings
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
            response = requests.get(source_url, timeout=10, verify=False)
            response.raise_for_status()
            text_content = response.text
            
            if not text_content.strip():
                raise ValueError("Endpoint returned empty response.")
                
            if "<html" in text_content.lower() or "<!doctype html" in text_content.lower():
                if "xml" not in text_content.lower(): # Basic heuristic
                    raise ValueError("Endpoint returned HTML instead of data format.")
                    
        except Exception as e:
            print(f"  -> Fetch failed ({e}).")
            if fallback_data:
                print("  -> Using fallback data.")
                text_content = fallback_data
            else:
                print("  -> No fallback provided. Aborting.")
                return
                
        # 2. Parse Data
        words = strategy.parse(text_content)
        print(f"  -> Extracted {len(words)} morphological tokens.")
        
        # 3. Store Data
        if words:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM words WHERE text_source = ?", (source_name,))
            cursor.executemany('''
                INSERT INTO words (verse_id, text_source, form, lemma, pos)
                VALUES (?, ?, ?, ?, ?)
            ''', words)
            conn.commit()
            conn.close()
            print(f"  -> Successfully committed to {self.db_path.name}.")
        else:
            print("  -> No tokens extracted. Database unchanged.")

if __name__ == "__main__":
    print("Testing Biblical Baselines (Phase 1) Ingestion...")
    
    # TEI XML Mock for Josephus
    mock_tei = """<?xml version="1.0" encoding="UTF-8"?>
    <TEI>
        <text>
            <body>
                <w lemma="ἐν" pos="PREP">ἐν</w>
                <w lemma="ἀρχή" pos="NOUN">ἀρχῇ</w>
            </body>
        </text>
    </TEI>"""
    
    engine = CorpusIngestionEngine("greek_baseline.db")
    engine.ingest(
        source_url="http://perseus.tufts.edu/mock/josephus.xml",
        strategy=TeiXmlParser("JOSEPHUS"),
        source_name="JOSEPHUS",
        fallback_data=mock_tei
    )
