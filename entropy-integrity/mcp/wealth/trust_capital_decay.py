"""
wealth_trust_capital_decay — Treat trust as capital with formation cost,
betrayal shock, recovery half-life, spillover, option loss, coordination overhead.
"""

import uuid
from datetime import datetime, timezone


def wealth_trust_capital_decay(
    trust_events: list[dict],
    current_trust_balance: float = 0.5,
) -> dict:
    """
    Model trust as capital with decay dynamics.

    Args:
        trust_events: [{event_type, magnitude, timestamp}]
            event_type: formation | betrayal | recovery | spillover
        current_trust_balance: Current trust level 0.0-1.0

    Returns:
        Trust capital analysis
    """
    formation_cost = 0.0
    betrayal_shock = 0.0
    recovery_accumulated = 0.0
    spillover = 0.0

    for event in trust_events:
        etype = event.get("event_type", "unknown")
        magnitude = event.get("magnitude", 0.0)

        if etype == "formation":
            formation_cost += magnitude
        elif etype == "betrayal":
            betrayal_shock += magnitude
        elif etype == "recovery":
            recovery_accumulated += magnitude
        elif etype == "spillover":
            spillover += magnitude

    # Trust balance trajectory
    net_trust = current_trust_balance
    if betrayal_shock > 0:
        # Recovery half-life: trust recovers slower than it decays
        recovery_needed = betrayal_shock * 2  # double the recovery needed
        recovery_ratio = recovery_accumulated / max(recovery_needed, 0.01)
        net_trust = max(0.0, current_trust_balance - betrayal_shock + (recovery_accumulated * 0.5))

    # Coordination overhead: low trust = high overhead
    coordination_overhead = max(0.0, 1.0 - current_trust_balance)

    # Option loss: trust enables options; distrust closes them
    option_loss = max(0.0, betrayal_shock - recovery_accumulated) * 0.5

    return {
        "capital_id": f"tcd-{uuid.uuid4().hex[:12]}",
        "current_balance": round(current_trust_balance, 4),
        "formation_cost": round(formation_cost, 4),
        "betrayal_shock": round(betrayal_shock, 4),
        "recovery_accumulated": round(recovery_accumulated, 4),
        "recovery_ratio": round(recovery_ratio, 4) if betrayal_shock > 0 else None,
        "spillover": round(spillover, 4),
        "coordination_overhead": round(coordination_overhead, 4),
        "option_loss": round(option_loss, 4),
        "net_trajectory": round(net_trust, 4),
        "interpretation": (
            "Trust is rebuilding — recovery on track" if net_trust > 0.6 else
            "Trust is fragile — betrayal shock not yet recovered"
            if betrayal_shock > recovery_accumulated else
            "Trust is depleted — significant investment needed"
        ),
        "metadata": {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_trust_capital_decay",
        },
    }
