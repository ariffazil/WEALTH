"""Shared test fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Make the wave_forge package importable without installing it.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wave_forge.synthetic import HistorySeries  # noqa: E402


def make_synthetic_history(days: int = 730, seed: int = 1337) -> HistorySeries:
    """Build a deterministic GBM-like XAUUSD history with realistic gold characteristics.

    Mirrors ``harness.synthetic_history`` but is local so tests do not
    depend on the calibration harness module being importable.
    """
    rng = np.random.default_rng(seed)
    drift = 0.0003
    vol = 0.011
    level = 2400.0
    rets = rng.normal(drift, vol, size=days)
    close = level * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[close[0]], close[:-1]]) * (1 + rng.normal(0, 0.002, days))
    high = np.maximum(close, open_) * (1 + np.abs(rng.normal(0, 0.003, days)))
    low = np.minimum(close, open_) * (1 - np.abs(rng.normal(0, 0.003, days)))
    volume = rng.integers(10_000, 100_000, size=days)
    idx = pd.date_range(end=pd.Timestamp.now("UTC").normalize(), periods=days, freq="D")
    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )
    return HistorySeries(
        df=df,
        source="SYNTHETIC",
        reason=f"test_synthetic_gbm_d{days}_s{seed}",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def make_sinusoidal_history(
    days: int = 730, seed: int = 1337, freq_days: int = 30, amp: float = 50.0
) -> HistorySeries:
    """History with a *real* embedded cycle — for testing that the
    decomposition can recover genuine structure.

    The series is a level 2400 close + a 30-day sine wave of amplitude
    50 + small Gaussian noise. M4-WAVE should validate at least one
    wavelet/CEEMDAN mode in the band of freq_days.
    """
    rng = np.random.default_rng(seed)
    n = days
    t = np.arange(n, dtype=float)
    close = 2400.0 + amp * np.sin(2.0 * np.pi * t / freq_days) + rng.normal(0, 5.0, n)
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(close, open_) + 1.0
    low = np.minimum(close, open_) - 1.0
    volume = rng.integers(10_000, 100_000, size=n)
    idx = pd.date_range(end=pd.Timestamp.now("UTC").normalize(), periods=n, freq="D")
    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )
    return HistorySeries(
        df=df,
        source="SYNTHETIC",
        reason=f"test_sinusoidal_d{days}_f{freq_days}",
        fetched_at="2026-09-25T00:00:00+00:00",
    )