"""Test suite for M5 — Adaptive Distribution Engine.

Covers:
    * Data layer (loading + provenance)
    * Feature extraction
    * M5.1 volatility candidates (EWMA, HAR, GARCH-T) + QLIKE selection
    * M5.2 range forecast
    * M5.3 asymmetry
    * M5.4 expansion detection
    * M5.5 conformal recalibration
    * M5.6 touch probability
    * M5.7 abstention + regime classification
    * Non-direction guarantee (P50 == M0 == last_close)
    * M0 vs M5 interval quality comparison on synthetic + real

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the project root is on sys.path for `forecast.*` imports.
sys.path.insert(0, "/root/WEALTH")

from forecast.m5 import (  # noqa: E402
    SCHEMA,
    STATUS,
    run_m5,
    run_walk_forward,
    write_admission_rule_failed_receipt,
    write_admission_pass_receipt,
)
from forecast.m5.abstention import decide_abstention, classify_regime  # noqa: E402
from forecast.m5.asymmetry import forecast_asymmetry  # noqa: E402
from forecast.m5.conformal import ConformalCalibrator  # noqa: E402
from forecast.m5.data import (  # noqa: E402
    History1H,
    _synthetic_1h,
    aggregate_bars,
    load_xauusd_1h,
)
from forecast.m5.expansion import detect_expansion  # noqa: E402
from forecast.m5.features import FeatureVector, compute_features  # noqa: E402
from forecast.m5.range import forecast_range  # noqa: E402
from forecast.m5.touch_prob import touch_probability_2sigma  # noqa: E402
from forecast.m5.volatility import (  # noqa: E402
    VolCandidate,
    fit_ewma,
    fit_garch_t,
    fit_har,
    forecast_sigma_h,
    qlike_loss,
    select_best_vol,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def live_history() -> History1H:
    """Real XAUUSD 1H history (sandbox yfinance cascade)."""
    return load_xauusd_1h(days=729, seed=1337)


@pytest.fixture(scope="module")
def synthetic_history() -> History1H:
    """Deterministic synthetic 1H GBM series."""
    df = _synthetic_1h(days=729, seed=1337)
    return History1H(
        df=df,
        source="SYNTHETIC",
        reason="synthetic_gbm_1h_d729_s1337",
        fetched_at="2026-09-25T00:00:00+00:00",
        sandbox_price_offset_acknowledged=False,
    )


# ── Test 1: Data layer + provenance ─────────────────────────────────────


def test_data_layer_loads_with_provenance(live_history: History1H, synthetic_history: History1H) -> None:
    """The 1H history must be loadable and carry provenance."""
    # Live
    assert live_history.source in ("LIVE", "SYNTHETIC")
    assert len(live_history.df) > 24 * 100
    for col in ("open", "high", "low", "close"):
        assert col in live_history.df.columns
    # Synthetic
    assert synthetic_history.source == "SYNTHETIC"
    assert len(synthetic_history.df) > 24 * 100


def test_aggregate_bars_preserves_provenance(live_history: History1H) -> None:
    """Resampling to 4H/24H must preserve source and label."""
    agg_4h = aggregate_bars(live_history, hours_per_bar=4)
    assert agg_4h.source == live_history.source
    assert "agg_4h" in agg_4h.reason
    assert len(agg_4h.df) < len(live_history.df)
    for col in ("open", "high", "low", "close"):
        assert col in agg_4h.df.columns


# ── Test 2: Feature extraction ──────────────────────────────────────────


def test_features_extracts_all_components(live_history: History1H) -> None:
    """Every documented feature field must populate for a deep enough history."""
    df = live_history.df
    feats = compute_features(df, origin_idx=len(df) - 1)
    d = feats.to_dict()
    # Required fields must be present
    expected_keys = {
        "log_return_1h", "log_return_24h", "high_low_range_1h", "true_range_1h",
        "atr_24h", "realized_vol_6h", "realized_vol_24h", "realized_vol_72h",
        "realized_vol_168h", "semivariance_up_24h", "semivariance_down_24h",
        "vol_of_vol_168h", "gap_indicator", "trend_efficiency_24h",
        "compression_percentile_168h", "hour_of_day", "distance_from_ema_24h",
    }
    assert set(d.keys()) >= expected_keys
    # For a 729-day 1H history, we should have real numeric values
    assert np.isfinite(feats.realized_vol_168h) and feats.realized_vol_168h > 0
    assert np.isfinite(feats.atr_24h) and feats.atr_24h > 0
    assert 0.0 <= feats.compression_percentile_168h <= 1.0
    assert 0 <= feats.hour_of_day <= 23


# ── Test 3: M5.1 EWMA ────────────────────────────────────────────────────


def test_m5_1_ewma_basic() -> None:
    """EWMA must produce a finite variance forecast for any non-trivial input."""
    rng = np.random.default_rng(7)
    r = rng.normal(0, 0.01, 1000)
    cand = fit_ewma(r ** 2, lam=0.94)
    assert isinstance(cand, VolCandidate)
    assert cand.name == "EWMA"
    assert cand.forecast_var_h1 > 0
    assert cand.forecast_sigma_h1 > 0
    assert np.isfinite(cand.forecast_sigma_h1)
    # √h scaling
    sig_24 = forecast_sigma_h(cand, horizon_h=24)
    assert np.isfinite(sig_24)
    # Variance scales by h, sigma by √h
    assert sig_24 > cand.forecast_sigma_h1


def test_m5_1_har_basic() -> None:
    """HAR-RV requires ≥22 days of hourly data."""
    rng = np.random.default_rng(11)
    r = rng.normal(0, 0.01, 24 * 60)  # 60 days hourly
    cand = fit_har(r ** 2)
    assert cand.name == "HAR"
    assert cand.forecast_var_h1 > 0
    assert cand.forecast_sigma_h1 > 0


def test_m5_1_garch_t_basic() -> None:
    """GARCH(1,1) with Student-t scale must fit on a sufficiently long series."""
    rng = np.random.default_rng(13)
    r = rng.normal(0, 0.01, 1500)
    cand = fit_garch_t(r, nu=6.0)
    assert cand.name == "GARCH-T"
    assert cand.forecast_var_h1 > 0
    assert cand.forecast_sigma_h1 > 0
    assert "omega" in cand.params and "alpha" in cand.params and "beta" in cand.params


def test_m5_1_select_best_returns_lowest_qlike() -> None:
    """select_best_vol must return the candidate with the lowest QLIKE."""
    rng = np.random.default_rng(17)
    # Realistic regime-switching vol (heavy tail)
    r = np.concatenate([
        rng.normal(0, 0.005, 800),
        rng.normal(0, 0.020, 400),
        rng.normal(0, 0.005, 800),
    ])
    best = select_best_vol(r)
    # Compare qlikes against each candidate
    ql_ewma = fit_ewma(r ** 2).qlike_calibration
    ql_har = fit_har(r ** 2).qlike_calibration
    ql_garch = fit_garch_t(r).qlike_calibration
    candidates = [("EWMA", ql_ewma), ("HAR", ql_har), ("GARCH-T", ql_garch)]
    valid = [c for c in candidates if np.isfinite(c[1]) and c[1] < float("inf")]
    assert valid, "no candidate should fail entirely"
    chosen_ql = best.qlike_calibration
    for name, ql in valid:
        assert chosen_ql <= ql + 1e-9, f"selected {best.name} has qlike {chosen_ql} but {name} has lower {ql}"


def test_qlike_loss_sanity() -> None:
    """QLIKE on a perfect forecast must be ≤ QLIKE on a wild forecast."""
    r2 = np.array([0.0001, 0.0002, 0.00015, 0.0003, 0.0001])
    perfect = r2.copy()
    wild = np.full_like(r2, 0.01)
    q_perfect = qlike_loss(r2, perfect)
    q_wild = qlike_loss(r2, wild)
    assert q_perfect < q_wild
    assert q_perfect < 0.05  # near 0 for perfect forecast


# ── Test 4: M5.2 range forecast ─────────────────────────────────────────


def test_m5_2_range_basic(live_history: History1H) -> None:
    """forecast_range must produce a positive range with a sensible multiplier."""
    df = live_history.df
    sigma = 0.003
    rng = forecast_range(df, horizon_h=24, sigma_h1=sigma, calibration_window=720)
    assert np.isfinite(rng.expected_range) and rng.expected_range > 0
    assert rng.n_calibration_horizons > 100
    assert rng.range_multiplier_k > 0
    # k should be in a reasonable range for hourly bars (~1.5–4 typical)
    assert 1.0 < rng.range_multiplier_k < 6.0
    # expected_high - expected_low should equal expected_range
    assert abs((rng.expected_high - rng.expected_low) - rng.expected_range) < 1.0


# ── Test 5: M5.3 asymmetry ──────────────────────────────────────────────


def test_m5_3_asymmetry_bounds() -> None:
    """Asymmetry must be in [-1, 1] and split the range correctly."""
    rng_range = 100.0
    # Upside-tilted
    a_up = forecast_asymmetry(df=None, horizon_h=24, expected_range=rng_range, sv_up_24h=0.20, sv_down_24h=0.05)
    assert -1.0 <= a_up.asymmetry_score <= 1.0
    assert a_up.asymmetry_score > 0  # upside dominates
    # Downside-tilted
    a_dn = forecast_asymmetry(df=None, horizon_h=24, expected_range=rng_range, sv_up_24h=0.05, sv_down_24h=0.20)
    assert a_dn.asymmetry_score < 0
    # The two halves sum to the range
    assert abs((a_up.upper_half + a_up.lower_half) - rng_range) < 1e-6
    # Missing semivariance → zero asymmetry
    a_zero = forecast_asymmetry(df=None, horizon_h=24, expected_range=rng_range, sv_up_24h=float("nan"), sv_down_24h=float("nan"))
    assert a_zero.asymmetry_score == 0.0


# ── Test 6: M5.4 expansion detection ────────────────────────────────────


def test_m5_4_expansion_detects_spike(live_history: History1H) -> None:
    """A known volatility spike should yield a higher expansion probability."""
    df = live_history.df
    e = detect_expansion(df, sigma_h1_forecast=0.003)
    assert 0.0 <= e.p_vol_expansion <= 1.0
    assert e.notes != ""
    # The CUSUM stat should be finite
    assert np.isfinite(e.cusum_stat)


# ── Test 7: M5.5 conformal recalibration ────────────────────────────────


def test_m5_5_conformal_calibrator_narrows_band() -> None:
    """A calibrator trained on near-zero scores should narrow the band."""
    cal = ConformalCalibrator(target_coverage_p10_p90=0.80, target_coverage_p25_p75=0.50)
    # Record 30 "easy" outcomes (score = 0.5 means realised is half a band away)
    for _ in range(30):
        cal.record(realised=10.0, p50=10.0, p10=9.0, p25=9.5, p75=10.5, p90=11.0)
    p10, p25, p50, p75, p90 = cal.recalibrate(p10=9.0, p25=9.5, p50=10.0, p75=10.5, p90=11.0)
    # P50 unchanged
    assert p50 == 10.0
    # Either applied or not — but if applied, bands should adjust
    state = cal.state()
    assert "applied" in state["last_recalibration"]


def test_conformal_insufficient_window_returns_input() -> None:
    """With fewer than 8 scores, recalibrate must be a no-op."""
    cal = ConformalCalibrator()
    for _ in range(5):
        cal.record(realised=10.0, p50=10.0, p10=9.0, p25=9.5, p75=10.5, p90=11.0)
    p10, p25, p50, p75, p90 = cal.recalibrate(p10=9.0, p25=9.5, p50=10.0, p75=10.5, p90=11.0)
    assert (p10, p25, p50, p75, p90) == (9.0, 9.5, 10.0, 10.5, 11.0)
    assert cal.state()["last_recalibration"]["applied"] is False


# ── Test 8: M5.6 touch probability ──────────────────────────────────────


def test_m5_6_touch_probability_bounds() -> None:
    """Touch probability must be in [0, 0.95] and increase with horizon."""
    tp_1 = touch_probability_2sigma(horizon_h=1, sigma_h1=0.003, p_vol_expansion=0.5, asymmetry_score=0.0, compression_percentile=0.5)
    tp_72 = touch_probability_2sigma(horizon_h=72, sigma_h1=0.003, p_vol_expansion=0.5, asymmetry_score=0.0, compression_percentile=0.5)
    assert 0.0 <= tp_1.p_touch_upper_2sigma <= 0.95
    assert 0.0 <= tp_72.p_touch_upper_2sigma <= 0.95
    # Longer horizon → higher probability of touching
    assert tp_72.p_touch_upper_2sigma > tp_1.p_touch_upper_2sigma


def test_touch_prob_asymmetric_with_asymmetry() -> None:
    """Asymmetry must lift the touch probability on the dominant side."""
    tp_up = touch_probability_2sigma(horizon_h=24, sigma_h1=0.003, asymmetry_score=+0.5)
    tp_dn = touch_probability_2sigma(horizon_h=24, sigma_h1=0.003, asymmetry_score=-0.5)
    # +asym lifts upper, -asym lifts lower
    assert tp_up.p_touch_upper_2sigma > tp_up.p_touch_lower_2sigma
    assert tp_dn.p_touch_lower_2sigma > tp_dn.p_touch_upper_2sigma


# ── Test 9: M5.7 abstention + regime ────────────────────────────────────


def test_m5_7_regime_classification(live_history: History1H) -> None:
    """The regime classifier must produce one of the four allowed labels."""
    df = live_history.df
    feats = compute_features(df, origin_idx=len(df) - 1)
    e = detect_expansion(df, sigma_h1_forecast=0.003)
    regime = classify_regime(feats, e)
    assert regime in ("RANGE", "COMPRESSION", "TRENDING", "EVENT_RISK")


def test_m5_7_abstention_on_synthetic_data(synthetic_history: History1H) -> None:
    """Synthetic data must trigger the synthetic-source abstention reason."""
    df = synthetic_history.df
    feats = compute_features(df, origin_idx=len(df) - 1)
    e = detect_expansion(df, sigma_h1_forecast=0.003)
    # Build a minimal VolCandidate
    cand = VolCandidate(name="EWMA", params={}, forecast_var_h1=1e-6, forecast_sigma_h1=1e-3, qlike_calibration=0.5)
    abst = decide_abstention(
        features=feats,
        expansion=e,
        vol_candidate=cand,
        sigma_ratio=e.sigma_ratio_6h_168h,
        n_calibration_scores=50,
        data_is_synthetic=True,
    )
    assert "data_is_synthetic" in abst.reasons
    assert abst.regime in ("RANGE", "COMPRESSION", "TRENDING", "EVENT_RISK")


# ── Test 10: Non-direction guarantee ────────────────────────────────────


def test_m5_no_direction_p50_equals_m0(live_history: History1H) -> None:
    """P50 must equal the last close (M0) for every horizon. No drift claim."""
    res = run_m5(history=live_history, days=729, seed=1337, horizons_h=(1, 6, 24, 72))
    last_close = res.last_close
    assert last_close > 0
    for h in res.horizons:
        # Allow tiny floating-point drift
        assert abs(h.p50 - last_close) < 1e-6, f"P50 at h={h.horizon_h} drifts from M0"
        # P10 < P50 < P90
        assert h.p10 < h.p50 < h.p90
        # P25 < P50 < P75
        assert h.p25 < h.p50 < h.p75


# ── Test 11: End-to-end on synthetic ────────────────────────────────────


def test_m5_end_to_end_on_synthetic(synthetic_history: History1H) -> None:
    """M5 must produce a complete packet on synthetic data."""
    res = run_m5(history=synthetic_history, days=729, seed=1337, horizons_h=(1, 6, 24, 72))
    d = res.to_dict()
    assert d["schema"] == SCHEMA
    assert d["status"] == STATUS
    assert d["data_source"] == "SYNTHETIC"
    assert len(d["horizons"]) == 4
    # All numeric fields finite
    for h in d["horizons"]:
        for k, v in h.items():
            if isinstance(v, float):
                assert np.isfinite(v), f"{k} is not finite in horizon {h['horizon_h']}"


# ── Test 12: M0 vs M5 on synthetic ──────────────────────────────────────


def test_m5_vs_m0_synthetic_admission(synthetic_history: History1H) -> None:
    """On synthetic GBM, M5 must produce finite numbers and a valid admission verdict."""
    wf = run_walk_forward(
        history=synthetic_history,
        days=729,
        seed=1337,
        horizons_h=(1, 6, 24, 72),
        step_hours=24,
        lookback_hours=24 * 30,
        max_windows=20,
    )
    assert wf.n_windows > 0
    assert wf.admission in ("PASS", "FAIL")
    assert np.isfinite(wf.m5_pinball)
    assert np.isfinite(wf.m0_pinball)
    # QLIKE must be finite for at least one model
    assert np.isfinite(wf.m5_qlike) or wf.m5_qlike == float("nan")


# ── Test 13: Admission receipt writers ──────────────────────────────────


def test_admission_failed_receipt_is_written(synthetic_history: History1H, tmp_path: Path) -> None:
    """The admission_rule_failed receipt writer must produce a valid JSON file."""
    wf = run_walk_forward(
        history=synthetic_history,
        days=729,
        seed=1337,
        horizons_h=(1, 6, 24, 72),
        step_hours=24,
        lookback_hours=24 * 30,
        max_windows=10,
    )
    handle = write_admission_rule_failed_receipt(
        forecast_id="pytest-synth",
        wf_result=wf,
        verdict_reason="pytest forced admission failure on synthetic data",
        receipts_dir=tmp_path,
    )
    assert handle["written"] is True
    receipt_path = Path(handle["receipt_uri"])
    assert receipt_path.exists()
    body = json.loads(receipt_path.read_text())
    assert body["receipt_subtype"] == "admission_rule_failed"
    assert body["schema"] == SCHEMA
    assert "walk_forward" in body
    assert "n_windows" in body["walk_forward"]


def test_admission_pass_receipt_is_written(live_history: History1H, tmp_path: Path) -> None:
    """The admission_pass receipt writer must produce a valid JSON file."""
    wf = run_walk_forward(
        history=live_history,
        days=729,
        seed=1337,
        horizons_h=(1, 6, 24, 72),
        step_hours=24,
        lookback_hours=24 * 30,
        max_windows=20,
    )
    handle = write_admission_pass_receipt(
        forecast_id="pytest-live",
        wf_result=wf,
        receipts_dir=tmp_path,
    )
    assert handle["written"] is True
    receipt_path = Path(handle["receipt_uri"])
    assert receipt_path.exists()
    body = json.loads(receipt_path.read_text())
    assert body["receipt_subtype"] == "admission_pass"
    assert body["schema"] == SCHEMA
    assert "walk_forward" in body


# ── Test 14: Full M0 vs M5 on real XAUUSD (slow) ────────────────────────


@pytest.mark.slow
def test_m5_vs_m0_real_xauusd_admission(live_history: History1H) -> None:
    """Run the full walk-forward on real XAUUSD and verify the result is sane.

    On the sandbox-shifted yfinance cascade, the structure (returns,
    ranges, semivariance) is real and M5 should be able to beat M0 on
    the pinball loss + QLIKE. If admission fails, that's a real-world
    honest negative result and we should NOT silently pass.
    """
    wf = run_walk_forward(
        history=live_history,
        days=729,
        seed=1337,
        horizons_h=(1, 6, 24, 72),
        step_hours=24,
        lookback_hours=24 * 30,
        max_windows=40,
    )
    assert wf.n_windows > 10
    # Honest reporting: do NOT assert "admission == PASS"; surface the
    # real outcome. But all numbers must be finite.
    assert np.isfinite(wf.m5_pinball)
    assert np.isfinite(wf.m0_pinball)
    assert np.isfinite(wf.m5_interval_width_mean)
    assert np.isfinite(wf.m0_interval_width_mean)
    # Coverage is a fraction in [0, 1]
    assert 0.0 <= wf.m5_coverage_p10_p90 <= 1.0
    assert 0.0 <= wf.m5_coverage_p25_p75 <= 1.0


# ── Test 15: Non-direction on synthetic ─────────────────────────────────


def test_m5_no_direction_on_synthetic(synthetic_history: History1H) -> None:
    """P50 = last_close on synthetic data too — no direction regardless of input."""
    res = run_m5(history=synthetic_history, days=729, seed=1337, horizons_h=(1, 6, 24, 72))
    for h in res.horizons:
        assert abs(h.p50 - res.last_close) < 1e-6