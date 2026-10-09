"""Tests for forecast/event_sentinel.

Contract under test
-------------------
* ``EVENT_RISK_STATES`` is the canonical vocabulary — never an ad-hoc string.
* ``compute_event_risk_state`` is deterministic w.r.t. ``now`` (frozen).
* The state machine is monotone in time-to-event:
    BLOCK_TRADE (≤ block_hours)
   > RESET_FORECAST (≤ horizon_hours)
   > WIDEN_INTERVAL (≤ widen_hours)
   > NORMAL (else, given an elevated-impact next event)
* Malformed input (None, wrong types, empty list) collapses to NO_EVENT_FEED,
  never raises.
* Past-only calendars are observable as NORMAL with reason "all_events_in_past"
  — the sentinel does not invent a "next_event".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from forecast.event_sentinel import (
    DEFAULT_BLOCK_HOURS,
    DEFAULT_FORECAST_HORIZON_HOURS,
    DEFAULT_WIDEN_HOURS,
    EVENT_RISK_STATES,
    EventSentinelState,
    compute_event_risk_state,
)


UTC = timezone.utc
T0 = datetime(2026, 9, 25, 10, 0, 0, tzinfo=UTC)


def _evt(when_offset_hours: float, *, impact: str = "high", label: str = "X") -> dict[str, Any]:
    """Build a calendar event ``offset_hours`` after T0."""
    dt = T0 + timedelta(hours=when_offset_hours)
    return {
        "datetime": dt.isoformat(),
        "impact": impact,
        "event": label,
        "currency": "USD",
    }


# ══════════════════════════════════════════════════════════════════════════
# Vocabulary + helper integrity
# ══════════════════════════════════════════════════════════════════════════


def test_event_risk_vocabulary_is_frozen_set() -> None:
    assert isinstance(EVENT_RISK_STATES, frozenset)
    assert EVENT_RISK_STATES == frozenset(
        {"NORMAL", "WIDEN_INTERVAL", "RESET_FORECAST", "BLOCK_TRADE", "NO_EVENT_FEED"}
    )


def test_compute_event_risk_state_deterministic_with_now() -> None:
    """Same payload + same ``now`` → same verdict."""
    cal = {"events": [_evt(1.0, impact="high")]}
    a = compute_event_risk_state(cal, now=T0)
    b = compute_event_risk_state(cal, now=T0)
    assert a.state == b.state
    assert a.time_to_next_hours == b.time_to_next_hours
    assert a.reason == b.reason


def test_event_sentinel_state_unknown_value_collapses() -> None:
    """A state outside the vocabulary must collapse to NO_EVENT_FEED."""
    s = EventSentinelState(state="GARBAGE", reason="forced")
    assert s.state == "NO_EVENT_FEED"


# ══════════════════════════════════════════════════════════════════════════
# State machine precedence
# ══════════════════════════════════════════════════════════════════════════


def test_block_trade_when_high_impact_within_45_minutes() -> None:
    cal = {"events": [_evt(0.5, impact="high")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "BLOCK_TRADE"
    assert out.time_to_next_hours == pytest.approx(0.5, abs=1e-6)
    assert "BLOCK_TRADE" in out.reason_codes
    assert out.high_impact_count == 1


def test_widen_interval_when_high_impact_within_6_hours_outside_horizon_block() -> None:
    """High-impact event at +3h sits between block (45m) and the 72h horizon
    but within the 6h widen window ⇒ WIDEN_INTERVAL."""
    cal = {"events": [_evt(3.0, impact="high")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "WIDEN_INTERVAL"


def test_reset_forecast_when_high_impact_within_72h_outside_widen_window() -> None:
    """High-impact event at +24h is inside the forecast horizon but outside
    the 6h widen window ⇒ RESET_FORECAST (cone is suspect, must re-baseline)."""
    cal = {"events": [_evt(24.0, impact="high")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "RESET_FORECAST"
    assert out.in_horizon_event is not None


def test_normal_when_high_impact_outside_all_windows() -> None:
    cal = {"events": [_evt(120.0, impact="high")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "NORMAL"
    assert "HIGH_IMPACT_FAR" in out.reason_codes


def test_low_impact_event_does_not_trigger_block_or_widen() -> None:
    """A low-impact event 1h out must NOT block or widen the cone."""
    cal = {"events": [_evt(1.0, impact="low")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "NORMAL"


def test_medium_impact_event_within_horizon_triggers_reset() -> None:
    """Medium-impact events still trigger RESET_FORECAST inside the horizon
    because they may still move the macro tape enough to invalidate the cone."""
    cal = {"events": [_evt(36.0, impact="medium")]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "RESET_FORECAST"
    assert out.medium_impact_count == 1


# ══════════════════════════════════════════════════════════════════════════
# Empty / malformed feed — never raises, always NO_EVENT_FEED
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"events": []},
        {"events": "not-a-list"},
        {"events": [None]},
        {"events": [{"event": "no datetime"}]},
        "raw string",
        42,
    ],
)
def test_malformed_payload_collapses_to_no_event_feed(payload: Any) -> None:
    out = compute_event_risk_state(payload, now=T0)
    assert out.state == "NO_EVENT_FEED"
    assert out.time_to_next_hours is None
    assert out.high_impact_count == 0
    assert out.medium_impact_count == 0


def test_past_only_calendar_is_normal_with_past_only_reason() -> None:
    """A feed whose events are all in the past must NOT invent a next event —
    NORMAL with reason=``all_events_in_past`` is the honest verdict."""
    cal = {"events": [_evt(-24.0), _evt(-48.0)]}
    out = compute_event_risk_state(cal, now=T0)
    assert out.state == "NORMAL"
    assert out.reason == "all_events_in_past"
    assert "PAST_ONLY" in out.reason_codes
    assert out.time_to_next_hours is None


# ══════════════════════════════════════════════════════════════════════════
# Wire shape + standalone importability
# ══════════════════════════════════════════════════════════════════════════


def test_to_dict_emits_canonical_wire_shape() -> None:
    cal = {"events": [_evt(0.5, impact="high")]}
    out = compute_event_risk_state(cal, now=T0)
    wire = out.to_dict()
    assert wire["state"] == "BLOCK_TRADE"
    assert wire["widen_hours"] == DEFAULT_WIDEN_HOURS
    assert wire["block_hours"] == DEFAULT_BLOCK_HOURS
    assert wire["horizon_hours"] == DEFAULT_FORECAST_HORIZON_HOURS
    assert wire["time_to_next_hours"] == pytest.approx(0.5, abs=1e-6)
    assert isinstance(wire["next_event"], dict)
    assert wire["next_event"]["impact"] == "high"
    assert wire["provenance"] == "OBSERVED"
    assert wire["observed_at"]


def test_module_is_importable_standalone() -> None:
    """The sentinel must be importable without pulling in orchestrator."""
    import importlib

    import forecast.event_sentinel as mod

    importlib.reload(mod)
    assert callable(mod.compute_event_risk_state)
    assert mod.EventSentinelState is not None
    assert "BLOCK_TRADE" in mod.EVENT_RISK_STATES


def test_window_thresholds_are_exposed_and_sensible() -> None:
    """block_hours < widen_hours < horizon_hours, all positive."""
    assert 0 < DEFAULT_BLOCK_HOURS < DEFAULT_WIDEN_HOURS < DEFAULT_FORECAST_HORIZON_HOURS


def test_uses_next_event_hint_when_events_list_is_empty() -> None:
    """The endpoint returns a ``next_event`` even when the list is sparse —
    honour the hint if it parses cleanly."""
    payload = {
        "events": [],
        "next_event": _evt(2.0, impact="high"),
    }
    out = compute_event_risk_state(payload, now=T0)
    assert out.state == "WIDEN_INTERVAL"
    assert out.next_event is not None
    assert out.time_to_next_hours == pytest.approx(2.0, abs=1e-6)


def test_short_minute_padding_tolerated() -> None:
    """``11:0:00`` (un-padded minute) is the format the upstream sometimes
    returns; the parser must accept it without losing the row."""
    cal = {
        "events": [
            {
                "datetime": "2026-09-25T11:0:00+00:00",
                "impact": "high",
                "event": "CPI",
            }
        ]
    }
    out = compute_event_risk_state(cal, now=T0)
    assert out.state != "NO_EVENT_FEED"
    assert out.next_event is not None
