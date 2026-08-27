"""
WEALTH capital_health — Financial health metrics — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Annotated, Any

from pydantic import BeforeValidator
from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import (
    CoercedList, CoercedDictList, _coerce_json_string, _call_legacy_tool,
)


def register_health(mcp):
    """Register the health tool on the given FastMCP instance."""
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

        # ═══ ASYMMETRIC RISK — TradeMaster DeepScalper distillation (2026-08-18) ═══
        if m == "asymmetric_risk":
            import sys as _sys

            _wealth_root = "/root/WEALTH"
            if _wealth_root not in _sys.path:
                _sys.path.insert(0, _wealth_root)

            from wealth_core.asymmetric_risk import compute_asymmetric_risk

            # Accept trade_returns and equity_curve in the standard params
            # Use upside_scenarios as trade_returns, downside_scenarios as equity_curve
            trade_rets = list(upside_scenarios or [])
            equity_curve = list(downside_scenarios or [])
            loss_aversion = float(conservative_factor) if conservative_factor else 2.5
            base_risk = (
                float(oil_price_assumption_usd) if oil_price_assumption_usd else 1.0
            )

            if not trade_rets or not equity_curve:
                return wrap_result(
                    tool_name="capital_health",
                    domain="risk",
                    result={
                        "status": "ERROR",
                        "error_code": "MISSING_DATA",
                        "message": "asymmetric_risk requires upside_scenarios (trade_returns) and downside_scenarios (equity_curve)",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            result = compute_asymmetric_risk(
                trade_rets, equity_curve, loss_aversion, base_risk
            )
            return wrap_result(
                tool_name="capital_health",
                domain="risk",
                result={
                    "standard_kelly": result.standard_kelly,
                    "asymmetric_kelly": result.asymmetric_kelly,
                    "loss_aversion_coefficient": result.loss_aversion_coefficient,
                    "omega_ratio": result.omega_ratio,
                    "pain_to_gain_ratio": result.pain_to_gain_ratio,
                    "recommended_risk_pct": result.recommended_risk_pct,
                    "position_scaling": result.position_scaling,
                    "drawdown_state": result.drawdown_state,
                    "metrics": result.metrics,
                    "recommendations": result.recommendations,
                    "framework": "DeepScalper Asymmetric Risk (TradeMaster distillation)",
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "asymmetric_risk_engine",
                    "trademaster_distillation",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        raise ValueError(
            f"Unknown mode '{mode}'. Valid: conservation, flow, runway, survival, fiscal_breakeven, confluence, asymmetry, asymmetric_risk"
        )
