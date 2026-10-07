"""Tests for the 888-JUDGE admission verdict and QUARANTINE / HOLD paths.

Covers:

* when any upstream gate fails, the judge returns QUARANTINE
* when the admission rule fails (M4-WAVE loses to M0/M2/M4-TREND),
  the judge returns HOLD with the correct reason_codes
* the judge never self-authorises USE; promotion always carries the
  ``PROMOTION_REQUIRES_F13_AUTHORIZATION`` token
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
from wave_forge.agents import _444_stability as stability
from wave_forge.agents import _555_auditor as auditor
from wave_forge.agents import _888_judge as judge
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
        reason=f"test_synthetic_judge_{len(closes)}d",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def test_quarantine_when_causality_fails() -> None:
    """If the causality gate fails, the judge returns QUARANTINE."""
    closes = [2400.0] * 10
    history = _history(np.array(closes))
    cert = causality.AGENT_000_Causality(history)
    assert not cert.ok
    # Stub the rest — the judge short-circuits on causality failure.
    decomp = decomposer.DecompositionRecord(
        ok=True, failures=[], observed_at="2026-01-01T00:00:00"
    )
    ws = wave_state.WaveStatePosterior(ok=True, failures=[], observed_at="2026-01-01T00:00:00")
    path = path_forge.ForgePath(ok=True, observed_at="2026-01-01T00:00:00")
    stab = stability.StabilityReport(ok=True, observed_at="2026-01-01T00:00:00")
    audit = auditor.AuditReport(ok=True, observed_at="2026-01-01T00:00:00")
    v = judge.AGENT_888_Judge(
        cert=cert, decomp=decomp, wave_state=ws, path=path, stability=stab, audit=audit
    )
    assert v.verdict == "QUARANTINE"
    assert any("causality_failed" in c for c in v.reason_codes)


def test_hold_when_admission_rule_fails() -> None:
    """When audit.promotion_recommended is False, judge returns HOLD."""
    closes = np.linspace(2400, 2500, 400)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.DecompositionRecord(
        ok=True, failures=[], observed_at="2026-01-01T00:00:00"
    )
    ws = wave_state.WaveStatePosterior(ok=True, failures=[], observed_at="2026-01-01T00:00:00")
    path = path_forge.ForgePath(ok=True, observed_at="2026-01-01T00:00:00")
    stab = stability.StabilityReport(ok=True, observed_at="2026-01-01T00:00:00")
    audit = auditor.AuditReport(
        ok=True,
        skill_vs_M0=-0.1,
        skill_vs_M2=-0.1,
        skill_vs_M4_TREND=-0.1,
        promotion_recommended=False,
        reason="M4_WAVE_NOT_BEATING_M0",
        observed_at="2026-01-01T00:00:00",
    )
    v = judge.AGENT_888_Judge(
        cert=cert, decomp=decomp, wave_state=ws, path=path, stability=stab, audit=audit
    )
    assert v.verdict == "HOLD"
    assert any("ADMISSION" in c for c in v.reason_codes)
    assert not v.admission_passed


def test_use_carries_f13_authorisation_token() -> None:
    """Even USE requires F13 authorisation — the judge does not self-authorise."""
    closes = np.linspace(2400, 2500, 400)
    history = _history(closes)
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.DecompositionRecord(
        ok=True, failures=[], observed_at="2026-01-01T00:00:00"
    )
    ws = wave_state.WaveStatePosterior(ok=True, failures=[], observed_at="2026-01-01T00:00:00")
    path = path_forge.ForgePath(ok=True, observed_at="2026-01-01T00:00:00")
    stab = stability.StabilityReport(ok=True, observed_at="2026-01-01T00:00:00")
    audit = auditor.AuditReport(
        ok=True,
        skill_vs_M0=0.05,
        skill_vs_M2=0.05,
        skill_vs_M4_TREND=0.05,
        promotion_recommended=True,
        reason="ALL_ADMISSION_GATES_PASSED",
        observed_at="2026-01-01T00:00:00",
    )
    v = judge.AGENT_888_Judge(
        cert=cert, decomp=decomp, wave_state=ws, path=path, stability=stab, audit=audit
    )
    assert v.verdict == "USE"
    assert "PROMOTION_REQUIRES_F13_AUTHORIZATION" in v.reason_codes
    assert v.admission_passed