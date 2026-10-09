"""M5.2 — future high-low range forecast.

The future range is the expected absolute high-low excursion over the
forecast horizon. M5 forecasts it from a volatility-conditioned model:

    E[high - low | horizon] = k(σ, h)

with k estimated from realised (high - low) over rolling windows of
length ``h`` in the calibration set.

We use a *median* relationship (not OLS on the upper tail), so the
range forecast is robust to fat-tail extreme sessions.

The estimator

    range_proxy = (high - low) of the future horizon
    range_normalised = range_proxy / (σ_h * √h)

We then take the median of range_normalised over the last K horizons.
The forecast is:

    E_range = median(range_normalised) * σ_h * √h

The median-normalised multiplier k̂ is also returned so the calibration
test can compare it to a literature anchor (~2.0-2.5 for daily bars).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RangeForecast:
    expected_range: float
    expected_high: float
    expected_low: float
    range_multiplier_k: float  # k̂ — typical range / (σ_h * √h)
    n_calibration_horizons: int
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "expected_range": self.expected_range,
            "expected_high": self.expected_high,
            "expected_low": self.expected_low,
            "range_multiplier_k": self.range_multiplier_k,
            "n_calibration_horizons": self.n_calibration_horizons,
            "notes": self.notes,
        }


def forecast_range(
    df: pd.DataFrame,
    *,
    horizon_h: int,
    sigma_h1: float,
    calibration_window: int = 720,
) -> RangeForecast:
    """Forecast the future high-low range over ``horizon_h``.

    Parameters
    ----------
    df
        1H OHLCV frame.
    horizon_h
        Forward horizon in hours.
    sigma_h1
        1H-ahead conditional σ (from M5.1) — used to scale the range.
    calibration_window
        Number of most-recent hourly bars to estimate the normalised
        range multiplier k̂.
    """
    if df is None or len(df) < horizon_h + 24:
        return RangeForecast(
            expected_range=float("nan"),
            expected_high=float("nan"),
            expected_low=float("nan"),
            range_multiplier_k=float("nan"),
            n_calibration_horizons=0,
            notes="insufficient_history",
        )
    if not np.isfinite(sigma_h1) or sigma_h1 <= 0:
        return RangeForecast(
            expected_range=float("nan"),
            expected_high=float("nan"),
            expected_low=float("nan"),
            range_multiplier_k=float("nan"),
            n_calibration_horizons=0,
            notes="sigma_unavailable",
        )

    closes = df["close"].astype(float).to_numpy()
    highs = df["high"].astype(float).to_numpy()
    lows = df["low"].astype(float).to_numpy()

    n = len(closes)
    start = max(24, n - calibration_window)
    closes_w = closes[start:]
    highs_w = highs[start:]
    lows_w = lows[start:]

    # Compute realised σ over the calibration window (hourly std of log ret)
    log_ret = np.diff(np.log(closes_w))
    if log_ret.size < 50:
        return RangeForecast(
            expected_range=float("nan"),
            expected_high=float("nan"),
            expected_low=float("nan"),
            range_multiplier_k=float("nan"),
            n_calibration_horizons=0,
            notes="calibration_window_too_short",
        )

    # Rolling σ estimates at horizon_h to normalise the range
    sqrt_h = np.sqrt(float(horizon_h))
    ranges_norm = []
    h2 = max(2, int(horizon_h))  # need >= 2 returns for std(ddof=1)
    # We need both h2+1 consecutive high/low bars for the range.
    # log_ret is the array of len(closes_w) - 1 returns.
    max_j = min(log_ret.size - h2, len(highs_w) - h2 - 1)
    for j in range(0, max(0, max_j)):
        seg = log_ret[j : j + h2]
        if seg.size < 2:
            continue
        local_sigma = float(np.std(seg, ddof=1))
        if local_sigma <= 0 or not np.isfinite(local_sigma):
            continue
        # Range over the corresponding h2+1 price bars
        i_start = j
        i_end = j + h2 + 1
        if i_end > len(highs_w):
            break
        realised_high = float(np.max(highs_w[i_start:i_end]))
        realised_low = float(np.min(lows_w[i_start:i_end]))
        realised_range = realised_high - realised_low
        if realised_range > 0 and closes_w[i_start] > 0 and realised_high > 0:
            log_range = float(np.log(realised_high / realised_low))
            sigma_horizon = local_sigma * sqrt_h
            if sigma_horizon > 0:
                ranges_norm.append(log_range / sigma_horizon)

    if not ranges_norm:
        return RangeForecast(
            expected_range=float("nan"),
            expected_high=float("nan"),
            expected_low=float("nan"),
            range_multiplier_k=float("nan"),
            n_calibration_horizons=0,
            notes="no_realised_ranges",
        )

    k_hat = float(np.median(ranges_norm))
    # Range forecast scaled by the *current* M5.1 conditional σ
    # k_hat is dimensionless in log space; multiply by σ_h * √h.
    log_range = float(k_hat * sigma_h1 * sqrt_h)
    last_close = float(closes[-1])
    # Convert back to price units: half-width = last * (exp(log_range/2) - 1)
    # and full range = 2 * half-width
    half_width_price = last_close * (np.exp(log_range / 2.0) - 1.0)
    expected_range = float(2.0 * half_width_price)
    # Symmetric range around last close as the M0 center — M5 has no
    # direction. The asymmetry from M5.3 widens one side later.
    return RangeForecast(
        expected_range=expected_range,
        expected_high=last_close + half_width_price,
        expected_low=last_close - half_width_price,
        range_multiplier_k=k_hat,
        n_calibration_horizons=len(ranges_norm),
        notes="median_normalised_log_range",
    )


__all__ = ["RangeForecast", "forecast_range"]