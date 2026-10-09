"""Disagreement protocol — F / T / D preservation.

M7 must NEVER merge contradictory organs into a single score. The
disagreement vector is itself a survival input (it widens the safety
envelope and shortens the review window).

This module owns:

    DisagreementVector    — typed disagreement record
    assess_disagreement   — compute the vector from F/T/D inputs
    widen_for_disagreement — adjust confidence / interval / size / review

The disagreement protocol
-------------------------

Per spec:

    if organs_disagree -> confidence DOWN, interval_width UP,
                         position_size DOWN, review_frequency UP

We encode these as multiplicative / additive adjustments:

    * confidence_multiplier ∈ (0, 1]
    * interval_multiplier ∈ [1, +∞)
    * size_multiplier ∈ (0, 1]
    * review_halflife_hours — explicit, derived from the disagreement

The caller is responsible for actually applying the adjustments.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np


# When the disagreement vector is empty, use this default. It is
# mildly conservative (no agreement assumed).
DISAGREEMENT_DEFAULT = {
    "f_value": 0.0,
    "t_value": 0.0,
    "d_value": 0.0,
    "agreement_score": 0.5,         # neither agree nor disagree
    "max_pairwise_diff": 1.0,
    "confidence_multiplier": 0.5,
    "interval_multiplier": 2.0,
    "size_multiplier": 0.5,
    "review_halflife_hours": 12.0,
    "notes": "default_unknown_disagreement",
}


@dataclass(frozen=True)
class DisagreementVector:
    f_value: float                  # fundamentals signal (normalised, signed)
    t_value: float                  # technical signal (normalised, signed)
    d_value: float                  # distribution / M5 signal (normalised, signed)
    agreement_score: float          # 1 = perfect agreement, 0 = max disagreement
    max_pairwise_diff: float        # largest |F-T|, |T-D|, |D-F|
    confidence_multiplier: float    # in (0, 1]
    interval_multiplier: float      # in [1, +∞)
    size_multiplier: float          # in (0, 1]
    review_halflife_hours: float    # smaller = review more often
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _normalise_signal(x: float) -> float:
    """Clamp to [-1, 1] and return NaN-safe 0 for NaN."""
    if not np.isfinite(x):
        return 0.0
    return float(max(-1.0, min(1.0, x)))


def assess_disagreement(
    *,
    f_value: float,
    t_value: float,
    d_value: float,
    review_baseline_hours: float = 24.0,
) -> DisagreementVector:
    """Compute the disagreement vector from F/T/D organ signals.

    All three values are normalised to [-1, 1] internally.

    Parameters
    ----------
    f_value, t_value, d_value : float
        Raw signals from the three organs. Each should be on a
        comparable scale (e.g. -1 = strong bearish, +1 = strong bullish).
    review_baseline_hours : float
        The "no disagreement" review cadence. Disagreement shortens it.
    """
    f = _normalise_signal(f_value)
    t = _normalise_signal(t_value)
    d = _normalise_signal(d_value)

    diffs = [abs(f - t), abs(t - d), abs(d - f)]
    max_diff = float(max(diffs))
    # Agreement: 1 - mean pairwise diff in [0, 1]
    agreement = float(1.0 - np.mean(diffs))

    # Adjustments per spec.
    # When agreement=1 → no adjustment. When agreement=0 → max adjustment.
    # confidence: multiply by max(0.1, agreement)
    confidence_mult = float(max(0.1, agreement))
    # interval: widen as agreement falls. At agreement=0, double it.
    interval_mult = float(1.0 + (1.0 - agreement))
    # size: shrink as agreement falls. At agreement=0, half it.
    size_mult = float(max(0.1, agreement))
    # review: half-life shrinks as disagreement grows.
    review_hl = float(max(1.0, review_baseline_hours * (0.25 + 0.75 * agreement)))

    reasons: list[str] = []
    if max_diff > 1.5:
        reasons.append("pairwise_diff_above_normalised_max")
    if agreement < 0.3:
        reasons.append("strong_disagreement")

    return DisagreementVector(
        f_value=f,
        t_value=t,
        d_value=d,
        agreement_score=agreement,
        max_pairwise_diff=max_diff,
        confidence_multiplier=confidence_mult,
        interval_multiplier=interval_mult,
        size_multiplier=size_mult,
        review_halflife_hours=review_hl,
        notes="pairwise_diff_then_multiplicative_penalty",
        reasons=reasons,
    )


def widen_for_disagreement(
    *,
    confidence: float,
    interval_width: float,
    position_size: float,
    disagreement: DisagreementVector,
) -> tuple[float, float, float]:
    """Apply the disagreement protocol to (confidence, interval, size).

    Returns adjusted (confidence, interval_width, position_size).

    The caller is responsible for clamping to physical limits.
    """
    new_confidence = float(confidence) * disagreement.confidence_multiplier
    new_interval = float(interval_width) * disagreement.interval_multiplier
    new_size = float(position_size) * disagreement.size_multiplier
    return (
        max(0.0, min(1.0, new_confidence)),
        max(0.0, new_interval),
        max(0.0, new_size),
    )


__all__ = [
    "DisagreementVector",
    "DISAGREEMENT_DEFAULT",
    "assess_disagreement",
    "widen_for_disagreement",
]
