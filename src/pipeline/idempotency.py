import sqlite3
import time
import logging
import threading
import random

logger = logging.getLogger(__name__)

def execute_with_backoff(conn: sqlite3.Connection, query: str, params: tuple = (), max_retries: int = 5):
    """Executes a SQL query with exponential backoff for SQLite lock contentions."""
    retries = 0
    while True:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() or "busy" in str(e).lower():
                if retries >= max_retries:
                    logger.error(f"Max retries reached for query: {query}")
                    raise
                sleep_time = (2 ** retries) + random.uniform(0, 1)
                logger.warning(f"Database locked. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                retries += 1
            else:
                raise

def setup_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

def setup_state_table(conn: sqlite3.Connection):
    query = '''
        CREATE TABLE IF NOT EXISTS global_pipeline_state (
            node_name TEXT,
            sub_task_id TEXT DEFAULT 'ALL',
            status TEXT NOT NULL,
            last_updated REAL NOT NULL,
            PRIMARY KEY (node_name, sub_task_id)
        )
    '''
    execute_with_backoff(conn, query)

class HeartbeatController:
    def __init__(self, thread, stop_event, db_path):
        self.thread = thread
        self.stop_event = stop_event
        self.db_path = db_path

    def set(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            conn.close()

    def is_set(self):
        return self.stop_event.is_set()

    def wait(self, timeout=None):
        return self.stop_event.wait(timeout)

def start_heartbeat(db_path: str, node_name: str, sub_task_id: str = 'ALL'):
    stop_event = threading.Event()
    
    def heartbeat_worker():
        conn = setup_connection(db_path)
        try:
            while not stop_event.is_set():
                current_time = time.time()
                query = '''
                    UPDATE global_pipeline_state 
                    SET last_updated = ?
                    WHERE node_name = ? AND sub_task_id = ? AND status = 'RUNNING'
                '''
                execute_with_backoff(conn, query, (current_time, node_name, sub_task_id))
                stop_event.wait(60.0)
        finally:
            conn.close()

    thread = threading.Thread(target=heartbeat_worker, daemon=True)
    thread.start()
    return HeartbeatController(thread, stop_event, db_path)

def check_and_update_state(conn: sqlite3.Connection, node_name: str, sub_task_id: str = 'ALL', force: bool = False) -> bool:
    """
    Returns True if the node/sub_task should run, False if it should be skipped.
    Updates state to RUNNING if it should run.
    """
    setup_state_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT status, last_updated FROM global_pipeline_state WHERE node_name = ? AND sub_task_id = ?", (node_name, sub_task_id))
    row = cursor.fetchone()
    
    current_time = time.time()
    
    if row:
        status, last_updated = row[0], row[1]
        if status == 'SUCCESS' and not force:
            logger.info(f"Node '{node_name}' (task '{sub_task_id}') previously succeeded. Skipping.")
            return False
        if status == 'RUNNING' and not force:
            if current_time - last_updated < 180.0:
                logger.warning(f"Node '{node_name}' (task '{sub_task_id}') is currently running (heartbeat {current_time - last_updated:.1f}s ago). Skipping.")
                return False
            else:
                logger.warning(f"Node '{node_name}' (task '{sub_task_id}') is in zombie RUNNING state (heartbeat {current_time - last_updated:.1f}s ago). Forcing run.")
    
    query = '''
        INSERT INTO global_pipeline_state (node_name, sub_task_id, status, last_updated)
        VALUES (?, ?, 'RUNNING', ?)
        ON CONFLICT(node_name, sub_task_id) DO UPDATE SET status='RUNNING', last_updated=excluded.last_updated
    '''
    execute_with_backoff(conn, query, (node_name, sub_task_id, current_time))
    return True

def mark_success(conn: sqlite3.Connection, node_name: str, sub_task_id: str = 'ALL'):
    query = '''
        UPDATE global_pipeline_state 
        SET status='SUCCESS', last_updated=?
        WHERE node_name=? AND sub_task_id=?
    '''
    execute_with_backoff(conn, query, (time.time(), node_name, sub_task_id))

def mark_failure(conn: sqlite3.Connection, node_name: str, sub_task_id: str = 'ALL'):
    query = '''
        UPDATE global_pipeline_state 
        SET status='FAILED', last_updated=?
        WHERE node_name=? AND sub_task_id=?
    '''
    execute_with_backoff(conn, query, (time.time(), node_name, sub_task_id))
