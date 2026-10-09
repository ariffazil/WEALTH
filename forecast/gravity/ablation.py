"""555-ABLATION — M0/M1/M2/M3/M4 walk-forward tournament.

Models
======

* **M0** — random-walk baseline. P50 = last close; bands = ±1.282 σ·√h.
* **M1** — price-only baseline (no gravity, no wave). Uses log-linear
           trend extrapolation + the same M0 σ floor.
* **M2** — sparse gravity baseline. Uses DFII10 + USD slope only; the
           "original" gravity model with two features.
* **M3** — wave-only baseline from :mod:`wave_forge` (no gravity).
           Re-runs the challenger pipeline but does NOT consult the
           gravity features.
* **M4** — full challenger: wave + gravity. The cone is built by mixing
           the wave path with the regime-conditional cone from the
           444-DISTRIBUTION.

Walk-forward harness
====================

For every origin day ``t`` in ``[train_end, total - horizon]``:

  1. Build a window ending at ``t``.
  2. Compute each model's P10/P50/P90 at horizon ``h ∈ {24, 48, 72}``.
  3. Score against the realised close at ``t + h``.
  4. Accumulate pinball loss per model per quantile.
  5. Coverage = fraction of realised closes inside [P10, P90].

Skill score = ``1 - (model_pinball / M0_pinball)``. Positive ⇒ beats M0.

Admission rule
==============

M4 must beat M0, M1, M2, AND M3 on walk-forward pinball to be promoted
out of ``SHADOW_CHALLENGER``. If any of these is not satisfied, we
write an ``admission_rule_failed`` receipt and recommend ``SHADOW``.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import numpy as np


WALK_FORWARD_LOOKBACK = 365
WALK_FORWARD_HORIZONS_H: tuple[int, ...] = (24, 48, 72)
WALK_FORWARD_STEP_DAYS = 30
PINBALL_QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)

# Promotion floor: skill vs baseline must be strictly > 0.
PROMOTION_SKILL_FLOOR = 0.0

# Trend window used by M1 (price-only baseline).
TREND_WINDOW = 30


@dataclass(frozen=True)
class ModelSkillRow:
    """One row of the ablation table."""

    name: str
    pinball: float
    pinball_skill_vs_M0: float
    pinball_skill_vs_M1: float
    pinball_skill_vs_M2: float
    pinball_skill_vs_M3: float
    coverage_p10_p90: float
    bias_p50: float
    n_windows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pinball": round(self.pinball, 4),
            "pinball_skill_vs_M0": round(self.pinball_skill_vs_M0, 4),
            "pinball_skill_vs_M1": round(self.pinball_skill_vs_M1, 4),
            "pinball_skill_vs_M2": round(self.pinball_skill_vs_M2, 4),
            "pinball_skill_vs_M3": round(self.pinball_skill_vs_M3, 4),
            "coverage_p10_p90": round(self.coverage_p10_p90, 4),
            "bias_p50": round(self.bias_p50, 6),
            "n_windows": self.n_windows,
        }


@dataclass(frozen=True)
class AblationTable:
    """The full tournament result."""

    rows: list[ModelSkillRow]
    M4_promoted: bool
    reasons: list[str]
    observed_at: str
    n_windows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "M4_promoted": bool(self.M4_promoted),
            "reasons": list(self.reasons),
            "observed_at": self.observed_at,
            "n_windows": self.n_windows,
            "rows": [r.to_dict() for r in self.rows],
        }


# ── Pinball loss ────────────────────────────────────────────────────────


def _pinball(y_true: float, y_hat: float, q: float) -> float:
    diff = y_true - y_hat
    return float(max(q * diff, (q - 1.0) * diff))


# ── Per-model forecast helpers ──────────────────────────────────────────


def _m0_forecast(closes: np.ndarray, horizons_h: tuple[int, ...]) -> dict:
    """M0 — random walk. P50 = last close; bands = ±1.282 σ·√h."""
    if closes.size < 2:
        return {}
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    out: dict[int, tuple[float, float, float, float, float]] = {}
    for h in horizons_h:
        s = sigma * np.sqrt(h)
        out[h] = (
            last * np.exp(-1.282 * s),
            last * np.exp(-0.674 * s),
            last,
            last * np.exp(0.674 * s),
            last * np.exp(1.282 * s),
        )
    return out


def _m1_forecast(closes: np.ndarray, horizons_h: tuple[int, ...]) -> dict:
    """M1 — price-only baseline. Trend + M0 σ floor."""
    if closes.size < TREND_WINDOW + 1:
        return _m0_forecast(closes, horizons_h)
    win = closes[-TREND_WINDOW:]
    log_close = np.log(win)
    slope_per_day = float((log_close[-1] - log_close[0]) / (len(win) - 1))
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    out: dict[int, tuple[float, float, float, float, float]] = {}
    for h in horizons_h:
        days = h / 24.0
        median = last * np.exp(slope_per_day * days)
        s = sigma * np.sqrt(h)
        out[h] = (
            median * np.exp(-1.282 * s),
            median * np.exp(-0.674 * s),
            median,
            median * np.exp(0.674 * s),
            median * np.exp(1.282 * s),
        )
    return out


def _m2_forecast(
    closes: np.ndarray,
    horizons_h: tuple[int, ...],
    *,
    gravity_points: Optional[list[tuple[datetime, float, float]]] = None,
) -> dict:
    """M2 — sparse gravity baseline.

    Uses (real_yield, USD) slopes only, mapped to a directional shift
    on the median; bands are M0's bands (M2 has no distribution of its
    own — it is the *sparse* gravity model).

    ``gravity_points`` is a list of (timestamp, real_yield_pct_change,
    usd_pct_change) at the *origin*. When omitted, M2 falls back to a
    flat-bias default.
    """
    if closes.size < TREND_WINDOW + 1:
        return _m0_forecast(closes, horizons_h)
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01

    # Default: flat bias.
    bias_per_24h = 0.0
    if gravity_points:
        _, ry_pct, usd_pct = gravity_points[-1]
        # Falling real yield → bullish gold; rising USD → bearish gold.
        bias_per_24h = float(-ry_pct * 0.20 + (-usd_pct) * 0.20)
        bias_per_24h = max(-0.005, min(0.005, bias_per_24h))

    out: dict[int, tuple[float, float, float, float, float]] = {}
    for h in horizons_h:
        days = h / 24.0
        median = last * (1.0 + bias_per_24h * days)
        s = sigma * np.sqrt(h)
        out[h] = (
            median * np.exp(-1.282 * s),
            median * np.exp(-0.674 * s),
            median,
            median * np.exp(0.674 * s),
            median * np.exp(1.282 * s),
        )
    return out


def _m3_forecast(
    closes: np.ndarray,
    horizons_h: tuple[int, ...],
    *,
    m4_wave_predictor: Optional[Callable[..., dict]] = None,
    seed: int = 1337,
) -> dict:
    """M3 — wave-only baseline (no gravity).

    Delegates to the supplied ``m4_wave_predictor`` if given; otherwise
    falls back to M1 (so M3 has *something* to score). The wave-forge
    pipeline provides the predictor when running on real history.
    """
    if m4_wave_predictor is None:
        return _m1_forecast(closes, horizons_h)
    try:
        return m4_wave_predictor(closes, horizons_h=horizons_h, seed=seed)
    except Exception:
        return _m1_forecast(closes, horizons_h)


def _m4_forecast(
    closes: np.ndarray,
    horizons_h: tuple[int, ...],
    *,
    m4_wave_predictor: Optional[Callable[..., dict]] = None,
    gravity_points: Optional[list[tuple[datetime, float, float]]] = None,
    sigma_override: Optional[float] = None,
    seed: int = 1337,
) -> dict:
    """M4 — full challenger: wave + gravity.

    The cone is a *mix* of M3's wave path and the regime-conditional
    cone from 444-DISTRIBUTION. We approximate the regime cone here
    using the simple gravity mapping (real_yield + USD slopes) so the
    tournament stays self-contained; the full gravity path lives in
    :mod:`gravity.distribution`.
    """
    if closes.size < TREND_WINDOW + 1:
        return _m0_forecast(closes, horizons_h)
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma_raw = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    sigma = sigma_override if sigma_override is not None else sigma_raw

    # Regime conditional: combine wave path's median shift with the
    # gravity-implied bias.
    if m4_wave_predictor is not None:
        try:
            wave = m4_wave_predictor(closes, horizons_h=horizons_h, seed=seed)
        except Exception:
            wave = _m1_forecast(closes, horizons_h)
    else:
        wave = _m1_forecast(closes, horizons_h)

    # Gravity bias — same as M2 but capped and added to the wave median.
    gravity_bias_per_24h = 0.0
    if gravity_points:
        _, ry_pct, usd_pct = gravity_points[-1]
        gravity_bias_per_24h = float(-ry_pct * 0.30 + (-usd_pct) * 0.30)
        gravity_bias_per_24h = max(-0.007, min(0.007, gravity_bias_per_24h))

    out: dict[int, tuple[float, float, float, float, float]] = {}
    for h in horizons_h:
        days = h / 24.0
        # Pull the wave path's median if present; otherwise trend.
        wave_h = wave.get(h)
        if wave_h is not None:
            wave_median = float(wave_h[2])
            # Mix wave sigma (band-derived) with M0 sigma.
            wave_p10, wave_p90 = float(wave_h[0]), float(wave_h[4])
            wave_sigma = (math.log(wave_p90 / wave_median) / 1.282) if wave_median > 0 else sigma
            mixed_sigma = 0.6 * wave_sigma + 0.4 * sigma
        else:
            wave_median = last
            mixed_sigma = sigma
        median = wave_median * (1.0 + gravity_bias_per_24h * days)
        s = mixed_sigma * math.sqrt(h)
        out[h] = (
            median * math.exp(-1.282 * s),
            median * math.exp(-0.674 * s),
            median,
            median * math.exp(0.674 * s),
            median * math.exp(1.282 * s),
        )
    return out


import math  # placed after the helpers so the math import is local; safe.


# ── Walk-forward scoring ────────────────────────────────────────────────


def _walk_forward_score(
    history_close: np.ndarray,
    *,
    predictor: Callable[..., dict],
    lookback: int = WALK_FORWARD_LOOKBACK,
    horizons_h: tuple[int, ...] = WALK_FORWARD_HORIZONS_H,
    step_days: int = WALK_FORWARD_STEP_DAYS,
    predictor_kwargs: Optional[dict] = None,
) -> tuple[float, float, float, int]:
    """Run the walk-forward and return (mean_pinball, coverage, bias_p50, n_windows)."""
    n = len(history_close)
    if n < lookback + max(horizons_h) // 24 + 1:
        return 0.0, 0.0, 0.0, 0
    pinball_total = 0.0
    pinball_n = 0
    coverage_hits = 0
    coverage_total = 0
    biases: list[float] = []

    pkwargs = predictor_kwargs or {}

    for t in range(lookback, n - max(horizons_h) // 24, step_days):
        window = history_close[: t + 1]
        # Anchor the predictor's "now" at the window's last timestamp.
        # Use a UTC-aligned midnight so downstream code accepts it.
        anchor_iso = (datetime.now(timezone.utc) - timedelta(days=n - t - 1)).isoformat()
        actuals = {
            h: float(history_close[t + h // 24])
            if (t + h // 24) < n else float("nan")
            for h in horizons_h
        }
        if any(np.isnan(v) for v in actuals.values()):
            continue
        try:
            forecast = predictor(window, horizons_h=horizons_h, **pkwargs)
        except Exception:
            continue
        if not forecast:
            continue
        for h in horizons_h:
            if h not in forecast:
                continue
            p10, p25, p50, p75, p90 = forecast[h]
            actual = actuals[h]
            for q, yhat in zip(PINBALL_QUANTILES, (p10, p25, p50, p75, p90)):
                pinball_total += _pinball(actual, yhat, q)
                pinball_n += 1
            if p10 <= actual <= p90:
                coverage_hits += 1
            coverage_total += 1
            if h == 24 and p50 > 0:
                biases.append((p50 - actual) / actual)
    if pinball_n == 0:
        return 0.0, 0.0, 0.0, 0
    mean_pinball = pinball_total / pinball_n
    coverage = coverage_hits / max(coverage_total, 1)
    bias_p50 = float(np.mean(biases)) if biases else 0.0
    n_origins = (n - lookback - max(horizons_h) // 24) // step_days
    return mean_pinball, coverage, bias_p50, n_origins


from datetime import timedelta  # noqa: E402  (re-export import)


# ── Public agent ────────────────────────────────────────────────────────


def run_ablation_tournament(
    *,
    history: np.ndarray,
    m4_wave_predictor: Optional[Callable[..., dict]] = None,
    gravity_points: Optional[list[tuple[datetime, float, float]]] = None,
    seed: int = 1337,
    now: Optional[datetime] = None,
) -> AblationTable:
    """Run the M0/M1/M2/M3/M4 walk-forward tournament.

    Returns the ablation table with per-model pinball, coverage, bias
    and skill scores against every other model. M4 promotion is decided
    against ``PROMOTION_SKILL_FLOOR`` (strict > 0 against M0/M1/M2/M3).
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    closes = np.asarray(history, dtype=float)
    closes = closes[~np.isnan(closes)]
    if closes.size < WALK_FORWARD_LOOKBACK + max(WALK_FORWARD_HORIZONS_H) // 24 + 1:
        return AblationTable(
            rows=[],
            M4_promoted=False,
            reasons=["insufficient_history"],
            observed_at=observed_at,
            n_windows=0,
        )

    m0_pb, m0_cov, _, n_win = _walk_forward_score(closes, predictor=_m0_forecast)
    m1_pb, m1_cov, _, _ = _walk_forward_score(closes, predictor=_m1_forecast)
    m2_pb, m2_cov, _, _ = _walk_forward_score(
        closes,
        predictor=_m2_forecast,
        predictor_kwargs={"gravity_points": gravity_points},
    )
    m3_pb, m3_cov, _, _ = _walk_forward_score(
        closes,
        predictor=_m3_forecast,
        predictor_kwargs={"m4_wave_predictor": m4_wave_predictor, "seed": seed},
    )
    m4_pb, m4_cov, m4_bias, _ = _walk_forward_score(
        closes,
        predictor=_m4_forecast,
        predictor_kwargs={
            "m4_wave_predictor": m4_wave_predictor,
            "gravity_points": gravity_points,
            "seed": seed,
        },
    )

    def _skill(model_pb: float, baseline_pb: float) -> float:
        if baseline_pb <= 0:
            return 0.0
        return 1.0 - (model_pb / baseline_pb)

    # Per-model rows.
    rows = [
        ModelSkillRow(
            name="M0_random_walk",
            pinball=m0_pb,
            pinball_skill_vs_M0=0.0,
            pinball_skill_vs_M1=_skill(m0_pb, m1_pb),
            pinball_skill_vs_M2=_skill(m0_pb, m2_pb),
            pinball_skill_vs_M3=_skill(m0_pb, m3_pb),
            coverage_p10_p90=m0_cov,
            bias_p50=0.0,
            n_windows=n_win,
        ),
        ModelSkillRow(
            name="M1_price_only",
            pinball=m1_pb,
            pinball_skill_vs_M0=_skill(m1_pb, m0_pb),
            pinball_skill_vs_M1=0.0,
            pinball_skill_vs_M2=_skill(m1_pb, m2_pb),
            pinball_skill_vs_M3=_skill(m1_pb, m3_pb),
            coverage_p10_p90=m1_cov,
            bias_p50=0.0,
            n_windows=n_win,
        ),
        ModelSkillRow(
            name="M2_sparse_gravity",
            pinball=m2_pb,
            pinball_skill_vs_M0=_skill(m2_pb, m0_pb),
            pinball_skill_vs_M1=_skill(m2_pb, m1_pb),
            pinball_skill_vs_M2=0.0,
            pinball_skill_vs_M3=_skill(m2_pb, m3_pb),
            coverage_p10_p90=m2_cov,
            bias_p50=0.0,
            n_windows=n_win,
        ),
        ModelSkillRow(
            name="M3_wave_only",
            pinball=m3_pb,
            pinball_skill_vs_M0=_skill(m3_pb, m0_pb),
            pinball_skill_vs_M1=_skill(m3_pb, m1_pb),
            pinball_skill_vs_M2=_skill(m3_pb, m2_pb),
            pinball_skill_vs_M3=0.0,
            coverage_p10_p90=m3_cov,
            bias_p50=0.0,
            n_windows=n_win,
        ),
        ModelSkillRow(
            name="M4_wave_plus_gravity",
            pinball=m4_pb,
            pinball_skill_vs_M0=_skill(m4_pb, m0_pb),
            pinball_skill_vs_M1=_skill(m4_pb, m1_pb),
            pinball_skill_vs_M2=_skill(m4_pb, m2_pb),
            pinball_skill_vs_M3=_skill(m4_pb, m3_pb),
            coverage_p10_p90=m4_cov,
            bias_p50=m4_bias,
            n_windows=n_win,
        ),
    ]

    # Promotion rule: M4 must beat every baseline.
    s_vs_m0 = _skill(m4_pb, m0_pb)
    s_vs_m1 = _skill(m4_pb, m1_pb)
    s_vs_m2 = _skill(m4_pb, m2_pb)
    s_vs_m3 = _skill(m4_pb, m3_pb)

    reasons: list[str] = []
    if s_vs_m0 <= PROMOTION_SKILL_FLOOR:
        reasons.append(f"M4_NOT_BEATING_M0:skill={s_vs_m0:.4f}")
    if s_vs_m1 <= PROMOTION_SKILL_FLOOR:
        reasons.append(f"M4_NOT_BEATING_M1:skill={s_vs_m1:.4f}")
    if s_vs_m2 <= PROMOTION_SKILL_FLOOR:
        reasons.append(f"M4_NOT_BEATING_M2:skill={s_vs_m2:.4f}")
    if s_vs_m3 <= PROMOTION_SKILL_FLOOR:
        reasons.append(f"M4_NOT_BEATING_M3:skill={s_vs_m3:.4f}")
    promoted = len(reasons) == 0
    if promoted:
        reasons = ["ALL_ADMISSION_GATES_PASSED"]

    return AblationTable(
        rows=rows,
        M4_promoted=promoted,
        reasons=reasons,
        observed_at=observed_at,
        n_windows=n_win,
    )


__all__ = [
    "WALK_FORWARD_LOOKBACK",
    "WALK_FORWARD_HORIZONS_H",
    "WALK_FORWARD_STEP_DAYS",
    "PINBALL_QUANTILES",
    "PROMOTION_SKILL_FLOOR",
    "ModelSkillRow",
    "AblationTable",
    "run_ablation_tournament",
]
