import subprocess
import json
import os
from typing import Any, List, Optional
from fastmcp import FastMCP

# Initialize FastMCP server
# WEALTH = Sovereign Valuation Kernel (Physics > Narrative)
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
def npv_reward(initial_investment: float, cash_flows: List[float], discount_rate: float, terminal_value: float = 0) -> Any:
    """Compute Net Present Value (NPV), Terminal Value, and EAA. [Reward Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate, "terminal_value": terminal_value}
    return invoke_node_tool("npv_reward", args)

@mcp.tool(name="wealth_irr_yield")
def irr_yield(initial_investment: float, cash_flows: List[float], reinvestment_rate: float = 0.1) -> Any:
    """Compute IRR and MIRR (Efficiency/Potential). [Energy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "reinvestment_rate": reinvestment_rate}
    return invoke_node_tool("irr_yield", args)

@mcp.tool(name="wealth_pi_efficiency")
def pi_efficiency(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Profitability Index (Value per Ringgit). [Energy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("pi_efficiency", args)

@mcp.tool(name="wealth_emv_risk")
def emv_risk(scenarios: List[dict]) -> Any:
    """Compute Expected Monetary Value (Probability-weighted outcomes). [Entropy Dimension]"""
    args = {"scenarios": scenarios}
    return invoke_node_tool("emv_risk", args)

@mcp.tool(name="wealth_audit_entropy")
def audit_entropy(initial_investment: float, cash_flows: List[float], discount_rate: float = 0.1) -> Any:
    """Audit project cash flows for noise, sign-changes, and sensitivity. [Entropy Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("audit_entropy", args)

@mcp.tool(name="wealth_dscr_leverage")
def dscr_leverage(ebitda: float, principal: float, interest: float) -> Any:
    """Compute Debt Service Coverage Ratio (Structural Load). [Survival Dimension]"""
    args = {"ebitda": ebitda, "principal": principal, "interest": interest}
    return invoke_node_tool("dscr_leverage", args)

@mcp.tool(name="wealth_payback_time")
def payback_time(initial_investment: float, cash_flows: List[float], discount_rate: float = 0) -> Any:
    """Compute Standard or Discounted Payback Period (Recovery Velocity). [Time Dimension]"""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("payback_time", args)

@mcp.tool(name="wealth_growth_velocity")
def growth_velocity(principal: float, rate: float, years: int, annual_contribution: float = 0, monthly_burn: float = 0) -> Any:
    """Compute Compound Growth and Runway Depletion. [Velocity Dimension]"""
    args = {"principal": principal, "rate": rate, "years": years, "annual_contribution": annual_contribution, "monthly_burn": monthly_burn}
    return invoke_node_tool("growth_velocity", args)

@mcp.tool(name="wealth_networth_state")
def networth_state(assets: List[dict] = [], liabilities: List[dict] = []) -> Any:
    """Compute accumulated multi-asset state (Balance Sheet). [Mass Dimension]"""
    args = {"assets": assets, "liabilities": liabilities}
    return invoke_node_tool("networth_state", args)

@mcp.tool(name="wealth_cashflow_flow")
def cashflow_flow(income: List[dict] = [], expenses: List[dict] = []) -> Any:
    """Compute metabolic rate (Monthly Liquidity). [Flow Dimension]"""
    args = {"income": income, "expenses": expenses}
    return invoke_node_tool("cashflow_flow", args)

@mcp.tool(name="wealth_score_kernel")
def score_kernel(base_rate: float, dS: float = 0, peace2: float = 1.0, maruahScore: float = 0.5, compare: bool = False, wealth_signals: dict = {}, extractive_signals: dict = {}) -> Any:
    """Calculate risk-adjusted rates or compare capital advantages. [Allocation Dimension]"""
    args = {"base_rate": base_rate, "dS": dS, "peace2": peace2, "maruahScore": maruahScore, "compare": compare, "wealth_signals": wealth_signals, "extractive_signals": extractive_signals}
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
            "F2: Reinvestment risk must be modeled via MIRR, not just IRR.",
            "F3: Time-Value is a physical decay function.",
            "F4: Decisions under uncertainty require EMV weighting.",
            "F5: Leverage must never break the DSCR floor (1.2x)."
        ],
        "seal": "999 SEAL ALIVE"
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
        "Velocity": "Rate of expansion (Growth)."
    }, indent=2)

@mcp.resource("wealth://samples/project")
def get_sample_project() -> str:
    """Canonical JSON template for project evaluation."""
    return json.dumps({
        "project_id": "SAMPLE_PROFIT_001",
        "initial_investment": 1000000,
        "cash_flows": [200000, 300000, 400000, 500000, 600000],
        "discount_rate": 0.12,
        "terminal_value": 500000,
        "scenarios": [
            {"name": "BASE", "probability": 0.6, "outcome": 1500000},
            {"name": "STRESS", "probability": 0.4, "outcome": 800000}
        ]
    }, indent=2)

# =============================================================================
# PROMPTS (Sacred Workflows)
# =============================================================================

@mcp.prompt()
def evaluate_project(project_data: str) -> str:
    """Prompt to perform a full physical evaluation of a capital project."""
    return f"""Evaluate the following project using the WEALTH Valuation Kernel.
Data: {project_data}

Required Steps:
1. Compute NPV (Reward) and IRR (Energy).
2. Audit cashflows for sign-changes and multiple IRR risks.
3. Calculate Profitability Index (Efficiency).
4. Run standard and discounted payback (Time).
5. Provide verdict per F2 CLAIM (Physics > Narrative).
"""

@mcp.prompt()
def analyze_sensitivity(initial_investment: float, cash_flows: str) -> str:
    """Prompt to perform a discount-rate sensitivity sweep."""
    return f"""Run a sensitivity sweep for a project with:
Initial Outlay: {initial_investment}
Flows: {cash_flows}

Analyze how the NPV shifts across 80% to 120% of the target hurdle rate. Identify the 'Death Cross' (where NPV < 0).
"""

@mcp.prompt()
def draft_capital_memo(evaluation_results: str) -> str:
    """Prompt to generate a Sovereign Capital Decision Memo."""
    return f"""Draft a formal Capital Decision Memo based on these physics-based results:
{evaluation_results}

The memo must include:
- Executive Verdict (SEAL/VOID)
- Value Creation Delta (NPV)
- Structural Load (DSCR/Leverage)
- Velocity Audit (Payback/Growth)
- Risk Probability (EMV)

Signature: 999 SEAL ALIVE.
"""

if __name__ == "__main__":
    mcp.run()
