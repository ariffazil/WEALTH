"""M5 data layer — load XAUUSD 1H history with provenance stamping.

Strategy
========

* Try the wealth_core / engines cascade first (fetch_ohlcv, 1h, 730d).
  In this sandbox it returns the LIVE yfinance PAXG-USD feed; the levels
  are shifted (~$4300 instead of ~$3300) but the *structure* (returns,
  ranges, gaps, semivariance) is real and usable for distribution
  forecasting.
* The cascade label is preserved as-is ("LIVE_fetch_ohlcv_cascade")
  with an additional explicit ``sandbox_price_offset_acknowledged=True``
  flag so downstream readers know.
* If the cascade fails entirely, fall back to the deterministic GBM
  series used by the rest of forecast/*, but only as a last resort.

The :func:`load_xauusd_1h` function returns a :class:`History1H` that
carries a 1H-indexed DataFrame with open/high/low/close/volume and a
provenance tag. NO 4H/24H resampling is performed here — callers can
down-sample on demand with :func:`aggregate_bars`.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional

import numpy as np
import pandas as pd

HistorySource = Literal["LIVE", "SYNTHETIC", "MISSING"]


@dataclass(frozen=True)
class History1H:
    """1H XAUUSD OHLCV with provenance stamped on it.

    Length of :attr:`df` is the number of 1H bars; a 729-day fetch
    returns ~17,500 rows.
    """

    df: pd.DataFrame
    source: HistorySource
    reason: str
    fetched_at: str
    sandbox_price_offset_acknowledged: bool = False

    def __post_init__(self) -> None:
        if self.df is None or len(self.df) == 0:
            raise ValueError("History1H must carry at least one row")
        for col in ("open", "high", "low", "close"):
            if col not in self.df.columns:
                raise ValueError(f"History1H missing column '{col}'")
        if self.source == "LIVE" and self.reason.startswith("synthetic_"):
            raise ValueError("provenance mismatch: LIVE labelled but reason starts with synthetic_")
        if self.source == "SYNTHETIC" and not self.reason.startswith("synthetic_"):
            raise ValueError("provenance mismatch: SYNTHETIC labelled but reason does not start with synthetic_")

    @property
    def close(self) -> pd.Series:
        return self.df["close"].astype(float)

    @property
    def log_return(self) -> pd.Series:
        return np.log(self.close).diff()

    @property
    def is_synthetic(self) -> bool:
        return self.source == "SYNTHETIC"


def _try_live_1h(days: int = 729) -> Optional[pd.DataFrame]:
    """Try the live wealth_core cascade at 1H."""
    try:
        eng_path = "/root/WEALTH/engines/commodity/gold-api"
        wealth_path = "/root/WEALTH"
        for p in (eng_path, wealth_path):
            if p not in sys.path:
                sys.path.insert(0, p)
        from fetch_gold import fetch_ohlcv  # type: ignore

        # yfinance caps 1H lookback at 730d.
        period = f"{min(max(days, 30), 730)}d"
        df = fetch_ohlcv(interval="1h", period=period)
        if df is None or len(df) == 0:
            return None
        if "close" not in df.columns:
            return None
        # Normalise columns
        cols = {c: c.lower() for c in df.columns}
        df = df.rename(columns=cols)
        # Ensure numeric
        for c in ("open", "high", "low", "close"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["close"]).reset_index(drop=False)
        # Stable time column
        if "time" not in df.columns and "Time" in df.columns:
            df = df.rename(columns={"Time": "time"})
        if "time" not in df.columns and "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "time"})
        if "time" not in df.columns and "Date" in df.columns:
            df = df.rename(columns={"Date": "time"})
        if "time" not in df.columns:
            # yfinance sometimes puts the index name as None
            idx_name = df.index.name or "time"
            df = df.rename_axis(idx_name)
            df = df.reset_index()
            if "index" in df.columns:
                df = df.rename(columns={"index": "time"})
            elif idx_name in df.columns:
                df = df.rename(columns={idx_name: "time"})
        if "time" not in df.columns:
            return None
        df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
        df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
        # Make 'time' the index for downstream consumers.
        df = df.set_index("time")
        return df
    except Exception:
        return None


def _synthetic_1h(days: int = 729, seed: int = 1337) -> pd.DataFrame:
    """Build a 1H synthetic GBM series anchored on the calibration harness's
    daily series. Local import keeps this module importable in isolation.
    """
    import importlib

    harness_path = "/root/WEALTH/forecast/calibration"
    if harness_path not in sys.path:
        sys.path.insert(0, harness_path)
    harness = importlib.import_module("harness")

    daily = harness.synthetic_history(days=days, seed=seed)
    # Daily OHLC -> 1H via deterministic walk: 24 hourly steps per day.
    rng = np.random.default_rng(seed)
    rows = []
    for ts, row in daily.iterrows():
        o = float(row["open"])
        h_d = float(row["high"])
        l_d = float(row["low"])
        c = float(row["close"])
        # 23 intraday steps + final close at step 24.
        if o <= 0 or c <= 0:
            continue
        # Per-hour log vol from daily vol (~1.1% daily)
        sigma_h = 0.011 / np.sqrt(24)
        for h in range(24):
            if h == 23:
                p = c
                hp = max(p, h_d)
                lp = min(p, l_d)
            else:
                p = o * np.exp(np.cumsum(rng.normal(0, sigma_h, 1))[-1])
                hp = p * (1 + abs(rng.normal(0, sigma_h / 2)))
                lp = p * (1 - abs(rng.normal(0, sigma_h / 2)))
            rows.append({
                "time": ts + pd.Timedelta(hours=h),
                "open": o if h == 0 else prev,
                "high": hp,
                "low": lp,
                "close": p,
                "volume": float(row.get("volume", 0)) / 24.0,
            })
            prev = p
            o = p
    df = pd.DataFrame(rows).set_index("time").sort_index()
    return df


def load_xauusd_1h(days: int = 729, seed: int = 1337) -> History1H:
    """Return a 1H XAUUSD history with provenance stamped.

    The cascade fetches ``days`` calendar days at 1H resolution. In this
    sandbox the live cascade returns ~17,500 rows spanning ~729 days.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    df = _try_live_1h(days=days)
    if df is not None:
        # The yfinance sandbox feed returns shifted levels (~$4300 vs
        # real-world ~$3300). The structure is real; levels are not.
        # Mark it explicitly so downstream readers don't claim a price.
        return History1H(
            df=df,
            source="LIVE",
            reason="live_fetch_ohlcv_cascade_1h",
            fetched_at=now_iso,
            sandbox_price_offset_acknowledged=True,
        )
    synth = _synthetic_1h(days=days, seed=seed)
    return History1H(
        df=synth,
        source="SYNTHETIC",
        reason=f"synthetic_gbm_1h_d{days}_s{seed}",
        fetched_at=now_iso,
        sandbox_price_offset_acknowledged=False,
    )


def aggregate_bars(history: History1H, hours_per_bar: int) -> History1H:
    """Down-sample 1H bars to N-hour bars. Honest resampling — no level invention.

    The aggregated frame keeps open = first, high = max, low = min,
    close = last, volume = sum. Index becomes the bar start time.
    """
    if hours_per_bar <= 0 or hours_per_bar == 1:
        return history
    df = history.df.copy()
    # Floor timestamps to the bar boundary
    freq = f"{hours_per_bar}h"
    bars = df.resample(freq, label="left", closed="left")
    agg = pd.DataFrame({
        "open": bars["open"].first(),
        "high": bars["high"].max(),
        "low": bars["low"].min(),
        "close": bars["close"].last(),
        "volume": bars["volume"].sum(),
    }).dropna(subset=["close"])
    return History1H(
        df=agg,
        source=history.source,
        reason=f"{history.reason}__agg_{hours_per_bar}h",
        fetched_at=history.fetched_at,
        sandbox_price_offset_acknowledged=history.sandbox_price_offset_acknowledged,
    )


__all__ = [
    "History1H",
    "HistorySource",
    "load_xauusd_1h",
    "aggregate_bars",
]