import subprocess
import json
import os
from typing import Any, List, Optional
from fastmcp import FastMCP

# Initialize FastMCP server
# WEALTH v1.3.0: Sovereign Valuation Kernel (Physics > Narrative)
mcp = FastMCP("WEALTH Valuation Kernel")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVOKE_SCRIPT = os.path.join(BASE_DIR, "scripts", "invoke_tool.js")

def invoke_node_tool(tool_name: str, args: dict) -> Any:
    """Invoke a WEALTH dimensional tool via the Node bridge script."""
    try:
        result = subprocess.run(
            ["node", INVOKE_SCRIPT, tool_name, json.dumps(args)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": True, "message": e.stderr.strip() or str(e)}
    except json.JSONDecodeError:
        return {"error": True, "message": "Failed to decode JSON output from Node"}

# =============================================================================
# TOOLS (Dimensional Forge)
# =============================================================================

@mcp.tool(name="wealth_npv_reward")
def npv_reward(initial_investment: float, cash_flows: List[float], discount_rate: float, terminal_value: float = 0, period_unit: str = "annual") -> Any:
    """Compute NPV, Terminal Value, and EAA. [Reward Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate, "terminal_value": terminal_value, "period_unit": period_unit}
    return invoke_node_tool("npv_reward", args)

@mcp.tool(name="wealth_irr_yield")
def irr_yield(initial_investment: float, cash_flows: List[float], reinvestment_rate: float = 0.1, period_unit: str = "annual") -> Any:
    """Compute IRR and MIRR (Potential). [Energy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "reinvestment_rate": reinvestment_rate, "period_unit": period_unit}
    return invoke_node_tool("irr_yield", args)

@mcp.tool(name="wealth_pi_efficiency")
def pi_efficiency(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Profitability Index (Concentration). [Energy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("pi_efficiency", args)

@mcp.tool(name="wealth_emv_risk")
def emv_risk(scenarios: List[dict]) -> Any:
    """Compute Expected Monetary Value (Probability Density). [Entropy Dimension]"""
    args = {"scenarios": scenarios}
    return invoke_node_tool("emv_risk", args)

@mcp.tool(name="wealth_audit_entropy")
def audit_entropy(initial_investment: float, cash_flows: List[float], discount_rate: float = 0.1) -> Any:
    """Audit project cash flows for noise and multiple IRRs. [Entropy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("audit_entropy", args)

@mcp.tool(name="wealth_dscr_leverage")
def dscr_leverage(ebitda: float, principal: float, interest: float, period_unit: str = "annual") -> Any:
    """Compute Debt Service Coverage Ratio (Structural Load). [Survival Dimension]"""
    args = {"ebitda": ebitda, "principal": principal, "interest": interest, "period_unit": period_unit}
    return invoke_node_tool("dscr_leverage", args)

@mcp.tool(name="wealth_payback_time")
def payback_time(initial_investment: float, cash_flows: List[float], discount_rate: float = 0, period_unit: str = "annual") -> Any:
    """Compute Payback Period (Recovery Velocity). [Time Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate, "period_unit": period_unit}
    return invoke_node_tool("payback_time", args)

@mcp.tool(name="wealth_growth_velocity")
def growth_velocity(principal: float, rate: float, years: int, annual_contribution: float = 0, monthly_burn: float = 0) -> Any:
    """Compute Compound Growth and Runway. [Velocity Dimension]"""
    args = {"principal": principal, "rate": rate, "years": years, "annual_contribution": annual_contribution, "monthly_burn": monthly_burn}
    return invoke_node_tool("growth_velocity", args)

@mcp.tool(name="wealth_networth_state")
def networth_state(assets: List[dict] = [], liabilities: List[dict] = []) -> Any:
    """Compute portfolio balance sheet (Accumulated Mass). [Mass Dimension]
    Asset tags: equity | cash | property | digital | debt | business
    """
    args = {"assets": assets, "liabilities": liabilities}
    return invoke_node_tool("networth_state", args)

@mcp.tool(name="wealth_cashflow_flow")
def cashflow_flow(income: List[dict] = [], expenses: List[dict] = []) -> Any:
    """Compute metabolic liquidity (Flow Dimension). [Flow Dimension]"""
    args = {"income": income, "expenses": expenses}
    return invoke_node_tool("cashflow_flow", args)

@mcp.tool(name="wealth_score_kernel")
def score_kernel(base_rate: float, dS: float, peace2: float, maruahScore: float, compare: bool = False, extractive_signals: dict = {}) -> Any:
    """Final Sovereign Allocation Verdict. [Allocation Dimension]"""
    args = {"base_rate": base_rate, "dS": dS, "peace2": peace2, "maruahScore": maruahScore, "compare": compare, "extractive_signals": extractive_signals}
    return invoke_node_tool("score_kernel", args)

# =============================================================================
# RESOURCES (Sacred Data)
# =============================================================================

@mcp.resource("wealth://doctrine/valuation")
def get_valuation_doctrine() -> str:
    """Valuation Doctrine: Constitutional principles for capital allocation."""
    return json.dumps({
        "motto": "Physics > Narrative",
        "principles": [
            "F1: Absolute Value (NPV) is the primary anchor.",
            "F2: Reinvestment risk must be modeled via MIRR.",
            "F3: Time-Value is a physical decay function.",
            "F4: Leverage must never break the DSCR floor (1.25x).",
            "F5: Mandatory governance signals (dS, peace2, maruah) for SEAL."
        ],
        "protocol": "Dimensional Forge v1.3.0"
    }, indent=2)

@mcp.resource("wealth://dimensions/definitions")
def get_dimensional_definitions() -> str:
    """Physical Dimensions of Wealth defined in the kernel."""
    return json.dumps({
        "Reward": "Total energy output (NPV, EAA).",
        "Energy": "Efficiency and potential (IRR, PI).",
        "Entropy": "Risk, noise, and probability (EMV, Audit).",
        "Time": "Recovery velocity (Payback).",
        "Mass": "Accumulated state (Net Worth).",
        "Flow": "Metabolic rate (Cash Flow).",
        "Velocity": "Rate of expansion (Growth).",
        "Survival": "Structural load capacity (DSCR).",
        "Allocation": "Sovereign decision kernel (Score)."
    }, indent=2)

if __name__ == "__main__":
    mcp.run()
