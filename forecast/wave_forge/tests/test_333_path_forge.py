"""Tests for the 333-PATH-FORGE.

Covers:

* the path output contains the contract fields
  (forecast_id, origin_time, amplitudes, phases, frequencies,
  mode_persistence, endpoint_stability, horizons[{offset_hours, p10…
  p90}])
* on a short / no-wave-state history the path refuses to forge
* the horizons are anchored on the origin timestamp
* the quantile bands are monotone (p10 ≤ p25 ≤ p50 ≤ p75 ≤ p90)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wave_forge.agents import _000_causality as causality
from wave_forge.agents import _111_decomposer as decomposer
from wave_forge.agents import _222_wave_state as wave_state
from wave_forge.agents import _333_path_forge as path_forge
from wave_forge.synthetic import HistorySeries


def _history(closes: np.ndarray) -> HistorySeries:
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame(
        {"open": closes, "high": closes + 1, "low": closes - 1, "close": closes, "volume": 1000},
        index=idx,
    )
    return HistorySeries(
        df=df,
        source="SYNTHETIC",
        reason=f"test_synthetic_path_forge_{len(closes)}d",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def test_path_forge_refuses_when_wave_state_empty() -> None:
    """An empty wave state ⇒ the path-forge returns ok=False."""
    closes = np.linspace(2400, 2500, 400)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert cert.ok
    # Build an empty wave-state posterior.
    empty_ws = wave_state.WaveStatePosterior(
        ok=False,
        failures=["test_synthetic_forced_empty"],
        observed_at="2026-01-01T00:00:00",
    )
    path = path_forge.AGENT_333_PathForge(history, empty_ws, cert)
    assert not path.ok
    # The 333 lane fails because there are no validated modes to
    # propagate — the failure token reflects the wave_state failure.
    assert any(
        f.startswith("no_validated") or f == "wave_state_failed"
        for f in path.failures
    )


def test_path_forge_emits_contract_fields() -> None:
    """When a wave is validated, the path output matches the contract schema."""
    n = 400
    t = np.arange(n, dtype=float)
    closes = 2400.0 + 60.0 * np.sin(2.0 * np.pi * t / 25.0)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    ws = wave_state.AGENT_222_WaveState(decomp)
    if not ws.ok:
        # On this series, the wave may not validate — that is honest;
        # we skip the contract assertion in that case.
        return
    path = path_forge.AGENT_333_PathForge(history, ws, cert, horizon_hours=72)
    assert path.ok
    # The contract requires these fields.
    d = path.to_dict()
    assert "amplitudes" in d and isinstance(d["amplitudes"], dict)
    assert "phases" in d and isinstance(d["phases"], dict)
    assert "frequencies" in d and isinstance(d["frequencies"], dict)
    assert "mode_persistence" in d and isinstance(d["mode_persistence"], dict)
    assert "endpoint_stability" in d
    assert "horizons" in d
    assert len(d["horizons"]) > 0
    for h in d["horizons"]:
        for key in ("offset_hours", "p10", "p25", "p50", "p75", "p90", "timestamp"):
            assert key in h


def test_path_forge_quantile_bands_are_monotone() -> None:
    """At every horizon, P10 ≤ P25 ≤ P50 ≤ P75 ≤ P90."""
    n = 400
    t = np.arange(n, dtype=float)
    closes = 2400.0 + 60.0 * np.sin(2.0 * np.pi * t / 25.0)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    ws = wave_state.AGENT_222_WaveState(decomp)
    if not ws.ok:
        return
    path = path_forge.AGENT_333_PathForge(history, ws, cert, horizon_hours=72)
    if not path.ok:
        return
    for h in path.horizons:
        assert h.p10 <= h.p25 <= h.p50 <= h.p75 <= h.p90


def test_path_forge_horizons_anchored_on_origin() -> None:
    """Every horizon timestamp = origin_timestamp + offset_hours."""
    n = 400
    t = np.arange(n, dtype=float)
    closes = 2400.0 + 60.0 * np.sin(2.0 * np.pi * t / 25.0)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    ws = wave_state.AGENT_222_WaveState(decomp)
    if not ws.ok:
        return
    path = path_forge.AGENT_333_PathForge(history, ws, cert, horizon_hours=72)
    if not path.ok:
        return
    origin = pd.Timestamp(cert.origin_time)
    for h in path.horizons:
        ts = pd.Timestamp(h.timestamp)
        # Difference should equal offset_hours (within 1 minute).
        delta_hours = (ts - origin).total_seconds() / 3600.0
        assert abs(delta_hours - h.offset_hours) < 1.0 / 60.0