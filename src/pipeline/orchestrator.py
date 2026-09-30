import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "synoptics.db"

class SystemIntelligenceGraph:
    """
    Implements the Graph Engineering architecture for the Synoptic Pipeline.
    Manages Task Organization (DAG), Component Coordination (Nodes), and Runtime State.
    """
    def __init__(self, pericope_id):
        self.pericope_id = pericope_id
        self.state = "INIT"

    def log_state(self, node_name, status, quality_score=None, message=""):
        """Runtime State Management: Records execution evidence into the SQLite ledger."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO execution_logs (pericope_id, node_name, status, quality_score, message)
            VALUES (?, ?, ?, ?, ?)
        """, (self.pericope_id, node_name, status, quality_score, message))
        conn.commit()
        conn.close()

    def node_philologist(self):
        """
        Component Coordination: The Philologist Node
        Extracts Greek text and evaluates alignment quality.
        (Placeholder for Smith-Waterman implementation)
        """
        print(f"\n[NODE: PHILOLOGIST] Analyzing Pericope {self.pericope_id}...")
        
        # 1. Fetch Data
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT v.text_source, w.lemma 
            FROM words w JOIN verses v ON w.verse_id = v.id 
            WHERE v.pericope_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(self.pericope_id,))
        conn.close()
        
        if df.empty:
            self.log_state("PHILOLOGIST", "FAILED", message="No data found.")
            return False

        mat_len = len(df[df['text_source'] == 'MAT'])
        luk_len = len(df[df['text_source'] == 'LUK'])

        # Component Call: Execute the Philologist Engine
        from philologist import align_with_transpositions
        df_mat = df[df['text_source'] == 'MAT'].reset_index(drop=True)
        df_luk = df[df['text_source'] == 'LUK'].reset_index(drop=True)
        
        quality_score, self.Y_lexical = align_with_transpositions(df_mat, df_luk)

        print(f"  -> Extracted MAT ({mat_len} words) and LUK ({luk_len} words).")
        print(f"  -> Alignment Quality Score: {quality_score:.2f}")

        # Fault Localization (Quality Gate)
        if quality_score < 0.40:
            msg = f"Score {quality_score:.2f} too low. Possible mid-verse split or independent tradition."
            self.log_state("PHILOLOGIST", "ANOMALY_DETECTED", quality_score, msg)
            return False
            
        self.log_state("PHILOLOGIST", "SUCCESS", quality_score, "Alignment passed quality gate.")
        return True

    def node_recovery(self):
        """Fault Recovery Node: Handles anomalies detected by earlier nodes."""
        print(f"[NODE: RECOVERY] Halting downstream Bayesian models for Pericope {self.pericope_id}.")
        print("  -> Isolating corrupted pericope to prevent statistical poisoning.")
        self.log_state("RECOVERY", "RESOLVED", message="Execution halted safely.")

    def run_pipeline(self):
        """Task Organization: The execution DAG."""
        print(f"=== GRAPH EXECUTION INITIATED: Pericope {self.pericope_id} ===")
        self.log_state("ORCHESTRATOR", "STARTED")
        
        # Edge 1: Philologist Node
        alignment_valid = self.node_philologist()
        
        # Conditional Edge: Proceed to Math or Route to Recovery
        if not alignment_valid:
            print(f"\n[FAULT LOCALIZATION] Structural anomaly detected in Pericope {self.pericope_id}.")
            self.node_recovery()
        else:
            print(f"\n[NODE: STATISTICIAN] Alignment validated. Routing to Statistician...")
            self.log_state("STATISTICIAN", "RUNNING", message="Executing HMM.")
            
            from statistician_node import run_hmm_autocorrelation
            transmat = run_hmm_autocorrelation(self.Y_lexical)
            
            if transmat is not None:
                self.log_state("STATISTICIAN", "SUCCESS", message="Autocorrelation resolved.")
            else:
                self.log_state("STATISTICIAN", "FAILED", message="HMM Convergence Error.")

if __name__ == "__main__":
    # Test on Pericope 1 (The Mismatched Prologue)
    graph = SystemIntelligenceGraph(pericope_id=1)
    graph.run_pipeline()
    
    # Test on Pericope 2 (The Valid Double Tradition)
    graph = SystemIntelligenceGraph(pericope_id=2)
    graph.run_pipeline()
