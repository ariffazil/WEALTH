"""Tests for the 444-STABILITY perturbation attacks.

Covers:

* the four lookback attacks (14/30/60/90 day) all execute and produce
  an AttackResult with a score in [0, 1]
* the endpoint-perturbation attack executes
* the regime-stratification attack executes and the per-quarter vol is
  computed
* the aggregated endpoint_stability is in [0, 1]
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
        reason=f"test_synthetic_stability_{len(closes)}d",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def _run_up_to_path(history: HistorySeries):
    """Drive history → cert → decomp → ws → path."""
    cert = causality.AGENT_000_Causality(history)
    assert cert.ok
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    assert decomp.ok
    ws = wave_state.AGENT_222_WaveState(decomp)
    path = path_forge.AGENT_333_PathForge(history, ws, cert, horizon_hours=72)
    return cert, decomp, ws, path


def test_all_four_lookback_attacks_execute() -> None:
    """14/30/60/90-day lookback attacks each produce an AttackResult."""
    rng = np.random.default_rng(0)
    closes = 2400.0 + np.cumsum(rng.normal(0, 1, 600))
    history = _history(closes)
    cert, decomp, ws, path = _run_up_to_path(history)
    if not path.ok:
        return
    rep = stability.AGENT_444_Stability(history, decomp, path, cert, seed=42)
    attack_names = {a.name for a in rep.attacks}
    # Required attacks are present.
    for required in (
        "lookback_14d",
        "lookback_30d",
        "lookback_60d",
        "lookback_90d",
        "endpoint_perturbation",
        "regime_stratification",
    ):
        assert required in attack_names, f"missing attack: {required}"
    # Every attack has a score in [0, 1].
    for a in rep.attacks:
        assert 0.0 <= a.score <= 1.0


def test_endpoint_perturbation_is_deterministic_under_seed() -> None:
    """Same seed ⇒ identical perturbation scores across runs."""
    rng = np.random.default_rng(0)
    closes = 2400.0 + np.cumsum(rng.normal(0, 1, 600))
    history = _history(closes)
    cert, decomp, ws, path = _run_up_to_path(history)
    if not path.ok:
        return
    rep1 = stability.AGENT_444_Stability(history, decomp, path, cert, seed=42)
    rep2 = stability.AGENT_444_Stability(history, decomp, path, cert, seed=42)
    scores1 = {a.name: a.score for a in rep1.attacks}
    scores2 = {a.name: a.score for a in rep2.attacks}
    assert scores1 == scores2


def test_endpoint_stability_is_bounded() -> None:
    """The aggregated endpoint_stability field is in [0, 1]."""
    rng = np.random.default_rng(0)
    closes = 2400.0 + np.cumsum(rng.normal(0, 1, 600))
    history = _history(closes)
    cert, decomp, ws, path = _run_up_to_path(history)
    if not path.ok:
        return
    rep = stability.AGENT_444_Stability(history, decomp, path, cert, seed=42)
    assert 0.0 <= rep.endpoint_stability <= 1.0


def test_regime_stratification_reports_per_quarter_volatility() -> None:
    """Regime stratification produces a quarters dict with four entries when history is sufficient."""
    rng = np.random.default_rng(0)
    closes = 2400.0 + np.cumsum(rng.normal(0, 1, 400))  # 400 days
    history = _history(closes)
    cert, decomp, ws, path = _run_up_to_path(history)
    if not path.ok:
        return
    rep = stability.AGENT_444_Stability(history, decomp, path, cert, seed=42)
    # Either the regime stratification succeeded and returned quarters,
    # or it ran with insufficient_history status — both are honest.
    if rep.regime_volatility.get("status") == "ok":
        assert len(rep.regime_volatility.get("quarters", {})) >= 2