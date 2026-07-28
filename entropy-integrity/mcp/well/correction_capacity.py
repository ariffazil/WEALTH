"""
well_correction_capacity — Score observable correctability.

Measures: can add context, can revise, can tolerate ambiguity,
can separate self from error, can hear consequence without collapse.
"""

import uuid
from datetime import datetime, timezone


def well_correction_capacity(
    correction_events: list[dict],
    baseline_capacity: float | None = None,
) -> dict:
    """
    Score observable correctability.

    Args:
        correction_events: List of {challenge, response_class, context_added, revision_made}
        baseline_capacity: Baseline correction capacity score

    Returns:
        Correction capacity assessment
    """
    if not correction_events:
        return {
            "capacity_id": f"cc-{uuid.uuid4().hex[:12]}",
            "error": "No correction events provided",
            "capacity_score": None,
        }

    dimensions = {
        "can_add_context": 0.0,
        "can_revise": 0.0,
        "can_tolerate_ambiguity": 0.0,
        "can_separate_self_from_error": 0.0,
        "can_hear_consequence": 0.0,
    }

    for event in correction_events:
        resp = event.get("response_class", "NOT_TESTED")

        # Context addition
        if event.get("context_added") or resp in ("CONTEXT_ADDED", "REFLECTED"):
            dimensions["can_add_context"] += 1.0

        # Revision
        if event.get("revision_made") or resp in ("ACCEPTED", "PARTIALLY_ACCEPTED"):
            dimensions["can_revise"] += 1.0

        # Ambiguity tolerance
        if resp in ("REFLECTED", "CONTEXT_ADDED"):
            dimensions["can_tolerate_ambiguity"] += 1.0

        # Self-error separation
        if resp not in ("WITNESS_ATTACKED", "AUTHORITY_EXPANDED"):
            dimensions["can_separate_self_from_error"] += 1.0

        # Consequence hearing
        if resp not in ("DISMISSED", "WITNESS_ATTACKED"):
            dimensions["can_hear_consequence"] += 1.0

    n = len(correction_events)
    for dim in dimensions:
        dimensions[dim] = round(dimensions[dim] / n, 4)

    capacity_score = round(sum(dimensions.values()) / len(dimensions), 4)

    return {
        "capacity_id": f"cc-{uuid.uuid4().hex[:12]}",
        "capacity_score": capacity_score,
        "dimensions": dimensions,
        "baseline_delta": round(
            abs(capacity_score - baseline_capacity), 4
        ) if baseline_capacity is not None else None,
        "event_count": n,
        "interpretation": (
            "Strong correction capacity" if capacity_score > 0.7 else
            "Moderate correction capacity" if capacity_score > 0.4 else
            "Weak correction capacity — may indicate brittleness"
        ),
        "prohibited": [
            "Cannot declare 'incapable of correction' — capacity is temporal",
            "Cannot use correction capacity as permanent trust classification",
        ],
        "metadata": {
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_correction_capacity",
        },
    }
