import subprocess
import json
import os
from typing import Any, List, Optional
from fastmcp import FastMCP

# Initialize FastMCP server
# WEALTH = Valuation Kernel (NPV, IRR, Networth, Cashflow).
mcp = FastMCP("WEALTH Valuation Kernel")

# Paths
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

# --- Personal & Portfolio Valuation (wealth.personal.*) ---

@mcp.tool(name="wealth.personal.networth")
def personal_networth(assets: List[dict] = [], liabilities: List[dict] = []) -> Any:
    """Compute net worth with epistemic degradation."""
    args = {"assets": assets, "liabilities": liabilities}
    return invoke_node_tool("personal.networth", args)

@mcp.tool(name="wealth.personal.cashflow")
def personal_cashflow(income: List[dict] = [], expenses: List[dict] = []) -> Any:
    """Compute monthly cashflow and runway."""
    args = {"income": income, "expenses": expenses}
    return invoke_node_tool("personal.cashflow", args)

@mcp.tool(name="wealth.personal.growth")
def personal_growth(principal: float, rate: float, years: int, annual_contribution: float = 0) -> Any:
    """Project compound growth with F7 humility bands."""
    args = {"principal": principal, "rate": rate, "years": years, "annual_contribution": annual_contribution}
    return invoke_node_tool("personal.growth", args)

@mcp.tool(name="wealth.personal.runway")
def personal_runway(current_savings: float, monthly_burn: float, monthly_income: float = 0) -> Any:
    """Runway depletion estimate."""
    args = {"current_savings": current_savings, "monthly_burn": monthly_burn, "monthly_income": monthly_income}
    return invoke_node_tool("personal.runway", args)

# --- Capital & Project Evaluation (wealth.capital.*) ---

@mcp.tool(name="wealth.capital.score")
def capital_score(base_rate: float, dS: float = 0, peace2: float = 1.0, maruahScore: float = 0.5, trustIndex: float = 0.5, deltaCiv: float = 0) -> Any:
    """Calculate risk-adjusted cost of capital from signals."""
    args = {"base_rate": base_rate, "dS": dS, "peace2": peace2, "maruahScore": maruahScore, "trustIndex": trustIndex, "deltaCiv": deltaCiv}
    return invoke_node_tool("capital.score", args)

@mcp.tool(name="wealth.capital.compare")
def capital_compare(base_rate: float, wealth_signals: dict, extractive_signals: dict) -> Any:
    """Compare risk-adjusted rates between WEALTH and extractive nodes."""
    args = {"base_rate": base_rate, "wealth_signals": wealth_signals, "extractive_signals": extractive_signals}
    return invoke_node_tool("capital.compare", args)

@mcp.tool(name="wealth.capital.npv")
def capital_npv(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Net Present Value (NPV). Absolute value creation indicator."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("capital.npv", args)

@mcp.tool(name="wealth.capital.irr")
def capital_irr(initial_investment: float, cash_flows: List[float]) -> Any:
    """Compute Internal Rate of Return (IRR). Efficiency indicator."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital.irr", args)

@mcp.tool(name="wealth.capital.mirr")
def capital_mirr(initial_investment: float, cash_flows: List[float], finance_rate: float, reinvestment_rate: float) -> Any:
    """Compute Modified Internal Rate of Return (MIRR). Fixes IRR flaws."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "finance_rate": finance_rate, "reinvestment_rate": reinvestment_rate}
    return invoke_node_tool("capital.mirr", args)

@mcp.tool(name="wealth.capital.emv")
def capital_emv(scenarios: List[dict]) -> Any:
    """Compute Expected Monetary Value (EMV). Probability-weighted adjustment."""
    args = {"scenarios": scenarios}
    return invoke_node_tool("capital.emv", args)

@mcp.tool(name="wealth.capital.pi")
def capital_pi(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Profitability Index (PI). PV inflows / PV outflows."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discount_rate": discount_rate}
    return invoke_node_tool("capital.pi", args)

@mcp.tool(name="wealth.capital.payback")
def capital_payback(initial_investment: float, cash_flows: List[float], discounted: bool = False, discount_rate: float = 0) -> Any:
    """Compute Payback Period (standard or discounted)."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows, "discounted": discounted, "discount_rate": discount_rate}
    return invoke_node_tool("capital.payback", args)

@mcp.tool(name="wealth.capital.roi")
def capital_roi(initial_investment: float, cash_flows: List[float]) -> Any:
    """Compute Return on Investment (ROI). Basic gain-to-cost ratio."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital.roi", args)

@mcp.tool(name="wealth.capital.eaa")
def capital_eaa(npv: float, discount_rate: float, years: int) -> Any:
    """Compute Equivalent Annual Annuity (EAA)."""
    args = {"npv": npv, "discount_rate": discount_rate, "years": years}
    return invoke_node_tool("capital.eaa", args)

@mcp.tool(name="wealth.capital.audit")
def capital_audit(initial_investment: float, cash_flows: List[float]) -> Any:
    """Audit project cash flows for non-normal patterns (multiple IRRs, etc)."""
    args = {"initial_investment": initial_investment, "cash_flows": cash_flows}
    return invoke_node_tool("capital.audit", args)

# --- Resources ---

@mcp.resource("wealth://valuation/kernel")
def valuation_kernel_metadata() -> str:
    """Metadata about the WEALTH Valuation Kernel."""
    return json.dumps({
        "status": "ALIVE",
        "domain": "finance.valuation",
        "epistemic": "CLAIM",
        "protocol": "FastMCP"
    })

if __name__ == "__main__":
    mcp.run()
