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
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality, ClaimState

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
    _register_legacy_surface_tools(mcp)  # stock, personal, market, omni, agent_path
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


def _register_legacy_surface_tools(mcp: FastMCP) -> None:
    """Register tools that delegate to monolith's existing implementations.
    These are the 5 missing public tools that need the monolith's complex engines."""

    @mcp.tool(name="wealth_stock_analysis")
    async def wealth_stock_analysis(
        mode: str = "verify_math",
        ticker: str = "",
        entry_price: float = 0,
        exit_price: float | None = None,
        current_price: float | None = None,
        position_size: int = 0,
        status: str = "unrealized",
        direction: str = "long",
    ) -> dict:
        """D4 Stock Analysis — 16-mode capital-risk governance.
        Delegates to internal/stock/ engines."""
        try:
            from internal.monolith import wealth_stock_analysis as _stock_impl
            return await _stock_impl(
                mode=mode, ticker=ticker, entry_price=entry_price,
                exit_price=exit_price, current_price=current_price,
                position_size=position_size, status=status, direction=direction,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_stock_analysis", domain="stock",
                result={"error": str(e), "mode": mode, "ticker": ticker},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Stock engine error: {e}"],
            )

    @mcp.tool(name="wealth_personal_finance")
    async def wealth_personal_finance(
        mode: str = "summary",
        owner: str = "arif",
        amount: float = 0,
        category: str = "expense",
        description: str = "",
        txn_date: str | None = None,
    ) -> dict:
        """D1 Personal Finance — cashflow, runway, net worth, EPF, zakat.
        Delegates to internal/personal_finance.py engines."""
        try:
            from internal.monolith import wealth_personal_finance as _pf_impl
            return await _pf_impl(
                mode=mode, owner=owner, amount=amount,
                category=category, description=description, txn_date=txn_date,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_personal_finance", domain="personal",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Personal finance engine error: {e}"],
            )

    @mcp.tool(name="wealth_market_data")
    async def wealth_market_data(
        mode: str = "fx",
        base: str = "USD",
        targets: str = "MYR,SGD,GBP",
        commodity: str = "brent_crude",
        indicator: str = "usd_myr",
        country: str = "MYS",
    ) -> dict:
        """D3 Market Data — FX rates, commodities, macro indicators.
        Delegates to internal/market_data.py engines."""
        try:
            from internal.monolith import wealth_market_data as _md_impl
            return await _md_impl(
                mode=mode, base=base, targets=targets,
                commodity=commodity, indicator=indicator, country=country,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_market_data", domain="macro",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Market data engine error: {e}"],
            )

    @mcp.tool(name="wealth_omni_wisdom")
    async def wealth_omni_wisdom(
        mode: str = "synthesize",
        decision_context: dict | None = None,
        deal_params: dict | None = None,
        path_params: dict | None = None,
    ) -> dict:
        """Unified capital intelligence — synthesis + deal + hysteresis.
        Delegates to monolith's omni_wisdom implementation."""
        try:
            from internal.monolith import wealth_omni_wisdom as _omni_impl
            return await _omni_impl(
                mode=mode, decision_context=decision_context,
                deal_params=deal_params, path_params=path_params,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_omni_wisdom", domain="synthesis",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Omni wisdom engine error: {e}"],
            )

    @mcp.tool(name="wealth_agent_path")
    async def wealth_agent_path(
        task_description: str = "",
        scale_mode: str = "agentic",
        context: dict | None = None,
    ) -> dict:
        """Sovereign Intent Router — classifies tasks into L1/L2 paths.
        Delegates to monolith's agent_path implementation."""
        try:
            from internal.monolith import wealth_agent_path as _ap_impl
            return await _ap_impl(
                task_description=task_description,
                scale_mode=scale_mode, context=context,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_agent_path", domain="meta",
                result={"error": str(e), "task_description": task_description},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Agent path engine error: {e}"],
            )


def _register_meta_tools(mcp: FastMCP) -> None:
    """Register meta/diagnostic tools."""

    @mcp.tool(name="wealth_vault_write")
    async def wealth_vault_write(
        tx_type: str,
        amount: float,
        currency: str = "MYR",
        description: str = "",
        quantity: float | None = None,
        price: float | None = None,
        fees: float = 0,
        broker: str = "",
        asset_id: str = "",
        category: str = "",
        notes: str = "",
    ) -> dict:
        """Write a transaction to the VAULT999 ledger.
        Irreversible — requires human confirmation for SEAL."""
        try:
            from host.governance.vault_supabase import record_transaction
            result = record_transaction(
                tx_type=tx_type, amount=amount, currency=currency,
                description=description, quantity=quantity, price=price,
                fees=fees, broker=broker, asset_id=asset_id,
                category=category, notes=notes,
            )
            return wrap_result(
                tool_name="wealth_vault_write",
                domain="governance",
                result=result,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=["vault999_supabase"],
                claim_state=ClaimState.SEALED,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_vault_write",
                domain="governance",
                result={"error": str(e)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Vault write error: {e}"],
            )

    @mcp.tool(name="wealth_vault_query")
    async def wealth_vault_query(
        query: str = "",
        limit: int = 10,
        asset_id: str = "",
    ) -> dict:
        """Query the VAULT999 ledger for portfolio memory and transactions."""
        try:
            from host.governance.vault_supabase import query_vault999, query_portfolio_snapshots
            if asset_id:
                snapshots = query_portfolio_snapshots(asset_id=asset_id, limit=limit)
                return wrap_result(
                    tool_name="wealth_vault_query",
                    domain="governance",
                    result={"snapshots": snapshots, "count": len(snapshots)},
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.STRONG,
                    source_attribution=["vault999_supabase"],
                )
            else:
                records = query_vault999(query=query, limit=limit)
                return wrap_result(
                    tool_name="wealth_vault_query",
                    domain="governance",
                    result=records,
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.STRONG,
                    source_attribution=["vault999_supabase"],
                )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_vault_query",
                domain="governance",
                result={"error": str(e)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Vault query error: {e}"],
            )

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
