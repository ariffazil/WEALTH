"""
WEALTH Core — Cascade Model Engine.

Pure computation: no I/O, no MCP, no side effects.

Models feedback loops between institutional stress dimensions.
Detects spiral vs linear decline vs recovery.

The institutional collapse spiral:
  financial stress → rightsizing → governance erosion →
  intelligence compromise → external exploitation →
  more financial stress → spiral

Each dimension feeds into the next. A spiral is detected when
the product of consecutive deltas is positive (all declining)
AND the magnitude is accelerating.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

_CONFIDENCE_CAP = 0.90


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _compute_deltas(
    timeline: List[Dict[str, Any]], key: str
) -> List[float]:
    """Compute first differences for a given key across timeline."""
    values = [t.get(key, 0.0) for t in timeline]
    return [values[i + 1] - values[i] for i in range(len(values) - 1)]


def _detect_cascade_type(
    timeline: List[Dict[str, Any]],
) -> str:
    """
    Detect whether the trajectory is LINEAR, SPIRAL, or RECOVERING.

    SPIRAL: all stress dimensions worsening simultaneously with acceleration.
    RECOVERING: at least 3 dimensions improving in last 2 periods.
    LINEAR: otherwise.
    """
    if len(timeline) < 3:
        return "LINEAR"  # Insufficient data for spiral detection

    stress_keys = [
        "financial_stress",
        "legal_exposure",
        "external_exploitation",
    ]
    capacity_keys = ["governance_capacity", "workforce_stability"]

    # Check last 2 periods for trend
    last_two = timeline[-2:]

    # For stress keys: increasing is bad
    stress_worsening = 0
    for key in stress_keys:
        if len(last_two) >= 2:
            delta = last_two[-1].get(key, 0) - last_two[-2].get(key, 0)
            if delta > 0.02:  # threshold to avoid noise
                stress_worsening += 1

    # For capacity keys: decreasing is bad
    capacity_declining = 0
    for key in capacity_keys:
        if len(last_two) >= 2:
            delta = last_two[-1].get(key, 0) - last_two[-2].get(key, 0)
            if delta < -0.02:
                capacity_declining += 1

    # Check acceleration (second derivative)
    accelerating = 0
    for key in stress_keys:
        deltas = _compute_deltas(timeline, key)
        if len(deltas) >= 2:
            second_delta = deltas[-1] - deltas[-2]
            if second_delta > 0.01:  # Accelerating increase in stress
                accelerating += 1

    # SPIRAL: stress worsening + capacity declining + acceleration
    if stress_worsening >= 2 and capacity_declining >= 1 and accelerating >= 1:
        return "SPIRAL"

    # Check for recovery
    improving = 0
    for key in stress_keys:
        if len(last_two) >= 2:
            delta = last_two[-1].get(key, 0) - last_two[-2].get(key, 0)
            if delta < -0.02:
                improving += 1
    for key in capacity_keys:
        if len(last_two) >= 2:
            delta = last_two[-1].get(key, 0) - last_two[-2].get(key, 0)
            if delta > 0.02:
                improving += 1

    if improving >= 3:
        return "RECOVERING"

    return "LINEAR"


def _compute_acceleration_factor(timeline: List[Dict[str, Any]]) -> float:
    """
    Compute acceleration factor: how fast the spiral is tightening.

    Positive = accelerating decline. Negative = decelerating.
    Returns float, not clamped (can exceed 1.0 for extreme spirals).
    """
    if len(timeline) < 3:
        return 0.0

    # Average second derivative across all dimensions
    all_keys = [
        "financial_stress",
        "governance_capacity",
        "workforce_stability",
        "legal_exposure",
        "external_exploitation",
    ]

    accelerations = []
    for key in all_keys:
        deltas = _compute_deltas(timeline, key)
        if len(deltas) >= 2:
            # For capacity keys, declining is negative acceleration
            second = deltas[-1] - deltas[-2]
            # Normalize: for stress keys positive is bad, for capacity keys negative is bad
            if key in ("governance_capacity", "workforce_stability"):
                second = -second  # Flip so positive = bad
            accelerations.append(second)

    if not accelerations:
        return 0.0

    return round(sum(accelerations) / len(accelerations), 4)


def _find_weakest_link(timeline: List[Dict[str, Any]]) -> str:
    """Find the dimension that declined most in the last period."""
    if len(timeline) < 2:
        return "insufficient_data"

    last = timeline[-1]
    prev = timeline[-2]

    # For stress dimensions: higher is worse
    stress_dims = {
        "financial_stress": last.get("financial_stress", 0) - prev.get("financial_stress", 0),
        "legal_exposure": last.get("legal_exposure", 0) - prev.get("legal_exposure", 0),
        "external_exploitation": last.get("external_exploitation", 0) - prev.get("external_exploitation", 0),
    }

    # For capacity dimensions: lower is worse
    capacity_dims = {
        "governance_capacity": prev.get("governance_capacity", 0) - last.get("governance_capacity", 0),
        "workforce_stability": prev.get("workforce_stability", 0) - last.get("workforce_stability", 0),
    }

    all_deltas = {**stress_dims, **capacity_dims}
    if not all_deltas:
        return "insufficient_data"

    return max(all_deltas, key=all_deltas.get)  # type: ignore[arg-type]


def _project_trajectory(
    timeline: List[Dict[str, Any]], periods: int = 4
) -> List[float]:
    """
    Project composite stress trajectory forward.

    Uses linear extrapolation of recent trend (last 3 periods).
    Returns list of projected composite stress values.
    """
    if len(timeline) < 2:
        return []

    # Compute composite for each period
    composites = []
    for t in timeline:
        composite = (
            t.get("financial_stress", 0) * 0.30
            + (1.0 - t.get("governance_capacity", 1.0)) * 0.25
            + (1.0 - t.get("workforce_stability", 1.0)) * 0.20
            + t.get("legal_exposure", 0) * 0.15
            + t.get("external_exploitation", 0) * 0.10
        )
        composites.append(composite)

    # Linear trend from last 3 points (or fewer)
    recent = composites[-min(3, len(composites)):]
    if len(recent) < 2:
        return [round(composites[-1], 4)] * periods

    # Average delta
    deltas = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    avg_delta = sum(deltas) / len(deltas)

    # Project forward, clamped to [0, 1]
    projected = []
    current = composites[-1]
    for _ in range(periods):
        current = _clamp(current + avg_delta)
        projected.append(round(current, 4))

    return projected


def _simulate_intervention(
    timeline: List[Dict[str, Any]],
    intervention: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simulate the impact of an intervention on the cascade.

    Returns projected trajectory with and without intervention.
    """
    action = intervention.get("action", "")
    intervention_period = intervention.get("period", 3)

    # Without intervention
    baseline = _project_trajectory(timeline, periods=intervention_period)

    # With intervention: model the effect
    # Different interventions have different impact profiles
    impact_factor = 0.0
    affected_dimension = "unknown"

    if action == "rightsizing_pause":
        # Pausing rightsizing stabilizes workforce, slightly helps governance
        impact_factor = 0.08
        affected_dimension = "workforce_stability"
    elif action == "governance_reform":
        # Governance reform: appoint independent NEDs, restructure committees
        impact_factor = 0.12
        affected_dimension = "governance_capacity"
    elif action == "legal_consolidation":
        # Consolidate legal strategy: reduce litigation exposure
        impact_factor = 0.10
        affected_dimension = "legal_exposure"
    elif action == "retention_program":
        # Retain key personnel: slow workforce destabilization
        impact_factor = 0.06
        affected_dimension = "workforce_stability"
    elif action == "counterparty_renegotiation":
        # Renegotiate with counterparties: reduce exploitation pressure
        impact_factor = 0.07
        affected_dimension = "external_exploitation"
    else:
        # Generic intervention: modest effect
        impact_factor = 0.05
        affected_dimension = "general"

    # Apply intervention effect: reduce projected stress by impact_factor per period
    # Effect accumulates but with diminishing returns
    with_intervention = []
    for i, base_val in enumerate(baseline):
        # Diminishing returns: each period the marginal effect decreases
        period_effect = impact_factor * (0.7 ** i)
        with_intervention.append(round(_clamp(base_val - period_effect), 4))

    return {
        "baseline_trajectory": baseline,
        "intervention_trajectory": with_intervention,
        "intervention_action": action,
        "affected_dimension": affected_dimension,
        "estimated_improvement": round(
            sum(baseline) - sum(with_intervention), 4
        ) if baseline and with_intervention else 0.0,
    }


def compute_cascade(
    timeline: List[Dict[str, Any]],
    intervention_scenario: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Model cascade dynamics from institutional stress timeline.

    Returns:
      - cascade_type: LINEAR/SPIRAL/RECOVERING
      - acceleration_factor: how fast the spiral is tightening
      - weakest_link: dimension declining fastest
      - projected_trajectory: list of projected composite stress values
      - intervention_impact: dict if intervention provided
      - confidence: capped at 0.90
    """
    cascade_type = _detect_cascade_type(timeline)
    acceleration = _compute_acceleration_factor(timeline)
    weakest = _find_weakest_link(timeline)
    trajectory = _project_trajectory(timeline)

    result: Dict[str, Any] = {
        "cascade_type": cascade_type,
        "acceleration_factor": acceleration,
        "weakest_link": weakest,
        "projected_trajectory": trajectory,
        "timeline_periods": len(timeline),
    }

    if intervention_scenario:
        result["intervention_impact"] = _simulate_intervention(
            timeline, intervention_scenario
        )

    # Confidence: lower with fewer data points
    confidence = min(_CONFIDENCE_CAP, len(timeline) / 5.0)
    result["confidence"] = round(confidence, 4)
    result["confidence_note"] = "Capped at 0.90 per F7 HUMILITY"

    return result
