"""M7.3 — Expected shortfall (CVaR) at confidence level alpha.

CVaR (also called Expected Shortfall) is the expected loss conditional
on the loss exceeding the VaR threshold. It is the coherent tail-risk
measure that VaR is not.

Given an M5 quantile distribution, we approximate CVaR at level
``alpha`` (default alpha=0.05 — the worst 5% of outcomes) by:

    CVaR_alpha = E[L | L > VaR_alpha]

Implementation
--------------

Two paths:

1. **Parametric** (default): if the M5 quantiles are well-formed, we
   fit a log-normal return distribution to (p10, p50, p90), then
   compute the analytic CVaR under that distribution. This is the
   fast path used when M5's quantiles are honest.

2. **Honest fallback**: if the quantiles are missing or pathological,
   we return data_insufficient=True so the caller defaults to HOLD.

Notes
-----

* All losses are reported as positive numbers. CVaR is the magnitude
  of expected loss in the worst tail.
* The function does NOT add the liquidation cost — that's M7.4.
  CVaR is the price-side shortfall only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class CVaRResult:
    cvar_alpha: float                # expected shortfall in price units (positive)
    var_alpha: float                 # VaR in price units (positive)
    alpha: float                     # tail level (e.g. 0.05)
    horizon_h: int
    side: str                        # LONG / SHORT / FLAT — CVaR direction matters
    p10: float = float("nan")
    p50: float = float("nan")
    p90: float = float("nan")
    data_insufficient: bool = False
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def compute_cvar(
    *,
    m5_horizon: dict,
    side: str,
    horizon_h: int,
    alpha: float = 0.05,
) -> CVaRResult:
    """Compute CVaR at level alpha.

    Parameters
    ----------
    m5_horizon : dict
        Single horizon block from M5 (p10, p50, p90).
    side : str
        "LONG" measures downside shortfall (P[L < VaR]).
        "SHORT" measures upside shortfall (P[L > VaR] where L = price-up).
        "FLAT" returns 0.
    horizon_h : int
        The horizon label (1, 6, 24, 72).
    alpha : float
        Tail probability. Default 0.05 (worst 5%).

    Returns
    -------
    CVaRResult. The shortfall is reported as a positive price-unit
    number representing the expected adverse excursion in the tail.
    """
    if not (0.0 < alpha < 1.0):
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            data_insufficient=True,
            notes="invalid_alpha",
            reasons=["invalid_alpha"],
        )

    if side == "FLAT":
        return CVaRResult(
            cvar_alpha=0.0,
            var_alpha=0.0,
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            notes="flat_position",
        )

    if side not in ("LONG", "SHORT"):
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            data_insufficient=True,
            notes="invalid_side",
            reasons=["invalid_side"],
        )

    p10 = m5_horizon.get("p10")
    p50 = m5_horizon.get("p50")
    p90 = m5_horizon.get("p90")
    if not (isinstance(p10, (int, float)) and isinstance(p50, (int, float)) and isinstance(p90, (int, float))):
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            data_insufficient=True,
            notes="missing_m5_quantiles",
            reasons=["missing_m5_quantiles"],
        )
    if not (np.isfinite(p10) and np.isfinite(p50) and np.isfinite(p90)):
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            data_insufficient=True,
            notes="nonfinite_m5_quantiles",
            reasons=["nonfinite_m5_quantiles"],
        )
    if p10 <= 0 or p50 <= 0 or p90 <= 0 or p90 < p50 or p50 < p10:
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            data_insufficient=True,
            notes="non_monotonic_quantiles",
            reasons=["non_monotonic_quantiles"],
        )

    # Fit log-normal to the M5 quantiles.
    mu = float(np.log(p50))
    sigma_upper = float(np.log(p90 / p50) / norm.ppf(0.9))
    # Lower leg: use abs() because z(0.1) is negative — we want a positive sigma.
    sigma_lower = float(np.log(p50 / p10) / abs(norm.ppf(0.1)))
    sigma = (sigma_upper + sigma_lower) / 2.0
    if sigma <= 0 or not np.isfinite(sigma):
        return CVaRResult(
            cvar_alpha=float("nan"),
            var_alpha=float("nan"),
            alpha=alpha,
            horizon_h=horizon_h,
            side=side,
            p10=float(p10), p50=float(p50), p90=float(p90),
            data_insufficient=True,
            notes="non_positive_sigma",
            reasons=["non_positive_sigma"],
        )

    # Analytic CVaR under log-normal:
    #   For X ~ LogNormal(mu, sigma), let Z = (log X - mu)/sigma ~ N(0,1).
    #   For LONG-side downside tail with probability alpha:
    #       VaR_alpha = exp(mu + sigma * Φ^{-1}(alpha))
    #       CVaR_alpha = E[X | X <= VaR_alpha]
    #                  = exp(mu + sigma^2/2) * Φ(z_alpha - sigma) / alpha
    #   See e.g. Glasserman, Monte Carlo Methods in Financial Engineering.
    z_alpha = float(norm.ppf(alpha))
    var_price = float(np.exp(mu + sigma * z_alpha))

    if side == "LONG":
        # Lower-tail CVaR
        expected_tail = float(np.exp(mu + 0.5 * sigma ** 2) * norm.cdf(z_alpha - sigma) / alpha)
        var_alpha_price = float(var_price)
        cvar_price = float(p50 - expected_tail)  # loss = entry - tail mean
        var_loss = float(p50 - var_alpha_price)
    else:  # SHORT
        # Upper-tail CVaR — use the symmetric formula at 1-alpha
        z_upper = float(norm.ppf(1.0 - alpha))
        var_alpha_price = float(np.exp(mu + sigma * z_upper))
        expected_tail = float(np.exp(mu + 0.5 * sigma ** 2) * (1.0 - norm.cdf(z_upper - sigma)) / alpha)
        cvar_price = float(expected_tail - p50)  # loss = tail mean - entry
        var_loss = float(var_alpha_price - p50)

    # Floor at 0; CVaR must be positive.
    cvar_price = max(0.0, float(cvar_price))
    var_loss = max(0.0, float(var_loss))

    return CVaRResult(
        cvar_alpha=cvar_price,
        var_alpha=var_loss,
        alpha=alpha,
        horizon_h=horizon_h,
        side=side,
        p10=float(p10), p50=float(p50), p90=float(p90),
        notes="log_normal_analytic_cvar",
    )


__all__ = ["CVaRResult", "compute_cvar"]
