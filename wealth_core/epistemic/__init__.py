"""
WEALTH Core — Epistemic Intelligence.

The missing layer: detecting when institutions systematically learn too late.

Seven dimensions:
- Model Ownership: Who proposed it defends it (identity risk)
- Signal Demotion: Evidence seen but ranked secondary
- Analog Anchoring: Success template overrides evidence
- Pipeline Inertia: Approval system makes pivot hard
- Governance Constraint: Challenge without breaking system
- Contradiction Density: Wells disagreeing with models
- Zweig Alignment: Incentive-truth mapping (3 rules)

People do not defend what is true.
People defend what their incentives make survivable.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from .model_ownership import detect_model_ownership
from .signal_demotion import detect_signal_demotion
from .analog_anchoring import detect_analog_anchoring
from .pipeline_inertia import detect_pipeline_inertia
from .governance_constraint import detect_governance_constraint
from .contradiction_density import detect_contradiction_density
from .zweig_mapping import map_zweig_alignment

__all__ = [
    "detect_model_ownership",
    "detect_signal_demotion",
    "detect_analog_anchoring",
    "detect_pipeline_inertia",
    "detect_governance_constraint",
    "detect_contradiction_density",
    "map_zweig_alignment",
    "audit_epistemic",
]

EPISTEMIC_DIMENSIONS = [
    "model_ownership",
    "signal_demotion",
    "analog_anchoring",
    "pipeline_inertia",
    "governance_constraint",
    "contradiction_density",
    "zweig_alignment",
]

RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def audit_epistemic(
    scenario: str,
    actors: list[str] | None = None,
    context: dict | None = None,
) -> dict:
    """
    Audit epistemic bias in institutional decision-making.

    Returns dict with 7 dimension scores, risk levels, and evidence.
    Detects: model ownership, signal demotion, analog anchoring,
    pipeline inertia, governance constraint, contradiction density,
    and Zweig incentive-truth alignment.

    This tool detects EPISTEMIC bias — when institutions systematically
    learn too late. It does NOT detect financial capture (use wealth_power_audit).
    """
    ctx = context or {}
    actor_list = actors or []

    dimensions = []
    for eval_fn in [
        detect_model_ownership,
        detect_signal_demotion,
        detect_analog_anchoring,
        detect_pipeline_inertia,
        detect_governance_constraint,
        detect_contradiction_density,
        map_zweig_alignment,
    ]:
        dim = eval_fn(scenario, actor_list, ctx)
        dimensions.append(dim)

    # Determine overall epistemic risk
    risk_levels = [d.get("risk_level", "LOW") for d in dimensions]
    max_risk = max(risk_levels, key=lambda r: RISK_ORDER.get(r, 0))

    # Compute epistemic integrity score (inverse of bias)
    # LOW=1, MEDIUM=0.66, HIGH=0.33, CRITICAL=0
    RISK_TO_INTEGRITY = {"LOW": 1.0, "MEDIUM": 0.66, "HIGH": 0.33, "CRITICAL": 0.0}
    integrity_scores = [RISK_TO_INTEGRITY.get(r, 0.5) for r in risk_levels]
    epistemic_integrity = round(sum(integrity_scores) / len(integrity_scores), 3)

    # Identify dominant bias modes
    dominant_biases = []
    for dim in dimensions:
        if RISK_ORDER.get(dim.get("risk_level", "LOW"), 0) >= RISK_ORDER["HIGH"]:
            dominant_biases.append(
                {
                    "dimension": dim["dimension"],
                    "risk": dim["risk_level"],
                    "evidence": dim.get("evidence", "")[:200],
                }
            )

    # Zweig verdict
    zweig_dim = next(
        (d for d in dimensions if d["dimension"] == "zweig_alignment"), None
    )
    zweig_verdict = "unknown"
    if zweig_dim:
        zweig_verdict = zweig_dim.get("truth_filter", "unknown")

    return {
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "all_dimensions_present": len(dimensions) == 7,
        "overall_epistemic_risk": max_risk,
        "epistemic_integrity": epistemic_integrity,
        "dominant_biases": dominant_biases,
        "dominant_bias_count": len(dominant_biases),
        "zweig_verdict": zweig_verdict,
        "summary": _build_summary(
            dimensions, max_risk, epistemic_integrity, zweig_verdict
        ),
    }


def _build_summary(
    dimensions: list[dict],
    max_risk: str,
    integrity: float,
    zweig_verdict: str,
) -> str:
    """Build human-readable summary of epistemic audit."""
    high_dims = [
        d["dimension"]
        for d in dimensions
        if RISK_ORDER.get(d.get("risk_level", "LOW"), 0) >= RISK_ORDER["HIGH"]
    ]

    if not high_dims:
        return (
            f"Epistemic integrity: {integrity:.0%}. "
            f"No dominant bias detected. "
            f"Zweig filter: {zweig_verdict}."
        )

    bias_list = ", ".join(high_dims)
    return (
        f"Epistemic integrity: {integrity:.0%}. "
        f"CRITICAL: {len(high_dims)} bias dimensions elevated: {bias_list}. "
        f"Zweig filter: {zweig_verdict}. "
        f"Institution may be systematically learning too late."
    )
