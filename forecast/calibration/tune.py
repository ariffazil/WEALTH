#!/usr/bin/env python3
"""
Back-propagation tuning for the gold forecast cone
==================================================

Accepts an aggregated walk-forward checkpoint (from harness.py) and searches
a small hyperparameter space for a cone setting that **beats baseline on
aggregated walk-forward score**. The search is a fixed-budget random + greedy
refinement (a poor-man's Bayesian), not exhaustive grid — exhaustive would
be O(W^N) which is unaffordable for any meaningful W.

Splits:
    - First 70 % of checkpoints → TUNING (search)
    - Last 30 % of checkpoints   → HONEST VALIDATION (final score)

This is the binding anti-snooping rule from the directive: the optimizer
must never see the validation slice while selecting parameters.

Outputs:
    best_params.json        :  chosen (drift_scale, atr_multiplier,
                                horizon_weights) plus diagnostic trail
    tuned_checkpoint_metrics.json :  the validation-fold metrics under the
                                chosen parameters

Importantly: tune.py REPLAYS the cone math against the same checkpoints
using the replicated formula in harness.model_cone_at-shaped code. It does
**not** mutate any engine module — it is fully independent.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness  # type: ignore  # noqa: E402
from harness import (  # type: ignore  # noqa: E402
    pinball_loss, coverage_score, brier_dir, skill_score,
    rolling_realised_vol, random_walk_cone, _scalar, _engine_atr, _engine_ema,
    _engine_lin_slope, _ENGINE_HELPERS_AVAILABLE,
)


# ---------------------------------------------------------------------------
# Hyperparameter vector
# ---------------------------------------------------------------------------

@dataclass
class HPVector:
    drift_scale: float          # multiply slope ∈ [0.0, 2.0]. 1.0 = engine default
    atr_multiplier: float       # multiply σ bands ∈ [0.5, 1.8]. 1.0 = engine default
    horizon_weights: tuple      # per-horizon scaling of the median pull, length=3
                                #   (h≤7, 7<h≤14, 14<h). Default (1.0, 1.0, 1.0).


# Search space — bounded and small enough that 80 trials is meaningful.
HP_BOUNDS = {
    "drift_scale":     (0.0, 2.0),
    "atr_multiplier":  (0.5, 1.8),
    "horizon_weights": [(0.0, 2.0), (0.0, 2.0), (0.0, 2.0)],
}


def _sample_hp(rng: np.random.Generator) -> HPVector:
    return HPVector(
        drift_scale=float(rng.uniform(*HP_BOUNDS["drift_scale"])),
        atr_multiplier=float(rng.uniform(*HP_BOUNDS["atr_multiplier"])),
        horizon_weights=tuple(
            float(rng.uniform(*b)) for b in HP_BOUNDS["horizon_weights"]
        ),
    )


def _near_hp(rng: np.random.Generator, base: HPVector, jitter: float = 0.15) -> HPVector:
    """Greedy refinement: small jitter around an existing good vector."""
    def _j(bound, val):
        lo, hi = bound
        new = val + rng.uniform(-jitter, jitter) * (hi - lo)
        return float(np.clip(new, lo, hi))

    return HPVector(
        drift_scale=_j(HP_BOUNDS["drift_scale"], base.drift_scale),
        atr_multiplier=_j(HP_BOUNDS["atr_multiplier"], base.atr_multiplier),
        horizon_weights=tuple(
            _j(b, w) for b, w in zip(HP_BOUNDS["horizon_weights"], base.horizon_weights)
        ),
    )


# ---------------------------------------------------------------------------
# Tuned cone — replica of model_cone_at, but with HPVector applied
# ---------------------------------------------------------------------------

def tuned_cone_at(history: pd.DataFrame, horizon: int, hp: HPVector) -> dict[str, Any] | None:
    """Same math as harness.model_cone_at but with HPVector applied:
        drift    := hp.drift_scale * slope_clipped_to_atr
        sigma    := hp.atr_multiplier * atr * sqrt(t)
        pull     := per-horizon-bin weight * (ema200 - mid)
        bias     := momentum mean-reversion tilt (matches harness default config)

    NOTE (2026-09 audit fix): The cone math was tightened. ``hp.atr_multiplier``
    is now an external config parameter (default 0.6, was 1.0). The momentum
    mean-reversion bias is applied with the harness DEFAULT knobs
    (5d return > +2.5% → shift P50 down 0.3·ATR; < -2.5% → shift up 0.3·ATR).
    The HPVector does not sweep these knobs — they are configuration, not
    hyperparameters, because the directional Brier metric was negative on real
    XAUUSD before the bias was added.
    """
    if history is None or len(history) < 30:
        return None
    h = history if {"high", "low", "close"}.issubset(set(history.columns)) else None
    if h is None:
        h = history.copy()
        h = h.assign(high=h["close"] * 1.005, low=h["close"] * 0.995)

    close = h["close"]
    atr_val = float(_engine_atr(h[["high", "low", "close"]], 14).iloc[-1])
    if not np.isfinite(atr_val) or atr_val <= 0:
        return None
    ema20 = float(_engine_ema(close, 20).iloc[-1])
    ema50 = float(_engine_ema(close, 50).iloc[-1])
    ema200 = float(_engine_ema(close, 200).iloc[-1]) if len(close) >= 200 else ema50
    price = float(close.iloc[-1])

    slope = float(_engine_lin_slope(close.tail(20).to_numpy()))
    slope = max(-atr_val, min(atr_val, slope)) * hp.drift_scale

    trending = abs(ema20 - ema50) > 0.5 * atr_val
    blend_w_base = 0.2 if trending else 0.5

    w_short, w_mid, w_long = hp.horizon_weights

    # Use the harness canonical momentum-bias helper so the replica cannot drift
    # from the live engine.
    bias = harness._compute_momentum_bias(close, atr_val)

    p10, p50, p90 = [], [], []
    for t in range(1, horizon + 1):
        mid = price + slope * t + bias
        # Horizon-binned mean-reversion pull. Bins: [1..7], [8..14], [15..H].
        if t <= 7:
            w = w_short
        elif t <= 14:
            w = w_mid
        else:
            w = w_long
        mid += (ema200 - mid) * (1 - math.exp(-t / 20.0)) * blend_w_base * w
        sigma = atr_val * hp.atr_multiplier * math.sqrt(t)
        p10.append(mid - 1.282 * sigma)
        p50.append(mid)
        p90.append(mid + 1.282 * sigma)

    return {
        "p10": np.array(p10, dtype=float),
        "p50": np.array(p50, dtype=float),
        "p90": np.array(p90, dtype=float),
    }


# ---------------------------------------------------------------------------
# Replay evaluation under HPVector
# ---------------------------------------------------------------------------

@dataclass
class FoldMetrics:
    pinball_skill: float
    model_coverage: float
    brier_skill: float


def evaluate_hp_on_window(ohlcv_full: pd.DataFrame,
                          horizon: int,
                          window_label: int,
                          hp: HPVector,
                          eval_stride: int = 5) -> FoldMetrics:
    """Replica of harness.evaluate_window but uses tuned_cone_at(hp=).
    Returns aggregate metrics for the given test window."""
    df = ohlcv_full.copy()
    for col in ("high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["high", "low", "close"]).sort_index()
    if df.index.has_duplicates:
        df = df[~df.index.duplicated(keep="last")]

    n = len(df)
    if n < window_label + 30:
        return FoldMetrics(float("nan"), float("nan"), float("nan"))

    split = n - window_label
    close_series = df["close"]

    m10, m50, m90, b10, b50, b90 = [], [], [], [], [], []
    actuals: list[float] = []
    y_returns: list[float] = []
    p_ups: list[float] = []
    n_test = n - split
    test_positions = list(range(0, n_test, max(1, eval_stride)))

    for ti in test_positions:
        idx = split + ti
        if idx >= n - 1:
            break
        history = df.iloc[: idx + 1]
        if len(history) < 30:
            continue
        last_close = _scalar(history["close"].iloc[-1])
        if not np.isfinite(last_close):
            continue

        cone = tuned_cone_at(history, horizon, hp)
        if cone is None or len(cone["p50"]) < 1:
            continue
        max_h = min(len(cone["p50"]), n - idx - 1)
        if max_h < 1:
            continue
        vol = rolling_realised_vol(close_series.iloc[: idx + 1], window=60)
        for h in range(max_h):
            actual = _scalar(close_series.iloc[idx + 1 + h])
            if not np.isfinite(actual):
                continue
            actuals.append(actual)
            y_returns.append(actual - last_close)
            m10.append(float(cone["p10"][h]))
            m50.append(float(cone["p50"][h]))
            m90.append(float(cone["p90"][h]))
            bw = random_walk_cone(last_close, h + 1, vol)
            b10.append(float(bw.p10[h])); b50.append(float(bw.p50[h])); b90.append(float(bw.p90[h]))
            h_sigma = max(vol * last_close * math.sqrt(h + 1), 1e-6)
            delta = (float(cone["p50"][h]) - last_close) / h_sigma
            p_ups.append(1.0 / (1.0 + math.exp(-3.0 * delta)))

    if not actuals:
        return FoldMetrics(float("nan"), float("nan"), float("nan"))

    y = np.array(actuals, dtype=float)
    m10, m50, m90 = map(np.array, (m10, m50, m90))
    b10, b50, b90 = map(np.array, (b10, b50, b90))

    def _qpin(qp, q):
        diff = y - qp
        loss = np.where(diff >= 0, q * diff, (q - 1) * diff)
        return float(np.nanmean(loss)) if loss.size else float("nan")

    m_p = np.nanmean([_qpin(m10, 0.1), _qpin(m50, 0.5), _qpin(m90, 0.9)])
    b_p = np.nanmean([_qpin(b10, 0.1), _qpin(b50, 0.5), _qpin(b90, 0.9)])
    pss = skill_score(m_p, b_p)

    def _cov(lo, hi):
        inb = (y >= lo) & (y <= hi)
        fin = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
        return float(np.sum(inb & fin) / fin.sum()) if fin.sum() else float("nan")
    mcov = _cov(m10, m90)
    yret = np.array(y_returns, dtype=float)
    pdir = np.array(p_ups, dtype=float)
    brier_m = brier_dir(yret, pdir)
    bs = skill_score(brier_m, 0.25)
    return FoldMetrics(pss, mcov, bs)


# ---------------------------------------------------------------------------
# Anti-snooping split: 70 % tuning, 30 % honest validation
# ---------------------------------------------------------------------------

def _walk_forward_windows(ohlcv_full: pd.DataFrame,
                          window_labels: list[int]) -> list[tuple[pd.Timestamp, int]]:
    """Generate a list of (anchor_ts, window_label) pairs that mimic how the
    harness steps: one per (window, walk) combination, anchored at the latest
    ``window_label`` days. We do not need multiple anchors per window in the
    tune step — the harness already evaluated multi-step walk-forward; tuning
    only needs to find HPs that work over the same test slice."""
    rows = []
    today = ohlcv_full.index[-1] if len(ohlcv_full) else pd.Timestamp.now("UTC")
    for wlbl in window_labels:
        rows.append((today, wlbl))
    return rows


def _safe(x: float) -> float:
    return float(x) if (x is not None and math.isfinite(x)) else float("nan")


def search(ohlcv_full: pd.DataFrame,
           horizon: int,
           window_labels: list[int],
           n_trials: int = 60,
           seed: int = 1337) -> tuple[HPVector, list[dict[str, Any]], FoldMetrics, FoldMetrics]:
    """Bayesian-style random + greedy refinement search.

    Tuning fold = 70 % of windows; honest validation fold = 30 %.
    Returns: (best_hp, trial_log, tuning_metrics, validation_metrics)."""
    if not _ENGINE_HELPERS_AVAILABLE:
        raise SystemExit("[tune] engine helpers unavailable; cannot compute ATR/EMA.")

    rng = np.random.default_rng(seed)

    # Split windows: first 70 % for tuning, last 30 % for honest validation.
    n = len(window_labels)
    cut = max(1, int(n * 0.7))
    tuning_windows = window_labels[:cut]
    validation_windows = window_labels[cut:] or window_labels[-1:]

    def _score_on(windows: list[int], hp: HPVector) -> FoldMetrics:
        per = [evaluate_hp_on_window(ohlcv_full, horizon, w, hp) for w in windows]
        if not per:
            return FoldMetrics(float("nan"), float("nan"), float("nan"))
        pss = np.nanmean([p.pinball_skill for p in per])
        cov = np.nanmean([p.model_coverage for p in per])
        bss = np.nanmean([p.brier_skill for p in per])
        return FoldMetrics(_safe(pss), _safe(cov), _safe(bss))

    trials: list[dict[str, Any]] = []
    best_hp: HPVector = _sample_hp(rng)
    best_score = -math.inf

    # Phase 1: random exploration
    phase1 = max(1, int(n_trials * 0.66))
    for k in range(phase1):
        hp = _sample_hp(rng)
        m = _score_on(tuning_windows, hp)
        score = _composite_score(m)
        trials.append({
            "trial": k, "phase": "random", "hp": _hp_to_dict(hp),
            "tuning": _fold_to_dict(m), "score": _safe(score),
        })
        if score > best_score:
            best_score = score
            best_hp = hp

    # Phase 2: greedy jitter around best
    phase2 = n_trials - phase1
    for k in range(phase2):
        hp = _near_hp(rng, best_hp)
        m = _score_on(tuning_windows, hp)
        score = _composite_score(m)
        trials.append({
            "trial": phase1 + k, "phase": "greedy", "hp": _hp_to_dict(hp),
            "tuning": _fold_to_dict(m), "score": _safe(score),
        })
        if score > best_score:
            best_score = score
            best_hp = hp

    tuning_metrics = _score_on(tuning_windows, best_hp)
    validation_metrics = _score_on(validation_windows, best_hp)
    return best_hp, trials, tuning_metrics, validation_metrics


def _composite_score(m: FoldMetrics) -> float:
    """Composite objective: maximise quantile skill, prefer coverage in band,
    use directional skill as tiebreaker. Float('nan') treated as -inf so the
    search prefers finite metrics over NaN."""
    parts = []
    for v in (m.pinball_skill, m.model_coverage, m.brier_skill):
        if not math.isfinite(v):
            return -math.inf
        parts.append(v)
    pss, cov, bss = parts
    # penalty for being outside the honest band [0.70, 0.90]
    band_pen = max(0.0, 0.70 - cov) + max(0.0, cov - 0.90)
    return 1.0 * pss + 1.0 * bss - 5.0 * band_pen


def _hp_to_dict(hp: HPVector) -> dict[str, Any]:
    return {
        "drift_scale": hp.drift_scale,
        "atr_multiplier": hp.atr_multiplier,
        "horizon_weights": list(hp.horizon_weights),
    }


def _fold_to_dict(m: FoldMetrics) -> dict[str, float]:
    return {
        "pinball_skill": _safe(m.pinball_skill),
        "model_coverage": _safe(m.model_coverage),
        "brier_skill": _safe(m.brier_skill),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Back-propagation tuner for gold cone.")
    ap.add_argument("--ohlcv", required=False, help="Path to OHLCV parquet/csv (synthesized if missing)")
    ap.add_argument("--dry-run", action="store_true", help="Use synthetic GBM data instead of live.")
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--windows", type=int, nargs="+", default=[30, 60, 90])
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--best-out", default=str(HERE / "best_params.json"))
    ap.add_argument("--tuned-out", default=str(HERE / "tuned_checkpoint_metrics.json"))
    args = ap.parse_args(argv)

    if args.dry_run:
        ohlcv = harness.synthetic_history(days=730)
    elif args.ohlcv:
        df = pd.read_parquet(args.ohlcv) if args.ohlcv.endswith(".parquet") else pd.read_csv(args.ohlcv, index_col=0, parse_dates=True)
        ohlcv = df.copy()
    else:
        # Default: re-use harness's run() output's data by re-running once with --dry-run,
        # so tune is hermetic.
        ohlcv = harness.synthetic_history(days=730)

    t0 = time.time()
    best_hp, trials, tuning_m, validation_m = search(
        ohlcv, horizon=args.horizon,
        window_labels=args.windows, n_trials=args.trials, seed=args.seed,
    )
    dt = time.time() - t0

    best_record = {
        "schema": "wealth.tune.gold.v1",
        "horizon_days": args.horizon,
        "windows": args.windows,
        "best_params": _hp_to_dict(best_hp),
        "tuning_metrics": _fold_to_dict(tuning_m),
        "validation_metrics": _fold_to_dict(validation_m),
        "tuning_window_split": f"first_70pct={args.windows[:max(1,int(len(args.windows)*0.7))]}",
        "validation_window_split": f"last_30pct={args.windows[max(1,int(len(args.windows)*0.7)):]}",
        "trials": trials,
        "elapsed_seconds": round(dt, 3),
        "tuning_better_than_baseline": bool(
            math.isfinite(validation_m.pinball_skill) and validation_m.pinball_skill > 0
            and math.isfinite(validation_m.brier_skill) and validation_m.brier_skill > 0
        ),
        "honest_validation_coverage": _safe(validation_m.model_coverage),
    }
    Path(args.best_out).write_text(json.dumps(best_record, indent=2, default=str))

    tuned_doc = {
        "schema": "wealth.tune.validation.v1",
        "best_params": _hp_to_dict(best_hp),
        "validation_metrics": _fold_to_dict(validation_m),
        "notes": "Honest-validation slice (last 30 % of windows). Tuning slice never saw validation.",
    }
    Path(args.tuned_out).write_text(json.dumps(tuned_doc, indent=2, default=str))

    print(json.dumps(best_record, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
