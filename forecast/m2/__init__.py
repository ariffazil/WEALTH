"""WEALTH forecast — M2 cross-asset regime detection.

Reads DXY / US10Y / Silver from ``/api/gold/macro`` and emits a discrete
``m2_regime_posterior`` describing the joint direction of the three
instruments that drive XAUUSD. The 111-Regime lane of the orchestrator
consumes this output alongside its own classifier.

Standalone import — no dependency on the rest of forecast.orchestrator.

    from forecast.m2 import (
        RegimePosterior,
        M2_REGIME_STATES,
        compute_regime_posterior,
    )

Laws binding this module
------------------------
* NO FAKE PRICE — every input must come from a live macro feed.
* Without sufficient evidence (single snapshot only), the only admissible
  verdict is ``UNKNOWN``; do not invent a direction from a single quote.
* With one observation per asset and a supplied history, classify the
  trend of each asset from the *slope* of the history. With a single
  snapshot and no history, refuse to commit to a directional label.
* The state name describes the *driver*, not the asset. ``USD_TRENDING_UP``
  means the dollar is rising (bearish for gold); ``RATES_RISING`` means
  US10Y is rising (also bearish for gold). The downstream 111 lane
  combines these into a gold-specific view.
* Posterior confidence ∈ [0, 1] — never set to a value outside the band,
  never lie about evidence strength.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

# Public, frozen vocabulary. Importers must match against this set.
M2_REGIME_STATES = frozenset(
    {
        "USD_TRENDING_UP",
        "USD_TRENDING_DOWN",
        "RATES_RISING",
        "RATES_FALLING",
        "MIXED",
        "UNKNOWN",
    }
)

# Default classification thresholds (fractional slope per step).
# A movement smaller than these is treated as noise and the asset is
# declared "flat" for that input; mixed-flats downgrade the joint state
# to MIXED unless a single driver dominates.
DEFAULT_USD_TREND_THRESHOLD = 0.0015   # 0.15% fractional slope per step on DXY
DEFAULT_US10Y_TREND_THRESHOLD = 0.002  # 0.2% fractional slope per step on US10Y (~8bp on 4%)
DEFAULT_SILVER_TREND_THRESHOLD = 0.005  # 0.5% fractional slope per step on silver

# History window length (number of points) used when caller passes history
# as a list. With fewer points, we fall back to snapshot-only mode.
MIN_HISTORY_POINTS = 3


@dataclass
class RegimePosterior:
    """The M2 regime verdict emitted by ``compute_regime_posterior``.

    ``state`` is the canonical label; ``confidence`` is the evidence-weighted
    posterior probability in [0, 1]; ``drivers`` records the per-asset
    direction (the evidence) so downstream code can audit the verdict.
    """

    state: str = "UNKNOWN"
    confidence: float = 0.0
    drivers: dict[str, str] = field(default_factory=dict)
    # Evidence raw numbers — for audit and review (NEVER silently dropped).
    evidence: dict[str, Any] = field(default_factory=dict)
    provenance: str = "UNKNOWN"  # OBSERVED | DERIVED | UNKNOWN
    reason: str = "no_macro_payload"
    observed_at: str = ""
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in M2_REGIME_STATES:
            self.state = "UNKNOWN"
        # Confidence is a probability — clamp, do not truncate silently.
        try:
            c = float(self.confidence)
        except (TypeError, ValueError):
            c = 0.0
        if c != c:  # NaN
            c = 0.0
        if c < 0.0:
            c = 0.0
        elif c > 1.0:
            c = 1.0
        self.confidence = round(c, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "confidence": self.confidence,
            "drivers": dict(self.drivers),
            "evidence": dict(self.evidence),
            "provenance": self.provenance,
            "reason": self.reason,
            "observed_at": self.observed_at,
            "reason_codes": list(self.reason_codes),
        }


# ── Helpers ──────────────────────────────────────────────────────────────


def _as_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        if f != f:  # NaN
            return None
        return f
    if isinstance(value, str):
        try:
            return float(value.strip())
        except (TypeError, ValueError):
            return None
    return None


def _slope_pct(values: list[float]) -> Optional[float]:
    """Return the average per-step fractional change over a series.

    Uses the simple endpoint-to-endpoint slope normalized by the mean of
    the series, which is robust to a single noisy tick. Returns None if
    the series is too short or has zero/negative mean.
    """
    cleaned = [v for v in values if isinstance(v, (int, float)) and v == v]
    if len(cleaned) < 2:
        return None
    first, last = cleaned[0], cleaned[-1]
    n = len(cleaned) - 1
    mean = sum(cleaned) / len(cleaned)
    if mean <= 0:
        return None
    return (last - first) / (mean * n) if n > 0 else 0.0


def _classify_direction(
    slope_pct: Optional[float],
    threshold: float,
) -> str:
    """Classify a single driver as UP / DOWN / FLAT from a fractional slope."""
    if slope_pct is None:
        return "UNKNOWN"
    if slope_pct > threshold:
        return "UP"
    if slope_pct < -threshold:
        return "DOWN"
    return "FLAT"


def _extract_macro_value(payload: Any, *keys: str) -> Optional[float]:
    """Walk a list of candidate keys, returning the first parseable float."""
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload:
            v = _as_float(payload[key])
            if v is not None:
                return v
    # Nested: payload['macro'] or payload['data']
    for nest_key in ("macro", "data", "snapshot"):
        nested = payload.get(nest_key)
        if isinstance(nested, dict):
            v = _extract_macro_value(nested, *keys)
            if v is not None:
                return v
    return None


def _history_for(
    macro_payload: Any, history: Optional[dict[str, list[float]]], key: str
) -> Optional[list[float]]:
    """Pull a series for ``key`` from explicit history or payload's series block."""
    if isinstance(history, dict):
        series = history.get(key)
        if isinstance(series, list) and series:
            return [float(x) for x in series if isinstance(x, (int, float))]
    if isinstance(macro_payload, dict):
        for series_key in ("history", "series", "values", key + "_history"):
            series = macro_payload.get(series_key)
            if isinstance(series, dict) and isinstance(series.get(key), list):
                return [float(x) for x in series[key] if isinstance(x, (int, float))]
    return None


# ── Core computation ────────────────────────────────────────────────────


def compute_regime_posterior(
    macro_payload: Any,
    *,
    history: Optional[dict[str, list[float]]] = None,
    now: Optional[datetime] = None,
    usd_threshold: float = DEFAULT_USD_TREND_THRESHOLD,
    us10y_threshold: float = DEFAULT_US10Y_TREND_THRESHOLD,
    silver_threshold: float = DEFAULT_SILVER_TREND_THRESHOLD,
) -> RegimePosterior:
    """Compute the discrete M2 regime posterior from a macro snapshot.

    Parameters
    ----------
    macro_payload
        The body of ``/api/gold/macro``. Accepts the documented flat shape
        ``{"dxy": ..., "us10y": ..., "silver": ...}`` or nested under
        ``macro`` / ``data``. ``None`` or non-dict → ``UNKNOWN``.
    history
        Optional ``{"dxy": [..], "us10y": [..], "silver": [..]}`` series.
        Each list is in chronological order (oldest first). When supplied
        and at least ``MIN_HISTORY_POINTS`` long, per-asset slope is
        computed from history; otherwise we fall back to snapshot-only
        mode (which is only sufficient for ``UNKNOWN``).
    now
        The "current" wall-clock for stamping the verdict. Production
        defaults to ``datetime.now(timezone.utc)``; tests pass a frozen
        value.
    usd_threshold
        Fraction-of-DXY movement required to call USD "trending". Default 0.15%.
    us10y_threshold
        Absolute yield movement (in percentage points) required to call
        rates "rising/falling". Default 0.02pp (= 2 bps).
    silver_threshold
        Fraction-of-silver movement required. Default 0.5%.

    Returns
    -------
    RegimePosterior
        The verdict + confidence + per-driver evidence. Never raises on
        malformed input — malformed input collapses to ``UNKNOWN``.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    posterior = RegimePosterior()
    posterior.observed_at = now.isoformat()

    if not isinstance(macro_payload, dict):
        posterior.reason = "macro_payload_not_dict"
        posterior.reason_codes.append("UNKNOWN")
        return posterior

    dxy = _extract_macro_value(macro_payload, "dxy", "DXY", "us_dollar_index")
    us10y = _extract_macro_value(macro_payload, "us10y", "US10Y", "us_10y", "ten_year")
    silver = _extract_macro_value(macro_payload, "silver", "XAGUSD", "xag")

    posterior.evidence = {
        "dxy": dxy,
        "us10y": us10y,
        "silver": silver,
        "timestamp": macro_payload.get("timestamp") if isinstance(macro_payload, dict) else None,
    }

    if dxy is None and us10y is None and silver is None:
        posterior.reason = "no_macro_values_found"
        posterior.reason_codes.append("UNKNOWN")
        return posterior

    # If the caller supplied history for at least one asset, compute slopes.
    drivers: dict[str, str] = {}
    slopes: dict[str, Optional[float]] = {}

    h_dxy = _history_for(macro_payload, history, "dxy")
    h_us10y = _history_for(macro_payload, history, "us10y")
    h_silver = _history_for(macro_payload, history, "silver")

    if isinstance(h_dxy, list) and len(h_dxy) >= MIN_HISTORY_POINTS:
        slopes["dxy"] = _slope_pct(h_dxy)
    if isinstance(h_us10y, list) and len(h_us10y) >= MIN_HISTORY_POINTS:
        slopes["us10y"] = _slope_pct(h_us10y)
    if isinstance(h_silver, list) and len(h_silver) >= MIN_HISTORY_POINTS:
        slopes["silver"] = _slope_pct(h_silver)

    if not slopes:
        # Snapshot-only — refuse to commit to a directional label.
        posterior.state = "UNKNOWN"
        posterior.provenance = "OBSERVED"
        posterior.confidence = 0.0
        posterior.reason = "snapshot_only_no_history"
        posterior.reason_codes.append("SNAPSHOT_ONLY")
        posterior.evidence["slopes"] = None
        return posterior

    posterior.evidence["slopes"] = {k: v for k, v in slopes.items() if v is not None}
    posterior.provenance = "DERIVED"

    # Classify per-asset direction.
    if "dxy" in slopes and slopes["dxy"] is not None:
        drivers["dxy"] = _classify_direction(slopes["dxy"], usd_threshold)
    if "us10y" in slopes and slopes["us10y"] is not None:
        drivers["us10y"] = _classify_direction(slopes["us10y"], us10y_threshold)
    if "silver" in slopes and slopes["silver"] is not None:
        drivers["silver"] = _classify_direction(slopes["silver"], silver_threshold)

    posterior.drivers = drivers

    # Build the joint verdict from per-asset drivers.
    # Precedence: if both USD and rates agree on direction → emit that.
    # If they disagree → MIXED. If only one is known → emit the dominant.
    usd_dir = drivers.get("dxy", "UNKNOWN")
    rates_dir = drivers.get("us10y", "UNKNOWN")
    silver_dir = drivers.get("silver", "UNKNOWN")

    # A single high-confidence driver can dominate, but with two known and
    # one unknown we can still classify as USD or RATES based on what is
    # known. With three unknowns we must say UNKNOWN.
    known = {k: v for k, v in drivers.items() if v in ("UP", "DOWN")}

    if not known:
        # Every known driver is FLAT or UNKNOWN — flat markets do not give
        # us a directional regime label.
        posterior.state = "UNKNOWN"
        posterior.confidence = 0.2
        posterior.reason = "all_drivers_flat_or_unknown"
        posterior.reason_codes.append("FLAT_DRIVERS")
        return posterior

    if usd_dir in ("UP", "DOWN") and rates_dir in ("UP", "DOWN"):
        if usd_dir == "DOWN" and rates_dir == "DOWN":
            # Risk-on gold-friendly — but not in our taxonomy; report MIXED.
            posterior.state = "MIXED"
            posterior.confidence = 0.5
            posterior.reason = "usd_and_rates_both_falling_risk_on"
            posterior.reason_codes.append("USD_DOWN")
            posterior.reason_codes.append("RATES_DOWN")
        elif usd_dir == "UP" and rates_dir == "UP":
            posterior.state = "MIXED"
            posterior.confidence = 0.55
            posterior.reason = "usd_and_rates_both_rising_risk_off"
            posterior.reason_codes.append("USD_UP")
            posterior.reason_codes.append("RATES_UP")
        else:
            # Conflicting USD vs rates — MIXED, low confidence.
            posterior.state = "MIXED"
            posterior.confidence = 0.35
            posterior.reason = "usd_vs_rates_conflict"
            posterior.reason_codes.append("CONFLICT")
        return posterior

    if usd_dir in ("UP", "DOWN"):
        posterior.state = "USD_TRENDING_UP" if usd_dir == "UP" else "USD_TRENDING_DOWN"
        # Higher confidence if silver agrees (silver and DXY should move
        # opposite in the normal regime).
        if silver_dir == ("DOWN" if usd_dir == "UP" else "UP"):
            posterior.confidence = 0.8
            posterior.reason_codes.append("SILVER_CONFIRMS")
        elif silver_dir == usd_dir:
            posterior.confidence = 0.4
            posterior.reason_codes.append("SILVER_DIVERGES")
        else:
            posterior.confidence = 0.65
            posterior.reason_codes.append("SILDER_FLAT_OR_UNKNOWN")
        posterior.reason = f"usd_{usd_dir.lower()}_dominant"
        return posterior

    if rates_dir in ("UP", "DOWN"):
        posterior.state = "RATES_RISING" if rates_dir == "UP" else "RATES_FALLING"
        posterior.confidence = 0.7
        if silver_dir == ("DOWN" if rates_dir == "UP" else "UP"):
            posterior.confidence = 0.85
            posterior.reason_codes.append("SILVER_CONFIRMS")
        elif silver_dir == rates_dir:
            posterior.confidence = 0.4
            posterior.reason_codes.append("SILVER_DIVERGES")
        posterior.reason = f"rates_{rates_dir.lower()}_dominant"
        return posterior

    # Only FLAT/UNKNOWN drivers survived — UNKNOWN.
    posterior.state = "UNKNOWN"
    posterior.confidence = 0.2
    posterior.reason = "no_directional_driver"
    posterior.reason_codes.append("NO_DIRECTION")
    return posterior


# (Helper constants above are the source of truth; no aliasing needed.)


__all__ = [
    "M2_REGIME_STATES",
    "RegimePosterior",
    "compute_regime_posterior",
    "DEFAULT_USD_TREND_THRESHOLD",
    "DEFAULT_US10Y_TREND_THRESHOLD",
    "DEFAULT_SILVER_TREND_THRESHOLD",
    "MIN_HISTORY_POINTS",
]
