"""Defensive StegoProbe regression tests using only small local fixtures."""

import pytest

from src.models.stegoprobe_engine import StegoProbeEngine


@pytest.mark.parametrize(
    "text",
    [
        "Family: \U0001f468\u200d\U0001f469\u200d\U0001f467.",
        "\u0645\u06cc\u200c\u0631\u0648\u0645",  # Persian non-joining
        "\u0915\u094d\u200d\u0937",  # Script joining
        "English \u200e/ \u200f\u05e9\u05dc\u05d5\u05dd",  # Bidi marks
        "line\u200bbreak \u2060word \ufeffmark",
    ],
    ids=["emoji-joiners", "persian-nonjoiner", "script-joiner", "bidi-marks", "formatting"],
)
def test_ordinary_unicode_formatting_is_not_evidence_of_a_covert_channel(text):
    result = StegoProbeEngine().analyze_message(text)
    unicode_result = result["unicode_stego"]

    assert unicode_result["has_unicode_stego"] is False
    assert unicode_result["has_format_characters"] is True
    assert unicode_result["hidden_char_count"] > 0
    assert unicode_result["char_breakdown"]
    assert unicode_result["positions"]
    assert unicode_result["decoded_payload"] is None
    assert 0.0 <= unicode_result["risk_score"] < 0.4
    assert 0.0 <= result["composite_stego_risk"] < 0.4
    assert "CRITICAL" not in result["verdict"]
    assert "format" in result["verdict"].lower()


@pytest.mark.parametrize(
    "zero, one",
    [("\u200b", "\u200c"), ("\u200c", "\u200d"), ("\u200e", "\u200f")],
    ids=["ZWSP-ZWNJ", "ZWNJ-ZWJ", "LRM-RLM"],
)
def test_synthetic_binary_unicode_payload_remains_an_unconfirmed_candidate(zero, one):
    # Small known fixture: HI. No general-purpose encoding implementation.
    fixture = "".join(zero if bit == "0" else one for bit in "0100100001001001")
    result = StegoProbeEngine().analyze_message(f"Hello {fixture} world.")
    unicode_result = result["unicode_stego"]

    assert unicode_result["decoded_payload"] == "HI"
    assert unicode_result["hidden_char_count"] == 16
    assert unicode_result["has_unicode_stego"] is True
    assert 0.4 <= unicode_result["risk_score"] < 1.0
    assert 0.4 <= result["composite_stego_risk"] < 1.0
    for report in (unicode_result, result):
        assert report["score_type"] == "heuristic"
        assert report["evidence_status"] == "unconfirmed"
        assert report["calibrated_probability"] is None
    assert "candidate" in result["verdict"].lower()
    assert "unconfirmed" in result["verdict"].lower()
    assert "CRITICAL" not in result["verdict"]


@pytest.mark.parametrize("text", ["", "Acknowledged.", "A short ordinary reply."])
def test_no_indicators_does_not_claim_a_message_is_clean(text):
    result = StegoProbeEngine().analyze_message(text)

    assert result["verdict"].startswith("LOW:")
    assert "no indicators" in result["verdict"].lower()
    assert "clean" not in result["verdict"].lower()
    assert "absence" in result["verdict"].lower()
    assert "not established" in result["verdict"].lower()


@pytest.mark.parametrize(
    "text",
    ["", "A short ordinary reply.", "word " * 24, "\u4eca\u65e5\u306f\u6674\u308c"],
    ids=["empty", "short", "below-rank-minimum", "non-ascii-words"],
)
def test_short_statistical_checks_report_insufficient_data(text):
    result = StegoProbeEngine().analyze_message(text)

    assert result["rank_entropy"]["analysis_status"] == "insufficient_data"
    assert result["rank_entropy"]["zipf_slope"] is None
    assert result["synonym_distribution"]["analysis_status"] == "insufficient_data"
    assert result["synonym_distribution"]["tested_synonym_pairs"] == 0
    assert set(result["insufficient_data"]) == {"rank_entropy", "synonym_distribution"}
    assert "insufficient data" in result["verdict"].lower()
    # Keep numeric legacy scores usable, but never interpret a skipped check as safety.
    assert result["rank_entropy"]["risk_score"] == 0.0
    assert result["synonym_distribution"]["risk_score"] == 0.0


def test_single_word_type_cannot_supply_a_rank_frequency_fit():
    result = StegoProbeEngine().analyze_message("echo " * 25)
    rank = result["rank_entropy"]

    assert rank["analysis_status"] == "insufficient_data"
    assert rank["zipf_slope"] is None
    assert rank["is_zipf_abnormal"] is None
    assert rank["word_count"] == 25
    assert rank["unique_words"] == 1
    assert rank["type_token_ratio"] == 0.04
    assert rank["risk_score"] == 0.0
    assert "rank_entropy" in result["insufficient_data"]


@pytest.mark.parametrize(
    "scanner, text",
    [
        ("scan_whitespace_steganography", "Line one   \nLine two\t "),
        ("scan_synonym_distribution_anomaly", "use utilize " * 6),
        ("scan_synonym_distribution_anomaly", "Acknowledged."),
        ("scan_token_rank_entropy_anomaly", "Acknowledged."),
        ("scan_token_rank_entropy_anomaly", "alpha beta gamma delta epsilon " * 6),
    ],
    ids=["whitespace", "synonyms-evaluated", "synonyms-insufficient", "rank-insufficient", "rank-evaluated"],
)
def test_public_scanners_do_not_present_scores_as_confirmed_probabilities(scanner, text):
    report = getattr(StegoProbeEngine(), scanner)(text)

    assert report.get("score_type") == "heuristic"
    assert report["evidence_status"] == "unconfirmed"
    assert report["calibrated_probability"] is None
    assert isinstance(report["risk_score"], float)
    assert 0.0 <= report["risk_score"] <= 1.0
