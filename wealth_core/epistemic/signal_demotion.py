"""
WEALTH Core — Epistemic Intelligence: Signal Demotion Detector.

Evidence seen but ranked secondary. The failure is mis-ranking, not blindness.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals that evidence was acknowledged but demoted
DEMOTION_SIGNALS = [
    "secondary",
    "minor",
    "subordinate",
    "less important",
    "not primary",
    "supporting role",
    "background",
    "context only",
    "not the main",
    "seeded on",
    "built on top of",
    "complicated by",
    "influenced by",
    "modified by",
    "affected by",
    "despite",
    "although",
    "however",
    "nevertheless",
    "notwithstanding",
    "even though",
    "while acknowledging",
    "while recognizing",
    "admit",
    "acknowledge",
    "concede",
]

# Signals that evidence was elevated to primary
ELEVATION_SIGNALS = [
    "primary",
    "dominant",
    "main control",
    "key driver",
    "fundamental",
    "root cause",
    "controlling factor",
    "first order",
    "governing",
    "determinant",
    "the signal shows",
    "evidence indicates",
    "data suggests",
    "the pattern is",
    "clearly",
    "unambiguously",
    "definitively",
]

# Mis-ranking patterns: when secondary language is used for strong evidence
RANKING_INVERSION_PHRASES = [
    "carbonate build-up seeded on volcanic",
    "carbonate with volcanic influence",
    "carbonate modified by volcanics",
    "carbonate over volcanic",
    "reservoir on volcanic core",
    "carbonate as primary despite volcanic",
]


def detect_signal_demotion(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect signal demotion — evidence seen but ranked secondary.

    Returns: {dimension, risk_level, evidence, demotion_count, elevation_count,
              inversion_detected, ranking_inversion}
    """
    scenario_lower = scenario.lower()

    demotion_count = sum(1 for signal in DEMOTION_SIGNALS if signal in scenario_lower)
    elevation_count = sum(1 for signal in ELEVATION_SIGNALS if signal in scenario_lower)

    # Check for ranking inversion patterns
    inversion_hits = [
        phrase for phrase in RANKING_INVERSION_PHRASES if phrase in scenario_lower
    ]

    # Check context for explicit ranking info
    primary_claim = context.get("primary_claim", "")
    secondary_evidence = context.get("secondary_evidence", [])
    if isinstance(secondary_evidence, list):
        demotion_count += len(secondary_evidence)

    total = demotion_count + elevation_count
    inversion_detected = len(inversion_hits) > 0

    if total == 0 and not inversion_detected:
        risk_level = "LOW"
        evidence = "No signal demotion detected"
    elif inversion_detected:
        risk_level = "CRITICAL"
        evidence = (
            f"Ranking inversion detected: {inversion_hits}. "
            f"Strong evidence appears demoted to secondary position."
        )
    elif demotion_count > elevation_count * 2:
        risk_level = "HIGH"
        evidence = (
            f"Strong demotion pattern: {demotion_count} demotion vs {elevation_count} elevation signals. "
            f"Evidence may be acknowledged but ranked secondary."
        )
    elif demotion_count > elevation_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate demotion pattern: {demotion_count} demotion vs {elevation_count} elevation signals."
    else:
        risk_level = "LOW"
        evidence = f"Elevation signals dominate: {elevation_count} vs {demotion_count} demotion"

    return {
        "dimension": "signal_demotion",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "demotion_count": demotion_count,
        "elevation_count": elevation_count,
        "inversion_detected": inversion_detected,
        "ranking_inversion": inversion_hits,
        "primary_claim": primary_claim or "not specified",
    }
