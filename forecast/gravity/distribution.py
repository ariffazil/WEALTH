"""444_DISTRIBUTION — regime-conditional P10/P25/P50/P75/P90 cone.

Inputs: a 111_REGIME posterior + a recent XAUUSD close series.

Output: per horizon (24h / 48h / 72h):
  * ``p10``, ``p25``, ``p50``, ``p75``, ``p90`` in price units
  * ``expected_range`` = p90 - p10
  * ``vol_expansion_probability`` ∈ [0, 1]
  * ``regime_conditional_band`` = which regime voted the cone

The cone is NOT a direction call. It is a distribution over the next
``h`` hours conditional on the current regime posterior. The downstream
caller may combine the cone with cost assumptions to derive a P(up after
cost) — but that derivation lives outside this module.

Per-regime cone parameters (log-space):

    RANGE        ⇒ symmetric, σ_h = 1.05 · σ60 · √h/24
    TREND_UP     ⇒ median shift = +0.20·σ60·√h/24, σ_h = 1.20 · σ60 · √h/24
    TREND_DOWN   ⇒ mirror of TREND_UP
    COMPRESSION  ⇒ σ_h = 0.55 · σ60 · √h/24 (range compression)
    TRANSITION   ⇒ σ_h = 1.45 · σ60 · √h/24 (range expansion)
    EVENT_RISK   ⇒ σ_h = 1.85 · σ60 · √h/24 (vol-of-vol premium)

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from .regime import RegimePosterior111


HORIZONS_H: tuple[int, ...] = (24, 48, 72)
QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)


@dataclass
class HorizonDistribution:
    """A single-horizon quantile cone."""

    horizon_h: int = 24
    p10: float = 0.0
    p25: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    expected_range: float = 0.0
    vol_expansion_prob: float = 0.0
    regime_vote: str = "RANGE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon_h": self.horizon_h,
            "p10": round(self.p10, 4),
            "p25": round(self.p25, 4),
            "p50": round(self.p50, 4),
            "p75": round(self.p75, 4),
            "p90": round(self.p90, 4),
            "expected_range": round(self.expected_range, 4),
            "vol_expansion_prob": round(self.vol_expansion_prob, 4),
            "regime_vote": self.regime_vote,
        }


@dataclass
class Distribution444:
    """The full 444-DISTRIBUTION packet."""

    origin_price: float = 0.0
    sigma_60: float = 0.0
    horizons: list[HorizonDistribution] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    provenance: str = "UNKNOWN"  # OBSERVED | DERIVED | UNKNOWN
    observed_at: str = ""
    reason: str = ""
    reason_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for h in self.horizons:
            if h.p10 > h.p50 or h.p50 > h.p90:
                # Bands must be ordered. If regime logic ever inverted them,
                # force a monotonic sort.
                vals = sorted([h.p10, h.p25, h.p50, h.p75, h.p90])
                h.p10, h.p25, h.p50, h.p75, h.p90 = vals

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin_price": round(self.origin_price, 4),
            "sigma_60": round(self.sigma_60, 6),
            "horizons": [h.to_dict() for h in self.horizons],
            "evidence": dict(self.evidence),
            "provenance": self.provenance,
            "observed_at": self.observed_at,
            "reason": self.reason,
            "reason_codes": list(self.reason_codes),
        }


# ── Helpers ──────────────────────────────────────────────────────────────


def _realised_vol_60d(closes: list[float]) -> float:
    """Realised vol (per-step std of log returns) over the last 60 closes."""
    cleaned = [float(c) for c in closes if isinstance(c, (int, float)) and c > 0]
    if len(cleaned) < 10:
        return 1e-3  # safe default
    log_p = np.log(np.array(cleaned))
    rets = np.diff(log_p)
    if len(rets) < 2:
        return 1e-3
    return float(np.std(rets[-60:])) if len(rets) >= 2 else float(np.std(rets))


def expected_range_p10_p90(p10: float, p90: float) -> float:
    """Helper — the simple range between p10 and p90."""
    return float(max(0.0, p90 - p10))


def volatility_expansion_probability(
    regime_posterior: RegimePosterior111,
    closes: Optional[list[float]] = None,
) -> float:
    """P(vol expands > 1.4x median) within 24h, conditioned on regime.

    Returns a number in [0, 1]. EVENT_RISK and TRANSITION vote highest;
    COMPRESSION votes lowest. The closes are optional; when present,
    a low recent-realised-vol ratio nudges the probability down (realised
    compression is its own evidence).
    """
    p = regime_posterior.posterior or {}
    base = (
        0.85 * float(p.get("EVENT_RISK", 0.0))
        + 0.65 * float(p.get("TRANSITION", 0.0))
        + 0.40 * float(p.get("TREND_UP", 0.0))
        + 0.40 * float(p.get("TREND_DOWN", 0.0))
        + 0.20 * float(p.get("RANGE", 0.0))
        + 0.05 * float(p.get("COMPRESSION", 0.0))
    )
    # Recent realised vol nudge: if vol is currently compressed, the
    # probability of *expansion* rises (mean-reversion).
    if closes is not None and len(closes) > 60:
        log_p = np.log(np.array(closes, dtype=float))
        rets = np.diff(log_p)
        if len(rets) >= 60:
            recent = float(np.std(rets[-20:]))
            median = float(np.median(
                [float(np.std(rets[i - 20:i])) for i in range(20, len(rets))]
            ))
            if median > 0:
                ratio = recent / median
                if ratio < 0.75:
                    base = min(1.0, base + 0.20)  # mean reversion
                elif ratio > 1.40:
                    base = max(0.0, base - 0.15)
    return float(max(0.0, min(1.0, base)))


# ── Cone construction ───────────────────────────────────────────────────


# Per-regime cone parameters (in σ_60 units).
_REGIME_SIGMA_MULT: dict[str, float] = {
    "RANGE": 1.05,
    "TREND_UP": 1.20,
    "TREND_DOWN": 1.20,
    "COMPRESSION": 0.55,
    "TRANSITION": 1.45,
    "EVENT_RISK": 1.85,
}
_REGIME_DRIFT_MULT: dict[str, float] = {
    "RANGE": 0.0,
    "TREND_UP": 0.20,
    "TREND_DOWN": -0.20,
    "COMPRESSION": 0.0,
    "TRANSITION": 0.0,
    "EVENT_RISK": 0.0,
}


def quantile_cone_from_regime(
    *,
    origin_price: float,
    sigma_60: float,
    horizon_h: int,
    regime_posterior: RegimePosterior111,
) -> HorizonDistribution:
    """Build a single-horizon cone by mixing per-regime cones.

    Each regime contributes a (drift, σ) parameter; we average them
    weighted by the regime posterior mass, then emit the 5 quantiles.
    """
    if origin_price <= 0 or sigma_60 <= 0:
        # Safe default: flat band around origin.
        eps = max(origin_price * 0.005, 1.0)
        return HorizonDistribution(
            horizon_h=horizon_h,
            p10=origin_price - eps,
            p25=origin_price - eps / 2,
            p50=origin_price,
            p75=origin_price + eps / 2,
            p90=origin_price + eps,
            expected_range=2 * eps,
            vol_expansion_prob=0.5,
            regime_vote=regime_posterior.state,
        )

    # Per-regime mix.
    pos = regime_posterior.posterior or {regime_posterior.state: 1.0}
    mixed_sigma_mult = sum(
        _REGIME_SIGMA_MULT.get(k, 1.0) * float(v)
        for k, v in pos.items()
    )
    mixed_drift_mult = sum(
        _REGIME_DRIFT_MULT.get(k, 0.0) * float(v)
        for k, v in pos.items()
    )
    # Quantile z-values (standard normal).
    z10 = -1.282
    z25 = -0.674
    z50 = 0.0
    z75 = 0.674
    z90 = 1.282
    sigma_h = sigma_60 * mixed_sigma_mult * math.sqrt(horizon_h / 24.0)
    drift_h = mixed_drift_mult * sigma_60 * math.sqrt(horizon_h / 24.0)
    median = origin_price * math.exp(drift_h)
    p10 = median * math.exp(z10 * sigma_h)
    p25 = median * math.exp(z25 * sigma_h)
    p50 = median
    p75 = median * math.exp(z75 * sigma_h)
    p90 = median * math.exp(z90 * sigma_h)
    return HorizonDistribution(
        horizon_h=horizon_h,
        p10=float(p10),
        p25=float(p25),
        p50=float(p50),
        p75=float(p75),
        p90=float(p90),
        expected_range=float(p90 - p10),
        vol_expansion_prob=volatility_expansion_probability(
            regime_posterior,
            closes=None,  # closed below
        ),
        regime_vote=regime_posterior.state,
    )


def compute_distribution_444(
    *,
    closes: list[float],
    regime_posterior: RegimePosterior111,
    horizons: tuple[int, ...] = HORIZONS_H,
    now: Optional[datetime] = None,
) -> Distribution444:
    """Compute the full distribution packet at the requested horizons."""
    now = now or datetime.now(timezone.utc)
    observed_at = now.isoformat()
    closes_clean = [float(c) for c in closes if isinstance(c, (int, float)) and c > 0]
    if not closes_clean:
        return Distribution444(
            provenance="UNKNOWN",
            observed_at=observed_at,
            reason="no_closes",
            reason_codes=["NO_CLOSES"],
        )
    origin_price = float(closes_clean[-1])
    sigma_60 = _realised_vol_60d(closes_clean)
    horiz: list[HorizonDistribution] = []
    for h in horizons:
        d = quantile_cone_from_regime(
            origin_price=origin_price,
            sigma_60=sigma_60,
            horizon_h=h,
            regime_posterior=regime_posterior,
        )
        horiz.append(d)
    vol_expansion = volatility_expansion_probability(regime_posterior, closes=closes_clean)
    evidence = {
        "n_closes": len(closes_clean),
        "regime_state": regime_posterior.state,
        "regime_confidence": regime_posterior.confidence,
        "vol_expansion_24h": vol_expansion,
        "sigma_60_raw": sigma_60,
        "sigma_60_annualised_pct": sigma_60 * math.sqrt(252) * 100.0,
    }
    reason = (
        f"regime={regime_posterior.state}_conf={regime_posterior.confidence:.3f}"
        f"_sigma60={sigma_60:.4f}"
    )
    return Distribution444(
        origin_price=origin_price,
        sigma_60=sigma_60,
        horizons=horiz,
        evidence=evidence,
        provenance="DERIVED",
        observed_at=observed_at,
        reason=reason,
        reason_codes=[
            f"H{h}" for h in horizons
        ] + ["CONE_BUILT_FROM_REGIME_MIX"],
    )


__all__ = [
    "HORIZONS_H",
    "QUANTILES",
    "HorizonDistribution",
    "Distribution444",
    "quantile_cone_from_regime",
    "compute_distribution_444",
    "expected_range_p10_p90",
    "volatility_expansion_probability",
]
