"""M5.6 — touch probability for ±2σ levels.

Given the M5 forecast (volatility, range, asymmetry, expansion prob)
we estimate the probability that the future path *touches* the
±2σ_horizon levels over the forecast horizon.

Approach
========

We approximate the future log-return as a Brownian bridge starting
from 0 and *ending* at the forecast median offset (0 by M5 design,
because P50 = M0). With volatility σ_h and Student-t heavy-tail
scaling ν=6:

    p_touch_upper = P( max_{τ∈[0,h]} W_τ ≥ +2σ )
                   = 2 * Φ(-2 / sqrt(h_inv)) * sqrt(h_inv)
                   ≈ 2 * (1 - Φ(2)) for unit horizon
    For heavy tails, scale by Student-t tail probability.

We use a closed-form first-passage approximation (Poisson-clipped):

    p_touch_upper ≈ 2 * (1 - Φ(2 / √h))     for the Gaussian core
    p_touch_lower ≈ 2 * Φ(-2 / √h)
    heavy_tail_uplift = (1 + (ν-2)/ν)^{-1}   # scale at ν=6: 0.816

Then we *boost* the touch probability when:

    * expansion probability > 0.5 (vol expansion is happening)
    * asymmetry score > 0.3 (upside tilt) for upper; < -0.3 for lower
    * compression percentile > 0.9 (squeezed — reversion more likely)

The boost is additive but capped at 0.95 per side.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class TouchProb:
    p_touch_upper_2sigma: float
    p_touch_lower_2sigma: float
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "p_touch_upper_2sigma": self.p_touch_upper_2sigma,
            "p_touch_lower_2sigma": self.p_touch_lower_2sigma,
            "notes": self.notes,
        }


def touch_probability_2sigma(
    *,
    horizon_h: int,
    sigma_h1: float,
    p_vol_expansion: float = 0.0,
    asymmetry_score: float = 0.0,
    compression_percentile: float = 0.5,
    nu: float = 6.0,
) -> TouchProb:
    """Estimate the probability of touching ±2σ levels over the horizon."""
    if not np.isfinite(sigma_h1) or sigma_h1 <= 0 or horizon_h <= 0:
        return TouchProb(
            p_touch_upper_2sigma=float("nan"),
            p_touch_lower_2sigma=float("nan"),
            notes="invalid_inputs",
        )

    sqrt_h = np.sqrt(float(horizon_h))
    # ±2σ level in normalised units
    z = 2.0 / sqrt_h  # divide by sqrt(h) so that over h hours, the bound is +2σ_h

    # First-passage probability (Poisson bound) for Brownian motion starting at 0
    # P(sup >= L) over horizon [0, 1] with σ=1 is roughly 2 * (1 - Φ(L))
    # We scale z = 2/sqrt(h) so for h=1 we have 2 (the level), and for
    # h=4 we have 1 (so 2σ/h level -> the σ value, which is 2σ_h/σ_h=2 in
    # scaled units).
    p_up_base = float(2.0 * (1.0 - norm.cdf(z)))
    p_dn_base = float(2.0 * norm.cdf(-z))

    # Heavy-tail uplift: t-distribution gives higher tail probability
    # than Gaussian with the same scale. Use an additive inflation.
    if np.isfinite(nu) and nu > 2:
        t_scale = float(np.sqrt((nu - 2.0) / nu))  # < 1
        # We *rescale* σ so the tails become fatter; the actual touch
        # prob with Student-t innovations is roughly p_base / t_scale
        # for the same level. Capped to 0.95.
        p_up = float(np.clip(p_up_base / t_scale, 0.0, 0.95))
        p_dn = float(np.clip(p_dn_base / t_scale, 0.0, 0.95))
    else:
        p_up = float(np.clip(p_up_base, 0.0, 0.95))
        p_dn = float(np.clip(p_dn_base, 0.0, 0.95))

    # Boost from vol expansion — symmetric uplift capped at +0.20
    if np.isfinite(p_vol_expansion) and p_vol_expansion > 0.5:
        boost = float(np.clip(0.4 * (p_vol_expansion - 0.5), 0.0, 0.2))
        p_up = float(np.clip(p_up + boost, 0.0, 0.95))
        p_dn = float(np.clip(p_dn + boost, 0.0, 0.95))

    # Asymmetry uplift — positive asym lifts upper, negative lifts lower
    if np.isfinite(asymmetry_score):
        asym_uplift = float(np.clip(abs(asymmetry_score) * 0.10, 0.0, 0.10))
        if asymmetry_score > 0:
            p_up = float(np.clip(p_up + asym_uplift, 0.0, 0.95))
        else:
            p_dn = float(np.clip(p_dn + asym_uplift, 0.0, 0.95))

    # Compression: high compression percentile → next move is more likely
    # to "break out" — uplift both sides slightly.
    if np.isfinite(compression_percentile) and compression_percentile > 0.9:
        squeeze_uplift = float(np.clip((compression_percentile - 0.9) * 0.5, 0.0, 0.05))
        p_up = float(np.clip(p_up + squeeze_uplift, 0.0, 0.95))
        p_dn = float(np.clip(p_dn + squeeze_uplift, 0.0, 0.95))

    return TouchProb(
        p_touch_upper_2sigma=float(p_up),
        p_touch_lower_2sigma=float(p_dn),
        notes="first_passage_brownian_plus_uplifts",
    )


__all__ = ["TouchProb", "touch_probability_2sigma"]