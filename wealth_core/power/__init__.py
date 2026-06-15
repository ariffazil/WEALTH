"""
WEALTH Core — Power Intelligence.

The missing AGI-grade economic layer.
Detects the invisible geometry of power in any capital decision.

Six dimensions:
- Incentive Map: Who benefits? Who carries downside?
- Capture Detector: Is this advice captured by interest?
- Rent Extraction: Is hidden rent being extracted?
- Opacity Scorer: How opaque is the valuation?
- Coercion Detector: Is time-pressure being used to force action?
- Rule Asymmetry: Who can change the rules? Who cannot?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from .incentive_map import map_incentives
from .capture_detector import detect_capture
from .rent_extraction import detect_rent_extraction
from .opacity_scorer import score_opacity
from .coercion_detector import detect_coercion
from .rule_asymmetry import detect_rule_asymmetry

__all__ = [
    "map_incentives",
    "detect_capture",
    "detect_rent_extraction",
    "score_opacity",
    "detect_coercion",
    "detect_rule_asymmetry",
    "audit_power",
]

POWER_DIMENSIONS = [
    "incentive_asymmetry",
    "capture_risk",
    "rent_extraction",
    "opacity",
    "coercion",
    "rule_asymmetry",
]


def audit_power(
    scenario: str,
    actors: list[str] | None = None,
    context: dict | None = None,
) -> dict:
    """
    Audit the power dynamics of a capital scenario.

    Returns dict with dimension scores, risk levels, and evidence.
    Catches AI advice that sounds balanced but hides weak evidence
    or dangerous allocation geometry.
    """
    ctx = context or {}
    actor_list = actors or []

    dimensions = []
    for eval_fn in [
        map_incentives,
        detect_capture,
        detect_rent_extraction,
        score_opacity,
        detect_coercion,
        detect_rule_asymmetry,
    ]:
        dim = eval_fn(scenario, actor_list, ctx)
        dimensions.append(dim)

    # Determine overall capture risk
    risk_levels = [d.get("risk_level", "LOW") for d in dimensions]
    risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    max_risk = max(risk_levels, key=lambda r: risk_order.get(r, 0))

    return {
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "all_dimensions_present": len(dimensions) == 6,
        "overall_capture_risk": max_risk,
    }
