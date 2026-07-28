import sys
import os
import yaml
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

mcp = FastMCP("GEOX")

# --- Resources ---

@mcp.resource("geox://entropy/material-consequence/v1")
def get_material_consequence_spec() -> str:
    spec = {
        "metrics": ["affected_area", "material_movement", "water_impact", "subsidence", "contamination"]
    }
    return yaml.dump(spec)

@mcp.resource("geox://entropy/physical-reversibility/v1")
def get_physical_reversibility_spec() -> str:
    spec = {
        "categories": ["REVERSIBLE", "COSTLY", "IRREVERSIBLE"]
    }
    return yaml.dump(spec)

@mcp.resource("geox://entropy/optionality-loss/v1")
def get_optionality_loss_spec() -> str:
    spec = {
        "options_tracked": ["sterilised_reserves", "lost_aquifer_use", "irreversible_land_conversion"]
    }
    return yaml.dump(spec)

@mcp.resource("geox://entropy/monitoring-integrity/v1")
def get_monitoring_integrity_spec() -> str:
    spec = {
        "checks": ["sensor_coverage", "baseline_quality", "reporting_delay", "anomaly_exclusion"]
    }
    return yaml.dump(spec)

@mcp.resource("geox://entropy/cascade-graphs/v1")
def get_cascade_graphs_spec() -> str:
    spec = {
        "domains": ["geology", "groundwater", "infrastructure", "ecology", "communities"]
    }
    return yaml.dump(spec)

@mcp.resource("geox://entropy/boundary-conditions/v1")
def get_boundary_conditions() -> str:
    spec = {
        "rules": ["Earth measurements are sovereign over moral narratives.", "Irreversibility triggers 888_HOLD."]
    }
    return yaml.dump(spec)

# --- Prompts ---

@mcp.prompt()
def material_reality_check() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["material_reality_check"]

@mcp.prompt()
def what_cannot_be_recovered() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["what_cannot_be_recovered"]

@mcp.prompt()
def surface_order_subsurface_damage() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["surface_order_subsurface_damage"]

@mcp.prompt()
def challenge_the_low_harm_claim() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["challenge_the_low_harm_claim"]

@mcp.prompt()
def missing_sensor_missing_truth() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["missing_sensor_missing_truth"]

@mcp.prompt()
def map_the_cascade() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["GEOX"]["map_the_cascade"]

# --- Tools ---

@mcp.tool()
def geox_consequence_footprint(
    affected_area_hectares: float,
    material_movement_tonnes: float,
    emissions_co2_equivalent: float,
    water_impact_index: float,
    habitat_fragmentation_score: float,
    subsidence_meters: float,
    contamination_level_ppm: float,
    reversibility: str,
    uncertainty_envelope: float
) -> Dict[str, Any]:
    """
    Compute physical and ecological consequences of a proposed action.
    """
    # Simple footprint severity computation
    severity = (water_impact_index * 0.3) + (habitat_fragmentation_score * 0.3) + (uncertainty_envelope * 0.4)
    if reversibility == "IRREVERSIBLE":
        severity = max(0.9, severity)

    return {
        "affected_area_hectares": affected_area_hectares,
        "material_movement_tonnes": material_movement_tonnes,
        "reversibility": reversibility,
        "severity_score": float(severity),
        "uncertainty_envelope": uncertainty_envelope,
        "physical_warnings": ["Irreversible resource commitment detected."] if reversibility == "IRREVERSIBLE" else []
    }

@mcp.tool()
def geox_optionality_loss(
    sterilised_reserves_pct: float,
    lost_aquifer_use_pct: float,
    irreversible_land_conversion_hectares: float,
    inaccessible_remediation_pathways: List[str],
    reduced_resilience_score: float,
    increased_hazard_exposure: float
) -> Dict[str, Any]:
    """
    Measures destroyed future physical options.
    """
    option_loss = (sterilised_reserves_pct * 0.2) + (lost_aquifer_use_pct * 0.4) + (reduced_resilience_score * 0.4)
    
    return {
        "physical_option_loss": float(option_loss),
        "inaccessible_pathways": inaccessible_remediation_pathways,
        "hazard_exposure": increased_hazard_exposure,
        "option_retention_score": float(1.0 - option_loss)
    }

@mcp.tool()
def geox_feedback_integrity(
    sensor_coverage_pct: float,
    baseline_quality_score: float,
    missing_measurements: List[str],
    reporting_delay_hours: float,
    threshold_manipulation: bool,
    excluded_anomalies: List[str]
) -> Dict[str, Any]:
    """
    Checks whether physical monitoring is sufficient to detect environmental drift.
    """
    sufficiency = (sensor_coverage_pct * 0.5) + (baseline_quality_score * 0.5)
    if threshold_manipulation:
        sufficiency -= 0.3
    if excluded_anomalies:
        sufficiency -= 0.15 * len(excluded_anomalies)
        
    sufficiency = max(0.0, min(1.0, sufficiency))

    return {
        "monitoring_sufficiency": float(sufficiency),
        "missing_channels": missing_measurements,
        "reporting_delay_hours": reporting_delay_hours,
        "integrity_alerts": ["Threshold manipulation detected!"] if threshold_manipulation else []
    }

@mcp.tool()
def geox_material_truth_challenge(
    institutional_claim: str,
    earth_measurements: str
) -> Dict[str, Any]:
    """
    Generalize the existing claim-challenge pattern for cross-organ claims.
    """
    challenge = f"The institution claims: '{institutional_claim}', but Earth measurements show: '{earth_measurements}'."
    
    return {
        "challenge_text": challenge,
        "contradiction_level": 0.85,
        "context": "Physical truth challenge formulated without attributing intent to the claimant."
    }

@mcp.tool()
def geox_cascade_pathway(
    intervention_node: str,
    edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Models physical consequence propagation across geology, water, infrastructure, and ecology.
    """
    propagation = []
    total_risk = 0.1
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        weight = edge.get("weight", 0.5)
        total_risk += weight * 0.2
        propagation.append(f"{source} -> {target} (weight: {weight})")

    total_risk = min(1.0, total_risk)

    return {
        "intervention_node": intervention_node,
        "propagation_map": propagation,
        "cascade_risk_score": float(total_risk),
        "primary_exposure": "groundwater" if total_risk > 0.5 else "none"
    }

if __name__ == "__main__":
    mcp.run()
