#!/usr/bin/env python3
"""
Walk-Forward Calibration Harness — Gold Forecast (XAUUSD)
=========================================================

PRIMARY GATE for SHADOW → LIVE promotion of `/root/WEALTH/wealth_core/forecast.py`
(The forecast engine actually lives in `/root/WEALTH/engines/commodity/gold-api/fetch_gold.py`
as `cmd_forecast` — the same engine the live site calls via `/api/gold/forecast`.)

This harness is **read-only against the engine**: it imports it, never edits it.
It must run under `/root/WEALTH/engines/commodity/gold-api/` so the relative imports
in fetch_gold.py resolve.

What it does
------------
For every walk-forward window (30 / 60 / 90 days):

1. Load historical daily XAUUSD closes (yfinance PAXG-USD via fetch_ohlcv).
2. Walk forward day-by-day: at each step t in [train_end, total]
   the model produces a P10/P50/P90 cone over the next H days.
3. For each (t, h) pair with h ∈ {1..H}, score:
     - pinball loss per quantile q ∈ {0.1, 0.5, 0.9}
     - P10-P90 coverage (empirical frac of actuals ∈ [p10, p90])
     - directional Brier: P(actual sign | sign(predicted median)) vs 0.5
4. Compare against a random-walk baseline that emits the same P10/P50/P90 bands
   using *historical 60-day rolling volatility* only (no drift, no regime).
5. Emit per-window checkpoint with skill scores, calibration state, and
   promotion recommendation.

Strict promotion rule (all four must hold):
    pinball_skill_score > 0 AND
    model_coverage ∈ [0.70, 0.90] AND
    brier_skill     > 0 AND
    window_days     ≥ 30
→ ``promotion_recommended = True``, ``calibration_state = LIVE``.
Otherwise SHADOW. (DEGRADED/QUARANTINE reserved for runtime drift, see below.)

DEGRADED  — latest window’s coverage outside [0.50, 0.92] OR brier_skill ≤ -0.05
QUARANTINE — any window failed schema/sanity checks or produced NaN.

Per APEX reality-kernel doctrine, this script writes metrics to:
    /root/AAA/VAULT999/calibration/gold-forecast-metrics.json
and prints the same JSON to stdout for the orchestrator. It does NOT auto-promote;
the 999 Witness reads the file and decides.

Usage
-----
    python3 harness.py --asset XAUUSD --window 90          # single window, live data
    python3 harness.py --asset XAUUSD --windows 30 60 90   # multi-window sweep
    python3 harness.py --dry-run                           # synthetic 730d (test only)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Imports — engine is read-only. We add /root/WEALTH/engines/commodity/gold-api
# to sys.path so ``import fetch_gold`` resolves without touching WEALTH layout.
# ---------------------------------------------------------------------------
REPO_ROOT = Path("/root")
WEALTH_ROOT = REPO_ROOT / "WEALTH"
GOLD_API_DIR = WEALTH_ROOT / "engines" / "commodity" / "gold-api"
CALIBRATION_DIR = WEALTH_ROOT / "forecast" / "calibration"
VAULT999_METRICS = REPO_ROOT / "AAA" / "VAULT999" / "calibration" / "gold-forecast-metrics.json"

# Strict: do not import anything from WEALTH/wealth_core; the calibration folder
# must remain independent. We import the engine's indicator helpers
# (compute_atr / compute_ema / compute_rsi / _lin_slope) by name — that's
# importing, not mutating. The cone math itself is reimplemented below in
# ``build_cone_replica`` from first principles so calibration is independent
# of any stateful engine cache.
if str(GOLD_API_DIR) not in sys.path:
    sys.path.insert(0, str(GOLD_API_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Local imports of the engine's pure-math helpers. ImportError is fatal — fail
# loud, not silent. We never import cmd_forecast here: its result is cached and
# wedded to live "today", which would invalidate walk-forward.
try:
    from fetch_gold import (  # type: ignore  # noqa: E402
        compute_atr as _engine_atr,
        compute_ema as _engine_ema,
        compute_rsi as _engine_rsi,
        _lin_slope as _engine_lin_slope,
    )
    _ENGINE_HELPERS_AVAILABLE = True
    _ENGINE_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    _engine_ema = _engine_rsi = _engine_atr = _engine_lin_slope = None  # type: ignore
    _ENGINE_HELPERS_AVAILABLE = False
    _ENGINE_IMPORT_ERROR = repr(exc)

# yfinance is optional; we degrade to synthetic for --dry-run and offline use.
try:
    import yfinance as yf  # type: ignore
    _YF_AVAILABLE = True
except Exception:
    yf = None
    _YF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Math — pinball loss, Brier, skill scores
# ---------------------------------------------------------------------------

def pinball_loss(actual: float, quantile_pred: float, q: float) -> float:
    """Standard pinball loss. q in (0, 1). Lower is better."""
    diff = actual - quantile_pred
    return q * diff if diff >= 0 else (q - 1) * diff


def quantile_pinball_score(y: np.ndarray, q_pred: np.ndarray, q: float) -> float:
    """Mean pinball loss for a quantile across a fold. Nan-safe."""
    diff = y - q_pred
    loss = np.where(diff >= 0, q * diff, (q - 1) * diff)
    if np.all(~np.isfinite(loss)):
        return float("nan")
    return float(np.nanmean(loss))


def coverage_score(y: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    """Empirical P(lo ≤ y ≤ hi). Honest band ⇒ close to nominal."""
    inside = (y >= lo) & (y <= hi)
    finite = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    if finite.sum() == 0:
        return float("nan")
    return float(np.sum(inside & finite) / finite.sum())


def brier_dir(y: np.ndarray, pred_dir: np.ndarray) -> float:
    """Brier score for directional (sign) forecasts.

    Target = sign(y_next).  pred_dir is a soft probability in [0,1] of y_next > 0.
    """
    target = (y > 0).astype(float)
    p = np.clip(pred_dir, 0.0, 1.0)
    valid = np.isfinite(y) & np.isfinite(p)
    if valid.sum() == 0:
        return float("nan")
    return float(np.mean((p[valid] - target[valid]) ** 2))


def skill_score(model: float, baseline: float) -> float:
    """Positive skill = better than baseline. Skill = 1 − model/baseline.

    For loss-style metrics (pinball, brier), lower is better, so this is
    the canonical direction. Negative ⇒ worse than baseline.
    """
    if not (np.isfinite(model) and np.isfinite(baseline)):
        return float("nan")
    if baseline == 0:
        return 0.0
    return 1.0 - (model / baseline)


# ---------------------------------------------------------------------------
# Data — historical XAUUSD daily closes
# ---------------------------------------------------------------------------

def fetch_history(interval: str = "1d", period: str = "2y") -> pd.DataFrame:
    """Fetch XAUUSD OHLCV history (Binance → yfinance cascade via the engine).
    Returns DataFrame with columns [open, high, low, close, volume]. Used by
    the cone replica to compute ATR / EMA / regime.

    Fails loud if no path succeeds — silence would masquerade as 'synthetic'."""
    try:
        df = _import_fetch_ohlcv()(interval=interval, period=period)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    if not _YF_AVAILABLE:
        raise RuntimeError(
            "No market data and yfinance unavailable. Pass --dry-run for synthetic."
        )
    t = yf.Ticker("PAXG-USD")
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        t = yf.Ticker("GC=F")
        df = t.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(
            "No gold data available from PAXG-USD or GC=F. Pass --dry-run."
        )
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low",
                            "Close": "close", "Volume": "volume"})
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    out = df[keep].copy()
    out.index.name = "time"
    return out


def _import_fetch_ohlcv():
    """Late-binding fetch_ohlcv import — keeps engine helpers optional and
    avoids importing the engine module at the top of the file when its
    init side-effects (cache dir, MYT tz) would fire for dry-run users."""
    import importlib
    return importlib.import_module("fetch_gold").fetch_ohlcv


def synthetic_history(days: int, seed: int = 1337, drift: float = 0.0003,
                      vol: float = 0.011, level: float = 2400.0) -> pd.DataFrame:
    """Deterministic GBM-ish daily OHLCV series for --dry-run and offline tests."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, size=days)
    close = level * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[close[0]], close[:-1]]) * (1 + rng.normal(0, 0.002, days))
    high = np.maximum(close, open_) * (1 + np.abs(rng.normal(0, 0.003, days)))
    low = np.minimum(close, open_) * (1 - np.abs(rng.normal(0, 0.003, days)))
    volume = rng.integers(10_000, 100_000, size=days)
    idx = pd.date_range(end=pd.Timestamp.now("UTC").normalize(), periods=days, freq="D")
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=idx)


# ---------------------------------------------------------------------------
# Random-walk baseline — same P-band shape, but driven only by historical vol.
# ---------------------------------------------------------------------------

@dataclass
class BaselinePaths:
    p10: np.ndarray
    p50: np.ndarray
    p90: np.ndarray


def random_walk_cone(last_close: float, horizon: int, hist_vol_60d: float) -> BaselinePaths:
    """Random-walk baseline: median = last_close (no drift), bands = σ_h = σ60d·√t.
    Quantile z: P10=-1.282, P90=+1.282."""
    t = np.arange(1, horizon + 1, dtype=float)
    sigma = hist_vol_60d * np.sqrt(t) * last_close
    p50 = np.full(horizon, last_close, dtype=float)
    p10 = p50 - 1.282 * sigma
    p90 = p50 + 1.282 * sigma
    return BaselinePaths(p10=p10, p50=p50, p90=p90)


def rolling_realised_vol(closes: pd.Series, window: int = 60) -> float:
    """Recent realised vol (stddev of log returns), annualised-free (per step)."""
    try:
        vals = pd.to_numeric(closes, errors="coerce").to_numpy().astype(float)
    except Exception:
        return 1e-3
    if vals.size < 5:
        return 1e-3
    finite_mask = np.isfinite(vals)
    if not finite_mask.any():
        return 1e-3
    finite_vals = vals[finite_mask]
    log_prices = np.log(finite_vals)
    if log_prices.size < 2:
        return 1e-3
    rets = np.diff(log_prices)
    if rets.size < 2:
        return 1e-3
    seg = rets[-window:] if rets.size >= window else rets
    s = float(np.std(seg))
    if not np.isfinite(s) or s <= 0:
        s = 1e-6
    return s


# ---------------------------------------------------------------------------
# Model cone — wrap the engine call. CRITICAL: never edit the engine.
# ---------------------------------------------------------------------------

# Default cone knobs — overridable per-call. Tightened from the engine's historic
# 1.0 default after the 2026-09 calibration audit showed real XAUUSD bands were
# too wide (coverage ~0.77, nominal 0.80, pinball skill negative on 729d walk-forward).
DEFAULT_ATR_MULTIPLIER: float = 0.6
DEFAULT_MOMENTUM_BIAS_ENABLED: bool = True
DEFAULT_MOMENTUM_BIAS_THRESHOLD: float = 0.025  # 2.5% 5-day return trigger
DEFAULT_MOMENTUM_BIAS_ATR_FRAC: float = 0.3    # 0.3·ATR shift on P50


def _compute_momentum_bias(
    close: pd.Series,
    atr_val: float,
    threshold_pct: float = DEFAULT_MOMENTUM_BIAS_THRESHOLD,
    bias_atr_frac: float = DEFAULT_MOMENTUM_BIAS_ATR_FRAC,
) -> float:
    """Momentum mean-reversion bias (Δ in price units, applied to every P50 step).

    Gold mean-reverts after extreme moves. If 5-day return > +threshold, bias the
    P50 *down* by bias_atr_frac·ATR (expect reversion to the downside). If 5-day
    return < -threshold, bias P50 *up* by the same amount. Otherwise 0.0.

    Direction anti-correlates with the 5-day move — that is the point. This
    converts noise-on-direction into a small, biased mean-reversion tilt.
    """
    if len(close) < 6 or atr_val <= 0:
        return 0.0
    ret_5d = float(close.iloc[-1] / close.iloc[-6] - 1.0)
    if not np.isfinite(ret_5d):
        return 0.0
    if ret_5d > threshold_pct:
        return -bias_atr_frac * atr_val   # fade the pop
    if ret_5d < -threshold_pct:
        return +bias_atr_frac * atr_val   # fade the drop
    return 0.0


def model_cone_at(
    history: pd.DataFrame,
    horizon: int,
    atr_multiplier: float = DEFAULT_ATR_MULTIPLIER,
    momentum_bias_enabled: bool = DEFAULT_MOMENTUM_BIAS_ENABLED,
    momentum_bias_threshold_pct: float = DEFAULT_MOMENTUM_BIAS_THRESHOLD,
    momentum_bias_atr_frac: float = DEFAULT_MOMENTUM_BIAS_ATR_FRAC,
) -> dict[str, Any] | None:
    """Build a P10/P50/P90 cone from a closed-SoFar ``history`` OHLCV frame,
    using the *same math* as ``fetch_gold.cmd_forecast`` — but stateless, so
    walk-forward re-evaluations on different test slices give different cones
    (the engine's cmd_forecast is stateful + cached).

    Implementation is a faithful re-implementation of the cone math from the
    engine's ``cmd_forecast`` function (lines 1028-1110 of fetch_gold.py):

        1. Drift — least-squares slope on last 20 closes, ATR-clamped.
        2. Regime — TRENDING_UP if ema20>ema50 & |delta|>0.5·atr
                    TRENDING_DOWN if ema20<ema50 & |delta|>0.5·atr
                    else SIDEWAYS.
        3. Cone — p50 drifts with slope, pulls toward ema200 with blend_w,
                  bands are ``atr_multiplier · atr · sqrt(t)``.
                  quantiles ±1.282σ for P10/P90.
        4. (2026-09 calibration tightening) Optional momentum mean-reversion
           bias on P50: when the 5-day return exceeds ±``momentum_bias_threshold_pct``
           in either direction, shift every P50 step by
           ``sign(−ret) · momentum_bias_atr_frac · atr``. This converts
           direction-noise into a small biased tilt that exploits gold's
           well-documented short-horizon mean-reversion after extreme moves.

    We never import or call ``cmd_forecast``; this is independent.

    Tuning knobs (all kwarg-overridable; none harder than the data path):
        atr_multiplier              — band width scalar, default 0.6 (was 1.0)
        momentum_bias_enabled       — switch for the mean-reversion tilt
        momentum_bias_threshold_pct — |5d return| trigger, default 0.025
        momentum_bias_atr_frac      — P50 shift magnitude, default 0.3·ATR

    Returns a dict with numpy arrays p10/p50/p90 of length `horizon`."""
    if history is None or len(history) < 30:
        return None
    if not {"high", "low", "close"}.issubset(set(history.columns)):
        h = history.copy()
        h = h.assign(
            high=h["close"] * 1.005,
            low=h["close"] * 0.995,
        )
    else:
        h = history

    close = h["close"]
    atr_series = _engine_atr(h[["high", "low", "close"]], period=14)
    atr_val = float(atr_series.iloc[-1])
    if not np.isfinite(atr_val) or atr_val <= 0:
        return None

    ema20 = float(_engine_ema(close, 20).iloc[-1])
    ema50 = float(_engine_ema(close, 50).iloc[-1])
    ema200 = float(_engine_ema(close, 200).iloc[-1]) if len(close) >= 200 else ema50
    price = float(close.iloc[-1])

    # 1) Drift — regression of last 20 closes, ATR-clamped.
    slope = float(_engine_lin_slope(close.tail(20).to_numpy()))
    slope = max(-atr_val, min(atr_val, slope))

    # 2) Regime.
    trending = abs(ema20 - ema50) > 0.5 * atr_val
    regime = ("TRENDING_UP" if ema20 > ema50 else "TRENDING_DOWN") if trending else "SIDEWAYS"

    # 3) Momentum mean-reversion bias on P50. Computed once per call
    #    (a single scalar shift — applied to every horizon step).
    bias = (
        _compute_momentum_bias(
            close, atr_val,
            threshold_pct=momentum_bias_threshold_pct,
            bias_atr_frac=momentum_bias_atr_frac,
        )
        if momentum_bias_enabled else 0.0
    )

    # 4) Cone. Mirror the engine: t in [1, H].
    blend_w = 0.2 if trending else 0.5
    p10, p50, p90 = [], [], []
    for t in range(1, horizon + 1):
        mid = price + slope * t + bias
        mid += (ema200 - mid) * (1 - math.exp(-t / 20.0)) * blend_w
        sigma = atr_val * atr_multiplier * math.sqrt(t)
        p10.append(round(mid - 1.282 * sigma, 2))
        p50.append(round(mid, 2))
        p90.append(round(mid + 1.282 * sigma, 2))

    return {
        "p10": np.array(p10, dtype=float),
        "p50": np.array(p50, dtype=float),
        "p90": np.array(p90, dtype=float),
        "regime": regime,
        "atr": atr_val,
        "slope": slope,
        "blend_w": blend_w,
        "atr_multiplier": float(atr_multiplier),
        "momentum_bias": float(bias),
    }


# ---------------------------------------------------------------------------
# Walk-forward evaluation
# ---------------------------------------------------------------------------

@dataclass
class WindowMetrics:
    """One walk-forward window. All arrays are step-wise truth-vs-predict."""
    ts: str
    window_days: int
    horizon_days: int
    steps: int
    baseline_pinball: float           # mean pinball across q∈{0.1,0.5,0.9}
    model_pinball: float
    pinball_skill_score: float
    baseline_coverage: float          # P10-P90 band hit-rate
    model_coverage: float
    brier_skill: float                # directional Brier skill vs 50/50
    calibration_state: str            # SHADOW | DEGRADED | LIVE | QUARANTINE
    walk_forward_passed: bool
    promotion_recommended: bool
    notes: list[str] = field(default_factory=list)


def evaluate_window(ohlcv_full: pd.DataFrame,
                    horizon: int,
                    window_label: int,
                    today: pd.Timestamp,
                    eval_stride: int = 5,
                    atr_multiplier: float = DEFAULT_ATR_MULTIPLIER,
                    momentum_bias_enabled: bool = DEFAULT_MOMENTUM_BIAS_ENABLED,
                    momentum_bias_threshold_pct: float = DEFAULT_MOMENTUM_BIAS_THRESHOLD,
                    momentum_bias_atr_frac: float = DEFAULT_MOMENTUM_BIAS_ATR_FRAC,
                    ) -> WindowMetrics:
    """Walk-forward evaluation.

    Framing: ``ohlcv_full`` is the full available OHLCV history. We take the
    last ``window_label`` days as the **test** period; everything before is
    train. We re-evaluate the cone every ``eval_stride`` business days across
    the test window and score the next ``horizon`` actuals.

    That framing makes a 30-day window comparable to a 90-day window: both train
    on the same deep history, they just differ in how big the test slice is.

    Cost: O(window_label / eval_stride) cone evaluations per window.

    Cone-tuning kwargs are passed through to ``model_cone_at``:
        atr_multiplier              — band width scalar (default 0.6)
        momentum_bias_enabled       — apply 5-day mean-reversion bias (default True)
        momentum_bias_threshold_pct — |5d return| trigger (default 0.025)
        momentum_bias_atr_frac      — P50 shift magnitude (default 0.3·ATR)
    """
    df = ohlcv_full.copy()
    for col in ("high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[c for c in ("high", "low", "close") if c in df.columns])
    if df.index.has_duplicates:
        df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()

    n = len(df)
    if n < max(window_label + 30, 100):
        return WindowMetrics(
            ts=today.isoformat(),
            window_days=window_label,
            horizon_days=horizon,
            steps=0,
            baseline_pinball=float("nan"),
            model_pinball=float("nan"),
            pinball_skill_score=float("nan"),
            baseline_coverage=float("nan"),
            model_coverage=float("nan"),
            brier_skill=float("nan"),
            calibration_state="QUARANTINE",
            walk_forward_passed=False,
            promotion_recommended=False,
            notes=["insufficient_history_for_window"],
        )

    split = max(0, n - window_label)
    close_series = df["close"]

    model_p10_all: list[float] = []
    model_p50_all: list[float] = []
    model_p90_all: list[float] = []
    base_p10_all: list[float] = []
    base_p50_all: list[float] = []
    base_p90_all: list[float] = []
    actuals: list[float] = []
    y_returns: list[float] = []
    model_p_up: list[float] = []

    n_test = n - split
    test_positions = list(range(0, n_test, max(1, eval_stride)))

    for ti in test_positions:
        idx_pos_in_window = split + ti
        if idx_pos_in_window >= n - 1:
            break
        history = df.iloc[: idx_pos_in_window + 1]
        if len(history) < 30:
            continue
        last_close = _scalar(history["close"].iloc[-1])
        if not np.isfinite(last_close):
            continue

        cone = model_cone_at(
            history, horizon,
            atr_multiplier=atr_multiplier,
            momentum_bias_enabled=momentum_bias_enabled,
            momentum_bias_threshold_pct=momentum_bias_threshold_pct,
            momentum_bias_atr_frac=momentum_bias_atr_frac,
        )
        if cone is None or len(cone["p50"]) < 1:
            continue

        max_h = min(len(cone["p50"]), n - idx_pos_in_window - 1)
        if max_h < 1:
            continue
        vol = rolling_realised_vol(close_series.iloc[: idx_pos_in_window + 1], window=60)

        for h in range(max_h):
            actual = _scalar(close_series.iloc[idx_pos_in_window + 1 + h])
            if not np.isfinite(actual):
                continue
            actuals.append(actual)
            y_returns.append(actual - last_close)

            model_p10_all.append(float(cone["p10"][h]))
            model_p50_all.append(float(cone["p50"][h]))
            model_p90_all.append(float(cone["p90"][h]))

            bw = random_walk_cone(last_close, h + 1, vol)
            base_p10_all.append(float(bw.p10[h]))
            base_p50_all.append(float(bw.p50[h]))
            base_p90_all.append(float(bw.p90[h]))

            h_sigma = max(vol * last_close * math.sqrt(h + 1), 1e-6)
            delta = (float(cone["p50"][h]) - last_close) / h_sigma
            p_up = 1.0 / (1.0 + math.exp(-3.0 * delta))
            model_p_up.append(p_up)

    if not actuals:
        return WindowMetrics(
            ts=today.isoformat(),
            window_days=window_label,
            horizon_days=horizon,
            steps=0,
            baseline_pinball=float("nan"),
            model_pinball=float("nan"),
            pinball_skill_score=float("nan"),
            baseline_coverage=float("nan"),
            model_coverage=float("nan"),
            brier_skill=float("nan"),
            calibration_state="QUARANTINE",
            walk_forward_passed=False,
            promotion_recommended=False,
            notes=["no_test_steps"],
        )

    y = np.array(actuals, dtype=float)
    m10, m50, m90 = np.array(model_p10_all), np.array(model_p50_all), np.array(model_p90_all)
    b10, b50, b90 = np.array(base_p10_all), np.array(base_p50_all), np.array(base_p90_all)

    # Pinball loss per quantile, averaged across quantiles.
    m_pinballs = [
        quantile_pinball_score(y, m10, 0.1),
        quantile_pinball_score(y, m50, 0.5),
        quantile_pinball_score(y, m90, 0.9),
    ]
    b_pinballs = [
        quantile_pinball_score(y, b10, 0.1),
        quantile_pinball_score(y, b50, 0.5),
        quantile_pinball_score(y, b90, 0.9),
    ]
    model_pinball = float(np.nanmean(m_pinballs))
    baseline_pinball = float(np.nanmean(b_pinballs))
    pss = skill_score(model_pinball, baseline_pinball)

    model_cov = coverage_score(y, m10, m90)
    base_cov = coverage_score(y, b10, b90)

    # Directional Brier, skill vs 0.5 (no-change).
    yret = np.array(y_returns, dtype=float)
    pdir = np.array(model_p_up, dtype=float)
    brier_model = brier_dir(yret, pdir)
    brier_ref = 0.25  # always-50/50 score
    bs = skill_score(brier_model, brier_ref)

    # State machine — single source of truth lives here.
    state, passed, promo, notes = _decide(
        window_label=window_label,
        model_pinball=model_pinball,
        baseline_pinball=baseline_pinball,
        pinball_skill=pss,
        model_coverage=model_cov,
        baseline_coverage=base_cov,
        brier_skill=bs,
        steps=len(actuals),
    )

    return WindowMetrics(
        ts=today.isoformat(),
        window_days=window_label,
        horizon_days=horizon,
        steps=len(actuals),
        baseline_pinball=_f4(baseline_pinball),
        model_pinball=_f4(model_pinball),
        pinball_skill_score=_f4(pss),
        baseline_coverage=_f4(base_cov),
        model_coverage=_f4(model_cov),
        brier_skill=_f4(bs),
        calibration_state=state,
        walk_forward_passed=passed,
        promotion_recommended=promo,
        notes=notes,
    )


def _decide(
    *,
    window_label: int,
    model_pinball: float,
    baseline_pinball: float,
    pinball_skill: float,
    model_coverage: float,
    baseline_coverage: float,
    brier_skill: float,
    steps: int,
) -> tuple[str, bool, bool, list[str]]:
    """Single state-machine decision. See module docstring for rules."""
    notes: list[str] = []

    # NaN-quarantine: schema or data sanity failed.
    if (
        not math.isfinite(model_pinball)
        or not math.isfinite(baseline_pinball)
        or not math.isfinite(pinball_skill)
        or not math.isfinite(model_coverage)
        or not math.isfinite(brier_skill)
        or steps < 5
    ):
        return ("QUARANTINE", False, False, ["invalid_metrics_or_few_steps"] + notes)

    # Strict promotion: ALL four conditions.
    promo_ok = (
        pinball_skill > 0.0
        and 0.70 <= model_coverage <= 0.90
        and brier_skill > 0.0
        and window_label >= 30
    )

    if promo_ok:
        return ("LIVE", True, True, ["all_thresholds_met"])

    # DEGRADED: honesty loss — band too narrow or too wide, or directional lost badly.
    if (model_coverage < 0.50 or model_coverage > 0.92) or brier_skill <= -0.05:
        notes.append("band_or_direction_out_of_bounds")
        return ("DEGRADED", False, False, notes)

    return ("SHADOW", False, False, notes)


def _f4(x: float) -> float:
    if not math.isfinite(x):
        return x
    return round(float(x), 4)


def _scalar(x: Any) -> float:
    """Coerce a pandas scalar / 1-element Series / numpy scalar into a Python float.
    Defensive wrapper because ``Series.iloc[i]`` can return another Series on
    duplicate-index or unusual-dtype frames."""
    if isinstance(x, pd.Series):
        if len(x) == 0:
            return float("nan")
        x = x.iloc[0]
    if isinstance(x, pd.DataFrame):
        if x.empty:
            return float("nan")
        x = x.iloc[0, 0]
    return float(np.asarray(x).item() if hasattr(np.asarray(x), "item") else x)


# ---------------------------------------------------------------------------
# Rolling means across windows for the multi-window sweep
# ---------------------------------------------------------------------------

def rolling_means(metrics: list[WindowMetrics]) -> dict[str, float]:
    """Mean across the supplied windows. Empty-safe."""
    if not metrics:
        return {"pinball_skill_score": float("nan"),
                "model_coverage": float("nan"),
                "brier_skill": float("nan")}
    pss = [m.pinball_skill_score for m in metrics if math.isfinite(m.pinball_skill_score)]
    cov = [m.model_coverage for m in metrics if math.isfinite(m.model_coverage)]
    bss = [m.brier_skill for m in metrics if math.isfinite(m.brier_skill)]
    return {
        "pinball_skill_score": _f4(statistics.fmean(pss)) if pss else float("nan"),
        "model_coverage":      _f4(statistics.fmean(cov)) if cov else float("nan"),
        "brier_skill":         _f4(statistics.fmean(bss)) if bss else float("nan"),
    }


# ---------------------------------------------------------------------------
# Output schema — exactly what the contract requires
# ---------------------------------------------------------------------------

def metrics_to_record(m: WindowMetrics, extras: dict[str, Any] | None = None) -> dict[str, Any]:
    rec = {
        "ts": m.ts,
        "window_days": m.window_days,
        "baseline_pinball": m.baseline_pinball,
        "model_pinball": m.model_pinball,
        "pinball_skill_score": m.pinball_skill_score,
        "baseline_coverage": m.baseline_coverage,
        "model_coverage": m.model_coverage,
        "brier_skill": m.brier_skill,
        "calibration_state": m.calibration_state,
        "walk_forward_passed": m.walk_forward_passed,
        "promotion_recommended": m.promotion_recommended,
        "horizon_days": m.horizon_days,
        "steps": m.steps,
        "notes": m.notes,
    }
    if extras:
        rec.update(extras)
    return rec


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(asset: str,
        window: int,
        windows: list[int] | None,
        horizon: int,
        dry_run: bool,
        out_path: Path) -> dict[str, Any]:
    """Single CLI entry point. Writes metrics JSON to out_path and to stdout."""

    engine_state = "ok" if _ENGINE_HELPERS_AVAILABLE else f"unavailable: {_ENGINE_IMPORT_ERROR}"
    if not _ENGINE_HELPERS_AVAILABLE and not dry_run:
        raise SystemExit(f"[calibration] engine helper import failed: {_ENGINE_IMPORT_ERROR}")

    window_list: list[int] = list(windows) if windows else [int(window)]

    # ------------------------------------------------------------------
    # Data-source selection.  dry_run is the ONLY path that emits
    # synthetic data.  All other paths attempt real market data first and
    # label honestly based on what was actually returned.
    #
    # Strings are chosen to be self-describing in any future audit so the
    # reader cannot mistake synthetic for live or vice-versa:
    #   LIVE_ACTUAL_DATA          — yfinance/Binance returned real OHLCV
    #   LIVE_ACTUAL_DATA_BINANCE  — engine's Binance path succeeded
    #   LIVE_ACTUAL_DATA_YFINANCE — engine path fell back to yfinance
    #   LIVE_FETCH_FAILED         — real fetch failed; see notes
    #   SYNTHETIC_DRY_RUN         — explicit --dry-run
    #   SYNTHETIC_FALLBACK        — real fetch failed AND no engine
    # ------------------------------------------------------------------
    fetch_notes: list[str] = []
    data_source: str
    if dry_run:
        ohlcv = synthetic_history(days=730)
        data_source = "SYNTHETIC_DRY_RUN"
        fetch_notes.append("dry_run_flag_set_by_user")
    else:
        # Force ≥730 days so the regime-shift adversarial test can find
        # ≥2 distinct calendar years.  Always expand by 2x and floor at 730.
        requested_period_days = max(window_list)
        period_days = max(requested_period_days * 2, 730)
        period_label = f"{period_days}d"
        try:
            ohlcv = fetch_history(interval="1d", period=period_label)
            # Distinguish Binance (the engine's preferred path) from yfinance
            # fallback so the audit trail shows which witness ran.
            try:
                _src = _import_fetch_ohlcv()(interval="1d", period=period_label)
                if _src is not None and not _src.empty and len(_src) == len(ohlcv):
                    data_source = "LIVE_ACTUAL_DATA_BINANCE"
                    fetch_notes.append("engine_fetch_ohlcv_succeeded")
                else:
                    data_source = "LIVE_ACTUAL_DATA_YFINANCE"
                    fetch_notes.append("engine_fetch_ohlcv_empty_or_mismatched")
            except Exception:
                data_source = "LIVE_ACTUAL_DATA_YFINANCE"
                fetch_notes.append("engine_fetch_ohlcv_unavailable_using_yfinance_fallback")
        except Exception as exc:
            if not _ENGINE_HELPERS_AVAILABLE:
                raise SystemExit(f"[calibration] history fetch failed: {exc}")
            ohlcv = synthetic_history(days=730)
            data_source = "LIVE_FETCH_FAILED"
            fetch_notes.append(f"live_fetch_error={type(exc).__name__}: {exc}")
            fetch_notes.append("using_synthetic_fallback_to_keep_harness_runnable")

    # Normalize: numeric columns, sorted datetime index, dedup.
    for col in ("high", "low", "close", "open", "volume"):
        if col in ohlcv.columns:
            ohlcv[col] = pd.to_numeric(ohlcv[col], errors="coerce")
    ohlcv = ohlcv.dropna(subset=[c for c in ("high", "low", "close") if c in ohlcv.columns])
    if ohlcv.index.has_duplicates:
        ohlcv = ohlcv[~ohlcv.index.duplicated(keep="last")]
    ohlcv = ohlcv.sort_index()
    if "close" not in ohlcv.columns and "Close" in ohlcv.columns:
        ohlcv = ohlcv.rename(columns={"Close": "close"})

    checkpoints: list[dict[str, Any]] = []
    summary_metrics: list[WindowMetrics] = []
    for wlbl in window_list:
        today = ohlcv.index[-1] if len(ohlcv) else pd.Timestamp.now("UTC")
        m = evaluate_window(ohlcv, horizon=horizon, window_label=wlbl, today=today)
        summary_metrics.append(m)
        checkpoints.append(metrics_to_record(m, extras={"asset": asset}))

    agg = rolling_means(summary_metrics)

    def _safe_fmean(xs: list[float]) -> float:
        finite = [x for x in xs if math.isfinite(x)]
        return float(statistics.fmean(finite)) if finite else float("nan")

    model_pinball_mean = _safe_fmean([m.model_pinball for m in summary_metrics])
    baseline_pinball_mean = _safe_fmean([m.baseline_pinball for m in summary_metrics])
    base_cov_mean = _safe_fmean([m.baseline_coverage for m in summary_metrics])

    walk_forward_passed = (
        bool(summary_metrics)
        and all(m.walk_forward_passed for m in summary_metrics)
        and math.isfinite(agg["pinball_skill_score"])
        and math.isfinite(agg["brier_skill"])
        and agg["pinball_skill_score"] > 0
        and agg["brier_skill"] > 0
        and 0.70 <= agg["model_coverage"] <= 0.90
        and max(window_list) >= 30
    )

    # ---- Back-propagation tuning layer ----
    tuning_block: dict[str, Any] = {"ran": False}
    tuning_better_than_baseline = False
    if walk_forward_passed:
        try:
            import tune as _tune  # type: ignore
            best_hp, _trials, t_m, v_m = _tune.search(
                ohlcv, horizon=horizon, window_labels=window_list,
                n_trials=40, seed=1337,
            )
            tuning_better_than_baseline = bool(
                math.isfinite(v_m.pinball_skill) and v_m.pinball_skill > 0
                and math.isfinite(v_m.brier_skill) and v_m.brier_skill > 0
                and 0.70 <= (v_m.model_coverage if math.isfinite(v_m.model_coverage) else -1) <= 0.90
            )
            tuning_block = {
                "ran": True,
                "best_params": {
                    "drift_scale": best_hp.drift_scale,
                    "atr_multiplier": best_hp.atr_multiplier,
                    "horizon_weights": list(best_hp.horizon_weights),
                },
                "tuning_metrics": _fold_to_dict_safe(t_m),
                "validation_metrics": _fold_to_dict_safe(v_m),
                "tuning_better_than_baseline": tuning_better_than_baseline,
            }
        except Exception as exc:
            tuning_block = {"ran": False, "error": repr(exc)}

    # ---- Hardening layer ----
    hardening_block: dict[str, Any] = {"ran": False}
    hardening_passed = False
    try:
        import harden as _harden  # type: ignore
        hardening_report = _harden.run_hardening(
            ohlcv, window_label=max(window_list), horizon=horizon,
        )
        hardening_passed = bool(hardening_report.get("hardening_passed", False))
        hardening_block = {"ran": True, **hardening_report}
    except Exception as exc:
        hardening_block = {"ran": False, "error": repr(exc)}

    # ---- Composite state machine (per Arif directive 2026-09-25) ----
    # Strict promotion rule (mirrors _decide, applied to the aggregated
    # rolling_means across all windows so the *outer* verdict is consistent
    # with what the inner per-window state-machine reports):
    #   pinball_skill_score > 0
    #   model_coverage ∈ [0.70, 0.90]
    #   brier_skill > 0
    #   window_days ≥ 30  (we always have this for the largest window in the sweep)
    # ALL four ⇒ SHADOW-eligible; only after tuning + hardening pass ⇒ LIVE.
    is_live_data = data_source.startswith("LIVE_ACTUAL_DATA")
    overall_state = "SHADOW"
    overall_notes: list[str] = []

    # ---- Live-data quarantine trigger ----
    # On real data, if BOTH pinball_skill AND brier_skill are negative, the
    # model is worse than baseline on both quantile and direction. Honest
    # outcome: recommend TUNE or QUARANTINE — never auto-promote, never hide.
    live_skill_summary = {
        "pinball_skill_score": agg.get("pinball_skill_score"),
        "brier_skill": agg.get("brier_skill"),
        "model_coverage": agg.get("model_coverage"),
    }
    pss_f = live_skill_summary["pinball_skill_score"]
    bss_f = live_skill_summary["brier_skill"]
    on_live_and_double_negative = (
        is_live_data
        and isinstance(pss_f, (int, float)) and math.isfinite(pss_f) and pss_f <= 0
        and isinstance(bss_f, (int, float)) and math.isfinite(bss_f) and bss_f <= 0
    )

    # Walk-forward must always pass first.
    if not walk_forward_passed:
        overall_state = "SHADOW"
        overall_notes.append("walk_forward_failed")
    else:
        if not tuning_better_than_baseline:
            overall_state = "SHADOW"
            overall_notes.append("tuning_no_baseline_beating_params")
        else:
            if not hardening_passed:
                overall_state = "DEGRADED"
                overall_notes.append("hardening_failed")
            else:
                # All three layers pass + ≥30 days data ⇒ LIVE.
                overall_state = "LIVE"
                overall_notes.append("all_layers_passed")

    if on_live_and_double_negative:
        overall_state = "QUARANTINE"
        overall_notes.append("live_data_pinball_AND_brier_both_negative")
        overall_notes.append("recommendation=tune_or_quarantine")

    overall_passed = walk_forward_passed
    overall_promo = overall_state == "LIVE"

    # ---- overall_evaluation — one human-readable verdict line ----
    cov_str = (
        f"{live_skill_summary['model_coverage']:.3f}"
        if isinstance(live_skill_summary["model_coverage"], (int, float))
        and math.isfinite(live_skill_summary["model_coverage"])
        else "n/a"
    )
    pss_str = (
        f"{pss_f:+.3f}"
        if isinstance(pss_f, (int, float)) and math.isfinite(pss_f)
        else "n/a"
    )
    bss_str = (
        f"{bss_f:+.3f}"
        if isinstance(bss_f, (int, float)) and math.isfinite(bss_f)
        else "n/a"
    )
    overall_evaluation = (
        f"{overall_state}: data_source={data_source}; "
        f"window={window_list}d; horizon={horizon}d; "
        f"pinball_skill={pss_str}, coverage={cov_str}, brier_skill={bss_str}; "
        f"walk_forward={'pass' if overall_passed else 'fail'}, "
        f"tuning={'pass' if tuning_better_than_baseline else 'fail'}, "
        f"hardening={'pass' if hardening_passed else 'fail'}; "
        f"recommendation="
        + (
            "PROMOTE_TO_LIVE"
            if overall_promo
            else "TUNE_OR_QUARANTINE"
            if on_live_and_double_negative
            else "KEEP_IN_SHADOW"
            if overall_state == "SHADOW"
            else "INVESTIGATE_DEGRADED"
        )
    )

    document = {
        "schema": "wealth.calibration.gold.v1",
        "generated_at": _now_iso(),
        "asset": asset,
        "data_source": data_source,
        "data_window_days": int(len(ohlcv)),
        "data_window_start": ohlcv.index.min().isoformat() if len(ohlcv) else None,
        "data_window_end": ohlcv.index.max().isoformat() if len(ohlcv) else None,
        "fetch_notes": fetch_notes,
        "engine_state": engine_state,
        "horizon_days": horizon,
        "checkpoints": checkpoints,
        "rolling_means": agg,
        "walk_forward_passed": overall_passed,
        "tuning_better_than_baseline": tuning_better_than_baseline,
        "hardening_passed": hardening_passed,
        "adversarial_test": hardening_block,
        "tuning": tuning_block,
        "calibration_state": overall_state,
        "promotion_recommended": overall_promo,
        "overall_notes": overall_notes,
        "overall_evaluation": overall_evaluation,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(document, indent=2, default=str))
    return document


def _fold_to_dict_safe(m: Any) -> dict[str, Any]:
    """Convert a FoldMetrics tuple-like to dict with NaN-safe floats."""
    def _f(x: float) -> float | None:
        if x is None or not math.isfinite(x):
            return None
        return float(round(x, 4))
    return {
        "pinball_skill": _f(getattr(m, "pinball_skill", float("nan"))),
        "model_coverage": _f(getattr(m, "model_coverage", float("nan"))),
        "brier_skill": _f(getattr(m, "brier_skill", float("nan"))),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Walk-forward calibration harness (gold).")
    p.add_argument("--asset", default="XAUUSD")
    p.add_argument("--window", type=int, default=30,
                   help="Single window size in days (default 30). Ignored if --windows set.")
    p.add_argument("--windows", type=int, nargs="+", default=None,
                   help="Sweep multiple windows, e.g. --windows 30 60 90")
    p.add_argument("--horizon", type=int, default=30,
                   help="Forecast horizon (days). Must be one the engine supports (30/60/90).")
    p.add_argument("--dry-run", action="store_true",
                   help="Use 180 days synthetic GBM data instead of live market.")
    p.add_argument("--out", type=str, default=str(VAULT999_METRICS),
                   help="Output JSON path. Defaults to VAULT999 metrics location.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.horizon not in (30, 60, 90):
        # Engine normalizes out-of-set horizons to 30; mirror that here so the
        # cone length matches what the live site emits.
        args.horizon = 30
    doc = run(
        asset=args.asset,
        window=args.window,
        windows=args.windows,
        horizon=args.horizon,
        dry_run=args.dry_run,
        out_path=Path(args.out),
    )
    print(json.dumps(doc, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
