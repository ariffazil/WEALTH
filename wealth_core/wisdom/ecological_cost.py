"""
WEALTH Core — Wisdom Economics: Ecological Cost.

What is the environmental externality?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

HIGH_COST_SIGNALS = [
    "fossil fuel",
    "carbon emission",
    "deforestation",
    "water pollution",
    "plastic waste",
    "habitat destruction",
    "overfishing",
    "mining",
    "land degradation",
    "biodiversity loss",
]

LOW_COST_SIGNALS = [
    "renewable",
    "carbon neutral",
    "circular economy",
    "sustainable",
    "reforestation",
    "clean energy",
    "recycling",
    "conservation",
    "regenerative",
    "net zero",
]


def evaluate_ecological_cost(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate ecological cost of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (high ecological cost) to 1.0 (low ecological cost / beneficial)
    """
    proposal_lower = proposal.lower()

    high_cost_count = sum(
        1 for signal in HIGH_COST_SIGNALS if signal in proposal_lower
    )
    low_cost_count = sum(
        1 for signal in LOW_COST_SIGNALS if signal in proposal_lower
    )

    total = high_cost_count + low_cost_count
    if total == 0:
        score = 0.5
        evidence = "No ecological signals detected"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = low_cost_count / total
        evidence = (
            f"Found {low_cost_count} low-cost signals "
            f"and {high_cost_count} high-cost signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    return {
        "dimension": "ecological",
        "score": round(score, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "high_cost_signals": high_cost_count,
        "low_cost_signals": low_cost_count,
    }
