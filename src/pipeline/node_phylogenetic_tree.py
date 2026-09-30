import os
import sys
import glob
import json
import sqlite3
import argparse
import logging
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram, to_tree
import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_tradition_name(db_path):
    basename = os.path.basename(db_path)
    name, _ = os.path.splitext(basename)
    return name.capitalize()

def extract_tradition_vectors(data_dir):
    """
    Extracts the average motif vector for each database (tradition) in the data_dir.
    Hostile Code Review:
    - What if table doesn't exist? (try/except and check schema)
    - What if table is empty? (skip)
    - What if vector sizes differ? (will throw error during stacking, but we pad or ensure they are same size. MiniLM-L12 is 384 dim, so they should be same. But let's check).
    - What if a vector is all NaN/0? (we'll sanitize).
    """
    db_pattern = os.path.join(data_dir, "*.db")
    db_files = glob.glob(db_pattern)
    
    traditions = []
    vectors = []
    
    for db_path in db_files:
        tradition = get_tradition_name(db_path)
        logger.info(f"Processing {tradition} from {db_path}...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_embeddings'")
            if not cursor.fetchone():
                logger.warning(f"No vector_embeddings table in {tradition}. Skipping.")
                continue
                
            # We query the vector and we also want a proxy for density.
            # Using the count of verses or length of text as weight. If tables are missing, we default to 1.
            try:
                cursor.execute("""
                    SELECT ve.vector_blob, 
                           COALESCE((SELECT COUNT(*) FROM verses v WHERE v.pericope_id = ve.pericope_id), 1) as weight
                    FROM vector_embeddings ve
                    WHERE ve.vector_blob IS NOT NULL
                """)
            except sqlite3.OperationalError:
                # Fallback if verses table is missing
                cursor.execute("SELECT vector_blob, 1 as weight FROM vector_embeddings WHERE vector_blob IS NOT NULL")
                
            rows = cursor.fetchall()
            if not rows:
                logger.warning(f"No vectors found in {tradition}. Skipping.")
                continue
                
            # Aggregate vectors
            db_vectors = []
            weights = []
            for (blob, weight) in rows:
                try:
                    vec = np.frombuffer(blob, dtype=np.float32)
                    
                    # Sanitize: check for NaNs or Infs
                    if not np.isfinite(vec).all():
                        logger.warning(f"Non-finite vector found in {tradition}. Skipping this pericope.")
                        continue
                        
                    # Handle all-zero vectors
                    if np.linalg.norm(vec) == 0:
                        logger.warning(f"All-zero vector found in {tradition}. Skipping this pericope.")
                        continue
                        
                    db_vectors.append(vec)
                    weights.append(weight)
                except Exception as e:
                    logger.error(f"Error parsing blob in {tradition}: {e}")
                    continue
                    
            if not db_vectors:
                logger.warning(f"No valid vectors found in {tradition} after sanitization. Skipping.")
                continue
                
            # Compute naive mathematical mean first to use as a reference point
            db_vectors_np = np.vstack(db_vectors)
            weights_np = np.array(weights).reshape(-1, 1)
            mean_vector = np.sum(db_vectors_np * weights_np, axis=0) / np.sum(weights_np)
            
            # Medoid approach: Find the actual vector closest to the mean
            # This prevents opposing semantic vectors from cancelling each other out to [0,0,0]
            distances = np.linalg.norm(db_vectors_np - mean_vector, axis=1)
            medoid_idx = np.argmin(distances)
            centroid = db_vectors_np[medoid_idx]
            
            # Normalize the centroid vector itself (L2 norm) to prevent massive texts from having skewed magnitudes
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            
            # Ensure centroid is finite and non-zero
            if not np.isfinite(centroid).all() or np.linalg.norm(centroid) == 0:
                logger.warning(f"Invalid centroid for {tradition}. Skipping.")
                continue
                
            traditions.append(tradition)
            vectors.append(centroid)
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error for {db_path}: {e}")
        finally:
            conn.close()
            
    return traditions, vectors

def build_tree_dict(node, labels):
    """
    Recursively builds a dictionary representation of the SciPy linkage tree.
    """
    if node.is_leaf():
        return {"name": labels[node.id], "id": int(node.id)}
    
    return {
        "id": int(node.id),
        "distance": float(node.dist),
        "children": [
            build_tree_dict(node.left, labels),
            build_tree_dict(node.right, labels)
        ]
    }

def run_phylogenetic_aggregation(data_dir: str):
    logger.info("Starting Global Phylogenetic Aggregation...")
    
    traditions, vectors = extract_tradition_vectors(data_dir)
    
    if len(traditions) < 2:
        logger.error(f"Not enough traditions with valid vectors to build a tree (found {len(traditions)}). Need at least 2.")
        return
        
    logger.info(f"Computing Distance Matrix for {len(traditions)} traditions...")
    
    X = np.vstack(vectors)
    
    # Compute Cosine distance
    try:
        # pdist returns condensed distance matrix
        dist_matrix = pdist(X, metric='cosine')
        
        # Sanitize dist matrix
        # Cosine distance can sometimes yield small negative numbers due to floating point inaccuracies
        dist_matrix = np.clip(dist_matrix, 0, 2)
        
        if not np.isfinite(dist_matrix).all():
            logger.error("Distance matrix contains NaNs or Infs. Cannot proceed.")
            return
            
    except Exception as e:
        logger.error(f"Failed to compute distance matrix: {e}")
        return
        
    logger.info("Computing Hierarchical Clustering (UPGMA)...")
    try:
        Z = linkage(dist_matrix, method='average')
    except Exception as e:
        logger.error(f"Failed to compute linkage: {e}")
        return
        
    # Setup export paths
    global_graph_dir = os.path.join(data_dir, "global_graph")
    os.makedirs(global_graph_dir, exist_ok=True)
    
    # 1. Export JSON Tree
    try:
        root_node, _ = to_tree(Z, rd=True)
        tree_dict = build_tree_dict(root_node, traditions)
        json_path = os.path.join(global_graph_dir, "phylogenetic_tree.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tree_dict, f, indent=2)
        logger.info(f"Exported JSON tree to {json_path}")
    except Exception as e:
        logger.error(f"Failed to export JSON tree: {e}")
        
    # 2. Render Dendrogram Image
    try:
        # Dynamically scale figure size based on number of leaves (texts)
        # Base height is 8, plus 0.3 for each additional text to prevent overlap
        fig_height = max(8, len(traditions) * 0.3)
        fig_width = 12
        
        plt.figure(figsize=(fig_width, fig_height))
        plt.title('Phylogenetic Cladogram of Textual Traditions (Semantic Motifs)')
        plt.xlabel('Cosine Distance')
        plt.ylabel('Tradition')
        
        # We plot horizontally so labels are easier to read
        dendrogram(
            Z,
            labels=traditions,
            orientation='left',
            leaf_font_size=10,
            color_threshold=0.7 * max(Z[:, 2]) # Default threshold coloring
        )
        
        plt.tight_layout()
        img_path = os.path.join(global_graph_dir, "phylogenetic_tree.png")
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Exported Dendrogram image to {img_path}")
        
    except Exception as e:
        logger.error(f"Failed to render dendrogram image: {e}")
        
    logger.info("Phylogenetic Aggregation Completed Successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global Phylogenetic Tree Aggregator")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to directory containing processed SQLite databases")
    args = parser.parse_args()
    
    run_phylogenetic_aggregation(args.data_dir)
