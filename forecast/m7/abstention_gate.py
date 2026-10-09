"""M7.7 — Abstention / safety gate: ACT / REDUCE / HOLD / BLOCK verdict.

The verdict is determined by the regime-action table:

    regime               | survival_p ≥ 0.9 | survival_p 0.7–0.9 | survival_p < 0.7
    ---------------------+------------------+----------------------+--------------------
    RANGE                | ACT (size=base)  | REDUCE (size×0.5)    | HOLD
    COMPRESSION          | REDUCE (size×0.5)| REDUCE (size×0.25)   | HOLD
    TRENDING             | ACT (size=base)  | REDUCE (size×0.5)    | BLOCK
    EVENT_RISK           | REDUCE (size×0.5)| HOLD                 | BLOCK

Definitions:

    survival_p = 1 - p_margin_breach    (from M7.1)
    regime     ∈ {RANGE, COMPRESSION, TRENDING, EVENT_RISK}  (from M5.7)

HARD BLOCKS (override the table):

    * p_margin_breach > alpha (default 0.10) ⇒ BLOCK
    * survival_p < 0.5 ⇒ BLOCK (no matter the regime)
    * stop_favoured_over_target (p_stop_first > 0.6) ⇒ BLOCK or REDUCE
    * CVaR exceeds max acceptable loss ⇒ BLOCK
    * data_insufficient on any required module ⇒ HOLD
    * strong disagreement between F/T/D ⇒ at least REDUCE
    * participation > 50% of ADV ⇒ BLOCK (cannot liquidate cleanly)

MAY_NOT:
    * may_increase_size = False
    * may_override_human = False

Outputs:

    verdict ∈ {ACT, REDUCE, HOLD, BLOCK}
    size_multiplier ∈ [0, 1]   — what fraction of base size to use
    reason_codes — list of strings explaining the verdict
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

import numpy as np


Verdict = Literal["ACT", "REDUCE", "HOLD", "BLOCK"]


VERDICTS = ("ACT", "REDUCE", "HOLD", "BLOCK")


# Regime → action table (per spec). Each entry is (survival_p threshold,
# base_size_multiplier). Three tiers: >=0.9, >=0.7, <0.7.
# Tuples: (verdict, size_multiplier)
REGIME_ACTION_TABLE: dict[str, tuple[tuple[Verdict, float], tuple[Verdict, float], tuple[Verdict, float]]] = {
    # regime:        (>=0.9,                 0.7–0.9,              <0.7)
    "RANGE":         (("ACT",    1.0),       ("REDUCE", 0.5),       ("HOLD",  0.0)),
    "COMPRESSION":   (("REDUCE", 0.5),       ("REDUCE", 0.25),      ("HOLD",  0.0)),
    "TRENDING":      (("ACT",    1.0),       ("REDUCE", 0.5),       ("BLOCK", 0.0)),
    "EVENT_RISK":    (("REDUCE", 0.5),       ("HOLD",   0.0),       ("BLOCK", 0.0)),
}


# Default alpha — survival probability threshold.
DEFAULT_ALPHA = 0.10


@dataclass(frozen=True)
class RegimeAction:
    regime: str
    survival_p: float
    base_verdict: Verdict
    base_size_multiplier: float


@dataclass(frozen=True)
class SafetyGateVerdict:
    verdict: Verdict
    size_multiplier: float         # in [0, 1]
    regime: str
    survival_prob: float
    regime_action: RegimeAction
    alpha: float
    reason_codes: list[str] = field(default_factory=list)
    notes: str = ""
    hard_block: bool = False        # True if a hard-block rule fired

    def to_dict(self) -> dict:
        return asdict(self)


def _lookup_regime_action(regime: str, survival_p: float) -> RegimeAction:
    """Pick the regime-action tuple from the table based on survival_p."""
    if regime not in REGIME_ACTION_TABLE:
        regime = "RANGE"
    hi, mid, lo = REGIME_ACTION_TABLE[regime]
    if survival_p >= 0.9:
        verdict, mult = hi
    elif survival_p >= 0.7:
        verdict, mult = mid
    else:
        verdict, mult = lo
    return RegimeAction(
        regime=regime,
        survival_p=survival_p,
        base_verdict=verdict,
        base_size_multiplier=mult,
    )


def decide_safety_gate(
    *,
    regime: str,
    p_margin_breach: float,
    p_stop_before_target: float = 0.0,
    cvar_exceeds_max_loss: bool = False,
    participation_above_50pct: bool = False,
    strong_disagreement: bool = False,
    data_insufficient: bool = False,
    alpha: float = DEFAULT_ALPHA,
    flat_position: bool = False,
) -> SafetyGateVerdict:
    """Compute the safety gate verdict.

    Parameters
    ----------
    regime : str
        M5.7 regime label ∈ {"RANGE", "COMPRESSION", "TRENDING", "EVENT_RISK"}.
    p_margin_breach : float
        M7.1 result. survival_p = 1 - p_margin_breach.
    p_stop_before_target : float
        M7.2 result. > 0.6 is treated as a strong negative signal.
    cvar_exceeds_max_loss : bool
        True if M7.3 CVaR is larger than the user's max acceptable loss.
    participation_above_50pct : bool
        True if order size exceeds 50% of ADV — cannot liquidate cleanly.
    strong_disagreement : bool
        True if F/T/D organs strongly disagree (per disagreement.py).
    data_insufficient : bool
        True if any required M7 module returned data_insufficient=True.
    alpha : float
        Hard survival-probability threshold. Default 0.10 (i.e. we block
        if p_margin_breach > 10%).
    flat_position : bool
        If the proposed position is FLAT, the verdict is ACT with size
        0 — there is nothing to trade.

    Returns
    -------
    SafetyGateVerdict with verdict, size_multiplier, and reason codes.
    """
    reasons: list[str] = []
    notes_parts = []

    # Flat position short-circuits to ACT with size 0.
    if flat_position:
        return SafetyGateVerdict(
            verdict="ACT",
            size_multiplier=0.0,
            regime=regime,
            survival_prob=1.0,
            regime_action=_lookup_regime_action("RANGE", 1.0),
            alpha=alpha,
            reason_codes=["flat_position_zero_size"],
            notes="flat_position_no_risk",
            hard_block=False,
        )

    # Validate alpha
    if not (np.isfinite(alpha) and 0 < alpha < 1):
        reasons.append("invalid_alpha_using_default")
        alpha = DEFAULT_ALPHA

    survival_p = 1.0 - float(p_margin_breach) if np.isfinite(p_margin_breach) else 0.0
    survival_p = max(0.0, min(1.0, survival_p))

    regime_action = _lookup_regime_action(regime, survival_p)
    verdict = regime_action.base_verdict
    size_mult = regime_action.base_size_multiplier
    hard_block = False

    # Hard block rules
    if data_insufficient:
        # Insufficient data ⇒ HOLD, not BLOCK (we don't know the answer
        # is dangerous, we just can't decide).
        reasons.append("data_insufficient")
        notes_parts.append("data_insufficient_hold")
        return SafetyGateVerdict(
            verdict="HOLD",
            size_multiplier=0.0,
            regime=regime,
            survival_prob=survival_p,
            regime_action=regime_action,
            alpha=alpha,
            reason_codes=reasons,
            notes=";".join(notes_parts),
            hard_block=False,
        )

    # Hard block rules — the constraint equation P(margin breach) < alpha
    # is the spec-level invariant. If the breach exceeds alpha, the
    # mission is violated regardless of regime. The regime table
    # governs intermediate verdicts *within* the constraint, not
    # against it.
    if float(p_margin_breach) > alpha:
        reasons.append("p_margin_breach_above_alpha")
        verdict = "BLOCK"
        size_mult = 0.0
        hard_block = True

    if survival_p < 0.5 and verdict != "BLOCK":
        reasons.append("survival_p_below_50pct")
        verdict = "BLOCK"
        size_mult = 0.0
        hard_block = True

    if p_stop_before_target > 0.6 and verdict == "ACT":
        reasons.append("stop_favoured_over_target")
        verdict = "REDUCE"
        size_mult = min(size_mult, 0.25)

    if p_stop_before_target > 0.8 and verdict != "BLOCK":
        reasons.append("stop_extreme")
        verdict = "BLOCK"
        size_mult = 0.0
        hard_block = True

    if cvar_exceeds_max_loss:
        reasons.append("cvar_exceeds_max_acceptable_loss")
        verdict = "BLOCK"
        size_mult = 0.0
        hard_block = True

    if participation_above_50pct:
        reasons.append("participation_above_50pct_adv")
        verdict = "BLOCK"
        size_mult = 0.0
        hard_block = True

    # Disagreement: never downgrade past BLOCK, but force at least REDUCE.
    if strong_disagreement and verdict == "ACT":
        reasons.append("strong_disagreement_force_reduce")
        verdict = "REDUCE"
        size_mult = min(size_mult, 0.5)
    elif strong_disagreement and verdict == "REDUCE":
        reasons.append("strong_disagreement_shrinks_size")
        size_mult = min(size_mult, 0.25)

    # Final safety: ACT implies survival_p >= 0.9 — anything less forces REDUCE.
    if verdict == "ACT" and survival_p < 0.9:
        reasons.append("act_requires_survival_p_above_0_9")
        verdict = "REDUCE"
        size_mult = min(size_mult, 0.5)

    notes_parts.append(f"regime_action:{regime}_{survival_p:.2f}")
    if hard_block:
        notes_parts.append("hard_block")

    return SafetyGateVerdict(
        verdict=verdict,
        size_multiplier=float(max(0.0, min(1.0, size_mult))),
        regime=regime if regime in REGIME_ACTION_TABLE else "RANGE",
        survival_prob=survival_p,
        regime_action=regime_action,
        alpha=float(alpha),
        reason_codes=reasons,
        notes=";".join(notes_parts),
        hard_block=hard_block,
    )


__all__ = [
    "Verdict",
    "VERDICTS",
    "REGIME_ACTION_TABLE",
    "DEFAULT_ALPHA",
    "RegimeAction",
    "SafetyGateVerdict",
    "decide_safety_gate",
]
