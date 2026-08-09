"""
WEALTH Canonical Tools — 8-mode capital surface (FORGED 2026-07-07).

Collapses ~40 flat tools into 8 mode-dispatched canonical tools.
All existing implementations preserved. Legacy tool names survive as wrappers.

DITEMPA BUKAN DIBERI — Forged from the SVB backtest, not given.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BeforeValidator
from wealth_contracts.authority import ExecutionAuthority
from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality
from wealth_mcp import (
    CAPITAL_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
    WEALTH_VERSION,
)


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


def _coerce_dict_to_list_of_dicts(v: Any) -> Any:
    """Coerce a single dict into list-of-dicts. F1 AMANAH: prevents silent
    input dropping when MCP transport serializes a single dict instead of
    a list of dicts. Applies to all CoercedDictList parameters."""
    v = _coerce_json_string(v)
    if isinstance(v, dict):
        return [v]
    return v


# Schema-level coerced types — Pydantic validates AFTER coercion
CoercedList = Annotated[list[float] | None, BeforeValidator(_coerce_json_string)]
CoercedIntList = Annotated[list[int] | None, BeforeValidator(_coerce_json_string)]
CoercedDict = Annotated[dict | None, BeforeValidator(_coerce_json_string)]
CoercedDictList = Annotated[list[dict] | None, BeforeValidator(_coerce_json_string)]
CoercedDictListStrict = Annotated[
    list[dict] | None, BeforeValidator(_coerce_dict_to_list_of_dicts)
]
CoercedStrList = Annotated[list[str] | None, BeforeValidator(_coerce_json_string)]


def register_canonical_tools(mcp):
    """Register the 8 canonical WEALTH tools. Call from server.py after imports."""

    # Core math
    from wealth_core.math import irr as _irr
    from wealth_core.math import npv as _npv
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
        description="Deductive capital math primitives — pure computation, no inference or governance verdict. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
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
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        # Coerce MCP transport string serialization (fallback for non-Annotated params)

        m = mode.lower()
        # SURVIVAL-OF-THE-FITTEST FIX 2026-07-24: alias normalization.
        # Accept common aliases so callers using verbose mode names
        # (e.g. "monte_carlo") still hit the canonical short name ("mc").
        # One-way: canonical modes win if both are aliased.
        _MODE_ALIASES = {
            "monte_carlo": "mc",
            "monte-carlo": "mc",
            "expected_monetary_value": "emv",
            "expected_value_of_information": "evoi",
            "value_of_information": "evoi",
            "expected_value": "emv",
            "kelly_criterion": "kelly",
            "mean_variance": "markowitz",
            "markowitz_mean_variance": "markowitz",
            "net_present_value": "npv",
            "internal_rate_of_return": "irr",
        }
        m = _MODE_ALIASES.get(m, m)

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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
        description="Financial health metrics — deductive computation from structured inputs, no inference or governance verdict. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
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
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
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
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "flow":
            return wrap_result(
                tool_name="capital_health",
                domain="capital",
                result=compute_flow(income, expenses),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["user_provided_cashflows"],
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "survival":
            # Zen Phase 2.2: validate submode before delegating — never silently fall through
            _VALID_SURVIVAL_SUBMODES = {
                "personal_finance",
                "corporate_runway",
                "sovereign_fiscal",
            }
            _sm = str(survival_submode or "").strip().lower()
            if _sm and _sm not in _VALID_SURVIVAL_SUBMODES:
                return wrap_result(
                    tool_name="capital_health",
                    domain="capital",
                    result={
                        "status": "ERROR",
                        "error_code": "UNKNOWN_SUBMODE",
                        "message": f"Unknown survival_submode '{survival_submode}'. Valid: {', '.join(sorted(_VALID_SURVIVAL_SUBMODES))}",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[
                        f"Unknown survival_submode '{survival_submode}'. Valid: {', '.join(sorted(_VALID_SURVIVAL_SUBMODES))}"
                    ],
                    session_id=session_id,
                    actor_id=actor_id,
                )

            if _sm == "sovereign_fiscal" or (
                total_govt_expenditure is not None
                and petronas_dividend_base_rm is not None
            ):
                if any(
                    v is None
                    for v in [
                        total_govt_expenditure,
                        non_oil_revenue,
                        petronas_dividend_base_rm,
                        oil_price_assumption_usd,
                    ]
                ):
                    # Loop 8 fix: return structured error instead of raising ValueError (MCP schema violation)
                    missing = [
                        k
                        for k, v in [
                            ("total_govt_expenditure", total_govt_expenditure),
                            ("non_oil_revenue", non_oil_revenue),
                            ("petronas_dividend_base_rm", petronas_dividend_base_rm),
                            ("oil_price_assumption_usd", oil_price_assumption_usd),
                        ]
                        if v is None
                    ]
                    return wrap_result(
                        tool_name="capital_health",
                        domain="capital",
                        result={
                            "status": "ERROR",
                            "error_code": "MISSING_REQUIRED_PARAMS",
                            "message": f"sovereign_fiscal requires: total_govt_expenditure, non_oil_revenue, petronas_dividend_base_rm, oil_price_assumption_usd",
                            "missing_params": missing,
                        },
                        epistemic_tag=EpistemicTag.ASSUMED,
                        evidence_quality=EvidenceQuality.MISSING,
                        errors=[
                            f"Missing required params for sovereign_fiscal: {', '.join(missing)}"
                        ],
                        session_id=session_id,
                        actor_id=actor_id,
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
                    session_id=session_id,
                    actor_id=actor_id,
                )

            if _sm == "corporate_runway":
                # Corporate runway: liquid_assets / monthly_burn → runway_months.
                # Distinct from personal_finance — no income/expense, burn rate is the driver.
                if liquid_assets is None or monthly_burn is None:
                    return wrap_result(
                        tool_name="capital_health",
                        domain="capital",
                        result={
                            "status": "ERROR",
                            "error_code": "MISSING_REQUIRED_PARAMS",
                            "message": "corporate_runway requires liquid_assets and monthly_burn",
                            "missing_params": [
                                k
                                for k, v in [
                                    ("liquid_assets", liquid_assets),
                                    ("monthly_burn", monthly_burn),
                                ]
                                if v is None
                            ],
                        },
                        epistemic_tag=EpistemicTag.ASSUMED,
                        evidence_quality=EvidenceQuality.MISSING,
                        errors=[
                            "corporate_runway requires liquid_assets and monthly_burn"
                        ],
                        session_id=session_id,
                        actor_id=actor_id,
                    )
                runway_months = (
                    liquid_assets / monthly_burn if monthly_burn > 0 else float("inf")
                )
                return wrap_result(
                    tool_name="capital_health",
                    domain="capital",
                    result={
                        "runway_months": round(runway_months, 1),
                        "liquid_assets": liquid_assets,
                        "monthly_burn": monthly_burn,
                        "verdict": "CORPORATE_RUNWAY_ADEQUATE"
                        if runway_months >= 12
                        else "CORPORATE_RUNWAY_CRITICAL",
                        "interpretation": (
                            f"Corporate runway: {runway_months:.1f} months at burn rate {monthly_burn}/month."
                            if runway_months < float("inf")
                            else "Infinite runway (zero burn rate)."
                        ),
                    },
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=["corporate_runway_computation"],
                    session_id=session_id,
                    actor_id=actor_id,
                )

            # Survival engine — delegates to the server-side implementation
            raw = await _call_legacy_tool(
                "wealth_survival_engine",
                {
                    "mode": _sm or "personal_finance",
                    "monthly_income": monthly_income_v,
                    "monthly_expenses": monthly_expenses_v,
                    "liquid_assets": liquid_assets,
                    "horizon_months": horizon_months,
                },
            )
            # If empty inputs / insufficient signal, enforce DRAFT / MISSING
            is_empty = (
                (monthly_income_v is None or monthly_income_v == 0)
                and (monthly_expenses_v is None or monthly_expenses_v == 0)
                and (liquid_assets is None or liquid_assets == 0)
            )
            if is_empty and isinstance(raw, dict):
                raw.setdefault("input_empty", True)

            # C4 FIX 2026-08-06: tool_name was "capital_market" — wrong attribution.
            # This is capital_health survival mode. Audit trail must preserve origin.
            return wrap_result(
                tool_name="capital_health",
                domain="capital",
                result=raw,
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                claim_state=ClaimState.DRAFT,
                execution_authorized=False,
                requires_888_hold=True,
                source_attribution=["survival_engine_unverified"],
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
        description="Abductive institutional diagnostics — inference from partial evidence across stress, governance, and institutional domains. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain": "institutional", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_diagnose(
        mode: str,
        domain_scope: str = "",
        payload: CoercedDict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """Mode-dispatched institutional diagnostics (ZEN 2026-07-11 W3).

        Surface: mode, domain_scope, payload. Mode-specific fields in payload.
        domain_scope: unknown fields REJECTED by engines (not zeroed). Math unchanged.
        """
        # Coerce MCP transport string serialization

        m = str(mode).lower()
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "collapse_signature":
            from wealth_core.collapse_signature.scanner import compute_collapse_risk

            return wrap_result(
                tool_name="capital_diagnose",
                domain="collapse",
                result=compute_collapse_risk(
                    p.get("scenario") or p.get("domain_scope") or ""
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["collapse_corpus:enron,pdvsa,pemex,1mdb,worldcom"],
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
            )

        if m in ("petronas_vitals", "sovereign_pulse", "petronas_phi"):
            # COMPUTE_ONLY distance-to-trip organ — no allocation, no trade signal
            from wealth_core.petronas_vitals import compute_petronas_vitals

            result = compute_petronas_vitals(
                tripwires=p.get("tripwires"),
                weights=p.get("weights"),
            )
            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "PETRONAS Group FRA FY2025 IFR",
                    "wealth_core.petronas_vitals",
                    "arif-fazil.com/vitals",
                ],
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
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
                session_id=session_id,
                actor_id=actor_id,
            )

        # Loop 9 fix: return structured error for unknown mode (was: ValueError with incomplete mode list)
        _VALID_MODES = [
            "stress_index",
            "governance_capacity",
            "cascade_model",
            "exploitation_detect",
            "collapse_signature",
            "beautiful_mouse",
            "capture_scan",
            "power_audit",
            "bid_surface",
            "optimize_mwc",
            "cadence_monitor",
            "crisis_reflex",
            "petronas_vitals",
            "sovereign_pulse",
            "petronas_phi",
        ]
        return wrap_result(
            tool_name="capital_diagnose",
            domain="institutional",
            result={
                "status": "ERROR",
                "error_code": "UNKNOWN_MODE",
                "message": f"Unknown mode '{mode}'. Valid: {', '.join(_VALID_MODES)}",
                "valid_modes": _VALID_MODES,
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            errors=[f"Unknown mode '{mode}'. Valid: {', '.join(_VALID_MODES)}"],
            session_id=session_id,
            actor_id=actor_id,
        )

    # capital_wisdom DELETED 2026-08-06 — M0 audit. Normative synthesis
    # violates 'WEALTH computes, arifOS frames'. F13 directive: DELETE.
    # 120 lines removed. arifOS owns framing; WEALTH owns computation.

    # ═══════════════════════════════════════════════════════════════════
    # 5. capital_market — Market data and stock analysis
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_market",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Market data and commodity intelligence — observational with derived and interpreted fields. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
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
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
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
            # Zen Phase 4: route through internal get_snapshot engine
            # instead of stale wealth_market_data legacy path.
            _COMMODITY_MAP = {
                "brent_crude": "oil",
                "wti_crude": "oil",
                "natural_gas_henry": "gas",
                "natural_gas_jkm": "gas",
                "lng_asia": "gas",
                "gold": "gold",
            }
            engine_name = _COMMODITY_MAP.get(commodity.lower().replace(" ", "_"), None)
            if engine_name:
                from wealth_core.commodity_engines import get_snapshot

                raw = await get_snapshot(engine_name)
            else:
                raw = await _call_legacy_tool(
                    "wealth_market_data", {"mode": "commodity", "commodity": commodity}
                )
            # Zen C9: cross-witness metadata
            if isinstance(raw, dict):
                raw["_cross_witness"] = {
                    "primary_source": "wealth_core.commodity_engines",
                    "feed_type": "LIVE" if engine_name else "CACHED",
                    "witness_status": "SINGLE_SOURCE",
                    "note": "Cross-witness requires second independent source. Delta > 3% would raise WITNESS_DIVERGENCE.",
                }
            return wrap_result(
                tool_name="capital_market",
                domain="capital",
                result=raw,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["commodity_engine_live"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
            )

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

        # ── Internal engine modes: gold, oil, gas ─────────────────────────
        # These call the internal commodity engines at :3456-3458.
        # WEALTH owns meaning. Engines supply evidence.
        if m in ("gold", "oil", "gas"):
            from wealth_core.commodity_engines import call_engine, get_snapshot

            # Map commodity parameter to operation (backward compat)
            # Preferred: capital_market(mode="gold", operation="snapshot")
            if "operation" in sp and sp["operation"]:
                op = sp["operation"]
            else:
                op = commodity if commodity != "brent_crude" else "snapshot"

            # Map common names to engine endpoint names
            op_map = {
                "signal": "signal_v2",
                "daily": "daily_brief",
            }
            engine_op = op_map.get(op, op)

            if engine_op == "snapshot":
                raw = await get_snapshot(m)
            else:
                raw = await call_engine(m, engine_op)

            # ── FLAME Enrichment (P2, 2026-07-25) ─────────────────────
            # For signal/daily modes, enrich raw engine output with FLAME
            # natural-language interpretation. FLAME is ADVISORY only —
            # it NEVER generates buy/sell/hold recommendations.
            flame_signal = None
            if engine_op in ("signal_v2", "daily_brief"):
                try:
                    from tools.flame_client import flame_market_signal

                    raw_str = json.dumps(raw) if isinstance(raw, dict) else str(raw)
                    flame_signal = flame_market_signal(
                        raw_str, commodity=m, timeout_s=8
                    )
                except Exception:
                    pass  # FLAME is optional — never block on failure

            result = raw
            if flame_signal:
                result = {
                    "engine_output": raw,
                    "flame_interpretation": flame_signal,
                    "_note": "FLAME interpretation is ADVISORY only. "
                    "Verify with governed cascade before any capital decision.",
                }

            return wrap_result(
                tool_name="capital_market",
                domain="capital",
                result=result,
                epistemic_tag=EpistemicTag.OBSERVED
                if engine_op == "snapshot"
                else EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[f"wealth://commodity/{m}/{engine_op}"],
                session_id=session_id,
                actor_id=actor_id,
            )

        raise ValueError(
            f"Unknown mode '{mode}'. "
            "Valid: fx, commodity, indicator, stock, gold, oil, gas"
        )

    # ═══════════════════════════════════════════════════════════════════
    # 6. capital_ledger — Immutable vault
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_ledger",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="VAULT999 immutable ledger access — query read-only, write requires human acknowledgment. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain", "kind", "canonical", "action:irreversible", "risk:c2"},
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
        amount_satoshi: int = 0,
        payment_hash: str = "",
        ack_irreversible: bool = False,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        m = mode.lower()

        if m == "query":
            raw = await _call_legacy_tool(
                "wealth_vault_query",
                {
                    "query": query,
                    "limit": limit,
                    "asset_id": asset_id,
                    "session_id": session_id,
                },
            )
            return wrap_result(
                tool_name="capital_ledger",
                domain="vault",
                result=raw,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.OBSERVED,
                source_attribution=["vault999_query"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
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
                    evidence_quality=EvidenceQuality.SPECULATED,
                    execution_authority=ExecutionAuthority.BLOCKED,
                    requires_888_hold=True,
                    source_attribution=["ledger_write_gate"],
                    session_id=session_id,
                    trace_id=trace_id,
                    actor_id=actor_id,
                    warnings=["No ledger mutation was attempted."],
                )
            raw = await _call_legacy_tool(
                "wealth_vault_write",
                {
                    "tx_type": tx_type,
                    "amount": amount,
                    "currency": currency,
                    "description": description,
                    "amount_satoshi": amount_satoshi,
                    "payment_hash": payment_hash,
                    "ack_irreversible": True,
                    "session_id": session_id,
                    "trace_id": trace_id,
                    "actor_id": actor_id,
                },
            )
            persisted = raw.get("status") == "APPENDED"
            return wrap_result(
                tool_name="capital_ledger",
                domain="vault",
                result=raw,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=(
                    EvidenceQuality.OBSERVED
                    if persisted
                    else EvidenceQuality.SPECULATED
                ),
                execution_authority=(
                    ExecutionAuthority.OBSERVATION
                    if persisted
                    else ExecutionAuthority.BLOCKED
                ),
                requires_888_hold=not persisted,
                source_attribution=["vault999_local_append"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                errors=[] if persisted else ["Ledger persistence was not confirmed."],
            )

        raise ValueError(f"Unknown mode '{mode}'. Valid: query, write")

    # ═══════════════════════════════════════════════════════════════════
    # 7. capital_registry — Meta and introspection
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_registry",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="WEALTH meta/introspection — registry status, tool schema, domain index, health check. Observational only. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain": "meta", "kind": "observational", "canonical": "v1"},
    )
    async def capital_registry(
        mode: str = "status",
        tool_name: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        del tool_name  # Reserved for schema lookup compatibility.
        m = mode.lower()
        canonical_tools = list(CAPITAL_TOOL_NAMES)
        public_tools = list(PUBLIC_TOOL_NAMES)
        architecture = f"federated-{len(canonical_tools)}-canonical"

        # Live Probe of all canonical & public tool modules (Fix W6)
        probe_failures = []
        for t_name in public_tools:
            try:
                if t_name == "capital_entropy":
                    # Zen Phase 3.2: use the same importlib path as capital_entropy tool,
                    # not the broken 'from entropy_integrity.mcp.wealth' import
                    import importlib.util as _iu
                    from pathlib import Path as _P

                    _ent_base = (
                        _P(__file__).resolve().parents[2]
                        / "entropy-integrity"
                        / "mcp"
                        / "wealth"
                    )
                    _ent_file = _ent_base / "power_consequence_map.py"
                    if _ent_file.is_file():
                        _ent_spec = _iu.spec_from_file_location("pcm_probe", _ent_file)
                        if _ent_spec and _ent_spec.loader:
                            _ent_mod = _iu.module_from_spec(_ent_spec)
                            _ent_spec.loader.exec_module(_ent_mod)
                    else:
                        raise ImportError(
                            f"entropy-integrity module absent: {_ent_file}"
                        )
                elif t_name == "wealth_judge_handoff":
                    from wealth_contracts.envelope import ClaimState
            except Exception as _p_exc:
                probe_failures.append(f"{t_name}: {type(_p_exc).__name__} ({_p_exc})")

        reg_truth = "PASS" if not probe_failures else "DEGRADED"

        if m == "status":
            return wrap_result(
                tool_name="capital_registry",
                domain="meta",
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                result={
                    "status": "OK" if not probe_failures else "DEGRADED",
                    "organ": "WEALTH",
                    "version": WEALTH_VERSION,
                    "architecture": architecture,
                    "canonical_tools": canonical_tools,
                    "canonical_tool_count": len(canonical_tools),
                    "public_tools": public_tools,
                    "public_tool_count": len(public_tools),
                    "registry_truth": reg_truth,
                    "probe_failures": probe_failures,
                    "legacy_dispatch": "direct_import",
                    "final_authority": "ARIF",
                    "read_only": True,
                },
            )

        if m == "schema":
            # This mapping is deliberately limited to PUBLIC_TOOL_NAMES.  Legacy
            # engines remain callable through internal dispatch, but they are not
            # public MCP tools and must not appear in the registry schema.
            tool_schemas = {
                "capital_primitive": {
                    "modes": [
                        "npv",
                        "irr",
                        "emv",
                        "evoi",
                        "mc",
                        "kelly",
                        "markowitz",
                        "robust",
                        "chance_constrained",
                        "two_stage",
                    ],
                    "description": "Financial mathematics and decision analysis primitives",
                },
                "capital_health": {
                    "modes": [
                        "conservation",
                        "flow",
                        "runway",
                        "survival",
                        "fiscal_breakeven",
                        "confluence",
                        "asymmetry",
                    ],
                    "survival_submodes": [
                        "personal_finance",
                        "corporate_runway",
                        "sovereign_fiscal",
                    ],
                    "description": "Financial health, runway, and survival computation",
                },
                "capital_diagnose": {
                    "modes": [
                        "stress_index",
                        "governance_capacity",
                        "cascade_model",
                        "exploitation_detect",
                        "collapse_signature",
                        "beautiful_mouse",
                        "capture_scan",
                        "power_audit",
                        "bid_surface",
                        "optimize_mwc",
                        "cadence_monitor",
                        "crisis_reflex",
                    ],
                    "description": "Abductive institutional diagnosis and governance capacity",
                },
                "capital_market": {
                    "modes": [
                        "fx",
                        "commodity",
                        "indicator",
                        "stock",
                        "gold",
                        "oil",
                        "gas",
                    ],
                    "description": "Live commodity, FX, and country market indicators",
                },
                "capital_ledger": {
                    "modes": ["query", "write"],
                    "description": "VAULT999 immutable append-only ledger",
                },
                "capital_registry": {
                    "modes": ["status", "schema", "domains", "health"],
                    "description": "WEALTH organ self-introspection and registry status",
                },
                "capital_entropy": {
                    "modes": [
                        "power_consequence_map",
                        "metric_purpose_audit",
                        "responsibility_ledger",
                        "trust_capital_decay",
                        "coercive_order_cost",
                        "entropy_externality",
                    ],
                    "description": "Thermodynamic power/consequence and metric-purpose drift",
                },
                "wealth_judge_handoff": {
                    "modes": ["prepare", "submit"],
                    "description": "Sovereign 888_HOLD judge handoff envelope",
                },
            }
            return wrap_result(
                tool_name="capital_registry",
                domain="meta",
                result={
                    "version": WEALTH_VERSION,
                    "architecture": architecture,
                    "tools": tool_schemas,
                    "canonical_tool_count": len(canonical_tools),
                    "public_tool_count": len(public_tools),
                },
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
            )

        if m == "domains":
            return wrap_result(
                tool_name="capital_registry",
                domain="meta",
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                result={
                    "version": WEALTH_VERSION,
                    "domains": [
                        {
                            "name": "capital",
                            "kind": "deductive",
                            "tools": ["capital_primitive", "capital_health"],
                        },
                        {
                            "name": "institutional",
                            "kind": "abductive",
                            "tools": ["capital_diagnose", "capital_entropy"],
                        },
                        {
                            "name": "market",
                            "kind": "observational",
                            "tools": ["capital_market"],
                        },
                        {
                            "name": "vault",
                            "kind": "mutating",
                            "tools": ["capital_ledger"],
                        },
                        {
                            "name": "governance",
                            "kind": "advisory",
                            "tools": ["wealth_judge_handoff"],
                        },
                        {
                            "name": "meta",
                            "kind": "observational",
                            "tools": ["capital_registry"],
                        },
                    ],
                    "canonical_tool_count": len(canonical_tools),
                    "public_tool_count": len(public_tools),
                    "legacy_dispatch": "direct_import",
                },
            )

        if m == "health":
            return wrap_result(
                tool_name="capital_registry",
                domain="meta",
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                result={
                    "status": "ALIVE",
                    "version": WEALTH_VERSION,
                    "domain": "WEALTH Federated Domain",
                    "architecture": architecture,
                    "canonical_tools": len(canonical_tools),
                    "public_tools": len(public_tools),
                },
            )

        # Zen Phase 2: unknown mode → structured error, never MCP -32602
        return wrap_result(
            tool_name="capital_registry",
            domain="meta",
            result={
                "status": "ERROR",
                "error_code": "UNKNOWN_MODE",
                "message": f"Unknown mode '{mode}'. Valid: status, schema, domains, health",
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            claim_state=ClaimState.VOID,
            errors=[f"Unknown mode '{mode}'. Valid: status, schema, domains, health"],
            session_id=session_id,
            actor_id=actor_id,
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
                import asyncio

                from host.governance.vault_supabase import append_vault999

                action = str(args.get("tx_type") or args.get("action") or "capital_tx")
                record = {
                    "tool": "capital_ledger",
                    "action": action,
                    "payload": {
                        "amount": args.get("amount"),
                        "amount_satoshi": args.get("amount_satoshi"),
                        "currency": args.get("currency"),
                        "description": args.get("description"),
                        "payment_hash": args.get("payment_hash"),
                    },
                    "verdict": "SEAL",
                    "session_id": args.get("session_id"),
                    "trace_id": args.get("trace_id"),
                    "actor_id": args.get("actor_id"),
                }
                result = await asyncio.to_thread(append_vault999, record)
                if not isinstance(result, dict):
                    return {
                        "status": "ERROR",
                        "error": "VAULT999 append returned no observable result.",
                    }

                persistence = result.get("persistence") or {
                    "status": "UNCONFIRMED",
                    "error": "VAULT999 append did not report persistence state.",
                }
                response = {
                    "status": persistence.get("status", "UNCONFIRMED"),
                    "action": action,
                    "persistence": persistence,
                    "integrity": result.get("integrity"),
                }
                vault_id = result.get("event_id") or result.get("ledger_id")
                chain_hash = result.get("chain_hash")
                if vault_id:
                    response["vault_id"] = vault_id
                if chain_hash:
                    response["chain_hash"] = chain_hash
                return response

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
                    "version": WEALTH_VERSION,
                    "role": "Capital Intelligence for arifOS federation",
                    "authority": "WEALTH computes. arifOS judges. Arif decides.",
                    "canonical_tools": list(CAPITAL_TOOL_NAMES),
                    "canonical_tool_count": len(CAPITAL_TOOL_NAMES),
                    "public_tools": list(PUBLIC_TOOL_NAMES),
                    "public_tool_count": len(PUBLIC_TOOL_NAMES),
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
        description="Capital and institutional entropy analysis — measures information loss, consequence displacement, and metric drift. Computes, never allocates. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={
            "domain": "institutional",
            "kind": "abductive",
            "canonical": "v1",
            "entropy": "mesh",
        },
    )
    async def capital_entropy(
        mode: str,
        decision_makers: CoercedDictListStrict = None,
        beneficiaries: CoercedDictListStrict = None,
        cost_bearers: CoercedDictListStrict = None,
        veto_holders: CoercedStrList = None,
        declared_purpose: str | None = None,
        current_kpis: CoercedDictListStrict = None,
        actual_behaviors: CoercedStrList = None,
        excluded_outcomes: CoercedStrList = None,
        decision_ref: str | None = None,
        actors: CoercedDictListStrict = None,
        trust_events: CoercedDictListStrict = None,
        current_trust_balance: float = 0.5,
        order_indicators: CoercedDict = None,
        suppression_indicators: CoercedDict = None,
        actor_ref: str | None = None,
        local_efficiency_claims: CoercedDict = None,
        exported_costs: CoercedDictListStrict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
        shadow: bool = False,
    ) -> dict:
        """Entropy Integrity Mesh — WEALTH domain witness."""
        # Parameters are coerced by the Pydantic BeforeValidator annotations.
        if veto_holders is not None:
            veto_holders = [
                {"name": value} if isinstance(value, str) else value
                for value in veto_holders
            ]

        def _wrap_entropy(result: dict) -> dict:
            return wrap_result(
                tool_name="capital_entropy",
                domain="institutional",
                result=result,
                source_attribution=["entropy_integrity_local_dependency"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                shadow=shadow,
            )

        def _entropy_failure(
            code: str,
            message: str,
            *,
            action: str,
            hold: bool,
        ) -> dict:
            result = {
                "status": "UNAVAILABLE" if hold else "ERROR",
                "error_code": code,
                "message": message,
                "tool": "capital_entropy",
                "mode": m,
                "action": action,
            }
            if hold:
                result["holds"] = [code]
            return wrap_result(
                tool_name="capital_entropy",
                domain="institutional",
                result=result,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.SPECULATED,
                execution_authority=ExecutionAuthority.BLOCKED,
                requires_888_hold=False,
                source_attribution=["entropy_integrity_dependency_check"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                shadow=shadow,
                errors=[message],
            )

        m = str(mode).lower().strip()
        try:
            import importlib.util
            from pathlib import Path

            base = (
                Path(__file__).resolve().parents[2]
                / "entropy-integrity"
                / "mcp"
                / "wealth"
            )

            def _safe_load_module(name: str, filename: str):
                if not base.is_dir():
                    raise ImportError(
                        f"optional dependency directory is absent from this repository: {base}"
                    )
                filepath = base / filename
                if not filepath.is_file():
                    raise ImportError(
                        f"optional dependency module is absent: {filepath}"
                    )
                spec = importlib.util.spec_from_file_location(name, filepath)
                if spec is None or spec.loader is None:
                    raise ImportError(
                        f"cannot load optional dependency module: {filepath}"
                    )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module

            if m == "power_consequence_map":
                module = _safe_load_module("pcm", "power_consequence_map.py")
                return _wrap_entropy(
                    module.wealth_power_consequence_map(
                        decision_makers=decision_makers or [],
                        beneficiaries=beneficiaries or [],
                        cost_bearers=cost_bearers or [],
                        veto_holders=veto_holders,
                    )
                )

            if m == "metric_purpose_audit":
                # Zen Phase 3: keyword overlap is not semantic analysis.
                # This tool computes token-set Jaccard similarity only.
                # Output tagged SPECULATED/MISSING to prevent false precision.
                module = _safe_load_module("mpa", "metric_purpose_audit.py")
                raw_result = module.wealth_metric_purpose_audit(
                    declared_purpose=declared_purpose or "",
                    current_kpis=current_kpis or [],
                    actual_behaviors=actual_behaviors or [],
                    excluded_outcomes=excluded_outcomes,
                )
                # Strip the machine-generated interpretation verdict
                raw_result.pop("interpretation", None)
                raw_result["_zen_note"] = (
                    "Interpretation removed per Phase 3. "
                    "Keyword-overlap alignment scores are token-set Jaccard similarity — "
                    "NOT semantic analysis. Use the reflection questions, not the numbers."
                )
                return _wrap_entropy(
                    {
                        "audit_id": raw_result.get("audit_id"),
                        "declared_purpose": raw_result.get("declared_purpose"),
                        "kpi_alignment": raw_result.get("kpi_alignment", []),
                        "purpose_fidelity": raw_result.get("purpose_fidelity"),
                        "gaming_signals": raw_result.get("gaming_signals", []),
                        "externality_count": raw_result.get("externality_count", 0),
                        "excluded_outcomes": raw_result.get("excluded_outcomes", []),
                        "reflection": raw_result.get("reflection", []),
                        "metadata": raw_result.get("metadata", {}),
                        "_zen_note": (
                            "Interpretation removed per Phase 3. "
                            "Keyword-overlap alignment scores are token-set Jaccard similarity — "
                            "NOT semantic analysis. Use the reflection questions, not the numbers."
                        ),
                    }
                )

            if m == "responsibility_ledger":
                module = _safe_load_module("rl", "responsibility_ledger.py")
                return _wrap_entropy(
                    module.wealth_responsibility_ledger(
                        decision_ref=decision_ref or "", actors=actors or []
                    )
                )

            if m == "trust_capital_decay":
                module = _safe_load_module("tcd", "trust_capital_decay.py")
                return _wrap_entropy(
                    module.wealth_trust_capital_decay(
                        trust_events=trust_events or [],
                        current_trust_balance=current_trust_balance,
                    )
                )

            if m == "coercive_order_cost":
                module = _safe_load_module("coc", "coercive_order_cost.py")
                return _wrap_entropy(
                    module.wealth_coercive_order_cost(
                        order_indicators=order_indicators or {},
                        suppression_indicators=suppression_indicators or {},
                    )
                )

            if m == "entropy_externality":
                module = _safe_load_module("ee", "entropy_externality.py")
                return _wrap_entropy(
                    module.wealth_entropy_externality(
                        actor_ref=actor_ref or "",
                        local_efficiency_claims=local_efficiency_claims or {},
                        exported_costs=exported_costs or [],
                    )
                )

            return _entropy_failure(
                "UNKNOWN_MODE",
                f"Unknown mode '{mode}'.",
                action=(
                    "Use one of: power_consequence_map, metric_purpose_audit, "
                    "responsibility_ledger, trust_capital_decay, "
                    "coercive_order_cost, entropy_externality"
                ),
                hold=False,
            )
        except ImportError as exc:
            return _entropy_failure(
                "ENTROPY_MODULE_MISSING",
                str(exc),
                action=(
                    "Declare and vendor the optional entropy-integrity dependency "
                    "inside this repository before enabling this mode."
                ),
                hold=True,
            )
        except Exception as exc:
            return _entropy_failure(
                "ENTROPY_COMPUTE_ERROR",
                f"{type(exc).__name__}: {exc}",
                action="Inspect the named local dependency module and retry.",
                hold=True,
            )

    # ═══════════════════════════════════════════════════════════════════
    # 9. wealth_judge_handoff — Handoff envelope validation and submission
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="wealth_judge_handoff",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Build or validate structured handoff envelope for arifOS governance review and 888_HOLD judgment. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain": "meta", "kind": "governance", "canonical": "v1"},
    )
    async def wealth_judge_handoff(
        mode: str = "prepare",
        intent: str = "",
        reversibility: str = "REVERSIBLE",
        blast_radius: str = "low",
        actor_id: str | None = None,
        # C10 2026-08-06: This flag is CALLER-DECLARED. WEALTH has no independent
        # cryptographic verification of actor identity. Gate policy (blast_radius=
        # critical → 888_HOLD) is enforceable only when this flag is externally
        # verified (e.g., via SCT token validation in the governance wrapper).
        # Until C10 hardening, do not treat this as a security boundary.
        actor_cryptographically_verified: bool = False,
        payload: CoercedDict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """Validate and prepare handoff envelope for arifOS governance."""
        m = str(mode).lower().strip()
        p = payload or {}

        # 0. Unknown mode gate — never silently accept invalid modes (loop 10 fix)
        if m not in ("prepare", "submit"):
            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="meta",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_MODE",
                    "message": f"Unknown mode '{mode}'. Valid modes: prepare, submit.",
                    "valid_modes": ["prepare", "submit"],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Unknown mode '{mode}'. Valid: prepare, submit."],
                session_id=session_id,
                actor_id=actor_id,
            )

        # 1. Intent validation: reject vague/unbounded intents
        intent_clean = str(intent or p.get("intent", "")).strip()
        vague_intents = [
            "aku nak tau semua truth",
            "everything",
            "all truth",
            "tau semua",
            "test",
        ]
        is_unbounded = (
            not intent_clean
            or any(v in intent_clean.lower() for v in vague_intents)
            or len(intent_clean) < 5
        )

        # 2. Reversibility validation: enforce standard enum
        rev_raw = (
            str(reversibility or p.get("reversibility", "REVERSIBLE")).strip().upper()
        )
        valid_reversibility = {"REVERSIBLE", "IRREVERSIBLE", "SEALED_GATE", "READ_ONLY"}
        is_invalid_reversibility = rev_raw not in valid_reversibility

        # 3. Blast radius & authentication check
        blast = str(blast_radius or p.get("blast_radius", "low")).lower().strip()
        is_critical = blast == "critical"
        auth_verified = bool(
            actor_cryptographically_verified
            or p.get("actor_cryptographically_verified")
        )

        # Rule: blast_radius=critical without cryptographic actor verification requires 888_HOLD
        requires_888 = is_critical and not auth_verified

        errors = []
        warnings = []
        if is_unbounded:
            errors.append(
                f"INADMISSIBLE_INTENT: Intent '{intent_clean}' is unbounded/vague. Provide bounded, specific intent."
            )
        if is_invalid_reversibility:
            errors.append(
                f"INVALID_REVERSIBILITY: '{reversibility}' is not a valid reversibility level. Must be one of {sorted(list(valid_reversibility))}."
            )
        if requires_888:
            warnings.append(
                "888_HOLD_REQUIRED: Critical blast radius requires 888_HOLD or cryptographic actor verification."
            )

        if m == "submit" and (errors or requires_888):
            # Submission forbidden if validation errors exist or 888_HOLD required
            result = {
                "status": "REJECTED_BY_GOVERNANCE",
                "mode": "submit",
                "submitted": False,
                "hold_reason": "888_HOLD_REQUIRED"
                if requires_888
                else "VALIDATION_FAILED",
                "action": "PREPARE_ONLY",
                "validation_errors": errors,
                "warnings": warnings,
            }
            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="meta",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.SPECULATED,
                claim_state=ClaimState.VOID if errors else ClaimState.DRAFT,
                execution_authorized=False,
                requires_888_hold=True,
                errors=errors,
                warnings=warnings,
                session_id=session_id,
                actor_id=actor_id,
            )

        status = "PREPARED" if m == "prepare" else "SUBMITTED"
        result = {
            "status": status,
            "mode": m,
            "submitted": (status == "SUBMITTED"),
            "intent": intent_clean,
            "reversibility": rev_raw if not is_invalid_reversibility else "UNKNOWN",
            "blast_radius": blast,
            "actor_id": actor_id or "unverified",
            "actor_cryptographically_verified": auth_verified,
            "requires_888_hold": requires_888,
            "validation_errors": errors,
            "warnings": warnings,
        }
        return wrap_result(
            tool_name="wealth_judge_handoff",
            domain="meta",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED
            if not errors
            else EpistemicTag.SPECULATED,
            evidence_quality=EvidenceQuality.MODERATE
            if not errors
            else EvidenceQuality.WEAK,
            claim_state=ClaimState.DRAFT if m == "prepare" else ClaimState.QC_VERIFIED,
            execution_authorized=(status == "SUBMITTED" and not requires_888),
            requires_888_hold=requires_888,
            errors=errors,
            warnings=warnings,
            session_id=session_id,
            actor_id=actor_id,
        )

    # ═══════════════════════════════════════════════════════════════════
    # 9. capital_indicator — Technical analysis indicators (FORGED 2026-08-09)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_indicator",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Compute technical analysis indicators for any yfinance symbol. "
            "Indicators: ema, sma, rsi, macd, bb (Bollinger Bands), psar (Parabolic SAR), "
            "atr, adx. Pure numpy computation — no external TA library needed. "
            "SIDE EFFECT: writes a vault receipt."
        ),
        tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_indicator(
        symbol: str = "GC=F",
        indicator: str = "rsi",
        period: int = 14,
        interval: str = "1d",
        lookback: str = "6mo",
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        import numpy as np
        import yfinance as yf

        sym = symbol.upper()
        ind = indicator.lower().strip()

        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=lookback, interval=interval)
        except Exception as e:
            return wrap_result(
                tool_name="capital_indicator",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "FETCH_FAILED",
                    "message": str(e)[:200],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )
        if hist.empty:
            return wrap_result(
                tool_name="capital_indicator",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "NO_DATA",
                    "message": f"No price data for {sym}",
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

        close = hist["Close"].values.astype(np.float64)
        high = hist["High"].values.astype(np.float64) if "High" in hist else close
        low = hist["Low"].values.astype(np.float64) if "Low" in hist else close
        n = len(close)
        p = int(period)

        result: dict = {
            "symbol": sym,
            "indicator": indicator.upper(),
            "period": p,
            "interval": interval,
            "data_points": n,
        }

        # ── EMA ──
        if ind == "ema":
            alpha = 2.0 / (p + 1)
            ema_vals = np.zeros(n)
            ema_vals[0] = float(close[0])
            for i in range(1, n):
                ema_vals[i] = alpha * close[i] + (1 - alpha) * ema_vals[i - 1]
            result["current"] = round(float(ema_vals[-1]), 4)
            result["current_price"] = round(float(close[-1]), 4)
            result["series_last_5"] = [round(float(v), 4) for v in ema_vals[-5:]]

        # ── SMA ──
        elif ind == "sma":
            sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
            result["current"] = round(float(sma_vals[-1]), 4)
            result["current_price"] = round(float(close[-1]), 4)
            if len(sma_vals) >= 5:
                result["series_last_5"] = [round(float(v), 4) for v in sma_vals[-5:]]

        # ── RSI ──
        elif ind == "rsi":
            deltas = np.diff(close)
            gain = np.where(deltas > 0, deltas, 0.0)
            loss = np.where(deltas < 0, -deltas, 0.0)
            avg_gain = np.zeros(n)
            avg_loss = np.zeros(n)
            avg_gain[p] = np.mean(gain[:p])
            avg_loss[p] = np.mean(loss[:p])
            for i in range(p + 1, n):
                avg_gain[i] = (avg_gain[i - 1] * (p - 1) + gain[i - 1]) / p
                avg_loss[i] = (avg_loss[i - 1] * (p - 1) + loss[i - 1]) / p
            rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
            rsi_vals = 100.0 - (100.0 / (1.0 + rs))
            result["current"] = round(float(rsi_vals[-1]), 2)
            result["overbought"] = result["current"] > 70
            result["oversold"] = result["current"] < 30
            result["series_last_5"] = [round(float(v), 2) for v in rsi_vals[-5:]]

        # ── MACD ──
        elif ind == "macd":
            # EMA of close: fast=12, slow=26, signal=9 by default
            fast_p, slow_p, sig_p = 12, 26, 9
            if p != 14:  # user override via period param
                fast_p = p
                slow_p = p * 2
                sig_p = max(5, p // 2)

            def _ema(series, span):
                alpha = 2.0 / (span + 1)
                out = np.zeros(len(series))
                out[0] = float(series[0])
                for i in range(1, len(series)):
                    out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
                return out

            ema_fast = _ema(close, fast_p)
            ema_slow = _ema(close, slow_p)
            macd_line = ema_fast - ema_slow
            signal_line = _ema(macd_line, sig_p)
            histogram = macd_line - signal_line
            result["macd_line"] = round(float(macd_line[-1]), 6)
            result["signal_line"] = round(float(signal_line[-1]), 6)
            result["histogram"] = round(float(histogram[-1]), 6)
            result["bullish"] = bool(macd_line[-1] > signal_line[-1])

        # ── Bollinger Bands ──
        elif ind in ("bb", "bollinger"):
            sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
            rolling_std = np.array(
                [np.std(close[i : i + p], ddof=0) for i in range(n - p + 1)]
            )
            upper = sma_vals + 2 * rolling_std
            lower = sma_vals - 2 * rolling_std
            result["sma"] = round(float(sma_vals[-1]), 4)
            result["upper"] = round(float(upper[-1]), 4)
            result["lower"] = round(float(lower[-1]), 4)
            result["current_price"] = round(float(close[-1]), 4)
            result["bandwidth_pct"] = round(
                float((upper[-1] - lower[-1]) / sma_vals[-1] * 100), 2
            )
            result["price_position_pct"] = round(
                float((close[-1] - lower[-1]) / (upper[-1] - lower[-1]) * 100), 1
            )

        # ── Parabolic SAR ──
        elif ind in ("psar", "parabolic_sar", "sar"):
            af_init = 0.02
            af_max = 0.20
            af_step = 0.02
            psar = np.zeros(n)
            # Start: first bar determines trend
            trend_up = True
            ep = float(high[0])  # extreme point
            af = af_init
            psar[0] = float(low[0])
            for i in range(1, n):
                psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
                if trend_up:
                    psar[i] = min(psar[i], float(low[i - 1]), float(low[max(0, i - 2)]))
                    if float(high[i]) > ep:
                        ep = float(high[i])
                        af = min(af + af_step, af_max)
                    if float(low[i]) < psar[i]:
                        trend_up = False
                        psar[i] = ep
                        ep = float(low[i])
                        af = af_init
                else:
                    psar[i] = max(
                        psar[i], float(high[i - 1]), float(high[max(0, i - 2)])
                    )
                    if float(low[i]) < ep:
                        ep = float(low[i])
                        af = min(af + af_step, af_max)
                    if float(high[i]) > psar[i]:
                        trend_up = True
                        psar[i] = ep
                        ep = float(high[i])
                        af = af_init
            result["current"] = round(float(psar[-1]), 4)
            result["current_price"] = round(float(close[-1]), 4)
            result["trend"] = "BULL" if close[-1] > psar[-1] else "BEAR"
            result["psar_below_price"] = bool(close[-1] > psar[-1])

        # ── ATR ──
        elif ind == "atr":
            tr = np.zeros(n)
            for i in range(1, n):
                tr[i] = max(
                    float(high[i]) - float(low[i]),
                    abs(float(high[i]) - float(close[i - 1])),
                    abs(float(low[i]) - float(close[i - 1])),
                )
            atr_vals = np.zeros(n)
            atr_vals[p] = np.mean(tr[1 : p + 1])
            for i in range(p + 1, n):
                atr_vals[i] = (atr_vals[i - 1] * (p - 1) + tr[i]) / p
            result["current"] = round(float(atr_vals[-1]), 4)
            result["current_price"] = round(float(close[-1]), 4)
            result["atr_pct"] = round(float(atr_vals[-1] / close[-1] * 100), 2)

        # ── ADX ──
        elif ind == "adx":
            tr = np.zeros(n)
            plus_dm = np.zeros(n)
            minus_dm = np.zeros(n)
            for i in range(1, n):
                h_diff = float(high[i]) - float(high[i - 1])
                l_diff = float(low[i - 1]) - float(low[i])
                plus_dm[i] = h_diff if h_diff > l_diff and h_diff > 0 else 0.0
                minus_dm[i] = l_diff if l_diff > h_diff and l_diff > 0 else 0.0
                tr[i] = max(
                    float(high[i]) - float(low[i]),
                    abs(float(high[i]) - float(close[i - 1])),
                    abs(float(low[i]) - float(close[i - 1])),
                )
            atr_smooth = np.zeros(n)
            atr_smooth[p] = np.mean(tr[1 : p + 1])
            plus_di_smooth = np.zeros(n)
            plus_di_smooth[p] = (
                100 * np.mean(plus_dm[1 : p + 1]) / max(atr_smooth[p], 1e-10)
            )
            minus_di_smooth = np.zeros(n)
            minus_di_smooth[p] = (
                100 * np.mean(minus_dm[1 : p + 1]) / max(atr_smooth[p], 1e-10)
            )
            for i in range(p + 1, n):
                atr_smooth[i] = (atr_smooth[i - 1] * (p - 1) + tr[i]) / p
                plus_di_smooth[i] = (
                    plus_di_smooth[i - 1] * (p - 1)
                    + 100 * plus_dm[i] / max(atr_smooth[i], 1e-10)
                ) / p
                minus_di_smooth[i] = (
                    minus_di_smooth[i - 1] * (p - 1)
                    + 100 * minus_dm[i] / max(atr_smooth[i], 1e-10)
                ) / p
            dx = (
                100
                * np.abs(plus_di_smooth - minus_di_smooth)
                / np.maximum(plus_di_smooth + minus_di_smooth, 1e-10)
            )
            adx_vals = np.zeros(n)
            adx_vals[2 * p] = np.mean(dx[p : 2 * p])
            for i in range(2 * p + 1, n):
                adx_vals[i] = (adx_vals[i - 1] * (p - 1) + dx[i]) / p
            result["current"] = round(float(adx_vals[-1]), 2)
            result["plus_di"] = round(float(plus_di_smooth[-1]), 2)
            result["minus_di"] = round(float(minus_di_smooth[-1]), 2)
            result["trending"] = bool(adx_vals[-1] > 25)

        # ── TRAJECTORY / TEMPORAL — multi-indicator state snapshot ──
        elif ind in ("trajectory", "temporal", "state", "full"):
            # Compute all key indicators for temporal awareness
            out: dict = {
                "symbol": sym,
                "mode": "temporal",
                "interval": interval,
                "data_points": n,
                "current_price": round(float(close[-1]), 2),
            }

            # --- RSI ---
            deltas = np.diff(close)
            gain = np.where(deltas > 0, deltas, 0.0)
            loss = np.where(deltas < 0, -deltas, 0.0)
            avg_g = np.zeros(n)
            avg_l = np.zeros(n)
            avg_g[p] = np.mean(gain[:p])
            avg_l[p] = np.mean(loss[:p])
            for i in range(p + 1, n):
                avg_g[i] = (avg_g[i - 1] * (p - 1) + gain[i - 1]) / p
                avg_l[i] = (avg_l[i - 1] * (p - 1) + loss[i - 1]) / p
            rs_vals = avg_g / np.where(avg_l == 0, 1e-10, avg_l)
            rsi_all = 100.0 - (100.0 / (1.0 + rs_vals))
            out["rsi"] = {
                "current": round(float(rsi_all[-1]), 1),
                "signal": "overbought"
                if rsi_all[-1] > 70
                else ("oversold" if rsi_all[-1] < 30 else "neutral"),
                "trend_5": "rising" if rsi_all[-1] > rsi_all[-6] else "falling",
                "roc_5": round(float(rsi_all[-1] - rsi_all[-6]), 1),
            }

            # --- MACD ---
            def _e(series, span):
                a = 2.0 / (span + 1)
                o = np.zeros(len(series))
                o[0] = float(series[0])
                for i in range(1, len(series)):
                    o[i] = a * series[i] + (1 - a) * o[i - 1]
                return o

            macd_line = _e(close, 12) - _e(close, 26)
            signal_l = _e(macd_line, 9)
            hist = macd_line - signal_l
            out["macd"] = {
                "line": round(float(macd_line[-1]), 4),
                "signal": round(float(signal_l[-1]), 4),
                "histogram": round(float(hist[-1]), 4),
                "bullish": bool(macd_line[-1] > signal_l[-1]),
                "cross_5": "bullish_cross"
                if macd_line[-1] > signal_l[-1] and macd_line[-6] <= signal_l[-6]
                else (
                    "bearish_cross"
                    if macd_line[-1] < signal_l[-1] and macd_line[-6] >= signal_l[-6]
                    else "none"
                ),
            }

            # --- Bollinger Bands ---
            sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
            rstd = np.array(
                [np.std(close[i : i + p], ddof=0) for i in range(n - p + 1)]
            )
            bb_upper = sma_vals + 2 * rstd
            bb_lower = sma_vals - 2 * rstd
            bb_pos = (close[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]) * 100
            bb_width = (bb_upper[-1] - bb_lower[-1]) / sma_vals[-1] * 100
            out["bollinger"] = {
                "position_pct": round(float(bb_pos), 0),
                "bandwidth": round(float(bb_width), 1),
                "signal": "breakout_above"
                if bb_pos > 100
                else ("breakout_below" if bb_pos < 0 else "inside"),
                "squeeze": bool(bb_width < 5),
            }

            # --- EMA alignment (regime) ---
            e20 = _e(close, 20)
            e50 = _e(close, 50)
            e200_long = _e(
                np.concatenate([np.full(max(0, 200 - n), close[0]), close]), 200
            )
            if len(e200_long) > n:
                e200_long = e200_long[-n:]
            trend = "SIDEWAYS"
            if e20[-1] > e50[-1] > e200_long[-1]:
                trend = "UPTREND"
            elif e20[-1] < e50[-1] < e200_long[-1]:
                trend = "DOWNTREND"
            out["regime"] = {
                "trend": trend,
                "ema20": round(float(e20[-1]), 2),
                "ema50": round(float(e50[-1]), 2),
                "ema200": round(float(e200_long[-1]), 2),
                "strength_pct": round(
                    float(abs(e20[-1] - e200_long[-1]) / e200_long[-1] * 100), 2
                ),
            }

            # --- PSAR ---
            af_i = 0.02
            af_m = 0.20
            af_s = 0.02
            psar = np.zeros(n)
            t_up = True
            ep_v = float(high[0])
            af_v = af_i
            psar[0] = float(low[0])
            for i in range(1, n):
                psar[i] = psar[i - 1] + af_v * (ep_v - psar[i - 1])
                if t_up:
                    psar[i] = min(psar[i], float(low[i - 1]), float(low[max(0, i - 2)]))
                    if float(high[i]) > ep_v:
                        ep_v = float(high[i])
                        af_v = min(af_v + af_s, af_m)
                    if float(low[i]) < psar[i]:
                        t_up = False
                        psar[i] = ep_v
                        ep_v = float(low[i])
                        af_v = af_i
                else:
                    psar[i] = max(
                        psar[i], float(high[i - 1]), float(high[max(0, i - 2)])
                    )
                    if float(low[i]) < ep_v:
                        ep_v = float(low[i])
                        af_v = min(af_v + af_s, af_m)
                    if float(high[i]) > psar[i]:
                        t_up = True
                        psar[i] = ep_v
                        ep_v = float(high[i])
                        af_v = af_i
            out["psar"] = {
                "value": round(float(psar[-1]), 2),
                "trend": "BULL" if close[-1] > psar[-1] else "BEAR",
                "distance_pct": round(
                    float(abs(close[-1] - psar[-1]) / close[-1] * 100), 2
                ),
            }

            # --- ATR ---
            tr_arr = np.zeros(n)
            for i in range(1, n):
                tr_arr[i] = max(
                    high[i] - low[i],
                    abs(high[i] - close[i - 1]),
                    abs(low[i] - close[i - 1]),
                )
            atr_s = np.zeros(n)
            atr_s[p] = np.mean(tr_arr[1 : p + 1])
            for i in range(p + 1, n):
                atr_s[i] = (atr_s[i - 1] * (p - 1) + tr_arr[i]) / p
            atr_now = float(atr_s[-1])
            atr_5_ago = float(atr_s[max(0, n - 6)])
            out["atr"] = {
                "current": round(atr_now, 2),
                "pct_of_price": round(atr_now / close[-1] * 100, 2),
                "expanding": bool(atr_now > atr_5_ago * 1.1),
                "contracting": bool(atr_now < atr_5_ago * 0.9),
            }

            # --- ADX ---
            px_dm = np.zeros(n)
            nx_dm = np.zeros(n)
            for i in range(1, n):
                hd = float(high[i]) - float(high[i - 1])
                ld = float(low[i - 1]) - float(low[i])
                px_dm[i] = hd if hd > ld and hd > 0 else 0.0
                nx_dm[i] = ld if ld > hd and ld > 0 else 0.0
            atr_adx = np.zeros(n)
            atr_adx[p] = np.mean(tr_arr[1 : p + 1])
            pdi = np.zeros(n)
            pdi[p] = 100 * np.mean(px_dm[1 : p + 1]) / max(atr_adx[p], 1e-10)
            ndi = np.zeros(n)
            ndi[p] = 100 * np.mean(nx_dm[1 : p + 1]) / max(atr_adx[p], 1e-10)
            for i in range(p + 1, n):
                atr_adx[i] = (atr_adx[i - 1] * (p - 1) + tr_arr[i]) / p
                pdi[i] = (
                    pdi[i - 1] * (p - 1) + 100 * px_dm[i] / max(atr_adx[i], 1e-10)
                ) / p
                ndi[i] = (
                    ndi[i - 1] * (p - 1) + 100 * nx_dm[i] / max(atr_adx[i], 1e-10)
                ) / p
            dx_v = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-10)
            adx_all = np.zeros(n)
            adx_all[2 * p] = np.mean(dx_v[p : 2 * p])
            for i in range(2 * p + 1, n):
                adx_all[i] = (adx_all[i - 1] * (p - 1) + dx_v[i]) / p
            out["adx"] = {
                "current": round(float(adx_all[-1]), 1),
                "plus_di": round(float(pdi[-1]), 1),
                "minus_di": round(float(ndi[-1]), 1),
                "trending": bool(adx_all[-1] > 25),
                "strong_trend": bool(adx_all[-1] > 40),
            }

            # --- Signal summary ---
            signals = []
            if out["regime"]["trend"] == "UPTREND" and out["adx"]["trending"]:
                signals.append("BULL_TREND")
            elif out["regime"]["trend"] == "DOWNTREND" and out["adx"]["trending"]:
                signals.append("BEAR_TREND")
            if out["rsi"]["signal"] == "overbought":
                signals.append("RSI_OVERBOUGHT")
            elif out["rsi"]["signal"] == "oversold":
                signals.append("RSI_OVERSOLD")
            if out["bollinger"]["signal"] == "breakout_above":
                signals.append("BB_BREAKOUT_UP")
            elif out["bollinger"]["signal"] == "breakout_below":
                signals.append("BB_BREAKOUT_DOWN")
            if out["bollinger"]["squeeze"]:
                signals.append("BB_SQUEEZE")
            if out["macd"]["bullish"]:
                signals.append("MACD_BULLISH")
            else:
                signals.append("MACD_BEARISH")
            if out["psar"]["trend"] == "BULL":
                signals.append("PSAR_BULL")
            else:
                signals.append("PSAR_BEAR")
            if out["atr"]["expanding"]:
                signals.append("VOL_EXPANDING")
            elif out["atr"]["contracting"]:
                signals.append("VOL_CONTRACTING")

            # Confluence score: count how many agree with trend direction
            bull_align = sum(
                1
                for s in signals
                if "BULL" in s
                or s in ("RSI_OVERSOLD", "BB_BREAKOUT_UP", "MACD_BULLISH", "PSAR_BULL")
            )
            bear_align = sum(
                1
                for s in signals
                if "BEAR" in s
                or s
                in ("RSI_OVERBOUGHT", "BB_BREAKOUT_DOWN", "MACD_BEARISH", "PSAR_BEAR")
            )
            total = max(len(signals), 1)
            out["confluence"] = {
                "bull_signals": bull_align,
                "bear_signals": bear_align,
                "total": total,
                "bull_pct": round(bull_align / total * 100),
                "verdict": "STRONG_BULL"
                if bull_align >= total * 0.7
                else (
                    "STRONG_BEAR"
                    if bear_align >= total * 0.7
                    else (
                        "BULL_LEAN"
                        if bull_align > bear_align
                        else ("BEAR_LEAN" if bear_align > bull_align else "MIXED")
                    )
                ),
            }
            out["signals"] = signals

            result = out

        else:
            valid = "ema, sma, rsi, macd, bb, psar, atr, adx"
            return wrap_result(
                tool_name="capital_indicator",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_INDICATOR",
                    "message": f"Unknown '{indicator}'. Valid: {valid}",
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

        return wrap_result(
            tool_name="capital_indicator",
            domain="market",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.OBSERVED,
            source_attribution=[f"yfinance:{sym}"],
            session_id=session_id,
            actor_id=actor_id,
        )

    # ═══════════════════════════════════════════════════════════════════
    # 10. capital_backtest — Strategy backtest runner (FORGED 2026-08-09)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_backtest",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Run strategy backtest on XAUUSD using the proven indicator fusion "
            "(EMA alignment + ATR-scaled stops + RSI pullback filter + S/R zones). "
            "Wraps the v2 backtest engine. Returns win rate, profit factor, Sharpe, "
            "max drawdown, and trade log. SIDE EFFECT: writes a vault receipt."
        ),
        tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_backtest(
        symbol: str = "GC=F",
        interval: str = "1h",
        lookback: str = "2y",
        initial_capital: float = 10000.0,
        risk_per_trade_pct: float = 1.0,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        import sys, os, json as _json, datetime as _dt

        # Add trading path for imports
        _trading_path = "/root/WEALTH/trading"
        if _trading_path not in sys.path:
            sys.path.insert(0, _trading_path)

        try:
            import yfinance as yf

            sym = symbol.upper()
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=lookback, interval=interval)
            if hist.empty:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="market",
                    result={
                        "status": "ERROR",
                        "error_code": "NO_DATA",
                        "message": f"No data for {sym} at {interval}",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            # Convert to OHLCV list for the backtest engine
            from signals.scanner import OHLCV as _OHLCV

            candles = []
            for idx, row in hist.iterrows():
                candles.append(
                    _OHLCV(
                        timestamp=idx,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row.get("Volume", 0)),
                    )
                )

            # Configure and run backtest
            from backtest.engine_v2 import BacktestConfig, run_backtest

            cfg = BacktestConfig()
            cfg.initial_equity = float(initial_capital)
            cfg.risk_per_trade = float(risk_per_trade_pct) / 100.0
            cfg.symbol = sym

            bt_result = run_backtest(candles, cfg)

            # Extract key metrics
            metrics = bt_result.get("metrics", {})
            trades = bt_result.get("trades", [])

            summary = {
                "symbol": sym,
                "interval": interval,
                "lookback": lookback,
                "data_points": len(candles),
                "date_range": {
                    "from": str(candles[0].timestamp)[:19] if candles else None,
                    "to": str(candles[-1].timestamp)[:19] if candles else None,
                },
                "initial_capital": float(initial_capital),
                "final_equity": round(float(metrics.get("final_equity", 0)), 2),
                "total_return_pct": round(float(metrics.get("total_return_pct", 0)), 2),
                "total_trades": int(metrics.get("total_trades", 0)),
                "win_rate_pct": round(float(metrics.get("win_rate_pct", 0)), 1),
                "profit_factor": round(float(metrics.get("profit_factor", 0)), 2),
                "sharpe_ratio": round(float(metrics.get("sharpe_ratio", 0)), 2),
                "max_drawdown_pct": round(float(metrics.get("max_drawdown_pct", 0)), 2),
                "avg_win": round(float(metrics.get("avg_win", 0)), 2),
                "avg_loss": round(float(metrics.get("avg_loss", 0)), 2),
                "last_5_trades": [
                    {
                        "entry": t.get("entry_price"),
                        "exit": t.get("exit_price"),
                        "direction": t.get("direction"),
                        "pnl": t.get("pnl"),
                        "exit_reason": t.get("exit_reason", ""),
                    }
                    for t in trades[-5:]
                ],
            }

            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result=summary,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.OBSERVED,
                source_attribution=[f"yfinance:{sym}", "engine_v2"],
                session_id=session_id,
                actor_id=actor_id,
            )

        except ImportError as e:
            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "IMPORT_FAILED",
                    "message": f"Trading engine import failed: {e}",
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )
        except Exception as e:
            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "BACKTEST_FAILED",
                    "message": str(e)[:300],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

    # ═══════════════════════════════════════════════════════════════════
    # 11. capital_entry_plan — S/R-aware entry/stop/target (FORGED 2026-08-09)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_entry_plan",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Compute S/R-aware entry zone, stop loss, and take profit targets "
            "for XAUUSD. Combines swing-point support/resistance clustering with "
            "ATR-based risk scaling. Returns structured trade plan: entry_zone, "
            "stop_loss, target_1, target_2, risk_reward_ratio. "
            "SIDE EFFECT: writes a vault receipt."
        ),
        tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_entry_plan(
        symbol: str = "GC=F",
        interval: str = "1h",
        lookback: str = "3mo",
        trend_bias: str = "auto",
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        import numpy as np
        import yfinance as yf

        sym = symbol.upper()
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=lookback, interval=interval)
        except Exception as e:
            return wrap_result(
                tool_name="capital_entry_plan",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "FETCH_FAILED",
                    "message": str(e)[:200],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )
        if hist.empty:
            return wrap_result(
                tool_name="capital_entry_plan",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "NO_DATA",
                    "message": f"No data for {sym}",
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

        high = hist["High"].values.astype(np.float64)
        low = hist["Low"].values.astype(np.float64)
        close = hist["Close"].values.astype(np.float64)
        n = len(close)

        # ── Compute ATR(14) ──
        p = 14
        tr = np.zeros(n)
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        atr_vals = np.zeros(n)
        atr_vals[p] = np.mean(tr[1 : p + 1])
        for i in range(p + 1, n):
            atr_vals[i] = (atr_vals[i - 1] * (p - 1) + tr[i]) / p
        current_atr = float(atr_vals[-1])
        current_price = float(close[-1])

        # ── Compute EMA alignment for trend detection ──
        def _ema(series, span):
            alpha = 2.0 / (span + 1)
            out = np.zeros(len(series))
            out[0] = float(series[0])
            for i in range(1, len(series)):
                out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
            return out

        ema20 = _ema(close, 20)
        ema50 = _ema(close, 50)
        ema200 = _ema(
            np.concatenate([np.full(200 - n, close[0]), close]) if n < 200 else close,
            200,
        )
        if len(ema200) > n:
            ema200 = ema200[-n:]

        trend = "SIDEWAYS"
        if ema20[-1] > ema50[-1] > ema200[-1]:
            trend = "UPTREND"
        elif ema20[-1] < ema50[-1] < ema200[-1]:
            trend = "DOWNTREND"
        if trend_bias.lower() == "long" and trend == "DOWNTREND":
            trend = "SIDEWAYS"  # Don't fight trend
        elif trend_bias.lower() == "short" and trend == "UPTREND":
            trend = "SIDEWAYS"

        # ── Find swing S/R zones (local maxima/minima clustering) ──
        lookback_swing = 20
        swing_highs = []
        swing_lows = []
        for i in range(lookback_swing, n - lookback_swing):
            if all(
                high[i] >= high[i - j] for j in range(1, lookback_swing + 1)
            ) and all(high[i] >= high[i + j] for j in range(1, lookback_swing + 1)):
                swing_highs.append(float(high[i]))
            if all(low[i] <= low[i - j] for j in range(1, lookback_swing + 1)) and all(
                low[i] <= low[i + j] for j in range(1, lookback_swing + 1)
            ):
                swing_lows.append(float(low[i]))

        # Cluster nearby levels
        def _cluster(levels, tolerance_pct=0.5):
            if not levels:
                return []
            levels = sorted(set(levels))
            clusters = []
            current = [levels[0]]
            for lvl in levels[1:]:
                if (
                    abs(lvl - current[-1]) / max(current[-1], 1e-10) * 100
                    < tolerance_pct
                ):
                    current.append(lvl)
                else:
                    clusters.append((sum(current) / len(current), len(current)))
                    current = [lvl]
            clusters.append((sum(current) / len(current), len(current)))
            return [
                (round(price, 2), strength)
                for price, strength in clusters
                if strength >= 2
            ]

        resistance_zones = _cluster(swing_highs)
        support_zones = _cluster(swing_lows)

        # ── Build trade plan ──
        nearest_support = support_zones[0][0] if support_zones else current_price * 0.98
        nearest_resistance = (
            resistance_zones[0][0] if resistance_zones else current_price * 1.02
        )
        next_resistance = (
            resistance_zones[1][0]
            if len(resistance_zones) > 1
            else current_price * 1.04
        )

        if trend == "UPTREND":
            entry_zone = round(nearest_support, 2)
            stop_loss = round(nearest_support - 2 * current_atr, 2)
            target_1 = round(nearest_resistance, 2)
            target_2 = round(next_resistance, 2)
            direction = "LONG"
        elif trend == "DOWNTREND":
            entry_zone = round(nearest_resistance, 2)
            stop_loss = round(nearest_resistance + 2 * current_atr, 2)
            target_1 = round(nearest_support, 2)
            target_2 = round(
                support_zones[1][0] if len(support_zones) > 1 else current_price * 0.97,
                2,
            )
            direction = "SHORT"
        else:
            entry_zone = round(current_price, 2)
            stop_loss = round(current_price - 2 * current_atr, 2)
            target_1 = round(current_price + 2 * current_atr, 2)
            target_2 = round(current_price + 3 * current_atr, 2)
            direction = "NEUTRAL"

        risk = abs(entry_zone - stop_loss)
        reward_1 = abs(target_1 - entry_zone)
        reward_2 = abs(target_2 - entry_zone)
        rr_1 = round(reward_1 / risk, 2) if risk > 0 else 0.0
        rr_2 = round(reward_2 / risk, 2) if risk > 0 else 0.0

        return wrap_result(
            tool_name="capital_entry_plan",
            domain="market",
            result={
                "symbol": sym,
                "interval": interval,
                "current_price": round(current_price, 2),
                "trend": trend,
                "atr": round(current_atr, 2),
                "atr_pct": round(current_atr / current_price * 100, 2),
                "direction": direction,
                "entry_zone": entry_zone,
                "stop_loss": stop_loss,
                "target_1": target_1,
                "target_2": target_2,
                "risk": round(risk, 2),
                "risk_reward_1": rr_1,
                "risk_reward_2": rr_2,
                "support_zones": support_zones[:3],
                "resistance_zones": resistance_zones[:3],
            },
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.OBSERVED,
            source_attribution=[f"yfinance:{sym}"],
            session_id=session_id,
            actor_id=actor_id,
        )

    return {
        "capital_primitive": capital_primitive,
        "capital_health": capital_health,
        "capital_diagnose": capital_diagnose,
        "capital_market": capital_market,
        "capital_ledger": capital_ledger,
        "capital_registry": capital_registry,
        "capital_entropy": capital_entropy,
        "wealth_judge_handoff": wealth_judge_handoff,
        "capital_indicator": capital_indicator,
        "capital_backtest": capital_backtest,
        "capital_entry_plan": capital_entry_plan,
        # Zen Phase 2: capital_wisdom DELETED 2026-08-06 — normative synthesis
        # violates 'WEALTH computes, arifOS frames'. M0 audit confirmed.
        # F13 directive: DELETE, not REGISTER. arifOS owns framing.
    }
