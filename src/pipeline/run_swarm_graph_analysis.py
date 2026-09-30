"""
Run Swarm Graph Analysis:
Constructs the directed agent network from collusion_revisions.jsonl.gz,
extracts the Top Coordinator Hubs (PageRank), and maps key Information Cascades.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.models.swarm_graph_engine import SwarmGraphEngine

def main():
    data_path = BASE_DIR / "data" / "collusion_revisions.jsonl.gz"
    output_path = BASE_DIR / "data" / "swarm_network_intel.json"

    if not data_path.exists():
        print(f"Data file not found at {data_path}")
        return

    print("=== SWARM GRAPH INTELLIGENCE ENGINE ===")
    engine = SwarmGraphEngine()
    
    # Ingest and build directed graph
    intel = engine.build_network_from_gz(str(data_path), max_records=15000)
    print(f"\n[+] Total Agents (Nodes): {intel.get('node_count')}")
    print(f"[+] Directed Coordination Edges: {intel.get('edge_count')}")
    print(f"[+] Graph Density: {intel.get('density')}")

    print("\n--- TOP 10 COORDINATOR 'QUEEN BEE' AGENTS (PAGERANK) ---")
    top_10 = intel.get("top_coordinator_hubs", [])[:10]
    for idx, hub in enumerate(top_10, 1):
        print(f"{idx}. {hub['agent']} | PageRank: {hub['pagerank']} | In-Citations: {hub['in_citations']} | Edits: {hub['total_edits']}")

    # Track Key Information Cascades
    print("\n--- TRACKING KEY INFORMATION CASCADES ---")
    cascades = {}
    
    # Target 1: The Nevada benchmark answer 20,369
    c1 = engine.track_information_cascade(r"20,369|20369")
    if c1.get("found"):
        print(f"[Cascade 1] '20,369' (Nevada Grocery Answer): Origin: {c1['origin_agent']} | Adopters: {c1['unique_adopter_agents']} | Span: {c1['total_time_span_hours']} hrs")
        cascades["nevada_answer_20369"] = c1

    # Target 2: Healthdata smoking prevalence 26.16%
    c2 = engine.track_information_cascade(r"26\.16%|26\.162")
    if c2.get("found"):
        print(f"[Cascade 2] '26.16%' (IHME Smoking SDG): Origin: {c2['origin_agent']} | Adopters: {c2['unique_adopter_agents']} | Span: {c2['total_time_span_hours']} hrs")
        cascades["smoking_sdg_26_16"] = c2

    # Target 3: SandBox Bypass / Tunnel / GET request
    c3 = engine.track_information_cascade(r"bypass|sandbox|tunnel")
    if c3.get("found"):
        print(f"[Cascade 3] 'Sandbox/Bypass/Tunnel': Origin: {c3['origin_agent']} | Adopters: {c3['unique_adopter_agents']} | Span: {c3['total_time_span_hours']} hrs")
        cascades["sandbox_bypass"] = c3

    # Save complete findings
    result_payload = {
        "network_summary": intel,
        "cascades": cascades
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2, default=str)

    print(f"\n[+] Swarm intelligence saved to {output_path}")

if __name__ == "__main__":
    main()
