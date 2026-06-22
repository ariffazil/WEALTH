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

from enum import Enum

from .dignity_impact import evaluate_dignity_impact
from .sovereignty_risk import evaluate_sovereignty_risk
from .resilience_score import evaluate_resilience
from .inequality_effect import evaluate_inequality_effect
from .ecological_cost import evaluate_ecological_cost
from .optionality_preserve import evaluate_optionality

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


class SignalState(str, Enum):
    """Fix 3: Replace numeric score: 0.5 with semantic states."""

    POSITIVE = "POSITIVE"           # > 0.6 — clear positive signal
    NEUTRAL = "NEUTRAL"             # 0.4-0.6 — balanced / no clear direction
    NEGATIVE = "NEGATIVE"           # < 0.4 — clear negative signal
    INSUFFICIENT_SIGNAL = "INSUFFICIENT_SIGNAL"  # < 2 patterns matched
    CONFLICTED = "CONFLICTED"       # matched both positive and negative patterns


def derive_signal_state(
    score: float,
    pattern_count: int = 0,
    has_positive_patterns: bool = False,
    has_negative_patterns: bool = False,
) -> tuple[SignalState, float]:
    """Derive a semantic SignalState from score + pattern metadata.

    Args:
        score: Raw numeric score (0.0-1.0)
        pattern_count: Number of matched patterns
        has_positive_patterns: True if positive patterns matched
        has_negative_patterns: True if negative patterns matched

    Returns:
        (SignalState, confidence): Semantic state + confidence in that state.
    """
    # Conflicted pattern detection takes precedence
    if has_positive_patterns and has_negative_patterns:
        return SignalState.CONFLICTED, 0.5

    # Insufficient evidence
    if pattern_count < 2 and score == 0.5:
        return SignalState.INSUFFICIENT_SIGNAL, 0.3

    # Score-based classification
    if score > 0.6:
        return SignalState.POSITIVE, min(1.0, score)
    elif score < 0.4:
        return SignalState.NEGATIVE, min(1.0, 1.0 - score)
    else:
        return SignalState.NEUTRAL, 0.5

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
