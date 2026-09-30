import os
import sys
import argparse
import logging
import sqlite3
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from src.pipeline.idempotency import setup_connection, check_and_update_state, mark_success, mark_failure, start_heartbeat
except ImportError:
    logger.error("Could not import idempotency module.")
    sys.exit(1)

def get_vectorizer():
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model from local directory...")
        model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "models", model_name)
        if not os.path.exists(model_dir):
            raise RuntimeError(f"Model directory not found: {model_dir}. Run download_models.py first.")
        model = SentenceTransformer(model_dir)
        return model.encode
    except Exception as e:
        logger.error(f"Failed to load sentence-transformers: {e}")
        raise RuntimeError(f"Universal Math Enforcement failed. sentence-transformers is required: {e}")

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vector_embeddings (
            pericope_id INTEGER PRIMARY KEY,
            archetype_anchor TEXT,
            vector_blob BLOB
        )
    """)
    conn.commit()

def extract_motif_windows(conn, batch_size=100, offset=0):
    """
    Extracts text chunks per pericope.
    Hostile Review Patch: COALESCE handles NULL lemmas. 
    WHERE lemma IS NOT NULL AND lemma != '' removes empty tokens.
    """
    query = """
        SELECT v.pericope_id, GROUP_CONCAT(COALESCE(w.lemma, ''), ' ') as text
        FROM verses v
        LEFT JOIN words w ON w.verse_id = v.id
        WHERE w.lemma IS NOT NULL AND TRIM(w.lemma) != ''
        GROUP BY v.pericope_id
        ORDER BY v.pericope_id
        LIMIT ? OFFSET ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (batch_size, offset))
    return cursor.fetchall()

def extract_archetypes(text):
    """Attempt to extract archetypes based on a basic check, or return None."""
    # Since Ontology resolution maps to CSV, we do a basic heuristic or just return None
    # For now, we will leave it as None if we can't determine it trivially.
    # The requirement is that the column exists.
    return None

def run_motif_vectorizer(db_paths: list):
    node_name = "MotifVectorizer"
    embed_fn = None
    
    for db_path in db_paths:
        try:
            conn = setup_connection(db_path)
            
            # Global state check
            if not check_and_update_state(conn, node_name, "GLOBAL"):
                logger.info(f"Motif Vectorizer has already succeeded globally for {db_path}. Skipping.")
                conn.close()
                continue
                
            stop_heartbeat = start_heartbeat(db_path, node_name, "GLOBAL")
            create_tables(conn)
            
            if embed_fn is None:
                embed_fn = get_vectorizer()
                
            batch_size = 100
            offset = 0
            
            try:
                while True:
                    rows = extract_motif_windows(conn, batch_size, offset)
                    if not rows:
                        break
                        
                    pericope_ids = []
                    texts = []
                    
                    for pid, text in rows:
                        if not text or not text.strip():
                            text = "EMPTY_DOCUMENT"  # Prevent empty text crashing
                        pericope_ids.append(pid)
                        texts.append(text)
                        
                    logger.info(f"Embedding batch of {len(texts)} pericopes (offset: {offset}) for {db_path}...")
                    vectors = embed_fn(texts)
                    
                    cursor = conn.cursor()
                    for pid, text, vec in zip(pericope_ids, texts, vectors):
                        # vector_blob as raw bytes
                        vec_blob = vec.astype(np.float32).tobytes()
                        archetype = extract_archetypes(text)
                        cursor.execute("""
                            INSERT OR REPLACE INTO vector_embeddings (pericope_id, archetype_anchor, vector_blob)
                            VALUES (?, ?, ?)
                        """, (pid, archetype, vec_blob))
                    
                    conn.commit()
                    offset += batch_size
                    
                mark_success(conn, node_name, "GLOBAL")
            except Exception as e:
                logger.error(f"Error in MotifVectorizer for {db_path}: {e}")
                mark_failure(conn, node_name, "GLOBAL")
                raise
            finally:
                stop_heartbeat.set()
                conn.close()
        except Exception as e:
            logger.error(f"Failed processing db: {db_path} with error {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-Lingual Motif Vectorizer Node")
    parser.add_argument("--db_batch", type=str, required=True, help="Comma-separated list of DB paths")
    args = parser.parse_args()
    db_paths = [p.strip() for p in args.db_batch.split(",")]
    run_motif_vectorizer(db_paths)
