import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_command(command, description):
    print(f"\n[SYSTEM ENGINEER] Starting: {description}")
    print(f"[SYSTEM ENGINEER] Command: {command}")
    try:
        subprocess.run(command, check=True, shell=True, cwd=BASE_DIR)
        print(f"[SYSTEM ENGINEER] Success: {description}")
    except subprocess.CalledProcessError as e:
        print(f"[SYSTEM ENGINEER] Error during {description}: {e}")
        sys.exit(1)

def main():
    print("=========================================================")
    print(" FORENSIC ANTIQUITY ENGINE - FULL SYSTEM PIPELINE (v2.0) ")
    print("=========================================================")
    
    # 1. Unpack and Ingest
    run_command("python src/data_loader/unpack_and_ingest.py", "Data Extraction and Heuristic Synthesis")
    
    # 2. Intelligence Core / Report Writer (report_writer imports intelligence_core)
    run_command("python src/agents/report_writer.py", "Intelligence Core Processing and Manifesto Generation")
    
    # 3. Hypothesis Generator (10,000 vectors)
    run_command("python src/agents/hypothesis_generator.py", "Combinatorial Ideation and Disruption Scoring")
    
    # 4. Discovery Engineer
    run_command("python src/agents/discovery_engineer.py", "Global Text Discovery and Geographical Gap Analysis")
    
    print("\n[SYSTEM ENGINEER] All systems nominal. Pipeline completed successfully.")

if __name__ == "__main__":
    main()
