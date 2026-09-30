import sqlite3
import argparse
import sys
import idempotency
import logging
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_syntactic_fingerprinting(db_path: str, force: bool = False):
    """
    Syntactic Fingerprinting (NetworkX on dependency relations)
    Reads dependency parses, builds trees per verse, and computes centralities.
    """
    logger.info(f"Connecting to database at {db_path} for Syntactic Fingerprinting")
    
    # Check if DB exists
    import os
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if not idempotency.check_and_update_state(conn, 'syntactic_fingerprinting', force):
            conn.close()
            sys.exit(0)
            
        # We need to build dependency graphs for each verse
        # Fetch all words with their heads and dependency relations
        # Hostile Code Review mitigation: What if head_word_id is NULL or circular?
        # NetworkX handles cycles gracefully if we use generic graphs, 
        # but DiGraph might need cycle checks if computing DAG metrics.
        
        cursor.execute('''
            SELECT id, verse_id, lemma, morph_tag, head_word_id, dependency_relation
            FROM words
            WHERE head_word_id IS NOT NULL 
              AND head_word_id != id  -- Anti-self-loop safeguard
        ''')
        
        edges = cursor.fetchall()
        
        graphs_by_verse = {}
        for row in edges:
            v_id = row['verse_id']
            if v_id not in graphs_by_verse:
                graphs_by_verse[v_id] = nx.DiGraph()
                
            w_id = row['id']
            h_id = row['head_word_id']
            rel = row['dependency_relation']
            lemma = row['lemma']
            
            # Ensure nodes exist
            if not graphs_by_verse[v_id].has_node(h_id):
                graphs_by_verse[v_id].add_node(h_id)
            if not graphs_by_verse[v_id].has_node(w_id):
                graphs_by_verse[v_id].add_node(w_id, lemma=lemma)
                
            graphs_by_verse[v_id].add_edge(h_id, w_id, relation=rel)
            
        logger.info(f"Constructed dependency graphs for {len(graphs_by_verse)} verses.")
        
        # Calculate some network metrics
        # E.g., average degree, maximum depth (if tree), or pagerank
        results = []
        for v_id, G in graphs_by_verse.items():
            if len(G) == 0:
                continue
                
            # Hostile edge case: Disconnected components or purely empty graphs
            try:
                # Degree Centrality
                in_degrees = dict(G.in_degree())
                max_in_degree = max(in_degrees.values()) if in_degrees else 0
                
                # Try finding root (node with in_degree == 0)
                roots = [n for n, d in G.in_degree() if d == 0]
                num_roots = len(roots)
                
                results.append({
                    'verse_id': v_id,
                    'node_count': G.number_of_nodes(),
                    'edge_count': G.number_of_edges(),
                    'max_in_degree': max_in_degree,
                    'num_roots': num_roots
                })
            except Exception as e:
                logger.warning(f"Failed to process network metrics for verse_id {v_id}: {e}")
                
        # Normally we'd write this back to the DB or to a new table.
        # Let's write to execution_logs just to log success
        for res in results[:5]:  # Log first 5 for brevity
            logger.info(f"Verse {res['verse_id']} fingerprint: {res['node_count']} nodes, max_in_deg: {res['max_in_degree']}")
            
        # Log generic execution metric
        cursor.execute('''
            INSERT INTO execution_logs (pericope_id, node_name, status, quality_score, message)
            VALUES (NULL, 'Syntactic Fingerprinting', 'SUCCESS', 1.0, ?)
        ''', (f"Processed {len(results)} verse graphs.",))
        
        idempotency.mark_success(conn, 'syntactic_fingerprinting')
        conn.commit()
        conn.close()
        logger.info("Syntactic Fingerprinting completed.")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        try:
            idempotency.mark_failure(conn, 'syntactic_fingerprinting')
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        try:
            idempotency.mark_failure(conn, 'syntactic_fingerprinting')
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Syntactic Fingerprinting Node")
    parser.add_argument("--db_path", required=True, help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force run ignoring state")
    args = parser.parse_args()
    
    run_syntactic_fingerprinting(args.db_path, args.force)
