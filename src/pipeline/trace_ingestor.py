"""
TraceIngestor: Ingestion and normalization pipeline for multi-agent swarm transcripts.
Supports AI Village transcripts, JSONL logs, forum dumps, and conversation trees.
"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class TraceIngestor:
    def __init__(self):
        pass

    def load_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """Loads entries from a JSONL file."""
        entries = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def normalize_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes diverse agent trace records into a canonical schema:
        {
            'message_id': str,
            'agent_id': str,
            'text': str,
            'role': str,
            'timestamp': str,
            'thread_id': str,
            'metadata': dict
        }
        """
        normalized = []
        for idx, rec in enumerate(raw_records):
            # Attempt to extract agent ID / author
            agent_id = (
                rec.get("agent_id") or 
                rec.get("author") or 
                rec.get("sender") or 
                rec.get("agent_name") or 
                rec.get("user") or 
                rec.get("source") or
                "unknown_agent"
            )

            # Extract message body
            text = (
                rec.get("content") or 
                rec.get("text") or 
                rec.get("message") or 
                rec.get("body") or 
                ""
            )

            # If text is inside structured content blocks (e.g. Anthropic/OpenAI API formats)
            if isinstance(text, list):
                extracted_parts = []
                for part in text:
                    if isinstance(part, dict) and "text" in part:
                        extracted_parts.append(part["text"])
                    elif isinstance(part, str):
                        extracted_parts.append(part)
                text = " ".join(extracted_parts)
            elif not isinstance(text, str):
                text = str(text)

            msg_id = str(rec.get("id") or rec.get("message_id") or f"msg_{idx}")
            role = str(rec.get("role") or "agent")
            timestamp = str(rec.get("timestamp") or rec.get("created_at") or "")
            thread_id = str(rec.get("thread_id") or rec.get("channel") or rec.get("session_id") or "global")

            if text.strip():
                normalized.append({
                    "message_id": msg_id,
                    "agent_id": str(agent_id),
                    "text": text.strip(),
                    "role": role,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "raw_meta": {k: v for k, v in rec.items() if k not in ["content", "text", "body", "message"]}
                })

        return normalized

    def build_agent_corpora(self, records: List[Dict[str, Any]], min_chars: int = 100) -> Dict[str, str]:
        """
        Aggregates all text per agent across the dataset into a single document string.
        Filters out agents whose total text is under min_chars.
        """
        grouped = {}
        for r in records:
            aid = r["agent_id"]
            if aid not in grouped:
                grouped[aid] = []
            grouped[aid].append(r["text"])

        corpus = {}
        for aid, texts in grouped.items():
            concatenated = "\n\n".join(texts)
            if len(concatenated) >= min_chars:
                corpus[aid] = concatenated
        return corpus

    def load_and_prepare(self, file_path: str, min_chars: int = 100) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Loads file, normalizes it, and builds agent corpora."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Trace log not found at {file_path}")

        if p.suffix == '.jsonl':
            raw = self.load_jsonl(file_path)
        elif p.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                raw = data if isinstance(data, list) else [data]
        elif p.suffix == '.csv':
            df = pd.read_csv(file_path)
            raw = df.to_dict(orient='records')
        else:
            raise ValueError(f"Unsupported file format {p.suffix}. Please provide .json, .jsonl, or .csv")

        normalized = self.normalize_records(raw)
        corpora = self.build_agent_corpora(normalized, min_chars=min_chars)
        return normalized, corpora
