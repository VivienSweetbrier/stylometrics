import sqlite3
import csv
import urllib.request
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"
MACULA_FILE = RAW_DIR / "macula-greek.tsv"

# Macula Greek TSV URL (Clear-Bible repository)
MACULA_URL = "https://raw.githubusercontent.com/Clear-Bible/macula-greek/main/SBLGNT/tsv/macula-greek-SBLGNT.tsv"

def download_macula_data():
    """Downloads the pre-aligned Macula Greek TSV if it doesn't exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not MACULA_FILE.exists():
        print(f"Downloading Macula Greek TSV from {MACULA_URL}...")
        try:
            urllib.request.urlretrieve(MACULA_URL, MACULA_FILE)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading: {e}")
            print("Please manually download the macula-greek.tsv file into data/raw/")
            return False
    else:
        print("Macula Greek TSV already exists locally.")
    return True

def ingest_to_db():
    """Parses the Macula TSV and populates the SQLite database with syntactic and morphological data."""
    if not MACULA_FILE.exists():
        print("Cannot ingest: Macula TSV missing.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Ingesting Macula Greek data into the database (Filtering for Synoptics)...")
    
    # Insert a dummy pericope for unassigned verses until we load a Gospel Parallels index
    cursor.execute("INSERT OR IGNORE INTO pericopes (id, tradition_type) VALUES (1, 'Unassigned')")
    
    word_id_map = {}     # Maps Macula's string xml_id to our integer primary keys
    head_mapping = {}    # Stores head relationships to update in a second pass

    with open(MACULA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        
        current_verse_ref = ""
        verse_id = 0
        word_pk = 1

        for row in reader:
            ref = row.get("ref", "")
            # Ensure we have a valid reference
            if not ref or len(ref) < 3:
                continue
            
            book = ref.split(" ")[0] if " " in ref else "UNK"

            # Create verse record if we've moved to a new verse
            if ref != current_verse_ref:
                current_verse_ref = ref
                verse_id += 1
                cursor.execute("""
                    INSERT OR IGNORE INTO verses (id, pericope_id, text_source, verse_ref, position_index)
                    VALUES (?, ?, ?, ?, ?)
                """, (verse_id, 1, book, ref, verse_id))

            xml_id = row.get("xml_id")
            word_id_map[xml_id] = word_pk
            
            lemma = row.get("lemma", "")
            morph = row.get("morph", "")  
            relation = row.get("relation", "")
            head_xml_id = row.get("head", "")

            # Store the head mapping to resolve after all words are inserted
            if head_xml_id:
                head_mapping[word_pk] = head_xml_id

            # Insert word
            cursor.execute("""
                INSERT OR IGNORE INTO words (id, verse_id, lemma, morph_tag, dependency_relation)
                VALUES (?, ?, ?, ?, ?)
            """, (word_pk, verse_id, lemma, morph, relation))
            
            word_pk += 1

    conn.commit()
    
    # Second pass: Update the head_word_id now that all words have internal integer primary keys
    print("Resolving and building the Syntactic Dependency Tree (PROIEL)...")
    for internal_word_id, target_xml_id in head_mapping.items():
        target_internal_id = word_id_map.get(target_xml_id)
        if target_internal_id:
            cursor.execute("""
                UPDATE words SET head_word_id = ? WHERE id = ?
            """, (target_internal_id, internal_word_id))

    conn.commit()
    conn.close()
    print("Ingestion and Syntax Tree alignment complete!")

if __name__ == "__main__":
    if download_macula_data():
        ingest_to_db()
