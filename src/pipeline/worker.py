import time
import sys
import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.pipeline.job_queue import fetch_pending_job, complete_job, fail_job
from src.data_loader.bulk_ingestor import BulkIngestor
from src.pipeline.threat_clustering import ThreatClusteringEngine
from src.agents.cyber_intelligence import CyberIntelligenceCore

def run_worker():
    print("Starting worker daemon...")
    clustering_engine = ThreatClusteringEngine(model_name='all-MiniLM-L6-v2', min_cluster_size=3)
    intelligence_core = CyberIntelligenceCore()
    ingestor = BulkIngestor()

    while True:
        job = fetch_pending_job()
        if job:
            job_id = job['job_id']
            print(f"Processing job {job_id}")
            try:
                module = job['module']
                s3_key = job['s3_key']
                text_col = job['text_col']

                # Download from S3 to temp file (Mocked as local disk copy)
                import shutil
                from src.pipeline.job_queue import BASE_DIR
                
                _, ext = os.path.splitext(s3_key)
                if not ext:
                    if module == "1. Ransomware Group Attribution (Splinter Tracking)":
                        ext = ".zip"
                    elif module in ["2. Sockpuppet Networks (Troll Farm Detection)", "3. Business Email Compromise (BEC) Stylometry"]:
                        ext = ".csv"
                        
                fd, temp_path = tempfile.mkstemp(suffix=ext)
                os.close(fd)
                
                try:
                    upload_path = BASE_DIR / "threat_uploads" / s3_key
                    shutil.copy2(upload_path, temp_path)
                    
                    if module == "1. Ransomware Group Attribution (Splinter Tracking)":
                        documents = ingestor.process_file(temp_path, "zip")
                    elif module in ["2. Sockpuppet Networks (Troll Farm Detection)", "3. Business Email Compromise (BEC) Stylometry"]:
                        if text_col:
                            ingestor.text_column = text_col
                        documents = ingestor.process_file(temp_path, "csv")
                    else:
                        raise ValueError(f"Unknown module {module}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                if module == "3. Business Email Compromise (BEC) Stylometry":
                    if len(documents) < 5:
                        raise ValueError("Need at least 5 verified emails to build a reliable baseline.")
                    suspect_text = job.get('extra_data', {}).get('suspect_text')
                    if not suspect_text:
                        raise ValueError("No suspect email text provided for stylometric analysis.")
                        
                    df_results, intel_briefs = clustering_engine.detect_stylometric_anomaly(documents, suspect_text)
                else:
                    if len(documents) < 3:
                        raise ValueError("Need at least 3 documents to form clusters.")

                    df_results = clustering_engine.cluster_documents(documents)
                    intel_briefs = intelligence_core.generate_intelligence_brief(df_results)

                # Convert dataframe to dict for json serialization
                results = {
                    'df_results': df_results.to_dict(orient='records'),
                    'intel_briefs': intel_briefs
                }

                complete_job(job_id, results)
                print(f"Completed job {job_id}")
            except Exception as e:
                print(f"Failed job {job_id}: {e}")
                fail_job(job_id, str(e))
        else:
            # fetch_pending_job blocks for 1 sec, so short sleep is enough
            time.sleep(1)

if __name__ == "__main__":
    run_worker()
