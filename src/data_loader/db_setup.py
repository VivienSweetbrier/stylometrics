import sqlite3
import os

def setup_database(db_path: str):
    """Initializes the SQLite schema for the Synoptic Problem pipeline."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Tables
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

    # Pillar 3: Runtime State Management (The Evidence Ledger)
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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hypothesis_dags (
        hypothesis_id INTEGER PRIMARY KEY,
        hypothesis_name TEXT,
        source_node TEXT,
        target_node TEXT
    )''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

from pathlib import Path

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "processed" / "synoptics.db"
    setup_database(str(db_path))
