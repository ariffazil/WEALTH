"""WEALTH forecast — event sentinel.

Schedules-aware risk filter that consumes the calendar feed from
``/api/gold/calendar`` and emits a discrete ``EVENT_RISK`` state that the
777/888 lanes of the orchestrator MUST consult before approving a trade.

Standalone import — no dependency on the rest of forecast.orchestrator.

    from forecast.event_sentinel import (
        EventSentinelState,
        EVENT_RISK_STATES,
        compute_event_risk_state,
    )

Laws binding this module
------------------------
* NO FAKE EVENTS — every calendar entry must come from a live feed.
* Never invent a "next event" from the current time; if the feed is empty
  or malformed the only admissible verdict is ``NO_EVENT_FEED``.
* ``BLOCK_TRADE`` is an honest signal that the next high-impact event is
  imminent; do not soften it for "user experience".
* ``RESET_FORECAST`` means the next event is *inside* the target forecast
  horizon (+72h) — the cone is suspect and the judge must re-baseline.
* ``WIDEN_INTERVAL`` means an event is within the next widening window
  without being in-horizon — bands must be widened but the cone is still
  admissible. Do not collapse this into NORMAL.
* State transitions are timestamped and carry the evidence; never collapse
  to a Boolean.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

# Public, frozen vocabulary. Importers must match against this set, never
# against string literals (collapses to single source of truth).
EVENT_RISK_STATES = frozenset(
    {
        "NORMAL",
        "WIDEN_INTERVAL",
        "RESET_FORECAST",
        "BLOCK_TRADE",
        "NO_EVENT_FEED",
    }
)

# Default widening/block windows — overridable in compute_event_risk_state.
DEFAULT_WIDEN_HOURS = 6.0       # event within this many hours ⇒ WIDEN_INTERVAL
DEFAULT_BLOCK_HOURS = 0.75      # event within this many hours ⇒ BLOCK_TRADE (45 min)
DEFAULT_FORECAST_HORIZON_HOURS = 72.0  # event inside forecast horizon ⇒ RESET_FORECAST

# Impact taxonomy: only these impacts affect risk state. Anything not in
# this set is treated as a low-impact filler entry.
HIGH_IMPACTS = frozenset({"high"})
MEDIUM_IMPACTS = frozenset({"medium"})


@dataclass
class EventSentinelState:
    """The event-risk verdict emitted by ``compute_event_risk_state``.

    The ``state`` field is the canonical verdict; everything else is
    provenance + the evidence that produced the verdict (APEX invariant 2:
    a claim without provenance is not evidence).
    """

    state: str = "NO_EVENT_FEED"
    widen_hours: float = DEFAULT_WIDEN_HOURS
    block_hours: float = DEFAULT_BLOCK_HOURS
    horizon_hours: float = DEFAULT_FORECAST_HORIZON_HOURS
    next_event: Optional[dict[str, Any]] = None
    time_to_next_hours: Optional[float] = None
    in_horizon_event: Optional[dict[str, Any]] = None
    high_impact_count: int = 0
    medium_impact_count: int = 0
    reason: str = "no_calendar_provided"
    provenance: str = "UNKNOWN"  # OBSERVED | DERIVED | UNKNOWN
    observed_at: str = ""
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in EVENT_RISK_STATES:
            # Collapse an unknown verdict to NO_EVENT_FEED — never silently
            # accept a value outside the vocabulary.
            self.state = "NO_EVENT_FEED"

    def to_dict(self) -> dict[str, Any]:
        """Wire shape for embedding in the orchestration packet."""
        return {
            "state": self.state,
            "widen_hours": self.widen_hours,
            "block_hours": self.block_hours,
            "horizon_hours": self.horizon_hours,
            "next_event": self.next_event,
            "time_to_next_hours": self.time_to_next_hours,
            "in_horizon_event": self.in_horizon_event,
            "high_impact_count": self.high_impact_count,
            "medium_impact_count": self.medium_impact_count,
            "reason": self.reason,
            "provenance": self.provenance,
            "observed_at": self.observed_at,
            "reason_codes": list(self.reason_codes),
        }


# ── Helpers ──────────────────────────────────────────────────────────────


def _to_aware_dt(value: Any, fallback_tz: timezone) -> Optional[datetime]:
    """Best-effort parse to an aware datetime.

    Accepts ISO 8601 strings (with or without offset), epoch seconds, or
    pre-built ``datetime`` instances. Returns None on any failure — the
    caller treats None as "cannot schedule against this entry".
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=fallback_tz)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(float(value), tz=fallback_tz)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    s = value.strip()
    # Normalise separators so we tolerate both "T" and a single space
    # between date and time, and pad short minute fields ("11:0:00" → "11:00:00").
    s_norm = s.replace("T", " ")
    # Pad bare single-digit minutes when the time component is HH:M(:SS).
    time_part = s_norm.split(" ", 1)[1] if " " in s_norm else s_norm
    if ":" in time_part:
        hm = time_part.split(":", 2)
        # Pad minutes.
        if len(hm) >= 2 and hm[1].isdigit() and len(hm[1]) == 1:
            hm[1] = "0" + hm[1]
        # Pad seconds.
        if len(hm) == 3 and hm[2].isdigit() and len(hm[2]) == 1:
            hm[2] = "0" + hm[2]
        s_norm = s_norm.split(" ", 1)[0] + " " + ":".join(hm) if " " in s_norm else ":".join(hm)
    s_norm = s_norm.replace(" ", "T")
    try:
        dt = datetime.fromisoformat(s_norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=fallback_tz)
        return dt
    except ValueError:
        pass
    # Last-resort: trim a trailing 'Z' and retry.
    if s.endswith("Z"):
        try:
            return datetime.fromisoformat(s[:-1] + "+00:00")
        except ValueError:
            return None
    return None


def _normalize_event(raw: dict[str, Any], fallback_tz: timezone) -> Optional[dict[str, Any]]:
    """Lift a calendar entry into a canonical dict with a parsed datetime.

    Returns None if no timestamp is recoverable — the caller drops these.
    """
    if not isinstance(raw, dict):
        return None
    dt = _to_aware_dt(raw.get("datetime"), fallback_tz)
    if dt is None:
        dt = _to_aware_dt(raw.get("date"), fallback_tz)
    if dt is None:
        return None
    impact = str(raw.get("impact") or "").strip().lower() or "unknown"
    return {
        "datetime": dt.isoformat(),
        "timestamp": dt,  # internal — caller uses this for ordering
        "event": str(raw.get("event") or raw.get("title") or ""),
        "currency": str(raw.get("currency") or ""),
        "impact": impact,
        "actual": raw.get("actual"),
        "forecast": raw.get("forecast"),
        "previous": raw.get("previous"),
    }


def _extract_events(payload: Any) -> tuple[list[dict[str, Any]], Optional[dict[str, Any]]]:
    """Pull the events list and the publisher's next_event hint from a payload.

    The endpoint at ``/api/gold/calendar`` returns ``{events: [...], next_event: {...}}``.
    A defensively-written reader accepts either that shape, a bare list, or
    a dict with a single "events"/"data"/"items" key. Anything else returns
    an empty list and no next_event.
    """
    if isinstance(payload, list):
        return list(payload), None
    if not isinstance(payload, dict):
        return [], None
    events_raw: Iterable[Any]
    for key in ("events", "data", "items", "schedule"):
        if key in payload and isinstance(payload[key], list):
            events_raw = payload[key]
            break
    else:
        events_raw = []
    next_hint = payload.get("next_event") if isinstance(payload, dict) else None
    return list(events_raw), next_hint if isinstance(next_hint, dict) else None


# ── Core computation ────────────────────────────────────────────────────


def compute_event_risk_state(
    calendar_payload: Any,
    *,
    now: Optional[datetime] = None,
    widen_hours: float = DEFAULT_WIDEN_HOURS,
    block_hours: float = DEFAULT_BLOCK_HOURS,
    horizon_hours: float = DEFAULT_FORECAST_HORIZON_HOURS,
    fallback_tz: Optional[timezone] = None,
) -> EventSentinelState:
    """Compute the discrete EVENT_RISK state for a calendar payload.

    Parameters
    ----------
    calendar_payload
        The body of ``/api/gold/calendar``. Accepts either the documented
        ``{"events": [...], "next_event": {...}}`` shape or a bare list.
        ``None`` or a non-dict / non-list payload → ``NO_EVENT_FEED``.
    now
        The "current" wall-clock for the computation. Tests pass a frozen
        value; production defaults to ``datetime.now(timezone.utc)``.
    widen_hours
        Time window (hours) inside which an event widens the cone but does
        not yet block. Default 6h.
    block_hours
        Time window (hours) inside which an event blocks trades outright.
        Default 0.75h (45 minutes).
    horizon_hours
        The forecast horizon — any event within this window from ``now``
        triggers ``RESET_FORECAST``. Default 72h.
    fallback_tz
        Timezone applied to events whose timestamp lacks tzinfo. Defaults
        to UTC.

    Returns
    -------
    EventSentinelState
        The verdict plus the evidence. Never raises on malformed input —
        malformed input collapses to ``NO_EVENT_FEED``.
    """
    fallback_tz = fallback_tz or timezone.utc
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=fallback_tz)

    state = EventSentinelState(
        widen_hours=float(widen_hours),
        block_hours=float(block_hours),
        horizon_hours=float(horizon_hours),
    )

    raw_events, next_hint = _extract_events(calendar_payload)
    normalized: list[dict[str, Any]] = []
    for entry in raw_events:
        ne = _normalize_event(entry, fallback_tz)
        if ne is not None:
            normalized.append(ne)

    if not normalized:
        # A publisher's "next_event" hint is useful even when the events list
        # is malformed; honour it only if we can normalise it.
        hint = _normalize_event(next_hint, fallback_tz) if next_hint else None
        if hint is not None:
            normalized.append(hint)

    if not normalized:
        state.state = "NO_EVENT_FEED"
        state.provenance = "UNKNOWN"
        state.reason = "calendar_empty_or_unparseable"
        state.reason_codes.append("NO_EVENT_FEED")
        state.observed_at = now.isoformat()
        return state

    # Categorise impacts and order by time.
    high = [e for e in normalized if e["impact"] in HIGH_IMPACTS]
    medium = [e for e in normalized if e["impact"] in MEDIUM_IMPACTS]
    state.high_impact_count = len(high)
    state.medium_impact_count = len(medium)

    # "Next event" = the earliest future or current event.
    future = [e for e in normalized if e["timestamp"] >= now - timedelta(minutes=1)]
    if not future:
        # All events are in the past. Use the last event as the most recent
        # data point, but the time-to-next is None — declare NORMAL with a
        # "past_only" reason so the observer sees the truth.
        state.state = "NORMAL"
        state.provenance = "OBSERVED"
        state.reason = "all_events_in_past"
        state.reason_codes.append("PAST_ONLY")
        state.observed_at = now.isoformat()
        return state

    future.sort(key=lambda e: e["timestamp"])
    nxt = future[0]
    state.next_event = {k: v for k, v in nxt.items() if k != "timestamp"}
    dt_hours = (nxt["timestamp"] - now).total_seconds() / 3600.0
    state.time_to_next_hours = round(dt_hours, 4)

    in_horizon = [e for e in future if e["timestamp"] <= now + timedelta(hours=horizon_hours)]
    if in_horizon:
        in_horizon.sort(key=lambda e: e["timestamp"])
        ie = in_horizon[0]
        state.in_horizon_event = {k: v for k, v in ie.items() if k != "timestamp"}

    # Decision precedence — BLOCK_TRADE > WIDEN_INTERVAL > RESET_FORECAST > NORMAL.
    # Rationale: a *close* event (within widen window) needs interval widening
    # first; an event further out but still inside the forecast horizon needs
    # the cone re-baselined. BLOCK is the tightest, NORMAL the loosest.
    impact_elevates = nxt["impact"] in HIGH_IMPACTS or nxt["impact"] in MEDIUM_IMPACTS
    is_high = nxt["impact"] in HIGH_IMPACTS

    codes: list[str] = []
    if impact_elevates and dt_hours <= block_hours:
        state.state = "BLOCK_TRADE"
        state.provenance = "OBSERVED"
        state.reason = (
            f"next_event_in_{round(dt_hours * 60, 1)}_min"
            f"_{nxt['impact']}_impact"
        )
        codes.append("BLOCK_TRADE")
        codes.append(f"IMPACT_{nxt['impact'].upper()}")
        codes.append(f"MINUTES_TO_EVENT_{int(dt_hours * 60)}")
    elif impact_elevates and dt_hours <= widen_hours:
        state.state = "WIDEN_INTERVAL"
        state.provenance = "OBSERVED"
        state.reason = (
            f"next_event_in_{round(dt_hours, 2)}h"
            f"_{nxt['impact']}_impact"
        )
        codes.append("WIDEN_INTERVAL")
        codes.append(f"IMPACT_{nxt['impact'].upper()}")
        codes.append(f"HOURS_TO_EVENT_{round(dt_hours, 2)}")
    elif impact_elevates and dt_hours <= horizon_hours:
        state.state = "RESET_FORECAST"
        state.provenance = "OBSERVED"
        state.reason = (
            f"next_event_within_{horizon_hours}h_horizon"
            f"_{nxt['impact']}_impact"
        )
        codes.append("RESET_FORECAST")
        codes.append(f"IMPACT_{nxt['impact'].upper()}")
        codes.append(f"HOURS_TO_EVENT_{round(dt_hours, 2)}")
    else:
        state.state = "NORMAL"
        state.provenance = "OBSERVED"
        if is_high:
            state.reason = f"high_impact_event_{round(dt_hours, 2)}h_outside_widen_window"
            codes.append("HIGH_IMPACT_FAR")
        else:
            state.reason = "no_elevated_event_in_widen_window"
            codes.append("CLEAR")
        codes.append(f"HOURS_TO_NEXT_{round(dt_hours, 2)}")

    state.reason_codes = codes
    state.observed_at = now.isoformat()
    return state


__all__ = [
    "EVENT_RISK_STATES",
    "EventSentinelState",
    "compute_event_risk_state",
    "DEFAULT_WIDEN_HOURS",
    "DEFAULT_BLOCK_HOURS",
    "DEFAULT_FORECAST_HORIZON_HOURS",
]
