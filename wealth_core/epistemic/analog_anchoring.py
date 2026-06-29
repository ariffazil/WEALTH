"""
WEALTH Core — Epistemic Intelligence: Analog Anchoring Detector.

Success template overrides evidence. Past success becomes present bias.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals of analog dependency / template thinking
ANCHORING_SIGNALS = [
    "analog",
    "analogue",
    "similar to",
    "like",
    "comparable",
    "precedent",
    "template",
    "play type",
    "proven",
    "successful analog",
    "based on",
    "modeled after",
    "following",
    "consistent with proven",
    "proven play",
    "proven concept",
    "de-risked by",
    "analogous to",
    "mirrors",
    "resembles",
    "Tepat",
    "Layang",
    "Layang-Layang",
    "analogous field",
    "analogous reservoir",
]

# Signals of evidence-first thinking (anti-anchoring)
EVIDENCE_FIRST_SIGNALS = [
    "data shows",
    "evidence indicates",
    "observations suggest",
    "measurements show",
    "the data",
    "field evidence",
    "well data",
    "seismic data",
    "log data",
    "core data",
    "direct observation",
    "first principles",
    "from scratch",
    "no analog",
    "unprecedented",
    "novel",
    "unique",
    "different from",
    "unlike",
    "not comparable",
    "breaks the pattern",
    "does not fit",
    "inconsistent with",
]


def detect_analog_anchoring(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect analog anchoring — success template overrides evidence.

    Returns: {dimension, risk_level, evidence, anchoring_count, evidence_first_count,
              anchoring_ratio, analogs_named}
    """
    scenario_lower = scenario.lower()

    anchoring_count = sum(1 for signal in ANCHORING_SIGNALS if signal in scenario_lower)
    evidence_first_count = sum(
        1 for signal in EVIDENCE_FIRST_SIGNALS if signal in scenario_lower
    )

    # Extract named analogs
    named_analogs = [
        signal
        for signal in ANCHORING_SIGNALS
        if signal in scenario_lower and len(signal) > 3  # Skip short words
    ]

    total = anchoring_count + evidence_first_count
    anchoring_ratio = anchoring_count / max(1, total)

    if total == 0:
        risk_level = "LOW"
        evidence = "No analog anchoring signals detected"
    elif anchoring_ratio > 0.7:
        risk_level = "HIGH"
        evidence = (
            f"Strong analog dependency: {anchoring_count} anchoring vs {evidence_first_count} evidence-first signals. "
            f"Named analogs: {named_analogs[:5]}"
        )
    elif anchoring_ratio > 0.5:
        risk_level = "MEDIUM"
        evidence = f"Moderate analog dependency: {anchoring_count} anchoring vs {evidence_first_count} evidence-first signals."
    else:
        risk_level = "LOW"
        evidence = f"Evidence-first signals dominate: {evidence_first_count} vs {anchoring_count} anchoring"

    return {
        "dimension": "analog_anchoring",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "anchoring_count": anchoring_count,
        "evidence_first_count": evidence_first_count,
        "anchoring_ratio": round(anchoring_ratio, 3),
        "analogs_named": named_analogs[:10],
    }
