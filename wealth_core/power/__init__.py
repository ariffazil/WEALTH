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


# Structural coercion: phrases that indicate incentive geometry
# without explicit time pressure — the coercion_detector blind spot.
STRUCTURAL_COERCION_PATTERNS = [
    "only option",
    "no alternative",
    "must accept",
    "forced to",
    "required to",
    "mandatory participation",
    "compulsory",
    "no exit",
    "cannot leave",
    "locked in",
    "renegotiate impossible",
    "take it or leave it",
    "non-negotiable",
    "binding",
    "irrevocable",
    "waive right",
    "renounce claim",
    "forfeit if you switch",
    "penalty for exiting",
    "exit fee",
    "switching cost",
    "asymmetric information",
    "information asymmetry",
    "one-sided",
    "counterparty discretion",
    "discretionary pricing",
    "unilateral terms",
    "adverse selection",
    "moral hazard",
    "principal agent problem",
    "aligned incentives",
    "your only pension",
    "your only healthcare",
    "government-mandated",
    "by law you must",
]

RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _detect_structural_coercion(scenario: str, dimensions: list[dict]) -> dict:
    """
    Detect structural coercion — incentive geometry that forces action
    WITHOUT explicit time pressure.

    This is the coercion_detector blind spot: coercion=LOW but
    exposure=HIGH via structural relationship.

    RSI-02 FIX: added 2026-06-25.
    """
    scenario_lower = scenario.lower()

    # Pattern match against structural coercion phrases
    structural_hits = [
        p for p in STRUCTURAL_COERCION_PATTERNS
        if p in scenario_lower
    ]

    # Find coercion dimension and non-coercion dimensions
    coercion_dim = next((d for d in dimensions if d.get("dimension") == "coercion"), None)
    other_dims = [d for d in dimensions if d.get("dimension") != "coercion"]

    coercion_is_low = (
        coercion_dim is None
        or coercion_dim.get("risk_level", "LOW") == "LOW"
    )
    has_high_exposure = any(
        RISK_ORDER.get(d.get("risk_level", "LOW"), 0) >= RISK_ORDER["HIGH"]
        for d in other_dims
    )

    # Condition: coercion=LOW but other dimension exposure=HIGH
    structural_detected = (
        coercion_is_low
        and has_high_exposure
        and len(structural_hits) > 0
    )

    if structural_detected:
        high_exposure_dims = [
            d["dimension"] for d in other_dims
            if RISK_ORDER.get(d.get("risk_level", "LOW"), 0) >= RISK_ORDER["HIGH"]
        ]
        return {
            "structural_coercion_detected": True,
            "structural_coercion_risk": "HIGH" if len(structural_hits) >= 2 else "MEDIUM",
            "evidence": (
                f"Coercion=LOW but structural pressure detected via incentive geometry. "
                f"Patterns matched: {structural_hits}. "
                f"High-exposure dimensions: {high_exposure_dims}."
            ),
            "structural_patterns": structural_hits,
            "coercion_blind_spot": True,
        }

    return {
        "structural_coercion_detected": False,
        "structural_coercion_risk": "LOW",
        "evidence": "No structural coercion detected",
        "structural_patterns": [],
        "coercion_blind_spot": False,
    }


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

    RSI-02 FIX (2026-06-25): Added structural_coercion check —
    detects incentive geometry coercion when explicit coercion=LOW
    but exposure=HIGH. The coercion_detector is blind to structural
    pressure (no time-pressure keywords) but the power audit is not.
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

    # RSI-02 FIX: structural coercion check
    structural = _detect_structural_coercion(scenario, dimensions)

    # Determine overall capture risk
    risk_levels = [d.get("risk_level", "LOW") for d in dimensions]
    if structural["structural_coercion_detected"]:
        # Upgrade overall risk if structural coercion found
        struct_rank = RISK_ORDER.get(structural["structural_coercion_risk"], 1)
        risk_levels.append(structural["structural_coercion_risk"])

    max_risk = max(risk_levels, key=lambda r: RISK_ORDER.get(r, 0))

    return {
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "all_dimensions_present": len(dimensions) == 6,
        "overall_capture_risk": max_risk,
        # RSI-02 FIX: structural coercion fields
        "structural_coercion_detected": structural["structural_coercion_detected"],
        "structural_coercion_risk": structural["structural_coercion_risk"],
        "structural_coercion_evidence": structural["evidence"],
        "structural_patterns": structural["structural_patterns"],
        "coercion_blind_spot": structural["coercion_blind_spot"],
    }
