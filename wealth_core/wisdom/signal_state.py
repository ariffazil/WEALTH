"""
Signal state types for WEALTH wisdom dimensions.

Extracted from __init__.py to break circular import cycle
(where dignity_impact.py imports from __init__ while __init__ was still loading).

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from enum import Enum


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
