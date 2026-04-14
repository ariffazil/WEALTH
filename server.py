import subprocess
import json
import os
from typing import Any, List, Optional
from fastmcp import FastMCP

# Initialize FastMCP server
# The user's platform expects "mcp" as the instance name.
mcp = FastMCP("WEALTH Sovereign Governance Host")

# Paths
# Since we are now at the root of the WEALTH directory:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVOKE_SCRIPT = os.path.join(BASE_DIR, "scripts", "invoke_tool.js")

def invoke_node_tool(tool_name: str, args: dict) -> Any:
    """Invoke a WEALTH tool via the Node bridge script."""
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

# --- Tool Definitions ---

@mcp.tool()
def wealth_check_floors(operation_type: str, reversible: bool = True, **kwargs) -> Any:
    """Run WEALTH F1-F13 floor checks on a proposed operation."""
    args = {"type": operation_type, "reversible": reversible, **kwargs}
    return invoke_node_tool("check_floors", args)

@mcp.tool()
def wealth_seal_999(peace2: float = 1.0, confidence: float = 0.0, holds: List[str] = [], violations: List[str] = [], human_confirmed: bool = False) -> Any:
    """Attempt a 999 SEAL on a decision state."""
    args = {"peace2": peace2, "confidence": confidence, "holds": holds, "violations": violations, "human_confirmed": human_confirmed}
    return invoke_node_tool("seal_999", args)

@mcp.tool()
def wealth_capitalx_score(base_rate: float, dS: float = 0, peace2: float = 1.0, maruahScore: float = 0.5, trustIndex: float = 0.5, deltaCiv: float = 0) -> Any:
    """Calculate risk-adjusted cost of capital from constitutional signals."""
    args = {"base_rate": base_rate, "dS": dS, "peace2": peace2, "maruahScore": maruahScore, "trustIndex": trustIndex, "deltaCiv": deltaCiv}
    return invoke_node_tool("capitalx_score", args)

@mcp.tool()
def wealth_compute_networth(assets: List[dict] = [], liabilities: List[dict] = []) -> Any:
    """Compute net worth with epistemic degradation."""
    args = {"assets": assets, "liabilities": liabilities}
    return invoke_node_tool("compute_networth", args)

@mcp.tool()
def wealth_compute_cashflow(income: List[dict] = [], expenses: List[dict] = []) -> Any:
    """Compute monthly cashflow and runway."""
    args = {"income": income, "expenses": expenses}
    return invoke_node_tool("compute_cashflow", args)

@mcp.tool()
def wealth_compute_maruah(financial_integrity: float = 0.5, sovereignty: float = 0.5, debt_dignity: float = 0.5, amanah_index: float = 0.5, community_contribution: float = 0.0) -> Any:
    """Compute the Maruah dignity/integrity score."""
    args = {"financial_integrity": financial_integrity, "sovereignty": sovereignty, "debt_dignity": debt_dignity, "amanah_index": amanah_index, "community_contribution": community_contribution}
    return invoke_node_tool("compute_maruah", args)

@mcp.tool()
def civilizational_prosperity_index(gdp_per_capita_growth: Optional[float] = None, employment_quality: Optional[float] = None, energy_access: Optional[float] = None) -> Any:
    """Compute the Global Prosperity Index (Civilizational Maruah)."""
    args = {"gdp_per_capita_growth": gdp_per_capita_growth, "employment_quality": employment_quality, "energy_access": energy_access}
    return invoke_node_tool("civilizational_prosperity", args)

# --- Capital Budgeting & Project Analysis (F2 CLAIM) ---

@mcp.tool()
def capital_npv(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Net Present Value (NPV). Absolute value creation indicator."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("capital_npv", args)

@mcp.tool()
def capital_irr(initial_investment: float, cash_flows: List[float]) -> Any:
    """Compute Internal Rate of Return (IRR). Efficiency indicator."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital_irr", args)

@mcp.tool()
def capital_emv(scenarios: List[dict]) -> Any:
    """Compute Expected Monetary Value (EMV). Probability-weighted risk adjustment."""
    args = {"scenarios": scenarios}
    return invoke_node_tool("capital_emv", args)

@mcp.tool()
def capital_pi(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Profitability Index (PI). Efficiency indicator (PV inflows / PV outflows)."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("capital_pi", args)

@mcp.tool()
def capital_payback(initial_investment: float, cash_flows: List[float], discounted: bool = False, discount_rate: float = 0) -> Any:
    """Compute Payback Period (standard or discounted). Recovery speed indicator."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discounted": discounted, "discount_rate": discount_rate}
    return invoke_node_tool("capital_payback", args)

@mcp.tool()
def capital_mirr(initial_investment: float, cash_flows: List[float], finance_rate: float, reinvestment_rate: float) -> Any:
    """Compute Modified Internal Rate of Return (MIRR). Fixes IRR reinvestment flaws."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "finance_rate": finance_rate, "reinvestment_rate": reinvestment_rate}
    return invoke_node_tool("capital_mirr", args)

@mcp.tool()
def capital_roi(initial_investment: float, cash_flows: List[float]) -> Any:
    """Compute Return on Investment (ROI). Basic gain-to-cost ratio."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital_roi", args)

@mcp.tool()
def capital_eaa(npv: float, discount_rate: float, years: int) -> Any:
    """Compute Equivalent Annual Annuity (EAA). For comparing projects with unequal lives."""
    args = {"npv": npv, "discount_rate": discount_rate, "years": years}
    return invoke_node_tool("capital_eaa", args)

@mcp.tool()
def capital_audit(initial_investment: float, cash_flows: List[float]) -> Any:
    """Audit project cash flows for non-normal patterns and potential IRR issues (F2 CLAIM)."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital_audit", args)

# --- Resources ---

@mcp.resource("wealth://governance/floors")
def get_floors() -> str:
    """F1-F13 floor definitions and hold types."""
    floors_path = os.path.join(BASE_DIR, "host/kernel/floors.js")
    try:
        with open(floors_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading floors: {str(e)}"

if __name__ == "__main__":
    mcp.run()
