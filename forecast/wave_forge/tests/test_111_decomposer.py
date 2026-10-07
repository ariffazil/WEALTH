"""Tests for the 111-DECOMPOSER (wavelet + CEEMDAN).

Covers:

* clean history ⇒ both decompositions succeed, at least one mode each
* causal-gate failure ⇒ empty record with `causality_gate_failed`
* the wavelet + CEEMDAN pipelines can each extract a known sinusoid
* the Hilbert envelope is computed for every mode
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wave_forge.agents import _000_causality as causality
from wave_forge.agents import _111_decomposer as decomposer
from wave_forge.decompose import ceemdan_decompose, hilbert_envelope, wavelet_decompose


def _clean_history():
    import pandas as pd

    n = 400
    rng = np.random.default_rng(0)
    closes = 2400.0 + np.cumsum(rng.normal(0, 1, n))
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame(
        {"open": closes, "high": closes + 1, "low": closes - 1, "close": closes, "volume": 1000},
        index=idx,
    )
    from wave_forge.synthetic import HistorySeries

    return HistorySeries(
        df=df,
        source="SYNTHETIC",
        reason=f"test_synthetic_decomposer_{n}d",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def test_causality_failure_short_circuits_decomposer() -> None:
    """When causality gate fails, the decomposer returns ok=False."""
    from wave_forge.synthetic import HistorySeries

    # 10-day history fails the causality minimum.
    import pandas as pd

    closes = [2400.0] * 10
    df = pd.DataFrame({"close": closes}, index=pd.date_range("2024-01-01", periods=10, freq="D"))
    history = HistorySeries(
        df=df,
        source="test_synthetic_short",
        reason="test_synthetic_short",
        fetched_at="2026-01-01T00:00:00",
    )
    cert = causality.AGENT_000_Causality(history)
    assert not cert.ok
    decomp = decomposer.AGENT_111_Decomposer(history, cert)
    assert not decomp.ok
    assert "causality_gate_failed" in decomp.failures


def test_wavelet_decomposition_extracts_components() -> None:
    """Wavelet decompose a 256-point sinusoid → 5 components at level 4."""
    from wave_forge.decompose import wavelet_reconstruct

    n = 256
    t = np.arange(n, dtype=float)
    x = np.sin(2.0 * np.pi * t / 16) + 0.5 * np.sin(2.0 * np.pi * t / 32)
    comps = wavelet_decompose(x, wavelet="sym4", level=4)
    assert len(comps) == 5  # cA_4 + cD_4..cD_1
    # Each component has the same length as the input (SWT is
    # shift-invariant and does not downsample).
    for c in comps:
        assert c.shape == (n,)
    # Lossless reconstruction via inverse SWT — this is the round-trip
    # invariant the SWT family provides.
    rec = wavelet_reconstruct(comps, wavelet="sym4")
    np.testing.assert_allclose(rec, x, atol=1e-6)


def test_ceemdan_extracts_at_least_one_imf() -> None:
    """CEEMDAN returns at least one IMF for a non-trivial signal."""
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(0, 1, 256))
    x = x - np.linspace(x[0], x[-1], len(x))  # detrend
    imfs = ceemdan_decompose(x, ensemble_size=20, seed=42)
    assert len(imfs) >= 2  # at least one IMF + the residual
    # All components should have the same length as the input.
    for imf in imfs:
        assert imf.shape == x.shape


def test_hilbert_envelope_returns_amp_phase_freq() -> None:
    """Hilbert envelope returns amp/phase/instantaneous_frequency."""
    n = 256
    t = np.arange(n, dtype=float)
    x = np.sin(2.0 * np.pi * t / 16)
    env = hilbert_envelope(x)
    assert env["amplitude"].shape == (n,)
    assert env["phase"].shape == (n,)
    assert env["instantaneous_frequency"].shape == (n,)
    # For a pure sine wave, the instantaneous frequency at the centre
    # should be approximately 1/16 cycles per sample.
    centre_freq = float(env["instantaneous_frequency"][n // 2])
    expected = 1.0 / 16.0
    assert abs(centre_freq - expected) < 0.05


def test_decomposer_runs_on_clean_history() -> None:
    """The 111 lane runs both decompositions and produces mode records."""
    history = _clean_history()
    cert = causality.AGENT_000_Causality(history)
    assert cert.ok
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    assert decomp.ok, f"decomposer failed: {decomp.failures}"
    assert decomp.wavelet, "wavelet produced no components"
    assert decomp.ceemdan, "CEEMDAN produced no IMFs"


def test_decomposition_record_exposes_hilbert_envelope() -> None:
    """Each ModeRecord in the DecompositionRecord carries a Hilbert envelope."""
    history = _clean_history()
    cert = causality.AGENT_000_Causality(history)
    decomp = decomposer.AGENT_111_Decomposer(history, cert, ensemble_size=10, seed=42)
    # Every wavelet mode has amplitude/phase/frequency of length >0.
    for mode in decomp.wavelet:
        assert mode.amplitude.size > 0
        assert mode.phase.size > 0
        assert mode.frequency.size > 0
        assert mode.source == "wavelet"