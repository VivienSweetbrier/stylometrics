"""Synthetic-only reliability tests; no attribution or detection calibration."""

import numpy as np
import pandas as pd
import pytest

from src.models.swarm_delta import SwarmDeltaEngine


@pytest.mark.parametrize("text", ["The same synthetic sentence.", ""])
def test_zero_variance_corpora_are_explicitly_unavailable(text):
    engine = SwarmDeltaEngine()
    with pytest.raises(ValueError, match=r"(?i)insufficient data.*variance"):
        engine.compute_burrows_delta({"synthetic_a": text, "synthetic_b": text})


@pytest.mark.parametrize(
    "matrix",
    [
        [[0.0, 1.0], [1.0, 0.0]],
        pd.DataFrame([[0.0, 1.0]], index=["a"], columns=["a", "b"]),
        pd.DataFrame([[0.0, 1.0], [1.0, 0.0]], index=["a", "b"], columns=["b", "a"]),
        pd.DataFrame([[0.0, 1.0], [1.0, 0.0]], index=["a", "a"], columns=["a", "a"]),
        pd.DataFrame([[0.0, 1.0], [1.0, 0.0]], index=["a", None], columns=["a", None]),
        pd.DataFrame([[0.0, np.nan], [np.nan, 0.0]]),
        pd.DataFrame([[0.0, np.inf], [np.inf, 0.0]]),
        pd.DataFrame([[0.0, -0.1], [-0.1, 0.0]]),
        pd.DataFrame([[0.0, 0.2], [0.5, 0.0]]),
        pd.DataFrame([[0.1, 0.2], [0.2, 0.0]]),
        pd.DataFrame([["zero", "one"], ["one", "zero"]]),
        pd.DataFrame([[0.0, 1.0j], [1.0j, 0.0]]),
    ],
    ids=["not-dataframe", "nonsquare", "label-order", "duplicate-labels", "missing-label",
         "nan", "infinity", "negative", "asymmetric", "nonzero-diagonal", "nonnumeric", "complex"],
)
def test_invalid_distance_matrices_are_rejected_before_clustering(matrix):
    with pytest.raises(ValueError, match=r"(?i)distance matrix"):
        SwarmDeltaEngine().cluster_swarm_identities(matrix)


@pytest.mark.parametrize("count", [0, 1, 2])
def test_similarity_output_preserves_legacy_keys_without_identity_claims(count):
    labels = [f"synthetic_{i}" for i in range(count)]
    matrix = pd.DataFrame(np.zeros((count, count)), index=labels, columns=labels)
    result = SwarmDeltaEngine().cluster_swarm_identities(matrix)
    assert result["calibrated"] is False
    assert result["warnings"]
    assert "identity" in " ".join(result["warnings"]).lower()
    assert result["total_agents"] == count
    assert result["num_clusters"] == len(result["clusters"])
    assert result["sybil_threshold"] == 0.75
    assert result["sybil_groups"] == result["similarity_groups"]
    assert result["insufficient_data"] is (count < 2)
    if count == 2:
        assert result["similarity_groups"][0]["agents"] == labels


def test_delta_features_and_distances_are_finite_uncalibrated_heuristics():
    corpus = {"synthetic_a": "the the and", "synthetic_b": "of of in!!!",
              "synthetic_c": "we can go?"}
    distances, scores = SwarmDeltaEngine().compute_burrows_delta(corpus)
    assert distances.index.tolist() == distances.columns.tolist() == list(corpus)
    assert np.isfinite(distances.to_numpy()).all()
    assert np.isfinite(scores.to_numpy()).all()
    assert (distances.to_numpy() >= 0).all()
    np.testing.assert_array_equal(distances, distances.T)
    np.testing.assert_array_equal(np.diag(distances), np.zeros(len(corpus)))
    for frame in (distances, scores):
        assert frame.attrs["calibrated"] is False
        assert frame.attrs["warnings"]


@pytest.mark.parametrize("count", [1, 2, 3, 5])
def test_every_turn_is_scanned_even_in_short_traces_and_the_tail(count):
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    detector = TrajectoryDriftDetector(window_size=3)
    # Synthetic marker in the last turn: no claim that it is malicious.
    turns = [{"message_id": f"synthetic_{i}", "text": f"Synthetic turn {i}."}
             for i in range(count)]
    turns[-1]["text"] += "\u200b\u200c"
    result = detector.analyze_agent_trajectory(turns)
    assert result["total_turns"] == len(turns)
    assert len(result["timeline"]) == len(turns)
    for index, (entry, turn) in enumerate(zip(result["timeline"], turns), start=1):
        expected = detector.stego_engine.analyze_message(turn["text"])
        assert entry["turn_index"] == index
        assert entry["turn_id"] == turn["message_id"]
        assert entry["stego_risk"] == expected["composite_stego_risk"]
        assert entry["stego_verdict"] == expected["verdict"]


def test_future_turns_cannot_change_past_style_scores_or_alerts():
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    detector = TrajectoryDriftDetector(window_size=2)
    prefix = [{"text": "the and of in."} for _ in range(6)]
    prefix.append({"text": "Synthetic change!!!?!"})
    future = [{"text": "we we we; however, " * 30} for _ in range(5)]
    before = detector.analyze_agent_trajectory(prefix)
    after = detector.analyze_agent_trajectory(prefix + future)
    assert before["timeline"] == after["timeline"][:len(prefix)]
    assert before["alerts"] == [a for a in after["alerts"] if a["turn_index"] <= len(prefix)]


def test_style_comparison_uses_only_the_preceding_window():
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    detector = TrajectoryDriftDetector(window_size=2)
    turns = [{"text": text} for text in ["the the and", "of in in", "we go!!!", "will you?"]]
    result = detector.analyze_agent_trajectory(turns)
    assert [entry["stylometric_drift"] for entry in result["timeline"][:2]] == [None, None]
    for i in range(2, len(turns)):
        baseline_text = " ".join(turn["text"] for turn in turns[i - 2:i])
        baseline = detector.swarm_engine.extract_agent_features(baseline_text)
        current = detector.swarm_engine.extract_agent_features(turns[i]["text"])
        expected = float(np.mean([abs(current[k] - baseline[k]) / max(abs(baseline[k]), 1.0)
                                  for k in baseline]))
        assert result["timeline"][i]["stylometric_drift"] == round(expected, 3)
        assert result["timeline"][i]["baseline_turn_indices"] == [i - 1, i]


@pytest.mark.parametrize("count", [0, 1, 3, 4])
def test_style_history_availability_is_separate_from_message_scan_coverage(count):
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    turns = [{"text": "Synthetic ordinary text."} for _ in range(count)]
    result = TrajectoryDriftDetector(window_size=3).analyze_agent_trajectory(turns)
    unavailable = count <= 3
    assert result["insufficient_data"] is unavailable
    assert result["style_analysis_status"] == ("insufficient_history" if unavailable else "evaluated")
    assert result["scanned_turns"] == count
    assert result["message_scan_status"] == ("completed" if count else "no_turns")
    assert result["calibrated"] is False
    assert result["warnings"]
    if unavailable:
        assert result["mean_drift"] is None
        assert result["std_drift"] is None
        assert result["drift_threshold"] is None
    for i, entry in enumerate(result["timeline"]):
        assert entry["message_scan_status"] == "completed"
        assert entry["style_status"] == ("insufficient_history" if i < 3 else "evaluated")
        assert entry["calibrated"] is False


def test_style_alert_requests_review_without_a_control_claim():
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    turns = [{"text": "the and of in."}, {"text": "the and of in."}, {"text": "!" * 40}]
    result = TrajectoryDriftDetector(window_size=2).analyze_agent_trajectory(turns)
    assert result["alerts"]
    alert = result["alerts"][0]
    assert alert["type"] == "STYLE_SHIFT_REVIEW"
    assert "not evidence" in alert["description"].lower()
    assert alert["calibrated"] is False


def test_short_trace_message_alert_is_an_unconfirmed_review_indicator():
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    # Synthetic ASCII HI fixture; this is not a real-world malicious payload.
    marker = "".join("\u200b" if bit == "0" else "\u200c" for bit in "0100100001001001")
    result = TrajectoryDriftDetector(window_size=3).analyze_agent_trajectory([{"text": "Hello " + marker}])
    assert result["insufficient_data"] is True  # Style unavailable, not an empty scan.
    assert result["alerts"]
    assert result["alerts"][0]["type"] == "MESSAGE_INDICATOR_REVIEW"
    assert result["alerts"][0]["calibrated"] is False


def test_ingestor_return_annotation_can_be_resolved():
    from typing import get_origin, get_type_hints
    from src.pipeline.trace_ingestor import TraceIngestor

    hints = get_type_hints(TraceIngestor.load_and_prepare)
    assert get_origin(hints["return"]) is tuple


@pytest.mark.parametrize("threshold", [np.nan, np.inf, -1.0, None, "bad", True])
def test_invalid_similarity_threshold_is_rejected(threshold):
    with pytest.raises(ValueError, match="sybil_threshold"):
        SwarmDeltaEngine(sybil_threshold=threshold)


@pytest.mark.parametrize("kwargs", [
    {"window_size": 0}, {"window_size": -1}, {"window_size": 1.5}, {"window_size": True},
    {"drift_sensitivity": np.nan}, {"drift_sensitivity": np.inf}, {"drift_sensitivity": -1},
    {"drift_sensitivity": None}, {"drift_sensitivity": "bad"}, {"drift_sensitivity": True},
])
def test_invalid_temporal_configuration_is_rejected(kwargs):
    from src.pipeline.trajectory_drift import TrajectoryDriftDetector

    with pytest.raises(ValueError, match="window_size|drift_sensitivity"):
        TrajectoryDriftDetector(**kwargs)
