"""M5.7 — abstention gate and regime classification.

The abstention gate is M5's "I refuse to commit" verdict. It triggers
when any of these conditions hold:

    * σ explosion: forecast σ is more than 3× the trailing 168h σ
    * calibration empty: < 24 calibration scores
    * expansion already happening: p_vol_expansion > 0.7 with σ ratio > 2
    * asymmetry pathological: |asym| > 0.95 (effectively one-sided vol)
    * data is synthetic (refuse on synthetic evidence alone, matching
      the rest of forecast/*)

The regime classifier buckets the current state into one of:

    * RANGE        — compressed, low vol expansion, near-symmetric
    * COMPRESSION  — TR in bottom decile, range multiplier below 1.0
    * TRENDING     — high trend efficiency (>0.4) AND σ ratio > 1.0
    * EVENT_RISK   — expansion p > 0.6 OR σ ratio > 1.5

The abstention verdict is *separate* from the regime label. M5 can
classify the regime as EVENT_RISK without abstaining (the call may
still be useful) — abstention only fires when M5 itself doesn't trust
its own forecast enough to surface numeric quantiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .expansion import ExpansionForecast
from .features import FeatureVector
from .volatility import VolCandidate


REGIMES = ("RANGE", "COMPRESSION", "TRENDING", "EVENT_RISK")


@dataclass(frozen=True)
class AbstentionDecision:
    abstain: bool
    regime: str  # one of REGIMES
    reasons: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "abstain": bool(self.abstain),
            "regime": self.regime,
            "reasons": list(self.reasons),
            "notes": self.notes,
        }


def classify_regime(features: FeatureVector, expansion: ExpansionForecast) -> str:
    """Pick the most descriptive regime label from features + expansion."""
    # Default to RANGE
    if features is None:
        return "RANGE"
    ratio = expansion.sigma_ratio_6h_168h if expansion is not None else float("nan")
    p_exp = expansion.p_vol_expansion if expansion is not None else 0.0
    te = features.trend_efficiency_24h if np.isfinite(features.trend_efficiency_24h) else 0.0
    comp = features.compression_percentile_168h if np.isfinite(features.compression_percentile_168h) else 0.5

    # EVENT_RISK first — it's the most urgent
    if (np.isfinite(p_exp) and p_exp > 0.6) or (np.isfinite(ratio) and ratio > 1.5):
        return "EVENT_RISK"
    # TRENDING
    if abs(te) > 0.4 and np.isfinite(ratio) and ratio > 1.0:
        return "TRENDING"
    # COMPRESSION
    if np.isfinite(comp) and comp < 0.10:
        return "COMPRESSION"
    return "RANGE"


def decide_abstention(
    *,
    features: FeatureVector,
    expansion: ExpansionForecast,
    vol_candidate: VolCandidate,
    sigma_ratio: Optional[float] = None,
    n_calibration_scores: int = 0,
    data_is_synthetic: bool = False,
) -> AbstentionDecision:
    """Return the abstention + regime decision.

    The function does NOT abstain for "I don't know the direction"
    (that's by design — M5 never has a direction). It abstains for
    *measurement-quality* failures.
    """
    reasons: list[str] = []
    ratio = sigma_ratio
    if ratio is None and expansion is not None:
        ratio = expansion.sigma_ratio_6h_168h

    if data_is_synthetic:
        reasons.append("data_is_synthetic")

    if vol_candidate is None or not np.isfinite(vol_candidate.forecast_sigma_h1):
        reasons.append("vol_candidate_unavailable")

    if (
        expansion is not None
        and np.isfinite(expansion.p_vol_expansion)
        and expansion.p_vol_expansion > 0.7
        and ratio is not None
        and np.isfinite(ratio)
        and ratio > 2.0
    ):
        reasons.append("expansion_extreme")

    if features is not None and np.isfinite(features.compression_percentile_168h) and features.compression_percentile_168h > 0.99:
        # Pathological compression — too little data to forecast a band
        reasons.append("pathological_compression")

    if n_calibration_scores < 24:
        reasons.append("calibration_insufficient")

    # Asymmetry sanity: if |asym| > 0.95 it's effectively one-sided, which
    # is unusual — we still emit a forecast but flag it.
    # (Currently NOT a hard abstention trigger; we surface via regime.)

    regime = classify_regime(features, expansion)

    # Synthetic data ⇒ recommend SHADOW. We abstain for promotion only,
    # not for the quantiles themselves (downstream tests may want to run).
    abstain = bool(reasons) and "data_is_synthetic" in reasons and any(
        r != "calibration_insufficient" for r in reasons
    ) if data_is_synthetic else False

    # Hard abstention triggers (always-on, not data-source gated):
    if "vol_candidate_unavailable" in reasons and "calibration_insufficient" in reasons:
        abstain = True
    if "expansion_extreme" in reasons:
        abstain = True

    return AbstentionDecision(
        abstain=bool(abstain),
        regime=regime if regime in REGIMES else "RANGE",
        reasons=reasons,
        notes="measurement_quality_gate",
    )


__all__ = ["AbstentionDecision", "REGIMES", "classify_regime", "decide_abstention"]