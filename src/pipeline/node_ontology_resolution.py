import sqlite3
import argparse
import sys
import os
import csv
import logging
from pathlib import Path

# Fix import path for idempotency
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import idempotency

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Hardcoded Ontology Dictionary
# Maps localized lemma strings directly to universal authoritative anchors.
# Strict mapping, no fuzzy matching.
ONTOLOGY_MAP = {
    # Characters / Archetypes
    "zeus": "[ARCHETYPE: SKY_FATHER]",
    "jupiter": "[ARCHETYPE: SKY_FATHER]",
    "odin": "[ARCHETYPE: SKY_FATHER]",
    "achilles": "[ARCHETYPE: TRAGIC_HERO]",
    "jesus": "[ARCHETYPE: SAVIOR_FIGURE]",
    "christ": "[ARCHETYPE: SAVIOR_FIGURE]",
    "prometheus": "[ARCHETYPE: TRICKSTER_CREATOR]",
    "loki": "[ARCHETYPE: TRICKSTER]",
    "enki": "[ARCHETYPE: TRICKSTER_CREATOR]",
    
    # Events
    "flood": "[EVENT: APOCALYPTIC_FLOOD]",
    "deluge": "[EVENT: APOCALYPTIC_FLOOD]",
    "ragnarok": "[EVENT: APOCALYPTIC_END]",
    "apocalypse": "[EVENT: APOCALYPTIC_END]",
    "crucifixion": "[EVENT: DIVINE_SACRIFICE]",
    
    # Objects / Themes
    "ark": "[OBJECT: SALVATION_VESSEL]",
    "boat": "[OBJECT: SALVATION_VESSEL]",
    "cross": "[OBJECT: SACRIFICIAL_ALTAR]",
    "thunderbolt": "[OBJECT: DIVINE_WEAPON]",
    "mjolnir": "[OBJECT: DIVINE_WEAPON]",
}

def export_to_csv(nodes, edges, output_dir):
    """
    Export lists of nodes and edges to Neo4j formatted CSV files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    nodes_csv = os.path.join(output_dir, "nodes.csv")
    edges_csv = os.path.join(output_dir, "edges.csv")
    
    # Append if exists, but we need headers if creating new
    nodes_exist = os.path.isfile(nodes_csv)
    edges_exist = os.path.isfile(edges_csv)
    
    try:
        with open(nodes_csv, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not nodes_exist:
                writer.writerow(["node_id", "label"])
            # Deduplicate nodes before writing
            unique_nodes = { (n['id'], n['label']) for n in nodes }
            for n_id, label in unique_nodes:
                writer.writerow([n_id, label])
                
        with open(edges_csv, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not edges_exist:
                writer.writerow(["source_node", "target_node", "relationship_type", "weight"])
            for e in edges:
                writer.writerow([e['source'], e['target'], e['type'], e['weight']])
                
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        raise

def run_ontology_resolution(db_path: str, force: bool = False):
    logger.info(f"Connecting to database at {db_path} for Ontology Resolution")
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
        
    conn = None
    stop_heartbeat = None
    
    try:
        # Use idempotency setup connection to ensure WAL mode
        conn = idempotency.setup_connection(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check idempotency state
        if not idempotency.check_and_update_state(conn, 'ontology_resolution', force=force):
            logger.info("Ontology resolution already completed. Skipping.")
            conn.close()
            return
            
        # Start heartbeat
        stop_heartbeat = idempotency.start_heartbeat(db_path, 'ontology_resolution')
        
        # Querying the database
        cursor = conn.cursor()
        
        # Hostile Code Review mitigation: Handle missing head_word_id, morph_tag
        # Use lower() on lemma for case-insensitive hardcoded map lookups, but fallback if lemma is NULL
        query = '''
            SELECT w.id, w.verse_id, w.lemma, w.head_word_id, h.lemma as head_lemma
            FROM words w
            LEFT JOIN words h ON w.head_word_id = h.id
            WHERE w.lemma IS NOT NULL
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        
        mapped_nodes = []
        mapped_edges = []
        
        # To avoid massive duplicates per row, keep track of processed entities in this run
        resolved_entities = set()
        
        for row in rows:
            lemma = row['lemma'].strip().lower()
            
            if lemma in ONTOLOGY_MAP:
                anchor = ONTOLOGY_MAP[lemma]
                
                # We have a node!
                if anchor not in resolved_entities:
                    mapped_nodes.append({'id': anchor, 'label': 'OntologyAnchor'})
                    resolved_entities.add(anchor)
                    
                # We can also map localized lemmas as nodes to link to anchors
                # Or create a link between a verse and the anchor. Let's link lemma to anchor.
                local_node_id = f"lemma_{lemma}"
                mapped_nodes.append({'id': local_node_id, 'label': 'LocalEntity'})
                
                mapped_edges.append({
                    'source': local_node_id,
                    'target': anchor,
                    'type': 'MAPS_TO',
                    'weight': 1.0
                })
                
                # If there is a head word, and it also maps, link them (co-occurrence in syntax)
                head_lemma = row['head_lemma']
                if head_lemma:
                    head_lemma_clean = head_lemma.strip().lower()
                    if head_lemma_clean in ONTOLOGY_MAP:
                        head_anchor = ONTOLOGY_MAP[head_lemma_clean]
                        mapped_edges.append({
                            'source': anchor,
                            'target': head_anchor,
                            'type': 'SYNTACTIC_RELATION',
                            'weight': 1.0
                        })

        logger.info(f"Found {len(mapped_nodes)} localized->universal mappings.")
        
        # Export to Neo4j CSVs
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, 'data', 'processed', 'global_graph')
        
        export_to_csv(mapped_nodes, mapped_edges, output_dir)
        logger.info(f"Exported mappings to {output_dir}")
        
        # Mark success
        idempotency.mark_success(conn, 'ontology_resolution')
        conn.commit()
        logger.info("Ontology resolution completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during ontology resolution: {e}")
        if conn:
            try:
                idempotency.mark_failure(conn, 'ontology_resolution')
            except Exception as e2:
                logger.error(f"Failed to mark failure: {e2}")
    finally:
        if stop_heartbeat:
            stop_heartbeat.set()
        if conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global Entity Resolution Node")
    parser.add_argument("--db_path", required=True, help="Path to SQLite database")
    parser.add_argument("--force", action="store_true", help="Force run ignoring state")
    args = parser.parse_args()
    
    run_ontology_resolution(args.db_path, args.force)
