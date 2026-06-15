"""
WEALTH Federated Domain — MCP Server.

Replaces internal/monolith.py as the canonical entry point.
Imports from wealth_core/ and wealth_contracts/.
Exposes the same MCP surface with clean architecture.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import os
import sys
from typing import Any

# Ensure parent directory is in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastmcp import FastMCP

# Import contracts
from wealth_contracts.envelope import WealthEnvelope, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality

# Import core engines
from wealth_core.wisdom import compute_wisdom
from wealth_core.power import audit_power
from wealth_core.capital import (
    compute_conservation,
    compute_flow,
    compute_runway,
    compute_gradient,
    compute_energy,
    compute_inertia,
    npv,
    irr,
    profitability_index,
    payback_period,
    emv,
    dscr,
)
from wealth_core.risk import (
    compute_emv,
    monte_carlo_simulation,
    compute_evoi,
    detect_false_confluence,
    compute_asymmetry,
)
from wealth_core.math import compute_kappa_r, compute_psi_le, get_qdf_version


def create_mcp_server() -> FastMCP:
    """Create and configure the WEALTH MCP server."""
    
    mcp = FastMCP(
        "WEALTH Federated Domain",
        version="2026.06.15",
        instructions=(
            "WEALTH — Capital Intelligence for arifOS federation. "
            "Computes capital, risk, wisdom, and power metrics. "
            "Does NOT authorize execution. WEALTH computes. arifOS judges. Arif decides."
        ),
    )

    # ── Register tools ────────────────────────────────────────────────────
    _register_wisdom_tools(mcp)
    _register_power_tools(mcp)
    _register_capital_tools(mcp)
    _register_risk_tools(mcp)
    _register_meta_tools(mcp)

    return mcp


def _register_wisdom_tools(mcp: FastMCP) -> None:
    """Register Wisdom Economics tools."""

    @mcp.tool(name="wealth_wisdom_evaluate")
    async def wealth_wisdom_evaluate(
        proposal: str,
        capital_type: str = "financial",
        context: dict | None = None,
    ) -> dict:
        """
        Evaluate a capital allocation proposal across 6 wisdom dimensions.
        Returns dignity impact, sovereignty effect, resilience score,
        inequality effect, ecological cost, and optionality preservation.

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_wisdom(proposal, capital_type, context)
        return wrap_result(
            tool_name="wealth_wisdom_evaluate",
            domain="wisdom",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=["proposal_text_analysis"],
            dignity_impact=_extract_dimension(result, "dignity"),
            sovereignty_effect=_extract_dimension(result, "sovereignty"),
        )


def _register_power_tools(mcp: FastMCP) -> None:
    """Register Power Intelligence tools."""

    @mcp.tool(name="wealth_power_audit")
    async def wealth_power_audit(
        scenario: str,
        actors: list[str] | None = None,
        context: dict | None = None,
    ) -> dict:
        """
        Audit the power dynamics of a capital scenario.
        Returns incentive map, capture risk, rent extraction score,
        opacity level, coercion signals, and rule asymmetry.

        Catches AI advice that sounds balanced but hides weak evidence
        or dangerous allocation geometry.
        """
        result = audit_power(scenario, actors, context)
        return wrap_result(
            tool_name="wealth_power_audit",
            domain="power",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=["scenario_text_analysis"],
            capture_risk_level=result.get("overall_capture_risk"),
        )

    @mcp.tool(name="wealth_capture_scan")
    async def wealth_capture_scan(
        advice_text: str,
        source_model: str = "",
    ) -> dict:
        """
        Scan AI-generated financial advice for capture signals.
        Detects: hidden incentives, omitted downsides, false precision,
        time-pressure language, authority claims without evidence.
        """
        result = audit_power(advice_text, [source_model, "user"], {})
        return wrap_result(
            tool_name="wealth_capture_scan",
            domain="power",
            result={
                "capture_risk": result.get("overall_capture_risk"),
                "dimensions": result.get("dimensions", []),
                "source_model": source_model,
            },
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=[f"model:{source_model}" if source_model else "unknown"],
            capture_risk_level=result.get("overall_capture_risk"),
        )


def _register_capital_tools(mcp: FastMCP) -> None:
    """Register capital domain tools."""

    @mcp.tool(name="wealth_compute_npv")
    async def wealth_compute_npv(
        cash_flows: list[float],
        discount_rate: float,
    ) -> dict:
        """Compute Net Present Value of a series of cash flows."""
        result = npv(cash_flows, discount_rate)
        return wrap_result(
            tool_name="wealth_compute_npv",
            domain="capital",
            result={"npv": result, "cash_flows": cash_flows, "discount_rate": discount_rate},
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.STRONG,
            source_attribution=["user_provided_inputs"],
        )

    @mcp.tool(name="wealth_compute_irr")
    async def wealth_compute_irr(
        cash_flows: list[float],
        initial_investment: float,
    ) -> dict:
        """Compute Internal Rate of Return."""
        result = irr(cash_flows, initial_investment)
        return wrap_result(
            tool_name="wealth_compute_irr",
            domain="capital",
            result={"irr": result, "cash_flows": cash_flows, "initial_investment": initial_investment},
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.STRONG,
            source_attribution=["user_provided_inputs"],
        )

    @mcp.tool(name="wealth_conservation_check")
    async def wealth_conservation_check(
        assets: list[dict] | None = None,
        liabilities: list[dict] | None = None,
    ) -> dict:
        """Compute capital conservation: net worth, asset/liability totals."""
        result = compute_conservation(assets, liabilities)
        return wrap_result(
            tool_name="wealth_conservation_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_portfolio"],
        )

    @mcp.tool(name="wealth_flow_check")
    async def wealth_flow_check(
        income: list[dict] | None = None,
        expenses: list[dict] | None = None,
    ) -> dict:
        """Compute cash flow: net, income, expenses, monthly burn."""
        result = compute_flow(income, expenses)
        return wrap_result(
            tool_name="wealth_flow_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_cashflow"],
        )

    @mcp.tool(name="wealth_runway_check")
    async def wealth_runway_check(
        liquid_assets: float,
        monthly_burn: float,
        conservative_factor: float = 0.8,
    ) -> dict:
        """Compute financial runway in months."""
        result = compute_runway(liquid_assets, monthly_burn, conservative_factor)
        return wrap_result(
            tool_name="wealth_runway_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_assets"],
        )


def _register_risk_tools(mcp: FastMCP) -> None:
    """Register risk domain tools."""

    @mcp.tool(name="wealth_emv_compute")
    async def wealth_emv_compute(
        outcomes: list[float],
        probabilities: list[float],
    ) -> dict:
        """Compute Expected Monetary Value with variance and std dev."""
        result = compute_emv(outcomes, probabilities)
        return wrap_result(
            tool_name="wealth_emv_compute",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_scenarios"],
        )

    @mcp.tool(name="wealth_monte_carlo")
    async def wealth_monte_carlo(
        initial_value: float,
        growth_rate: float,
        volatility: float,
        periods: int = 10,
        simulations: int = 1000,
        seed: int | None = None,
    ) -> dict:
        """Run Monte Carlo simulation for value projection."""
        result = monte_carlo_simulation(
            initial_value, growth_rate, volatility, periods, simulations, seed
        )
        return wrap_result(
            tool_name="wealth_monte_carlo",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["monte_carlo_simulation"],
        )

    @mcp.tool(name="wealth_evoi_compute")
    async def wealth_evoi_compute(
        prior_pos: float,
        posterior_pos: float,
        well_cost_musd: float,
        p50_value_musd: float,
        discount_rate: float = 0.1,
    ) -> dict:
        """Compute Expected Value of Information (EVOI)."""
        result = compute_evoi(prior_pos, posterior_pos, well_cost_musd, p50_value_musd, discount_rate)
        return wrap_result(
            tool_name="wealth_evoi_compute",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["evoi_calculation"],
        )

    @mcp.tool(name="wealth_confluence_check")
    async def wealth_confluence_check(
        indicators: list[dict],
    ) -> dict:
        """Detect false confluence — indicators measuring the same signal."""
        result = detect_false_confluence(indicators)
        return wrap_result(
            tool_name="wealth_confluence_check",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["indicator_analysis"],
        )

    @mcp.tool(name="wealth_asymmetry_check")
    async def wealth_asymmetry_check(
        upside_scenarios: list[float],
        downside_scenarios: list[float],
    ) -> dict:
        """Compute risk asymmetry — is the distribution skewed?"""
        result = compute_asymmetry(upside_scenarios, downside_scenarios)
        return wrap_result(
            tool_name="wealth_asymmetry_check",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["scenario_analysis"],
        )


def _register_meta_tools(mcp: FastMCP) -> None:
    """Register meta/diagnostic tools."""

    @mcp.tool(name="wealth_system_registry_status")
    async def wealth_system_registry_status(mode: str = "registry") -> dict:
        """Registry truth diagnostic — intended vs registered vs callable."""
        if mode == "health":
            return {
                "status": "ALIVE",
                "version": "2026.06.15",
                "domain": "WEALTH Federated Domain",
                "transport": "streamable-http",
            }
        return {
            "status": "ALIVE",
            "version": "2026.06.15",
            "domain": "WEALTH Federated Domain",
            "public_tools": [
                "wealth_wisdom_evaluate",
                "wealth_power_audit",
                "wealth_capture_scan",
                "wealth_compute_npv",
                "wealth_compute_irr",
                "wealth_conservation_check",
                "wealth_flow_check",
                "wealth_runway_check",
                "wealth_emv_compute",
                "wealth_monte_carlo",
                "wealth_evoi_compute",
                "wealth_confluence_check",
                "wealth_asymmetry_check",
                "wealth_system_registry_status",
            ],
        }


def _extract_dimension(wisdom_result: dict, dimension: str) -> str | None:
    """Extract a single dimension score from wisdom result."""
    for dim in wisdom_result.get("dimensions", []):
        if dim.get("dimension") == dimension:
            score = dim.get("score", 0.5)
            if score > 0.7:
                return "positive"
            elif score < 0.3:
                return "negative"
            else:
                return "neutral"
    return None
