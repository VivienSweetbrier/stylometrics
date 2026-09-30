import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.pipeline.job_queue import _get_db

def commit_mass_sync():
    sync_file = "proposed_intel_sync.json"
    if not os.path.exists(sync_file):
        print(f"Error: {sync_file} not found. Run threat_orchestrator.py first.")
        return

    with open(sync_file, 'r') as f:
        payload = json.load(f)

    approved_ids = payload.get("approved_commit_ids", [])
    if not approved_ids:
        print("No approved jobs to commit.")
        return

    print(f"Committing {len(approved_ids)} approved Threat Intel jobs to the execution queue...")
    
    conn = _get_db()
    for job_id in approved_ids:
        conn.execute("UPDATE jobs SET status = 'approved_for_execution' WHERE job_id = ?", (job_id,))
        print(f"  [COMMITTED] Job {job_id}")

    conn.commit()
    conn.close()

    os.remove(sync_file)
    print("\n=== Mass Sync Complete. Workers will now process these jobs. ===")

if __name__ == "__main__":
    commit_mass_sync()
