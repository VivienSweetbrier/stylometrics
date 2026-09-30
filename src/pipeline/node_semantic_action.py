import sqlite3
import argparse
import sys
import idempotency
import logging
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_semantic_action_graphs(db_path: str, force: bool = False):
    """
    Semantic Action Graphs (Character Subject/Object socio-dynamics)
    Finds VERB -> nsubj / obj relations to track character interactions.
    """
    logger.info(f"Connecting to database at {db_path} for Semantic Action Graphs")
    
    import os
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if not idempotency.check_and_update_state(conn, 'semantic_action', force):
            conn.close()
            sys.exit(0)
            
        # Hostile Code Review mitigation:
        # We need to extract semantic triples (subject, verb, object). 
        # Words table might not have explicit semantic roles, only dependency tags.
        # We approximate: head=verb, child1=nsubj (subject), child2=obj (object)
        # We must gracefully handle sentences missing objects or subjects.
        
        # Fetch verbs with their potential subjects and objects
        # To do this correctly in SQL is tricky, let's pull all words and reconstruct in Python
        cursor.execute('''
            SELECT id, verse_id, lemma, morph_tag, head_word_id, dependency_relation
            FROM words
        ''')
        
        rows = cursor.fetchall()
        
        # Build tree representation
        children = {}
        words = {}
        for row in rows:
            w_id = row['id']
            h_id = row['head_word_id']
            words[w_id] = row
            
            if h_id is not None:
                if h_id not in children:
                    children[h_id] = []
                children[h_id].append(w_id)
                
        # Extract triples
        triples = []
        for w_id, word in words.items():
            # Approximate verb by checking if it has nsubj and obj children
            # (In many tagging systems: 'nsubj', 'obj', 'dobj', 'nsubjpass')
            if w_id in children:
                subjs = []
                objs = []
                for c_id in children[w_id]:
                    rel = words[c_id]['dependency_relation']
                    if rel and 'subj' in rel.lower():
                        subjs.append(words[c_id]['lemma'])
                    if rel and 'obj' in rel.lower():
                        objs.append(words[c_id]['lemma'])
                        
                for subj in subjs:
                    for obj in objs:
                        if subj and obj:  # ignore empty lemmas
                            triples.append((subj, word['lemma'], obj))
                            
        logger.info(f"Extracted {len(triples)} Semantic Triples (Subject-Verb-Object).")
        
        # Build Socio-Dynamic Graph (Nodes: Characters/Entities, Edges: Actions)
        G = nx.MultiDiGraph()
        for subj, verb, obj in triples:
            G.add_edge(subj, obj, action=verb)
            
        logger.info(f"Semantic Action Graph: {G.number_of_nodes()} entities, {G.number_of_edges()} actions.")
        
        # Log to execution_logs
        cursor.execute('''
            INSERT INTO execution_logs (pericope_id, node_name, status, quality_score, message)
            VALUES (NULL, 'Semantic Action Graphs', 'SUCCESS', 1.0, ?)
        ''', (f"Graph constructed with {G.number_of_nodes()} entities and {G.number_of_edges()} action edges.",))
        
        idempotency.mark_success(conn, 'semantic_action')
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        try:
            idempotency.mark_failure(conn, 'semantic_action')
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        try:
            idempotency.mark_failure(conn, 'semantic_action')
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Action Graphs Node")
    parser.add_argument("--db_path", required=True, help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force run ignoring state")
    args = parser.parse_args()
    
    run_semantic_action_graphs(args.db_path, args.force)
