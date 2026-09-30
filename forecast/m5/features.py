"""M5.0 feature extraction — pure price-derived inputs.

M5 strictly takes price-derived features; NO wave phase, NO news
sentiment, NO gravity. The inputs are:

    log_return_1h, log_return_24h
    high_low_range_1h (in price units)
    true_range_1h (in price units)
    atr_24h (mean TR over last 24 bars)
    realized_vol_6h, _24h, _72h, _168h (annualized sqrt(252*24) for 1h)
    semivariance_up_24h, semivariance_down_24h
    vol_of_vol_168h
    gap_indicator (overnight abs gap)
    trend_efficiency_24h (net / sum-abs)
    compression_percentile_168h (current TR vs last-168h distribution)
    hour_of_day (0-23)
    distance_from_ema_24h (log distance)

This module never invents a feature. When a feature cannot be computed
(not enough history), it returns NaN and the downstream code is expected
to treat NaN as "feature unavailable".
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureVector:
    """A flat bundle of M5 features at a single origin timestamp.

    All fields are floats (or NaN) unless suffixed with ``_int``.
    """

    # Returns / range
    log_return_1h: float = float("nan")
    log_return_24h: float = float("nan")
    high_low_range_1h: float = float("nan")  # price units
    true_range_1h: float = float("nan")  # price units
    atr_24h: float = float("nan")  # mean TR over 24 bars
    # Realized vol (annualised, sqrt(252*24) for 1H)
    realized_vol_6h: float = float("nan")
    realized_vol_24h: float = float("nan")
    realized_vol_72h: float = float("nan")
    realized_vol_168h: float = float("nan")
    # Semivariance (signed dispersion)
    semivariance_up_24h: float = float("nan")
    semivariance_down_24h: float = float("nan")
    # Vol-of-vol (annualised σ of σ over 168h)
    vol_of_vol_168h: float = float("nan")
    # Gap indicator (overnight abs log gap)
    gap_indicator: float = float("nan")
    # Trend efficiency (net / sum-abs over 24h)
    trend_efficiency_24h: float = float("nan")
    # Compression percentile (current TR vs last 168h distribution)
    compression_percentile_168h: float = float("nan")
    # Hour of day (0..23) at origin
    hour_of_day: int = -1
    # Distance from 24h EMA in log space
    distance_from_ema_24h: float = float("nan")

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _annualise_1h(sigma_h: float) -> float:
    """Annualise an hourly log-return std to annualised vol."""
    if not np.isfinite(sigma_h):
        return float("nan")
    # 1 year ~ 252 trading days * 24 hourly bars
    return float(sigma_h * np.sqrt(252 * 24))


def _true_range(prev_close: float, high: float, low: float) -> float:
    if not (np.isfinite(prev_close) and np.isfinite(high) and np.isfinite(low)):
        return float("nan")
    return max(
        abs(high - low),
        abs(high - prev_close),
        abs(low - prev_close),
    )


def compute_features(df: pd.DataFrame, *, origin_idx: Optional[int] = None) -> FeatureVector:
    """Compute the M5 feature vector at ``origin_idx``.

    Parameters
    ----------
    df
        1H OHLCV frame indexed by time. Must have columns
        ``open``, ``high``, ``low``, ``close``.
    origin_idx
        Integer positional index into ``df``. If None, uses the last
        row (default = forecast from the latest bar).

    Returns
    -------
    FeatureVector
        NaN-filled where data is insufficient.
    """
    if df is None or len(df) == 0:
        return FeatureVector()

    if origin_idx is None:
        origin_idx = len(df) - 1
    origin_idx = max(0, min(origin_idx, len(df) - 1))

    closes = df["close"].astype(float).to_numpy()
    highs = df["high"].astype(float).to_numpy()
    lows = df["low"].astype(float).to_numpy()
    opens = df["open"].astype(float).to_numpy()

    out = FeatureVector()

    # log returns
    if origin_idx >= 1:
        cur = float(np.log(closes[origin_idx] / closes[origin_idx - 1])) if closes[origin_idx - 1] > 0 else float("nan")
        out = FeatureVector(**{**out.to_dict(), "log_return_1h": cur})
    if origin_idx >= 24:
        cur = float(np.log(closes[origin_idx] / closes[origin_idx - 24])) if closes[origin_idx - 24] > 0 else float("nan")
        out = FeatureVector(**{**out.to_dict(), "log_return_24h": cur})

    # Hour of day from the index
    try:
        out = FeatureVector(**{**out.to_dict(), "hour_of_day": int(pd.Timestamp(df.index[origin_idx]).hour)})
    except Exception:
        pass

    # Range and TR at origin
    if origin_idx >= 0:
        h = float(highs[origin_idx])
        l = float(lows[origin_idx])
        if np.isfinite(h) and np.isfinite(l):
            out = FeatureVector(**{**out.to_dict(), "high_low_range_1h": h - l})
        if origin_idx >= 1 and np.isfinite(closes[origin_idx - 1]):
            out = FeatureVector(**{**out.to_dict(), "true_range_1h": _true_range(closes[origin_idx - 1], h, l)})

    # ATR-24 = mean TR over last 24 bars (excluding current)
    if origin_idx >= 24:
        trs = []
        for j in range(origin_idx - 23, origin_idx + 1):
            if j <= 0:
                continue
            tr = _true_range(closes[j - 1], highs[j], lows[j])
            if np.isfinite(tr):
                trs.append(tr)
        if trs:
            out = FeatureVector(**{**out.to_dict(), "atr_24h": float(np.mean(trs))})

    # Realized vols (annualised)
    def _realised(window: int) -> float:
        if origin_idx < window:
            return float("nan")
        seg = closes[origin_idx - window + 1 : origin_idx + 1]
        if seg.size < 2:
            return float("nan")
        rets = np.diff(np.log(seg))
        if rets.size < 2:
            return float("nan")
        sigma_h = float(np.std(rets, ddof=1))
        return _annualise_1h(sigma_h)

    out = FeatureVector(**{
        **out.to_dict(),
        "realized_vol_6h": _realised(6),
        "realized_vol_24h": _realised(24),
        "realized_vol_72h": _realised(72),
        "realized_vol_168h": _realised(168),
    })

    # Semivariance (24h)
    if origin_idx >= 24:
        seg = closes[origin_idx - 23 : origin_idx + 1]
        rets = np.diff(np.log(seg))
        if rets.size > 0:
            up = rets[rets > 0]
            dn = rets[rets < 0]
            sv_up = float(np.mean(up ** 2)) if up.size > 0 else 0.0
            sv_dn = float(np.mean(dn ** 2)) if dn.size > 0 else 0.0
            out = FeatureVector(**{
                **out.to_dict(),
                "semivariance_up_24h": float(np.sqrt(sv_up) * np.sqrt(252 * 24)),
                "semivariance_down_24h": float(np.sqrt(sv_dn) * np.sqrt(252 * 24)),
            })

    # Vol-of-vol over 168h rolling daily σ (24 bar sigma)
    if origin_idx >= 24 * 8:
        sigmas = []
        for j in range(origin_idx - 24 * 7, origin_idx - 24, 24):
            if j < 24:
                continue
            seg = closes[j - 24 : j + 1]
            rets = np.diff(np.log(seg))
            if rets.size > 1:
                sigmas.append(float(np.std(rets, ddof=1)))
        if len(sigmas) >= 3:
            out = FeatureVector(**{
                **out.to_dict(),
                "vol_of_vol_168h": _annualise_1h(float(np.std(sigmas, ddof=1))),
            })

    # Gap indicator: |log(open / prev close)|
    if origin_idx >= 1 and closes[origin_idx - 1] > 0 and opens[origin_idx] > 0:
        out = FeatureVector(**{
            **out.to_dict(),
            "gap_indicator": float(abs(np.log(opens[origin_idx] / closes[origin_idx - 1]))),
        })

    # Trend efficiency 24h: net / sum-abs
    if origin_idx >= 24:
        seg = closes[origin_idx - 23 : origin_idx + 1]
        rets = np.diff(np.log(seg))
        net = float(np.sum(rets))
        sabs = float(np.sum(np.abs(rets)))
        if sabs > 0:
            out = FeatureVector(**{**out.to_dict(), "trend_efficiency_24h": net / sabs})

    # Compression percentile 168h
    if origin_idx >= 168:
        tr_window = []
        for j in range(origin_idx - 167, origin_idx + 1):
            if j <= 0:
                continue
            tr = _true_range(closes[j - 1], highs[j], lows[j])
            if np.isfinite(tr):
                tr_window.append(tr)
        if len(tr_window) >= 50:
            cur_tr = tr_window[-1]
            below = sum(1 for x in tr_window if x <= cur_tr)
            out = FeatureVector(**{
                **out.to_dict(),
                "compression_percentile_168h": float(below / len(tr_window)),
            })

    # Distance from EMA-24 in log space
    if origin_idx >= 24:
        seg = closes[origin_idx - 23 : origin_idx + 1]
        # Standard EMA with α = 2/(N+1) = 2/25
        alpha = 2.0 / 25.0
        ema = float(seg[0])
        for v in seg[1:]:
            ema = alpha * v + (1.0 - alpha) * ema
        if ema > 0 and closes[origin_idx] > 0:
            out = FeatureVector(**{
                **out.to_dict(),
                "distance_from_ema_24h": float(np.log(closes[origin_idx] / ema)),
            })

    return out


def feature_array(df: pd.DataFrame) -> pd.DataFrame:
    """Compute features for every row in ``df``.

    Returns a DataFrame indexed by ``df.index`` with one column per
    :class:`FeatureVector` field.
    """
    rows = []
    index = []
    for i in range(len(df)):
        rows.append(compute_features(df, origin_idx=i))
        index.append(df.index[i])
    df_out = pd.DataFrame([r.to_dict() for r in rows], index=pd.Index(index, name=df.index.name))
    return df_out


__all__ = [
    "FeatureVector",
    "compute_features",
    "feature_array",
]