"""Agent 333 — PATH-FORGE.

Continues the validated wave modes forward ``horizon_hours`` (default 72)
and assembles the five-quantile path (P10/P25/P50/P75/P90).

Approach
========

For each validated mode we have, at the right edge of the history, the
**current phase**, **current instantaneous frequency**, and **current
amplitude**. We propagate the phase forward by linear extrapolation
(integrate frequency) and decay the amplitude geometrically. The decay
rate is calibrated per-mode from the right-edge amplitude envelope: if
the mode has been losing amplitude over the persistence window at rate
α, we apply the same decay forward.

We sum the propagated modes + the linear trend (saved by 111) to get
the central path. The quantile bands (P10/P25/P75/P90) come from a
*mode-conditional* Gaussian: each mode contributes its own σ (a
fraction of its edge amplitude), summed in quadrature across modes, so
modes with low edge amplitude contribute little uncertainty. This
respects the Falsifiability invariant: a mode that validated as
"persistence_low" still enters the path but with a tiny weight — it
cannot manufacture certainty it did not earn.

The endpoint-stability field is the dispersion of the central path
across the lookback attack (set up by 444). High dispersion ⇒ the
endpoint is at the right edge of the noise cone, and the path is
flagged as fragile.

Output schema (per the task contract):

    {
      forecast_id, origin_time,
      amplitudes:        {<source>:<idx>: <amp array length horizon_hours>},
      phases:            {<source>:<idx>: <phase array length horizon_hours>},
      frequencies:       {<source>:<idx>: <freq array length horizon_hours>},
      mode_persistence:  {<source>:<idx>: float},
      endpoint_stability: float,
      horizons:          [{offset_hours, p10, p25, p50, p75, p90}, ...],
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..synthetic import HistorySeries
from . import _000_causality as _causality
from . import _222_wave_state as _wave_state


# Default forward horizon (72 hours — the task contract).
HORIZON_HOURS = 72
HOURLY_STEPS_PER_DAY = 24
# We operate in *hourly* time. The 111 lane gave us daily closes; we
# need 72 hourly steps. We scale the validated modes' frequencies to
# hourly units (divide mean_period_steps by 24) and propagate them at
# the hourly step resolution.
STEPS_PER_DAY = HOURLY_STEPS_PER_DAY
# Default per-hour amplitude decay rate when the mode has not been
# losing amplitude. Geometric decay half-life = ln(2)/DECAY_PER_HOUR ≈
# 168 hours (~7 days) — long enough to matter, short enough that no
# mode stays flat forever.
DEFAULT_DECAY_PER_HOUR = 0.004


@dataclass(frozen=True)
class HorizonPoint:
    offset_hours: int
    timestamp: str
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "offset_hours": self.offset_hours,
            "timestamp": self.timestamp,
            "p10": round(self.p10, 4),
            "p25": round(self.p25, 4),
            "p50": round(self.p50, 4),
            "p75": round(self.p75, 4),
            "p90": round(self.p90, 4),
        }


@dataclass
class ForgePath:
    """The 333-PATH-FORGE output."""

    ok: bool
    origin_time: str = ""
    horizon_hours: int = HORIZON_HOURS
    horizons: List[HorizonPoint] = field(default_factory=list)
    amplitudes: Dict[str, np.ndarray] = field(default_factory=dict)
    phases: Dict[str, np.ndarray] = field(default_factory=dict)
    frequencies: Dict[str, np.ndarray] = field(default_factory=dict)
    mode_persistence: Dict[str, float] = field(default_factory=dict)
    endpoint_stability: float = 0.0
    failures: list[str] = field(default_factory=list)
    observed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        def _round_dict(d: dict, k: str) -> dict:
            return {key: [round(float(x), 4) for x in arr] for key, arr in d.items()}

        return {
            "agent": "333-PATH-FORGE",
            "ok": self.ok,
            "origin_time": self.origin_time,
            "horizon_hours": self.horizon_hours,
            "horizons": [h.to_dict() for h in self.horizons],
            "amplitudes": _round_dict(self.amplitudes, "amplitudes"),
            "phases": _round_dict(self.phases, "phases"),
            "frequencies": _round_dict(self.frequencies, "frequencies"),
            "mode_persistence": {k: round(v, 4) for k, v in self.mode_persistence.items()},
            "endpoint_stability": round(self.endpoint_stability, 4),
            "failures": list(self.failures),
            "observed_at": self.observed_at,
        }


def _mode_label(source: str, idx: int) -> str:
    return f"{source}:{idx}"


def _edge_phase_and_amp(
    mode: _wave_state.ValidatedMode,
) -> tuple[float, float]:
    """Return (phase at edge, instantaneous frequency at edge) in hourly units.

    The phase and frequency returned here are what the 222 lane stamped
    on the right edge (in *daily* sample units). We convert to hourly
    units by dividing mean_period_steps by 24; this is the cleanest
    place to do the unit conversion because the underlying mean period
    is the only scale-invariant quantity we have.
    """
    if mode.mean_period_steps is None or mode.mean_period_steps <= 0:
        return 0.0, 0.0
    # Hourly period (steps) = daily period / 24
    hourly_period = max(mode.mean_period_steps / STEPS_PER_DAY, 1.0)
    hourly_freq = 1.0 / hourly_period
    # Phase at edge is stored in radians. The validated mode's edge
    # frequency is in cycles/step; converting to cycles/hour:
    edge_freq_hz = mode.edge_frequency / STEPS_PER_DAY
    # Use 0 as the absolute phase reference — only the *change* in
    # phase matters for the propagation.
    return 0.0, float(edge_freq_hz)


def _phase_offset_for_mode(
    mode: _wave_state.ValidatedMode,
    full_phase_array: np.ndarray | None,
) -> float:
    """Return the phase at the right edge of the history for ``mode``.

    The validated mode carries only aggregate statistics (mean period,
    edge amplitude, edge frequency). To anchor the forward
    propagation we read the actual Hilbert phase from the underlying
    decomposition — this lives in the raw ``ModeRecord`` carried by
    the path. If unavailable (e.g. a future re-architecture) we
    default to 0.
    """
    if full_phase_array is None or full_phase_array.size == 0:
        return 0.0
    return float(full_phase_array[-1])


def _decay_rate_for_mode(mode: _wave_state.ValidatedMode) -> float:
    """Per-hour geometric amplitude decay for ``mode``.

    If the mode has been losing amplitude in the persistence window
    (persistence_ratio < 1), accelerate the decay; if it has been
    *gaining* (ratio > 1 is impossible — capped at 1 by 222), default.
    Conservative default is used for any mode the 222 lane did not flag.
    """
    # persistence_ratio is amp_edge / amp_peak over the persistence
    # window (default 30 daily samples). Convert to per-hour ratio by
    # assuming the persistence window covers 30 days of amplitude.
    if mode.persistence_ratio <= 0:
        return DEFAULT_DECAY_PER_HOUR * 4  # fast decay for degenerate modes
    # decay constant α such that exp(-α · 30·24) = persistence_ratio
    hours = _wave_state.PERSISTENCE_LOOKBACK * STEPS_PER_DAY
    if mode.persistence_ratio >= 1.0:
        return 0.0  # flat — no decay
    # α = -ln(persistence_ratio) / hours
    alpha = -np.log(max(mode.persistence_ratio, 1e-9)) / max(hours, 1)
    # Clamp to ±5× the default — pathological ratios produce nonsense.
    alpha = float(np.clip(alpha, 0.0, DEFAULT_DECAY_PER_HOUR * 5))
    return alpha


def _normal_quantile(p: float) -> float:
    """Standard-normal quantile via scipy (ppf is the inverse CDF)."""
    from scipy.stats import norm
    return float(norm.ppf(p))


def AGENT_333_PathForge(
    history: HistorySeries,
    wave_state: _wave_state.WaveStatePosterior,
    cert: _causality.CausalityCertificate,
    *,
    horizon_hours: int = HORIZON_HOURS,
    now: Optional[datetime] = None,
) -> ForgePath:
    """Continue validated modes forward and emit the quantile path."""
    observed_at = datetime.now(timezone.utc).isoformat()
    failures: list[str] = []

    if not wave_state.ok or not wave_state.validated:
        return ForgePath(
            ok=False,
            failures=["no_validated_modes"],
            origin_time=cert.origin_time,
            observed_at=observed_at,
        )
    if not cert.ok:
        return ForgePath(
            ok=False,
            failures=["causality_gate_failed"],
            origin_time=cert.origin_time,
            observed_at=observed_at,
        )

    horizon_hours = int(horizon_hours)
    if horizon_hours <= 0:
        return ForgePath(
            ok=False,
            failures=["horizon_non_positive"],
            origin_time=cert.origin_time,
            observed_at=observed_at,
        )

    # Anchor (current price) is the last close of the history.
    closes = pd.to_numeric(history.df["close"], errors="coerce").to_numpy(dtype=float)
    closes = np.asarray(closes[~np.isnan(closes)], dtype=float)
    if closes.size == 0 or closes[-1] <= 0:
        return ForgePath(
            ok=False,
            failures=["no_valid_close"],
            origin_time=cert.origin_time,
            observed_at=observed_at,
        )
    spot = float(closes[-1])

    # Per-mode propagation.
    n_steps = horizon_hours
    steps = np.arange(1, n_steps + 1, dtype=float)  # 1, 2, ..., 72
    central_path = np.zeros(n_steps, dtype=float)

    # Accumulate per-mode uncertainty (σ² contribution) for the
    # quantile bands. Each mode contributes (σ_mode)² where σ_mode is
    # proportional to its edge amplitude — high-amp modes are
    # *more* uncertain because they have more to misplace.
    sigma2_path = np.zeros(n_steps, dtype=float)

    amplitudes: Dict[str, np.ndarray] = {}
    phases: Dict[str, np.ndarray] = {}
    frequencies: Dict[str, np.ndarray] = {}
    mode_persistence: Dict[str, float] = {}

    # We also need to fold in the *trend* that 111 subtracted before
    # decomposition. The trend is approximated by a per-hour log drift
    # estimated from the persistence window (last 30 days of closes).
    persistence_window = min(_wave_state.PERSISTENCE_LOOKBACK, len(closes))
    if persistence_window >= 2:
        log_close = np.log(closes[-persistence_window:])
        # Average per-hour log drift over the window — geometric.
        hours_in_window = (persistence_window - 1) * STEPS_PER_DAY
        if hours_in_window > 0:
            trend_log_per_hour = (log_close[-1] - log_close[0]) / hours_in_window
        else:
            trend_log_per_hour = 0.0
    else:
        trend_log_per_hour = 0.0
    trend_path = np.log(spot) + trend_log_per_hour * steps
    central_path_log = trend_path.copy()  # log-space

    # Cap how many modes we propagate — the top MAX_PROPAGATED_MODES
    # by energy share. Adding more low-energy modes inflates the log
    # central path without improving coverage. (This is the cap that
    # keeps the synthetic-GBM baseline from blowing up the central
    # path with mostly-noise contributions.)
    MAX_PROPAGATED_MODES = 2
    sorted_modes = sorted(
        [m for m in wave_state.validated if m.edge_amplitude > 0],
        key=lambda m: m.energy_share,
        reverse=True,
    )[:MAX_PROPAGATED_MODES]

    for mode in sorted_modes:
        label = _mode_label(mode.source, mode.index)
        # Initial phase (we use 0 — only phase *changes* matter) and
        # edge frequency.
        _, edge_freq_hz = _edge_phase_and_amp(mode)
        if edge_freq_hz <= 0:
            # No frequency information — skip this mode's contribution
            # but record its (empty) propagation for audit.
            amplitudes[label] = np.zeros(n_steps)
            phases[label] = np.zeros(n_steps)
            frequencies[label] = np.zeros(n_steps)
            mode_persistence[label] = float(mode.persistence_ratio)
            continue
        # Propagated phase: φ(t) = phase_offset + 2π · edge_freq_hz · t.
        phase_t = mode.phase_offset + 2.0 * np.pi * edge_freq_hz * steps
        # Decaying amplitude.
        alpha = _decay_rate_for_mode(mode)
        amp_t = mode.edge_amplitude * np.exp(-alpha * steps)
        # Sinusoid contribution in log space? No — the modes were
        # extracted from the *detrended* price series. The
        # decomposition worked in price space, not log space. So the
        # contribution is in price space.
        contribution = amp_t * np.sin(phase_t)
        # Add to central path (price space). Note: this is *not* a
        # geometric path; for the central path we approximate log via
        # a small-angle assumption (sum of small amplitudes relative
        # to spot).
        # Convert contribution to log space by dividing by spot, then
        # add back to the log central path.
        if spot > 0:
            contribution_log = contribution / spot
            central_path_log = central_path_log + contribution_log

        # Per-mode σ contribution (price-space) — decay with the
        # amplitude envelope so a mode that vanished contributes no
        # uncertainty.
        # σ² contribution = (k · amp_edge)² · decay² where k=0.3
        # (calibrated so that the band width is comparable to a
        # one-sigma random-walk at the same horizon).
        sigma2_path += (0.3 * amp_t) ** 2

        amplitudes[label] = amp_t
        phases[label] = phase_t
        frequencies[label] = np.full(n_steps, edge_freq_hz, dtype=float)
        mode_persistence[label] = float(mode.persistence_ratio)

    # Convert log central path back to price space for the median.
    central_price = np.exp(central_path_log)
    # Endpoint volatility floor — even a perfectly flat series has a
    # non-zero random-walk σ; use the recent realised vol as a floor.
    if len(closes) >= 30:
        rets = np.diff(np.log(closes[-60:]))
        sigma_per_step = float(np.std(rets, ddof=1)) if rets.size > 1 else 0.005
    else:
        sigma_per_step = 0.005
    # Scale σ by sqrt(hours) for the forward horizon.
    sigma_h = sigma_per_step * np.sqrt(steps)
    sigma_price_h = central_price * sigma_h
    # Take the larger of: (mode-conditional σ) and the random-walk σ.
    # This is the conservative combination.
    mode_sigma = np.sqrt(sigma2_path)
    sigma_total = np.maximum(sigma_price_h, mode_sigma)

    # Quantile offsets at the standard normal.
    q10 = _normal_quantile(0.10)
    q25 = _normal_quantile(0.25)
    q75 = _normal_quantile(0.75)
    q90 = _normal_quantile(0.90)

    horizons: List[HorizonPoint] = []
    # Anchor time = origin (the right edge of the history).
    origin_ts = pd.Timestamp(cert.origin_time)
    if origin_ts.tzinfo is None:
        origin_ts = origin_ts.tz_localize("UTC")
    for h in (1, 6, 12, 24, 36, 48, 60, 72):
        if h > horizon_hours:
            continue
        i = h - 1
        mu = float(central_price[i])
        s = float(sigma_total[i])
        p10 = mu + q10 * s
        p25 = mu + q25 * s
        p50 = mu
        p75 = mu + q75 * s
        p90 = mu + q90 * s
        # ISO-8601 timestamp at this hour.
        ts = (origin_ts + timedelta(hours=h)).isoformat()
        horizons.append(
            HorizonPoint(
                offset_hours=h,
                timestamp=ts,
                p10=p10,
                p25=p25,
                p50=p50,
                p75=p75,
                p90=p90,
            )
        )

    # Endpoint stability: the dispersion of central_price[-1] across
    # the four 444 lookback attacks (14/30/60/90 days). The 444 lane
    # does the actual recomputation; here we publish the default value
    # (1.0 = perfectly stable) and let 444 overwrite it.
    endpoint_stability = 1.0

    return ForgePath(
        ok=True,
        origin_time=cert.origin_time,
        horizon_hours=horizon_hours,
        horizons=horizons,
        amplitudes=amplitudes,
        phases=phases,
        frequencies=frequencies,
        mode_persistence=mode_persistence,
        endpoint_stability=endpoint_stability,
        failures=failures,
        observed_at=observed_at,
    )


__all__ = [
    "AGENT_333_PathForge",
    "ForgePath",
    "HorizonPoint",
    "HORIZON_HOURS",
    "STEPS_PER_DAY",
]