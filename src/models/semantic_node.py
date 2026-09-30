import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path
import os
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HEBREW_DB = BASE_DIR / "data" / "processed" / "hebrew.db"
GREEK_DB = BASE_DIR / "data" / "processed" / "synoptics.db"

def build_verses(db_path, is_hebrew=False, limit=50):
    """Reconstructs full verses from the morphological word tables."""
    conn = sqlite3.connect(db_path)
    if is_hebrew:
        # Reconstruct Genesis 1 (n01001...)
        query = """
            SELECT "xml:id" as verse_id, group_concat(text, ' ') as text
            FROM words
            WHERE "xml:id" LIKE 'n01001%'
            GROUP BY "xml:id"
            LIMIT ?
        """
    else:
        # Reconstruct Mark 1 (MRK 1:...)
        query = """
            SELECT v.verse_ref as verse_id, group_concat(w.text, ' ') as text
            FROM words w
            JOIN verses v ON w.verse_id = v.id
            WHERE v.verse_ref LIKE 'MRK 1:%'
            GROUP BY v.id
            LIMIT ?
        """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def run_semantic_node():
    print("=== GRAPH NODE: CROSS-LINGUAL SEMANTIC SEARCH ===")
    print("Initializing Multi-lingual Vector Embeddings (MiniLM-L12)...")
    
    # Load a lightweight multi-lingual model supporting Greek and Hebrew
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    print("Extracting raw verses from SQLite databases...")
    df_heb = build_verses(HEBREW_DB, is_hebrew=True, limit=10)
    df_grk = build_verses(GREEK_DB, is_hebrew=False, limit=10)
    
    if df_heb.empty or df_grk.empty:
        print("Error: Could not reconstruct verses (ensure DB columns are correct).")
        return
        
    print(f"Extracted {len(df_heb)} Hebrew verses and {len(df_grk)} Greek verses.")
    
    # Initialize ChromaDB
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="abrahamic_synthesis")
    
    print("Embedding texts into unified vector space...")
    documents = df_heb['text'].tolist() + df_grk['text'].tolist()
    ids = df_heb['verse_id'].tolist() + df_grk['verse_id'].tolist()
    
    # Generate embeddings
    embeddings = model.encode(documents)
    
    # Add to Chroma
    collection.add(
        embeddings=embeddings.tolist(),
        documents=documents,
        ids=ids,
        metadatas=[{"lang": "hebrew"} for _ in range(len(df_heb))] + [{"lang": "greek"} for _ in range(len(df_grk))]
    )
    
    print("\n[PROTOTYPE SUCCESS: Cross-Lingual Vector DB is Online]")
    print("-> Both Hebrew and Greek verses now exist in a shared multidimensional space.")
    print("-> You can now mathematically query abstract theological concepts across languages without relying on translation.\n")

if __name__ == "__main__":
    run_semantic_node()
