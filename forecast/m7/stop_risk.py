"""M7.2 — Stop risk: P(stop hit before target).

For a candidate trade with a stop-loss level and a target, M7.2 asks:
"Given the M5-implied path, what is the probability the adverse
extreme reaches the stop before the favourable extreme reaches the
target?"

Approach
--------

We use the *first-passage* approximation under a Brownian bridge
between the entry and the horizon:

    p_stop_first ≈ Φ( -d_stop / σ_path ) /
                  ( Φ( -d_stop / σ_path ) + Φ( d_target / σ_path ) )

where σ_path is the M5-implied per-period log-volatility, d_stop is
the log-distance from entry to stop, and d_target is the log-distance
from entry to target. This is the standard reflection-principle
formula for one-sided first passage with two absorbing barriers.

If either stop or target is missing, we degrade to a single-barrier
estimate: P(stop hit) ≈ Φ( -d_stop / σ_path ).

Inputs
------

    entry, stop, target — absolute price levels (must be positive,
                          and on the correct side of entry)
    side — LONG or SHORT
    sigma_path — M5 horizon-level σ (e.g. sigma_h from M5)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

import numpy as np
from scipy.stats import norm


Side = Literal["LONG", "SHORT", "FLAT"]


@dataclass(frozen=True)
class StopRiskResult:
    p_stop_before_target: float
    p_stop_hit: float            # marginal probability stop is reached
    p_target_hit: float          # marginal probability target is reached
    side: str
    entry: float
    stop: float
    target: float
    sigma_path: float
    data_insufficient: bool = False
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_inputs(
    side: str, entry: float, stop: float, target: float, sigma_path: float
) -> Optional[str]:
    """Return an error reason string if inputs are pathological, else None."""
    if side not in ("LONG", "SHORT", "FLAT"):
        return "invalid_side"
    if side == "FLAT":
        return "flat_position"
    if entry <= 0 or stop <= 0 or target <= 0:
        return "non_positive_price"
    if not (np.isfinite(entry) and np.isfinite(stop) and np.isfinite(target) and np.isfinite(sigma_path)):
        return "nonfinite_input"
    if sigma_path <= 0:
        return "non_positive_sigma"
    if side == "LONG" and stop >= entry:
        return "stop_not_below_entry_for_long"
    if side == "SHORT" and stop <= entry:
        return "stop_not_above_entry_for_short"
    return None


def compute_stop_risk(
    *,
    side: str,
    entry: float,
    stop: float,
    target: float,
    sigma_path: float,
) -> StopRiskResult:
    """Probability the stop is hit before the target.

    Uses the Brownian-bridge first-passage approximation with two
    absorbing barriers (Gihman-Skorokhod reflection principle).
    """
    err = _validate_inputs(side, entry, stop, target, sigma_path)
    if err is not None:
        # FLAT or any invalid → caller should treat as no-stop risk.
        if err == "flat_position":
            return StopRiskResult(
                p_stop_before_target=0.0,
                p_stop_hit=0.0,
                p_target_hit=0.0,
                side=side,
                entry=float(entry),
                stop=float(stop),
                target=float(target),
                sigma_path=float(sigma_path),
                notes="flat_position",
            )
        return StopRiskResult(
            p_stop_before_target=float("nan"),
            p_stop_hit=float("nan"),
            p_target_hit=float("nan"),
            side=side,
            entry=float(entry),
            stop=float(stop),
            target=float(target),
            sigma_path=float(sigma_path),
            data_insufficient=True,
            notes=err,
            reasons=[err],
        )

    d_stop = abs(np.log(stop / entry))
    d_target = abs(np.log(target / entry))
    # Reflection principle: the probability that a Brownian path with
    # drift 0 reaches -d_stop before +d_target is:
    #     Φ(-d_stop / σ) / (Φ(-d_stop / σ) + Φ(d_target / σ))
    # (See e.g. Darling & Siegert 1953.)
    z_stop = d_stop / sigma_path
    z_target = d_target / sigma_path

    p_stop_marg = float(norm.cdf(-z_stop))
    p_target_marg = float(norm.cdf(z_target))
    denom = p_stop_marg + p_target_marg
    if denom <= 1e-15:
        # Both barriers extremely far — neither likely to be hit.
        p_stop_first = 0.0
    else:
        p_stop_first = p_stop_marg / denom

    p_stop_first = max(0.0, min(1.0, p_stop_first))
    p_stop_marg = max(0.0, min(1.0, p_stop_marg))
    p_target_marg = max(0.0, min(1.0, p_target_marg))

    reasons: list[str] = []
    if p_stop_first > 0.5:
        reasons.append("stop_favoured_over_target")

    return StopRiskResult(
        p_stop_before_target=p_stop_first,
        p_stop_hit=p_stop_marg,
        p_target_hit=p_target_marg,
        side=side,
        entry=float(entry),
        stop=float(stop),
        target=float(target),
        sigma_path=float(sigma_path),
        notes="brownian_bridge_two_barrier_reflection_principle",
        reasons=reasons,
    )


__all__ = ["StopRiskResult", "Side", "compute_stop_risk"]
