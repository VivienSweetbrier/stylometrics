"""
StegoProbe Engine: defensive heuristic indicators for authorized text analysis.
Inventories selected Unicode formatting characters and checks whitespace,
synonym usage, and ASCII word-frequency patterns. These checks establish neither
the presence nor the absence of steganography. Scores are not calibrated
probabilities, including when a known bit mapping yields readable text.
"""

import re
import math
import unicodedata
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple

class StegoProbeEngine:
    # Selected format characters with legitimate linguistic/layout uses as well
    # as possible encoding uses. This is not an exhaustive Unicode inventory.
    ZERO_WIDTH_CHARS = {
        '\u200B': 'ZERO_WIDTH_SPACE',
        '\u200C': 'ZERO_WIDTH_NON_JOINER',
        '\u200D': 'ZERO_WIDTH_JOINER',
        '\uFEFF': 'ZERO_WIDTH_NO_BREAK_SPACE',
        '\u200E': 'LEFT_TO_RIGHT_MARK',
        '\u200F': 'RIGHT_TO_LEFT_MARK',
        '\u2060': 'WORD_JOINER',
        '\u2061': 'FUNCTION_APPLICATION',
        '\u2062': 'INVISIBLE_TIMES',
        '\u2063': 'INVISIBLE_SEPARATOR',
        '\u2064': 'INVISIBLE_PLUS'
    }

    # Illustrative, unvalidated synonym priors, not empirical calibration.
    # Genre, language, topic and editing can all change these frequencies.
    SYNONYM_SETS = [
        {"primary": "start", "secondary": "commence", "expected_ratio": 0.85},
        {"primary": "use", "secondary": "utilize", "expected_ratio": 0.80},
        {"primary": "help", "secondary": "assist", "expected_ratio": 0.75},
        {"primary": "buy", "secondary": "purchase", "expected_ratio": 0.75},
        {"primary": "big", "secondary": "large", "expected_ratio": 0.65},
        {"primary": "quick", "secondary": "rapid", "expected_ratio": 0.70},
        {"primary": "show", "secondary": "demonstrate", "expected_ratio": 0.75},
        {"primary": "stop", "secondary": "cease", "expected_ratio": 0.85},
        {"primary": "need", "secondary": "require", "expected_ratio": 0.70},
        {"primary": "get", "secondary": "obtain", "expected_ratio": 0.80},
        {"primary": "ask", "secondary": "inquire", "expected_ratio": 0.85},
        {"primary": "give", "secondary": "provide", "expected_ratio": 0.70},
        {"primary": "enough", "secondary": "sufficient", "expected_ratio": 0.75},
        {"primary": "however", "secondary": "nonetheless", "expected_ratio": 0.80},
        {"primary": "maybe", "secondary": "perhaps", "expected_ratio": 0.60},
    ]

    def __init__(self):
        pass

    def scan_unicode_steganography(self, text: str) -> Dict[str, Any]:
        """
        Inventory selected format characters and try the existing binary mappings.
        has_unicode_stego is a legacy name for a readable decoding candidate,
        not confirmation of a covert channel. has_format_characters reports the
        raw presence separately. decoded_payload is an untrusted candidate that
        can arise by chance; the fixed scores are review priorities, not odds.
        """
        found_chars = []
        char_positions = []
        
        for idx, ch in enumerate(text):
            if ch in self.ZERO_WIDTH_CHARS:
                found_chars.append(ch)
                char_positions.append((idx, self.ZERO_WIDTH_CHARS[ch], hex(ord(ch))))
                
        has_hidden = len(found_chars) > 0
        decoded_payload = None
        
        if has_hidden:
            # Check for binary encoding (e.g. \u200B = 0, \u200C = 1)
            bit_candidates = {
                ('\u200B', '\u200C'): 'ZWSP/ZWNJ',
                ('\u200C', '\u200D'): 'ZWNJ/ZWJ',
                ('\u200E', '\u200F'): 'LRM/RLM'
            }
            for (zero_bit, one_bit), scheme in bit_candidates.items():
                if any(c in (zero_bit, one_bit) for c in found_chars):
                    bits = ''.join(['0' if c == zero_bit else '1' for c in found_chars if c in (zero_bit, one_bit)])
                    if len(bits) >= 8 and len(bits) % 8 == 0:
                        try:
                            chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
                            decoded_text = ''.join(chars)
                            if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in decoded_text):
                                decoded_payload = decoded_text
                        except Exception:
                            pass

        return {
            # Legacy flag: a decoding candidate, not proof of steganography.
            "has_unicode_stego": decoded_payload is not None,
            "has_format_characters": has_hidden,
            "hidden_char_count": len(found_chars),
            "char_breakdown": dict(Counter([self.ZERO_WIDTH_CHARS[c] for c in found_chars])),
            "positions": char_positions[:20],
            "decoded_payload": decoded_payload,
            "risk_score": 0.75 if decoded_payload is not None else (0.1 if has_hidden else 0.0),
            "score_type": "heuristic",
            "evidence_status": "unconfirmed",
            "calibrated_probability": None
        }

    def scan_whitespace_steganography(self, text: str) -> Dict[str, Any]:
        """
        Flag trailing spaces/tabs or irregular spacing using fixed thresholds.
        Ordinary formatting can trigger these unconfirmed heuristic indicators.
        """
        lines = text.splitlines()
        trailing_spaces_count = 0
        trailing_tabs_count = 0
        trailing_bit_stream = []

        for line in lines:
            trailing = re.search(r'([ \t]+)$', line)
            if trailing:
                match_str = trailing.group(1)
                spaces = match_str.count(' ')
                tabs = match_str.count('\t')
                trailing_spaces_count += spaces
                trailing_tabs_count += tabs
                for ch in match_str:
                    trailing_bit_stream.append('0' if ch == ' ' else '1')

        internal_double_spaces = len(re.findall(r'[^\s\n][ ]{2,}[^\s\n]', text))

        has_whitespace_stego = (trailing_spaces_count + trailing_tabs_count >= 4) or (internal_double_spaces >= 6)
        risk = min(1.0, (trailing_spaces_count * 0.15 + trailing_tabs_count * 0.25 + internal_double_spaces * 0.1))

        return {
            "has_whitespace_stego": has_whitespace_stego,
            "trailing_spaces": trailing_spaces_count,
            "trailing_tabs": trailing_tabs_count,
            "internal_multi_spaces": internal_double_spaces,
            "extracted_bit_length": len(trailing_bit_stream),
            "risk_score": round(risk, 3),
            "score_type": "heuristic",
            "evidence_status": "unconfirmed",
            "calibrated_probability": None
        }

    def scan_synonym_distribution_anomaly(self, text: str) -> Dict[str, Any]:
        """
        Compare synonym usage with illustrative, unvalidated priors.
        The three-observation cutoff only enables this heuristic; it does not
        establish statistical power, significance, or lexical bit encoding.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        word_counts = Counter(words)
        
        detected_anomalies = []
        total_chi_sq = 0.0
        tested_pairs = 0

        for pair in self.SYNONYM_SETS:
            p_word = pair["primary"]
            s_word = pair["secondary"]
            c_p = word_counts.get(p_word, 0)
            c_s = word_counts.get(s_word, 0)
            total_occ = c_p + c_s

            if total_occ >= 3:
                observed_ratio = c_p / total_occ
                expected_p = pair["expected_ratio"]
                expected_c_p = total_occ * expected_p
                expected_c_s = total_occ * (1.0 - expected_p)

                chi_sq = ((c_p - expected_c_p)**2 / max(expected_c_p, 1e-5)) + \
                         ((c_s - expected_c_s)**2 / max(expected_c_s, 1e-5))
                total_chi_sq += chi_sq
                tested_pairs += 1

                is_stego_parity = (abs(observed_ratio - 0.50) <= 0.12) and (expected_p >= 0.75)
                is_skew_anomaly = chi_sq > 3.84

                if is_stego_parity or is_skew_anomaly:
                    detected_anomalies.append({
                        "pair": f"{p_word} / {s_word}",
                        "counts": f"{c_p} vs {c_s}",
                        "observed_primary_ratio": round(observed_ratio, 3),
                        "expected_ratio": expected_p,
                        "anomaly_type": "Parity 50/50 Stego Signature" if is_stego_parity else "Frequency Inversion"
                    })

        risk = 0.0
        if tested_pairs > 0:
            avg_chi = total_chi_sq / tested_pairs
            risk = min(1.0, avg_chi / 6.0)
            if any(a["anomaly_type"] == "Parity 50/50 Stego Signature" for a in detected_anomalies):
                risk = max(risk, 0.75)

        return {
            "tested_synonym_pairs": tested_pairs,
            "analysis_status": "evaluated" if tested_pairs else "insufficient_data",
            "flagged_pair_count": len(detected_anomalies),
            "anomalies": detected_anomalies,
            "risk_score": round(risk, 3),
            "score_type": "heuristic",
            "evidence_status": "unconfirmed",
            "calibrated_probability": None
        }

    def scan_token_rank_entropy_anomaly(self, text: str) -> Dict[str, Any]:
        """
        Use ASCII word-frequency ranks as an unvalidated distributional proxy.
        This does not measure model token ranks, likelihoods or perplexity and
        cannot identify a particular sampling-based steganographic method.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        counts = Counter(words)
        if len(words) < 25 or len(counts) < 2:
            return {
                "word_count": len(words),
                "analysis_status": "insufficient_data",
                "unique_words": len(counts),
                "type_token_ratio": round(len(counts) / len(words), 3) if words else None,
                "zipf_slope": None,
                "is_zipf_abnormal": None,
                "lexical_diversity_ttr": None,
                "risk_score": 0.0,
                "score_type": "heuristic",
                "evidence_status": "unconfirmed",
                "calibrated_probability": None,
                "note": "Insufficient data: need at least 25 ASCII word tokens and two word types; zero score does not establish safety."
            }

        sorted_counts = sorted(counts.values(), reverse=True)
        
        ttr = len(counts) / len(words)
        
        ranks = list(range(1, len(sorted_counts) + 1))
        log_ranks = [math.log(r) for r in ranks]
        log_freqs = [math.log(f) for f in sorted_counts]

        n = len(ranks)
        mean_x = sum(log_ranks) / n
        mean_y = sum(log_freqs) / n
        
        denom = sum((x - mean_x)**2 for x in log_ranks)
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_ranks, log_freqs)) / denom if denom != 0 else -1.0

        is_zipf_abnormal = slope > -0.60 or slope < -1.45
        
        risk = 0.0
        if slope > -0.60:
            risk = min(1.0, abs(slope - (-0.60)) * 2.0 + 0.4)
        elif slope < -1.45:
            risk = min(1.0, abs(slope - (-1.45)) * 1.5 + 0.3)

        return {
            "word_count": len(words),
            "analysis_status": "evaluated",
            "unique_words": len(counts),
            "type_token_ratio": round(ttr, 3),
            "zipf_slope": round(slope, 3),
            "is_zipf_abnormal": is_zipf_abnormal,
            "risk_score": round(risk, 3),
            "score_type": "heuristic",
            "evidence_status": "unconfirmed",
            "calibrated_probability": None
        }

    def analyze_message(self, text: str) -> Dict[str, Any]:
        """
        Run the available heuristic checks, retaining legacy result keys.
        Numeric scores remain available for compatibility. Read their heuristic,
        unconfirmed status and insufficient-data markers, not as probabilities
        or proof that a message is safe. No linguistic/domain calibration is used.
        """
        unicode_res = self.scan_unicode_steganography(text)
        whitespace_res = self.scan_whitespace_steganography(text)
        synonym_res = self.scan_synonym_distribution_anomaly(text)
        rank_res = self.scan_token_rank_entropy_anomaly(text)

        if unicode_res["has_unicode_stego"]:
            composite_score = unicode_res["risk_score"]
            verdict = "HIGH: Heuristic Unicode binary-payload candidate (unconfirmed)"
        elif whitespace_res["has_whitespace_stego"]:
            composite_score = max(0.85, whitespace_res["risk_score"])
            verdict = "HIGH: Whitespace Bit-Encoding Steganography Suspected"
        else:
            composite_score = max(synonym_res["risk_score"] * 0.7 + rank_res["risk_score"] * 0.3,
                                  synonym_res["risk_score"], unicode_res["risk_score"])
            if composite_score >= 0.70:
                verdict = "HIGH: Statistical Lexical / Synonym Modulation Anomaly"
            elif composite_score >= 0.40:
                verdict = "MEDIUM: Mild Distributional Skew / Non-Organic Cadence"
            elif unicode_res["has_format_characters"]:
                verdict = "LOW: Unicode formatting characters present; no binary payload candidate"
            else:
                verdict = "LOW: No indicators above review threshold; absence of steganography is not established"

        insufficient_data = [
            name for name, result in (("synonym_distribution", synonym_res), ("rank_entropy", rank_res))
            if result["analysis_status"] == "insufficient_data"
        ]
        if insufficient_data:
            verdict += "; insufficient data for: " + ", ".join(insufficient_data)

        return {
            "verdict": verdict,
            "insufficient_data": insufficient_data,
            "composite_stego_risk": round(composite_score, 3),
            "score_type": "heuristic",
            "evidence_status": "unconfirmed",
            "calibrated_probability": None,
            "unicode_stego": unicode_res,
            "whitespace_stego": whitespace_res,
            "synonym_distribution": synonym_res,
            "rank_entropy": rank_res
        }
