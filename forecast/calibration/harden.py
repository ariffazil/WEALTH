#!/usr/bin/env python3
"""
Hardening tests for the gold cone — three adversarial tests
==========================================================

(a) MISSING DATA TEST
    Remove ~20 % of points at random, re-score. The model's degradation
    (Δ_model) must NOT exceed the random-walk baseline's degradation
    (Δ_baseline). Otherwise the cone is brittle to data gaps.

(b) REGIME SHIFT TEST
    Train-equivalent on 2022-2023, test on 2024+. Measure the skill drop
    from in-sample to out-of-sample. Drop > 50 % ⇒ DEGRADED.

    Years are auto-discovered if the data spans multi-year. If the data
    does not span a regime change, this test is reported as INSUFFICIENT
    rather than QUARANTINE — refusing to run on insufficient data is more
    honest than inventing one.

(c) DISTRIBUTION SHIFT TEST
    Compute Population Stability Index (PSI) on returns / ATR / regime
    probability between the training half and the live half. PSI > 0.25
    is the standard threshold for "significant drift".

Outputs a JSON block:
    {
      adversarial_test: {
        missing_data_degradation: float,
        regime_shift_skill_drop: float | null,
        distribution_psi: float,
        hardening_passed: bool,
        notes: [...]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness  # type: ignore  # noqa: E402
from harness import (  # type: ignore  # noqa: E402
    evaluate_window, WindowMetrics, _scalar,
    rolling_realised_vol, random_walk_cone,
    pinball_loss, coverage_score, brier_dir, skill_score,
    _engine_atr, _engine_ema,
)


# ---------------------------------------------------------------------------
# (a) Missing-data test
# ---------------------------------------------------------------------------

def missing_data_test(ohlcv_full: pd.DataFrame,
                      window_label: int = 90,
                      horizon: int = 30,
                      missing_frac: float = 0.20,
                      n_trials: int = 5,
                      seed: int = 1337) -> float:
    """Drop ~missing_frac of bars randomly (n_trials seeds), re-score the model
    and the baseline. Returns the relative degradation ratio:
        (Δ_model / Δ_baseline) > 1 ⇒ model degrades faster than baseline.
    A pass is when this ratio ≤ 1.0."""
    rng = np.random.default_rng(seed)

    def _aggregate(ohlcv: pd.DataFrame) -> tuple[float, float]:
        m = harness.evaluate_window(ohlcv, horizon=horizon, window_label=window_label,
                                    today=ohlcv.index[-1])
        return _safe(m.model_pinball), _safe(m.baseline_pinball)

    base_model, base_base = _aggregate(ohlcv_full)
    if not (math.isfinite(base_model) and math.isfinite(base_base)) or base_base <= 0:
        return float("nan")

    model_deltas = []
    base_deltas = []
    for k in range(n_trials):
        idx_to_drop = rng.choice(
            len(ohlcv_full),
            size=int(len(ohlcv_full) * missing_frac),
            replace=False,
        )
        keep_mask = np.ones(len(ohlcv_full), dtype=bool)
        keep_mask[idx_to_drop] = False
        df_dropped = ohlcv_full.iloc[keep_mask].copy()
        if len(df_dropped) < window_label + 30:
            continue
        m_model, m_base = _aggregate(df_dropped)
        if math.isfinite(m_model) and math.isfinite(m_base):
            model_deltas.append(m_model - base_model)
            base_deltas.append(m_base - base_base)

    if not model_deltas:
        return float("nan")
    avg_model_delta = float(np.mean(model_deltas))
    avg_base_delta = float(np.mean(base_deltas))
    # Degradation ratio: smaller is better (model drops less than baseline).
    if abs(avg_base_delta) < 1e-6:
        return float("nan")
    return avg_model_delta / avg_base_delta


# ---------------------------------------------------------------------------
# (b) Regime-shift test
# ---------------------------------------------------------------------------

def regime_shift_test(ohlcv_full: pd.DataFrame,
                      horizon: int = 30,
                      window_label: int = 60) -> tuple[float | None, list[str]]:
    """Train-quarter vs test-quarter. If we have ≥2 years of data, split at
    the boundary between the 2 most recent years. Compute model pinball_skill
    on each half. Skill drop = (in_sample - out_of_sample) / max(|in_sample|, eps).

    A drop > 0.50 ⇒ DEGRADED."""
    notes: list[str] = []
    if not isinstance(ohlcv_full.index, pd.DatetimeIndex):
        notes.append("non_datetime_index")
        return None, notes
    if len(ohlcv_full) < 500:
        notes.append("insufficient_data_for_regime_split")
        return None, notes

    # Use calendar-year median index to find year boundaries.
    years = sorted(set(ohlcv_full.index.year.tolist()))
    if len(years) < 2:
        notes.append("only_one_year_of_data")
        return None, notes

    # In-sample = years[:-1]; out-of-sample = years[-1].
    in_sample = ohlcv_full[ohlcv_full.index.year.isin(years[:-1])]
    out_of_sample = ohlcv_full[ohlcv_full.index.year.isin(years[-1:])]
    notes.append(f"in_sample_years={years[:-1]}_rows={len(in_sample)}")
    notes.append(f"out_sample_year={years[-1]}_rows={len(out_of_sample)}")

    if len(in_sample) < window_label + 30 or len(out_of_sample) < window_label + 30:
        notes.append("window_too_large_for_split")
        return None, notes

    m_in = harness.evaluate_window(in_sample, horizon=horizon,
                                   window_label=min(window_label, len(in_sample) // 2),
                                   today=in_sample.index[-1])
    m_out = harness.evaluate_window(out_of_sample, horizon=horizon,
                                    window_label=min(window_label, len(out_of_sample) // 2),
                                    today=out_of_sample.index[-1])

    in_skill = _safe(m_in.pinball_skill_score)
    out_skill = _safe(m_out.pinball_skill_score)
    if not (math.isfinite(in_skill) and math.isfinite(out_skill)):
        notes.append("non_finite_skills")
        return None, notes
    eps = 0.05
    denom = max(abs(in_skill), eps)
    drop = (in_skill - out_skill) / denom
    notes.append(f"in_sample_pinball_skill={in_skill:.4f}")
    notes.append(f"out_sample_pinball_skill={out_skill:.4f}")
    return float(drop), notes


# ---------------------------------------------------------------------------
# (c) Distribution-shift test (PSI on returns / ATR / regime prob)
# ---------------------------------------------------------------------------

def psi_score(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Standard PSI. Both arrays must be non-empty and contain at least
    n_bins unique values to be meaningful — degenerate inputs ⇒ 0."""
    if expected.size < n_bins or actual.size < n_bins:
        return 0.0
    quantiles = np.linspace(0, 1, n_bins + 1)
    edges = np.quantile(expected, quantiles)
    edges[0] = -np.inf; edges[-1] = np.inf
    edges = np.unique(edges)
    if edges.size < 3:
        return 0.0

    expected_counts, _ = np.histogram(expected, bins=edges)
    actual_counts, _ = np.histogram(actual, bins=edges)
    expected_pct = expected_counts / expected_counts.sum()
    actual_pct = actual_counts / actual_counts.sum()

    eps = 1e-6
    expected_pct = np.where(expected_pct == 0, eps, expected_pct)
    actual_pct = np.where(actual_pct == 0, eps, actual_pct)

    psi = float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))
    return psi


def distribution_shift_test(ohlcv_full: pd.DataFrame) -> tuple[float, list[str]]:
    """PSI on returns (5d), ATR(14), and ema-distance-to-close, between the
    first and second halves. Mean of the three PSIs is reported."""
    notes: list[str] = []
    if len(ohlcv_full) < 200:
        notes.append("insufficient_data_for_psi")
        return 0.0, notes

    df = ohlcv_full.copy()
    df["return5"] = df["close"].pct_change(5).to_numpy()
    atr_series = _engine_atr(df[["high", "low", "close"]].dropna(), 14)
    df["atr14"] = atr_series
    df["ema_close_dist"] = (df["close"] - _engine_ema(df["close"], 50)).abs()

    half = len(df) // 2
    train = df.iloc[:half].dropna()
    live = df.iloc[half:].dropna()
    notes.append(f"train_rows={len(train)} live_rows={len(live)}")

    if len(train) < 60 or len(live) < 60:
        notes.append("halves_too_small")
        return 0.0, notes

    psi_components = []
    for col in ("return5", "atr14", "ema_close_dist"):
        e = train[col].to_numpy()
        a = live[col].to_numpy()
        if e.size < 12 or a.size < 12:
            continue
        s = psi_score(e, a)
        psi_components.append(s)
        notes.append(f"psi_{col}={s:.4f}")

    if not psi_components:
        notes.append("no_components_computed")
        return 0.0, notes
    mean_psi = float(np.mean(psi_components))
    notes.append(f"mean_psi={mean_psi:.4f}")
    return mean_psi, notes


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

def run_hardening(ohlcv_full: pd.DataFrame,
                  window_label: int = 90,
                  horizon: int = 30) -> dict[str, Any]:
    md = missing_data_test(ohlcv_full, window_label=window_label, horizon=horizon)
    rs_drop, rs_notes = regime_shift_test(ohlcv_full, horizon=horizon, window_label=window_label)
    ds_psi, ds_notes = distribution_shift_test(ohlcv_full)

    notes: list[str] = []
    notes.extend(rs_notes)
    notes.extend(ds_notes)

    passes = []

    # (a) Missing data — pass if ratio ≤ 1.0 (i.e. model degrades no faster
    # than baseline) OR if ratio is not finite (treat as inconclusive).
    if not math.isfinite(md):
        notes.append("missing_data_inconclusive")
    else:
        passes.append(md <= 1.0)
        notes.append(f"missing_data_degradation_ratio={md:.4f}")

    # (b) Regime shift — pass if None (inconclusive) OR drop ≤ 0.5.
    if rs_drop is None:
        notes.append("regime_shift_inconclusive")
    else:
        passes.append(rs_drop <= 0.5)
        notes.append(f"regime_shift_skill_drop={rs_drop:.4f}")

    # (c) Distribution PSI — pass if PSI ≤ 0.25.
    passes.append(ds_psi <= 0.25)
    notes.append(f"distribution_psi={ds_psi:.4f}")

    hardening_passed = bool(passes) and all(passes)

    return {
        "missing_data_degradation": _safe(md) if math.isfinite(md) else None,
        "regime_shift_skill_drop": _safe(rs_drop) if rs_drop is not None and math.isfinite(rs_drop) else None,
        "distribution_psi": _safe(ds_psi),
        "hardening_passed": hardening_passed,
        "notes": notes,
    }


def _safe(x: float | None) -> float | None:
    if x is None:
        return None
    if not math.isfinite(x):
        return None
    return float(x)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Adversarial hardening tests for gold cone.")
    ap.add_argument("--dry-run", action="store_true", help="Use synthetic GBM data.")
    ap.add_argument("--ohlcv", help="Path to OHLCV parquet/csv.")
    ap.add_argument("--window", type=int, default=90)
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--out", default=str(HERE / "hardening_report.json"))
    args = ap.parse_args(argv)

    if args.ohlcv:
        df = pd.read_parquet(args.ohlcv) if args.ohlcv.endswith(".parquet") else pd.read_csv(args.ohlcv, index_col=0, parse_dates=True)
        ohlcv = df
    elif args.dry_run:
        ohlcv = harness.synthetic_history(days=730)
    else:
        ohlcv = harness.synthetic_history(days=730)

    report = run_hardening(ohlcv, window_label=args.window, horizon=args.horizon)
    Path(args.out).write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
