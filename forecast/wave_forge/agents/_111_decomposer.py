"""Agent 111 — DECOMPOSER.

Takes a causality-cleared history and decomposes it two ways in
parallel:

1. **Stationary Wavelet Transform** (``pywt.swt``, default sym4 at
   level 4) — gives shift-invariant sub-bands [cA_4, cD_4, cD_3,
   cD_2, cD_1].
2. **CEEMDAN** (from-scratch, ensemble default 50) — gives
   data-adaptive IMFs ordered high → low frequency, with the final
   residual as the trend.

Both decompositions get their Hilbert envelope (instantaneous
amplitude / phase / frequency) so the 222 lane has the raw material for
its posterior.

The output is a typed ``DecompositionRecord``. Both decompositions are
always attempted; if either fails (e.g. series too short for wavelet at
the requested level) the failure is recorded in the record and the
222 lane degrades gracefully using only the surviving decomposition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence

import numpy as np
import pandas as pd

from ..decompose import (
    ModeRecord,
    build_mode_records,
    ceemdan_decompose,
    wavelet_decompose,
)
from ..synthetic import HistorySeries
from . import _000_causality as _causality


# Default decomposition parameters — kept here (not in the function
# signature) so the auditor's reports can pin them deterministically.
WAVELET_NAME = "sym4"
WAVELET_LEVEL = 4
CEEMDAN_ENSEMBLE = 50
CEEMDAN_NOISE_STD = 0.2
CEEMDAN_MAX_IMFS = 8


@dataclass(frozen=True)
class DecompositionRecord:
    """The 111-DECOMPOSER output.

    Attributes
    ----------
    ok
        True if at least one decomposition succeeded.
    wavelet
        List of ``ModeRecord`` from SWT (empty if failed).
    ceemdan
        List of ``ModeRecord`` from CEEMDAN (empty if failed).
    failures
        List of failure tokens (empty when ok=True).
    used_window
        The trimmed history actually fed to the decompositions.
    notes
        Free-form audit notes (e.g. ensemble size used, padding applied).
    observed_at
        ISO-8601 UTC.
    """

    ok: bool
    wavelet: List[ModeRecord] = field(default_factory=list)
    ceemdan: List[ModeRecord] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    used_window: int = 0
    notes: dict[str, Any] = field(default_factory=dict)
    observed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "111-DECOMPOSER",
            "ok": self.ok,
            "wavelet_count": len(self.wavelet),
            "ceemdan_count": len(self.ceemdan),
            "failures": list(self.failures),
            "used_window": self.used_window,
            "notes": dict(self.notes),
            "observed_at": self.observed_at,
        }


def _safe_wavelet(x: np.ndarray, *, wavelet: str, level: int) -> tuple[Optional[List[np.ndarray]], Optional[str]]:
    """Wavelet decompose with try/except and pad-target adjustment."""
    try:
        return wavelet_decompose(x, wavelet=wavelet, level=level), None
    except Exception as exc:  # noqa: BLE001 — narrow reporting expected
        return None, f"wavelet_failed:{type(exc).__name__}"


def _safe_ceemdan(
    x: np.ndarray, *, ensemble_size: int, noise_std: float, max_imfs: int, seed: int
) -> tuple[Optional[List[np.ndarray]], Optional[str]]:
    """CEEMDAN with try/except — never raises to caller."""
    try:
        return (
            ceemdan_decompose(
                x,
                ensemble_size=ensemble_size,
                ensemble_noise_std=noise_std,
                max_imfs=max_imfs,
                seed=seed,
            ),
            None,
        )
    except Exception as exc:  # noqa: BLE001
        return None, f"ceemdan_failed:{type(exc).__name__}"


def AGENT_111_Decomposer(
    history: HistorySeries,
    cert: _causality.CausalityCertificate,
    *,
    wavelet_name: str = WAVELET_NAME,
    wavelet_level: int = WAVELET_LEVEL,
    ensemble_size: int = CEEMDAN_ENSEMBLE,
    noise_std: float = CEEMDAN_NOISE_STD,
    max_imfs: int = CEEMDAN_MAX_IMFS,
    seed: int = 1337,
) -> DecompositionRecord:
    """Run wavelet + CEEMDAN on the causality-cleared close series.

    Failure handling
    ---------------
    * Hard gate (``cert.ok is False``) ⇒ refuse to decompose. Return an
      empty record with ``failures=['causality_gate_failed']``.
    * Wavelet fails (e.g. too short) ⇒ record the failure, keep CEEMDAN.
    * CEEMDAN fails ⇒ record the failure, keep wavelet.
    * Both fail ⇒ ``ok=False`` with both failure tokens.

    The two decompositions are deliberately redundant: they expose
    different families of cycles (orthogonal basis vs data-adaptive
    basis). For 222 to claim a "validated mode", the same frequency band
    must appear in BOTH decompositions — that is the Falsifiability
    invariant of this pipeline.
    """
    observed_at = datetime.now(timezone.utc).isoformat()
    failures: list[str] = []

    if not cert.ok:
        return DecompositionRecord(
            ok=False,
            failures=["causality_gate_failed"],
            notes={"causality_failures": list(cert.failures)},
            observed_at=observed_at,
        )

    df = history.df
    closes = pd.to_numeric(df["close"], errors="coerce").to_numpy(dtype=float)
    closes = np.asarray(closes[~np.isnan(closes)], dtype=float)

    # Apply trim if the gate flagged it.
    trim = cert.notes.get("trim_window_days", 0)
    if trim and len(closes) > trim:
        closes = closes[-trim:]

    # Detrend with a linear fit so the wavelet doesn't see a DC offset
    # that absorbs the high-frequency content. We add the trend back
    # in the path-forge stage.
    t_idx = np.arange(len(closes), dtype=float)
    if len(closes) >= 2:
        slope, intercept = np.polyfit(t_idx, closes, 1)
        trend = slope * t_idx + intercept
        detrended = closes - trend
    else:
        slope, intercept, trend, detrended = 0.0, closes[-1], closes, np.zeros_like(closes)

    notes: dict[str, Any] = {
        "wavelet_name": wavelet_name,
        "wavelet_level": wavelet_level,
        "ceemdan_ensemble": ensemble_size,
        "ceemdan_noise_std": noise_std,
        "ceemdan_max_imfs": max_imfs,
        "trend_slope": float(slope),
        "trend_intercept": float(intercept),
        "trim_applied": bool(trim and len(closes) <= trim),
    }

    # ── Wavelet ─────────────────────────────────────────────────────────
    w_raw, w_err = _safe_wavelet(detrended, wavelet=wavelet_name, level=wavelet_level)
    if w_err:
        failures.append(w_err)
    wavelet_modes: List[ModeRecord] = []
    if w_raw:
        total_energy = float(np.sum(detrended * detrended)) + 1e-12
        wavelet_modes = build_mode_records(w_raw, source="wavelet", sample_total_energy=total_energy)

    # ── CEEMDAN ─────────────────────────────────────────────────────────
    c_raw, c_err = _safe_ceemdan(
        detrended,
        ensemble_size=ensemble_size,
        noise_std=noise_std,
        max_imfs=max_imfs,
        seed=seed,
    )
    if c_err:
        failures.append(c_err)
    ceemdan_modes: List[ModeRecord] = []
    if c_raw:
        total_energy = float(np.sum(detrended * detrended)) + 1e-12
        ceemdan_modes = build_mode_records(c_raw, source="ceemdan", sample_total_energy=total_energy)

    ok = bool(wavelet_modes or ceemdan_modes)
    if not ok:
        failures.append("both_decompositions_empty")

    return DecompositionRecord(
        ok=ok,
        wavelet=wavelet_modes,
        ceemdan=ceemdan_modes,
        failures=failures,
        used_window=len(closes),
        notes=notes,
        observed_at=observed_at,
    )


__all__ = [
    "AGENT_111_Decomposer",
    "DecompositionRecord",
    "WAVELET_NAME",
    "WAVELET_LEVEL",
    "CEEMDAN_ENSEMBLE",
    "CEEMDAN_NOISE_STD",
    "CEEMDAN_MAX_IMFS",
]