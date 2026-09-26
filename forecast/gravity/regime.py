"""111_REGIME — gravity-driven posterior over gold price regimes.

States
------

* **RANGE**       — gravity balanced, no dominant pull
* **TREND_UP**    — gravity pulls gold up (USD weak, real yields falling,
                    ETF inflows, CB demand up)
* **TREND_DOWN**  — gravity pulls gold down (USD strong, real yields rising,
                    ETF outflows, COT crowded long → mean reversion risk)
* **COMPRESSION** — realised vol < median AND no expansion signal
* **TRANSITION**  — gravity features are inconsistent across sources
* **EVENT_RISK**  — exogenous event window (FOMC / NFP / CPI) within 24h

The output is a *posterior* over these six states with confidence in
[0, 1]. The state with the largest posterior mass is the *point* state;
the full distribution is what downstream consumers should use.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Optional

import numpy as np
import pandas as pd

from .ingest import GravityFeatureSeries, IngestPoint


REGIME_STATES = frozenset({
    "RANGE",
    "TREND_UP",
    "TREND_DOWN",
    "COMPRESSION",
    "TRANSITION",
    "EVENT_RISK",
})


# Vol ratio thresholds (compression / expansion boundaries).
# Below compression: vol is < 75% of trailing median → COMPRESSION
# Above expansion: vol is > 1.4x trailing median → expansion flag
DEFAULT_VOL_RATIO_COMPRESSION = 0.75
DEFAULT_VOL_RATIO_EXPANSION = 1.40

# Feature slope thresholds for trend calls (per-step fractional change).
REAL_YIELD_SLOPE_THRESHOLD = 0.02     # 2 bp/day real-yield move = directional
USD_SLOPE_THRESHOLD = 0.0015          # 0.15% DXY move
ETF_FLOW_THRESHOLD_TONNES = 5.0       # weekly tonnage flow > 5t = directional
COT_NET_THRESHOLD_PCT = 10.0          # net long - short > 10pp = crowded

# Feature weight — every source has a prior weight in the regime vote.
# Real yield & USD dominate because they are the cleanest signals.
FEATURE_WEIGHTS: dict[str, float] = {
    "DFII10": 0.30,
    "USD_BASKET": 0.30,
    "SILVER_RESIDUAL": 0.10,
    "ETF_FLOW": 0.15,
    "COT_POSITIONING": 0.10,
    "CB_DEMAND": 0.05,
}


@dataclass
class RegimePosterior111:
    """The 111_REGIME verdict.

    ``state`` is the point estimate (highest posterior mass); the full
    ``posterior`` dict carries the probability mass over every state.
    Confidence is the mass on the point state.
    """

    state: str = "RANGE"
    confidence: float = 0.0
    posterior: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    provenance: str = "UNKNOWN"  # OBSERVED | DERIVED | UNKNOWN
    reason: str = ""
    observed_at: str = ""
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in REGIME_STATES:
            self.state = "RANGE"
        # Confidence ∈ [0, 1].
        try:
            c = float(self.confidence)
        except (TypeError, ValueError):
            c = 0.0
        if c != c:  # NaN
            c = 0.0
        self.confidence = max(0.0, min(1.0, round(c, 4)))
        # Normalize posterior so it sums to 1.0 (when non-empty).
        s = sum(max(0.0, float(v)) for v in self.posterior.values())
        if s > 0:
            self.posterior = {
                k: round(max(0.0, float(v)) / s, 6)
                for k, v in self.posterior.items()
            }

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "confidence": self.confidence,
            "posterior": dict(self.posterior),
            "evidence": dict(self.evidence),
            "provenance": self.provenance,
            "reason": self.reason,
            "observed_at": self.observed_at,
            "reason_codes": list(self.reason_codes),
        }


# ── Helpers ──────────────────────────────────────────────────────────────


def _series_points(
    series: GravityFeatureSeries, source: str
) -> list[IngestPoint]:
    return list(series.points_by_source.get(source, []))


def _released_subset(
    points: list[IngestPoint], when_iso: str
) -> list[IngestPoint]:
    """Filter to points whose release_ts <= when_iso (no look-ahead)."""
    try:
        when = pd.Timestamp(when_iso)
        if when.tzinfo is None:
            when = when.tz_localize("UTC")
    except Exception:
        return []
    out: list[IngestPoint] = []
    for p in points:
        try:
            rt = pd.Timestamp(p.release_ts)
            if rt.tzinfo is None:
                rt = rt.tz_localize("UTC")
        except Exception:
            continue
        if rt <= when:
            out.append(p)
    return sorted(out, key=lambda x: x.observation_ts)


def _slope_pct(values: list[float]) -> Optional[float]:
    cleaned = [v for v in values if isinstance(v, (int, float)) and v == v]
    if len(cleaned) < 2:
        return None
    first, last = cleaned[0], cleaned[-1]
    n = len(cleaned) - 1
    mean = sum(cleaned) / len(cleaned)
    if mean <= 0:
        return None
    return (last - first) / (mean * n) if n > 0 else 0.0


def _feature_vote(
    *,
    direction: str,         # "UP" | "DOWN" | "FLAT" | "UNKNOWN"
    weight: float,
    evidence: dict[str, Any],
    code: str,
) -> tuple[float, float, float]:
    """Translate a single feature's directional read into regime votes.

    Returns (up_vote, down_vote, range_vote).
    Direction UP (gold-bullish, e.g. USD weak) → TREND_UP vote.
    Direction DOWN (gold-bearish) → TREND_DOWN vote.
    FLAT / UNKNOWN → RANGE vote.
    """
    if direction == "UP":
        return (weight, 0.0, 0.0)
    if direction == "DOWN":
        return (0.0, weight, 0.0)
    return (0.0, 0.0, weight)


def _realised_vol_ratio(
    closes: list[float], window: int = 20
) -> Optional[float]:
    """Return recent_vol / trailing_median_vol as a ratio.

    Ratio < 1 ⇒ recent vol is below median (compression risk).
    Ratio > 1 ⇒ recent vol is above median (expansion risk).
    """
    cleaned = [float(v) for v in closes if isinstance(v, (int, float))]
    if len(cleaned) < window * 3:
        return None
    log_p = np.log(np.array(cleaned))
    rets = np.diff(log_p)
    if len(rets) < window:
        return None
    # Trailing median vol: 60-day rolling std median.
    rolling = []
    for i in range(window, len(rets)):
        seg = rets[i - window:i]
        rolling.append(float(np.std(seg)))
    if len(rolling) < 3:
        return None
    median_vol = float(np.median(rolling[:-1])) if len(rolling) >= 2 else rolling[0]
    recent = rolling[-1]
    if median_vol <= 0:
        return None
    return float(recent / median_vol)


# ── Public compute ──────────────────────────────────────────────────────


def compute_regime_posterior_111(
    series: GravityFeatureSeries,
    *,
    closes: Optional[list[float]] = None,
    event_window_hours: int = 0,
    vol_ratio_compression: float = DEFAULT_VOL_RATIO_COMPRESSION,
    vol_ratio_expansion: float = DEFAULT_VOL_RATIO_EXPANSION,
    now: Optional[datetime] = None,
) -> RegimePosterior111:
    """Compute the 111_REGIME posterior over the gold regime states.

    Parameters
    ----------
    series
        The :class:`GravityFeatureSeries` produced by the ingesters.
        Every feature value is filtered by ``release_ts <= now`` so the
        posterior never looks ahead.
    closes
        The XAUUSD close history for vol-ratio computation (optional).
        When None or too short, COMPRESSION / EXPANSION are not asserted.
    event_window_hours
        If an event (FOMC/NFP/CPI) is within this many hours, vote
        EVENT_RISK strongly. Pass 0 to disable.
    now
        Wall-clock override. Defaults to UTC now.
    """
    now = now or datetime.now(timezone.utc)
    now_iso = now.isoformat()
    posterior = RegimePosterior111(observed_at=now_iso)
    posterior.posterior = {s: 0.0 for s in REGIME_STATES}
    posterior.posterior["RANGE"] = 0.0  # base

    # ── 1. EVENT_RISK vote (overrides everything when present) ───────
    if event_window_hours > 0:
        posterior.posterior["EVENT_RISK"] = 0.85
        posterior.reason_codes.append("EVENT_WITHIN_WINDOW")
    else:
        posterior.posterior["EVENT_RISK"] = 0.02  # baseline

    # ── 2. Per-feature directional votes ─────────────────────────────
    up_votes = 0.0
    down_votes = 0.0
    range_votes = 0.0
    transition_signals = 0

    # Real yield (DFII10): rising real yield → bearish gold.
    dfii = _released_subset(_series_points(series, "DFII10"), now_iso)
    dfii_vals = [float(p.value) for p in dfii if isinstance(p.value, (int, float))]
    dfii_slope = _slope_pct(dfii_vals[-20:]) if len(dfii_vals) >= 3 else None
    if dfii_slope is not None:
        if dfii_slope > REAL_YIELD_SLOPE_THRESHOLD:
            d = "DOWN"  # rising real yield → bearish gold
            posterior.reason_codes.append("REAL_YIELD_RISING")
        elif dfii_slope < -REAL_YIELD_SLOPE_THRESHOLD:
            d = "UP"  # falling real yield → bullish gold
            posterior.reason_codes.append("REAL_YIELD_FALLING")
        else:
            d = "FLAT"
        w = FEATURE_WEIGHTS["DFII10"]
    else:
        d = "UNKNOWN"
        w = FEATURE_WEIGHTS["DFII10"]
    posterior.evidence["dfii10_slope"] = dfii_slope
    u, d_v, r = _feature_vote(
        direction=d, weight=w, evidence={"dfii10": dfii_slope},
        code="DFII10",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # USD basket: rising USD → bearish gold.
    usd = _released_subset(_series_points(series, "USD_BASKET"), now_iso)
    usd_vals = [float(p.value) for p in usd if isinstance(p.value, (int, float))]
    usd_slope = _slope_pct(usd_vals[-20:]) if len(usd_vals) >= 3 else None
    if usd_slope is not None:
        if usd_slope > USD_SLOPE_THRESHOLD:
            d2 = "DOWN"  # USD rising → bearish gold
            posterior.reason_codes.append("USD_RISING")
        elif usd_slope < -USD_SLOPE_THRESHOLD:
            d2 = "UP"  # USD falling → bullish gold
            posterior.reason_codes.append("USD_FALLING")
        else:
            d2 = "FLAT"
    else:
        d2 = "UNKNOWN"
    w = FEATURE_WEIGHTS["USD_BASKET"]
    u, d_v, r = _feature_vote(
        direction=d2, weight=w, evidence={"usd_slope": usd_slope},
        code="USD_BASKET",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # Silver residual: rising → bullish gold (correlation).
    silver = _released_subset(_series_points(series, "SILVER_RESIDUAL"), now_iso)
    silver_vals = [float(p.value) for p in silver if isinstance(p.value, (int, float))]
    silver_slope = _slope_pct(silver_vals[-20:]) if len(silver_vals) >= 3 else None
    if silver_slope is not None:
        d3 = "UP" if silver_slope > 0.005 else ("DOWN" if silver_slope < -0.005 else "FLAT")
    else:
        d3 = "UNKNOWN"
    u, d_v, r = _feature_vote(
        direction=d3, weight=FEATURE_WEIGHTS["SILVER_RESIDUAL"],
        evidence={"silver_slope": silver_slope}, code="SILVER",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # ETF flows: weekly tonnage flow (last vs prior week).
    etf = _released_subset(_series_points(series, "ETF_FLOW"), now_iso)
    etf_recent = [p.value for p in etf[-2:] if isinstance(p.value, (int, float))]
    etf_flow = None
    if len(etf_recent) == 2:
        etf_flow = etf_recent[1] - etf_recent[0]
    if etf_flow is not None:
        if etf_flow > ETF_FLOW_THRESHOLD_TONNES:
            d4 = "UP"  # inflows → bullish gold
            posterior.reason_codes.append("ETF_INFLOWS")
        elif etf_flow < -ETF_FLOW_THRESHOLD_TONNES:
            d4 = "DOWN"  # outflows → bearish gold
            posterior.reason_codes.append("ETF_OUTFLOWS")
        else:
            d4 = "FLAT"
    else:
        d4 = "UNKNOWN"
    u, d_v, r = _feature_vote(
        direction=d4, weight=FEATURE_WEIGHTS["ETF_FLOW"],
        evidence={"etf_flow_tonnes": etf_flow}, code="ETF",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # COT positioning: crowded long → mean-reversion risk → bearish.
    cot = _released_subset(_series_points(series, "COT_POSITIONING"), now_iso)
    cot_recent = [p.value for p in cot[-2:] if isinstance(p.value, (int, float))]
    cot_latest = cot_recent[-1] if cot_recent else None
    if cot_latest is not None:
        if cot_latest > COT_NET_THRESHOLD_PCT:
            d5 = "DOWN"  # crowded long → mean-reversion risk
            posterior.reason_codes.append("COT_CROWDED_LONG")
        elif cot_latest < -COT_NET_THRESHOLD_PCT:
            d5 = "UP"
            posterior.reason_codes.append("COT_CROWDED_SHORT")
        else:
            d5 = "FLAT"
    else:
        d5 = "UNKNOWN"
    u, d_v, r = _feature_vote(
        direction=d5, weight=FEATURE_WEIGHTS["COT_POSITIONING"],
        evidence={"cot_net": cot_latest}, code="COT",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # CB demand: structural prior — only flips TREND_UP if strongly positive.
    cb = _released_subset(_series_points(series, "CB_DEMAND"), now_iso)
    cb_recent = [p.value for p in cb[-1:] if isinstance(p.value, (int, float))]
    cb_latest = cb_recent[-1] if cb_recent else None
    if cb_latest is not None:
        if cb_latest > 1000:
            d6 = "UP"  # strong CB demand → mild structural bid
            posterior.reason_codes.append("CB_DEMAND_STRONG")
        elif cb_latest < 200:
            d6 = "DOWN"
            posterior.reason_codes.append("CB_DEMAND_WEAK")
        else:
            d6 = "FLAT"
    else:
        d6 = "UNKNOWN"
    u, d_v, r = _feature_vote(
        direction=d6, weight=FEATURE_WEIGHTS["CB_DEMAND"],
        evidence={"cb_demand_tonnes": cb_latest}, code="CB",
    )
    up_votes += u
    down_votes += d_v
    range_votes += r

    # Total weight sanity (should be ~1.0).
    total_w = up_votes + down_votes + range_votes
    if total_w <= 0:
        posterior.state = "RANGE"
        posterior.confidence = 0.0
        posterior.provenance = "UNKNOWN"
        posterior.reason = "no_gravity_evidence"
        posterior.reason_codes.append("NO_EVIDENCE")
        posterior.posterior = {s: 1.0 if s == "RANGE" else 0.0 for s in REGIME_STATES}
        return posterior

    # Empty-evidence: when every feature voted UNKNOWN (only range_votes
    # contributed and no directional signal exists), emit an explicit
    # UNKNOWN-provenance verdict with the RANGE point estimate. This
    # keeps the audit trail honest: "I see no gravity, the verdict is
    # RANGE because nothing pulled the price."
    if up_votes == 0 and down_votes == 0 and range_votes > 0:
        # Every feature was UNKNOWN/FLAT. Honour the RANGE verdict and
        # flag the reason so the audit trail is honest.
        if "NO_EVIDENCE" not in posterior.reason_codes:
            posterior.reason_codes.append("NO_DIRECTIONAL_EVIDENCE")
        # We let the composition logic below build the posterior;
        # we only set the reason here.
        posterior.reason = "no_directional_gravity_evidence"

    # ── 3. Transition signal: features disagree directionally ─────────
    # Count features voting UP vs DOWN; if both > 0.2 * total_w AND
    # their ratio < 2.0, this is a transition regime.
    if (
        up_votes > 0.2 * total_w
        and down_votes > 0.2 * total_w
        and min(up_votes, down_votes) > 0.4 * max(up_votes, down_votes)
    ):
        transition_signals += 1

    # ── 4. Vol ratio: COMPRESSION / EXPANSION flag ───────────────────
    vol_ratio = _realised_vol_ratio(closes) if closes else None
    posterior.evidence["vol_ratio"] = vol_ratio
    compression_active = False
    expansion_active = False
    if vol_ratio is not None:
        if vol_ratio < vol_ratio_compression:
            compression_active = True
            posterior.reason_codes.append("VOL_COMPRESSION")
        if vol_ratio > vol_ratio_expansion:
            expansion_active = True
            posterior.reason_codes.append("VOL_EXPANSION")

    # ── 5. Compose the posterior ──────────────────────────────────────
    norm = max(up_votes + down_votes + range_votes, 1e-9)
    up_share = up_votes / norm
    down_share = down_votes / norm
    range_share = range_votes / norm

    base = 0.0
    if compression_active:
        # COMPRESSION overrides trend votes — realised vol is compressing.
        posterior.posterior["COMPRESSION"] = 0.55
        posterior.posterior["RANGE"] = 0.30
        # Bleed some probability from trend states.
        posterior.posterior["TREND_UP"] = up_share * 0.30
        posterior.posterior["TREND_DOWN"] = down_share * 0.30
        # Re-normalise after override.
        s = sum(posterior.posterior.values())
        if s > 0:
            posterior.posterior = {
                k: round(v / s, 6) for k, v in posterior.posterior.items()
            }
        base = 0.0
    elif expansion_active:
        # Expansion → bleed probability into RANGE/TRANSITION.
        posterior.posterior["RANGE"] = max(posterior.posterior["RANGE"], 0.10)
        posterior.posterior["TRANSITION"] = max(
            posterior.posterior["TRANSITION"], 0.20
        )
        posterior.posterior["TREND_UP"] = up_share * 0.85
        posterior.posterior["TREND_DOWN"] = down_share * 0.85
        s = sum(posterior.posterior.values())
        if s > 0:
            posterior.posterior = {
                k: round(v / s, 6) for k, v in posterior.posterior.items()
            }
        base = 0.0
    else:
        posterior.posterior["TREND_UP"] = up_share * 0.9
        posterior.posterior["TREND_DOWN"] = down_share * 0.9
        posterior.posterior["RANGE"] = max(
            posterior.posterior["RANGE"], range_share * 0.8
        )
        s = sum(posterior.posterior.values())
        if s > 0:
            posterior.posterior = {
                k: round(v / s, 6) for k, v in posterior.posterior.items()
            }
        base = 0.0

    # Transition: when features disagree directionally (counted above).
    if transition_signals > 0 and not compression_active:
        posterior.posterior["TRANSITION"] = max(
            posterior.posterior.get("TRANSITION", 0.0), 0.35
        )
        # Bleed from RANGE / trend.
        bleed = 0.35 - posterior.posterior["TRANSITION"]
        if bleed > 0:
            for k in ("RANGE", "TREND_UP", "TREND_DOWN"):
                posterior.posterior[k] = max(
                    0.0, posterior.posterior.get(k, 0.0) - bleed / 3.0
                )
        s = sum(posterior.posterior.values())
        if s > 0:
            posterior.posterior = {
                k: round(v / s, 6) for k, v in posterior.posterior.items()
            }
        posterior.reason_codes.append("FEATURES_DISAGREE")

    # EVENT_RISK wins outright when active.
    if event_window_hours > 0:
        for k in posterior.posterior:
            if k != "EVENT_RISK":
                posterior.posterior[k] = round(posterior.posterior[k] * 0.10, 6)
        posterior.posterior["EVENT_RISK"] = round(
            sum(posterior.posterior.values()) + 0.5, 6
        )
        s = sum(posterior.posterior.values())
        if s > 0:
            posterior.posterior = {
                k: round(v / s, 6) for k, v in posterior.posterior.items()
            }

    # Point estimate: argmax.
    best_state = max(posterior.posterior.items(), key=lambda kv: kv[1])
    posterior.state = best_state[0]
    posterior.confidence = best_state[1]

    # Provenance — DERIVED when any feature had slope evidence,
    # OBSERVED only when all features had raw values without derivation.
    has_evidence = (
        dfii_slope is not None
        or usd_slope is not None
        or silver_slope is not None
        or etf_flow is not None
        or cot_latest is not None
        or cb_latest is not None
    )
    posterior.provenance = "DERIVED" if has_evidence else "UNKNOWN"
    posterior.reason = (
        f"regime_vote_up={up_share:.3f}_down={down_share:.3f}"
        f"_range={range_share:.3f}_vol_ratio={vol_ratio if vol_ratio is not None else 'NA'}"
    )
    return posterior


__all__ = [
    "REGIME_STATES",
    "RegimePosterior111",
    "compute_regime_posterior_111",
    "FEATURE_WEIGHTS",
    "DEFAULT_VOL_RATIO_COMPRESSION",
    "DEFAULT_VOL_RATIO_EXPANSION",
]
