"""
wealth_entropy_externality — Measure disorder exported to others
while the controlling actor reports local efficiency.

Captures: locally ordered, globally entropic.
"""

import uuid
from datetime import datetime, timezone


def wealth_entropy_externality(
    actor_ref: str,
    local_efficiency_claims: dict,
    exported_costs: list[dict],
) -> dict:
    """
    Measure entropy externality — disorder exported while reporting local order.

    Args:
        actor_ref: The actor claiming local efficiency
        local_efficiency_claims: {metric, value, measurement_scope}
        exported_costs: [{recipient, cost_type, magnitude, reversibility}]

    Returns:
        Externality assessment
    """
    # Local order score
    local_order = sum(
        c.get("value", 0) for c in local_efficiency_claims.values()
    ) / max(len(local_efficiency_claims), 1) if isinstance(local_efficiency_claims, dict) else 0.5

    # Exported disorder
    if exported_costs:
        total_exported = sum(c.get("magnitude", 0) for c in exported_costs)
        irreversible_exports = sum(
            1 for c in exported_costs if c.get("reversibility") == "IRREVERSIBLE"
        )
        externality_ratio = total_exported / max(len(exported_costs), 1)
        irreversibility_ratio = irreversible_exports / len(exported_costs)
    else:
        externality_ratio = 0.0
        irreversibility_ratio = 0.0

    # Entropy gap: high local order + high exported disorder
    entropy_gap = local_order * externality_ratio

    return {
        "externality_id": f"ee-{uuid.uuid4().hex[:12]}",
        "actor_ref": actor_ref,
        "local_order_score": round(local_order, 4),
        "externality_ratio": round(externality_ratio, 4),
        "irreversibility_ratio": round(irreversibility_ratio, 4),
        "entropy_gap": round(entropy_gap, 4),
        "exported_to": [c.get("recipient", "unknown") for c in exported_costs],
        "interpretation": (
            "HIGH entropy externality — local order achieved by exporting disorder"
            if entropy_gap > 0.5 else
            "MODERATE externality — some cost displacement present"
            if entropy_gap > 0.2 else
            "LOW externality — costs appear internalized"
        ),
        "reflection": [
            "Who bears the cost of this efficiency?",
            "Can the cost-bearers exit the arrangement?",
            "Would the actor accept this arrangement if they were the cost-bearer?",
        ],
        "metadata": {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_entropy_externality",
        },
    }
