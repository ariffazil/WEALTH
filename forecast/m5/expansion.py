"""M5.4 — volatility expansion detection.

A simple two-sided CUSUM-style detector on the absolute log-return
stream. We accumulate deviations of |r_t| from a rolling baseline; a
"break" is when the cumulative sum crosses a threshold based on the
recent distribution of |r|.

    s_t = max(0, s_{t-1} + (|r_t| - μ) - slack)
    break if s_t >= h_threshold

The expansion probability is calibrated to the empirical 1-rate of
breaks over the calibration window:

    p_expansion = (n_breaks_last_K + 1) / (K + 2)   # Laplace smoothed

Plus a *raw magnitude* signal: the ratio of the most-recent 6h σ to
the 168h σ. A ratio > 1.5 indicates an obvious expansion regime.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExpansionForecast:
    p_vol_expansion: float  # probability in [0, 1]
    cusum_stat: float
    sigma_ratio_6h_168h: float  # 6h σ / 168h σ
    raw_break_count_168h: int  # count of CUSUM breaks over last 168h
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "p_vol_expansion": self.p_vol_expansion,
            "cusum_stat": self.cusum_stat,
            "sigma_ratio_6h_168h": self.sigma_ratio_6h_168h,
            "raw_break_count_168h": self.raw_break_count_168h,
            "notes": self.notes,
        }


def detect_expansion(
    df: pd.DataFrame,
    *,
    sigma_h1_forecast: float,
    lookback: int = 168,
    slack: float = 0.0,
    h_multiplier: float = 4.0,
) -> ExpansionForecast:
    """Return an expansion probability and a CUSUM statistic.

    Parameters
    ----------
    df
        1H OHLCV frame.
    sigma_h1_forecast
        M5.1 forecast σ (used only for fallback reporting).
    lookback
        Number of hourly bars to inspect for the CUSUM statistic and
        break count.
    slack
        Allowance before accumulation kicks in (multiplier of |r|).
    h_multiplier
        CUSUM threshold as a multiple of the rolling std of |r|.
    """
    if df is None or len(df) < 24:
        return ExpansionForecast(
            p_vol_expansion=float("nan"),
            cusum_stat=float("nan"),
            sigma_ratio_6h_168h=float("nan"),
            raw_break_count_168h=0,
            notes="insufficient_history",
        )
    closes = df["close"].astype(float).to_numpy()
    log_ret = np.diff(np.log(closes))
    if log_ret.size < lookback:
        lookback = log_ret.size
    if lookback < 12:
        return ExpansionForecast(
            p_vol_expansion=float("nan"),
            cusum_stat=float("nan"),
            sigma_ratio_6h_168h=float("nan"),
            raw_break_count_168h=0,
            notes="insufficient_history_for_lookback",
        )

    abs_rets = np.abs(log_ret)
    window = abs_rets[-lookback:]
    mu = float(np.mean(window))
    sd = float(np.std(window, ddof=1))
    if sd <= 0 or not np.isfinite(sd):
        return ExpansionForecast(
            p_vol_expansion=float("nan"),
            cusum_stat=float("nan"),
            sigma_ratio_6h_168h=float("nan"),
            raw_break_count_168h=0,
            notes="zero_volatility_window",
        )

    h_thresh = h_multiplier * sd
    s = 0.0
    breaks = 0
    last_break = -1_000_000
    for idx, ar in enumerate(window):
        z = (ar - mu) - slack
        s = max(0.0, s + z)
        if s >= h_thresh:
            if idx - last_break >= 6:  # cool-down: don't double-count
                breaks += 1
                last_break = idx
            s = 0.0  # reset

    # Sigma ratio 6h / 168h
    if log_ret.size >= 168:
        s_6 = float(np.std(log_ret[-6:], ddof=1)) if 6 > 1 else float("nan")
        s_168 = float(np.std(log_ret[-168:], ddof=1)) if 168 > 1 else float("nan")
        sigma_ratio = s_6 / s_168 if s_168 > 0 else float("nan")
    elif log_ret.size >= 24:
        s_6 = float(np.std(log_ret[-6:], ddof=1))
        s_168 = float(np.std(log_ret[-24:], ddof=1))
        sigma_ratio = s_6 / s_168 if s_168 > 0 else float("nan")
    else:
        sigma_ratio = float("nan")

    # Probability — Laplace-smoothed frequency over last K windows
    K = 24  # number of past K-hour "expansion cycles" to look at
    if log_ret.size >= K:
        # Count expansion cycles over a sliding 6h window over the last K bars
        n_breaks_total = 0
        past_window = abs_rets[-K:]
        past_mu = float(np.mean(past_window))
        past_sd = float(np.std(past_window, ddof=1))
        if past_sd > 0 and np.isfinite(past_sd):
            s_acc = 0.0
            for ar in past_window:
                s_acc = max(0.0, s_acc + (ar - past_mu))
                if s_acc >= h_multiplier * past_sd:
                    n_breaks_total += 1
                    s_acc = 0.0
        p_exp = float((breaks + 1) / (K + 2))
    else:
        p_exp = float((breaks + 1) / (lookback + 2))

    # Bias the probability upward when sigma_ratio > 1.5
    if np.isfinite(sigma_ratio) and sigma_ratio > 1.5:
        # Mild uplift, capped at 0.95
        p_exp = float(min(0.95, p_exp + min(0.3, 0.2 * (sigma_ratio - 1.5))))

    return ExpansionForecast(
        p_vol_expansion=float(np.clip(p_exp, 0.0, 1.0)) if np.isfinite(p_exp) else float("nan"),
        cusum_stat=float(s),
        sigma_ratio_6h_168h=float(sigma_ratio) if np.isfinite(sigma_ratio) else float("nan"),
        raw_break_count_168h=int(breaks),
        notes="cusum_plus_sigma_ratio",
    )


__all__ = ["ExpansionForecast", "detect_expansion"]