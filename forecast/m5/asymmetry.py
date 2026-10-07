"""M5.3 — upside vs downside asymmetry via semivariance.

M5 emits an *asymmetry score* ∈ [-1, 1]:

    asym = (semivar_up - semivar_down) / (semivar_up + semivar_down + ε)

A positive value means upside variance dominates the recent window
(more upside dispersion than downside); negative means downside
dispersion dominates. The score is mapped to a *range shift*:

    upper_half  = expected_range * (1 + asym) / 2
    lower_half  = expected_range * (1 - asym) / 2

So M5's high-low band is *not* symmetric — the high is pulled up by
upside variance, the low is pulled down by downside variance. The
*median* (P50) is still M0.

Asymmetry score is bound to ±1 and clipped to keep the math finite.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AsymmetryForecast:
    asymmetry_score: float  # in [-1, 1]
    upper_half: float  # price units above center
    lower_half: float  # price units below center
    sv_up: float
    sv_down: float
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "asymmetry_score": self.asymmetry_score,
            "upper_half": self.upper_half,
            "lower_half": self.lower_half,
            "sv_up": self.sv_up,
            "sv_down": self.sv_down,
            "notes": self.notes,
        }


def forecast_asymmetry(
    df: pd.DataFrame,
    *,
    horizon_h: int,
    expected_range: float,
    sv_up_24h: float,
    sv_down_24h: float,
) -> AsymmetryForecast:
    """Estimate the asymmetry of the forecast range.

    Parameters
    ----------
    df
        1H OHLCV frame (used for robustness checks).
    horizon_h
        Forward horizon in hours (currently informational).
    expected_range
        M5.2 expected (high - low) over the horizon.
    sv_up_24h
        Upside semivariance (annualised) over the last 24 hours.
    sv_down_24h
        Downside semivariance (annualised) over the last 24 hours.
    """
    if not (np.isfinite(sv_up_24h) and np.isfinite(sv_down_24h)):
        return AsymmetryForecast(
            asymmetry_score=0.0,
            upper_half=expected_range * 0.5 if np.isfinite(expected_range) else float("nan"),
            lower_half=expected_range * 0.5 if np.isfinite(expected_range) else float("nan"),
            sv_up=float("nan"),
            sv_down=float("nan"),
            notes="semivariance_unavailable",
        )

    eps = 1e-12
    denom = sv_up_24h + sv_down_24h
    if denom <= eps:
        asym = 0.0
    else:
        asym = float(np.clip((sv_up_24h - sv_down_24h) / (denom + eps), -1.0, 1.0))

    if not np.isfinite(expected_range) or expected_range <= 0:
        upper = float("nan")
        lower = float("nan")
    else:
        # expected_range is the full price-range width (high-low). Split
        # by asymmetry: positive asym widens the upper half.
        upper = expected_range * (1.0 + asym) / 2.0
        lower = expected_range * (1.0 - asym) / 2.0

    return AsymmetryForecast(
        asymmetry_score=asym,
        upper_half=upper,
        lower_half=lower,
        sv_up=float(sv_up_24h),
        sv_down=float(sv_down_24h),
        notes="semivariance_normalised_asymmetry",
    )


__all__ = ["AsymmetryForecast", "forecast_asymmetry"]