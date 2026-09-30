import os
import json
import uuid
import datetime
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "threat_queue.db"
RESULTS_DIR = BASE_DIR / "threat_results"
RESULTS_DIR.mkdir(exist_ok=True)

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            module TEXT,
            s3_key TEXT,
            text_col TEXT,
            extra_data TEXT,
            status TEXT,
            error_message TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    return conn

def upload_to_s3(file_bytes, filename):
    """Mocking S3 with local disk for Concierge mode."""
    upload_dir = BASE_DIR / "threat_uploads"
    upload_dir.mkdir(exist_ok=True)
    s3_key = f"{uuid.uuid4()}_{filename}"
    file_path = upload_dir / s3_key
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return s3_key

def queue_job(module, s3_key, text_col=None, extra_data=None):
    job_id = str(uuid.uuid4())
    conn = _get_db()
    conn.execute(
        "INSERT INTO jobs (job_id, module, s3_key, text_col, extra_data, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job_id, module, s3_key, text_col, json.dumps(extra_data or {}), "pending_review", datetime.datetime.now(datetime.timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()
    return job_id

def get_job_status(job_id):
    conn = _get_db()
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not row:
        return None
        
    status = row['status']
    error_message = row['error_message'] or ''
    
    payload = None
    if status == 'completed':
        result_path = RESULTS_DIR / f"{job_id}.json"
        if result_path.exists():
            with open(result_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
                
    return {
        'status': status,
        'result_payload': payload,
        'error_message': error_message
    }

def fetch_pending_job():
    conn = _get_db()
    # Find one approved job
    row = conn.execute("SELECT * FROM jobs WHERE status = 'approved_for_execution' LIMIT 1").fetchone()
    if row:
        job_id = row['job_id']
        conn.execute("UPDATE jobs SET status = 'processing' WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()
        return {
            'job_id': job_id,
            'module': row['module'],
            's3_key': row['s3_key'],
            'text_col': row['text_col'],
            'extra_data': json.loads(row['extra_data']) if row['extra_data'] else {}
        }
    conn.close()
    return None

def complete_job(job_id, result_payload):
    result_path = RESULTS_DIR / f"{job_id}.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_payload, f)
        
    conn = _get_db()
    conn.execute("UPDATE jobs SET status = 'completed' WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()

def fail_job(job_id, error_message):
    conn = _get_db()
    conn.execute("UPDATE jobs SET status = 'failed', error_message = ? WHERE job_id = ?", (str(error_message), job_id))
    conn.commit()
    conn.close()
