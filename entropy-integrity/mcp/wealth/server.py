import sys
import os
import yaml
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from detectors.responsibility_diffusion import ResponsibilityDiffusionDetector

mcp = FastMCP("WEALTH")

# --- Resources ---

@mcp.resource("wealth://entropy/power-consequence/v1")
def get_power_consequence_spec() -> str:
    spec = {
        "formula": "consequence_gap = decision_power * benefit_capture * harm_distance * non_accountability",
        "description": "Calculates gap between decision authority and downside risk exposure."
    }
    return yaml.dump(spec)

@mcp.resource("wealth://entropy/metric-drift/v1")
def get_metric_drift_spec() -> str:
    spec = {
        "drift_indicators": ["proxy substitution", "KPI gaming", "exclusion of negative externalities"]
    }
    return yaml.dump(spec)

@mcp.resource("wealth://entropy/trust-capital/v1")
def get_trust_capital_spec() -> str:
    spec = {
        "trust_components": ["formation_cost", "betrayal_shock", "recovery_half_life", "coordination_overhead"]
    }
    return yaml.dump(spec)

@mcp.resource("wealth://entropy/responsibility-ledger/v1")
def get_responsibility_ledger_spec() -> str:
    spec = {
        "roles_tracked": ["proposer", "approver", "funder", "executor", "beneficiary", "witness"]
    }
    return yaml.dump(spec)

@mcp.resource("wealth://entropy/coercive-order/v1")
def get_coercive_order_spec() -> str:
    spec = {
        "components": ["surveillance", "enforcement", "silence", "fragility"]
    }
    return yaml.dump(spec)

@mcp.resource("wealth://entropy/externality-taxonomy/v1")
def get_externality_taxonomy() -> str:
    spec = {
        "externality_types": ["risk export", "waste export", "downstream complexity", "option sterilization"]
    }
    return yaml.dump(spec)

@mcp.resource("wealth://benchmarks/institutional-collapse-cases/v1")
def get_collapse_cases() -> str:
    with open("/root/entropy-integrity/resources/case_library.yaml", "r") as f:
        return f.read()

# --- Prompts ---

@mcp.prompt()
def follow_the_consequence() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["follow_the_consequence"]

@mcp.prompt()
def who_benefits_who_pays() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["who_benefits_who_pays"]

@mcp.prompt()
def metric_or_mission() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["metric_or_mission"]

@mcp.prompt()
def local_order_global_entropy() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["local_order_global_entropy"]

@mcp.prompt()
def would_you_accept_this_rule_under_an_opponent() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["would_you_accept_this_rule_under_an_opponent"]

@mcp.prompt()
def price_the_destroyed_optionality() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["price_the_destroyed_optionality"]

@mcp.prompt()
def find_the_laundered_authority() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WEALTH"]["find_the_laundered_authority"]

# --- Tools ---

@mcp.tool()
def wealth_entropy_risk(mode: str, metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Evaluates risk vectors for institutional entropy.
    Modes: power_consequence_gap, metric_purpose_drift, responsibility_diffusion,
    trust_externality, option_value_destruction, institutional_brittleness, entropy_cascade.
    """
    val = metrics.get(mode, 0.5)
    
    status = "LOW_RISK"
    if val > 0.7:
        status = "CRITICAL_RISK"
    elif val > 0.4:
        status = "MODERATE_RISK"

    return {
        "mode": mode,
        "entropy_risk_score": float(val),
        "status": status,
        "context": "Evaluated capital and incentive risk vector without personal motive attribution."
    }

@mcp.tool()
def wealth_power_consequence_map(
    decision_authority: float,
    economic_upside: float,
    downside_exposure: float,
    who_bears_irreversible_cost: str,
    compensation_vs_harm: float,
    exit_rights: bool,
    concentration_of_veto_power: float
) -> Dict[str, Any]:
    """
    Maps decision authority, economic benefits, and downside exposures to measure consequence gaps.
    """
    # consequence_gap = decision_power * benefit_capture * harm_distance * non_accountability
    decision_power = decision_authority
    benefit_capture = economic_upside
    harm_distance = 1.0 - downside_exposure
    non_accountability = 1.0 if not exit_rights else 0.5

    consequence_gap = decision_power * benefit_capture * harm_distance * non_accountability

    return {
        "consequence_gap": float(consequence_gap),
        "responsibility_matrix": {
            "authority": decision_authority,
            "benefit": economic_upside,
            "downside_distance": harm_distance,
            "cost_bearer": who_bears_irreversible_cost
        },
        "indicators": {
            "power_consequence_gap": consequence_gap > 0.5,
            "irreversible_exposure": downside_exposure < 0.2 and consequence_gap > 0.4
        }
    }

@mcp.tool()
def wealth_metric_purpose_audit(
    declared_purpose: str,
    current_KPIs: List[str],
    rewards: List[str],
    actual_behaviour: List[str],
    excluded_outcomes: List[str]
) -> Dict[str, Any]:
    """
    Audits proxy drift, metric capture, and purpose fidelity in KPI frameworks.
    """
    # Simple heuristics: drift increases with more excluded outcomes
    drift = len(excluded_outcomes) / max(1, len(current_KPIs))
    purpose_fidelity = 1.0 - (drift * 0.8)
    purpose_fidelity = max(0.0, min(1.0, purpose_fidelity))

    return {
        "proxy_drift": float(drift),
        "metric_capture": len(rewards) > len(current_KPIs),
        "gaming_incentives": ["High rewards on proxy metrics with unmeasured externalities."],
        "purpose_fidelity": float(purpose_fidelity)
    }

@mcp.tool()
def wealth_responsibility_ledger(
    proposed: str,
    approved: str,
    funded: str,
    executed: str,
    benefited: str,
    knew: List[str],
    could_stop: List[str],
    claimed_excuse: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tracks delegation, execution, and excuse patterns (responsibility laundering).
    """
    detector = ResponsibilityDiffusionDetector()
    diffusion_result = detector.detect(claimed_excuse or "")

    gaps = []
    if not approved:
        gaps.append("MISSING_APPROVER")
    if not executed:
        gaps.append("EXECUTION_WITHOUT_OWNER")
    if approved == executed and approved == benefited:
        gaps.append("TOTAL_SELF_DEAL")

    if diffusion_result["diffusion_detected"]:
        gaps.append("RESPONSIBILITY_LAUNDERING_DETECTED")

    return {
        "responsibility_trace": {
            "proposer": proposed,
            "approver": approved,
            "funder": funded,
            "executor": executed,
            "beneficiary": benefited,
            "witnesses": knew,
            "control_nodes": could_stop
        },
        "responsibility_gaps": gaps,
        "diffusion_metrics": diffusion_result
    }

@mcp.tool()
def wealth_trust_capital_decay(
    betrayal_shock: float,
    recovery_half_life_days: float,
    coordination_overhead: float
) -> Dict[str, Any]:
    """
    Calculates decay rates and options loss in trust capital.
    """
    decay_rate = betrayal_shock * (1.0 / max(1.0, recovery_half_life_days))
    trust_remaining = max(0.0, 1.0 - betrayal_shock)
    option_loss = coordination_overhead * betrayal_shock

    return {
        "decay_rate": float(decay_rate),
        "trust_capital_remaining": float(trust_remaining),
        "option_loss": float(option_loss)
    }

@mcp.tool()
def wealth_coercive_order_cost(
    surveillance_expenditure: float,
    enforcement_overhead: float,
    silence_index: float,
    turnover_rate: float
) -> Dict[str, Any]:
    """
    Quantifies the hidden cost of apparent stability (coercive order).
    """
    overhead = surveillance_expenditure + enforcement_overhead
    tail_fragility = (silence_index * 0.6) + (turnover_rate * 0.4)

    return {
        "coercive_overhead_cost": float(overhead),
        "tail_fragility_increase": float(tail_fragility),
        "posture": "FRAGILE_ORDER" if tail_fragility > 0.6 else "STABLE"
    }

@mcp.tool()
def wealth_entropy_externality(
    local_efficiency_score: float,
    exported_waste: float,
    exported_risk: float
) -> Dict[str, Any]:
    """
    Measures local efficiency achieved at the expense of global/downstream systems (locally ordered, globally entropic).
    """
    externality_index = (exported_waste + exported_risk) / 2.0
    drift = local_efficiency_score - (1.0 - externality_index)

    return {
        "externality_index": float(externality_index),
        "ordered_locally_entropic_globally": bool(drift > 0.3),
        "divergence_score": float(drift)
    }

if __name__ == "__main__":
    mcp.run()
