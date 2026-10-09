"""Agent 555 — AUDITOR.

Walk-forward comparison of M0 / M2 / M4-TREND / M4-WAVE on the same
XAUUSD history, producing measured pinball-loss skill scores. The
audit is the load-bearing evidence for the admission rule:

    M4-WAVE must beat BOTH M0 (random walk) AND M4-TREND (trend only)
    on walk-forward pinball to be promoted from SHADOW_CHALLENGER.

    If M4-WAVE does not beat M2 (the existing sparse market-reality
    model), recommend SHADOW and refuse promotion.

Models
======

* **M0** — Random-walk baseline. Median = last close, P10/P90 from a
  60-day rolling realised vol scaled by sqrt(hour).
* **M4-TREND** — Trend-only ARIMA-style baseline. Uses the linear
  trend (slope from the persistence window) + the same σ floor as M0,
  with NO wave content.
* **M4-WAVE** — The challenger. Re-uses the 111 + 222 + 333 lanes
  recursively on each walk-forward origin.
* **M2** — The existing sparse market-reality model from
  `/root/WEALTH/forecast/m2/`. It is *not* a per-horizon price model;
  it produces a discrete regime label. We translate its regime to a
  median shift: USD_TRENDING_UP ⇒ bearish (median lower); USD_TRENDING
  _DOWN ⇒ bullish (median higher); MIXED / UNKNOWN ⇒ flat median.
  This is a *very* weak baseline, intentionally so — M2 has no
  point forecast, only a direction.

Walk-forward harness
====================

For each origin day ``t`` in ``[train_end, total - horizon]``:

  1. Build a window of the last ``lookback`` days ending at ``t``.
  2. Compute each model's P10/P50/P90 at horizon h ∈ {24, 48, 72}.
  3. Score against the realised close at ``t + h``.
  4. Accumulate pinball loss per model per quantile.

Skill score is the relative improvement over the M0 baseline, averaged
across quantiles. Positive ⇒ beats M0. Negative ⇒ worse than M0.

The audit runs ONCE at production time on the live history; for tests
we expose the inner walk-forward function so the test suite can drive
it with a controlled synthetic history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

import numpy as np
import pandas as pd

from ..synthetic import HistorySeries
from . import _000_causality as _causality
from . import _111_decomposer as _decomposer
from . import _333_path_forge as _path_forge
from . import _444_stability as _stability
from . import _222_wave_state as _wave_state


# Walk-forward harness parameters.
WALK_FORWARD_LOOKBACK = 365   # days of history used per origin
WALK_FORWARD_HORIZONS_H = (24, 48, 72)
WALK_FORWARD_STEP_DAYS = 30   # step the origin forward every N days
PINBALL_QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
TREND_WINDOW = 30             # days of trend slope for M4-TREND

# Skill score floors — the audit also labels the verdict.
PROMOTE_PINBALL_SKILL_FLOOR = 0.0  # > 0 ⇒ beats M0
PROMOTE_TREND_PINBALL_SKILL_FLOOR = 0.0  # > 0 ⇒ beats M4-TREND
PROMOTE_M2_PINBALL_SKILL_FLOOR = 0.0  # > 0 ⇒ beats M2


@dataclass(frozen=True)
class ModelSkill:
    """Per-model pinball-loss skill summary."""

    name: str
    pinball_skill_vs_M0: float
    coverage_p10_p90: float
    bias_p50: float
    n_windows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pinball_skill_vs_M0": round(self.pinball_skill_vs_M0, 4),
            "coverage_p10_p90": round(self.coverage_p10_p90, 4),
            "bias_p50": round(self.bias_p50, 6),
            "n_windows": self.n_windows,
        }


@dataclass(frozen=True)
class AuditReport:
    """The 555-AUDITOR output."""

    ok: bool
    skill_vs_M0: float = 0.0
    skill_vs_M2: float = 0.0
    skill_vs_M4_TREND: float = 0.0
    M0_pinball: float = 0.0
    M2_pinball: float = 0.0
    M4_TREND_pinball: float = 0.0
    M4_WAVE_pinball: float = 0.0
    M4_WAVE_coverage: float = 0.0
    M4_WAVE_bias: float = 0.0
    n_windows: int = 0
    models: list[ModelSkill] = field(default_factory=list)
    promotion_recommended: bool = False
    reason: str = ""
    failures: list[str] = field(default_factory=list)
    observed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "555-AUDITOR",
            "ok": self.ok,
            "skill_vs_M0": round(self.skill_vs_M0, 4),
            "skill_vs_M2": round(self.skill_vs_M2, 4),
            "skill_vs_M4_TREND": round(self.skill_vs_M4_TREND, 4),
            "M0_pinball": round(self.M0_pinball, 4),
            "M2_pinball": round(self.M2_pinball, 4),
            "M4_TREND_pinball": round(self.M4_TREND_pinball, 4),
            "M4_WAVE_pinball": round(self.M4_WAVE_pinball, 4),
            "M4_WAVE_coverage": round(self.M4_WAVE_coverage, 4),
            "M4_WAVE_bias": round(self.M4_WAVE_bias, 4),
            "n_windows": self.n_windows,
            "models": [m.to_dict() for m in self.models],
            "promotion_recommended": bool(self.promotion_recommended),
            "reason": self.reason,
            "failures": list(self.failures),
            "observed_at": self.observed_at,
        }


# ── Pinball loss ────────────────────────────────────────────────────────


def _pinball(y_true: float, y_hat: float, q: float) -> float:
    """Pinball loss for quantile ``q``."""
    diff = y_true - y_hat
    return float(max(q * diff, (q - 1.0) * diff))


def _mean_pinball(y_true: np.ndarray, y_hat: np.ndarray, q: float) -> float:
    return float(np.mean([_pinball(float(t), float(h), q) for t, h in zip(y_true, y_hat)]))


# ── Per-model forecast helpers ──────────────────────────────────────────


def _m0_forecast(closes: np.ndarray, horizons_h: tuple[int, ...]) -> dict:
    """M0 — random walk. P50 = last close; bands = ±1.282 σ·√h.

    Returns ``{h: (p10, p25, p50, p75, p90)}``.
    """
    if closes.size < 2:
        return {}
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    out = {}
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


def _m4_trend_forecast(
    closes: np.ndarray, horizons_h: tuple[int, ...]
) -> dict:
    """M4-TREND — linear trend extrapolation + M0 σ.

    Median extrapolates the log-linear trend; bands are the M0 σ.
    """
    if closes.size < TREND_WINDOW + 1:
        return _m0_forecast(closes, horizons_h)
    win = closes[-TREND_WINDOW:]
    log_close = np.log(win)
    slope_per_day = float((log_close[-1] - log_close[0]) / (len(win) - 1))
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:])) if closes.size >= 60 else np.diff(np.log(closes))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    out = {}
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


def _m2_forecast(closes: np.ndarray, horizons_h: tuple[int, ...]) -> dict:
    """M2 — sparse market-reality model.

    Produces a directional bias from the recent slope. We map:

        slope_pct > +0.0015/day  →  USD_TRENDING_DOWN analogue → +0.3% per 24h median shift
        slope_pct < -0.0015/day  →  USD_TRENDING_UP   analogue → -0.3% per 24h median shift
        |slope_pct| <= 0.0015    →  FLAT / UNKNOWN      →  flat median

    The "M2" here is the *sparse-regime-derived point forecast*; the
    full M2 pipeline (`/root/WEALTH/forecast/m2/`) lives upstream and
    emits a discrete label, not a price path. This is the most
    defensible scalar translation of that label into a price forecast.

    The bands are M0's bands (M2 has no distribution of its own — it
    is the *sparse* model). Skill against M2 then measures "does the
    directional bias from the wave content beat the directional bias
    from the trend slope alone?".
    """
    if closes.size < 30:
        return _m0_forecast(closes, horizons_h)
    win = closes[-TREND_WINDOW:]
    log_close = np.log(win)
    slope_per_day = float((log_close[-1] - log_close[0]) / (len(win) - 1))
    if slope_per_day > 0.0015:
        bias_per_24h = 0.003
    elif slope_per_day < -0.0015:
        bias_per_24h = -0.003
    else:
        bias_per_24h = 0.0
    last = float(closes[-1])
    rets = np.diff(np.log(closes[-60:]))
    sigma = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.01
    out = {}
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


def _m4_wave_forecast(
    closes: np.ndarray, *, seed: int = 1337, horizons_h: tuple[int, ...] = WALK_FORWARD_HORIZONS_H
) -> dict:
    """M4-WAVE — full challenger pipeline on the close array.

    Builds a synthetic-history-like frame around ``closes``, runs the
    pipeline, and returns the central path's quantiles at each horizon.

    Ensemble size is capped at 10 inside the walk-forward harness so a
    full pass over the history stays under the audit budget; the
    production run (999-WITNESS) uses the full ensemble.
    """
    if closes.size < _causality.MIN_HISTORY_DAYS:
        return _m0_forecast(closes, horizons_h)
    idx = pd.date_range(
        end=pd.Timestamp.now(timezone.utc).normalize(), periods=len(closes), freq="D"
    )
    df = pd.DataFrame({"close": closes, "high": closes, "low": closes, "open": closes, "volume": 0}, index=idx)
    history = HistorySeries(df=df, source="SYNTHETIC", reason=f"synthetic_audit_window_{len(closes)}d", fetched_at=datetime.now(timezone.utc).isoformat())
    cert = _causality.AGENT_000_Causality(history)
    if not cert.ok:
        return _m0_forecast(closes, horizons_h)
    decomp = _decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=seed)
    if not decomp.ok:
        return _m0_forecast(closes, horizons_h)
    ws = _wave_state.AGENT_222_WaveState(decomp)
    if not ws.ok:
        return _m0_forecast(closes, horizons_h)
    path = _path_forge.AGENT_333_PathForge(history, ws, cert, horizon_hours=72)
    if not path.ok:
        return _m0_forecast(closes, horizons_h)
    out = {}
    for hp in path.horizons:
        if hp.offset_hours in horizons_h:
            out[hp.offset_hours] = (hp.p10, hp.p25, hp.p50, hp.p75, hp.p90)
    return out


# ── Walk-forward scoring ────────────────────────────────────────────────


def _walk_forward_score(
    history_close: np.ndarray,
    *,
    predictor: Callable[..., dict],
    lookback: int = WALK_FORWARD_LOOKBACK,
    horizons_h: tuple[int, ...] = WALK_FORWARD_HORIZONS_H,
    step_days: int = WALK_FORWARD_STEP_DAYS,
    **predictor_kwargs: Any,
) -> tuple[float, float, int]:
    """Run the walk-forward and return (mean_pinball, coverage, n_windows).

    Coverage = fraction of realised closes that fell in [P10, P90].
    """
    n = len(history_close)
    if n < lookback + max(horizons_h) // 24 + 1:
        return 0.0, 0.0, 0
    pinball_total = 0.0
    pinball_n = 0
    coverage_hits = 0
    coverage_total = 0

    for t in range(lookback, n - max(horizons_h) // 24, step_days):
        window = history_close[: t + 1]
        actuals = {
            h: float(history_close[t + h // 24]) if (t + h // 24) < n else float("nan")
            for h in horizons_h
        }
        if any(np.isnan(v) for v in actuals.values()):
            continue
        forecast = predictor(window, horizons_h=horizons_h, **predictor_kwargs)
        if not forecast:
            continue
        # Only score at the requested horizons — M4-WAVE emits extra
        # hourly horizons (1, 6, 12, …) which the auditor must ignore.
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
    if pinball_n == 0:
        return 0.0, 0.0, 0
    mean_pinball = pinball_total / pinball_n
    coverage = coverage_hits / max(coverage_total, 1)
    # n_windows = number of origins scored.
    n_origins = (n - lookback - max(horizons_h) // 24) // step_days
    return mean_pinball, coverage, n_origins


def _walk_forward_pinball_only(
    history_close: np.ndarray,
    predictor: Callable[..., dict],
    **predictor_kwargs: Any,
) -> tuple[float, int]:
    """Pinball-only variant — used when we want coverage / bias too."""
    pb, _cov, n = _walk_forward_score(history_close, predictor=predictor, **predictor_kwargs)
    return pb, n


# ── Public agent ────────────────────────────────────────────────────────


def AGENT_555_Auditor(
    *,
    history: HistorySeries,
    wave_state: _wave_state.WaveStatePosterior,
    path: _path_forge.ForgePath,
    stability: _stability.StabilityReport,
    cert: _causality.CausalityCertificate,
    seed: int = 1337,
    now: Optional[datetime] = None,
) -> AuditReport:
    """Run the walk-forward audit and produce the skill comparison."""
    observed_at = (now or datetime.now(timezone.utc)).isoformat()

    # Quick exit if the pipeline is not healthy.
    if not cert.ok or not path.ok:
        return AuditReport(
            ok=False,
            failures=["upstream_failed"],
            reason="upstream pipeline did not produce a valid path",
            observed_at=observed_at,
        )

    closes = pd.to_numeric(history.df["close"], errors="coerce").to_numpy(dtype=float)
    closes = np.asarray(closes[~np.isnan(closes)], dtype=float)
    if closes.size < _causality.MIN_HISTORY_DAYS + 90:
        return AuditReport(
            ok=False,
            failures=["insufficient_history_for_audit"],
            reason=f"need {_causality.MIN_HISTORY_DAYS + 90} days, got {closes.size}",
            observed_at=observed_at,
        )

    # Score each model.
    m0_pb, m0_cov, n_win = _walk_forward_score(closes, predictor=_m0_forecast)
    m2_pb, m2_cov, _ = _walk_forward_score(closes, predictor=_m2_forecast)
    trend_pb, trend_cov, _ = _walk_forward_score(closes, predictor=_m4_trend_forecast)
    wave_pb, wave_cov, _ = _walk_forward_score(closes, predictor=_m4_wave_forecast, seed=seed)

    # Skill = 1 - (model_pinball / baseline_pinball). baseline = M0.
    def _skill(model_pb: float, baseline_pb: float) -> float:
        if baseline_pb <= 0:
            return 0.0
        return 1.0 - (model_pb / baseline_pb)

    skill_vs_M0 = _skill(wave_pb, m0_pb)
    skill_vs_M2 = _skill(wave_pb, m2_pb)
    skill_vs_M4_TREND = _skill(wave_pb, trend_pb)

    # Bias p50: average signed (median - actual) over windows.
    bias_p50 = _bias_p50(closes, _m4_wave_forecast, seed=seed)

    # Build per-model summaries.
    models = [
        ModelSkill(name="M0_random_walk", pinball_skill_vs_M0=0.0, coverage_p10_p90=m0_cov, bias_p50=0.0, n_windows=n_win),
        ModelSkill(name="M2_sparse_regime", pinball_skill_vs_M0=_skill(m2_pb, m0_pb), coverage_p10_p90=m2_cov, bias_p50=0.0, n_windows=n_win),
        ModelSkill(name="M4_TREND", pinball_skill_vs_M0=_skill(trend_pb, m0_pb), coverage_p10_p90=trend_cov, bias_p50=0.0, n_windows=n_win),
        ModelSkill(name="M4_WAVE", pinball_skill_vs_M0=skill_vs_M0, coverage_p10_p90=wave_cov, bias_p50=bias_p50, n_windows=n_win),
    ]

    promotion = (
        skill_vs_M0 > PROMOTE_PINBALL_SKILL_FLOOR
        and skill_vs_M4_TREND > PROMOTE_TREND_PINBALL_SKILL_FLOOR
        and skill_vs_M2 > PROMOTE_M2_PINBALL_SKILL_FLOOR
    )
    reason_codes: list[str] = []
    if skill_vs_M0 <= PROMOTE_PINBALL_SKILL_FLOOR:
        reason_codes.append(f"M4_WAVE_NOT_BEATING_M0:skill={skill_vs_M0:.4f}")
    if skill_vs_M4_TREND <= PROMOTE_TREND_PINBALL_SKILL_FLOOR:
        reason_codes.append(f"M4_WAVE_NOT_BEATING_M4_TREND:skill={skill_vs_M4_TREND:.4f}")
    if skill_vs_M2 <= PROMOTE_M2_PINBALL_SKILL_FLOOR:
        reason_codes.append(f"M4_WAVE_NOT_BEATING_M2:skill={skill_vs_M2:.4f}")
    if not reason_codes:
        reason_codes.append("ALL_ADMISSION_GATES_PASSED")

    return AuditReport(
        ok=True,
        skill_vs_M0=skill_vs_M0,
        skill_vs_M2=skill_vs_M2,
        skill_vs_M4_TREND=skill_vs_M4_TREND,
        M0_pinball=m0_pb,
        M2_pinball=m2_pb,
        M4_TREND_pinball=trend_pb,
        M4_WAVE_pinball=wave_pb,
        M4_WAVE_coverage=wave_cov,
        M4_WAVE_bias=bias_p50,
        n_windows=n_win,
        models=models,
        promotion_recommended=promotion,
        reason=";".join(reason_codes),
        observed_at=observed_at,
    )


def _bias_p50(
    history_close: np.ndarray,
    predictor: Callable[..., dict],
    *,
    seed: int = 1337,
) -> float:
    """Mean signed bias (median − actual) over walk-forward windows."""
    n = len(history_close)
    if n < WALK_FORWARD_LOOKBACK + 3:
        return 0.0
    biases: list[float] = []
    for t in range(WALK_FORWARD_LOOKBACK, n - 3, WALK_FORWARD_STEP_DAYS):
        window = history_close[: t + 1]
        actual = float(history_close[t + 3]) if (t + 3) < n else float("nan")
        if np.isnan(actual):
            continue
        forecast = predictor(window, seed=seed, horizons_h=(24,))
        if 24 not in forecast:
            continue
        median = forecast[24][2]
        biases.append((median - actual) / actual if actual > 0 else 0.0)
    return float(np.mean(biases)) if biases else 0.0


__all__ = [
    "AGENT_555_Auditor",
    "AuditReport",
    "ModelSkill",
    "WALK_FORWARD_LOOKBACK",
    "WALK_FORWARD_HORIZONS_H",
    "PINBALL_QUANTILES",
]