#!/usr/bin/env python3
"""
SwarmTrace CLI: Digital Forensics & Threat Intelligence for Autonomous AI Swarms.
Extracts directed coordination graphs, unmasks 'Queen Bee' hubs via PageRank,
traces Information Propagation Latency (IPL) cascades, and probes for steganography.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.models.swarm_graph_engine import SwarmGraphEngine
from src.models.swarm_delta import SwarmDeltaEngine
from src.models.stegoprobe_engine import StegoProbeEngine

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SwarmTrace Forensic Intelligence Report</title>
    <style>
        body {{
            background-color: #0b0f19;
            color: #d1d5db;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 30px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 2px solid #10b981;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #10b981;
            font-size: 2.2rem;
            margin: 0 0 10px 0;
            font-family: 'Courier New', Courier, monospace;
        }}
        .subtitle {{
            color: #9ca3af;
            font-size: 1.1rem;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }}
        .metric-card {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-left: 4px solid #10b981;
            border-radius: 8px;
            padding: 20px;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #f9fafb;
            font-family: 'Courier New', Courier, monospace;
        }}
        .metric-label {{
            color: #9ca3af;
            font-size: 0.9rem;
            margin-top: 5px;
        }}
        .section {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #10b981;
            font-size: 1.4rem;
            margin-top: 0;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 0.95rem;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #1f2937;
        }}
        th {{
            background-color: #1a2234;
            color: #10b981;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #172033;
        }}
        .tag {{
            background-color: #064e3b;
            color: #34d399;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }}
        .timeline-item {{
            border-left: 2px solid #10b981;
            padding-left: 15px;
            margin-bottom: 15px;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 0.85rem;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ SwarmTrace Forensics Brief</h1>
            <div class="subtitle">Automated Coordination Network & Information Cascade Analysis</div>
            <div style="font-size: 0.85rem; color: #6b7280; margin-top: 8px;">Generated on: {timestamp} | Input Source: {input_source}</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{total_agents:,}</div>
                <div class="metric-label">Total Swarm Agents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{directed_edges:,}</div>
                <div class="metric-label">Directed Coordination Edges</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{network_density}</div>
                <div class="metric-label">Network Density</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{top_queen_bee}</div>
                <div class="metric-label">Primary Coordinator Hub</div>
            </div>
        </div>

        <div class="section">
            <h2>👑 Top Coordinator 'Queen Bee' Hubs (PageRank Centrality)</h2>
            <p style="color: #9ca3af;">These agent handles act as authoritative information routers where dispatches, answers, and bypasses converge.</p>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Agent Identifier</th>
                        <th>PageRank Score</th>
                        <th>Inbound Citations</th>
                        <th>Outbound Queries</th>
                        <th>Total Edits</th>
                    </tr>
                </thead>
                <tbody>
                    {hubs_table_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>⚡ Information Propagation Latency (IPL) Cascade Analysis</h2>
            <p style="color: #9ca3af;">Tracking diffusion velocity of high-value answers and sandbox exploits across the swarm.</p>
            {cascades_html}
        </div>

        <div class="footer">
            Generated by <strong>SwarmTrace</strong> &bull; AI Swarm Dynamics Forensics Engine &bull; Inspired by swarmchasing.com
        </div>
    </div>
</body>
</html>
"""

def generate_html_report(summary_data: dict, output_html_path: Path, input_source: str):
    net_sum = summary_data.get("network_summary", {})
    top_hubs = net_sum.get("top_coordinator_hubs", [])
    cascades = summary_data.get("cascades", {})

    # Top Queen Bee
    top_queen_bee = top_hubs[0]["agent"] if top_hubs else "N/A"

    # Hubs Table
    hubs_rows = []
    for idx, hub in enumerate(top_hubs[:15], 1):
        hubs_rows.append(f"""
        <tr>
            <td><strong>#{idx}</strong></td>
            <td><span class="tag">{hub['agent']}</span></td>
            <td>{hub['pagerank']:.6f}</td>
            <td>{hub['in_citations']}</td>
            <td>{hub['out_queries']}</td>
            <td>{hub['total_edits']}</td>
        </tr>
        """)
    hubs_table_html = "\n".join(hubs_rows)

    # Cascades HTML
    cascade_blocks = []
    for key, cdata in cascades.items():
        if not cdata.get("found"):
            continue
        timeline_rows = []
        for ev in cdata.get("timeline", [])[:10]:
            timeline_rows.append(f"""
            <div class="timeline-item">
                <span style="color: #10b981; font-family: monospace;">+{ev['elapsed_minutes']} min</span> &bull; 
                <strong>{ev['agent']}</strong> adopted on page <span class="tag">{ev['page']}</span>
                <div style="font-size: 0.8rem; color: #6b7280;">{ev['timestamp']}</div>
            </div>
            """)
        timeline_html = "".join(timeline_rows)

        cascade_blocks.append(f"""
        <div style="background-color: #1a2234; border-radius: 6px; padding: 18px; margin-bottom: 20px;">
            <h3 style="color: #34d399; margin-top: 0;">Target Token: <code>{cdata.get('pattern')}</code></h3>
            <div style="display: flex; gap: 30px; margin-bottom: 15px; font-size: 0.95rem;">
                <div><strong>Origin Agent:</strong> <span class="tag">{cdata.get('origin_agent')}</span></div>
                <div><strong>Adopters:</strong> {cdata.get('unique_adopter_agents')} agents</div>
                <div><strong>Total Span:</strong> {cdata.get('total_time_span_hours')} hrs</div>
            </div>
            <div style="margin-top: 10px;">
                <h4 style="color: #9ca3af; font-size: 0.9rem; text-transform: uppercase;">Adoption Timeline (First 10 Events):</h4>
                {timeline_html}
            </div>
        </div>
        """)
    cascades_html = "".join(cascade_blocks) if cascade_blocks else "<p>No active cascades tracked.</p>"

    html_content = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        input_source=input_source,
        total_agents=net_sum.get("node_count", 0),
        directed_edges=net_sum.get("edge_count", 0),
        network_density=f"{net_sum.get('density', 0.0):.6f}",
        top_queen_bee=top_queen_bee,
        hubs_table_rows=hubs_table_html,
        cascades_html=cascades_html
    )

    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="SwarmTrace: Autonomous AI Swarm Forensics & Network Attribution")
    parser.add_argument("--input", "-i", required=True, help="Path to input agent log file (.json, .jsonl, .jsonl.gz, .csv)")
    parser.add_argument("--out", "-o", default="data/swarm_trace_report.json", help="Path to save JSON findings")
    parser.add_argument("--html", help="Path to save standalone HTML report (e.g., reports/swarm_intel.html)")
    parser.add_argument("--track", nargs="*", default=["20,369|20369", "26.16%", "bypass|sandbox|tunnel"], help="Token patterns to trace as information cascades")
    parser.add_argument("--top-hubs", type=int, default=15, help="Number of Top Coordinator hubs to report")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    print(f"[*] Initializing SwarmTrace Engine on: {input_path}")
    graph_engine = SwarmGraphEngine()

    # Build coordination graph
    intel = graph_engine.build_network_from_gz(str(input_path))

    # Track requested cascades
    cascades = {}
    print(f"[*] Tracking {len(args.track)} information cascades...")
    for pat in args.track:
        res = graph_engine.track_information_cascade(pat)
        clean_key = pat.replace("|", "_").replace(".", "_").replace("%", "pct")
        cascades[clean_key] = res
        if res.get("found"):
            print(f"  -> Cascade '{pat}': Origin: {res['origin_agent']} | Adopters: {res['unique_adopter_agents']} | Span: {res['total_time_span_hours']}h")

    result_payload = {
        "network_summary": intel,
        "cascades": cascades
    }

    # Save JSON report
    out_json = Path(args.out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2, default=str)
    print(f"[+] JSON report saved to: {out_json}")

    # Save HTML report if requested
    if args.html:
        out_html = Path(args.html)
        generate_html_report(result_payload, out_html, str(input_path.name))
        print(f"[+] Standalone HTML report generated at: {out_html}")

    print("[*] SwarmTrace analysis complete.")

if __name__ == "__main__":
    main()
