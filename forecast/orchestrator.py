"""7-agent forecast orchestration for wealth.gold (schema wealth.gold.orchestration.v1).

Design contract
---------------
Each of the seven agents is a **separate pure-ish function** with a strict
input/output contract. An agent receives a typed input record and returns a
typed output record; it never reads global state except through the injected
``client`` (data access) and explicit arguments. This makes every hop
auditable, testable in isolation, and swappable.

Pipeline (sequential, each hop receiptable):

    000 Integrity   read  /api/gold/ticker + /api/gold/apex + /api/gold/macro
                          + /api/gold/forecast  →  validated InputBundle
    111 Regime      InputBundle           →  RegimeState
    333 Forecast    InputBundle + Regime  →  HorizonSet (P10/P25/P50/P75/P90)
    555 Calibration InputBundle + Horizon →  CalibrationState (SHADOW default)
    777 Translator  Regime + Horizon + Cal →  TranslatorOutput (stance candidates)
    888 Judge       all                    →  JudgeVerdict (ACT/WAIT/HOLD/BLOCKED)
    999 Witness     all                    →  WitnessReceipt (VAULT999 append)

Non-negotiables enforced in code (not prose):
  * NO FAKE OHLC. The only price path used is the live cone returned by the
    existing forecast engine. If the endpoint is unreachable the pipeline
    returns BLOCKED, never a synthesised path.
  * Default status is ``SHADOW``: ``human_confirmation_required=True`` and
    ``execution_enabled=False`` on every governed output until an F13-ratified
    calibration + authorization event flips them.
  * Importable, never run-on-load. ``run_orchestration()`` must be called.
  * Does not modify anything under /root/WEALTH/wealth_core/.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# New in this revision: event sentinel + M2 cross-asset regime detection.
# Standalone-importable — see forecast/event_sentinel/__init__.py and
# forecast/m2/__init__.py for the full contract.
from .event_sentinel import (
    EVENT_RISK_STATES,
    DEFAULT_BLOCK_HOURS as _EVT_BLOCK_HOURS,
    DEFAULT_FORECAST_HORIZON_HOURS as _EVT_HORIZON_HOURS,
    DEFAULT_WIDEN_HOURS as _EVT_WIDEN_HOURS,
    EventSentinelState,
    compute_event_risk_state as _compute_event_risk_state,
)
from .m2 import (
    M2_REGIME_STATES,
    DEFAULT_US10Y_TREND_THRESHOLD as _M2_US10Y_THRESHOLD,
    DEFAULT_USD_TREND_THRESHOLD as _M2_USD_THRESHOLD,
    DEFAULT_SILVER_TREND_THRESHOLD as _M2_SILVER_THRESHOLD,
    MIN_HISTORY_POINTS as _M2_MIN_HISTORY,
    RegimePosterior,
    compute_regime_posterior as _compute_regime_posterior,
)

# ── Constants ────────────────────────────────────────────────────────────

MYT = timezone(timedelta(hours=8))
SCHEMA = "wealth.gold.orchestration.v1"
STATUS_SHADOW = "SHADOW"

# Live federation surface. Overridable for tests / other hosts.
DEFAULT_BASE_URL = os.getenv("WEALTH_GOLD_API", "http://localhost:3456")
DEFAULT_TIMEOUT = float(os.getenv("WEALTH_GOLD_TIMEOUT", "12"))

# VAULT999 receipts directory (witness lane).
VAULT999_RECEIPTS = Path(
    os.getenv("VAULT999_RECEIPTS_DIR", "/root/AAA/VAULT999/receipts")
)

# Target horizons in hours. The upstream cone is a *daily* path (index 0 = D+1),
# so +24h → index 1, +48h → index 2, +72h → index 3.
TARGET_HORIZON_HOURS: tuple[int, ...] = (24, 48, 72)

VALID_REGIMES = frozenset(
    {
        "COMPRESSION",
        "EXPANSION",
        "TRENDING",
        "RANGING",
        "TRANSITION",
        "EXHAUSTION",
        "UNKNOWN",
    }
)

VALID_VERDICTS = frozenset({"ACT", "WAIT", "HOLD", "BLOCKED"})

# Round-trip cost assumption for p_up_after_cost (XAUUSD spread + slippage).
# Conservative, sourced from the venue assumption; exposed so the caller can
# override and so the number is never silently baked into a claim.
DEFAULT_ROUND_TRIP_COST_BPS = 6.0


# ══════════════════════════════════════════════════════════════════════════
# TYPED CONTRACTS — one dataclass per agent hop (strict input/output)
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class AgentEnvelope:
    """Common provenance wrapper every agent output carries.

    A claim without provenance is not evidence (APEX invariant 2).
    """

    agent: str
    tier: str
    schema: str = SCHEMA
    observed_at: str = ""
    provenance: str = "OBSERVED"  # OBSERVED | MEASURED | DERIVED | UNKNOWN
    ok: bool = True
    error: Optional[str] = None

    def stamp(self) -> "AgentEnvelope":
        self.observed_at = datetime.now(MYT).isoformat()
        return self


def _stamp_envelope(host: Any) -> Any:
    """Stamp the inner AgentEnvelope of any agent result and return the host.

    Each agent output dataclass carries an `envelope: AgentEnvelope`. The
    observed_at is recorded on the envelope, not the host, so the host
    dataclass need not define its own stamp method (keeps the data
    contracts frozen and dataclasses pure).
    """
    env = getattr(host, "envelope", None)
    if env is not None and hasattr(env, "stamp"):
        env.stamp()
    return host


# ── 000 Integrity ────────────────────────────────────────────────────────


@dataclass
class InputBundle:
    """000 output: validated live inputs from wealth.gold endpoints."""

    envelope: AgentEnvelope
    ticker: dict[str, Any] = field(default_factory=dict)
    apex: dict[str, Any] = field(default_factory=dict)
    macro: dict[str, Any] = field(default_factory=dict)
    forecast: dict[str, Any] = field(default_factory=dict)
    # Event sentinel + M2 regime additions. These are derived from the
    # inputs above by the 000 agent; downstream lanes read them from the
    # bundle so they never need to re-fetch the calendar / history feed.
    calendar: dict[str, Any] = field(default_factory=dict)
    event_risk: EventSentinelState = field(
        default_factory=lambda: EventSentinelState(
            state="NO_EVENT_FEED", reason="not_evaluated"
        )
    )
    m2_regime: RegimePosterior = field(
        default_factory=lambda: RegimePosterior(
            state="UNKNOWN", reason="not_evaluated"
        )
    )
    m2_history: dict[str, list[float]] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.envelope.ok)


# ── 111 Regime ───────────────────────────────────────────────────────────


@dataclass
class RegimeState:
    """111 output: classified regime + the evidence that produced it."""

    envelope: AgentEnvelope
    regime: str = "UNKNOWN"
    confidence: float = 0.0
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.regime not in VALID_REGIMES:
            self.regime = "UNKNOWN"


# ── 333 Forecast ─────────────────────────────────────────────────────────


@dataclass
class Horizon:
    """A single quantile tuple at one horizon. All five quantiles required."""

    offset_hours: int
    timestamp: str
    p10: Optional[float]
    p25: Optional[float]
    p50: Optional[float]
    p75: Optional[float]
    p90: Optional[float]
    p_up_after_cost: Optional[float] = None

    def has_full_distribution(self) -> bool:
        return all(
            v is not None
            for v in (self.p10, self.p25, self.p50, self.p75, self.p90)
        )


@dataclass
class HorizonSet:
    """333 output: the quantile distribution across target horizons."""

    envelope: AgentEnvelope
    horizons: list[Horizon] = field(default_factory=list)
    spot: Optional[float] = None
    basis: dict[str, Any] = field(default_factory=dict)
    upstream_schema: Optional[str] = None


# ── 555 Calibration ──────────────────────────────────────────────────────


@dataclass
class CalibrationState:
    """555 output: calibration status. SHADOW until walk-forward exists."""

    envelope: AgentEnvelope
    calibration_state: str = STATUS_SHADOW
    baseline: str = "ATR_DRIFT_CONE"
    pinball_skill: Optional[float] = None
    coverage: Optional[float] = None
    brier_skill: Optional[float] = None
    reason: str = "no_walk_forward_harness"


# ── 777 Translator ───────────────────────────────────────────────────────


@dataclass
class StanceCandidate:
    stance: str  # LONG | SHORT | FLAT | SAVE | WAIT
    reason_codes: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class TranslatorOutput:
    """777 output: human-decision candidates derived from the distribution."""

    envelope: AgentEnvelope
    trade_72h: StanceCandidate = field(
        default_factory=lambda: StanceCandidate(stance="FLAT")
    )
    physical_saving: StanceCandidate = field(
        default_factory=lambda: StanceCandidate(stance="WAIT")
    )


# ── 888 Judge ────────────────────────────────────────────────────────────


@dataclass
class JudgeVerdict:
    """888 output: final verdict. Default HOLD. May not self-authorize."""

    envelope: AgentEnvelope
    verdict: str = "HOLD"
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.verdict not in VALID_VERDICTS:
            self.verdict = "HOLD"


# ── 999 Witness ──────────────────────────────────────────────────────────


@dataclass
class WitnessReceipt:
    """999 output: the VAULT999 receipt for this orchestration run."""

    envelope: AgentEnvelope
    receipt_id: str = ""
    receipt_uri: str = ""
    written: bool = False
    trace_id: str = ""
    digest: str = ""


# ── Top-level result ─────────────────────────────────────────────────────


@dataclass
class OrchestrationResult:
    """The full governed packet emitted by run_orchestration()."""

    envelope: AgentEnvelope
    status: str = STATUS_SHADOW
    asset: str = "XAUUSD"
    forecast_id: str = ""
    forecast_origin: str = ""
    issued_at: str = ""
    regime: RegimeState | None = None
    horizons: list[Horizon] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    governance: dict[str, Any] = field(default_factory=dict)
    verdict: str = "HOLD"
    trace_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    # Additive (v1.1) — event sentinel + M2 cross-asset regime.
    event_risk_state: str = "NO_EVENT_FEED"
    m2_regime_posterior: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Emit the exact wealth.gold.orchestration.v1 wire shape."""
        return {
            "schema": SCHEMA,
            "forecast_id": self.forecast_id,
            "status": self.status,
            "asset": self.asset,
            "forecast_origin": self.forecast_origin,
            "issued_at": self.issued_at,
            "regime": {
                "state": self.regime.regime if self.regime else "UNKNOWN",
                "confidence": self.regime.confidence if self.regime else 0.0,
                "evidence": self.regime.evidence if self.regime else {},
            },
            "horizons": [asdict(h) for h in self.horizons],
            "validation": self.validation,
            "outputs": self.outputs,
            "governance": self.governance,
            "verdict": self.verdict,
            "trace_id": self.trace_id,
            # Schema v1.1 additions (top-level for downstream consumers).
            "event_risk_state": self.event_risk_state,
            "m2_regime_posterior": dict(self.m2_regime_posterior or {}),
        }


# ══════════════════════════════════════════════════════════════════════════
# DATA ACCESS — thin client, injectable so tests never hit the network
# ══════════════════════════════════════════════════════════════════════════


class GoldAPIClient:
    """Read-only client for the live wealth.gold surface (localhost:3456)."""

    def __init__(
        self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "WEALTH-Forecast/1.0"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError(f"unexpected payload type from {path}: {type(data)}")
        return data

    def ticker(self) -> dict[str, Any]:
        return self._get_json("/api/gold/ticker")

    def apex(self) -> dict[str, Any]:
        return self._get_json("/api/gold/apex")

    def macro(self) -> dict[str, Any]:
        return self._get_json("/api/gold/macro")

    def calendar(self) -> dict[str, Any]:
        return self._get_json("/api/gold/calendar")

    def forecast(self, horizon_days: int = 30) -> dict[str, Any]:
        return self._get_json(f"/api/gold/forecast?horizon={horizon_days}")

    def history(self, interval: str = "1d") -> dict[str, Any]:
        return self._get_json(f"/api/gold/history?interval={interval}")


# ══════════════════════════════════════════════════════════════════════════
# AGENT 000 — INTEGRITY
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : client (GoldAPIClient)
#   OUT: InputBundle
#   FAIL MODE: partial inputs recorded in .missing; envelope.ok=False only
#              when the *forecast* path is unavailable (no path → no forecast).
# ══════════════════════════════════════════════════════════════════════════


def AGENT_000_Integrity(
    client: Any,
    *,
    m2_history: Optional[dict[str, list[float]]] = None,
    now: Optional[datetime] = None,
    widen_hours: float = _EVT_WIDEN_HOURS,
    block_hours: float = _EVT_BLOCK_HOURS,
    horizon_hours: float = _EVT_HORIZON_HOURS,
) -> InputBundle:
    """Read + validate the live inputs. Never synthesises missing data.

    New in v1.1:
      * ``client.calendar()`` is read best-effort and recorded in
        ``bundle.calendar`` / ``bundle.sources['calendar']``.
      * Event sentinel + M2 regime are *derived* from those inputs and
        attached to the bundle, so downstream lanes can read them without
        re-fetching.
      * ``m2_history`` lets the caller pass a pre-collected history of
        DXY/US10Y/Silver (for unit tests and offline replays). Production
        runs leave it None and accept the snapshot-only M2 verdict.
    """
    env = AgentEnvelope(agent="000", tier="000-INTEGRITY", provenance="OBSERVED")
    bundle = InputBundle(envelope=env)

    readers = {
        "ticker": client.ticker,
        "apex": client.apex,
        "macro": client.macro,
        "forecast": client.forecast,
    }
    for name, fn in readers.items():
        try:
            data = fn()
            setattr(bundle, name, data if isinstance(data, dict) else {})
            bundle.sources[name] = getattr(client, "base_url", "unknown")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError,
                json.JSONDecodeError) as exc:  # noqa: PERF203
            bundle.missing.append(name)
            bundle.sources[name] = f"UNAVAILABLE: {type(exc).__name__}"

    # Calendar read — best-effort. A missing calendar is NEVER a blocker
    # for the integrity gate (the cone is still the load-bearing input),
    # but it IS a meaningful event_risk verdict (NO_EVENT_FEED).
    if hasattr(client, "calendar"):
        try:
            data = client.calendar()
            if isinstance(data, dict):
                bundle.calendar = data
                bundle.sources["calendar"] = getattr(client, "base_url", "unknown")
            else:
                bundle.missing.append("calendar")
                bundle.sources["calendar"] = "UNAVAILABLE: unexpected_payload"
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError,
                json.JSONDecodeError) as exc:  # noqa: PERF203
            bundle.missing.append("calendar")
            bundle.sources["calendar"] = f"UNAVAILABLE: {type(exc).__name__}"
    else:
        # Stub clients in the test suite may not implement calendar().
        # Don't penalise integrity for that — just mark the source absent.
        bundle.sources["calendar"] = "NO_CLIENT_METHOD"

    # Derive event_risk from the calendar payload (or NO_EVENT_FEED).
    bundle.event_risk = _compute_event_risk_state(
        bundle.calendar,
        now=now,
        widen_hours=widen_hours,
        block_hours=block_hours,
        horizon_hours=horizon_hours,
    )

    # Derive M2 regime posterior from macro + (optional) history.
    if isinstance(m2_history, dict) and m2_history:
        bundle.m2_history = {
            k: [float(x) for x in v if isinstance(x, (int, float))]
            for k, v in m2_history.items()
            if isinstance(v, list)
        }
    bundle.m2_regime = _compute_regime_posterior(
        bundle.macro,
        history=bundle.m2_history or None,
        now=now,
    )

    # Integrity gate: without a forecast cone there is no quantile path, and
    # this layer is forbidden from inventing one.
    cone = bundle.forecast.get("cone") if isinstance(bundle.forecast, dict) else None
    if not isinstance(cone, dict) or not cone.get("t"):
        env.ok = False
        env.error = "forecast_cone_unavailable"
        env.provenance = "UNKNOWN"
    elif bundle.missing:
        # Partial degradation is allowed but must be declared.
        env.provenance = "OBSERVED_PARTIAL"

    return _stamp_envelope(bundle)


# ══════════════════════════════════════════════════════════════════════════
# AGENT 111 — REGIME
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : InputBundle
#   OUT: RegimeState  (regime ∈ VALID_REGIMES, confidence ∈ [0,1])
#   RULE: classification is DERIVED from observed ticker/apex/forecast values.
#         When the inputs are too thin to distinguish, say TRANSITION/UNKNOWN
#         rather than guessing a confident label.
# ══════════════════════════════════════════════════════════════════════════


def AGENT_111_Regime(bundle: InputBundle) -> RegimeState:
    """Classify the market regime from observed values only.

    v1.1: the M2 cross-asset regime posterior is layered into the evidence
    block as ``m2_regime``. The 111 lane does NOT take direction from it —
    its own label still derives from observed price/EMA/ATR — but it
    reports the M2 state alongside so the 777 translator and 888 judge
    can see both views in one place.
    """
    env = AgentEnvelope(
        agent="111", tier="111-REGIME", provenance="DERIVED"
    )
    if not bundle.ok:
        env.ok = False
        env.error = "integrity_gate_failed"
        return RegimeState(envelope=env, regime="UNKNOWN", confidence=0.0).stamp()  # type: ignore[attr-defined]

    ticker = bundle.ticker or {}
    apex = bundle.apex or {}
    basis = (bundle.forecast or {}).get("basis", {}) or {}

    def _f(*cands: Any) -> Optional[float]:
        for c in cands:
            if isinstance(c, (int, float)) and not isinstance(c, bool):
                return float(c)
        return None

    price = _f(basis.get("close"), ticker.get("price"), apex.get("price"))
    atr = _f(basis.get("atr14"), apex.get("atr_14"))
    ema20 = _f(basis.get("ema20"), ticker.get("ema20"), apex.get("ema_20"))
    ema50 = _f(basis.get("ema50"), ticker.get("ema50"), apex.get("ema_50"))
    ema200 = _f(basis.get("ema200"), ticker.get("ema200"), apex.get("ema_200"))
    rsi = _f(basis.get("rsi"), ticker.get("rsi"), apex.get("rsi_14"))
    slope = _f(basis.get("slope_per_day"))

    evidence: dict[str, Any] = {
        "price": price,
        "atr14": atr,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "rsi": rsi,
        "slope_per_day": slope,
        "apex_state": apex.get("state"),
        "volatility_regime": apex.get("volatility_regime"),
        "upstream_regime": basis.get("regime"),
        # v1.1: M2 cross-asset evidence is layered here. The 111 label
        # remains derived from price/EMA/ATR; M2 is observational context.
        "m2_regime": (
            getattr(bundle, "m2_regime", None).to_dict()
            if getattr(bundle, "m2_regime", None) is not None
            else None
        ),
        "event_risk_state": (
            getattr(bundle, "event_risk", None).state
            if getattr(bundle, "event_risk", None) is not None
            else None
        ),
    }

    # Insufficient evidence → declare ignorance, do not invent a label.
    if price is None or atr is None or atr <= 0:
        env.ok = True
        env.provenance = "DERIVED_LOW_EVIDENCE"
        return RegimeState(
            envelope=env,
            regime="UNKNOWN",
            confidence=0.1,
            evidence={**evidence, "reason": "insufficient_evidence"},
        ).stamp()  # type: ignore[attr-defined]

    atr_pct = atr / price if price else 0.0
    ema_spread = (abs(ema20 - ema50) / price) if (ema20 and ema50 and price) else None
    above200 = (price - ema200) if ema200 else None
    dist200_pct = (above200 / price) if (above200 is not None and price) else None

    reason_codes: list[str] = []
    regime = "RANGING"
    confidence = 0.3

    # Trend strength: EMA20 vs EMA50 separation scaled by ATR.
    trend_strong = (
        ema_spread is not None
        and atr_pct > 0
        and (ema_spread / atr_pct) > 0.5
    )
    vol_regime = str(apex.get("volatility_regime") or "").lower()

    if trend_strong:
        regime = "TRENDING"
        direction = "UP" if (ema20 or 0) > (ema50 or 0) else "DOWN"
        reason_codes.append(f"ema20_vs_ema50_{direction}")
        confidence = min(0.85, 0.5 + (ema_spread or 0) * 8)
        # EXHAUSTION: trend intact but RSI at an extreme and price stretched
        # far from the long mean — the move is late, not fresh.
        if rsi is not None and (rsi >= 72 or rsi <= 28):
            stretched = dist200_pct is not None and abs(dist200_pct) > 3 * atr_pct
            if stretched:
                regime = "EXHAUSTION"
                reason_codes.append("rsi_extreme_plus_stretch_from_ema200")
                confidence = min(0.8, confidence)
    elif atr_pct > 0.02:
        regime = "EXPANSION"
        reason_codes.append("atr_pct_above_2pct")
        confidence = min(0.75, 0.4 + atr_pct * 10)
    elif atr_pct < 0.006:
        regime = "COMPRESSION"
        reason_codes.append("atr_pct_below_0p6pct")
        confidence = 0.55
    else:
        # Bounded, directionless activity: separated means but weak trend,
        # or a normal-vol chop.
        if vol_regime in ("high", "elevated"):
            regime = "TRANSITION"
            reason_codes.append("volatility_regime_elevated_without_trend")
            confidence = 0.35
        else:
            regime = "RANGING"
            reason_codes.append("ema_spread_within_half_atr")
            confidence = 0.5

    evidence["atr_pct"] = round(atr_pct, 6)
    evidence["ema_spread_pct"] = round(ema_spread, 6) if ema_spread is not None else None
    evidence["dist_ema200_pct"] = (
        round(dist200_pct, 6) if dist200_pct is not None else None
    )
    evidence["reason_codes"] = reason_codes

    return RegimeState(
        envelope=env, regime=regime, confidence=round(confidence, 4), evidence=evidence
    ).stamp()  # type: ignore[attr-defined]


# ══════════════════════════════════════════════════════════════════════════
# AGENT 333 — FORECAST
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : InputBundle, RegimeState
#   OUT: HorizonSet  (one Horizon per TARGET_HORIZON_HOURS, always 3)
#   RULE: quantiles come from the upstream cone verbatim. No synthetic OHLC,
#         no interpolation of a missing point, no fill-forward of a gap.
#         p_up_after_cost is DERIVED (P(price > spot + cost)) using a normal
#         approximation on the cone's own band width — explicitly labelled.
# ══════════════════════════════════════════════════════════════════════════


def _normal_cdf(x: float) -> float:
    """Standard normal CDF via erf — stdlib only."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def AGENT_333_Forecast(
    bundle: InputBundle,
    regime: RegimeState,
    cost_bps: float = DEFAULT_ROUND_TRIP_COST_BPS,
) -> HorizonSet:
    """Extract the quantile path at +24h/+48h/+72h from the live cone."""
    env = AgentEnvelope(
        agent="333", tier="333-FORECAST", provenance="OBSERVED_UPSTREAM"
    )
    if not bundle.ok:
        env.ok = False
        env.error = "integrity_gate_failed"
        return HorizonSet(envelope=env).stamp()  # type: ignore[attr-defined]

    forecast = bundle.forecast or {}
    cone = forecast.get("cone") or {}
    basis = forecast.get("basis") or {}

    t = cone.get("t") or []
    p10s = cone.get("p10") or []
    p25s = cone.get("p25") or []
    p50s = cone.get("p50") or []
    p75s = cone.get("p75") or []
    p90s = cone.get("p90") or []

    spot = basis.get("close")
    if not isinstance(spot, (int, float)):
        ticker_price = (bundle.ticker or {}).get("price")
        spot = ticker_price if isinstance(ticker_price, (int, float)) else None

    horizons: list[Horizon] = []
    generated_at = forecast.get("generated_at") or datetime.now(MYT).isoformat()

    for hours in TARGET_HORIZON_HOURS:
        # Daily cone → index 1 for +24h, 2 for +48h, 3 for +72h.
        idx = hours // 24
        if idx >= len(t) or idx >= len(p50s):
            # Upstream cannot reach this horizon. Emit the slot with nulls and
            # a reason — never a guessed number (NO FAKE OHLC).
            horizons.append(
                Horizon(
                    offset_hours=hours,
                    timestamp="",
                    p10=None,
                    p25=None,
                    p50=None,
                    p75=None,
                    p90=None,
                    p_up_after_cost=None,
                )
            )
            continue

        def _at(seq: list[Any], i: int) -> Optional[float]:
            try:
                v = seq[i]
                return float(v) if isinstance(v, (int, float)) else None
            except (IndexError, TypeError, ValueError):
                return None

        p10 = _at(p10s, idx)
        p25 = _at(p25s, idx)
        p50 = _at(p50s, idx)
        p75 = _at(p75s, idx)
        p90 = _at(p90s, idx)

        # Timestamp: prefer the cone's own date; fall back to arithmetic on
        # the issue stamp (still OBSERVED-derived, never invented OHLC).
        ts = str(t[idx])
        ts_iso = ts
        if ts and "T" not in ts:
            try:
                ts_iso = f"{ts}T{generated_at[11:19]}+08:00"
            except Exception:  # pragma: no cover - defensive
                ts_iso = ts

        # p_up_after_cost — probability the +h price exceeds spot plus
        # round-trip cost. Derived from the cone's own p25/p75 as the sigma
        # proxy (IQR/1.349 ≈ σ for a normal), so it inherits the upstream
        # distribution rather than assuming an external vol.
        p_up: Optional[float] = None
        if (
            spot is not None
            and spot > 0
            and p25 is not None
            and p75 is not None
            and p75 > p25
            and p50 is not None
        ):
            sigma = (p75 - p25) / 1.349
            threshold = spot * (1.0 + cost_bps / 10000.0)
            if sigma > 0:
                p_up = round(1.0 - _normal_cdf((threshold - p50) / sigma), 4)

        horizons.append(
            Horizon(
                offset_hours=hours,
                timestamp=ts_iso,
                p10=p10,
                p25=p25,
                p50=p50,
                p75=p75,
                p90=p90,
                p_up_after_cost=p_up,
            )
        )

    env.provenance = "OBSERVED_UPSTREAM"
    hs = HorizonSet(
        envelope=env,
        horizons=horizons,
        spot=float(spot) if isinstance(spot, (int, float)) else None,
        basis={
            "close": basis.get("close"),
            "atr14": basis.get("atr14"),
            "slope_per_day": basis.get("slope_per_day"),
            "regime_upstream": basis.get("regime"),
            "ema20": basis.get("ema20"),
            "ema50": basis.get("ema50"),
            "ema200": basis.get("ema200"),
            "rsi": basis.get("rsi"),
        },
        upstream_schema=forecast.get("schema"),
    )
    return hs.stamp()  # type: ignore[attr-defined]


# ══════════════════════════════════════════════════════════════════════════
# AGENT 555 — CALIBRATION
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : InputBundle, HorizonSet
#   OUT: CalibrationState
#   RULE: without a walk-forward harness there is no measured pinball skill,
#         no measured coverage, no measured Brier skill. Those fields stay
#         None and calibration_state stays SHADOW. Reading a "SHADOW" as
#         "uncalibrated but usable" is exactly the collapse this agent exists
#         to prevent — a None metric must never be rendered as 0.0 or as PASS.
#         The harness path is read if present; only real evidence moves state.
# ══════════════════════════════════════════════════════════════════════════

# Read the harness path lazily so tests can override the env var at runtime.
def _calibration_harness_path() -> Path:
    # Default path matches the output of /root/WEALTH/forecast/calibration/harness.py
    # (schema wealth.calibration.gold.v1), so the orchestrator promotes out of
    # SHADOW the moment the walk-forward harness produces a valid result.
    default = "/root/AAA/VAULT999/calibration/gold-forecast-metrics.json"
    return Path(os.getenv("WEALTH_CALIBRATION_HARNESS", default))


def AGENT_555_Calibration(
    bundle: InputBundle, horizons: HorizonSet
) -> CalibrationState:
    """Evaluate calibration state from measured evidence, else SHADOW."""
    env = AgentEnvelope(
        agent="555", tier="555-CALIBRATION", provenance="MEASURED"
    )
    state = CalibrationState(envelope=env)

    if not bundle.ok or not horizons.horizons:
        env.ok = False
        env.error = "no_horizon_set"
        env.provenance = "UNKNOWN"
        state.calibration_state = STATUS_SHADOW
        state.reason = "no_horizon_set"
        return state.stamp()  # type: ignore[attr-defined]

    # Evidence gate: a harness file is the only admissible source of measured
    # calibration numbers. Absent → SHADOW, with all metrics None.
    harness_path = _calibration_harness_path()
    if not harness_path.exists():
        state.calibration_state = STATUS_SHADOW
        state.reason = "no_walk_forward_harness"
        env.provenance = "UNKNOWN"
        return state.stamp()  # type: ignore[attr-defined]

    try:
        payload = json.loads(harness_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        state.calibration_state = STATUS_SHADOW
        state.reason = f"harness_unreadable:{type(exc).__name__}"
        env.provenance = "UNKNOWN"
        return state.stamp()  # type: ignore[attr-defined]

    # Two harnesses are accepted:
    #   (A) the WEALTH forecast/harness.py output (schema wealth.calibration.gold.v1)
    #       with rolling_means: {pinball_skill_score, model_coverage, brier_skill}
    #       plus top-level calibration_state and promotion_recommended.
    #   (B) a plain dict for tests with: {pinball_skill, coverage, brier_skill}.
    rolling = payload.get("rolling_means") if isinstance(payload, dict) else None

    def _num(v: Any) -> Optional[float]:
        if isinstance(v, bool):
            return None
        if isinstance(v, (int, float)) and math.isfinite(float(v)):
            return float(v)
        return None

    pinball = _num(
        (rolling or {}).get("pinball_skill_score") if isinstance(rolling, dict) else None
    )
    coverage = _num(
        (rolling or {}).get("model_coverage") if isinstance(rolling, dict) else None
    )
    brier = _num(
        (rolling or {}).get("brier_skill") if isinstance(rolling, dict) else None
    )
    if pinball is None:
        pinball = _num(payload.get("pinball_skill") if isinstance(payload, dict) else None)
    if coverage is None:
        coverage = _num(payload.get("coverage") if isinstance(payload, dict) else None)
    if brier is None:
        brier = _num(payload.get("brier_skill") if isinstance(payload, dict) else None)

    state.pinball_skill = pinball
    state.coverage = coverage
    state.brier_skill = brier
    if isinstance(payload, dict):
        if "baseline" in payload:
            state.baseline = str(payload["baseline"])
        elif isinstance(rolling, dict) and rolling.get("baseline"):
            state.baseline = str(rolling["baseline"])

    # Promotion rule: only real, positive measured skill promotes out of SHADOW.
    # The harness's own `calibration_state` is authoritative when present.
    harness_state = (
        str(payload.get("calibration_state")).upper()
        if isinstance(payload, dict) and payload.get("calibration_state") is not None
        else ""
    )
    harness_promotes = (
        bool(payload.get("promotion_recommended"))
        if isinstance(payload, dict)
        else False
    )

    measured_positive = (
        pinball is not None and pinball > 0
        and coverage is not None and 0.6 <= coverage <= 0.95
    )

    if harness_state == "LIVE" and harness_promotes and measured_positive:
        state.calibration_state = "CALIBRATED"
        state.reason = "harness_live_with_measured_skill"
    elif measured_positive:
        state.calibration_state = "CALIBRATED"
        state.reason = "measured_skill_positive_and_coverage_in_band"
    else:
        state.calibration_state = STATUS_SHADOW
        state.reason = "measured_skill_insufficient"

    return state.stamp()  # type: ignore[attr-defined]


# ══════════════════════════════════════════════════════════════════════════
# AGENT 777 — TRANSLATOR
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : RegimeState, HorizonSet, CalibrationState
#   OUT: TranslatorOutput  (trade_72h + physical_saving stance candidates)
#   RULE: emits *candidates* only. It does not judge, approve, or execute.
#         A candidate is a description of what the distribution says; the
#         888-APEX lane decides, and F13 authorises.
# ══════════════════════════════════════════════════════════════════════════


def AGENT_777_Translator(
    regime: RegimeState,
    horizons: HorizonSet,
    calibration: CalibrationState,
    cost_bps: float = DEFAULT_ROUND_TRIP_COST_BPS,
) -> TranslatorOutput:
    """Translate the distribution into decision-ready stance candidates."""
    env = AgentEnvelope(
        agent="777", tier="777-TRANSLATOR", provenance="DERIVED"
    )

    trade = StanceCandidate(stance="FLAT")
    saving = StanceCandidate(stance="WAIT")

    if not horizons.horizons:
        env.ok = False
        env.error = "no_horizon_set"
        trade.reason_codes.append("NO_PATH")
        saving.reason_codes.append("NO_PATH")
        return TranslatorOutput(
            envelope=env, trade_72h=trade, physical_saving=saving
        ).stamp()  # type: ignore[attr-defined]

    # Use the furthest horizon as the decision horizon for the 72h stance.
    h72 = next(
        (h for h in horizons.horizons if h.offset_hours == 72), horizons.horizons[-1]
    )
    spot = horizons.spot

    codes: list[str] = []
    # Local narrowing: has_full_distribution() guarantees all five quantiles
    # are non-None at runtime, but the type-checker can't see that. Re-bind
    # with non-Optional types so the arithmetic is unambiguous.
    p10_n = h72.p10
    p50_n = h72.p50
    p90_n = h72.p90
    if (
        h72.has_full_distribution()
        and spot is not None
        and spot > 0
        and p10_n is not None
        and p50_n is not None
        and p90_n is not None
    ):
        width_ratio = (p90_n - p10_n) / spot
        trailing = (p50_n - spot) / spot
        upside = h72.p_up_after_cost

        codes.append(f"REGIME_{regime.regime}")
        codes.append(f"CAL_{calibration.calibration_state}")
        codes.append(f"WIDTH_{round(width_ratio, 4)}")
        codes.append(f"TRAILING_EDGE_{round(trailing, 4)}")

        # Edge must beat cost after the round trip, and the cone must be
        # coherent enough for the median to be meaningful.
        edge_present = upside is not None and upside >= 0.55
        edge_against = upside is not None and upside <= 0.45

        if regime.regime == "UNKNOWN":
            trade.stance = "FLAT"
            codes.append("REGIME_UNKNOWN")
        elif regime.regime == "EXHAUSTION":
            trade.stance = "FLAT"
            codes.append("EXHAUSTION_NO_CHASE")
        elif edge_present:
            trade.stance = "LONG"
            codes.append("P_UP_AFTER_COST_GE_0p55")
        elif edge_against:
            trade.stance = "SHORT"
            codes.append("P_UP_AFTER_COST_LE_0p45")
        else:
            trade.stance = "FLAT"
            codes.append("EDGE_INSIDE_COST_BAND")

        trade.reason = (
            f"{regime.regime} · 72h median {h72.p50} vs spot {spot} · "
            f"P(up after {cost_bps}bp cost)={upside} · {calibration.reason}"
        )

        # Physical saving (the sovereign's actual use case: buy gold in MYR
        # terms, save, not trade). A saving stance is about *timing*, not
        # leverage — it asks whether waiting has positive expected value
        # against the cost of waiting.
        saving_codes: list[str] = [f"CAL_{calibration.calibration_state}"]
        if trailing > 0.005:
            saving.stance = "SAVE_NOW"
            saving_codes.append("MEDIAN_ABOVE_SPOT_GT_0p5pct")
        elif trailing < -0.005:
            saving.stance = "SAVE_WAIT"
            saving_codes.append("MEDIAN_BELOW_SPOT_GT_0p5pct")
        else:
            saving.stance = "SAVE_WAIT"
            saving_codes.append("MEDIAN_FLAT_VS_SPOT")
        # In SHADOW the saving candidate is never an instruction, only a
        # candidate — say so in the codes.
        saving_codes.append(f"STATUS_{calibration.calibration_state}")
        saving.reason_codes = saving_codes
        saving.reason = (
            f"72h median {h72.p50} vs spot {spot} · regime {regime.regime} · "
            f"calibration {calibration.calibration_state}"
        )
    else:
        # Partial/null path — stay flat and SAY WHY.
        trade.stance = "FLAT"
        trade.reason_codes = ["INCOMPLETE_DISTRIBUTION"]
        trade.reason = "horizon missing quantiles; cannot translate"
        saving.stance = "WAIT"
        saving.reason_codes = ["INCOMPLETE_DISTRIBUTION"]
        saving.reason = "horizon missing quantiles; cannot translate"

    trade.reason_codes = codes
    return TranslatorOutput(
        envelope=env, trade_72h=trade, physical_saving=saving
    ).stamp()  # type: ignore[attr-defined]


# ══════════════════════════════════════════════════════════════════════════
# AGENT 888 — JUDGE
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : InputBundle, RegimeState, HorizonSet, CalibrationState, TranslatorOutput
#   OUT: JudgeVerdict (ACT | WAIT | HOLD | BLOCKED) — default HOLD
#   RULE: Default HOLD. BLOCKED when integrity fails. In SHADOW calibration
#         the ceiling is WAIT — a candidate may never become an instruction
#         while calibration is unmeasured. The judge holds no authority to
#         promote execution; that requires F13.
# ══════════════════════════════════════════════════════════════════════════


def AGENT_888_Judge(
    bundle: InputBundle,
    regime: RegimeState,
    horizons: HorizonSet,
    calibration: CalibrationState,
    translator: TranslatorOutput,
) -> JudgeVerdict:
    """Return the final verdict. Default HOLD; cannot self-authorize ACT."""
    env = AgentEnvelope(agent="888", tier="888-APEX", provenance="DERIVED")
    codes: list[str] = []

    # 1. Integrity gate — upstream unreachable/malformed ⇒ BLOCKED.
    if not bundle.ok:
        codes.append("INTEGRITY_FAILED")
        env.provenance = "UNKNOWN"
        return JudgeVerdict(
            envelope=env, verdict="BLOCKED", reason_codes=codes
        ).stamp()  # type: ignore[attr-defined]

    # 2. Path completeness — no full distribution at any target horizon.
    complete = [h for h in horizons.horizons if h.has_full_distribution()]
    if not complete:
        codes.append("NO_COMPLETE_DISTRIBUTION")
        return JudgeVerdict(
            envelope=env, verdict="BLOCKED", reason_codes=codes
        ).stamp()  # type: ignore[attr-defined]

    # 3. Calibration ceiling — SHADOW caps the verdict at WAIT.
    if calibration.calibration_state != "CALIBRATED":
        codes.append("CALIBRATION_SHADOW")
        codes.append("EXECUTION_CEILING_WAIT")
        if translator.trade_72h.stance in ("LONG", "SHORT"):
            codes.append(f"CANDIDATE_{translator.trade_72h.stance}_NOT_PROMOTED")
        return JudgeVerdict(
            envelope=env, verdict="WAIT", reason_codes=codes
        ).stamp()  # type: ignore[attr-defined]

    # 4. Calibrated path — the distribution has a direction, but ACT still
    #    requires F13 authorization, which this layer cannot manufacture.
    if translator.trade_72h.stance in ("LONG", "SHORT") and regime.confidence >= 0.5:
        codes.append(f"STANCE_{translator.trade_72h.stance}")
        codes.append("CALIBRATED")
        codes.append("F13_AUTHORIZATION_REQUIRED_FOR_ACT")
        return JudgeVerdict(
            envelope=env, verdict="WAIT", reason_codes=codes
        ).stamp()  # type: ignore[attr-defined]

    codes.append("NO_ACTIONABLE_EDGE")
    return JudgeVerdict(
        envelope=env, verdict="HOLD", reason_codes=codes
    ).stamp()  # type: ignore[attr-defined]


# ══════════════════════════════════════════════════════════════════════════
# AGENT 999 — WITNESS
# ══════════════════════════════════════════════════════════════════════════
# Contract:
#   IN : OrchestrationResult (or the assembled packet dict), trace_id
#   OUT: WitnessReceipt (receipt_id, receipt_uri, written, digest)
#   RULE: Writes the receipt under VAULT999/receipts. A receipt is an
#         append-only event record; it is NOT a seal, and a failed write is
#         reported as written=False — never silently swallowed.
# ══════════════════════════════════════════════════════════════════════════


def AGENT_999_Witness(
    packet: dict[str, Any],
    trace_id: str,
    receipts_dir: Path = VAULT999_RECEIPTS,
) -> WitnessReceipt:
    """Write the orchestration receipt to VAULT999 and return its handle."""
    env = AgentEnvelope(agent="999", tier="999-WITNESS", provenance="MEASURED")
    receipt = WitnessReceipt(envelope=env, trace_id=trace_id)

    stamp = datetime.now(MYT).strftime("%Y%m%dT%H%M%S")
    forecast_id = packet.get("forecast_id") or "unknown"
    receipt_id = f"wealth-gold-orchestration-{forecast_id}-{stamp}"
    receipt.receipt_id = receipt_id

    try:
        receipts_dir.mkdir(parents=True, exist_ok=True)
        path = receipts_dir / f"{receipt_id}.json"
        body = {
            "receipt_id": receipt_id,
            "trace_id": trace_id,
            "issued_at": packet.get("issued_at"),
            "organ": "WEALTH",
            "lane": "gold-forecast-orchestration",
            "schema": SCHEMA,
            "constitutional_tier": "999-WITNESS",
            "status": packet.get("status"),
            "verdict": packet.get("verdict"),
            "governance": packet.get("governance"),
            "payload": packet,
        }
        text = json.dumps(body, indent=2, sort_keys=False, default=str)
        path.write_text(text, encoding="utf-8")
        receipt.receipt_uri = str(path)
        receipt.written = True
        receipt.digest = _sha256_hex(text)
    except OSError as exc:
        env.ok = False
        env.error = f"receipt_write_failed:{type(exc).__name__}"
        env.provenance = "UNKNOWN"
        receipt.written = False

    return receipt.stamp()  # type: ignore[attr-defined]


def _sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — the sequential pipeline
# ══════════════════════════════════════════════════════════════════════════


def run_orchestration(
    client: Any = None,
    *,
    write_receipt: bool = True,
    cost_bps: float = DEFAULT_ROUND_TRIP_COST_BPS,
    receipts_dir: Optional[Path] = None,
    m2_history: Optional[dict[str, list[float]]] = None,
    now: Optional[datetime] = None,
) -> OrchestrationResult:
    """Run the full 000→999 pipeline and return the governed packet.

    NOT executed at import time. The caller decides when reality is probed.

    v1.1 additions
    --------------
    ``m2_history`` — optional dict of ``{"dxy": [..], "us10y": [..],
    "silver": [..]}`` time series, oldest first. When supplied the M2
    regime verdict becomes DERIVED; otherwise the snapshot-only mode
    collapses to ``UNKNOWN`` (the safe answer).
    ``now`` — wall-clock override for tests; production defaults to
    ``datetime.now(timezone.utc)``.
    """
    client = client or GoldAPIClient()
    issued_at = (now or datetime.now(timezone.utc)).isoformat()
    if now is None:
        wall_now = datetime.now(MYT)
    else:
        wall_now = now.astimezone(MYT) if now.tzinfo else now.replace(tzinfo=MYT)
    issued_at = wall_now.isoformat()
    trace_id = uuid.uuid4().hex
    forecast_id = f"gold-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{trace_id[:8]}"

    # ── 000 Integrity ────────────────────────────────────────────────────
    bundle = AGENT_000_Integrity(client, m2_history=m2_history, now=now)

    # ── 111 Regime ───────────────────────────────────────────────────────
    regime = AGENT_111_Regime(bundle)

    # ── 333 Forecast ─────────────────────────────────────────────────────
    horizons = AGENT_333_Forecast(bundle, regime, cost_bps=cost_bps)

    # ── 555 Calibration ──────────────────────────────────────────────────
    calibration = AGENT_555_Calibration(bundle, horizons)

    # ── 777 Translator ───────────────────────────────────────────────────
    translator = AGENT_777_Translator(regime, horizons, calibration, cost_bps=cost_bps)

    # ── 888 Judge ────────────────────────────────────────────────────────
    verdict = AGENT_888_Judge(bundle, regime, horizons, calibration, translator)

    # ── Assemble the packet ──────────────────────────────────────────────
    # Status is SHADOW unless and until calibration is CALIBRATED *and* an
    # F13 authorization event exists. Default is always the safe lane.
    status = STATUS_SHADOW

    validation = {
        "baseline": calibration.baseline,
        "pinball_skill": calibration.pinball_skill,
        "coverage": calibration.coverage,
        "brier_skill": calibration.brier_skill,
        "calibration_state": calibration.calibration_state,
        "calibration_reason": calibration.reason,
        "cost_bps_round_trip": cost_bps,
        "integrity_missing": bundle.missing,
        "integrity_sources": bundle.sources,
        # v1.1: declare event sentinel + M2 evidence alongside the
        # existing calibration row so a downstream reader sees all the
        # upstream gates in one place.
        "event_risk_state": bundle.event_risk.state,
        "event_risk_reason": bundle.event_risk.reason,
        "event_risk_time_to_next_hours": bundle.event_risk.time_to_next_hours,
        "m2_regime_state": bundle.m2_regime.state,
        "m2_regime_confidence": bundle.m2_regime.confidence,
        "m2_regime_drivers": dict(bundle.m2_regime.drivers),
    }

    outputs = {
        "trade_72h": {
            "stance": translator.trade_72h.stance,
            "reason_codes": translator.trade_72h.reason_codes,
            "reason": translator.trade_72h.reason,
        },
        "physical_saving": {
            "stance": translator.physical_saving.stance,
            "reason_codes": translator.physical_saving.reason_codes,
            "reason": translator.physical_saving.reason,
        },
    }

    # Governance flags: ALWAYS safe by default. Flipping either one requires
    # an out-of-band F13 authority artifact, not a code path in this module.
    governance = {
        "human_confirmation_required": True,
        "execution_enabled": False,
        "status": status,
        "verdict": verdict.verdict,
        "reason_codes": verdict.reason_codes,
        "authority": "F13 required for promotion out of SHADOW",
        "domain_coordinate": "LANE/TIER (suffixed): 888-APEX judge · 555-ASI calibration",
    }

    result = OrchestrationResult(
        envelope=AgentEnvelope(
            agent="orchestrator",
            tier="PIPELINE",
            provenance="OBSERVED" if bundle.ok else "UNKNOWN",
            ok=bundle.ok,
            error=None if bundle.ok else bundle.envelope.error,
        ).stamp(),  # type: ignore[attr-defined]
        status=status,
        asset=str((bundle.ticker or {}).get("symbol") or "XAUUSD"),
        forecast_id=forecast_id,
        forecast_origin=str(
            getattr(client, "base_url", DEFAULT_BASE_URL)
        ),
        issued_at=issued_at,
        regime=regime,
        horizons=horizons.horizons,
        validation=validation,
        outputs=outputs,
        governance=governance,
        verdict=verdict.verdict,
        trace_id=trace_id,
        # v1.1 additions — surfaced at packet root.
        event_risk_state=bundle.event_risk.state,
        m2_regime_posterior=bundle.m2_regime.to_dict(),
    )

    packet = result.to_dict()

    # ── 999 Witness ──────────────────────────────────────────────────────
    if write_receipt:
        target_dir = receipts_dir if receipts_dir is not None else VAULT999_RECEIPTS
        receipt = AGENT_999_Witness(packet, trace_id, receipts_dir=target_dir)
        governance["receipt_uri"] = receipt.receipt_uri
        governance["receipt_written"] = receipt.written
        governance["receipt_id"] = receipt.receipt_id
        governance["receipt_digest"] = receipt.digest
        packet["governance"] = governance
        packet["receipt"] = {
            "receipt_id": receipt.receipt_id,
            "receipt_uri": receipt.receipt_uri,
            "written": receipt.written,
            "digest": receipt.digest,
        }
        result.governance = governance
    else:
        governance["receipt_uri"] = ""
        governance["receipt_written"] = False
        packet["governance"] = governance

    result.raw = packet
    return result


# ══════════════════════════════════════════════════════════════════════════
# CLI — explicit invocation only (never on import)
# ══════════════════════════════════════════════════════════════════════════


def main(argv: Optional[list[str]] = None) -> int:
    """Run the pipeline and print the governed packet."""
    import argparse

    parser = argparse.ArgumentParser(description="wealth.gold forecast orchestration")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--no-receipt", action="store_true")
    parser.add_argument("--cost-bps", type=float, default=DEFAULT_ROUND_TRIP_COST_BPS)
    parser.add_argument("--json", action="store_true", help="raw packet only")
    args = parser.parse_args(argv)

    client = GoldAPIClient(base_url=args.base_url)
    res = run_orchestration(
        client,
        write_receipt=not args.no_receipt,
        cost_bps=args.cost_bps,
    )
    if args.json:
        print(json.dumps(res.raw, indent=2, default=str))
    else:
        print(json.dumps(res.to_dict(), indent=2, default=str))
    return 0 if res.envelope.ok else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
