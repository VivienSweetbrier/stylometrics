import sqlite3
import argparse
import sys
import idempotency
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def needleman_wunsch(seq1, seq2, match=1, mismatch=-1, gap=-1):
    """
    Standard Needleman-Wunsch alignment algorithm for two sequences.
    """
    n, m = len(seq1), len(seq2)
    score_matrix = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        score_matrix[i][0] = i * gap
    for j in range(m + 1):
        score_matrix[0][j] = j * gap

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match_score = score_matrix[i - 1][j - 1] + (match if seq1[i - 1] == seq2[j - 1] else mismatch)
            delete = score_matrix[i - 1][j] + gap
            insert = score_matrix[i][j - 1] + gap
            score_matrix[i][j] = max(match_score, delete, insert)

    return score_matrix[n][m]

def run_sequence_alignment(db_path: str, force: bool = False):
    """
    Type-Scene DNA Alignment (Needleman-Wunsch on subset texts).
    Aligns lemma sequences across similar pericopes/verses.
    """
    logger.info(f"Connecting to database at {db_path} for Sequence Alignment")
    
    import os
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
        
    try:
        # Use idempotency setup to handle DB connection properly with WAL and timeout
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
            
            if not idempotency.check_and_update_state(conn, 'sequence_aligner', sub_task_id, force):
                continue
                
            stop_heartbeat = idempotency.start_heartbeat(db_path, 'sequence_aligner', sub_task_id)
            
            try:
                # Process the specific pericope
                cursor.execute('''
                    SELECT v.id as verse_id, w.lemma
                    FROM verses v
                    JOIN words w ON w.verse_id = v.id
                    WHERE w.lemma IS NOT NULL AND v.pericope_id = ?
                    ORDER BY v.id, w.id
                ''', (p_id,))
                
                rows = cursor.fetchall()
                sequences_by_verse = {}
                for row in rows:
                    v_id = row['verse_id']
                    lemma = row['lemma']
                    if v_id not in sequences_by_verse:
                        sequences_by_verse[v_id] = []
                    sequences_by_verse[v_id].append(lemma)
                    
                verse_ids = list(sequences_by_verse.keys())
                
                alignments = 0
                total_score = 0
                
                if len(verse_ids) >= 2:
                    # Compare the first verse against others in this pericope
                    v1 = verse_ids[0]
                    seq1 = sequences_by_verse[v1]
                    
                    for v2 in verse_ids[1:5]:  # Limit comparisons to cap runtime
                        seq2 = sequences_by_verse[v2]
                        score = needleman_wunsch(seq1, seq2)
                        alignments += 1
                        total_score += score
                        
                if alignments > 0:
                    avg_score = total_score / alignments
                    cursor.execute('''
                        INSERT INTO execution_logs (pericope_id, node_name, status, quality_score, message)
                        VALUES (?, 'Sequence Alignment', 'SUCCESS', ?, ?)
                    ''', (p_id, avg_score, f"Performed {alignments} alignments."))
                    conn.commit()
                    logger.info(f"Pericope {p_id} aligned. Avg Score: {avg_score:.2f}")
                    
                idempotency.mark_success(conn, 'sequence_aligner', sub_task_id)
                
            except Exception as e:
                logger.error(f"Error processing pericope {p_id}: {e}")
                idempotency.mark_failure(conn, 'sequence_aligner', sub_task_id)
            finally:
                stop_heartbeat.set()
                
        conn.close()
        logger.info("Sequence Alignment processing complete.")
        
    except Exception as e:
        logger.error(f"Top-level error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sequence Alignment Node")
    parser.add_argument("--db_path", required=True, help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force run ignoring state")
    args = parser.parse_args()
    
    run_sequence_alignment(args.db_path, args.force)
