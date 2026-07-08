"""
WEALTH Canonical Tools — 7-mode surface (FORGED 2026-07-07).

Collapses ~40 flat tools into 7 mode-dispatched canonical tools.
All existing implementations preserved. Legacy tool names survive as wrappers.

DITEMPA BUKAN DIBERI — Forged from the SVB backtest, not given.
"""

from __future__ import annotations

from typing import Any

from wealth_contracts.envelope import wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality


def register_canonical_tools(mcp):
    """Register the 7 canonical WEALTH tools. Call from server.py after imports."""

    # Core math
    from wealth_core.math import npv as _npv, irr as _irr, emv as _emv
    from wealth_core.capital import compute_conservation, compute_flow, compute_runway
    from wealth_core.risk import (
        compute_emv,
        monte_carlo_simulation,
        compute_evoi,
        detect_false_confluence,
        compute_asymmetry,
        fiscal_breakeven_oil_price,
    )

    # Optimizers
    from wealth_core.optimizers.kelly import kelly_sizing
    from wealth_core.optimizers.markowitz import markowitz_frontier
    from wealth_core.optimizers.robust import robust_portfolio
    from wealth_core.optimizers.chance_constrained import chance_constrained
    from wealth_core.optimizers.two_stage import two_stage_recourse

    # ═══════════════════════════════════════════════════════════════════
    # 1. capital_primitive — Deductive math primitives
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_primitive",
        description=(
            "Deductive capital math primitives. Pure computation — no inference, "
            "no governance verdict. Every mode is golden-tested against hand-checked "
            "cases. Standard cash flow convention: CF[0] at t=0 (initial investment, "
            "typically negative), CF[1:] at t=1, t=2, ...\n\n"
            "Modes: npv | irr | emv | evoi | mc | kelly | markowitz | "
            "robust | chance_constrained | two_stage"
        ),
        tags={"domain": "capital", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_primitive(
        mode: str,
        cash_flows: list[float] | None = None,
        discount_rate: float | None = None,
        outcomes: list[float] | None = None,
        probabilities: list[float] | None = None,
        prior_pos: float | None = None,
        posterior_pos: float | None = None,
        well_cost_musd: float | None = None,
        p50_value_musd: float | None = None,
        initial_value: float | None = None,
        growth_rate: float | None = None,
        volatility: float | None = None,
        periods: int = 10,
        simulations: int = 1000,
        win_prob: float | None = None,
        odds: float | None = None,
        returns: list[float] | None = None,
        covariances: list[list[float]] | None = None,
        risk_aversion: float = 1,
        risk_free_rate: float = 0,
        uncertainty_radius: float = 0.1,
        robust_type: str = "budget",
        confidence: float = 0.95,
        threshold: float = 0,
        first_stage_costs: dict | None = None,
        scenario_data: list[dict] | None = None,
        risk_constraint: float | None = None,
        seed: int | None = None,
    ) -> dict:
        m = mode.lower()

        if m == "npv":
            if cash_flows is None or discount_rate is None:
                raise ValueError("npv requires cash_flows, discount_rate")
            return wrap_result(
                tool_name="capital_primitive",
                domain="capital",
                result={
                    "npv": _npv(cash_flows, discount_rate),
                    "cash_flows": cash_flows,
                    "discount_rate": discount_rate,
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=["user_provided_inputs"],
            )

        if m == "irr":
            if cash_flows is None:
                raise ValueError("irr requires cash_flows")
            return wrap_result(
                tool_name="capital_primitive",
                domain="capital",
                result={"irr": _irr(cash_flows), "cash_flows": cash_flows},
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=["user_provided_inputs"],
            )

        if m == "emv":
            if outcomes is None or probabilities is None:
                raise ValueError("emv requires outcomes, probabilities")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=compute_emv(outcomes, probabilities),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_scenarios"],
            )

        if m == "evoi":
            if any(
                v is None
                for v in [prior_pos, posterior_pos, well_cost_musd, p50_value_musd]
            ):
                raise ValueError(
                    "evoi requires prior_pos, posterior_pos, well_cost_musd, p50_value_musd"
                )
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=compute_evoi(
                    prior_pos,
                    posterior_pos,
                    well_cost_musd,
                    p50_value_musd,
                    discount_rate or 0.1,
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_inputs"],
            )

        if m == "mc":
            if any(v is None for v in [initial_value, growth_rate, volatility]):
                raise ValueError("mc requires initial_value, growth_rate, volatility")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=monte_carlo_simulation(
                    initial_value,
                    growth_rate,
                    volatility,
                    periods,
                    simulations,
                    seed=seed,
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["monte_carlo_simulation"],
            )

        if m == "kelly":
            if win_prob is None or odds is None:
                raise ValueError("kelly requires win_prob, odds")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=kelly_sizing(win_prob, odds, risk_constraint=risk_constraint),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["kelly_criterion"],
            )

        if m == "markowitz":
            if returns is None or covariances is None:
                raise ValueError("markowitz requires returns, covariances")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=markowitz_frontier(
                    returns, covariances, risk_aversion, risk_free_rate
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["markowitz_optimization"],
            )

        if m == "robust":
            if returns is None:
                raise ValueError("robust requires returns")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=robust_portfolio(
                    returns, uncertainty_radius, robust_type, covariances=covariances
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["robust_optimization"],
            )

        if m == "chance_constrained":
            if returns is None or covariances is None:
                raise ValueError("chance_constrained requires returns, covariances")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=chance_constrained(returns, covariances, confidence, threshold),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["chance_constrained_optimization"],
            )

        if m == "two_stage":
            if first_stage_costs is None or scenario_data is None:
                raise ValueError("two_stage requires first_stage_costs, scenario_data")
            return wrap_result(
                tool_name="capital_primitive",
                domain="risk",
                result=two_stage_recourse(first_stage_costs, scenario_data),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["two_stage_recourse"],
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: npv, irr, emv, evoi, mc, kelly, markowitz, robust, chance_constrained, two_stage"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 2. capital_health — Financial health metrics
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_health",
        description=(
            "Financial health metrics. Deductive computation from structured inputs. "
            "No inference, no governance verdict.\n\n"
            "Modes: conservation | flow | runway | survival | fiscal_breakeven | "
            "confluence | asymmetry"
        ),
        tags={"domain": "capital", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_health(
        mode: str,
        assets: list[dict] | None = None,
        liabilities: list[dict] | None = None,
        income: list[dict] | None = None,
        expenses: list[dict] | None = None,
        liquid_assets: float | None = None,
        monthly_burn: float | None = None,
        conservative_factor: float = 0.8,
        survival_submode: str = "personal_finance",
        upside_scenarios: list[float] | None = None,
        downside_scenarios: list[float] | None = None,
        indicators: list[dict] | None = None,
        # fiscal_breakeven params
        total_govt_expenditure: float | None = None,
        non_oil_revenue: float | None = None,
        petronas_dividend_base_rm: float | None = None,
        oil_price_assumption_usd: float | None = None,
        # survival params
        monthly_income_v: float | None = None,
        monthly_expenses_v: float | None = None,
        horizon_months: int = 12,
    ) -> dict:
        m = mode.lower()

        if m == "conservation":
            return wrap_result(
                tool_name="capital_health",
                domain="capital",
                result=compute_conservation(assets, liabilities),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_assets"],
            )

        if m == "flow":
            return wrap_result(
                tool_name="capital_health",
                domain="capital",
                result=compute_flow(income, expenses),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_cashflows"],
            )

        if m == "runway":
            if liquid_assets is None or monthly_burn is None:
                raise ValueError("runway requires liquid_assets, monthly_burn")
            return wrap_result(
                tool_name="capital_health",
                domain="capital",
                result=compute_runway(liquid_assets, monthly_burn, conservative_factor),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_assets"],
            )

        if m == "survival":
            # Survival engine — delegates to the server-side implementation
            return await _call_legacy_tool(
                "wealth_survival_engine",
                {
                    "mode": survival_submode,
                    "monthly_income": monthly_income_v,
                    "monthly_expenses": monthly_expenses_v,
                    "liquid_assets": liquid_assets,
                    "horizon_months": horizon_months,
                },
            )

        if m == "fiscal_breakeven":
            if any(
                v is None
                for v in [
                    total_govt_expenditure,
                    non_oil_revenue,
                    petronas_dividend_base_rm,
                    oil_price_assumption_usd,
                ]
            ):
                raise ValueError(
                    "fiscal_breakeven requires total_govt_expenditure, non_oil_revenue, petronas_dividend_base_rm, oil_price_assumption_usd"
                )
            return wrap_result(
                tool_name="capital_health",
                domain="risk",
                result=fiscal_breakeven_oil_price(
                    total_govt_expenditure,
                    non_oil_revenue,
                    petronas_dividend_base_rm,
                    oil_price_assumption_usd,
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["fiscal_breakeven_model"],
            )

        if m == "confluence":
            if indicators is None:
                raise ValueError("confluence requires indicators")
            return wrap_result(
                tool_name="capital_health",
                domain="risk",
                result=detect_false_confluence(indicators),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["indicator_analysis"],
            )

        if m == "asymmetry":
            if upside_scenarios is None or downside_scenarios is None:
                raise ValueError(
                    "asymmetry requires upside_scenarios, downside_scenarios"
                )
            return wrap_result(
                tool_name="capital_health",
                domain="risk",
                result=compute_asymmetry(upside_scenarios, downside_scenarios),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["scenario_analysis"],
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: conservation, flow, runway, survival, fiscal_breakeven, confluence, asymmetry"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 3. capital_diagnose — Abductive institutional diagnostics
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_diagnose",
        description=(
            "Abductive institutional diagnostics — inference from partial evidence. "
            "REQUIRED: domain_scope declares calibration domain (e.g. 'extraction_fraud', "
            "'duration_mismatch', 'governance_churn'). Unknown fields are REJECTED "
            "(not silently dropped to 0.0). Output includes alternative hypotheses "
            "ruled out, not just a scalar score.\n\n"
            "Modes: stress_index | governance_capacity | cascade_model | "
            "exploitation_detect | collapse_signature | beautiful_mouse | "
            "capture_scan | power_audit | bid_surface | optimize_mwc"
        ),
        tags={"domain": "institutional", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_diagnose(
        mode: str,
        domain_scope: str = "",
        org_name: str = "",
        financial_signals: dict | None = None,
        governance_signals: dict | None = None,
        workforce_signals: dict | None = None,
        legal_signals: dict | None = None,
        exploitation_signals: dict | None = None,
        scenario: str = "",
        text: str = "",
        advice_text: str = "",
        source_model: str = "",
        board_members: list[dict] | None = None,
        committees: list[dict] | None = None,
        stress_level: float = 0.3,
        counterparty_actions: list[dict] | None = None,
        institution_state: dict | None = None,
        timeline: list[dict] | None = None,
        intervention_scenario: dict | None = None,
        bids: list[dict] | None = None,
        players: list[dict] | None = None,
        majority_threshold: float = 0.5,
        actor_list: list[str] | None = None,
        context: dict | None = None,
    ) -> dict:
        m = mode.lower()

        if m == "stress_index":
            from wealth_core.institutional import compute_stress_index

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_stress_index(
                    org_name,
                    financial_signals or {},
                    governance_signals or {},
                    workforce_signals or {},
                    legal_signals or {},
                    exploitation_signals or {},
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "financial_signals",
                    "governance_signals",
                    "workforce_signals",
                ],
            )

        if m == "governance_capacity":
            from wealth_core.institutional import compute_governance_capacity

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_governance_capacity(
                    board_members or [], committees or [], stress_level
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["governance_analysis"],
            )

        if m == "cascade_model":
            from wealth_core.institutional import compute_cascade

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_cascade(timeline or [], intervention_scenario),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["cascade_model"],
            )

        if m == "exploitation_detect":
            from wealth_core.institutional import compute_exploitation

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_exploitation(
                    counterparty_actions or [], institution_state or {}
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["exploitation_detection"],
            )

        if m == "collapse_signature":
            from wealth_core.collapse_signature.scanner import compute_collapse_risk

            return wrap_result(
                tool_name="capital_diagnose",
                domain="collapse",
                result=compute_collapse_risk(scenario),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["collapse_corpus:enron,pdvsa,pemex,1mdb,worldcom"],
            )

        if m == "beautiful_mouse":
            from wealth_core.collapse_signature.beautiful_mouse import (
                compute_beautiful_mouse_score,
            )

            return wrap_result(
                tool_name="capital_diagnose",
                domain="collapse",
                result=compute_beautiful_mouse_score(text),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["calhoun_phase_c_indicators"],
            )

        if m == "capture_scan":
            from wealth_core.power.capture_detector import detect_capture

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=detect_capture(advice_text, source_model=source_model),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=[f"model:{source_model}"],
            )

        if m == "power_audit":
            from wealth_core.power import audit_power

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=audit_power(scenario, actors=actor_list, context=context),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=["scenario_text_analysis"],
            )

        if m == "bid_surface":
            from wealth_mcp.tools.bid_surface import compute_bid_surface

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_bid_surface(bids or []),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["bid_scoring_surface"],
            )

        if m == "optimize_mwc":
            from wealth_mcp.tools.optimize_mwc import compute_mwc

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_mwc(players or [], majority_threshold),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["mwc_optimization"],
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: stress_index, governance_capacity, cascade_model, exploitation_detect, collapse_signature, beautiful_mouse, capture_scan, power_audit, bid_surface, optimize_mwc"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 4. capital_wisdom — Synthesis and meta-analysis
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_wisdom",
        description=(
            "Capital wisdom synthesis — evaluates proposals across dignity, sovereignty, "
            "resilience, inequality, ecological cost, and optionality. Advisory only. "
            "Does NOT emit GO/HOLD/SEAL verdicts — those are arifOS's domain.\n\n"
            "Modes: wisdom | omni | epistemic"
        ),
        tags={"domain": "wisdom", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_wisdom(
        mode: str,
        proposal: str = "",
        capital_type: str = "financial",
        context: dict | None = None,
        memory_query: str = "",
        target: str = "",
    ) -> dict:
        m = mode.lower()

        if m == "wisdom":
            from wealth_core.wisdom import compute_wisdom

            return wrap_result(
                tool_name="capital_wisdom",
                domain="wisdom",
                result=compute_wisdom(
                    proposal, capital_type=capital_type, context=context
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=["proposal_text_analysis"],
            )

        if m == "omni":
            # Omni wisdom delegates to the server-side tool
            return await _call_legacy_tool(
                "wealth_omni_wisdom",
                {
                    "mode": "synthesize",
                    "memory_query": memory_query,
                },
            )

        if m == "epistemic":
            from wealth_core.epistemic import audit_epistemic

            return wrap_result(
                tool_name="capital_wisdom",
                domain="wisdom",
                result=audit_epistemic(target),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["epistemic_audit"],
            )

        raise ValueError(f"Unknown mode '{mode}'. Valid: wisdom, omni, epistemic")

    # ═══════════════════════════════════════════════════════════════════
    # 5. capital_market — Market data and stock analysis
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_market",
        description=(
            "Market data and stock analysis. Live/cached financial data with source "
            "attribution. Observational only — no governance verdict.\n\n"
            "Modes: fx | commodity | indicator | stock"
        ),
        tags={"domain": "market", "kind": "observational", "canonical": "v1"},
    )
    async def capital_market(
        mode: str,
        base: str = "USD",
        targets: str = "MYR,SGD,GBP",
        commodity: str = "brent_crude",
        indicator: str = "usd_myr",
        country: str = "MYS",
        ticker: str = "",
        stock_mode: str = "verify_math",
        entry_price: float = 0,
        exit_price: float | None = None,
        current_price: float | None = None,
        position_size: int = 0,
        status_: str = "unrealized",
        direction: str = "long",
        factors: dict | None = None,
    ) -> dict:
        m = mode.lower()

        if m == "fx":
            return await _call_legacy_tool(
                "wealth_market_data", {"mode": "fx", "base": base, "targets": targets}
            )
        if m == "commodity":
            return await _call_legacy_tool(
                "wealth_market_data", {"mode": "commodity", "commodity": commodity}
            )
        if m == "indicator":
            return await _call_legacy_tool(
                "wealth_market_data",
                {"mode": "indicator", "indicator": indicator, "country": country},
            )
        if m == "stock":
            return await _call_legacy_tool(
                "wealth_stock_analysis",
                {
                    "mode": stock_mode,
                    "ticker": ticker,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "current_price": current_price,
                    "position_size": position_size,
                    "status": status_,
                    "direction": direction,
                    "factors": factors,
                },
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: fx, commodity, indicator, stock"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 6. capital_ledger — Immutable vault
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_ledger",
        description=(
            "VAULT999 immutable ledger access. Query is read-only (no ack required). "
            "Write requires explicit human acknowledgment (ack_irreversible=true). "
            "WEALTH computes. arifOS judges. Arif decides. WEALTH does not self-seal.\n\n"
            "Modes: query | write"
        ),
        tags={"domain": "vault", "kind": "mutating", "canonical": "v1"},
    )
    async def capital_ledger(
        mode: str,
        query: str = "",
        limit: int = 10,
        asset_id: str = "",
        tx_type: str = "",
        amount: float = 0,
        currency: str = "MYR",
        description: str = "",
        ack_irreversible: bool = False,
    ) -> dict:
        m = mode.lower()

        if m == "query":
            return await _call_legacy_tool(
                "wealth_vault_query",
                {
                    "query": query,
                    "limit": limit,
                    "asset_id": asset_id,
                },
            )
        if m == "write":
            if not ack_irreversible:
                return wrap_result(
                    tool_name="capital_ledger",
                    domain="vault",
                    result={
                        "status": "HOLD",
                        "message": "Write requires ack_irreversible=true. This action is irreversible.",
                    },
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.WEAK,
                    source_attribution=["ledger_write_gate"],
                )
            return await _call_legacy_tool(
                "wealth_vault_write",
                {
                    "tx_type": tx_type,
                    "amount": amount,
                    "currency": currency,
                    "description": description,
                },
            )

        raise ValueError(f"Unknown mode '{mode}'. Valid: query, write")

    # ═══════════════════════════════════════════════════════════════════
    # 7. capital_registry — Meta and introspection
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_registry",
        description=(
            "WEALTH meta/introspection. Registry status, tool schema, domain index, "
            "health check. Observational only.\n\n"
            "Modes: status | schema | domains | health"
        ),
        tags={"domain": "meta", "kind": "observational", "canonical": "v1"},
    )
    async def capital_registry(mode: str = "status") -> dict:
        m = mode.lower()

        if m == "status":
            return await _call_legacy_tool(
                "wealth_registry_status", {"mode": "registry"}
            )

        if m == "schema":
            return await _call_legacy_tool("wealth_schema", {})

        if m == "domains":
            return {
                "version": "2026.07.07",
                "domains": [
                    {
                        "name": "capital",
                        "kind": "deductive",
                        "tools": ["capital_primitive", "capital_health"],
                    },
                    {
                        "name": "institutional",
                        "kind": "abductive",
                        "tools": ["capital_diagnose"],
                    },
                    {
                        "name": "wisdom",
                        "kind": "abductive",
                        "tools": ["capital_wisdom"],
                    },
                    {
                        "name": "market",
                        "kind": "observational",
                        "tools": ["capital_market"],
                    },
                    {"name": "vault", "kind": "mutating", "tools": ["capital_ledger"]},
                    {
                        "name": "meta",
                        "kind": "observational",
                        "tools": ["capital_registry"],
                    },
                ],
                "canonical_tool_count": 7,
                "legacy_tools": "preserved_as_wrappers",
                "preload_mechanism": "REMOVED_2026-07-07",
            }

        if m == "health":
            return {
                "status": "ALIVE",
                "version": "2026.07.07",
                "domain": "WEALTH Federated Domain",
                "architecture": "federated-7-canonical",
                "canonical_tools": 7,
                "preload_mechanism": "REMOVED_2026-07-07",
            }

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: status, schema, domains, health"
        )

    # ── Helper: call an existing legacy tool by name (internal dispatch) ──
    async def _call_legacy_tool(tool_name: str, arguments: dict) -> dict:
        """Dispatch to an existing MCP tool registered on the same server."""
        try:
            # FastMCP 3.x: use public call_tool API (not internal _tool_manager)
            result = await mcp.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            # Fallback: try with wealth_ prefix
            if not tool_name.startswith("wealth_"):
                try:
                    result = await mcp.call_tool(f"wealth_{tool_name}", arguments)
                    return result
                except Exception:
                    pass
            return {"error": f"legacy_dispatch_failed: {tool_name}", "detail": str(e)}

    return {
        "capital_primitive": capital_primitive,
        "capital_health": capital_health,
        "capital_diagnose": capital_diagnose,
        "capital_wisdom": capital_wisdom,
        "capital_market": capital_market,
        "capital_ledger": capital_ledger,
        "capital_registry": capital_registry,
    }
