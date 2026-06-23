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

    return {
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "all_dimensions_present": len(dimensions) == 6,
    }
