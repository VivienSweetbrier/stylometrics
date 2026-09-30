import subprocess
import json
from celery import Celery

celery_app = Celery(
    "verification_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.task_time_limit = 10
celery_app.conf.task_soft_time_limit = 8

@celery_app.task(name="execute_dagitty", bind=True)
def execute_dagitty_task(self, payload_json: str) -> dict:
    try:
        result = subprocess.run(
            ["Rscript", "evaluate_causal_topology.R", payload_json],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {
            "topological_edit_distance": -1,
            "omitted_confounders": -1,
            "reversed_edges": -1,
            "error": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"error": "R subprocess timeout"}

@celery_app.task(name="execute_lean", bind=True)
def execute_lean_task(self, lean_syntax: str) -> dict:
    try:
        result = subprocess.run(
            ["lean", "--run", "-"],
            input=lean_syntax, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return {"logical_contradiction": False, "proof_state": "verified"}
        return {"logical_contradiction": True, "proof_state": "falsified", "error_trace": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"logical_contradiction": False, "proof_state": "timeout"}
