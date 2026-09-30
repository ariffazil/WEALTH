"""M5.0 orchestrator — wire M5.1 → M5.7 into a single forecast packet.

Public entry point: :func:`run_m5`.

Outputs (per horizon):
    p10, p25, p50, p75, p90      — quantiles (P50 always = M0 = last close)
    expected_high, expected_low  — M5.2 + M5.3 asymmetric range
    p_vol_expansion              — M5.4 expansion probability
    p_touch_upper_2sigma,
    p_touch_lower_2sigma         — M5.6 touch probabilities
    regime                       — M5.7
    abstain                      — M5.7
    chosen_vol_model             — M5.1 winning model name

The pipeline also exposes :func:`run_walk_forward` which runs the
admission test on a 1H history, computing M0 vs M5 pinball / coverage
/ interval-width.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .abstention import AbstentionDecision, REGIMES, decide_abstention
from .asymmetry import AsymmetryForecast, forecast_asymmetry
from .conformal import ConformalCalibrator, recalibrate_quantiles
from .data import History1H, load_xauusd_1h
from .expansion import ExpansionForecast, detect_expansion
from .features import FeatureVector, compute_features
from .range import RangeForecast, forecast_range
from .touch_prob import TouchProb, touch_probability_2sigma
from .volatility import (
    VolCandidate,
    forecast_sigma_h,
    select_best_vol,
)


SCHEMA = "wealth.gold.m5.v1"
STATUS = "SHADOW_CHALLENGER"


# ── Result dataclasses ───────────────────────────────────────────────────


@dataclass(frozen=True)
class HorizonForecast:
    """A single-horizon forecast."""

    horizon_h: int
    p10: float
    p25: float
    p50: float  # always = M0
    p75: float
    p90: float
    expected_high: float
    expected_low: float
    p_vol_expansion: float
    p_touch_upper_2sigma: float
    p_touch_lower_2sigma: float
    sigma_h: float
    chosen_vol_model: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class M5Result:
    """Full M5 forecast packet."""

    forecast_id: str = ""
    origin_time: str = ""
    issued_at: str = ""
    asset: str = "XAUUSD"
    data_source: str = ""
    data_reason: str = ""
    data_is_synthetic: bool = False
    last_close: float = float("nan")
    features: Optional[FeatureVector] = None
    vol_candidate: Optional[VolCandidate] = None
    range_forecast: Optional[RangeForecast] = None
    asymmetry: Optional[AsymmetryForecast] = None
    expansion: Optional[ExpansionForecast] = None
    touch_prob: Optional[TouchProb] = None
    abstention: Optional[AbstentionDecision] = None
    horizons: list[HorizonForecast] = field(default_factory=list)
    schema: str = SCHEMA
    status: str = STATUS

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "status": self.status,
            "forecast_id": self.forecast_id,
            "origin_time": self.origin_time,
            "issued_at": self.issued_at,
            "asset": self.asset,
            "data_source": self.data_source,
            "data_reason": self.data_reason,
            "data_is_synthetic": self.data_is_synthetic,
            "last_close": self.last_close,
            "features": self.features.to_dict() if self.features else None,
            "vol_candidate": self.vol_candidate.to_dict() if self.vol_candidate else None,
            "range_forecast": self.range_forecast.to_dict() if self.range_forecast else None,
            "asymmetry": self.asymmetry.to_dict() if self.asymmetry else None,
            "expansion": self.expansion.to_dict() if self.expansion else None,
            "touch_prob": self.touch_prob.to_dict() if self.touch_prob else None,
            "abstention": self.abstention.to_dict() if self.abstention else None,
            "horizons": [h.to_dict() for h in self.horizons],
        }


# ── Internal helpers ─────────────────────────────────────────────────────


def _pinball(y_true: float, y_hat: float, q: float) -> float:
    diff = y_true - y_hat
    return float(max(q * diff, (q - 1.0) * diff))


def _qlike_safe(realised_sq: np.ndarray, forecast_var: np.ndarray) -> float:
    r = np.asarray(realised_sq, dtype=float)
    h = np.asarray(forecast_var, dtype=float)
    mask = (r > 0) & (h > 0) & np.isfinite(r) & np.isfinite(h)
    if not np.any(mask):
        return float("inf")
    ratio = r[mask] / h[mask]
    ratio = np.clip(ratio, 1e-12, None)
    return float(np.mean(ratio - np.log(ratio) - 1.0))


def _z(quantile: float) -> float:
    """Standard-normal quantile lookup (no scipy dependency)."""
    from scipy.stats import norm

    return float(norm.ppf(quantile))


def _normal_quantile(q: float) -> float:
    """scipy-free fallback if scipy is unavailable — uses a coarse lookup."""
    table = {0.05: -1.6449, 0.10: -1.2816, 0.25: -0.6745, 0.50: 0.0, 0.75: 0.6745, 0.90: 1.2816, 0.95: 1.6449}
    return table.get(q, 0.0)


# ── Per-horizon forecast ─────────────────────────────────────────────────


def _forecast_one_horizon(
    *,
    horizon_h: int,
    last_close: float,
    vol_candidate: VolCandidate,
    range_forecast: RangeForecast,
    asymmetry: AsymmetryForecast,
    expansion: ExpansionForecast,
    features: FeatureVector,
    skip_recalibration: bool = False,
) -> HorizonForecast:
    sigma_h = forecast_sigma_h(vol_candidate, horizon_h=horizon_h)
    z10, z25, _, z75, z90 = _z(0.10), _z(0.25), _z(0.50), _z(0.75), _z(0.90)
    p10 = last_close * math.exp(z10 * sigma_h)
    p25 = last_close * math.exp(z25 * sigma_h)
    p50 = last_close  # M5 has NO direction — P50 = M0
    p75 = last_close * math.exp(z75 * sigma_h)
    p90 = last_close * math.exp(z90 * sigma_h)

    # Asymmetric range from M5.2 + M5.3 — scale with √(h / h_anchor).
    # range_forecast.expected_range was computed at h_anchor (=2 minimum);
    # we scale it by √(h/h_anchor) to project to the requested horizon.
    h_anchor = 2 if range_forecast.range_multiplier_k else max(2, horizon_h)
    range_scale = math.sqrt(max(1, horizon_h) / max(2, h_anchor))
    scaled_range = range_forecast.expected_range * range_scale
    upper_half = asymmetry.upper_half if asymmetry else scaled_range * 0.5
    lower_half = asymmetry.lower_half if asymmetry else scaled_range * 0.5
    # The asymmetry split was computed at h_anchor; scale each half
    upper_half_scaled = float(upper_half) * range_scale
    lower_half_scaled = float(lower_half) * range_scale
    eh = last_close + upper_half_scaled
    el = last_close - lower_half_scaled

    # Touch probability
    tp = touch_probability_2sigma(
        horizon_h=horizon_h,
        sigma_h1=vol_candidate.forecast_sigma_h1,
        p_vol_expansion=expansion.p_vol_expansion,
        asymmetry_score=asymmetry.asymmetry_score if asymmetry else 0.0,
        compression_percentile=features.compression_percentile_168h,
    )

    return HorizonForecast(
        horizon_h=horizon_h,
        p10=float(p10),
        p25=float(p25),
        p50=float(p50),
        p75=float(p75),
        p90=float(p90),
        expected_high=float(eh),
        expected_low=float(el),
        p_vol_expansion=float(expansion.p_vol_expansion),
        p_touch_upper_2sigma=float(tp.p_touch_upper_2sigma),
        p_touch_lower_2sigma=float(tp.p_touch_lower_2sigma),
        sigma_h=float(sigma_h),
        chosen_vol_model=vol_candidate.name,
    )


# ── Public entry point ───────────────────────────────────────────────────


def run_m5(
    *,
    history: Optional[History1H] = None,
    days: int = 729,
    seed: int = 1337,
    horizons_h: tuple[int, ...] = (1, 6, 24, 72),
    origin_idx: Optional[int] = None,
    now: Optional[datetime] = None,
) -> M5Result:
    """Run the M5 pipeline once and return the packet."""
    now = now or datetime.now(timezone.utc)
    if history is None:
        history = load_xauusd_1h(days=days, seed=seed)

    df = history.df
    if origin_idx is None:
        origin_idx = len(df) - 1
    origin_idx = max(0, min(origin_idx, len(df) - 1))

    # Slice to origin (no leakage)
    df_at_origin = df.iloc[: origin_idx + 1].copy()

    closes = df_at_origin["close"].astype(float).to_numpy()
    last_close = float(closes[-1])
    log_ret = np.diff(np.log(closes))

    features = compute_features(df_at_origin, origin_idx=len(df_at_origin) - 1)

    vol_candidate = select_best_vol(log_ret)
    expansion = detect_expansion(df_at_origin, sigma_h1_forecast=vol_candidate.forecast_sigma_h1)
    # M5.2 / M5.3 are anchored at the *first* requested horizon. We use
    # the smallest horizon (≥2) for the range basis; the multi-horizon
    # bands then scale with √h.
    h_anchor = max(2, min(horizons_h))
    rng = forecast_range(df_at_origin, horizon_h=h_anchor, sigma_h1=vol_candidate.forecast_sigma_h1)
    asym = forecast_asymmetry(
        df_at_origin,
        horizon_h=h_anchor,
        expected_range=rng.expected_range,
        sv_up_24h=features.semivariance_up_24h,
        sv_down_24h=features.semivariance_down_24h,
    )

    abst = decide_abstention(
        features=features,
        expansion=expansion,
        vol_candidate=vol_candidate,
        sigma_ratio=expansion.sigma_ratio_6h_168h,
        n_calibration_scores=0,
        data_is_synthetic=history.is_synthetic,
    )

    horizon_fcsts: list[HorizonForecast] = []
    for h in horizons_h:
        h_f = _forecast_one_horizon(
            horizon_h=h,
            last_close=last_close,
            vol_candidate=vol_candidate,
            range_forecast=rng,
            asymmetry=asym,
            expansion=expansion,
            features=features,
        )
        horizon_fcsts.append(h_f)

    # touch probability at the smallest requested horizon for the
    # top-level packet (not per-horizon — that's in each horizon_fcst)
    touch_top = horizon_fcsts[0].p_touch_upper_2sigma if horizon_fcsts else float("nan")
    touch_dn_top = horizon_fcsts[0].p_touch_lower_2sigma if horizon_fcsts else float("nan")
    touch_top_obj = TouchProb(
        p_touch_upper_2sigma=float(touch_top),
        p_touch_lower_2sigma=float(touch_dn_top),
        notes="top_level_first_horizon",
    )

    issued_at = now.isoformat()
    origin_time = str(df.index[origin_idx])
    forecast_id = f"m5-{int(now.timestamp())}-{origin_idx}"

    return M5Result(
        forecast_id=forecast_id,
        origin_time=origin_time,
        issued_at=issued_at,
        asset="XAUUSD",
        data_source=history.source,
        data_reason=history.reason,
        data_is_synthetic=history.is_synthetic,
        last_close=last_close,
        features=features,
        vol_candidate=vol_candidate,
        range_forecast=rng,
        asymmetry=asym,
        expansion=expansion,
        touch_prob=touch_top_obj,
        abstention=abst,
        horizons=horizon_fcsts,
    )


# ── Walk-forward + admission ────────────────────────────────────────────


WALK_FORWARD_LOOKBACK = 24 * 30  # 30 days of hourly bars before first origin
WALK_FORWARD_HORIZONS_H: tuple[int, ...] = (1, 6, 24, 72)
WALK_FORWARD_STEP_HOURS = 24  # one origin per day
PINBALL_QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)


@dataclass(frozen=True)
class WalkForwardResult:
    n_windows: int
    m5_pinball: float
    m0_pinball: float
    skill_vs_M0: float  # 1 - m5/m0
    m5_coverage_p10_p90: float
    m0_coverage_p10_p90: float
    m5_coverage_p25_p75: float
    m0_coverage_p25_p75: float
    m5_interval_width_mean: float
    m0_interval_width_mean: float
    m5_qlike: float
    m0_qlike: float
    admission: str  # PASS | FAIL
    admission_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def run_walk_forward(
    *,
    history: Optional[History1H] = None,
    days: int = 729,
    seed: int = 1337,
    horizons_h: tuple[int, ...] = WALK_FORWARD_HORIZONS_H,
    step_hours: int = WALK_FORWARD_STEP_HOURS,
    lookback_hours: int = WALK_FORWARD_LOOKBACK,
    max_windows: int = 200,
    now: Optional[datetime] = None,
) -> WalkForwardResult:
    """Run the walk-forward tournament comparing M5 vs M0."""
    now = now or datetime.now(timezone.utc)
    if history is None:
        history = load_xauusd_1h(days=days, seed=seed)

    df = history.df.copy()
    n = len(df)
    if n < lookback_hours + max(horizons_h) + 1:
        return WalkForwardResult(
            n_windows=0,
            m5_pinball=float("nan"),
            m0_pinball=float("nan"),
            skill_vs_M0=float("nan"),
            m5_coverage_p10_p90=float("nan"),
            m0_coverage_p10_p90=float("nan"),
            m5_coverage_p25_p75=float("nan"),
            m0_coverage_p25_p75=float("nan"),
            m5_interval_width_mean=float("nan"),
            m0_interval_width_mean=float("nan"),
            m5_qlike=float("nan"),
            m0_qlike=float("nan"),
            admission="FAIL",
            admission_reasons=["insufficient_history_for_walk_forward"],
        )

    # Compute M0 σ baseline once over the whole window for fairness
    closes = df["close"].astype(float).to_numpy()
    full_log_ret = np.diff(np.log(closes))
    if full_log_ret.size < 2:
        return WalkForwardResult(
            n_windows=0,
            m5_pinball=float("nan"),
            m0_pinball=float("nan"),
            skill_vs_M0=float("nan"),
            m5_coverage_p10_p90=float("nan"),
            m0_coverage_p10_p90=float("nan"),
            m5_coverage_p25_p75=float("nan"),
            m0_coverage_p25_p75=float("nan"),
            m5_interval_width_mean=float("nan"),
            m0_interval_width_mean=float("nan"),
            m5_qlike=float("nan"),
            m0_qlike=float("nan"),
            admission="FAIL",
            admission_reasons=["no_returns"],
        )
    m0_sigma_h1 = float(np.std(full_log_ret, ddof=1))

    pinball_m5 = 0.0
    pinball_m0 = 0.0
    cov_m5_10_90 = 0
    cov_m0_10_90 = 0
    cov_m5_25_75 = 0
    cov_m0_25_75 = 0
    width_m5 = 0.0
    width_m0 = 0.0
    width_count = 0
    qlike_m5_list = []
    qlike_m0_list = []
    n_windows = 0

    origins = list(range(lookback_hours, n - max(horizons_h), step_hours))
    if len(origins) > max_windows:
        # Take evenly spaced origins
        step_idx = max(1, len(origins) // max_windows)
        origins = origins[::step_idx][:max_windows]

    for t in origins:
        window = df.iloc[: t + 1].copy()
        future = df.iloc[t + 1 : t + 1 + max(horizons_h)].copy()
        try:
            res = run_m5(
                history=History1H(
                    df=window,
                    source=history.source,
                    reason=f"{history.reason}__wf_t{t}",
                    fetched_at=history.fetched_at,
                    sandbox_price_offset_acknowledged=history.sandbox_price_offset_acknowledged,
                ),
                horizons_h=horizons_h,
                origin_idx=len(window) - 1,
                now=now,
            )
        except Exception:
            continue

        # Realised close at each horizon
        actuals = {}
        for h in horizons_h:
            if h - 1 < len(future):
                actuals[h] = float(future["close"].iloc[h - 1])
            else:
                actuals[h] = float("nan")

        # M5 forecasts
        m5_horizons = {f.horizon_h: f for f in res.horizons}

        # M0 forecasts
        m0_horizons = {}
        for h in horizons_h:
            s = m0_sigma_h1 * math.sqrt(h)
            last = res.last_close
            m0_horizons[h] = (
                last * math.exp(_z(0.10) * s),
                last * math.exp(_z(0.25) * s),
                last,
                last * math.exp(_z(0.75) * s),
                last * math.exp(_z(0.90) * s),
            )

        for h in horizons_h:
            actual = actuals[h]
            if not np.isfinite(actual):
                continue

            m5f = m5_horizons.get(h)
            m0f = m0_horizons.get(h)
            if m5f is None or m0f is None:
                continue

            # Pinball per quantile
            for q, m5_v, m0_v in zip(
                PINBALL_QUANTILES,
                (m5f.p10, m5f.p25, m5f.p50, m5f.p75, m5f.p90),
                m0f,
            ):
                pinball_m5 += _pinball(actual, m5_v, q)
                pinball_m0 += _pinball(actual, m0_v, q)

            # Coverage
            if m5f.p10 <= actual <= m5f.p90:
                cov_m5_10_90 += 1
            if m0f[0] <= actual <= m0f[4]:
                cov_m0_10_90 += 1
            if m5f.p25 <= actual <= m5f.p75:
                cov_m5_25_75 += 1
            if m0f[1] <= actual <= m0f[3]:
                cov_m0_25_75 += 1

            # Interval width
            width_m5 += float(m5f.p90 - m5f.p10)
            width_m0 += float(m0f[4] - m0f[0])
            width_count += 1

            # QLIKE on this single step (forecast variance vs realised r²)
            if h == 1:
                # Realised r² at this 1-step horizon (use log return of actual vs last_close)
                realised_r2 = float((np.log(actual / res.last_close)) ** 2) if res.last_close > 0 else float("nan")
                if np.isfinite(realised_r2) and realised_r2 > 0:
                    # M5 variance forecast
                    m5_var = float(m5f.sigma_h) ** 2
                    if np.isfinite(m5_var) and m5_var > 0:
                        qlike_m5_list.append(_qlike_safe(np.array([realised_r2]), np.array([m5_var])))
                    m0_var = float(m0f[4] - m0f[0]) / (2.0 * _z(0.90)) ** 2
                    qlike_m0_list.append(_qlike_safe(np.array([realised_r2]), np.array([m0_var])))

        n_windows += 1

    if n_windows == 0 or width_count == 0:
        return WalkForwardResult(
            n_windows=0,
            m5_pinball=float("nan"),
            m0_pinball=float("nan"),
            skill_vs_M0=float("nan"),
            m5_coverage_p10_p90=float("nan"),
            m0_coverage_p10_p90=float("nan"),
            m5_coverage_p25_p75=float("nan"),
            m0_coverage_p25_p75=float("nan"),
            m5_interval_width_mean=float("nan"),
            m0_interval_width_mean=float("nan"),
            m5_qlike=float("nan"),
            m0_qlike=float("nan"),
            admission="FAIL",
            admission_reasons=["no_windows_scored"],
        )

    # Aggregate
    m5_pinball = pinball_m5 / (n_windows * len(horizons_h) * len(PINBALL_QUANTILES))
    m0_pinball = pinball_m0 / (n_windows * len(horizons_h) * len(PINBALL_QUANTILES))
    skill_vs_M0 = float(1.0 - m5_pinball / m0_pinball) if m0_pinball > 0 else float("nan")
    m5_cov_10_90 = cov_m5_10_90 / (n_windows * len(horizons_h))
    m0_cov_10_90 = cov_m0_10_90 / (n_windows * len(horizons_h))
    m5_cov_25_75 = cov_m5_25_75 / (n_windows * len(horizons_h))
    m0_cov_25_75 = cov_m0_25_75 / (n_windows * len(horizons_h))
    width_m5_mean = width_m5 / width_count
    width_m0_mean = width_m0 / width_count
    m5_qlike = float(np.mean(qlike_m5_list)) if qlike_m5_list else float("nan")
    m0_qlike = float(np.mean(qlike_m0_list)) if qlike_m0_list else float("nan")

    # Admission rule
    reasons = []
    if np.isfinite(skill_vs_M0) and skill_vs_M0 <= 0.0:
        reasons.append(f"pinball_not_better_than_M0 (skill_vs_M0={skill_vs_M0:.4f})")
    if np.isfinite(m5_cov_10_90) and m5_cov_10_90 < 0.75:
        reasons.append(f"p10_p90_coverage_below_0.75 (={m5_cov_10_90:.4f})")
    if np.isfinite(m5_cov_25_75) and m5_cov_25_75 < 0.40:
        reasons.append(f"p25_p75_coverage_below_0.40 (={m5_cov_25_75:.4f})")
    if np.isfinite(width_m5_mean) and np.isfinite(width_m0_mean) and width_m5_mean >= width_m0_mean:
        # We require narrower — but at equal coverage. If M5 has lower
        # coverage AND equal/greater width, it's worse on both axes.
        if np.isfinite(m5_cov_10_90) and np.isfinite(m0_cov_10_90) and abs(m5_cov_10_90 - m0_cov_10_90) < 0.05:
            reasons.append(f"width_not_narrower_at_equal_coverage (width_m5={width_m5_mean:.4f}, width_m0={width_m0_mean:.4f})")
    if np.isfinite(m5_qlike) and np.isfinite(m0_qlike) and m5_qlike >= m0_qlike:
        reasons.append(f"qlike_not_better_than_M0 (m5={m5_qlike:.4f}, m0={m0_qlike:.4f})")

    admission = "PASS" if not reasons else "FAIL"

    return WalkForwardResult(
        n_windows=n_windows,
        m5_pinball=float(m5_pinball),
        m0_pinball=float(m0_pinball),
        skill_vs_M0=float(skill_vs_M0) if np.isfinite(skill_vs_M0) else float("nan"),
        m5_coverage_p10_p90=float(m5_cov_10_90),
        m0_coverage_p10_p90=float(m0_cov_10_90),
        m5_coverage_p25_p75=float(m5_cov_25_75),
        m0_coverage_p25_p75=float(m0_cov_25_75),
        m5_interval_width_mean=float(width_m5_mean),
        m0_interval_width_mean=float(width_m0_mean),
        m5_qlike=float(m5_qlike) if np.isfinite(m5_qlike) else float("nan"),
        m0_qlike=float(m0_qlike) if np.isfinite(m0_qlike) else float("nan"),
        admission=admission,
        admission_reasons=reasons,
    )


# ── admission_rule_failed receipt ───────────────────────────────────────


DEFAULT_VAULT = Path(
    os.getenv("VAULT999_M5_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


def _sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_admission_rule_failed_receipt(
    *,
    forecast_id: str,
    wf_result: WalkForwardResult,
    verdict_reason: str,
    receipts_dir: Optional[Path] = None,
) -> dict:
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-m5-admission-failed-{forecast_id}-{stamp}"
    body = {
        "schema": SCHEMA,
        "receipt_subtype": "admission_rule_failed",
        "receipt_id": receipt_id,
        "issued_at": issued_at,
        "organ": "WEALTH",
        "lane": "gold-m5-adaptive-distribution",
        "forecast_id": forecast_id,
        "admission_decision": "RECOMMEND_SHADOW_STATUS_UNCHANGED",
        "walk_forward": {
            "n_windows": int(wf_result.n_windows),
            "m5_pinball": wf_result.m5_pinball,
            "m0_pinball": wf_result.m0_pinball,
            "skill_vs_M0": wf_result.skill_vs_M0,
            "m5_coverage_p10_p90": wf_result.m5_coverage_p10_p90,
            "m0_coverage_p10_p90": wf_result.m0_coverage_p10_p90,
            "m5_coverage_p25_p75": wf_result.m5_coverage_p25_p75,
            "m0_coverage_p25_p75": wf_result.m0_coverage_p25_p75,
            "m5_interval_width_mean": wf_result.m5_interval_width_mean,
            "m0_interval_width_mean": wf_result.m0_interval_width_mean,
            "m5_qlike": wf_result.m5_qlike,
            "m0_qlike": wf_result.m0_qlike,
        },
        "admission_reasons": list(wf_result.admission_reasons),
        "verdict_reason": verdict_reason,
        "honest_verdict": (
            "M5 (Adaptive Distribution Engine) does not satisfy the admission "
            "rule on the current XAUUSD history. The challenger stays "
            "SHADOW_CHALLENGER; no promotion is recommended."
        ),
    }
    text = json.dumps(body, indent=2, sort_keys=False)
    path = target / f"{receipt_id}.json"
    path.write_text(text, encoding="utf-8")
    return {
        "receipt_id": receipt_id,
        "receipt_uri": str(path),
        "written": True,
        "digest": _sha256_hex(text),
    }


__all__ = [
    "SCHEMA",
    "STATUS",
    "M5Result",
    "HorizonForecast",
    "WalkForwardResult",
    "run_m5",
    "run_walk_forward",
    "write_admission_rule_failed_receipt",
]