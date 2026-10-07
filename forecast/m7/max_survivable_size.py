"""M7.5 — Max survivable size (Kelly criterion × survival probability).

The Kelly criterion gives the fraction of bankroll that maximises
long-run growth for a binary or normal-edge bet:

    f* = (edge / variance)   — for a normal distribution of returns

We use the M5-implied (mu, sigma) and a direction derived from the
fundamentals+technical signal (passed in as ``edge_log``) to compute
the raw Kelly fraction, then deflate it by:

    * the survival probability (1 - p_margin_breach)
    * a disagreement penalty (multiplicative, see disagreement.py)
    * a half-life penalty (if the thesis is decaying fast, cut size)
    * a liquidity penalty (round-trip cost as a fraction of edge)

The output is the *maximum* size the model is willing to authorise.
M7 may never INCREASE size — the ceiling is the model's authorisation,
the actual size is the sovereign's choice.

If edge / survival inputs are missing or pathological, return
data_insufficient=True.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

import numpy as np


Side = Literal["LONG", "SHORT", "FLAT"]


@dataclass(frozen=True)
class MaxSurvivableSizeResult:
    kelly_fraction_raw: float       # unconstrained Kelly fraction of equity
    kelly_fraction_survival: float  # after survival-prob deflation
    kelly_fraction_final: float     # after disagreement, half-life, cost
    max_survivable_size_usd: float  # kelly_fraction_final * equity
    edge_log: float                 # log-return edge (mu_per_period)
    sigma_log: float                # log-return sigma (per period)
    survival_prob: float            # 1 - p_margin_breach (clamped)
    disagreement_penalty: float
    half_life_penalty: float
    cost_penalty: float
    equity_usd: float
    data_insufficient: bool = False
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Conservative fraction: half-Kelly is the academic recommendation for
# noisy edge estimation. We use quarter-Kelly because M7 is the safety
# organ — underestimating size is preferred to overestimating.
KELLY_FRACTION_OF_RAW = 0.25


def compute_max_survivable_size(
    *,
    edge_log: float,
    sigma_log: float,
    survival_prob: float,
    equity_usd: float,
    round_trip_cost_bps: float = 0.0,
    disagreement_penalty: float = 1.0,
    half_life_penalty: float = 1.0,
    kelly_fraction_of_raw: float = KELLY_FRACTION_OF_RAW,
) -> MaxSurvivableSizeResult:
    """Compute the max survivable size in USD.

    Parameters
    ----------
    edge_log : float
        Log-return edge per period (positive = expected gain). M7 does
        not forecast — the edge must come from an upstream signal
        (M5 distribution asymmetry, M2 regime, etc.).
    sigma_log : float
        Per-period log-return volatility.
    survival_prob : float
        1 - p_margin_breach, clamped to [0, 1]. If ≤ 0 ⇒ BLOCK.
    equity_usd : float
        Account equity used to scale the Kelly fraction.
    round_trip_cost_bps : float
        Total round-trip cost from M7.4. Used to subtract a flat
        cost drag from the edge.
    disagreement_penalty : float
        Multiplicative penalty in [0, 1]. 1.0 = no disagreement.
    half_life_penalty : float
        Multiplicative penalty in [0, 1]. 1.0 = stable thesis.
    kelly_fraction_of_raw : float
        Fraction of raw Kelly to use (default quarter-Kelly for safety).
    """
    reasons: list[str] = []

    if not (np.isfinite(edge_log)):
        return MaxSurvivableSizeResult(
            kelly_fraction_raw=float("nan"),
            kelly_fraction_survival=float("nan"),
            kelly_fraction_final=float("nan"),
            max_survivable_size_usd=float("nan"),
            edge_log=float(edge_log),
            sigma_log=float(sigma_log),
            survival_prob=float(survival_prob),
            disagreement_penalty=float(disagreement_penalty),
            half_life_penalty=float(half_life_penalty),
            cost_penalty=float("nan"),
            equity_usd=float(equity_usd),
            data_insufficient=True,
            notes="nonfinite_edge",
            reasons=["nonfinite_edge"],
        )

    if not (np.isfinite(sigma_log) and sigma_log > 0):
        return MaxSurvivableSizeResult(
            kelly_fraction_raw=float("nan"),
            kelly_fraction_survival=float("nan"),
            kelly_fraction_final=float("nan"),
            max_survivable_size_usd=float("nan"),
            edge_log=float(edge_log),
            sigma_log=float(sigma_log),
            survival_prob=float(survival_prob),
            disagreement_penalty=float(disagreement_penalty),
            half_life_penalty=float(half_life_penalty),
            cost_penalty=float("nan"),
            equity_usd=float(equity_usd),
            data_insufficient=True,
            notes="non_positive_sigma",
            reasons=["non_positive_sigma"],
        )

    if not (np.isfinite(equity_usd) and equity_usd > 0):
        return MaxSurvivableSizeResult(
            kelly_fraction_raw=float("nan"),
            kelly_fraction_survival=float("nan"),
            kelly_fraction_final=float("nan"),
            max_survivable_size_usd=float("nan"),
            edge_log=float(edge_log),
            sigma_log=float(sigma_log),
            survival_prob=float(survival_prob),
            disagreement_penalty=float(disagreement_penalty),
            half_life_penalty=float(half_life_penalty),
            cost_penalty=float("nan"),
            equity_usd=float(equity_usd),
            data_insufficient=True,
            notes="non_positive_equity",
            reasons=["non_positive_equity"],
        )

    # Subtract cost drag from the edge. cost_penalty = exp(-round_trip_cost_bps/10000)
    # acts as a multiplicative shrink of the edge (approximation for
    # small costs).
    if not (np.isfinite(round_trip_cost_bps) and round_trip_cost_bps >= 0):
        reasons.append("invalid_cost_bps_using_zero")
        round_trip_cost_bps = 0.0
    cost_penalty = float(np.exp(-round_trip_cost_bps / 10_000.0))

    effective_edge = float(edge_log) * cost_penalty

    # Raw Kelly fraction (normal-distribution form): f* = mu / sigma^2.
    # Cap at +/- 1.
    raw_kelly = effective_edge / (sigma_log ** 2)
    raw_kelly = max(-1.0, min(1.0, raw_kelly))

    # Deflate by survival probability. If survival is low, size is low.
    sp = float(survival_prob)
    if not (np.isfinite(sp)):
        sp = 0.0
        reasons.append("nonfinite_survival_clamped_to_zero")
    sp = max(0.0, min(1.0, sp))
    survival_kelly = raw_kelly * sp

    # Apply disagreement + half-life penalties.
    if not (np.isfinite(disagreement_penalty) and 0 <= disagreement_penalty <= 1):
        disagreement_penalty = 1.0
        reasons.append("invalid_disagreement_penalty_using_one")
    if not (np.isfinite(half_life_penalty) and 0 <= half_life_penalty <= 1):
        half_life_penalty = 1.0
        reasons.append("invalid_half_life_penalty_using_one")

    final_kelly = survival_kelly * disagreement_penalty * half_life_penalty
    final_kelly = max(-1.0, min(1.0, final_kelly))

    # Apply the safety fraction (default quarter-Kelly).
    final_kelly_safe = final_kelly * float(kelly_fraction_of_raw)
    final_kelly_safe = max(0.0, final_kelly_safe)  # size is always non-negative

    # Convert to USD. We use absolute size — the sign is carried by
    # the calling code, not by negative USD notional.
    if raw_kelly < 0 or survival_kelly < 0:
        reasons.append("negative_edge_after_deflation")

    max_size_usd = float(final_kelly_safe * equity_usd)

    return MaxSurvivableSizeResult(
        kelly_fraction_raw=raw_kelly,
        kelly_fraction_survival=survival_kelly,
        kelly_fraction_final=final_kelly_safe,
        max_survivable_size_usd=max_size_usd,
        edge_log=float(edge_log),
        sigma_log=float(sigma_log),
        survival_prob=sp,
        disagreement_penalty=float(disagreement_penalty),
        half_life_penalty=float(half_life_penalty),
        cost_penalty=cost_penalty,
        equity_usd=float(equity_usd),
        notes=f"kelly_mu_over_sigma2_x{kelly_fraction_of_raw}",
        reasons=reasons,
    )


__all__ = ["MaxSurvivableSizeResult", "Side", "compute_max_survivable_size", "KELLY_FRACTION_OF_RAW"]
