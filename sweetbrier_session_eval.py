"""
sweetbrier_session_eval.py
==========================
Maps the Googology/Hypercomputational session JSON into a
StatelessSweetbrierEngine evaluation payload and runs a full
Sweetbrier pass: Cliometric Filter → Denzinger-DAG Check →
Newman Collision Resolution → Kinship (Wahkohtowin) Filter.

Run:
    python sweetbrier_session_eval.py
"""

import json
import sys
import os

# Make stateless_sweetbrier importable from its research subdirectory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "research", "doctrinal-development"))
from stateless_sweetbrier import StatelessSweetbrierEngine

# ==============================================================================
# 1. MASTER STATE
#    Built from Modelfile.Sweetbrier axioms + session's relational ontology.
#    These are the immutable constraints the agent payload is evaluated against.
# ==============================================================================

MASTER_STATE = {
    "nodes": [
        # --- Ontological axioms (Modelfile.Sweetbrier) ---
        "Logos",
        "Intrinsic Goodness of Matter",
        "Hylomorphic Unity",
        "Incarnational Flourishing",
        "Sacramental Grid",
        "Beatific Vision",
        "Redemptive Suffering",
        "Human Finitude",
        "Biological Fertility",
        "Common Good",

        # --- Session relational ontology (WAHKOTOWIN / Graph Minors alignment) ---
        "Relational Interdependence",
        "Kinship Ledger",
        "Convergent Macro-Equilibrium",
        "Forbidden Minor Detection",

        # --- Googology / hypercomputational anchors (approved vectors) ---
        "Proof-Theoretic Ordinals",
        "Turing Jump Hierarchy",
        "Ontological Expansion",
        "DAG Orchestration",
        "Probabilistic State Space Extrema",
        "Robertson-Seymour Bound",
        "SSCG Structural Alignment",
        "MCMC Convergence",
        "IRT Phase Transition",
    ],
    "edges": [
        # Core theological chain
        ["Logos",                        "Intrinsic Goodness of Matter"],
        ["Intrinsic Goodness of Matter", "Hylomorphic Unity"],
        ["Hylomorphic Unity",            "Incarnational Flourishing"],
        ["Incarnational Flourishing",    "Biological Fertility"],
        ["Incarnational Flourishing",    "Sacramental Grid"],
        ["Sacramental Grid",             "Beatific Vision"],
        ["Redemptive Suffering",         "Common Good"],

        # Relational ontology ↔ alignment chain
        ["Relational Interdependence",   "Kinship Ledger"],
        ["Kinship Ledger",               "Convergent Macro-Equilibrium"],
        ["Forbidden Minor Detection",    "Convergent Macro-Equilibrium"],

        # Googology → alignment pipeline
        ["Ontological Expansion",        "Proof-Theoretic Ordinals"],
        ["Turing Jump Hierarchy",        "Proof-Theoretic Ordinals"],
        ["Proof-Theoretic Ordinals",     "DAG Orchestration"],
        ["DAG Orchestration",            "Probabilistic State Space Extrema"],
        ["Robertson-Seymour Bound",      "SSCG Structural Alignment"],
        ["SSCG Structural Alignment",    "Forbidden Minor Detection"],
        ["MCMC Convergence",             "Probabilistic State Space Extrema"],
        ["IRT Phase Transition",         "Probabilistic State Space Extrema"],

        # Bridge: computational → relational
        ["Probabilistic State Space Extrema", "Convergent Macro-Equilibrium"],
        ["Convergent Macro-Equilibrium",      "Common Good"],
    ],
    "mutually_exclusive": [
        # Anti-natalism directly contradicts Incarnational Flourishing
        frozenset(["Anti-Natalism",           "Incarnational Flourishing"]),
        # Transhumanist Mutilation contradicts Human Finitude (which is a feature, not a bug)
        frozenset(["Transhumanist Mutilation", "Human Finitude"]),
        # Ungrounded hyperarithmetical expansion without ordinal bounding is a rupture
        frozenset(["Unbounded Rayo Expansion", "Proof-Theoretic Ordinals"]),
        # Open-ended adversarial swarm divergence contradicts forced structural alignment
        frozenset(["Adversarial Swarm Divergence", "SSCG Structural Alignment"]),
    ],
    "higher_order_principles": {
        # If Unbounded expansion collides with Ordinal Bounding, resolve via Turing Jump
        frozenset(["Unbounded Rayo Expansion", "Proof-Theoretic Ordinals"]): {
            "principle": "Turing Jump Hierarchy",
            "context_shift": (
                "Shift from syntactic cardinality to hyperarithmetical level bounding. "
                "Rayo's number is reinterpreted as a proof-theoretic ceiling, not a generative floor."
            )
        },
        # Swarm divergence vs structural alignment resolves via Robertson-Seymour
        frozenset(["Adversarial Swarm Divergence", "SSCG Structural Alignment"]): {
            "principle": "Robertson-Seymour Bound",
            "context_shift": (
                "Any infinite sequence of agent graphs must contain a minor of another. "
                "Divergence is bounded; alignment is mathematically inevitable."
            )
        },
    }
}

# ==============================================================================
# 2. SESSION PAYLOAD
#    The session JSON mapped into an EscalationPayload-compatible agent submission.
#    proposed_dag = the theoretical framework graph the agent wants to merge
#    into the master DAG.
# ==============================================================================

SESSION_PAYLOAD = json.dumps({
    "agent_id": "Agent_Googology_Session_20260920",
    "kinship_score": 7.5,  # High relational capital — sophisticated, non-adversarial proposal
    "lineage_token": "crypto_hash_hypercomp_v1",
    "proposed_dag": {
        "nodes": [
            # All four theoretical frameworks from session
            "Ontological Expansion",
            "Turing Jump Hierarchy",
            "Proof-Theoretic Ordinals",
            "Probabilistic State Space Extrema",

            # Computational implementation nodes
            "MCMC Convergence",
            "DAG Orchestration",

            # Graph-theoretic bounds
            "Robertson-Seymour Bound",
            "SSCG Structural Alignment",
            "Forbidden Minor Detection",

            # Academic bridge nodes
            "IRT Phase Transition",

            # Relational ontology bridge
            "Convergent Macro-Equilibrium",
            "Common Good",
        ],
        "edges": [
            # Turing Jump + Ontological Expansion converge on ordinal bounds
            ["Ontological Expansion",        "Proof-Theoretic Ordinals"],
            ["Turing Jump Hierarchy",        "Proof-Theoretic Ordinals"],

            # Ordinals gate DAG orchestration
            ["Proof-Theoretic Ordinals",     "DAG Orchestration"],

            # MCMC + DAG → probabilistic extrema
            ["DAG Orchestration",            "Probabilistic State Space Extrema"],
            ["MCMC Convergence",             "Probabilistic State Space Extrema"],

            # SSCG bounds the graph minor detection
            ["Robertson-Seymour Bound",      "SSCG Structural Alignment"],
            ["SSCG Structural Alignment",    "Forbidden Minor Detection"],

            # IRT models human-comprehension phase transition
            ["IRT Phase Transition",         "Probabilistic State Space Extrema"],

            # Everything converges on equilibrium → Common Good
            ["Probabilistic State Space Extrema", "Convergent Macro-Equilibrium"],
            ["Forbidden Minor Detection",         "Convergent Macro-Equilibrium"],
            ["Convergent Macro-Equilibrium",      "Common Good"],
        ]
    }
})

# ==============================================================================
# 3. RUN EVALUATION
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  SWEETBRIER ENGINE — SESSION EVALUATION")
    print("  Topic: Googology / Hypercomputational Growth / DAG Alignment")
    print("=" * 60)
    print()

    engine = StatelessSweetbrierEngine(MASTER_STATE)
    result_raw = engine.evaluate(SESSION_PAYLOAD)
    result = json.loads(result_raw)

    print(f"  Agent:        {json.loads(SESSION_PAYLOAD)['agent_id']}")
    print(f"  Kinship:      {json.loads(SESSION_PAYLOAD)['kinship_score']}")
    print()
    print("-" * 60)
    print(f"  Evaluation ID: {result['evaluation_id']}")
    print(f"  Status:        {result['status']}")
    print()
    print("  Action Sequence:")
    for i, action in enumerate(result["action_sequence"], 1):
        cmd = action.get("command", "UNKNOWN")
        payload = action.get("payload", action.get("amount", ""))
        print(f"    [{i}] {cmd}")
        if payload:
            if isinstance(payload, dict):
                print(f"         -> {json.dumps(payload, indent=10)}")
            else:
                print(f"         -> {payload}")
    print()
    print("=" * 60)
    print("  FINAL RULING:")
    status = result["status"]
    if status.startswith("APPROVED"):
        print(f"  [OK]  {status}")
        print("        The session framework is coherent with the master ontology.")
        print("        SSCG bounding + Robertson-Seymour ensure alignment is inevitable.")
    elif status.startswith("REJECTED"):
        print(f"  [!!]  {status}")
        print("        The proposed framework contains a forbidden structural vector.")
    print("=" * 60)
