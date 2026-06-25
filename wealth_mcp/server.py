"""
WEALTH Federated Domain — MCP Server.

Replaces internal/monolith.py as the canonical entry point.
Imports from wealth_core/ and wealth_contracts/.
Exposes the same MCP surface with clean architecture.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import os
import sys

# Ensure parent directory is in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastmcp import FastMCP

# Import contracts
from wealth_contracts.envelope import wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality, ClaimState

# Import core engines
from wealth_core.wisdom import compute_wisdom
from wealth_core.power import audit_power
from wealth_core.capital import (
    compute_conservation,
    compute_flow,
    compute_runway,
    npv,
    irr,
)
from wealth_core.risk import (
    compute_emv,
    monte_carlo_simulation,
    compute_evoi,
    detect_false_confluence,
    compute_asymmetry,
    fiscal_breakeven_oil_price,
)
from wealth_core.collapse_signature.scanner import compute_collapse_risk
from wealth_core.collapse_signature.beautiful_mouse import compute_beautiful_mouse_score
from wealth_core.counterfactual import run_counterfactual
from wealth_arifos_bridge.judge_handoff import prepare_judge_handoff, submit_to_arif_judge


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

    # ── Wire arifOS organ governance wrapper around tool calls ─────────────
    try:
        from internal.organ_governance import check_governance as _check_governance
        from fastmcp.server.server import ToolResult
        from mcp.types import TextContent

        _original_call_tool = mcp.call_tool

        async def _governance_call_tool(name, arguments=None, **kwargs):
            if arguments is None:
                arguments = {}
            verdict, error = _check_governance(name, arguments)
            if error is not None:
                error_text = json.dumps({
                    "tool": name,
                    "governance_status": verdict,
                    "error_code": "ORGAN_GOVERNANCE_BLOCKED",
                    "message": f"arifOS {verdict}: governance check blocked execution",
                    "guard": "ORGAN_GOVERNANCE",
                    "floor": "L1-L13",
                })
                return ToolResult(
                    content=[TextContent(type="text", text=error_text)],
                    is_error=True,
                )
            # ── MACRO CONTEXT: available via contextvar, not injection ──────────
            # The _macro_state contextvar is set by the MCP transport layer.
            # Tools that need macro state call get_macro_context() directly.
            return await _original_call_tool(name, arguments, **kwargs)

        mcp.call_tool = _governance_call_tool
    except Exception as e:
        print(f"[GOVERNANCE] WEALTH federated governance wrapper failed to load: {e}")

    # ── Register tools ────────────────────────────────────────────────────
    _register_wisdom_tools(mcp)
    _register_power_tools(mcp)
    _register_capital_tools(mcp)
    _register_risk_tools(mcp)
    _register_legacy_surface_tools(mcp)  # stock, personal, market, omni, agent_path
    _register_meta_tools(mcp)
    _register_advanced_tools(mcp)  # beautiful mouse, judge handoff (forged 2026-06-24)
    _register_resources(mcp)
    _register_prompts(mcp)

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

    # ── Canonical: wealth_compute_emv ────────────────────────────────────
    @mcp.tool(name="wealth_compute_emv")
    async def wealth_compute_emv(
        outcomes: list[float],
        probabilities: list[float],
    ) -> dict:
        """Compute Expected Monetary Value with variance and std dev."""
        result = compute_emv(outcomes, probabilities)
        return wrap_result(
            tool_name="wealth_compute_emv",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_scenarios"],
        )

    # ── HARDENING 2026-06-25: legacy alias (was wealth_emv_compute) ───────
    # Registry expects this name; compat layer maps it but never registered it.
    @mcp.tool(name="wealth_emv_compute")
    async def wealth_emv_compute(
        outcomes: list[float],
        probabilities: list[float],
    ) -> dict:
        """[LEGACY ALIAS] Compute Expected Monetary Value. Use wealth_compute_emv."""
        return await wealth_compute_emv(outcomes, probabilities)

    # ── Canonical: wealth_monte_carlo_simulate ──────────────────────────────
    @mcp.tool(name="wealth_monte_carlo_simulate")
    async def wealth_monte_carlo_simulate(
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
            tool_name="wealth_monte_carlo_simulate",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["monte_carlo_simulation"],
        )

    # ── HARDENING 2026-06-25: legacy alias ────────────────────────────────
    @mcp.tool(name="wealth_monte_carlo")
    async def wealth_monte_carlo(
        initial_value: float,
        growth_rate: float,
        volatility: float,
        periods: int = 10,
        simulations: int = 1000,
        seed: int | None = None,
    ) -> dict:
        """[LEGACY ALIAS] Use wealth_monte_carlo_simulate."""
        return await wealth_monte_carlo_simulate(initial_value, growth_rate, volatility, periods, simulations, seed)

    # ── Canonical: wealth_compute_evoi ────────────────────────────────────
    @mcp.tool(name="wealth_compute_evoi")
    async def wealth_compute_evoi(
        prior_pos: float,
        posterior_pos: float,
        well_cost_musd: float,
        p50_value_musd: float,
        discount_rate: float = 0.1,
    ) -> dict:
        """Compute Expected Value of Information (EVOI)."""
        result = compute_evoi(prior_pos, posterior_pos, well_cost_musd, p50_value_musd, discount_rate)
        return wrap_result(
            tool_name="wealth_compute_evoi",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["evoi_calculation"],
        )

    # ── HARDENING 2026-06-25: legacy alias ────────────────────────────────
    @mcp.tool(name="wealth_evoi_compute")
    async def wealth_evoi_compute(
        prior_pos: float,
        posterior_pos: float,
        well_cost_musd: float,
        p50_value_musd: float,
        discount_rate: float = 0.1,
    ) -> dict:
        """[LEGACY ALIAS] Compute EVOI. Use wealth_compute_evoi."""
        return await wealth_compute_evoi(prior_pos, posterior_pos, well_cost_musd, p50_value_musd, discount_rate)

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

    # ── HARDENING 2026-06-25: fiscal breakeven — highest-signal gap ──────
    @mcp.tool(name="wealth_fiscal_breakeven")
    async def wealth_fiscal_breakeven(
        total_government_expenditure: float,
        non_oil_revenue: float,
        petronas_dividend_base_rm: float,
        oil_price_assumption_usd: float,
        petronas_production_boe_per_day: float = 350_000,
        royalty_tax_effective_rate: float = 0.30,
        target_fiscal_deficit_pct: float = 0.035,
        gdp_nominal_rm_billion: float = 390.0,
    ) -> dict:
        """
        Compute oil price at which Malaysia's fiscal path becomes unsustainable.

        Returns breakeven price, fiscal pressure classification (UNSUSTAINABLE/AT_RISK/MANAGEABLE),
        and sensitivity analysis. Answers what Monte Carlo cannot: a single threshold.

        Budget 2026 calibration: total revenue RM343.1B, operating exp RM302B,
        petroleum revenue RM43B (dividend RM20B + tax RM23B), target deficit 3.5% GDP.
        """
        result = fiscal_breakeven_oil_price(
            total_government_expenditure=total_government_expenditure,
            non_oil_revenue=non_oil_revenue,
            petronas_dividend_base_rm=petronas_dividend_base_rm,
            oil_price_assumption_usd=oil_price_assumption_usd,
            petronas_production_boe_per_day=petronas_production_boe_per_day,
            royalty_tax_effective_rate=royalty_tax_effective_rate,
            target_fiscal_deficit_pct=target_fiscal_deficit_pct,
            gdp_nominal_rm_billion=gdp_nominal_rm_billion,
        )
        return wrap_result(
            tool_name="wealth_fiscal_breakeven",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.CLAIM,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["malaysia_budget_2026", "petronas_annual_report"],
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
            return _md_impl(
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
        Modes:
          - synthesize: monolith synthesis (default)
          - deal_frame: monolith deal framing
          - path_params: hysteresis-aware path analysis
          - counterfactual: structured counterfactual across 13 primitives
                            (LOCAL, forged 2026-06-24)
        """
        # Local counterfactual mode — bridges MOF watch + V3 scenarios
        if mode == "counterfactual":
            try:
                base_context = decision_context or {}
                deltas = (deal_params or {}).get("deltas", [])
                cf_mode = (path_params or {}).get("cf_mode", "grid")
                top_k = int((path_params or {}).get("top_k", 5))
                result = run_counterfactual(
                    base_context=base_context,
                    deltas=deltas,
                    mode=cf_mode,
                    top_k=top_k,
                )
                return wrap_result(
                    tool_name="wealth_omni_wisdom",
                    domain="synthesis",
                    result=result,
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=["counterfactual_engine", "wealth_thermodynamics_v1"],
                )
            except Exception as e:
                return wrap_result(
                    tool_name="wealth_omni_wisdom", domain="synthesis",
                    result={"error": str(e), "mode": mode},
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[f"Counterfactual engine error: {e}"],
                )
        # Other modes delegate to monolith
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
            return _ap_impl(
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
                # Wisdom & Power
                "wealth_wisdom_evaluate",
                "wealth_power_audit",
                "wealth_capture_scan",
                # Capital
                "wealth_compute_npv",
                "wealth_compute_irr",
                "wealth_conservation_check",
                "wealth_flow_check",
                "wealth_runway_check",
                # Risk (canonical names)
                "wealth_compute_emv",
                "wealth_compute_evoi",
                "wealth_monte_carlo_simulate",
                "wealth_confluence_check",
                "wealth_asymmetry_check",
                # Domain engines
                "wealth_stock_analysis",
                "wealth_personal_finance",
                "wealth_market_data",
                "wealth_omni_wisdom",
                "wealth_agent_path",
                # Governance
                "wealth_vault_write",
                "wealth_vault_query",
                # Meta
                "wealth_system_registry_status",
                # Collapse signature (forged 2026-06-24)
                "wealth_collapse_signature_scan",
                "wealth_beautiful_mouse_scan",
                # Federation bridge (forged 2026-06-24)
                "wealth_arifos_judge_handoff",
            ],
        }

    # ── Collapse Signature (forged 2026-06-24) ────────────────────────────
    # Forensic tool: pattern-matches a scenario text against the institutional
    # collapse corpus (Enron, PDVSA, Pemex, 1MDB, WorldCom) and emits a
    # 2D risk map (Acemoglu × Calhoun) plus dimensional densities and
    # tripwire flags. Pairs with wealth-power-audit + wealth-capture-scan.
    #
    # Hard rule: diagnostic, not adversarial. Always pair with capture + power.
    # Hard rule: HIGH/CRITICAL → 888_HOLD.
    @mcp.tool(name="wealth_collapse_signature_scan")
    async def wealth_collapse_signature_scan(
        scenario: str,
        capital_type: str = "financial",
        historical_priors: list[str] | None = None,
    ) -> dict:
        """
        Scan a scenario text for institutional-collapse signatures against
        the historical corpus (Enron, PDVSA, Pemex, 1MDB, WorldCom).

        Returns:
        - profile: full signature profile (7 collapse signatures)
        - risk: collapse risk score
        - two_d_risk_map: Acemoglu × Calhoun quadrant
        - tripwires: 5-tripwire detection
        - dimensional_densities: per-axis density
        - priors_used: which corpus anchors were compared

        Use cases:
        - Audit a CEO speech / annual report against pre-collapse analogues
        - Compare PETRONAS / PEMEX / Petrobras narratives vs historical priors
        - Detect when a corporate narrative crosses from "technocratic
          optimism" into "triumphalism with structural erosion"

        DITEMPA BUKAN DIBERI. WEALTH computes, arifOS judges, Arif decides.
        """
        try:
            result = compute_collapse_risk(
                scenario=scenario,
                capital_type=capital_type,
                historical_priors=historical_priors or [],
            )
            # Cap confidence at 0.90 per F7 HUMILITY
            risk_score = result.get("risk", {}).get("score", 0.5)
            if isinstance(risk_score, (int, float)) and risk_score > 0.90:
                result["risk"]["score"] = 0.90
                result["risk"]["_humbled"] = True

            return wrap_result(
                tool_name="wealth_collapse_signature_scan",
                domain="collapse",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "collapse_corpus:enron,pdvsa,pemex,1mdb,worldcom",
                    f"priors_used:{','.join(historical_priors or ['none'])}",
                ],
                dignity_impact=result.get("profile", {})
                    .get("wisdom_axis", {}).get("dignity", {}).get("label"),
                capture_risk_level=result.get("profile", {})
                    .get("acemoglu_axis", {}).get("label"),
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_collapse_signature_scan",
                domain="collapse",
                result={"error": str(e), "scenario_length": len(scenario)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Collapse scanner error: {e}"],
            )


def _register_advanced_tools(mcp: FastMCP) -> None:
    """Register advanced forensic + federation-bridge tools (forged 2026-06-24).
    These close three eurekas: counterfactual mode (in omni_wisdom),
    beautiful mouse detector (Phase C early warning), and the
    arifOS judge handoff (federation loop closure).
    """

    # ── Beautiful Mouse Detector (Phase C early warning) ─────────────────
    # Detects Calhoun behavioural-death Phase C ENTRY. Lower threshold
    # than collapse scanner; fires earlier. Use BEFORE any institutional
    # health claim. Pairs with collapse_signature_scan.
    @mcp.tool(name="wealth_beautiful_mouse_scan")
    async def wealth_beautiful_mouse_scan(
        text: str,
        historical_priors: list[str] | None = None,
    ) -> dict:
        """
        Scan a narrative for Calhoun Phase C (Beautiful Mouse) signatures.

        Detects 6 indicators:
        1. PERFECT_PERFORMANCE  — no friction narrative
        2. ZERO_FAILURE        — absence of failure treated as virtue
        3. NARRATIVE_CENTRALISATION — one story dominates
        4. TALENT_DRAIN        — no one inside fights, Ψ sidelined
        5. MONITOR_CULTURE     — metrics over conflict
        6. EXTERNAL_BLAME      — delays and failures blamed outward

        Verdicts: ABSENT | EMERGING | ACTIVE | DOMINANT.
        Confidence hard-capped at 0.85 (lower than collapse scanner
        because Phase C is inherently ambiguous).

        Use cases:
        - Audit CEO speeches / annual reports for Phase C entry
        - Pre-flight check before any institutional health claim
        - Cross-check with collapse_signature_scan (Phase D imminent)

        F6 MARUAH: never names individuals. Reference roles, not people.
        F13 SOVEREIGN: diagnostic only, never declares collapse.

        DITEMPA BUKAN DIBERI. WEALTH computes, arifOS judges, Arif decides.
        """
        try:
            result = compute_beautiful_mouse_score(
                text=text,
                historical_priors=historical_priors or [],
            )
            if "error" in result:
                return wrap_result(
                    tool_name="wealth_beautiful_mouse_scan",
                    domain="collapse",
                    result=result,
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[result["error"]],
                )
            return wrap_result(
                tool_name="wealth_beautiful_mouse_scan",
                domain="collapse",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "calhoun_phase_c_indicators",
                    f"priors:{','.join(historical_priors or ['none'])}",
                ],
                capture_risk_level=result.get("phase_c_verdict"),
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_beautiful_mouse_scan",
                domain="collapse",
                result={"error": str(e), "text_length": len(text)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Beautiful mouse scan error: {e}"],
            )

    # ── arifOS Judge Handoff (federation loop closure) ───────────────────
    # Prepares a WEALTH verdict for arifOS 888_JUDGE. Two modes:
    # - prepare: build the envelope, return it. Agent or A-FORGE submits.
    # - submit:  actually call arif_judge via MCP, return the verdict.
    #
    # This is the architectural property that makes F13 SOVEREIGN a
    # substrate guarantee, not an agent discipline. WEALTH cannot make
    # constitutional decisions; the bridge is the only path that does.
    @mcp.tool(name="wealth_arifos_judge_handoff")
    async def wealth_arifos_judge_handoff(
        tool_name: str,
        result: str,
        intent: str,
        capability: str,
        blast_radius: str = "MEDIUM",
        reversibility_level: str = "PARTIAL",
        epistemic_state: str = "DERIVED",
        domain: str = "capital",
        mode: str = "prepare",
        session_id: str = "",
        actor_id: str = "WEALTH",
        evidence: str = "[]",
    ) -> dict:
        """
        Prepare (or submit) a WEALTH verdict for arifOS 888_JUDGE.

        Args:
            tool_name: the WEALTH tool that produced the verdict
            result: JSON string of the WEALTH result to be judged
            intent: the capital decision being proposed
            capability: the specific capability requested
                        (e.g., "register_collapse_signature_claim",
                         "execute_stock_trade", "issue_capital_recommendation")
            blast_radius: LOW | MEDIUM | HIGH | CRITICAL
            reversibility_level: FULL | PARTIAL | NONE
            epistemic_state: OBSERVED | DERIVED | INTERPRETED | SPECULATED
            domain: capital | risk | power | wisdom | collapse | meta
            mode: prepare (default) | submit
            session_id: optional arifOS session
            actor_id: calling actor (default: "WEALTH")
            evidence: JSON string of evidence list

        Modes:
        - prepare: builds the arif_judge envelope + constitutional pre-check.
                   Returns the envelope. Non-mutating. F1 AMANAH compliant.
        - submit:  actually calls arif_judge via MCP. Returns the verdict
                   or an error if arifOS is unreachable. F1: envelope
                   preserved on failure for retry.

        The handoff is an architectural property, not an agent discipline.
        WEALTH prepares. arifOS judges. The sovereign decides.

        DITEMPA BUKAN DIBEI. Forged, not given.
        """
        try:
            # Parse the JSON-encoded inputs
            try:
                result_dict = json.loads(result) if isinstance(result, str) else result
            except json.JSONDecodeError:
                return wrap_result(
                    tool_name="wealth_arifos_judge_handoff",
                    domain="governance",
                    result={"error": "result_must_be_valid_json", "received_type": type(result).__name__},
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=["result parameter is not valid JSON"],
                )
            try:
                evidence_list = json.loads(evidence) if isinstance(evidence, str) else (evidence or [])
            except json.JSONDecodeError:
                evidence_list = []

            handoff = prepare_judge_handoff(
                tool_name=tool_name,
                result=result_dict,
                intent=intent,
                capability=capability,
                blast_radius=blast_radius,
                reversibility_level=reversibility_level,
                epistemic_state=epistemic_state,
                domain=domain,
                session_id=session_id or None,
                actor_id=actor_id or None,
                evidence=evidence_list,
            )

            if mode == "submit" and handoff["readiness"] == "READY":
                submission = await submit_to_arif_judge(handoff["handoff_envelope"])
                return wrap_result(
                    tool_name="wealth_arifos_judge_handoff",
                    domain="governance",
                    result={
                        "handoff": handoff,
                        "submission": submission,
                    },
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.STRONG,
                    source_attribution=["wealth_arifos_bridge", "arifos_mcp"],
                    claim_state=ClaimState.SEALED,
                )

            return wrap_result(
                tool_name="wealth_arifos_judge_handoff",
                domain="governance",
                result=handoff,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=["wealth_arifos_bridge"],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_arifos_judge_handoff",
                domain="governance",
                result={"error": str(e), "tool_name": tool_name, "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Judge handoff error: {e}"],
            )


def _register_resources(mcp: FastMCP) -> None:
    """Register MCP resources for WEALTH (remediation: previously zero resources)."""

    @mcp.resource("afwealth://schema")
    def afwealth_schema() -> str:
        """WEALTH canonical tool surface and version info."""
        return json.dumps({
            "organ": "WEALTH",
            "version": "2026.06.15",
            "role": "Capital Intelligence for arifOS federation",
            "authority": "WEALTH computes. arifOS judges. Arif decides.",
            "protocol": "MCP 2025-11-25",
            "tool_prefix": "wealth_",
            "resource_scheme": "afwealth://",
            "canonical_tools": [
                "wealth_wisdom_evaluate", "wealth_power_audit", "wealth_capture_scan",
                "wealth_compute_npv", "wealth_compute_irr",
                "wealth_conservation_check", "wealth_flow_check", "wealth_runway_check",
                "wealth_compute_emv", "wealth_compute_evoi", "wealth_monte_carlo_simulate",
                "wealth_confluence_check", "wealth_asymmetry_check",
                "wealth_stock_analysis", "wealth_personal_finance",
                "wealth_market_data", "wealth_omni_wisdom", "wealth_agent_path",
                "wealth_vault_write", "wealth_vault_query",
                "wealth_system_registry_status",
                "wealth_collapse_signature_scan",
                "wealth_beautiful_mouse_scan",
                "wealth_arifos_judge_handoff",
            ],
            "naming_convention": "wealth_<verb>_<noun>",
        }, indent=2)

    @mcp.resource("afwealth://health")
    def afwealth_health() -> str:
        """WEALTH organ health status."""
        return json.dumps({
            "status": "ALIVE",
            "version": "2026.06.15",
            "domain": "WEALTH Federated Domain",
            "transport": "streamable-http",
            "read_only": True,
            "final_authority": "arifOS 888_JUDGE",
        }, indent=2)

    @mcp.resource("afwealth://tools/registry")
    def afwealth_tools_registry() -> str:
        """Full tool registry with deprecation status."""
        tools = {
            "active": [
                {"name": "wealth_wisdom_evaluate", "domain": "wisdom", "verb": "evaluate"},
                {"name": "wealth_power_audit", "domain": "power", "verb": "audit"},
                {"name": "wealth_capture_scan", "domain": "power", "verb": "scan"},
                {"name": "wealth_compute_npv", "domain": "capital", "verb": "compute"},
                {"name": "wealth_compute_irr", "domain": "capital", "verb": "compute"},
                {"name": "wealth_compute_emv", "domain": "risk", "verb": "compute"},
                {"name": "wealth_compute_evoi", "domain": "risk", "verb": "compute"},
                {"name": "wealth_monte_carlo_simulate", "domain": "risk", "verb": "simulate"},
                {"name": "wealth_conservation_check", "domain": "capital", "verb": "check"},
                {"name": "wealth_flow_check", "domain": "capital", "verb": "check"},
                {"name": "wealth_runway_check", "domain": "capital", "verb": "check"},
                {"name": "wealth_confluence_check", "domain": "risk", "verb": "check"},
                {"name": "wealth_asymmetry_check", "domain": "risk", "verb": "check"},
                {"name": "wealth_stock_analysis", "domain": "stock", "verb": "analysis"},
                {"name": "wealth_personal_finance", "domain": "personal", "verb": "finance"},
                {"name": "wealth_market_data", "domain": "macro", "verb": "data"},
                {"name": "wealth_omni_wisdom", "domain": "synthesis", "verb": "wisdom"},
                {"name": "wealth_agent_path", "domain": "meta", "verb": "path"},
                {"name": "wealth_vault_write", "domain": "governance", "verb": "write"},
                {"name": "wealth_vault_query", "domain": "governance", "verb": "query"},
                {"name": "wealth_system_registry_status", "domain": "meta", "verb": "status"},
                {"name": "wealth_collapse_signature_scan", "domain": "collapse", "verb": "scan"},
                {"name": "wealth_beautiful_mouse_scan", "domain": "collapse", "verb": "scan"},
                {"name": "wealth_arifos_judge_handoff", "domain": "governance", "verb": "handoff"},
            ],
        }
        return json.dumps(tools, indent=2)

    # ── Canon & doctrine resources (forged 2026-06-24) ────────────────────
    @mcp.resource("afwealth://canon/002-human-law")
    def afwealth_canon_002_human_law() -> str:
        """CANON 002 — Human Law as Capital Geometry. Draft, pending 888 ratification."""
        canon_path = os.path.join(
            base_dir, "canon", "002_HUMAN_LAW.md"
        )
        try:
            with open(canon_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps({
                "error": "canon_002_not_found",
                "expected_path": canon_path,
                "fallback": "Law is capital geometry. No value without jurisdiction.",
            }, indent=2)

    @mcp.resource("afwealth://glossary")
    def afwealth_glossary() -> str:
        """WEALTH/ArifOS canonical glossary. 999 SEAL ALIVE."""
        glossary_path = os.path.join(
            base_dir, "canon", "GLOSSARY.md"
        )
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps({
                "error": "glossary_not_found",
                "expected_path": glossary_path,
                "fallback_terms": [
                    {"term": "888_HOLD", "def": "Human sovereignty gate"},
                    {"term": "999_SEAL", "def": "Final legitimacy stamp"},
                    {"term": "ΔS", "def": "Entropy delta, must be ≤ 0"},
                    {"term": "F1-F13", "def": "Thirteen constitutional floors"},
                    {"term": "VAULT999", "def": "Append-only immutable ledger"},
                ],
            }, indent=2)

    @mcp.resource("afwealth://federation/contract")
    def afwealth_federation_contract() -> str:
        """WEALTH federation contract — position, authority, handoffs."""
        contract_path = os.path.join(
            base_dir, "FEDERATION_CONTRACT.md"
        )
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps({
                "organ": "WEALTH",
                "role": "Capital intelligence — compute, never allocate",
                "authority_chain": "arifOS (8088) → WEALTH (18082) → A-FORGE (7071) → VAULT999 (8100)",
                "owns": [
                    "NPV, IRR, EMV, EVOI, DSCR, payback",
                    "Portfolio allocation modeling",
                    "Market data (FX, commodities, equities)",
                    "D4 stock analysis",
                    "Capital-readiness feeds from GEOX",
                ],
                "never": [
                    "Moves capital or executes trades",
                    "Authorizes investment decisions",
                    "Adjudicates constitutional verdicts",
                ],
                "verdict": "WEALTH tells you what the capital looks like. It does not move the money. The sovereign decides.",
            }, indent=2)


def _register_prompts(mcp: FastMCP) -> None:
    """Register MCP prompts for WEALTH (remediation: previously zero prompts).
    Prompts are templated invocations an agent can fetch to standardise
    common capital-intelligence workflows."""

    @mcp.prompt(name="wealth_capital_deal_brief")
    def wealth_capital_deal_brief(
        proposal: str,
        capital_type: str = "financial",
        context: str = "{}",
    ) -> str:
        """
        Synthesise a capital recommendation across the 13 WEALTH
        thermodynamics primitives. Returns a templated brief that
        sequences conservation → flow → gradient → entropy → energy →
        time → inertia → field → signal → game → boundary → hysteresis
        → survival, then asks for the 6-dim wisdom evaluation.

        Use this prompt BEFORE making any irreversible capital decision.
        """
        return (
            "# WEALTH Capital Deal Brief\n\n"
            f"**Proposal:** {proposal}\n"
            f"**Capital type:** {capital_type}\n"
            f"**Context:** {context}\n\n"
            "## Required sequence (skip no primitive)\n\n"
            "1. **Conservation** — does the balance sheet balance? "
            "`wealth_conservation_check` first.\n"
            "2. **Flow** — what is the income / expense / burn? "
            "`wealth_flow_check`.\n"
            "3. **Gradient** — where is the pressure differential? "
            "`wealth_asymmetry_check`.\n"
            "4. **Entropy** — how uncertain is the future? "
            "`wealth_compute_emv`.\n"
            "5. **Energy + Time** — what is the present value of the work? "
            "`wealth_compute_npv` + `wealth_compute_irr`.\n"
            "6. **Field** — what is the macro context? "
            "`wealth_market_data` (mode=fx/commodity/indicator).\n"
            "7. **Signal** — is new information worth its cost? "
            "`wealth_compute_evoi`.\n"
            "8. **Game** — who else is in this game? "
            "`wealth_power_audit` + `wealth_capture_scan`.\n"
            "9. **Boundary** — where does this system end? "
            "`wealth_asymmetry_check`.\n"
            "10. **Hysteresis** — does the path constrain the next state? "
            "`wealth_omni_wisdom(mode=path_params, ...)`.\n"
            "11. **Survival** — can the system still be alive at horizon? "
            "`wealth_runway_check`.\n"
            "12. **Inertia** — what will resist change? "
            "`wealth_omni_wisdom` synthesis.\n"
            "13. **Final wisdom** — 6-dim dignity / sovereignty / "
            "resilience / inequality / ecological / optionality. "
            "`wealth_wisdom_evaluate`.\n\n"
            "## Hard rules\n\n"
            "- You may not skip 1–4 before running 5+.\n"
            "- HIGH/CRITICAL risk → 888_HOLD regardless of NPV.\n"
            "- `wealth_vault_write` is irreversible. Use only after "
            "  human confirmation.\n"
            "- `wealth_omni_wisdom` cold-start with no context returns "
            "  HOLD / 0.5 — that is correct. Add context, then re-run.\n"
            "- Capture-scan and power-audit must run before any "
            "  institutional collapse claim.\n"
        )

    @mcp.prompt(name="wealth_d4_stock_pre_trade")
    def wealth_d4_stock_pre_trade(
        ticker: str,
        direction: str = "long",
        entry_price: str = "0.0",
        position_size: str = "0",
    ) -> str:
        """
        12-mode pre-trade checklist for D4 stock analysis.
        Use this prompt BEFORE entering a position. Forces
        verify_math, fundamentals, contrast, confluence,
        TAC-9, dignity, and capture-scan before commitment.
        """
        return (
            "# D4 Stock Pre-Trade Checklist\n\n"
            f"**Ticker:** {ticker}\n"
            f"**Direction:** {direction}\n"
            f"**Entry price:** {entry_price}\n"
            f"**Position size:** {position_size}\n\n"
            "## Required modes (in order)\n\n"
            "1. `wealth_stock_analysis(mode='verify_math', ...)` — "
            "sanity check the inputs.\n"
            "2. `wealth_stock_analysis(mode='fundamentals', ...)` — "
            "company snapshot, market data, fundamentals.\n"
            "3. `wealth_compute_npv(...)` — discounted-cash framing "
            "of expected return.\n"
            "4. `wealth_compute_emv(...)` — Expected Monetary Value "
            "across scenarios.\n"
            "5. `wealth_stock_analysis(mode='TAC-9', ...)` — "
            "Time / Accuracy / Confidence 9-factor.\n"
            "6. `wealth_asymmetry_check(...)` — upside vs downside "
            "skew.\n"
            "7. `wealth_confluence_check(...)` — are your indicators "
            "measuring the same signal?\n"
            "8. `wealth_stock_analysis(mode='contrast', ...)` — "
            "compare against the opposite thesis.\n"
            "9. `wealth_stock_analysis(mode='pre_trade', ...)` — "
            "final pre-trade gate.\n"
            "10. `wealth_capture_scan(advice_text, source_model)` — "
            "audit your own reasoning for capture.\n"
            "11. `wealth_wisdom_evaluate(proposal, capital_type='financial')` — "
            "6-dim dignity/sovereignty/resilience/inequality/ecological/optionality.\n"
            "12. `arif_judge(intent, capability, blast_radius)` — "
            "constitutional verdict before any irreversible trade.\n\n"
            "## Hard rules\n\n"
            "- Never skip mode 1. Bad inputs cascade into bad trades.\n"
            "- Mode 8 (contrast) is the only mode that forces you to "
            "  steel-man the opposite thesis.\n"
            "- Mode 12 (arif_judge) is required for any position "
            "  > 1% of portfolio or > RM 50,000 notional.\n"
            "- `wealth_vault_write` records the trade. Use it AFTER "
            "  the position is open, not before.\n"
        )


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
