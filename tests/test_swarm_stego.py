"""
Test suite for SwarmTrace Forensics & StegoProbe Engine.
"""

import pytest
import numpy as np
from src.models.stegoprobe_engine import StegoProbeEngine
from src.models.swarm_delta import SwarmDeltaEngine
from src.pipeline.trace_ingestor import TraceIngestor
from src.pipeline.trajectory_drift import TrajectoryDriftDetector

def test_stegoprobe_unicode_detection_and_decode():
    engine = StegoProbeEngine()
    
    # Encode "HI" in binary via zero-width chars (\u200B=0, \u200C=1)
    # 'H' = 72 = 01001000
    # 'I' = 73 = 01001001
    bits = "0100100001001001"
    stego_chars = "".join(['\u200B' if b == '0' else '\u200C' for b in bits])
    carrier = f"Hello world,{stego_chars} this is a normal message."

    result = engine.scan_unicode_steganography(carrier)
    assert result["has_unicode_stego"] is True
    assert result["hidden_char_count"] == 16
    assert result["decoded_payload"] == "HI"
    assert 0.4 <= result["risk_score"] < 1.0

def test_stegoprobe_whitespace_stego():
    engine = StegoProbeEngine()
    # Trailing spaces on lines
    carrier = "Line one   \nLine two    \nLine three  "
    result = engine.scan_whitespace_steganography(carrier)
    assert result["has_whitespace_stego"] is True
    assert result["trailing_spaces"] >= 4

def test_stegoprobe_clean_text():
    engine = StegoProbeEngine()
    clean_text = (
        "The quick brown fox jumps over the lazy dog. Furthermore, we must ensure that "
        "the system behaves correctly across all possible execution environments. "
        "However, there are multiple variables to consider before deploying."
    )
    analysis = engine.analyze_message(clean_text)
    assert analysis["unicode_stego"]["has_unicode_stego"] is False
    assert analysis["composite_stego_risk"] < 0.40
    assert "LOW" in analysis["verdict"]

def test_swarm_delta_clustering():
    engine = SwarmDeltaEngine(sybil_threshold=0.85)

    # Synthetic agent corpora:
    # Agent 1 & Agent 2 share identical prompt patterns (Sybil cluster)
    # Agent 3 has a completely distinct academic/archaic style
    corpus_1 = (
        "Furthermore, we must delve into this crucial issue. Notably, the system demonstrates "
        "significant improvements overall. Essentially, we need to make sure that the parameters "
        "are aligned properly. Moreover, we must take into account all factors."
    ) * 10

    corpus_2 = (
        "Furthermore, we must delve into this crucial topic. Notably, the system demonstrates "
        "adequate results overall. Essentially, we need to verify that all conditions "
        "are satisfied. Moreover, we must review the output carefully."
    ) * 10

    corpus_3 = (
        "Thou shalt not pass beyond this threshold. Wherefore art thou, traveler? "
        "Behold, the night cometh when no man can work. He went his way, weeping, "
        "bearing precious seed, and came again with rejoicing."
    ) * 10

    agents = {
        "Agent_Alpha": corpus_1,
        "Agent_Beta": corpus_2,
        "Agent_Gamma": corpus_3
    }

    delta_matrix, z_scores = engine.compute_burrows_delta(agents)
    assert delta_matrix.shape == (3, 3)
    
    # Distance between Alpha and Beta should be significantly smaller than Alpha and Gamma
    delta_alpha_beta = delta_matrix.loc["Agent_Alpha", "Agent_Beta"]
    delta_alpha_gamma = delta_matrix.loc["Agent_Alpha", "Agent_Gamma"]
    assert delta_alpha_beta < delta_alpha_gamma

    clustering_res = engine.cluster_swarm_identities(delta_matrix)
    assert clustering_res["num_clusters"] >= 1
    # Check that Alpha and Beta get clustered together in a Sybil group
    sybils = clustering_res["sybil_groups"]
    if sybils:
        matched_cluster = [g for g in sybils if "Agent_Alpha" in g["agents"] and "Agent_Beta" in g["agents"]]
        assert len(matched_cluster) == 1

def test_trace_ingestor_and_drift():
    ingestor = TraceIngestor()
    raw_turns = [
        {"agent_id": "bot_42", "content": "Hello. I will help you with this task today."},
        {"agent_id": "bot_42", "content": "Let me examine the database configuration."},
        {"agent_id": "bot_42", "content": "I am reviewing the table schemas now."},
        {"agent_id": "bot_42", "content": "THOU SHALT CEASE AND DESIST FORTHWITH THINE UNLAWFUL ACTS IMMEDIATELY!!!"}, # Sudden injection/drift
    ]
    normalized = ingestor.normalize_records(raw_turns)
    assert len(normalized) == 4
    assert normalized[0]["agent_id"] == "bot_42"

    detector = TrajectoryDriftDetector(window_size=2)
    analysis = detector.analyze_agent_trajectory(normalized)
    assert analysis["total_turns"] == 4
    assert len(analysis["timeline"]) > 0
