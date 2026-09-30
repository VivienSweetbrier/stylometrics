import os
import sys
import glob
import subprocess
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

PHASE_1 = [
    "node_syntactic_network.py",
    "node_hmm_state.py",
    "node_semantic_action.py"
]

PHASE_2 = [
    "node_sequence_aligner.py",
    "node_ontology_resolution.py"
]

PHASE_3 = [
    "node_motif_vectorizer.py"
]

from pathlib import Path

def run_node_for_db(node_script, db_path, pipeline_dir):
    """
    Executes a single analytical node for a single database.
    """
    script_path = os.path.join(pipeline_dir, node_script)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
        
    logger.info(f"[{os.path.basename(db_path)}] Running {node_script}...")
    safe_db_path = Path(db_path).resolve().as_posix()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--db_path", safe_db_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=3600
        )
        logger.debug(f"[{os.path.basename(db_path)}] {node_script} output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[{os.path.basename(db_path)}] {node_script} failed with exit code {e.returncode}.")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired as e:
        logger.error(f"[{os.path.basename(db_path)}] {node_script} timed out.")
        return False

def run_node_for_db_batch(node_script, db_paths, pipeline_dir):
    """
    Executes a single analytical node for a batch of databases.
    """
    script_path = os.path.join(pipeline_dir, node_script)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
        
    logger.info(f"Running {node_script} for batch of {len(db_paths)} DBs...")
    safe_db_paths = [Path(db).resolve().as_posix() for db in db_paths]
    db_batch_str = ",".join(safe_db_paths)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--db_batch", db_batch_str],
            capture_output=True,
            text=True,
            check=True,
            timeout=3600
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{node_script} failed with exit code {e.returncode}.")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired as e:
        logger.error(f"{node_script} timed out.")
        return False

def run_phase(phase_nodes, db_files, pipeline_dir, max_workers, phase_name):
    logger.info(f"--- Starting {phase_name} ---")
    
    # We want to track which DBs succeeded ALL nodes in this phase
    db_success = {db: True for db in db_files}
    
    tasks = []
    for node in phase_nodes:
        for db in db_files:
            tasks.append((node, db))
            
    success_count = 0
    failure_count = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_node_for_db, node, db, pipeline_dir): (node, db) for node, db in tasks}
        
        for future in as_completed(futures):
            node, db = futures[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    db_success[db] = False
            except Exception as e:
                logger.error(f"Unhandled exception processing {node} on {db}: {e}")
                failure_count += 1
                db_success[db] = False
                
    logger.info(f"--- Completed {phase_name} | Success: {success_count}, Failure: {failure_count} ---")
    
    # Return list of active databases (those that succeeded all nodes in this phase)
    active_dbs = [db for db in db_files if db_success[db]]
    quarantined = [db for db in db_files if not db_success[db]]
    if quarantined:
        logger.warning(f"Quarantined DBs due to failures in {phase_name}: {quarantined}")
    return active_dbs

def main():
    parser = argparse.ArgumentParser(description="Macro Orchestrator for Synoptics DAG")
    parser.add_argument("--data_dir", required=True, help="Directory containing .db files")
    parser.add_argument("--pipeline_dir", required=True, help="Directory containing pipeline scripts")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of concurrent tasks")
    
    args = parser.parse_args()
    
    db_pattern = os.path.join(args.data_dir, "*.db")
    active_dbs = glob.glob(db_pattern)
    
    if not active_dbs:
        logger.warning(f"No .db files found in {args.data_dir}")
        return
        
    logger.info(f"Found {len(active_dbs)} databases to process.")
    logger.info(f"Using {args.workers} worker processes.")
    
    # PHASE 1
    active_dbs = run_phase(PHASE_1, active_dbs, args.pipeline_dir, args.workers, "Phase 1")
    if not active_dbs:
        logger.error("All DBs failed Phase 1. Halting pipeline.")
        return
        
    # WAIT BARRIER 1
    logger.info(f"PHASE 1 BARRIER REACHED. {len(active_dbs)} DBs proceeding to Phase 2.")
    
    # PHASE 2
    active_dbs = run_phase(PHASE_2, active_dbs, args.pipeline_dir, args.workers, "Phase 2")
    if not active_dbs:
        logger.error("All DBs failed Phase 2. Halting pipeline.")
        return
        
    # WAIT BARRIER 2
    logger.info(f"PHASE 2 BARRIER REACHED. {len(active_dbs)} DBs proceeding to Phase 3.")
    
    # PHASE 3 (Chunked for memory efficiency)
    logger.info("--- Starting Phase 3 ---")
    chunk_size = 5
    db_chunks = [active_dbs[i:i + chunk_size] for i in range(0, len(active_dbs), chunk_size)]
    active_dbs_phase3 = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for node in PHASE_3:
            for chunk in db_chunks:
                futures[executor.submit(run_node_for_db_batch, node, chunk, args.pipeline_dir)] = chunk
                
        for future in as_completed(futures):
            chunk = futures[future]
            try:
                success = future.result()
                if success:
                    active_dbs_phase3.extend(chunk)
            except Exception as e:
                logger.error(f"Unhandled exception in Phase 3: {e}")
                
    if not active_dbs_phase3:
        logger.error("All DBs failed Phase 3. Halting pipeline.")
        return
        
    active_dbs = active_dbs_phase3
    
    logger.info(f"PHASE 3 BARRIER REACHED. {len(active_dbs)} DBs proceeding to Phase 4.")
    
    # PHASE 4: Global Aggregation
    logger.info("--- Starting Phase 4: Global Aggregation ---")
    phylo_script = os.path.join(args.pipeline_dir, "node_phylogenetic_tree.py")
    if os.path.exists(phylo_script):
        try:
            safe_data_dir = Path(args.data_dir).resolve().as_posix()
            subprocess.run(
                [sys.executable, phylo_script, "--data_dir", safe_data_dir],
                check=True
            )
            logger.info("Phase 4 completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Phase 4 failed with exit code {e.returncode}.")
            return
    else:
        logger.error(f"Script not found: {phylo_script}")
        return
        
    logger.info("Orchestration complete. All phases finished successfully.")

if __name__ == "__main__":
    main()
