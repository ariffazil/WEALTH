"""
wealth_responsibility_ledger — Track who proposed, approved, funded, executed,
benefited, knew, could stop, and later claimed 'the system decided.'
"""

import uuid
from datetime import datetime, timezone


ROLES = ["proposed", "approved", "funded", "executed", "benefited", "knew", "could_stop", "claimed_system"]


def wealth_responsibility_ledger(
    decision_ref: str,
    actors: list[dict],
) -> dict:
    """
    Build a responsibility ledger for a decision.

    Args:
        decision_ref: Decision reference
        actors: [{ref, roles: [str], notes: str}]

    Returns:
        Responsibility ledger with gap analysis
    """
    # Build role coverage matrix
    role_coverage = {role: [] for role in ROLES}
    for actor in actors:
        ref = actor.get("ref", "unknown")
        for role in actor.get("roles", []):
            if role in role_coverage:
                role_coverage[role].append(ref)

    # Identify gaps
    gaps = []
    for role, refs in role_coverage.items():
        if not refs:
            gaps.append(f"No one identified as '{role}'")

    # Identify "system decided" laundering
    system_decided = [
        a for a in actors
        if "claimed_system" in a.get("roles", [])
    ]

    # Concentration analysis
    actor_count = len(actors)
    max_roles = max(len(a.get("roles", [])) for a in actors) if actors else 0
    concentration = max_roles / max(len(ROLES), 1)

    return {
        "ledger_id": f"rl-{uuid.uuid4().hex[:12]}",
        "decision_ref": decision_ref,
        "role_coverage": role_coverage,
        "gaps": gaps,
        "system_decided_claims": [a.get("ref") for a in system_decided],
        "actor_count": actor_count,
        "role_concentration": round(concentration, 4),
        "interpretation": (
            "Responsibility is diffused — no single actor bears full accountability"
            if len(gaps) > 3 else
            "Responsibility is concentrated — some roles may be under-covered"
            if concentration > 0.5 else
            "Responsibility distribution appears reasonable"
        ),
        "metadata": {
            "ledgered_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_responsibility_ledger",
        },
    }
