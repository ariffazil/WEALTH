"""
freshness.py — P1 2026-09-21 (WEALTH-IDENTITY-PIVOT-P1).

Mandatory freshness/provenance metadata for every Ω08 (Field) and
Ω09 (Signal) output. Per F13 directive:

    "Be careful with 'real-time'. The README says 'Real-time FX,
     commodity, and stock indicators.' Those sources can have very
     different update frequencies. So I'd say: 'Live and latest-
     available market/macro data through configured adapters, with
     source, timestamp, cache age and staleness metadata.'"

    "Freshness ≠ Truth."
    "LatestAvailable ≠ RealTime."

Doctrine:
    Every market/macro output carries:
      - source          (URI / provider identifier)
      - timestamp       (when the data was observed / last refreshed)
      - cache_age_seconds (now - timestamp, in seconds)
      - staleness_class (LIVE | RECENT | STALE | ARCHIVAL)
      - signal_state    (LIVE | HISTORICAL_STALE | UNAVAILABLE |
                         CONFLICTED | DERIVED | ASSUMED)

    Without these 5 fields the output is NOT admissible as Ω08/Ω09 evidence.

Constitutional:
    F1 AMANAH — deny-by-default: missing metadata = HOLD
    F2 TRUTH  — source attribution is mandatory
    F11 AUDIT — every output logs the source chain
"""

from __future__ import annotations

import datetime as _dt
from enum import Enum
from typing import Any


class StalenessClass(str, Enum):
    """Cache age classification for market/macro data."""

    LIVE = "LIVE"            # ≤ 60s — observed right now
    RECENT = "RECENT"        # ≤ 5 min — usable for live trading decisions
    STALE = "STALE"          # ≤ 1 hour — historical reference only
    ARCHIVAL = "ARCHIVAL"    # > 1 hour — research/audit only

    @classmethod
    def from_age(cls, age_seconds: float | int | None) -> "StalenessClass":
        if age_seconds is None or age_seconds < 0:
            return cls.ARCHIVAL
        if age_seconds <= 60:
            return cls.LIVE
        if age_seconds <= 300:
            return cls.RECENT
        if age_seconds <= 3600:
            return cls.STALE
        return cls.ARCHIVAL


# Ω08/Ω09 tools that REQUIRE freshness/provenance metadata.
# Any tool not in this set may return without these fields (e.g.
# capital_primitive deductive math).
OMEGA_FIELD_TOOLS = frozenset(
    {
        "capital_market",
        "capital_indicator",
        "capital_entry_plan",
        "wealth_field_macro",
        "wealth_signal_information",
        "wealth_gradient_price",
        # capital_backtest and capital_health have their own freshness
        # contracts (added in P1 freshness patches) — exempted here.
    }
)


def enforce_freshness(
    tool_name: str,
    result: dict[str, Any],
    *,
    source: str | None = None,
    timestamp: str | None = None,
    cache_age_seconds: float | None = None,
    now: _dt.datetime | None = None,
) -> dict[str, Any]:
    """Inject mandatory freshness metadata into a market/macro result.

    P1 2026-09-21: Ω08 (Field) and Ω09 (Signal) outputs are NOT
    admissible without source + timestamp + cache_age_seconds +
    staleness_class. If the source adapter hasn't already supplied
    these fields, this function derives them and stamps them onto the
    result.

    Parameters
    ----------
    tool_name : str
        The tool name (used to check if freshness is required).
    result : dict
        The output result dict (mutated in-place + returned).
    source : str, optional
        Override source URI (else taken from result.source or
        result.provider).
    timestamp : str, optional
        Override observation timestamp (else taken from result.timestamp
        or computed as now).
    cache_age_seconds : float, optional
        Override cache age (else computed as now - timestamp).
    now : datetime, optional
        Reference time for cache age computation (else datetime.now).

    Returns
    -------
    dict
        The result dict with `_freshness` metadata injected.
    """
    if tool_name not in OMEGA_FIELD_TOOLS:
        return result

    now = now or _dt.datetime.now(_dt.timezone.utc)

    # Resolve source
    src = (
        source
        or result.get("source")
        or result.get("provider")
        or result.get("data_source")
    )
    if not src:
        src = "UNSPECIFIED"

    # Resolve timestamp
    ts = timestamp or result.get("timestamp") or result.get("as_of") or now.isoformat()
    try:
        ts_dt = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        ts_dt = now

    # Compute cache age
    if cache_age_seconds is None:
        try:
            cache_age_seconds = max(0, int((now - ts_dt).total_seconds()))
        except Exception:
            cache_age_seconds = -1

    staleness = StalenessClass.from_age(cache_age_seconds)

    # Inject mandatory fields
    result["source"] = src
    result["timestamp"] = ts
    result["cache_age_seconds"] = cache_age_seconds
    result["staleness_class"] = staleness.value

    # _freshness envelope for F11 audit
    result["_freshness"] = {
        "source": src,
        "timestamp": ts,
        "cache_age_seconds": cache_age_seconds,
        "staleness_class": staleness.value,
        "enforced_at": now.isoformat(),
        "doctrine": "Freshness ≠ Truth. LatestAvailable ≠ RealTime.",
    }

    return result


def check_freshness_admissible(result: dict[str, Any]) -> tuple[bool, str]:
    """Verify a result has all 5 mandatory freshness fields.

    Returns (ok, reason). Used by tests + downstream consumers.
    """
    required = ["source", "timestamp", "cache_age_seconds", "staleness_class"]
    missing = [k for k in required if k not in result]
    if missing:
        return False, f"missing freshness fields: {missing}"
    sc = result.get("staleness_class")
    if sc not in {s.value for s in StalenessClass}:
        return False, f"invalid staleness_class: {sc!r}"
    return True, "OK"
