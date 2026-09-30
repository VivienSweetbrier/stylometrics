import sqlite3
import argparse
import sys
import idempotency
import logging
import numpy as np
import time
from hmmlearn import hmm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_true_hmm(db_path: str, force: bool = False):
    """
    True Hidden Markov Model (Gaussian HMM)
    Maps sequences of words to hidden states like 'Rote Memorization' vs 'Improvisation'.
    """
    logger.info(f"Connecting to database at {db_path} for True HMM Analysis")
    
    import os
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
        
    try:
        conn = idempotency.setup_connection(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all distinct pericope_ids
        cursor.execute('SELECT DISTINCT pericope_id FROM verses WHERE pericope_id IS NOT NULL ORDER BY pericope_id')
        pericopes = [row['pericope_id'] for row in cursor.fetchall()]
        
        if not pericopes:
            logger.warning("No pericopes found.")
            conn.close()
            return
            
        for p_id in pericopes:
            sub_task_id = str(p_id)
            
            if not idempotency.check_and_update_state(conn, 'true_hmm', sub_task_id, force):
                continue
                
            stop_heartbeat = idempotency.start_heartbeat(db_path, 'true_hmm', sub_task_id)
            
            try:
                cursor.execute('''
                    SELECT w.verse_id, w.lemma, w.is_verbatim_match 
                    FROM words w
                    JOIN verses v ON w.verse_id = v.id
                    WHERE v.pericope_id = ?
                    ORDER BY w.verse_id, w.id
                ''', (p_id,))
                
                rows = cursor.fetchall()
                if not rows:
                    logger.warning(f"No words found in pericope {p_id}.")
                    idempotency.mark_success(conn, 'true_hmm', sub_task_id)
                    stop_heartbeat.set()
                    continue
                    
                sequences = {}
                for row in rows:
                    v_id = row['verse_id']
                    if v_id not in sequences:
                        sequences[v_id] = []
                    
                    lemma_len = len(row['lemma']) if row['lemma'] else 0
                    is_verb = 1 if row['is_verbatim_match'] else 0
                    sequences[v_id].append([lemma_len, is_verb])
                    
                X = []
                lengths = []
                for v_id, seq in sequences.items():
                    if len(seq) > 2:
                        X.extend(seq)
                        lengths.append(len(seq))
                        
                if len(lengths) == 0:
                    idempotency.mark_success(conn, 'true_hmm', sub_task_id)
                    stop_heartbeat.set()
                    continue
                    
                X_np = np.array(X, dtype=np.float64)
                X_np += np.random.normal(0, 0.01, X_np.shape)
                
                model = hmm.GaussianHMM(n_components=2, covariance_type="diag", n_iter=20, random_state=42)
                model.fit(X_np, lengths)
                
                cursor.execute('''
                    INSERT INTO execution_logs (pericope_id, node_name, status, quality_score, message)
                    VALUES (?, 'True HMM', 'SUCCESS', 1.0, ?)
                ''', (p_id, f"HMM fitted on {len(lengths)} verses in pericope {p_id}. Converged: {model.monitor_.converged}"))
                conn.commit()
                
                idempotency.mark_success(conn, 'true_hmm', sub_task_id)
                logger.info(f"Pericope {p_id} HMM completed.")
                
            except Exception as e:
                logger.error(f"Error processing pericope {p_id}: {e}")
                idempotency.mark_failure(conn, 'true_hmm', sub_task_id)
            finally:
                stop_heartbeat.set()
                
        conn.close()
        logger.info("True HMM processing complete.")
        
    except Exception as e:
        logger.error(f"Top-level error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="True HMM Node")
    parser.add_argument("--db_path", required=True, help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force run ignoring state")
    args = parser.parse_args()
    
    run_true_hmm(args.db_path, args.force)
