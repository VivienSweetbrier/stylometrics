import sqlite3
import os
import xml.etree.ElementTree as ET
from pathlib import Path

def setup_homer_database(db_path: str):
    """Initializes the SQLite schema mirroring the Synoptic database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Tables - Keeping identical table names for downstream pipeline compatibility
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pericopes (
        id INTEGER PRIMARY KEY,
        tradition_type TEXT,
        special_m_flag BOOLEAN,
        special_l_flag BOOLEAN
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY,
        pericope_id INTEGER,
        text_source TEXT,
        verse_ref TEXT,
        position_index INTEGER,
        FOREIGN KEY(pericope_id) REFERENCES pericopes(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY,
        verse_id INTEGER,
        lemma TEXT,
        morph_tag TEXT,
        head_word_id INTEGER,
        dependency_relation TEXT,
        is_verbatim_match BOOLEAN,
        FOREIGN KEY(verse_id) REFERENCES verses(id),
        FOREIGN KEY(head_word_id) REFERENCES words(id)
    )''')

    # Pillar 3: Runtime State Management
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pericope_id INTEGER,
        node_name TEXT,
        status TEXT,
        quality_score REAL,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(pericope_id) REFERENCES pericopes(id)
    )''')

    conn.commit()
    return conn

def parse_agdt_and_load(xml_file: str, db_conn: sqlite3.Connection, text_source_name: str):
    """
    Parses an Ancient Greek Dependency Treebank (AGDT) XML file.
    Maps sentences/lines to 'verses' and tokens to 'words'.
    """
    cursor = db_conn.cursor()
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # For Homer, we might treat books or specific scenes as 'pericopes'. 
    # For now, we will create a single 'pericope' block per Book.
    current_book = None
    pericope_id = None

    for sentence in root.findall('.//sentence'):
        subdoc = sentence.get('subdoc', '') # e.g., "1.1" for Book 1, Line 1
        
        # Extract book number (naively split by dot)
        book_num = subdoc.split('.')[0] if '.' in subdoc else "Unknown"
        
        if book_num == "Unknown":
            continue
            
        if book_num != current_book:
            current_book = book_num
            # Create a new "pericope" (block/scene) for this Book
            cursor.execute('''
                INSERT INTO pericopes (tradition_type, special_m_flag, special_l_flag) 
                VALUES (?, ?, ?)
            ''', (f"{text_source_name}_Book_{book_num}", False, False))
            pericope_id = cursor.lastrowid

        verse_ref = subdoc
        position_index = int(sentence.get('id', 0))
        
        # Insert "verse" (Line)
        cursor.execute('''
            INSERT INTO verses (pericope_id, text_source, verse_ref, position_index)
            VALUES (?, ?, ?, ?)
        ''', (pericope_id, text_source_name, verse_ref, position_index))
        verse_id = cursor.lastrowid

        # Insert Words
        for word in sentence.findall('.//word'):
            word_id = word.get('id')
            lemma = word.get('lemma', '')
            morph_tag = word.get('postag', '')
            head_id = word.get('head', '')
            dep_rel = word.get('relation', '')

            # Skip punctuation which often has empty lemmas or specific tags in AGDT
            if morph_tag == 'u--------' or not lemma:
                continue

            # In a full implementation, we'd need to map local head_id to the global SQLite word.id.
            # For simplicity, we cast head_id as integer. A second pass is usually required for strict global FKs.
            head_word_id = int(head_id) if head_id and head_id.isdigit() else None

            cursor.execute('''
                INSERT INTO words (verse_id, lemma, morph_tag, head_word_id, dependency_relation, is_verbatim_match)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (verse_id, lemma, morph_tag, head_word_id, dep_rel, False))

    db_conn.commit()
    print(f"Loaded {text_source_name} into database.")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "processed"
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = data_dir / "homer.db"
    
    # 1. Initialize the Homeric database using the Synoptic schema
    conn = setup_homer_database(str(db_path))
    
    print(f"Created/Verified Homer Database at: {db_path}")
    print("\nTo load data, download the AGDT XML treebanks (e.g., tlg0012.tlg001.perseus-grc1.xml for the Iliad)")
    print("and execute the parse_agdt_and_load() function.")
    
    # 2. Parse the Treebanks
    raw_dir = base_dir / "data" / "raw"
    parse_agdt_and_load(str(raw_dir / "tlg0012.tlg001.perseus-grc1.tb.xml"), conn, "ILIAD")
    parse_agdt_and_load(str(raw_dir / "tlg0012.tlg002.perseus-grc1.tb.xml"), conn, "ODYSSEY")
    
    conn.close()
