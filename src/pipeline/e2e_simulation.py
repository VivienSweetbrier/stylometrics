import os
import sys
import uuid
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.pipeline.job_queue import queue_job, upload_to_s3

def create_mock_csv():
    """Generates a simple mock CSV in memory for Stylometry simulation."""
    csv_content = "id,text\n"
    csv_content += "1,Please process the attached invoice for Q3.\n"
    csv_content += "2,Can you wire the vendor payment by EOD?\n"
    csv_content += "3,Invoice attached. Wire immediately. Regards.\n"
    return csv_content.encode('utf-8')

def run_simulation():
    print("=== ThreatVector E2E Architecture Simulator ===\n")
    
    print("[1] Generating Mock Threat Evidence...")
    csv_bytes = create_mock_csv()
    s3_key_1 = upload_to_s3(csv_bytes, "mock_bec_baseline.csv")
    s3_key_2 = upload_to_s3(csv_bytes, "mock_ransomware_dump.csv")
    
    print("[2] Injecting Jobs into Mempool (Pending Queue)...")
    job1 = queue_job(
        module="3. Business Email Compromise (BEC) Stylometry", 
        s3_key=s3_key_1, 
        text_col="text",
        extra_data={"suspect_text": "Hey it's the CFO. I need 50k wired to this new account ASAP."}
    )
    job2 = queue_job(
        module="1. Ransomware Group Attribution (Splinter Tracking)", 
        s3_key=s3_key_2
    )
    
    print(f"  -> Injected Job {job1} (High Priority BEC)")
    print(f"  -> Injected Job {job2} (Standard Priority)")
    
    print("\n[3] Triggering the Astra Orchestrator...")
    # Run the orchestrator script
    orchestrator_path = Path(BASE_DIR) / "src" / "pipeline" / "threat_orchestrator.py"
    subprocess.run(["python", str(orchestrator_path)])
    
    print("\n=== Simulation Paused for HITL ===")
    print("The orchestrator has evaluated the mempool and generated 'proposed_intel_sync.json'.")
    print("To complete the simulation:")
    print("  1. Inspect 'proposed_intel_sync.json' to see the AI's structural evaluation.")
    print("  2. Run: python src/pipeline/commit_mass_sync.py to approve the jobs.")
    print("  3. Ensure worker.py is running to process the final approved queue!")

if __name__ == "__main__":
    run_simulation()
