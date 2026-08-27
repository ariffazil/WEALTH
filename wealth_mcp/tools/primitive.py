"""
WEALTH capital_primitive — Deductive math primitives — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
import json
from typing import Annotated, Any

from pydantic import BeforeValidator
from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import (
    CoercedList, CoercedDict, CoercedDictList, _coerce_json_string,
)



def register_primitive(mcp):
    """Register the primitive tool on the given FastMCP instance."""
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

    # ═══ REWARD DESIGN — TradeMaster distillation (2026-08-18) ═══
    if m == "reward_design":
        import sys as _sys

        _wealth_root = "/root/WEALTH"
        if _wealth_root not in _sys.path:
            _sys.path.insert(0, _wealth_root)

        from wealth_core.reward_design import compute_reward_design

        task_type = "portfolio"
        returns_list = list(returns) if returns else None
        risk_av = float(risk_aversion) if risk_aversion else 1.0
        max_dd_tolerance = 0.15

        result = compute_reward_design(
            task_type, returns_list, risk_av, max_dd_tolerance
        )
        return wrap_result(
            tool_name="capital_primitive",
            domain="risk",
            result={
                "recommended_reward": {
                    "name": result.recommended_reward.name,
                    "task_type": result.recommended_reward.task_type,
                    "formula": result.recommended_reward.formula,
                    "parameters": result.recommended_reward.parameters,
                    "description": result.recommended_reward.description,
                },
                "all_rewards": result.all_rewards,
                "task_type": result.task_type,
                "justification": result.justification,
                "framework": "Multi-Task Reward Design (TradeMaster distillation)",
            },
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["reward_design_engine", "trademaster_distillation"],
            session_id=session_id,
            actor_id=actor_id,
        )

    return wrap_result(
        tool_name="capital_primitive",
        domain="capital",
        result={
            "error": f"Unknown mode '{mode}'.",
            "valid_modes": [
                "npv", "irr", "emv", "evoi", "mc", "kelly",
                "markowitz", "robust", "chance_constrained",
                "two_stage", "reward_design",
            ],
        },
        epistemic_tag=EpistemicTag.DERIVED,
        evidence_quality=EvidenceQuality.WEAK,
        source_attribution=["capital_primitive:error"],
        session_id=session_id,
        actor_id=actor_id,
    )

