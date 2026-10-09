"""M5 — Adaptive Distribution Engine for XAUUSD.

Status: SHADOW_CHALLENGER.

M5 is NOT a directional oracle. Its only job is to predict the QUALITY
of the future *distribution* of returns around the M0 random-walk center:

    M5.0 — orchestrator: center = M0 (last close), features -> distribution
    M5.1 — conditional volatility: EWMA + HAR + GARCH-T candidates (best by QLIKE)
    M5.2 — future high-low range forecast
    M5.3 — upside vs downside asymmetry via semivariance
    M5.4 — volatility expansion detection (CUSUM-like)
    M5.5 — conformal recalibration layer
    M5.6 — touch probability for ±2σ levels
    M5.7 — abstention gate

Inputs are STRICTLY price-derived: 1H log returns, high-low range, ATR,
realized vol at 6H/24H/72H/168H windows, semivariance, vol-of-vol, gap
indicators, trend efficiency, compression percentile, hour-of-day, EMA
distance. NO wave phase, NO news sentiment, NO gravity.

Outputs (per horizon h):
    p10, p25, p50, p75, p90 — P50 always = M0 (last close * 1)
    expected_high, expected_low — M5.2 range
    p_upside_asym, p_downside_asym — M5.3 asymmetry in [-1, 1]
    p_vol_expansion — M5.4 expansion probability in [0, 1]
    p_touch_upper_2sigma, p_touch_lower_2sigma — M5.6
    regime ∈ {RANGE, COMPRESSION, TRENDING, EVENT_RISK} — M5.7
    abstain ∈ {True, False} — M5.7

Public entry point: :func:`run_m5`.

Laws binding this module
------------------------
* NO DIRECTION — M5 emits no directional forecast. P50 is always M0.
* NO FAKE DATA — every input comes from a live price cascade; provenance
  is stamped on every artifact.
* UNCERTAINTY SURVIVES — QLIKE, coverage and pinball are reported even
  when admission fails; we do not silently drop bad news.
* Honest verdict — if admission fails, write the admission_rule_failed
  receipt and recommend SHADOW.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from .features import FeatureVector, compute_features
from .volatility import (
    VolCandidate,
    fit_ewma,
    fit_har,
    fit_garch_t,
    qlike_loss,
    select_best_vol,
    forecast_sigma_h,
)
from .range import forecast_range
from .asymmetry import forecast_asymmetry
from .expansion import detect_expansion
from .conformal import ConformalCalibrator, recalibrate_quantiles
from .touch_prob import touch_probability_2sigma
from .abstention import AbstentionDecision, decide_abstention
from .engine import (
    M5Result,
    SCHEMA,
    STATUS,
    run_m5,
    run_walk_forward,
    write_admission_rule_failed_receipt,
)
from .receipts import write_admission_pass_receipt

__all__ = [
    "SCHEMA",
    "STATUS",
    "FeatureVector",
    "compute_features",
    "VolCandidate",
    "fit_ewma",
    "fit_har",
    "fit_garch_t",
    "qlike_loss",
    "select_best_vol",
    "forecast_sigma_h",
    "forecast_range",
    "forecast_asymmetry",
    "detect_expansion",
    "ConformalCalibrator",
    "recalibrate_quantiles",
    "touch_probability_2sigma",
    "AbstentionDecision",
    "decide_abstention",
    "M5Result",
    "run_m5",
    "run_walk_forward",
    "write_admission_rule_failed_receipt",
    "write_admission_pass_receipt",
]