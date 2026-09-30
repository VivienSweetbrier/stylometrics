import sqlite3
import pandas as pd
from pathlib import Path
import urllib.request
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "processed" / "hebrew.db"
TSV_URL = "https://media.githubusercontent.com/media/Clear-Bible/macula-hebrew/main/WLC/tsv/macula-hebrew.tsv"
TSV_PATH = DATA_DIR / "macula-hebrew.tsv"

def ingest_hebrew():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print("Downloading Macula Hebrew (WLC) TSV...")
    if not TSV_PATH.exists():
        urllib.request.urlretrieve(TSV_URL, TSV_PATH)
        print("Download complete.")
    else:
        print("TSV already exists.")
        
    print("Loading TSV into Pandas (this may take a moment)...")
    df = pd.read_csv(TSV_PATH, sep='\t', quoting=3, on_bad_lines='skip', low_memory=False)
    
    print("Building SQLite Database for the Hebrew Bible...")
    conn = sqlite3.connect(DB_PATH)
    
    # Standardize columns to match our Synoptics DB architecture where possible
    # In Macula Hebrew, 'xml:id' contains the verse ref (e.g., n01001001), 
    # 'lemma' contains the lexical root, and 'morph' contains the POS tagging.
    
    # We will just dump the dataframe into a clean table for now so the Stylometrist can access it.
    df.to_sql('words', conn, if_exists='replace', index=False)
    
    # Create indexes for fast querying
    conn.execute('CREATE INDEX IF NOT EXISTS idx_xml_id ON words("xml:id")')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_lemma ON words("lemma")')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_morph ON words("morph")')
    
    conn.commit()
    conn.close()
    print(f"Hebrew DB successfully built at: {DB_PATH}")

if __name__ == "__main__":
    ingest_hebrew()
