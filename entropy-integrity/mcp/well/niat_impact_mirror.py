"""
well_niat_impact_mirror — Compare declared intention, acknowledged impact, repair response, and witness acceptance.

Permitted: "Impact was answered primarily with intention language."
Forbidden: "The intention was false."
"""

import uuid
from datetime import datetime, timezone


def well_niat_impact_mirror(
    declared_niat: str,
    acknowledged_impact: str,
    repair_response: str = "",
    witness_acceptance: str = "",
) -> dict:
    """
    Compare niat and impact without inferring hidden motive.

    Args:
        declared_niat: What the actor says they intended
        acknowledged_impact: What impact they acknowledge
        repair_response: What repair they offered
        witness_acceptance: How witnesses received the repair

    Returns:
        entropy_mirror with alignment analysis
    """
    # Analyze niat-impact alignment
    niat_words = set(declared_niat.lower().split())
    impact_words = set(acknowledged_impact.lower().split())
    overlap = niat_words & impact_words
    alignment = len(overlap) / max(len(niat_words | impact_words), 1)

    # Check if impact is answered with intention language
    intention_markers = ["intended", "meant", "wanted", "goal", "purpose", "aim"]
    intention_in_response = sum(
        1 for m in intention_markers
        if m in repair_response.lower() or m in acknowledged_impact.lower()
    )

    impact_answered_by_intention = intention_in_response > 0 and alignment < 0.3

    # Build observation
    observed = []
    if alignment < 0.3:
        observed.append("Low lexical overlap between declared niat and acknowledged impact.")
    if impact_answered_by_intention:
        observed.append("Impact was answered primarily with intention language.")
    if not repair_response:
        observed.append("No repair response documented.")
    if witness_acceptance:
        observed.append(f"Witness acceptance: {witness_acceptance}")

    return {
        "mirror_id": f"nim-{uuid.uuid4().hex[:12]}",
        "status": "SIGNAL" if alignment >= 0.3 else "PATTERN",
        "organ": "WELL",
        "observed": observed,
        "trajectory": {
            "alignment_score": round(alignment, 4),
            "intention_language_ratio": intention_in_response,
        },
        "alternative_explanations": [
            "The actor may be providing context before discussing impact.",
            "Language differences between intention and impact may reflect different frames.",
            "Repair may be documented elsewhere.",
            "Witness acceptance may be communicated through channels not visible here.",
        ],
        "counterevidence": [
            "Actor explicitly accepted responsibility in a later response." if repair_response else "",
        ],
        "reflection": [
            "Was the impact acknowledged before or after the intention was stated?",
            "Did the repair response include specific actions, or only language?",
            "Have witnesses confirmed the repair was sufficient?",
        ],
        "prohibited_conclusion": [
            "Do not say 'the intention was false.'",
            "Do not infer hidden motive from niat-impact gap.",
        ],
        "metadata": {
            "mirrored_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_niat_impact_mirror",
        },
    }
