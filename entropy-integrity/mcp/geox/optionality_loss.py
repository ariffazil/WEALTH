"""
geox_optionality_loss — Measure destroyed future physical options.

Measures: sterilised reserves, lost aquifer use, irreversible land conversion,
inaccessible remediation pathways, reduced resilience, increased hazard exposure.
"""

import uuid
from datetime import datetime, timezone


def geox_optionality_loss(
    action_description: str,
    options_destroyed: list[dict],
    options_preserved: list[dict] | None = None,
) -> dict:
    """
    Measure physical optionality loss.

    Args:
        action_description: What action was taken
        options_destroyed: [{option, reversibility, value, time_horizon}]
        options_preserved: [{option, value}]

    Returns:
        Optionality loss assessment
    """
    destroyed_value = sum(o.get("value", 0) for o in options_destroyed)
    preserved_value = sum(o.get("value", 0) for o in (options_preserved or []))

    irreversible_destroyed = [
        o for o in options_destroyed if o.get("reversibility") == "IRREVERSIBLE"
    ]

    total_options = len(options_destroyed) + len(options_preserved or [])
    loss_ratio = len(options_destroyed) / max(total_options, 1)

    # Irreversibility amplification
    irreversible_ratio = len(irreversible_destroyed) / max(len(options_destroyed), 1)

    return {
        "loss_id": f"ol-{uuid.uuid4().hex[:12]}",
        "action": action_description,
        "options_destroyed_count": len(options_destroyed),
        "options_preserved_count": len(options_preserved or []),
        "loss_ratio": round(loss_ratio, 4),
        "irreversible_ratio": round(irreversible_ratio, 4),
        "destroyed_value": destroyed_value,
        "preserved_value": preserved_value,
        "irreversible_options": [o.get("option") for o in irreversible_destroyed],
        "interpretation": (
            "HIGH optionality loss — many future paths permanently closed"
            if loss_ratio > 0.7 or irreversible_ratio > 0.5 else
            "MODERATE optionality loss — some future paths closed"
            if loss_ratio > 0.3 else
            "LOW optionality loss — most future paths preserved"
        ),
        "reflection": [
            "What future options were destroyed by this action?",
            "Can the destroyed options be recovered?",
            "What would a future decision-maker wish had been preserved?",
        ],
        "metadata": {
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "geox_optionality_loss",
        },
    }
