"""Tests for forecast/m2.

Contract under test
-------------------
* ``M2_REGIME_STATES`` is the canonical vocabulary — never an ad-hoc string.
* ``compute_regime_posterior`` is deterministic w.r.t. ``history`` + ``now``.
* Snapshot-only input (no history) collapses to ``UNKNOWN`` with reason
  ``snapshot_only_no_history`` — the verifier must never fabricate a
  direction from a single quote.
* Direction classification is per-asset:
    USD_TRENDING_UP/DOWN    when DXY slope dominates
    RATES_RISING/FALLING    when US10Y slope dominates (USD/rates disagree)
    MIXED                   when USD and rates both move but disagree on sign
    UNKNOWN                 when no driver or only flat drivers
* Confidence ∈ [0, 1] (clamped, never NaN).
* Malformed input (None, non-dict) collapses to UNKNOWN, never raises.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from forecast.m2 import (
    DEFAULT_SILVER_TREND_THRESHOLD,
    DEFAULT_US10Y_TREND_THRESHOLD,
    DEFAULT_USD_TREND_THRESHOLD,
    M2_REGIME_STATES,
    MIN_HISTORY_POINTS,
    RegimePosterior,
    compute_regime_posterior,
)


UTC = timezone.utc
T0 = datetime(2026, 9, 25, 10, 0, 0, tzinfo=UTC)


def _rising_series(start: float, step_pct: float, n: int = 8) -> list[float]:
    """Build a series of ``n`` points each ``step_pct`` fractionally higher."""
    out = []
    v = start
    for _ in range(n):
        out.append(round(v, 6))
        v = v * (1.0 + step_pct)
    return out


def _falling_series(start: float, step_pct: float, n: int = 8) -> list[float]:
    return _rising_series(start, -step_pct, n)


def _flat_series(start: float, n: int = 8) -> list[float]:
    return [float(start)] * n


# ══════════════════════════════════════════════════════════════════════════
# Vocabulary + helper integrity
# ══════════════════════════════════════════════════════════════════════════


def test_m2_regime_vocabulary_is_frozen_set() -> None:
    assert isinstance(M2_REGIME_STATES, frozenset)
    assert M2_REGIME_STATES == frozenset(
        {
            "USD_TRENDING_UP",
            "USD_TRENDING_DOWN",
            "RATES_RISING",
            "RATES_FALLING",
            "MIXED",
            "UNKNOWN",
        }
    )


def test_compute_regime_posterior_deterministic() -> None:
    """Same inputs → same outputs (excluding observed_at)."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _rising_series(100.0, 0.005, 6),
        "us10y": _flat_series(4.0, 6),
        "silver": _falling_series(30.0, 0.01, 6),
    }
    a = compute_regime_posterior(macro, history=history, now=T0)
    b = compute_regime_posterior(macro, history=history, now=T0)
    assert a.state == b.state
    assert a.confidence == b.confidence
    assert a.drivers == b.drivers
    assert a.evidence == b.evidence


def test_regime_posterior_unknown_state_collapses() -> None:
    p = RegimePosterior(state="GIBBERISH")
    assert p.state == "UNKNOWN"


def test_regime_posterior_confidence_clamped() -> None:
    p1 = RegimePosterior(state="UNKNOWN", confidence=2.5)
    p2 = RegimePosterior(state="UNKNOWN", confidence=-0.7)
    p3 = RegimePosterior(state="UNKNOWN", confidence=float("nan"))
    assert p1.confidence == 1.0
    assert p2.confidence == 0.0
    assert p3.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════════
# Snapshot-only collapses to UNKNOWN
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"dxy": 100.0, "us10y": 4.0, "silver": 30.0},  # snapshot, no history
        {"macro": {"dxy": 100.0}},  # nested, no history
        "raw string",
        42,
    ],
)
def test_snapshot_only_collapses_to_unknown(payload: Any) -> None:
    out = compute_regime_posterior(payload, now=T0)
    assert out.state == "UNKNOWN"
    assert out.reason in (
        "snapshot_only_no_history",
        "macro_payload_not_dict",
        "no_macro_values_found",
    )


# ══════════════════════════════════════════════════════════════════════════
# Direction classification
# ══════════════════════════════════════════════════════════════════════════


def test_usd_trending_up_with_confirming_silver() -> None:
    """DXY rising sharply + silver falling → USD_TRENDING_UP, high confidence."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _rising_series(100.0, 0.01, 8),     # +1% per step
        "us10y": _flat_series(4.0, 8),
        "silver": _falling_series(30.0, 0.012, 8),  # silver falls with USD
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "USD_TRENDING_UP"
    assert out.confidence >= 0.6
    assert out.drivers["dxy"] == "UP"
    assert out.drivers["silver"] == "DOWN"
    assert "SILVER_CONFIRMS" in out.reason_codes


def test_rates_rising_with_confirming_silver() -> None:
    """US10Y rising sharply + silver falling → RATES_RISING."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _flat_series(100.0, 8),                 # USD flat
        "us10y": _rising_series(4.0, 0.005, 8),        # ~+0.5%/step
        "silver": _falling_series(30.0, 0.01, 8),
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "RATES_RISING"
    assert out.confidence >= 0.7
    assert out.drivers["us10y"] == "UP"


def test_mixed_when_usd_and_rates_conflict() -> None:
    """DXY rising + US10Y falling → MIXED (drivers disagree)."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _rising_series(100.0, 0.01, 8),
        "us10y": _falling_series(4.0, 0.005, 8),
        "silver": _flat_series(30.0, 8),
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "MIXED"
    assert out.drivers["dxy"] == "UP"
    assert out.drivers["us10y"] == "DOWN"
    assert "CONFLICT" in out.reason_codes


def test_all_drivers_flat_returns_unknown() -> None:
    """No directional movement anywhere → UNKNOWN with low confidence."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _flat_series(100.0, 8),
        "us10y": _flat_series(4.0, 8),
        "silver": _flat_series(30.0, 8),
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "UNKNOWN"
    assert out.reason == "all_drivers_flat_or_unknown"
    assert "FLAT_DRIVERS" in out.reason_codes


def test_short_history_falls_back_to_snapshot_unknown() -> None:
    """History shorter than MIN_HISTORY_POINTS must not be trusted → UNKNOWN."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {"dxy": [100.0, 101.0]}  # only 2 points (< MIN_HISTORY_POINTS)
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "UNKNOWN"
    assert out.reason == "snapshot_only_no_history"


# ══════════════════════════════════════════════════════════════════════════
# Wire shape + thresholds + standalone importability
# ══════════════════════════════════════════════════════════════════════════


def test_to_dict_emits_canonical_wire_shape() -> None:
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _rising_series(100.0, 0.01, 8),
        "us10y": _flat_series(4.0, 8),
        "silver": _falling_series(30.0, 0.012, 8),
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    wire = out.to_dict()
    assert wire["state"] == "USD_TRENDING_UP"
    assert isinstance(wire["confidence"], float)
    assert 0.0 <= wire["confidence"] <= 1.0
    assert isinstance(wire["drivers"], dict)
    assert isinstance(wire["evidence"], dict)
    assert "slopes" in wire["evidence"]
    assert wire["observed_at"]
    assert wire["provenance"] in ("OBSERVED", "DERIVED", "UNKNOWN")


def test_module_is_importable_standalone() -> None:
    """The M2 module must be importable without pulling in orchestrator."""
    import importlib

    import forecast.m2 as mod

    importlib.reload(mod)
    assert callable(mod.compute_regime_posterior)
    assert mod.RegimePosterior is not None
    assert "USD_TRENDING_UP" in mod.M2_REGIME_STATES
    assert "MIXED" in mod.M2_REGIME_STATES


def test_thresholds_are_positive_and_min_history_is_at_least_two() -> None:
    assert DEFAULT_USD_TREND_THRESHOLD > 0
    assert DEFAULT_US10Y_TREND_THRESHOLD > 0
    assert DEFAULT_SILVER_TREND_THRESHOLD > 0
    assert MIN_HISTORY_POINTS >= 2


def test_usd_trending_down_with_silver_rising() -> None:
    """Symmetric case: DXY falling + silver rising → USD_TRENDING_DOWN."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _falling_series(100.0, 0.01, 8),
        "us10y": _flat_series(4.0, 8),
        "silver": _rising_series(30.0, 0.012, 8),
    }
    out = compute_regime_posterior(macro, history=history, now=T0)
    assert out.state == "USD_TRENDING_DOWN"
    assert out.confidence >= 0.6


def test_custom_thresholds_change_classification() -> None:
    """Loosening the USD threshold must flip a borderline series to UP."""
    macro = {"dxy": 100.0, "us10y": 4.0, "silver": 30.0}
    history = {
        "dxy": _rising_series(100.0, 0.0005, 8),  # very small rise
        "us10y": _flat_series(4.0, 8),
        "silver": _flat_series(30.0, 8),
    }
    # Default threshold (0.0015) → still FLAT
    default = compute_regime_posterior(macro, history=history, now=T0)
    assert default.drivers["dxy"] == "FLAT"

    # Loosen to 0.0001 → UP
    loose = compute_regime_posterior(
        macro, history=history, now=T0, usd_threshold=0.0001
    )
    assert loose.drivers["dxy"] == "UP"
