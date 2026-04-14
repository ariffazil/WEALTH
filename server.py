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
