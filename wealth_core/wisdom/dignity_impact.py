"""
WEALTH Core — Wisdom Economics: Dignity Impact.

F6 MARUAH: Preserve human dignity.
Does this allocation preserve, erode, or have unclear impact on human dignity?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals that erode dignity
DIGNITY_EROSION_SIGNALS = [
    "debt trap",
    "predatory lending",
    "wage suppression",
    "essential service cut",
    "healthcare denial",
    "education barrier",
    "housing displacement",
    "surveillance capitalism",
    "attention exploitation",
    "addiction by design",
]

# Signals that preserve dignity
DIGNITY_PRESERVATION_SIGNALS = [
    "universal access",
    "fair wage",
    "healthcare provision",
    "education investment",
    "housing stability",
    "agency preservation",
    "informed consent",
    "exit option",
    "appeal mechanism",
    "dignity of labor",
]


def evaluate_dignity_impact(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate dignity impact of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (severe erosion) to 1.0 (strong preservation)
    """
    proposal_lower = proposal.lower()

    erosion_count = sum(
        1 for signal in DIGNITY_EROSION_SIGNALS
        if signal in proposal_lower
    )
    preservation_count = sum(
        1 for signal in DIGNITY_PRESERVATION_SIGNALS
        if signal in proposal_lower
    )

    total_signals = erosion_count + preservation_count
    if total_signals == 0:
        score = 0.5  # No signal — neutral
        evidence = "No dignity signals detected in proposal text"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = preservation_count / total_signals
        evidence = (
            f"Found {preservation_count} preservation signals "
            f"and {erosion_count} erosion signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    return {
        "dimension": "dignity",
        "score": round(score, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "erosion_signals": erosion_count,
        "preservation_signals": preservation_count,
    }
