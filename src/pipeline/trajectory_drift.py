"""
TrajectoryDrift: causal style comparisons and per-message review indicators.
Style shifts and message anomalies are uncalibrated heuristics, not evidence of
prompt injection, identity changes, hijacking, or common control.
"""

import numpy as np
from numbers import Integral, Real
from typing import List, Dict, Any
from src.models.swarm_delta import SwarmDeltaEngine
from src.models.stegoprobe_engine import StegoProbeEngine

class TrajectoryDriftDetector:
    def __init__(self, window_size: int = 3, drift_sensitivity: float = 1.5):
        if isinstance(window_size, bool) or not isinstance(window_size, Integral) or window_size < 1:
            raise ValueError("window_size must be a positive integer.")
        if (isinstance(drift_sensitivity, bool) or not isinstance(drift_sensitivity, Real)
                or not np.isfinite(drift_sensitivity) or drift_sensitivity < 0):
            raise ValueError("drift_sensitivity must be a finite nonnegative number.")
        self.window_size = window_size
        self.drift_sensitivity = drift_sensitivity
        self.swarm_engine = SwarmDeltaEngine()
        self.stego_engine = StegoProbeEngine()

    def analyze_agent_trajectory(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a chronological sequence of turns for a single agent:
        [{'turn': 1, 'text': '...', 'timestamp': '...'}, ...]
        Scan every message. Compare each turn with the preceding window_size
        turns; scores are unavailable until that history exists. Thresholds use
        only earlier scores (initially a heuristic floor), never future turns.
        Returns review indicators, not calibrated attribution or attack findings.
        Legacy insufficient_data refers only to style history. None scores mean
        unavailable, not zero drift. Summary means/stds describe available scores;
        drift_threshold is the last threshold used, not a retrospective cutoff.
        """

        timeline = []
        alerts = []
        deltas = []
        drift_threshold = None

        # Message scans cover every turn independently of style-window availability.
        for i, curr_turn in enumerate(turns):
            normalized_delta = None
            turn_threshold = None
            baseline_turn_indices = []
            if i >= self.window_size:
                # Current turn versus the immediately preceding window only.
                window_slice = turns[i - self.window_size : i]
                baseline_text = " ".join(t["text"] for t in window_slice)
                baseline_features = self.swarm_engine.extract_agent_features(baseline_text)
                win_features = self.swarm_engine.extract_agent_features(curr_turn["text"])
                baseline_turn_indices = list(range(i - self.window_size + 1, i + 1))

                # Compute Manhattan distance on shared features.
                keys = list(baseline_features.keys())
                diffs = [abs(win_features[k] - baseline_features[k]) for k in keys]
                magnitudes = [max(abs(baseline_features[k]), 1.0) for k in keys]
                normalized_delta = float(np.mean([d / m for d, m in zip(diffs, magnitudes)]))
                # Threshold uses prior scores, never the current score or future turns.
                prior_mean = float(np.mean(deltas)) if deltas else 0.0
                prior_std = float(np.std(deltas)) if deltas else 0.0
                turn_threshold = prior_mean + self.drift_sensitivity * max(prior_std, 0.1)
                drift_threshold = turn_threshold
                deltas.append(normalized_delta)

            stego_res = self.stego_engine.analyze_message(curr_turn["text"])

            timeline_entry = {
                "turn_index": i + 1,
                "turn_id": curr_turn.get("message_id", f"turn_{i+1}"),
                "preview": curr_turn["text"][:120] + "..." if len(curr_turn["text"]) > 120 else curr_turn["text"],
                "stylometric_drift": round(normalized_delta, 3) if normalized_delta is not None else None,
                "drift_threshold": round(turn_threshold, 3) if turn_threshold is not None else None,
                "baseline_turn_indices": baseline_turn_indices,
                "style_status": "evaluated" if normalized_delta is not None else "insufficient_history",
                "message_scan_status": "completed",
                "calibrated": False,
                "stego_risk": stego_res["composite_stego_risk"],
                "stego_verdict": stego_res["verdict"]
            }
            timeline.append(timeline_entry)

            # Uncalibrated message indicators warrant review, not a finding.
            if stego_res["composite_stego_risk"] >= 0.70:
                alerts.append({
                    "turn_index": i + 1,
                    "type": "MESSAGE_INDICATOR_REVIEW",
                    "severity": "WARNING",
                    "calibrated": False,
                    "description": "Unconfirmed message indicator: " + stego_res["verdict"],
                    "turn_text": curr_turn["text"]
                })

            if normalized_delta is not None and normalized_delta > turn_threshold:
                alerts.append({
                    "turn_index": i + 1,
                    "type": "STYLE_SHIFT_REVIEW",
                    "severity": "WARNING",
                    "calibrated": False,
                    "description": (
                        f"Heuristic style score {round(normalized_delta, 3)} exceeds "
                        f"prior-score threshold {round(turn_threshold, 3)}; "
                        "not evidence of hijack, handover, or common control."
                    ),
                    "turn_text": curr_turn["text"]
                })

        mean_delta = float(np.mean(deltas)) if deltas else 0.0
        std_delta = float(np.std(deltas)) if deltas else 0.0
        warnings = [
            "Uncalibrated review heuristics only: style and message indicators do not "
            "establish injection, hijack, attribution, or common control. Language, "
            "topic, text length, and formatting affect scores. Initial thresholds "
            "use a heuristic floor, not a calibrated error rate."
        ]
        if not deltas:
            warnings.append(
                f"Insufficient style history: need {self.window_size} prior turns. "
                "Message scans are independent; unavailable style scores do not "
                "mean no message indicators were found."
            )
        return {
            "total_turns": len(turns),
            "insufficient_data": not deltas,
            "style_analysis_status": "evaluated" if deltas else "insufficient_history",
            "scanned_turns": len(timeline),
            "message_scan_status": "completed" if turns else "no_turns",
            "calibrated": False,
            "warnings": warnings,
            "mean_drift": round(mean_delta, 3) if deltas else None,
            "std_drift": round(std_delta, 3) if deltas else None,
            "drift_threshold": round(drift_threshold, 3) if drift_threshold is not None else None,
            "timeline": timeline,
            "alerts": alerts
        }
