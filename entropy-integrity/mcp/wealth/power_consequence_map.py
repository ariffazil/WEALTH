"""
wealth_power_consequence_map — Map decision authority, economic upside, downside exposure,
who bears irreversible cost, compensation versus harm, exit rights, concentration of veto power.

Key metric: consequence_gap = decision_power x benefit_capture x harm_distance x non_accountability
"""

import uuid
from datetime import datetime, timezone


def wealth_power_consequence_map(
    decision_makers: list[dict],
    beneficiaries: list[dict],
    cost_bearers: list[dict],
    veto_holders: list[dict] | None = None,
) -> dict:
    """
    Map power and consequence distribution.

    Args:
        decision_makers: [{ref, authority_class, decision_power}]
        beneficiaries: [{ref, benefit_type, magnitude, exit_rights}]
        cost_bearers: [{ref, cost_type, magnitude, reversibility, compensation}]
        veto_holders: [{ref, veto_scope, accountable}]

    Returns:
        Power-consequence map with consequence_gap metric
    """
    # Decision power concentration
    if decision_makers:
        max_power = max(d.get("decision_power", 0.5) for d in decision_makers)
        power_concentration = max_power / max(len(decision_makers), 1)
    else:
        power_concentration = 0.5

    # Benefit capture
    if beneficiaries:
        total_benefit = sum(b.get("magnitude", 0) for b in beneficiaries)
        max_benefit = max(b.get("magnitude", 0) for b in beneficiaries)
        benefit_concentration = max_benefit / max(total_benefit, 0.01)
    else:
        benefit_concentration = 0.0

    # Harm distance
    if cost_bearers:
        irreversible_count = sum(1 for c in cost_bearers if c.get("reversibility") == "IRREVERSIBLE")
        harm_distance = irreversible_count / len(cost_bearers)
        uncompensated = sum(
            1 for c in cost_bearers
            if not c.get("compensation") or c.get("compensation") == "NONE"
        )
        compensation_gap = uncompensated / len(cost_bearers)
    else:
        harm_distance = 0.0
        compensation_gap = 0.0

    # Exit rights
    if beneficiaries:
        exit_available = sum(1 for b in beneficiaries if b.get("exit_rights", False))
        exit_ratio = exit_available / len(beneficiaries)
    else:
        exit_ratio = 1.0

    # Veto concentration
    veto_concentration = 0.0
    if veto_holders:
        accountable_vetoes = sum(1 for v in veto_holders if v.get("accountable", False))
        veto_concentration = 1.0 - (accountable_vetoes / max(len(veto_holders), 1))

    # Consequence gap composite
    consequence_gap = min(1.0, (
        power_concentration * 0.3 +
        benefit_concentration * 0.25 +
        harm_distance * 0.25 +
        compensation_gap * 0.2
    ))

    return {
        "map_id": f"pcm-{uuid.uuid4().hex[:12]}",
        "power_concentration": round(power_concentration, 4),
        "benefit_concentration": round(benefit_concentration, 4),
        "harm_distance": round(harm_distance, 4),
        "compensation_gap": round(compensation_gap, 4),
        "exit_ratio": round(exit_ratio, 4),
        "veto_concentration": round(veto_concentration, 4),
        "consequence_gap": round(consequence_gap, 4),
        "interpretation": (
            "HIGH consequence gap — decision-makers are insulated from consequences"
            if consequence_gap > 0.7 else
            "MODERATE consequence gap — some displacement present"
            if consequence_gap > 0.4 else
            "LOW consequence gap — consequences relatively well-integrated"
        ),
        "decision_makers_count": len(decision_makers),
        "beneficiaries_count": len(beneficiaries),
        "cost_bearers_count": len(cost_bearers),
        "metadata": {
            "mapped_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_power_consequence_map",
        },
    }
