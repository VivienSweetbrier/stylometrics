import os
import zipfile
import tempfile
import threading
import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.data_loader.bulk_ingestor import BulkIngestor
from src.pipeline import job_queue

def test_zip_bomb():
    ingestor = BulkIngestor()
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "bomb.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i in range(10001):
                zipf.writestr(f"file_{i}.txt", "dummy content")
        
        with pytest.raises(ValueError, match="Too many files in ZIP"):
            ingestor.ingest_zip(zip_path)

def test_csv_row_limit():
    ingestor = BulkIngestor(text_column="text")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "large.csv")
        # generate 55000 rows
        df = pd.DataFrame({"text": [f"row {i}" for i in range(55000)]})
        df.to_csv(csv_path, index=False)
        
        docs = ingestor.ingest_csv(csv_path)
        assert len(docs) == 50000

def test_job_queue_concurrency():
    # Setup test DB
    job_queue.DB_PATH = Path("data/test_cyber_jobs.db")
    if job_queue.DB_PATH.exists():
        job_queue.DB_PATH.unlink()
    job_queue.init_db()
    
    # Queue exactly 1 job
    job_queue.queue_job("test_module", "test_path", "text")
    
    results = []
    
    def worker():
        try:
            job = job_queue.fetch_pending_job()
            results.append(job)
        except sqlite3.OperationalError as e:
            results.append(e)
            
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    # Check results
    jobs_received = [r for r in results if r is not None and not isinstance(r, Exception)]
    nones_received = [r for r in results if r is None]
    errors_received = [r for r in results if isinstance(r, Exception)]
    
    assert len(jobs_received) == 1
    # We might have DB lock errors, which would mean our concurrency test needs to adjust connect timeout.
    # But ideally, exactly 1 thread gets the job and others get None (or maybe fail, but we'll see).
    # Since we use RETURNING it's one statement, very fast.
    assert len(nones_received) == 9
    assert len(errors_received) == 0

    if job_queue.DB_PATH.exists():
        job_queue.DB_PATH.unlink()
