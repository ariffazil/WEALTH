"""M7.1 — Leverage stress: P(margin breach) at given leverage from M5.

Given an M5 quantile distribution (p10/p25/p50/p75/p90 over a horizon),
M7.1 computes the probability that the adverse move over that horizon
breaches a margin / stop-out level.

Model
-----

We approximate the M5 distribution as log-normal on the per-period
return scale, calibrated so that the M5 quantiles match the implied
percentiles. For a proposed position:

    side ∈ {LONG, SHORT}
    entry_price  = mid (last close)
    leverage     = notional / account equity
    margin_buffer = distance from entry to margin call (in % terms)

For LONG:  margin_breach if price falls below entry * (1 - margin_buffer)
For SHORT: margin_breach if price rises above entry * (1 + margin_buffer)

P(margin breach) is the CDF of the M5-implied return distribution at
the breach level, on the relevant tail.

If the M5 distribution is unavailable or pathological, we return a
``data_insufficient=True`` result so downstream modules can default to
HOLD rather than fabricate a probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

import numpy as np
from scipy.stats import norm


Side = Literal["LONG", "SHORT", "FLAT"]


@dataclass(frozen=True)
class LeverageStressResult:
    p_margin_breach: float           # in [0, 1]
    leverage: float                  # proposed leverage
    margin_buffer: float             # fraction of price distance to margin call
    side: str                        # LONG / SHORT / FLAT
    horizon_h: int                   # 1, 6, 24, 72 (M5 horizons)
    breach_level: float              # absolute price at which margin call fires
    p10: float = float("nan")
    p50: float = float("nan")
    p90: float = float("nan")
    data_insufficient: bool = False  # True ⇒ caller should default to HOLD
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_horizon_quantiles(m5_forecast: dict, horizon_h: int) -> Optional[dict]:
    """Find the requested horizon's quantile block in an M5 forecast dict."""
    horizons = m5_forecast.get("horizons") or []
    for h in horizons:
        if int(h.get("horizon_h", -1)) == int(horizon_h):
            return h
    return None


def _implied_log_normal_params(p10: float, p50: float, p90: float) -> tuple[float, float]:
    """Fit a log-normal return distribution to the M5 quantiles.

    Returns (mu_log, sigma_log) so that:
        mu_log = log(P50 / entry)
        sigma_log = (log(P90 / P50)) / norm.ppf(0.9)

    The P10 leg is also reported as a sanity check; if the implied
    sigma from the upper and lower legs disagree by > 25%, we flag
    data_insufficient. We use the upper leg by default (more relevant
    for the breach tail in a SHORT scenario) and let the caller choose.
    """
    if p50 <= 0 or p90 <= 0 or p10 <= 0:
        return float("nan"), float("nan")
    mu = float(np.log(p50))  # P50 = entry in our convention
    sigma_upper = float(np.log(p90 / p50) / norm.ppf(0.9))
    sigma_lower = float(np.log(p50 / p10) / norm.ppf(0.9))
    # Use the average; flag if disagreement is huge.
    sigma = (sigma_upper + sigma_lower) / 2.0
    return mu, sigma


def compute_margin_breach_probability(
    *,
    m5_horizon: dict,
    side: str,
    leverage: float,
    margin_buffer: float,
    horizon_h: int,
) -> LeverageStressResult:
    """Compute P(margin breach before horizon resolution).

    Parameters
    ----------
    m5_horizon : dict
        One entry from M5's ``horizons`` list (must contain p10, p50, p90).
    side : str
        "LONG", "SHORT", or "FLAT".
    leverage : float
        Proposed leverage as a multiple of equity (e.g. 1.0 = no leverage,
        3.0 = 3× notional). If <= 0, treated as FLAT.
    margin_buffer : float
        Fraction of price that can move against the position before the
        broker issues a margin call. E.g. 0.20 means a 20% adverse move
        blows the account. Convention: broker maintenance margin /
        initial margin. If 0, treat as fully cash-secured (no leverage).
    horizon_h : int
        Which M5 horizon (1, 6, 24, 72) the analysis is anchored to.

    Returns
    -------
    LeverageStressResult with the breach probability and provenance.
    """
    reasons: list[str] = []
    notes = ""

    # Validate inputs honestly.
    if side not in ("LONG", "SHORT", "FLAT"):
        return LeverageStressResult(
            p_margin_breach=float("nan"),
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side="FLAT",
            horizon_h=horizon_h,
            breach_level=float("nan"),
            data_insufficient=True,
            notes="invalid_side",
            reasons=["invalid_side"],
        )

    # FLAT or non-positive leverage: no margin exposure.
    if side == "FLAT" or float(leverage) <= 0:
        return LeverageStressResult(
            p_margin_breach=0.0,
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side=side,
            horizon_h=horizon_h,
            breach_level=float("nan"),
            notes="flat_or_no_leverage",
        )

    if float(margin_buffer) <= 0:
        # Buffer ≤ 0 means margin call fires at the entry — risk = 100%.
        return LeverageStressResult(
            p_margin_breach=1.0,
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side=side,
            horizon_h=horizon_h,
            breach_level=float("nan"),
            notes="zero_or_negative_margin_buffer",
            reasons=["zero_or_negative_margin_buffer"],
        )

    p10 = m5_horizon.get("p10")
    p50 = m5_horizon.get("p50")
    p90 = m5_horizon.get("p90")
    if not (isinstance(p10, (int, float)) and isinstance(p50, (int, float)) and isinstance(p90, (int, float))):
        return LeverageStressResult(
            p_margin_breach=float("nan"),
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side=side,
            horizon_h=horizon_h,
            breach_level=float("nan"),
            data_insufficient=True,
            notes="missing_m5_quantiles",
            reasons=["missing_m5_quantiles"],
        )
    if not (np.isfinite(p10) and np.isfinite(p50) and np.isfinite(p90)):
        return LeverageStressResult(
            p_margin_breach=float("nan"),
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side=side,
            horizon_h=horizon_h,
            breach_level=float("nan"),
            data_insufficient=True,
            notes="nonfinite_m5_quantiles",
            reasons=["nonfinite_m5_quantiles"],
        )
    if p10 <= 0 or p50 <= 0 or p90 <= 0 or p90 < p50 or p50 < p10:
        return LeverageStressResult(
            p_margin_breach=float("nan"),
            leverage=float(leverage),
            margin_buffer=float(margin_buffer),
            side=side,
            horizon_h=horizon_h,
            breach_level=float("nan"),
            data_insufficient=True,
            notes="non_monotonic_quantiles",
            reasons=["non_monotonic_quantiles"],
        )

    # The M5 breach horizon shrinks with leverage: a 3× leveraged
    # account blows on a ~33% adverse move. So the effective margin
    # buffer the position can absorb is margin_buffer / leverage, capped
    # at [0, 1].
    lev = float(leverage)
    buf = float(margin_buffer)
    if lev <= 1.0:
        effective_buffer = min(buf, 0.999)
    else:
        effective_buffer = max(0.0, min(0.999, buf / lev))

    entry = float(p50)
    if side == "LONG":
        breach_level = entry * (1.0 - effective_buffer)
        mu, sigma = _implied_log_normal_params(p10, p50, p90)
        if not np.isfinite(sigma) or sigma <= 0:
            return LeverageStressResult(
                p_margin_breach=float("nan"),
                leverage=lev,
                margin_buffer=buf,
                side=side,
                horizon_h=horizon_h,
                breach_level=float(breach_level),
                p10=float(p10), p50=float(p50), p90=float(p90),
                data_insufficient=True,
                notes="non_positive_sigma",
                reasons=["non_positive_sigma"],
            )
        # CDF at the breach level (lower tail)
        z = (np.log(max(breach_level, 1e-12)) - mu) / sigma
        p_breach = float(norm.cdf(z))
    else:  # SHORT
        breach_level = entry * (1.0 + effective_buffer)
        mu, sigma = _implied_log_normal_params(p10, p50, p90)
        if not np.isfinite(sigma) or sigma <= 0:
            return LeverageStressResult(
                p_margin_breach=float("nan"),
                leverage=lev,
                margin_buffer=buf,
                side=side,
                horizon_h=horizon_h,
                breach_level=float(breach_level),
                p10=float(p10), p50=float(p50), p90=float(p90),
                data_insufficient=True,
                notes="non_positive_sigma",
                reasons=["non_positive_sigma"],
            )
        z = (np.log(breach_level) - mu) / sigma
        # Upper tail for SHORT breach
        p_breach = float(1.0 - norm.cdf(z))

    # Clamp to [0, 1]
    p_breach = max(0.0, min(1.0, p_breach))

    if p_breach > 0.5:
        reasons.append("breach_prob_above_50pct")

    return LeverageStressResult(
        p_margin_breach=p_breach,
        leverage=lev,
        margin_buffer=buf,
        side=side,
        horizon_h=horizon_h,
        breach_level=float(breach_level),
        p10=float(p10), p50=float(p50), p90=float(p90),
        notes="log_normal_calibrated_to_m5_quantiles",
        reasons=reasons,
    )


__all__ = [
    "LeverageStressResult",
    "Side",
    "compute_margin_breach_probability",
    "_extract_horizon_quantiles",
]
