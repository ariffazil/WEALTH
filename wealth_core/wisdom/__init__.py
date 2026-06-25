"""
WEALTH Core — Wisdom Economics.

Answers: "Is this wise?" not just "Is this profitable?"

Six dimensions:
- Dignity Impact: Does this preserve human dignity?
- Sovereignty Risk: Does this create dependency/capture?
- Resilience Score: Does this survive shocks?
- Inequality Effect: Does this widen or narrow inequality?
- Ecological Cost: What is the environmental externality?
- Optionality Preserve: Does this preserve future choices?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from .dignity_impact import evaluate_dignity_impact
from .sovereignty_risk import evaluate_sovereignty_risk
from .resilience_score import evaluate_resilience
from .inequality_effect import evaluate_inequality_effect
from .ecological_cost import evaluate_ecological_cost
from .optionality_preserve import evaluate_optionality
from .signal_state import SignalState, derive_signal_state  # noqa: F401

__all__ = [
    "evaluate_dignity_impact",
    "evaluate_sovereignty_risk",
    "evaluate_resilience",
    "evaluate_inequality_effect",
    "evaluate_ecological_cost",
    "evaluate_optionality",
    "compute_wisdom",
    "SignalState",
    "derive_signal_state",
]

WISDOM_DIMENSIONS = [
    "dignity",
    "sovereignty",
    "resilience",
    "inequality",
    "ecological",
    "optionality",
]


def compute_wisdom(
    proposal: str,
    capital_type: str = "financial",
    context: dict | None = None,
) -> dict:
    """
    Evaluate a capital allocation proposal across all 6 wisdom dimensions.
    Returns dict with dimension scores, evidence, and epistemic tags.

    This function does NOT judge. It computes wisdom dimensions.
    arifOS judges. Arif decides.

    RSI-03 FIX (2026-06-25): When all 6 dimensions score in [0.45, 0.55]
    the tool sets all_dimensions_neutral=True and caps confidence at 0.70.
    All-neutral is itself a signal — the tool found no strong conviction
    anywhere, which is meaningfully different from each dimension
    independently returning neutral.
    """
    ctx = context or {}

    dimensions = []
    for eval_fn in [
        evaluate_dignity_impact,
        evaluate_sovereignty_risk,
        evaluate_resilience,
        evaluate_inequality_effect,
        evaluate_ecological_cost,
        evaluate_optionality,
    ]:
        dim = eval_fn(proposal, capital_type, ctx)
        dimensions.append(dim)

    # RSI-03 FIX: all-neutral blind spot detection
    all_scores = [d.get("score", 0.5) for d in dimensions]
    all_neutral = all(0.45 <= s <= 0.55 for s in all_scores)

    if all_neutral:
        advisory = (
            "All 6 wisdom dimensions returned NEUTRAL (0.45–0.55). "
            "This is structurally different from one neutral dimension — "
            "it indicates the tool found no strong signal anywhere. "
            "Confidence capped at 0.70. Treat as UNCLEAR rather than balanced."
        )
        overall_confidence = 0.70
        neutral_flag = True
    else:
        # Average confidence across dimensions, downward-adjusted
        dim_confidences = [d.get("signal_confidence", 0.5) for d in dimensions]
        overall_confidence = round(sum(dim_confidences) / len(dim_confidences), 3)
        neutral_flag = False
        advisory = None

    return {
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "all_dimensions_present": len(dimensions) == 6,
        # RSI-03 FIX fields
        "all_dimensions_neutral": neutral_flag,
        "overall_wisdom_confidence": overall_confidence,
        "neutral_advisory": advisory,
    }
