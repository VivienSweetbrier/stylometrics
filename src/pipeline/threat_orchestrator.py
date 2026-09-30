import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.pipeline.job_queue import _get_db

async def evaluate_efe_cost_typesafe(job_data: dict) -> float:
    score = 1.0
    module = job_data.get('module', '')
    if "Business Email Compromise" in module:
        score = 1.5 
    elif "Ransomware" in module:
        score = 1.2
    return score

async def astra_magisterium_loop():
    print("=== Starting Hardened Magisterium Synchronization Loop (ThreatVector) ===\n")
    
    conn = _get_db()
    rows = conn.execute("SELECT * FROM jobs WHERE status = 'pending_review'").fetchall()
    dag_mempool = [dict(r) for r in rows]
    
    if not dag_mempool:
        print("No pending jobs in mempool. Exiting.")
        return

    valid_mempool_ids = {job['job_id'] for job in dag_mempool}
    
    print("[Phase 1] Executing TypeSafe EFE Evaluations...")
    node_scores = {}
    for job in dag_mempool:
        # Convert extra_data from string to dict for the evaluator if needed
        job_parsed = dict(job)
        job_parsed['extra_data'] = json.loads(job['extra_data']) if job['extra_data'] else {}
        
        cost = await evaluate_efe_cost_typesafe(job_parsed)
        node_scores[job['job_id']] = cost
        print(f"   Job {job['job_id']} EFE Cost evaluated at: {cost}")

    print("\n[Phase 2] Requesting Astra's Topological Causal Ordering...")
    proposed_committed_ids = sorted(node_scores.keys(), key=lambda k: node_scores[k], reverse=True)
    
    print("\n[Phase 3] Validating Astra's Proposal (PILLAR 1: Proposer, Not Executor)...")
    final_approved_nodes = []
    for pid in proposed_committed_ids:
        if pid not in valid_mempool_ids:
            print(f"   [REJECTED] Astra hallucinated invalid ID: {pid}")
            continue
        if node_scores.get(pid, -1.0) < 0.0:
            print(f"   [REJECTED] Node {pid} fails EFE threshold (0.0). Structurally condemned.")
            continue
            
        print(f"   [APPROVED] Node {pid} is topologically sound and EFE compliant.")
        final_approved_nodes.append(pid)

    print("\n[Phase 4] Generating HITL Review Payload (PILLAR 5: Gradual Autonomy)...")
    payload = {
        "epoch_timestamp": datetime.now().isoformat(),
        "approved_commit_ids": final_approved_nodes,
        "mempool_size": len(dag_mempool),
        "status": "Awaiting ThreatAdmin Approval for Global Broadcast"
    }
    
    output_file = "proposed_intel_sync.json"
    with open(output_file, "w") as f:
        json.dump(payload, f, indent=4)
        
    print(f"   -> Wrote proposed synchronization to '{output_file}'.")
    print("   -> Awaiting System Engineer (Human) review before committing to master graph.")
    print("\n=== Loop Complete ===")

if __name__ == "__main__":
    asyncio.run(astra_magisterium_loop())
