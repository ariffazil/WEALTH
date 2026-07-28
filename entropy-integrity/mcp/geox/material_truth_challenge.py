"""
geox_material_truth_challenge — Challenge institutional claims against Earth measurements.

Pattern: "The institution claims low harm, but Earth measurements show irreversible loss."
"""

import uuid
from datetime import datetime, timezone


def geox_material_truth_challenge(
    institutional_claim: str,
    earth_measurements: list[dict],
    measurement_confidence: float = 0.5,
) -> dict:
    """
    Challenge institutional claims against material reality.

    Args:
        institutional_claim: What the institution claims
        earth_measurements: [{measurement, value, unit, source, confidence}]
        measurement_confidence: Overall confidence in measurements

    Returns:
        Material truth challenge
    """
    # Extract key claims
    claim_lower = institutional_claim.lower()
    claim_words = set(claim_lower.split())

    # Check measurements against claim
    contradictions = []
    supporting = []

    low_harm_words = ["low", "minimal", "negligible", "safe", "no significant", "acceptable"]
    irreversible_words = ["irreversible", "permanent", "cannot be reversed", "sterilised"]

    claims_low_harm = any(w in claim_lower for w in low_harm_words)

    for measurement in earth_measurements:
        m_desc = measurement.get("measurement", "").lower()
        m_value = measurement.get("value", 0)
        m_confidence = measurement.get("confidence", 0.5)

        # Check if measurement contradicts low-harm claim
        if claims_low_harm:
            if any(w in m_desc for w in irreversible_words):
                contradictions.append({
                    "claim": institutional_claim,
                    "measurement": f"{measurement.get('measurement')}: {m_value} {measurement.get('unit', '')}",
                    "contradiction_type": "low_harm_vs_irreversible",
                    "confidence": m_confidence,
                })
            elif m_value > 0.7:  # high impact
                contradictions.append({
                    "claim": institutional_claim,
                    "measurement": f"{measurement.get('measurement')}: {m_value}",
                    "contradiction_type": "low_harm_vs_high_impact",
                    "confidence": m_confidence,
                })
        else:
            supporting.append(measurement)

    contradiction_confidence = (
        sum(c["confidence"] for c in contradictions) / len(contradictions)
        if contradictions else 0.0
    )

    return {
        "challenge_id": f"mtc-{uuid.uuid4().hex[:12]}",
        "institutional_claim": institutional_claim,
        "contradictions": contradictions,
        "supporting_measurements": [
            f"{m.get('measurement')}: {m.get('value')} {m.get('unit', '')}"
            for m in supporting
        ],
        "contradiction_count": len(contradictions),
        "contradiction_confidence": round(contradiction_confidence, 4),
        "measurement_confidence": measurement_confidence,
        "status": (
            "MATERIAL_CONTRADICTION" if contradictions and contradiction_confidence > 0.5 else
            "POSSIBLE_CONTRADICTION" if contradictions else
            "CONSISTENT"
        ),
        "reflection": [
            "What physically happened?",
            "Does the institutional claim survive contact with material evidence?",
            "What would Earth measurements show that the institution does not report?",
        ],
        "prohibited_conclusion": [
            "Do not infer institutional intent to deceive from contradiction alone.",
            "The institution may have information not visible to this analysis.",
        ],
        "metadata": {
            "challenged_at": datetime.now(timezone.utc).isoformat(),
            "tool": "geox_material_truth_challenge",
        },
    }
