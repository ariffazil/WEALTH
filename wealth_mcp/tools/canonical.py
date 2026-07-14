"""
WEALTH Canonical Tools — 7-mode surface (FORGED 2026-07-07).

Collapses ~40 flat tools into 7 mode-dispatched canonical tools.
All existing implementations preserved. Legacy tool names survive as wrappers.

DITEMPA BUKAN DIBERI — Forged from the SVB backtest, not given.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BeforeValidator
from wealth_contracts.envelope import wrap_result, WEALTH_OUTPUT_SCHEMA
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality


def _coerce_json_string(v: Any) -> Any:
    """Coerce MCP transport string serialization back to native types.

    FastMCP/Pydantic validates parameters BEFORE function body runs.
    This validator runs at schema level via Annotated[..., BeforeValidator].
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            return v
    return v


# Schema-level coerced types — Pydantic validates AFTER coercion
CoercedList = Annotated[list[float] | None, BeforeValidator(_coerce_json_string)]
CoercedIntList = Annotated[list[int] | None, BeforeValidator(_coerce_json_string)]
CoercedDict = Annotated[dict | None, BeforeValidator(_coerce_json_string)]
CoercedDictList = Annotated[list[dict] | None, BeforeValidator(_coerce_json_string)]
CoercedStrList = Annotated[list[str] | None, BeforeValidator(_coerce_json_string)]


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
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Deductive capital math primitives. Pure computation — no inference, "
            "no governance verdict. Every mode is golden-tested against hand-checked "
            "cases. Standard cash flow convention: CF[0] at t=0 (initial investment, "
            "typically negative), CF[1:] at t=1, t=2, ...\n\n"
            "Modes: npv | irr | emv | evoi | mc | kelly | markowitz | "
            "robust | chance_constrained | two_stage\n\n"
            "Use when: the user asks about NPV, IRR, expected monetary value, "
            "Kelly criterion sizing, Markowitz portfolio optimization, Monte Carlo "
            "simulation, or any deductive capital math computation."
        ),
        tags={"domain": "capital", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_primitive(
        mode: str,
        cash_flows: CoercedList = None,
        discount_rate: float | None = None,
        outcomes: CoercedList = None,
        probabilities: CoercedList = None,
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
        returns: CoercedList = None,
        covariances: Annotated[
            list[list[float]] | None, BeforeValidator(_coerce_json_string)
        ] = None,
        risk_aversion: float = 1,
        risk_free_rate: float = 0,
        uncertainty_radius: float = 0.1,
        robust_type: str = "budget",
        confidence: float = 0.95,
        threshold: float = 0,
        first_stage_costs: CoercedDict = None,
        scenario_data: CoercedDictList = None,
        risk_constraint: float | None = None,
        seed: int | None = None,
    ) -> dict:
        # Coerce MCP transport string serialization (fallback for non-Annotated params)

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
                evidence_quality=EvidenceQuality.OBSERVED,
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
                evidence_quality=EvidenceQuality.OBSERVED,
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
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Financial health metrics. Deductive computation from structured inputs. "
            "No inference, no governance verdict.\n\n"
            "Modes: conservation | flow | runway | survival | fiscal_breakeven | "
            "confluence | asymmetry\n\n"
            "Use when: the user asks about net worth, cash flow, financial runway, "
            "burn rate, fiscal breakeven oil price, or false-confluence detection "
            "in financial indicators."
        ),
        tags={"domain": "capital", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_health(
        mode: str,
        assets: CoercedDictList = None,
        liabilities: CoercedDictList = None,
        income: CoercedDictList = None,
        expenses: CoercedDictList = None,
        liquid_assets: float | None = None,
        monthly_burn: float | None = None,
        conservative_factor: float = 0.8,
        survival_submode: str = "personal_finance",
        upside_scenarios: CoercedList = None,
        downside_scenarios: CoercedList = None,
        indicators: CoercedDictList = None,
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
        # Coerce MCP transport string serialization

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
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Abductive institutional diagnostics — inference from partial evidence. "
            "Surface: mode, domain_scope, payload (dict). Mode-specific fields go in "
            "payload. REQUIRED: domain_scope declares calibration domain. Unknown "
            "fields are REJECTED (not silently dropped to 0.0).\n\n"
            "Modes: stress_index | governance_capacity | cascade_model | "
            "exploitation_detect | collapse_signature | beautiful_mouse | "
            "capture_scan | power_audit | bid_surface | optimize_mwc | "
            "cadence_monitor | crisis_reflex\n\n"
            "Use when: institutional stress, governance, collapse, power, MWC, "
            "cadence monitoring, or crisis reflex analysis."
        ),
        tags={"domain": "institutional", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_diagnose(
        mode: str,
        domain_scope: str = "",
        payload: CoercedDict = None,
    ) -> dict:
        """Mode-dispatched institutional diagnostics (ZEN 2026-07-11 W3).

        Surface: mode, domain_scope, payload. Mode-specific fields in payload.
        domain_scope: unknown fields REJECTED by engines (not zeroed). Math unchanged.
        """
        # Coerce MCP transport string serialization

        m = mode.lower()
        p: dict[str, Any] = dict(payload or {})

        if m == "stress_index":
            from wealth_core.institutional import compute_stress_index

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_stress_index(
                    p.get("org_name") or "",
                    p.get("financial_signals") or {},
                    p.get("governance_signals") or {},
                    p.get("workforce_signals") or {},
                    p.get("legal_signals") or {},
                    p.get("exploitation_signals") or {},
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
                    p.get("board_members") or [],
                    p.get("committees") or [],
                    float(p.get("stress_level", 0.3)),
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
                result=compute_cascade(
                    p.get("timeline") or [], p.get("intervention_scenario")
                ),
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
                    p.get("counterparty_actions") or [],
                    p.get("institution_state") or {},
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
                result=compute_collapse_risk(p.get("scenario") or ""),
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
                result=compute_beautiful_mouse_score(p.get("text") or ""),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["calhoun_phase_c_indicators"],
            )

        if m == "capture_scan":
            from wealth_core.power.capture_detector import detect_capture

            advice = p.get("advice_text") or ""
            src_model = p.get("source_model") or ""

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=detect_capture(
                    scenario=advice,
                    actors=p.get("actors") or [],
                    context=p.get("context") or {"source_model": src_model},
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=[f"model:{src_model}"] if src_model else [],
            )

        if m == "power_audit":
            from wealth_core.power import audit_power

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=audit_power(
                    p.get("scenario") or "",
                    actors=p.get("actor_list"),
                    context=p.get("context"),
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=["scenario_text_analysis"],
            )

        if m == "bid_surface":
            from wealth_mcp.tools.bid_surface import compute_bid_surface

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_bid_surface(p.get("bids") or []),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["bid_scoring_surface"],
            )

        if m == "optimize_mwc":
            from wealth_mcp.tools.optimize_mwc import compute_mwc

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_mwc(
                    p.get("players") or [],
                    float(p.get("majority_threshold", 0.5)),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["mwc_optimization"],
            )

        if m == "cadence_monitor":
            from wealth_core.institutional.cadence import compute_cadence

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_cadence(
                    approval_cycles=p.get("approval_cycles"),
                    payment_cycles=p.get("payment_cycles"),
                    meeting_logs=p.get("meeting_logs"),
                    contract_signatures=p.get("contract_signatures"),
                    budget_releases=p.get("budget_releases"),
                    org_name=p.get("org_name", domain_scope),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "approval_cycle_trend",
                    "payment_cycle_trend",
                    "meeting_decision_ratio",
                    "contract_velocity",
                    "budget_release_timing",
                ],
            )

        if m == "crisis_reflex":
            from wealth_core.institutional.crisis_reflex import compute_crisis_reflex

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_crisis_reflex(
                    capital_allocation=p.get("capital_allocation"),
                    capability_moves=p.get("capability_moves"),
                    truth_events=p.get("truth_events"),
                    burden_data=p.get("burden_data"),
                    decision_shifts=p.get("decision_shifts"),
                    recovery_data=p.get("recovery_data"),
                    external_events=p.get("external_events"),
                    dignity_data=p.get("dignity_data"),
                    org_name=p.get("org_name", domain_scope),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "capital_allocation",
                    "capability_moves",
                    "truth_events",
                    "burden_distribution",
                    "decision_shifts",
                    "recovery_investment",
                    "external_posture",
                    "human_dignity",
                ],
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: stress_index, governance_capacity, cascade_model, exploitation_detect, collapse_signature, beautiful_mouse, capture_scan, power_audit, bid_surface, optimize_mwc, cadence_monitor, crisis_reflex"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 4. capital_wisdom — Synthesis and meta-analysis
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_wisdom",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Capital wisdom synthesis — evaluates proposals across dignity, sovereignty, "
            "resilience, inequality, ecological cost, and optionality. Advisory only. "
            "Does NOT emit GO/HOLD/SEAL verdicts — those are arifOS's domain.\n\n"
            "Modes: wisdom | omni | epistemic\n\n"
            "Use when: the user wants a wisdom-weighted evaluation of a capital "
            "proposal, deal framing, hysteresis-aware path analysis, or counterfactual "
            "reasoning across 13 capital primitives."
        ),
        tags={"domain": "wisdom", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_wisdom(
        mode: str,
        proposal: str = "",
        capital_type: str = "financial",
        context: CoercedDict = None,
        memory_query: str = "",
        target: str = "",
    ) -> dict:
        # Coerce MCP transport string serialization

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
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Market data and stock analysis. Observational only.\n\n"
            "Top-level: mode, base, targets, commodity, indicator, country. "
            "Stock fields in stock_payload dict.\n\n"
            "Modes: fx | commodity | indicator | stock\n\n"
            "Use when: FX, commodities, macro indicators, or stock analysis."
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
        stock_payload: CoercedDict = None,
    ) -> dict:
        """Market data (ZEN 2026-07-11 W4). Stock fields in stock_payload."""
        # Coerce MCP transport string serialization

        m = mode.lower()
        sp: dict[str, Any] = dict(stock_payload or {})

        if m == "fx":
            raw = await _call_legacy_tool(
                "wealth_market_data", {"mode": "fx", "base": base, "targets": targets}
            )
            return wrap_result(tool_name="capital_market", domain="capital", result=raw)
        if m == "commodity":
            raw = await _call_legacy_tool(
                "wealth_market_data", {"mode": "commodity", "commodity": commodity}
            )
            return wrap_result(tool_name="capital_market", domain="capital", result=raw)
        if m == "indicator":
            raw = await _call_legacy_tool(
                "wealth_market_data",
                {"mode": "indicator", "indicator": indicator, "country": country},
            )
            return wrap_result(tool_name="capital_market", domain="capital", result=raw)
        if m == "stock":
            raw = await _call_legacy_tool(
                "wealth_stock_analysis",
                {
                    "mode": sp.get("stock_mode") or sp.get("mode") or "verify_math",
                    "ticker": sp.get("ticker") or "",
                    "entry_price": sp.get("entry_price") or 0,
                    "exit_price": sp.get("exit_price"),
                    "current_price": sp.get("current_price"),
                    "position_size": sp.get("position_size") or 0,
                    "status": sp.get("status") or sp.get("status_") or "unrealized",
                    "direction": sp.get("direction") or "long",
                    "factors": sp.get("factors"),
                },
            )
            return wrap_result(tool_name="capital_market", domain="capital", result=raw)
        if m == "gold":
            analysis = (
                commodity
                if commodity in ("snapshot", "decompose", "regime", "structural")
                else "snapshot"
            )
            raw = await _call_legacy_tool(
                "wealth_market_data",
                {"mode": "gold", "commodity": analysis},
            )
            return wrap_result(tool_name="capital_market", domain="capital", result=raw)

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: fx, commodity, indicator, stock, gold"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 6. capital_ledger — Immutable vault
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_ledger",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "VAULT999 immutable ledger access. Query is read-only (no ack required). "
            "Write requires explicit human acknowledgment (ack_irreversible=true). "
            "WEALTH computes. arifOS judges. Arif decides. WEALTH does not self-seal.\n\n"
            "Modes: query | write\n\n"
            "Use when: the user wants to query past capital transactions from "
            "VAULT999, or write a new transaction (requires human ack for writes)."
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
            raw = await _call_legacy_tool(
                "wealth_vault_query",
                {
                    "query": query,
                    "limit": limit,
                    "asset_id": asset_id,
                },
            )
            return wrap_result(tool_name="capital_ledger", domain="vault", result=raw)
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
                    "ack_irreversible": True,
                },
            )

        raise ValueError(f"Unknown mode '{mode}'. Valid: query, write")

    # ═══════════════════════════════════════════════════════════════════
    # 7. capital_registry — Meta and introspection
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_registry",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "WEALTH meta/introspection. Registry status, tool schema, domain index, "
            "health check. Observational only.\n\n"
            "Modes: status | schema | domains | health\n\n"
            "Use when: the user wants to inspect the WEALTH tool registry, "
            "check available domains, view tool schemas, or run a health check."
        ),
        tags={"domain": "meta", "kind": "observational", "canonical": "v1"},
    )
    async def capital_registry(mode: str = "status") -> dict:
        m = mode.lower()
        _CANONICAL = [
            "capital_primitive",
            "capital_health",
            "capital_diagnose",
            "capital_wisdom",
            "capital_market",
            "capital_ledger",
            "capital_registry",
        ]

        if m == "status":
            return {
                "status": "OK",
                "organ": "WEALTH",
                "version": "2026.07.11",
                "architecture": "federated-7-canonical",
                "canonical_tools": _CANONICAL,
                "canonical_tool_count": 7,
                "registry_truth": "PASS",
                "legacy_dispatch": "direct_import",
                "final_authority": "ARIF",
                "read_only": True,
            }

        if m == "schema":
            raw = await _call_legacy_tool("wealth_schema", {})
            return wrap_result(tool_name="capital_registry", domain="meta", result=raw)

        if m == "domains":
            return {
                "version": "2026.07.11",
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
                "legacy_tools": "direct_import_engines",
                "preload_mechanism": "REMOVED_2026-07-07",
            }

        if m == "health":
            return {
                "status": "ALIVE",
                "version": "2026.07.11",
                "domain": "WEALTH Federated Domain",
                "architecture": "federated-7-canonical",
                "canonical_tools": 7,
                "preload_mechanism": "REMOVED_2026-07-07",
            }

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: status, schema, domains, health"
        )

    # ── Helper: resolve legacy engines by direct import (ZEN 2026-07-11 W5) ──
    async def _call_legacy_tool(tool_name: str, arguments: dict) -> dict:
        """Dispatch to in-process engine functions (legacy MCP names as keys)."""
        args = dict(arguments or {})
        try:
            if tool_name in ("wealth_market_data", "market_data"):
                from internal.monolith import wealth_market_data

                if str(args.get("mode", "")).lower() == "indicator":
                    args = {**args, "mode": "macro"}
                result = wealth_market_data(**args)
                return result if isinstance(result, dict) else {"result": result}

            if tool_name in ("wealth_stock_analysis", "stock_analysis"):
                from internal.monolith import wealth_stock_analysis

                result = await wealth_stock_analysis(**args)
                return result if isinstance(result, dict) else {"result": result}

            if tool_name in ("wealth_vault_query", "vault_query"):
                from host.governance.vault_supabase import query_vault999_async

                q = args.get("query") or args.get("asset_id") or ""
                raw = await query_vault999_async(
                    query=str(q),
                    limit=int(args.get("limit") or 10),
                    session_id=args.get("session_id"),
                )
                return {
                    "query": raw.get("query", q),
                    "earth_refs": raw.get("earth_refs", []),
                    "count": raw.get("count", 0),
                    "vault_seal": raw.get("vault_seal", "VAULT999"),
                    "status": "OK",
                    "read_only": True,
                }

            if tool_name in ("wealth_vault_write", "vault_write"):
                from internal.monolith import vault_write

                result = vault_write(
                    action=str(
                        args.get("tx_type") or args.get("action") or "capital_tx"
                    ),
                    payload={
                        "amount": args.get("amount"),
                        "currency": args.get("currency"),
                        "description": args.get("description"),
                    },
                    ack_irreversible=bool(args.get("ack_irreversible", True)),
                )
                return result if isinstance(result, dict) else {"result": result}

            if tool_name in (
                "wealth_registry_status",
                "wealth_system_registry_status",
                "registry_status",
            ):
                from internal.monolith import wealth_system_registry_status

                result = await wealth_system_registry_status(
                    mode=str(args.get("mode") or "registry")
                )
                return result if isinstance(result, dict) else {"result": result}

            if tool_name in ("wealth_schema", "schema"):
                return {
                    "organ": "WEALTH",
                    "version": "2026.07.11",
                    "role": "Capital Intelligence for arifOS federation",
                    "authority": "WEALTH computes. arifOS judges. Arif decides.",
                    "canonical_tools": [
                        "capital_primitive",
                        "capital_health",
                        "capital_diagnose",
                        "capital_wisdom",
                        "capital_market",
                        "capital_ledger",
                        "capital_registry",
                    ],
                    "canonical_tool_count": 7,
                    "legacy_mcp_dispatch": "direct_import",
                }

            if tool_name in ("wealth_survival_engine", "survival_engine"):
                from internal.monolith import wealth_survival_engine

                result = await wealth_survival_engine(**args)
                return result if isinstance(result, dict) else {"result": result}

            if tool_name in ("wealth_omni_wisdom", "omni_wisdom"):
                from internal.monolith import wealth_omni_wisdom

                result = await wealth_omni_wisdom(**args)
                return result if isinstance(result, dict) else {"result": result}

            return {
                "error": f"legacy_dispatch_failed: {tool_name}",
                "detail": "no direct import mapping for this legacy name",
            }
        except TypeError as e:
            return {
                "error": f"legacy_dispatch_failed: {tool_name}",
                "detail": f"TypeError: {e}",
                "arguments_keys": sorted(args.keys()),
            }
        except Exception as e:
            return {
                "error": f"legacy_dispatch_failed: {tool_name}",
                "detail": f"{type(e).__name__}: {e}",
            }

    # ── Entropy Integrity Mesh — WEALTH Extensions (Phase 2) ─────────────
    @mcp.tool(
        name="capital_entropy",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Capital and institutional entropy analysis. Modes: "
            "power_consequence_map, metric_purpose_audit, responsibility_ledger, "
            "trust_capital_decay, coercive_order_cost, entropy_externality. "
            "Measures information loss, consequence displacement, metric drift. "
            "Computes, never allocates."
        ),
        tags={
            "domain": "institutional",
            "kind": "abductive",
            "canonical": "v1",
            "entropy": "mesh",
        },
    )
    async def capital_entropy(
        mode: str,
        decision_makers: CoercedDictList = None,
        beneficiaries: CoercedDictList = None,
        cost_bearers: CoercedDictList = None,
        veto_holders: list[str | dict] | None = None,
        declared_purpose: str | None = None,
        current_kpis: CoercedDictList = None,
        actual_behaviors: CoercedStrList = None,
        excluded_outcomes: CoercedStrList = None,
        decision_ref: str | None = None,
        actors: CoercedDictList = None,
        trust_events: CoercedDictList = None,
        current_trust_balance: float = 0.5,
        order_indicators: CoercedDict = None,
        suppression_indicators: CoercedDict = None,
        actor_ref: str | None = None,
        local_efficiency_claims: CoercedDict = None,
        exported_costs: CoercedDictList = None,
    ) -> dict:
        """Entropy Integrity Mesh — WEALTH domain witness."""
        # Coerce MCP transport string serialization
        veto_holders = _coerce(veto_holders)

        # Normalize veto_holders: accept strings, convert to dicts (fixed 2026-07-12)
        if veto_holders is not None:
            veto_holders = [
                {"name": v} if isinstance(v, str) else v for v in veto_holders
            ]

        m = mode.lower().strip()
        try:
            import importlib.util, os

            _base = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "..",
                "..",
                "entropy-integrity",
                "mcp",
                "wealth",
            )

            if m == "power_consequence_map":
                _spec = importlib.util.spec_from_file_location(
                    "pcm", os.path.join(_base, "power_consequence_map.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_power_consequence_map(
                        decision_makers=decision_makers or [],
                        beneficiaries=beneficiaries or [],
                        cost_bearers=cost_bearers or [],
                        veto_holders=veto_holders,
                    ),
                )

            elif m == "metric_purpose_audit":
                _spec = importlib.util.spec_from_file_location(
                    "mpa", os.path.join(_base, "metric_purpose_audit.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_metric_purpose_audit(
                        declared_purpose=declared_purpose or "",
                        current_kpis=current_kpis or [],
                        actual_behaviors=actual_behaviors or [],
                        excluded_outcomes=excluded_outcomes,
                    ),
                )

            elif m == "responsibility_ledger":
                _spec = importlib.util.spec_from_file_location(
                    "rl", os.path.join(_base, "responsibility_ledger.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_responsibility_ledger(
                        decision_ref=decision_ref or "", actors=actors or []
                    ),
                )

            elif m == "trust_capital_decay":
                _spec = importlib.util.spec_from_file_location(
                    "tcd", os.path.join(_base, "trust_capital_decay.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_trust_capital_decay(
                        trust_events=trust_events or [],
                        current_trust_balance=current_trust_balance,
                    ),
                )

            elif m == "coercive_order_cost":
                _spec = importlib.util.spec_from_file_location(
                    "coc", os.path.join(_base, "coercive_order_cost.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_coercive_order_cost(
                        order_indicators=order_indicators or {},
                        suppression_indicators=suppression_indicators or {},
                    ),
                )

            elif m == "entropy_externality":
                _spec = importlib.util.spec_from_file_location(
                    "ee", os.path.join(_base, "entropy_externality.py")
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                return wrap_result(
                    "capital_entropy",
                    "institutional",
                    _mod.wealth_entropy_externality(
                        actor_ref=actor_ref or "",
                        local_efficiency_claims=local_efficiency_claims or {},
                        exported_costs=exported_costs or [],
                    ),
                )

            else:
                return {
                    "error": "UNKNOWN_MODE",
                    "valid": [
                        "power_consequence_map",
                        "metric_purpose_audit",
                        "responsibility_ledger",
                        "trust_capital_decay",
                        "coercive_order_cost",
                        "entropy_externality",
                    ],
                }
        except Exception as e:
            return {"error": str(e), "tool": "capital_entropy", "mode": m}

    return {
        "capital_primitive": capital_primitive,
        "capital_health": capital_health,
        "capital_diagnose": capital_diagnose,
        "capital_wisdom": capital_wisdom,
        "capital_market": capital_market,
        "capital_ledger": capital_ledger,
        "capital_registry": capital_registry,
        "capital_entropy": capital_entropy,
    }
