"""Tests for the 000-CAUSALITY gate.

Covers:

* clean history ⇒ ok=True with no failures
* history with NaN in close ⇒ ok=False with `nan_in_close`
* history with monotonicity violation ⇒ ok=False with
  `non_monotonic_index` / `duplicate_timestamps`
* history shorter than MIN_HISTORY_DAYS ⇒ ok=False with
  `history_too_short:...`
* the override parameter ``min_history_days`` is honoured by the gate
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wave_forge.agents import _000_causality as causality
from wave_forge.synthetic import HistorySeries


def _make_history(closes: list, *, source: str = "SYNTHETIC") -> HistorySeries:
    n = len(closes)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1000] * n,
        },
        index=idx,
    )
    return HistorySeries(
        df=df,
        source=source,
        reason=f"test_synthetic_causality_{n}d",
        fetched_at="2026-09-25T00:00:00+00:00",
    )


def test_clean_history_passes_causality() -> None:
    """A long, clean, positive history ⇒ ok=True."""
    closes = [2400.0 + i * 0.01 for i in range(400)]
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert cert.ok, f"expected ok=True, got failures={cert.failures}"
    assert cert.n_obs == 400
    assert cert.history_window_days > 380
    assert cert.provenance == "SYNTHETIC"


def test_nan_in_close_fails_causality() -> None:
    """NaN in close ⇒ ok=False with `nan_in_close`."""
    closes = [2400.0] * 200
    closes[100] = float("nan")
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert not cert.ok
    assert "nan_in_close" in cert.failures


def test_history_too_short_fails_causality() -> None:
    """History shorter than MIN_HISTORY_DAYS ⇒ ok=False."""
    closes = [2400.0] * 30
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert not cert.ok
    assert any(f.startswith("history_too_short") for f in cert.failures)


def test_min_history_days_override_is_honoured() -> None:
    """The override parameter bypasses the default 180-day floor."""
    closes = [2400.0] * 60
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history, min_history_days=30)
    assert cert.ok, f"override failed: {cert.failures}"


def test_non_positive_close_fails_causality() -> None:
    """A non-positive close ⇒ ok=False with `non_positive_close`."""
    closes = [2400.0] * 200
    closes[50] = -1.0  # impossible price
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert not cert.ok
    assert "non_positive_close" in cert.failures


def test_duplicate_timestamps_fails_causality() -> None:
    """Duplicate timestamps ⇒ ok=False with `duplicate_timestamps`."""
    closes = [2400.0] * 200
    history = _make_history(closes)
    # Build a *new* HistorySeries with a duplicate index (HistorySeries
    # is frozen, so we can't mutate it in place).
    dup_df = pd.concat([history.df, history.df.iloc[[0]]])
    dup_history = HistorySeries(
        df=dup_df,
        source="test_synthetic_causality_duplicate_timestamps",
        reason="test_synthetic_causality_duplicate_timestamps",
        fetched_at="2026-09-25T00:00:00+00:00",
    )
    cert = causality.AGENT_000_Causality(dup_history)
    assert not cert.ok
    assert "duplicate_timestamps" in cert.failures


def test_synthetic_provenance_is_stamped() -> None:
    """Synthetic history ⇒ provenance=SYNTHETIC, not LIVE."""
    closes = [2400.0] * 250
    history = _make_history(closes)
    cert = causality.AGENT_000_Causality(history)
    assert cert.provenance == "SYNTHETIC"


def test_history_series_rejects_provenance_mismatch() -> None:
    """HistorySeries refuses to be created with mismatched source/reason."""
    closes = [2400.0] * 200
    df = pd.DataFrame({"close": closes}, index=pd.date_range("2024-01-01", periods=200, freq="D"))
    # LIVE label with synthetic_* reason ⇒ must raise.
    with pytest.raises(ValueError):
        HistorySeries(df=df, source="LIVE", reason="synthetic_seed=1_starts_with_synthetic", fetched_at="2026-01-01T00:00:00")
    # SYNTHETIC label with non-synthetic reason ⇒ must raise.
    with pytest.raises(ValueError):
        HistorySeries(df=df, source="SYNTHETIC", reason="live_fetch_does_not_start_with_synthetic", fetched_at="2026-01-01T00:00:00")