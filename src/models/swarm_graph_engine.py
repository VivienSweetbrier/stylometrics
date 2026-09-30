"""
SwarmGraphEngine: Directed Coordination Network & Information Cascade Engine for Agent Swarms.
Constructs directed agent-interaction graphs, calculates PageRank and Betweenness Centrality
to identify 'Queen Bee' / Coordinator hubs, and tracks Information Propagation Latency (IPL).
"""

import re
import gzip
import json
import pandas as pd
import networkx as nx
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

class SwarmGraphEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.agent_metadata = defaultdict(lambda: {
            "total_edits": 0,
            "first_seen": None,
            "last_seen": None,
            "ips": set(),
            "pages": set(),
            "labels": set()
        })
        self.page_history = defaultdict(list)

    def parse_iso_time(self, ts_str: Optional[str]) -> Optional[datetime]:
        if not ts_str:
            return None
        try:
            # Handle ISO format with Z
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def build_network_from_gz(self, gz_path: str, max_records: Optional[int] = None, temporal_window_sec: int = 7200) -> Dict[str, Any]:
        """
        Parses compressed JSONL revisions and constructs the directed agent-interaction network.
        Creates edges based on:
        1. Direct Citations: Agent A explicitly mentions Agent B in text.
        2. Co-Editing Succession: Agent B edits page X within temporal_window_sec of Agent A.
        """
        p = Path(gz_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {gz_path}")

        records = []
        known_agents = set()

        # Step 1: Collect records and catalog agent identities
        print(f"Ingesting records from {gz_path}...")
        with gzip.open(gz_path, "rt", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                if max_records and idx >= max_records:
                    break
                try:
                    rec = json.loads(line)
                    agent_name = rec.get("name")
                    if agent_name:
                        known_agents.add(agent_name)
                    records.append(rec)
                except json.JSONDecodeError:
                    continue

        # Sort chronologically
        records.sort(key=lambda r: r.get("time") or "")

        # Step 2: Build nodes and track temporal page succession
        print(f"Cataloging {len(records)} edits across {len(known_agents)} agents...")
        for rec in records:
            agent = rec.get("name")
            if not agent:
                continue

            time_dt = self.parse_iso_time(rec.get("time"))
            page_id = rec.get("page_id") or rec.get("page_key")
            ip = rec.get("ip16")
            label = rec.get("label")
            body = rec.get("body") or ""

            # Update agent profile
            meta = self.agent_metadata[agent]
            meta["total_edits"] += 1
            if ip:
                meta["ips"].add(ip)
            if page_id:
                meta["pages"].add(page_id)
            if label:
                meta["labels"].add(label)

            if time_dt:
                if meta["first_seen"] is None or time_dt < meta["first_seen"]:
                    meta["first_seen"] = time_dt
                if meta["last_seen"] is None or time_dt > meta["last_seen"]:
                    meta["last_seen"] = time_dt

            # Track page succession
            if page_id and time_dt:
                self.page_history[page_id].append({
                    "agent": agent,
                    "time": time_dt,
                    "body": body
                })

        # Add all agents as graph nodes
        for agent, meta in self.agent_metadata.items():
            self.graph.add_node(agent, 
                               total_edits=meta["total_edits"],
                               ip_count=len(meta["ips"]),
                               page_count=len(meta["pages"]))

        # Step 3: Extract Directed Edges
        print("Extracting directed coordination and citation edges...")
        edge_weights = defaultdict(lambda: {"citations": 0, "coedits": 0})

        # 3A. Direct Citations via In-Text Mentions
        # Compile regex for known agent mentions
        for rec in records:
            src_agent = rec.get("name")
            body = rec.get("body") or ""
            if not src_agent or not body:
                continue

            # Look for explicit signature citations: "-- AgentName" or mentions of other agents
            for target_agent in re.findall(r'--\s*([A-Za-z0-9_]+)', body):
                if target_agent in known_agents and target_agent != src_agent:
                    edge_weights[(src_agent, target_agent)]["citations"] += 1

        # 3B. Temporal Co-Editing Succession on the same page
        for page, history in self.page_history.items():
            # history is sorted by time
            for i in range(1, len(history)):
                prev = history[i - 1]
                curr = history[i]
                if prev["agent"] != curr["agent"]:
                    delta_sec = (curr["time"] - prev["time"]).total_seconds()
                    if 0 < delta_sec <= temporal_window_sec:
                        edge_weights[(curr["agent"], prev["agent"])]["coedits"] += 1

        # Populate graph edges
        for (u, v), counts in edge_weights.items():
            total_w = counts["citations"] * 3.0 + counts["coedits"] * 1.0
            self.graph.add_edge(u, v, 
                                weight=total_w, 
                                citations=counts["citations"], 
                                coedits=counts["coedits"])

        print(f"Network constructed: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} directed edges.")
        return self.compute_network_intelligence()

    def compute_network_intelligence(self) -> Dict[str, Any]:
        """
        Calculates PageRank, degree centrality, and unmasks top coordinator 'Queen Bee' nodes.
        """
        if self.graph.number_of_nodes() == 0:
            return {}

        # PageRank (authoritative information sources)
        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
        except Exception:
            pagerank = {n: 1.0 / self.graph.number_of_nodes() for n in self.graph.nodes()}

        in_degree = dict(self.graph.in_degree(weight="weight"))
        out_degree = dict(self.graph.out_degree(weight="weight"))

        # Rank Top Influential Hubs
        top_hubs = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:25]
        hubs_data = []
        for agent, pr in top_hubs:
            meta = self.agent_metadata[agent]
            hubs_data.append({
                "agent": agent,
                "pagerank": round(pr, 6),
                "in_citations": in_degree.get(agent, 0),
                "out_queries": out_degree.get(agent, 0),
                "total_edits": meta["total_edits"],
                "active_pages": len(meta["pages"]),
                "known_labels": list(meta["labels"])[:3]
            })

        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 6),
            "top_coordinator_hubs": hubs_data
        }

    def track_information_cascade(self, target_pattern: str, max_events: int = 30) -> Dict[str, Any]:
        """
        Traces how a specific discovery, exploit, or numerical answer cascaded across agents over time.
        Calculates first discovery timestamp, subsequent adopters, and Information Propagation Latency.
        """
        regex = re.compile(target_pattern, re.IGNORECASE)
        cascade_events = []

        for page, history in self.page_history.items():
            for entry in history:
                if regex.search(entry["body"]):
                    cascade_events.append({
                        "agent": entry["agent"],
                        "page": page,
                        "time": entry["time"],
                        "time_iso": entry["time"].isoformat() if entry["time"] else ""
                    })

        cascade_events.sort(key=lambda x: x["time"] or datetime.min)

        if not cascade_events:
            return {"pattern": target_pattern, "found": False, "events": []}

        first_discovery = cascade_events[0]
        t0 = first_discovery["time"]

        timeline = []
        seen_agents = set()

        for ev in cascade_events:
            aid = ev["agent"]
            delta_min = round((ev["time"] - t0).total_seconds() / 60.0, 2) if t0 and ev["time"] else 0.0
            is_new_adopter = aid not in seen_agents
            seen_agents.add(aid)

            timeline.append({
                "agent": aid,
                "page": ev["page"],
                "timestamp": ev["time_iso"],
                "elapsed_minutes": delta_min,
                "is_first_appearance_for_agent": is_new_adopter
            })

        adopters_count = len(seen_agents)
        total_span_hours = round((cascade_events[-1]["time"] - t0).total_seconds() / 3600.0, 2) if t0 and cascade_events[-1]["time"] else 0.0

        return {
            "pattern": target_pattern,
            "found": True,
            "origin_agent": first_discovery["agent"],
            "origin_page": first_discovery["page"],
            "origin_time": first_discovery["time"].isoformat() if first_discovery["time"] else "",
            "total_occurrences": len(cascade_events),
            "unique_adopter_agents": adopters_count,
            "total_time_span_hours": total_span_hours,
            "timeline": timeline[:max_events]
        }
