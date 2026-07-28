"""
wealth_coercive_order_cost — Quantify the hidden cost of apparent order.

Measures: surveillance expenditure, enforcement overhead, employee silence,
turnover, innovation loss, information suppression, tail fragility.
"""

import uuid
from datetime import datetime, timezone


def wealth_coercive_order_cost(
    order_indicators: dict,
    suppression_indicators: dict,
) -> dict:
    """
    Quantify hidden costs of apparent order.

    Args:
        order_indicators: {surveillance_spend, enforcement_headcount, policy_count, approval_layers}
        suppression_indicators: {silence_rate, turnover_rate, innovation_decline, information_friction}

    Returns:
        Coercive order cost assessment
    """
    # Visible order costs
    surveillance = order_indicators.get("surveillance_spend", 0)
    enforcement = order_indicators.get("enforcement_headcount", 0)
    policies = order_indicators.get("policy_count", 0)
    approvals = order_indicators.get("approval_layers", 0)

    # Hidden suppression costs
    silence = suppression_indicators.get("silence_rate", 0)
    turnover = suppression_indicators.get("turnover_rate", 0)
    innovation_decline = suppression_indicators.get("innovation_decline", 0)
    friction = suppression_indicators.get("information_friction", 0)

    # Composite: order cost = visible costs + hidden costs
    visible_cost = min(1.0, (surveillance * 0.3 + enforcement * 0.2 + policies * 0.1 + approvals * 0.1) / 10)
    hidden_cost = min(1.0, (silence * 0.3 + turnover * 0.25 + innovation_decline * 0.25 + friction * 0.2))
    total_cost = min(1.0, visible_cost * 0.4 + hidden_cost * 0.6)

    # Tail fragility: high order + high suppression = brittle
    fragility = visible_cost * hidden_cost

    return {
        "cost_id": f"coc-{uuid.uuid4().hex[:12]}",
        "visible_order_cost": round(visible_cost, 4),
        "hidden_suppression_cost": round(hidden_cost, 4),
        "total_cost": round(total_cost, 4),
        "tail_fragility": round(fragility, 4),
        "interpretation": (
            "HIGH hidden order cost — apparent stability may be masking suppression"
            if hidden_cost > 0.6 else
            "MODERATE order cost — some suppression signals present"
            if hidden_cost > 0.3 else
            "LOW order cost — order appears organic, not coerced"
        ),
        "reflection": [
            "What is the cost of maintaining the current order?",
            "Who is paying that cost?",
            "What happens to this order under unexpected stress?",
            "Are people complying out of agreement or out of fear?",
        ],
        "metadata": {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_coercive_order_cost",
        },
    }
