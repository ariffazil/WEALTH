"""
geox_consequence_footprint — Compute physical and ecological consequences of a proposed action.

Measures: affected area, material movement, emissions, water impact,
habitat fragmentation, subsidence, contamination, reversibility, uncertainty envelope.
"""

import uuid
from datetime import datetime, timezone


def geox_consequence_footprint(
    action_description: str,
    affected_area_km2: float | None = None,
    material_movement_tonnes: float | None = None,
    emissions_tonnes_co2e: float | None = None,
    water_impact_m3: float | None = None,
    habitat_fragmentation: str | None = None,
    subsidence_risk: str | None = None,
    contamination_risk: str | None = None,
    reversibility: str = "UNKNOWN",
    uncertainty_factor: float = 0.5,
) -> dict:
    """
    Compute physical consequence footprint.

    Returns:
        Confluence of physical consequence metrics
    """
    # Severity scoring
    severity = 0.0
    factors = []

    if affected_area_km2:
        area_score = min(1.0, affected_area_km2 / 100)  # 100km2 = max
        severity += area_score * 0.2
        factors.append(f"Affected area: {affected_area_km2} km²")

    if material_movement_tonnes:
        movement_score = min(1.0, material_movement_tonnes / 1_000_000)
        severity += movement_score * 0.15
        factors.append(f"Material movement: {material_movement_tonnes:,.0f} tonnes")

    if emissions_tonnes_co2e:
        emission_score = min(1.0, emissions_tonnes_co2e / 100_000)
        severity += emission_score * 0.15
        factors.append(f"Emissions: {emissions_tonnes_co2e:,.0f} tCO2e")

    if water_impact_m3:
        water_score = min(1.0, water_impact_m3 / 1_000_000)
        severity += water_score * 0.15
        factors.append(f"Water impact: {water_impact_m3:,.0f} m³")

    habitat_scores = {"NONE": 0, "LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "CRITICAL": 1.0}
    if habitat_fragmentation:
        hab_score = habitat_scores.get(habitat_fragmentation.upper(), 0.5)
        severity += hab_score * 0.15
        factors.append(f"Habitat fragmentation: {habitat_fragmentation}")

    subsidence_scores = {"NEGLIGIBLE": 0, "LOW": 0.2, "MODERATE": 0.5, "HIGH": 0.8, "SEVERE": 1.0}
    if subsidence_risk:
        sub_score = subsidence_scores.get(subsidence_risk.upper(), 0.5)
        severity += sub_score * 0.1
        factors.append(f"Subsidence risk: {subsidence_risk}")

    contamination_scores = {"NONE": 0, "LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "SEVERE": 1.0}
    if contamination_risk:
        cont_score = contamination_scores.get(contamination_risk.upper(), 0.5)
        severity += cont_score * 0.1
        factors.append(f"Contamination risk: {contamination_risk}")

    reversibility_scores = {"REVERSIBLE": 0.1, "COSTLY": 0.5, "IRREVERSIBLE": 1.0, "UNKNOWN": 0.5}
    rev_score = reversibility_scores.get(reversibility.upper(), 0.5)

    return {
        "footprint_id": f"cf-{uuid.uuid4().hex[:12]}",
        "action": action_description,
        "severity_score": round(min(1.0, severity), 4),
        "reversibility": reversibility,
        "reversibility_score": rev_score,
        "uncertainty_factor": uncertainty_factor,
        "factors": factors,
        "interpretation": (
            "HIGH physical consequence — material reality significantly altered"
            if severity > 0.7 else
            "MODERATE physical consequence — measurable impact"
            if severity > 0.3 else
            "LOW physical consequence — minimal material alteration"
        ),
        "reflection": [
            "What physically happened?",
            "What cannot be recovered?",
            "Is the monitoring sufficient to detect drift?",
        ],
        "metadata": {
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "geox_consequence_footprint",
        },
    }
