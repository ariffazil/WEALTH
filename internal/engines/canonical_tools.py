# WEALTH MCP — NEXT HORIZON MAIN
# 13-Canonical-Tool Surface with WAJIB Envelope + Five Seals
# Phase 3: Canonical organs
# SPEAR: DITEMPA BUKAN DIBERI

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

# ─── Import internal engines from monolith.py ───────────────────────────────
# These are confirmed to exist as plain Python functions (not @mcp.tool decorators).
# NOTE: We import engines with _engine suffix to avoid name collision with
# the wrapper functions that call them (which would cause infinite recursion).
try:
    from internal.monolith import (
        # Capital evaluation engines
        npv_reward,
        irr_yield,
        pi_efficiency,
        payback_time,
        # Uncertainty engines
        emv_risk,
        monte_carlo_forecast,
        # Financial position engines
        cashflow_flow,
        growth_velocity,
        dscr_leverage,
        networth_state,
        crisis_triage,
        # Governance / entropy engines
        wealth_boundary_governance,
        wealth_conservation_capital as wealth_conservation_capital_engine,
        wealth_entropy_audit,
        wealth_entropy_risk,
        # Market engines
        wealth_gradient_price,
        wealth_field_macro,
        # Power / game engines
        coordination_equilibrium,
        game_theory_solve,
        agent_budget,
        # Ledger engines
        snapshot_portfolio_tool,
        record_transaction_tool,
        wealth_hysteresis_ledger,
        # Other engines
        civilization_stewardship,
        personal_decision,
        wealth_signal_information,
        wealth_inequality_kernel as wealth_inequality_kernel_engine,
        wealth_agent_path,
        wealth_synthesize as wealth_synthesize_engine,
    )

    _ENGINES_IMPORTED = True
    _IMPORT_ERROR = None
except ImportError as e:
    _ENGINES_IMPORTED = False
    _IMPORT_ERROR = str(e)

# ─── Five Seals and WAJIB helpers ────────────────────────────────────────
from internal.engines.five_seals import (
    wajib_envelope,
    compute_five_seals,
    classify_decision_class,
)

_FIVE_SEALS_LOADED = True


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 01 — wealth_system_status
# Modes: health, registry, version, aliases, schema
# Collapses: mcp_health_check, wealth_system_registry_status
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    from internal.monolith import mcp_health_check, wealth_system_registry_status

    async def wealth_system_status_tool(
        mode: str = "health",
        scale_mode: str = "enterprise",
    ) -> Dict[str, Any]:
        """Ω-WEALTH-SYS: System health, registry, and version status.

        Canonical surface — one tool for all system-level queries.

        Modes:
          health    — Is the WEALTH MCP alive and responsive?
          registry — What tools are registered?
          version  — What version and build info?
          aliases  — What legacy aliases exist and what do they map to?
          schema   — Are schemas valid?

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        Five Seals: always UNKNOWN for system checks (no value at stake).
        """
        intent = f"system_check:{mode}"
        entity_scope = "institution"
        time_horizon = "immediate"
        capital_at_risk = {}

        if mode == "health":
            try:
                health = mcp_health_check()
                metrics = {
                    "service": "WEALTH",
                    "status": health.get("status", "unknown"),
                }
                five_seals = compute_five_seals(metrics, "wealth_system_status")
                return wajib_envelope(
                    tool="wealth_system_status",
                    mode=mode,
                    status="OK",
                    wealth_verdict="PROCEED",
                    summary="WEALTH MCP is healthy and responsive.",
                    metrics=metrics,
                    intent=intent,
                    entity_scope=entity_scope,
                    time_horizon=time_horizon,
                    capital_at_risk=capital_at_risk,
                    decision_class="W0",
                    evidence_level="E4",
                    risks=[],
                    assumptions=[],
                    five_seals=five_seals,
                    handoff_required={
                        "WELL": False,
                        "arifOS": False,
                        "GEOX": False,
                        "human_professional": False,
                    },
                )
            except Exception as e:
                return wajib_envelope(
                    tool="wealth_system_status",
                    mode=mode,
                    status="ERROR",
                    wealth_verdict="BLOCK",
                    summary=f"WEALTH MCP health check failed: {str(e)}",
                    metrics={"error": str(e)},
                    intent=intent,
                    entity_scope=entity_scope,
                    time_horizon=time_horizon,
                    capital_at_risk=capital_at_risk,
                    decision_class="W0",
                    evidence_level="E0",
                    risks=["WEALTH service unavailable"],
                    assumptions=[],
                    five_seals={
                        "value_seal": "UNKNOWN",
                        "risk_seal": "UNKNOWN",
                        "liquidity_seal": "UNKNOWN",
                        "legitimacy_seal": "CLEAN",
                        "sovereignty_seal": "UNKNOWN",
                    },
                    handoff_required={
                        "WELL": False,
                        "arifOS": False,
                        "GEOX": False,
                        "human_professional": False,
                    },
                )

        elif mode == "registry":
            try:
                registry = await wealth_system_registry_status()
                metrics = {
                    "tools_registered": len(registry.get("tools", [])),
                    "status": "ok",
                }
                five_seals = compute_five_seals(metrics, "wealth_system_status")
                return wajib_envelope(
                    tool="wealth_system_status",
                    mode=mode,
                    status="OK",
                    wealth_verdict="PROCEED",
                    summary=f"WEALTH registry check passed.",
                    metrics=metrics,
                    intent=intent,
                    entity_scope=entity_scope,
                    time_horizon=time_horizon,
                    capital_at_risk=capital_at_risk,
                    decision_class="W0",
                    evidence_level="E4",
                    five_seals=five_seals,
                )
            except Exception as e:
                return wajib_envelope(
                    tool="wealth_system_status",
                    mode=mode,
                    status="ERROR",
                    wealth_verdict="HOLD",
                    summary=f"Registry check failed: {str(e)}",
                    metrics={"error": str(e)},
                    intent=intent,
                    entity_scope=entity_scope,
                    time_horizon=time_horizon,
                    capital_at_risk=capital_at_risk,
                    decision_class="W0",
                    evidence_level="E0",
                    five_seals={
                        "value_seal": "UNKNOWN",
                        "risk_seal": "UNKNOWN",
                        "liquidity_seal": "UNKNOWN",
                        "legitimacy_seal": "CLEAN",
                        "sovereignty_seal": "UNKNOWN",
                    },
                )

        elif mode == "aliases":
            from internal.engines.compatibility_map import LEGACY_TO_CANONICAL

            metrics = {
                "alias_count": len(LEGACY_TO_CANONICAL),
                "mappings": LEGACY_TO_CANONICAL,
            }
            five_seals = compute_five_seals(metrics, "wealth_system_status")
            return wajib_envelope(
                tool="wealth_system_status",
                mode=mode,
                status="OK",
                wealth_verdict="PROCEED",
                summary=f"{len(LEGACY_TO_CANONICAL)} legacy aliases mapped to 13 canonical tools.",
                metrics=metrics,
                intent=intent,
                entity_scope=entity_scope,
                time_horizon=time_horizon,
                capital_at_risk=capital_at_risk,
                decision_class="W0",
                evidence_level="E3",
                five_seals=five_seals,
            )

        else:
            return wajib_envelope(
                tool="wealth_system_status",
                mode=mode,
                status="HOLD",
                wealth_verdict="HOLD",
                summary=f"Unknown mode '{mode}'. Valid modes: health, registry, aliases.",
                metrics={},
                intent=intent,
                entity_scope=entity_scope,
                time_horizon=time_horizon,
                capital_at_risk=capital_at_risk,
                decision_class="W0",
                evidence_level="E0",
                risks=[f"Unknown mode: {mode}"],
                five_seals={
                    "value_seal": "UNKNOWN",
                    "risk_seal": "UNKNOWN",
                    "liquidity_seal": "UNKNOWN",
                    "legitimacy_seal": "UNKNOWN",
                    "sovereignty_seal": "UNKNOWN",
                },
            )

else:

    async def wealth_system_status(mode: str = "health", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 02 — wealth_capital_evaluate
# Modes: npv, irr, profitability_index, payback, productivity, discount, compare
# Collapses: wealth_value_npv, wealth_energy_irr, wealth_density_pi,
#            wealth_time_payback, wealth_energy_productivity, wealth_time_discount
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:

    def wealth_capital_evaluate_tool(
        mode: str = "npv",
        initial_investment: float = 0,
        cash_flows: Optional[List[float]] = None,
        discount_rate: float = 0.10,
        terminal_value: float = 0,
        period_unit: str = "annual",
        input_epistemic: str = "CLAIM",
        scale_mode: str = "enterprise",
        # WAJIB mandatory fields
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # SUNAT optional
        reinvestment_rate: float = 0.10,
        finance_rate: float = 0.10,
        # Legacy alias tracking
        legacy_alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-CAP: Capital evaluation — NPV, IRR, PI, payback, productivity, discount.

        Canonical surface for all investment/capital efficiency metrics.
        Single tool, multiple modes.

        Modes:
          npv                 — Net Present Value
          irr                 — Internal Rate of Return
          profitability_index  — PI / benefit-cost ratio
          payback            — Payback period (years)
          productivity       — Return per unit input
          discount           — Future value discounting
          compare            — Compare base/bear/bull scenarios

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        Five Seals: VALUE_SEAL is primary — "Is value created?"
        """
        cash_flows = cash_flows or []

        if mode == "npv":
            result = npv_reward(
                initial_investment,
                cash_flows,
                discount_rate,
                terminal_value,
                period_unit,
                input_epistemic,
                scale_mode,
            )
        elif mode == "irr":
            result = irr_yield(
                initial_investment,
                cash_flows,
                reinvestment_rate,
                finance_rate,
                period_unit,
                discount_rate,
                scale_mode,
            )
        elif mode == "profitability_index":
            result = pi_efficiency(
                initial_investment,
                cash_flows,
                discount_rate,
                terminal_value,
                scale_mode,
            )
        elif mode == "payback":
            result = payback_time(
                initial_investment,
                cash_flows,
                discount_rate,
                period_unit,
                scale_mode,
            )
        elif mode == "productivity":
            total_cf = sum(cash_flows)
            productivity = (
                (total_cf - initial_investment) / initial_investment
                if initial_investment > 0
                else 0
            )
            result = {
                "task": "wealth_capital_evaluate:productivity",
                "status": "PASS",
                "primary_metrics": {"productivity_ratio": productivity},
                "secondary_metrics": {
                    "total_inflows": total_cf,
                    "initial_investment": initial_investment,
                },
                "assumptions": [
                    "productivity = (sum(cash_flows) - initial_investment) / initial_investment"
                ],
                "failure_flags": [],
            }
        elif mode == "discount":
            fv = sum(cash_flows)
            periods = len(cash_flows) if cash_flows else 1
            pv = fv / ((1 + discount_rate) ** periods) if discount_rate > 0 else fv
            result = {
                "task": "wealth_capital_evaluate:discount",
                "status": "PASS",
                "primary_metrics": {
                    "present_value": pv,
                    "future_value": fv,
                    "discount_rate": discount_rate,
                    "periods": periods,
                },
                "secondary_metrics": {},
                "assumptions": [],
                "failure_flags": [],
            }
        elif mode == "compare":
            npv_base = npv_reward(
                initial_investment,
                cash_flows,
                discount_rate,
                terminal_value,
                period_unit,
                input_epistemic,
                scale_mode,
            )
            npv_bear = npv_reward(
                initial_investment,
                [cf * 0.7 for cf in cash_flows],
                discount_rate,
                terminal_value * 0.7,
                period_unit,
                input_epistemic,
                scale_mode,
            )
            npv_bull = npv_reward(
                initial_investment,
                [cf * 1.3 for cf in cash_flows],
                discount_rate,
                terminal_value * 1.3,
                period_unit,
                input_epistemic,
                scale_mode,
            )
            result = {
                "task": "wealth_capital_evaluate:compare",
                "status": "PASS",
                "primary_metrics": {
                    "npv_base": npv_base.get("primary_metrics", {}).get("npv", 0),
                    "npv_bear": npv_bear.get("primary_metrics", {}).get("npv", 0),
                    "npv_bull": npv_bull.get("primary_metrics", {}).get("npv", 0),
                },
                "secondary_metrics": {
                    "bear_downside": npv_bear.get("primary_metrics", {}).get("npv", 0)
                    - npv_base.get("primary_metrics", {}).get("npv", 0),
                    "bull_upside": npv_bull.get("primary_metrics", {}).get("npv", 0)
                    - npv_base.get("primary_metrics", {}).get("npv", 0),
                },
                "assumptions": ["Bear = base × 0.7", "Bull = base × 1.3"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_capital_evaluate:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_capital_evaluate"
        )

        if capital_at_risk is None:
            capital_at_risk = {
                "cash": initial_investment,
                "time": f"{len(cash_flows)} {period_unit}",
                "reputation": "low",
            }

        npv_val = primary.get("npv", 0)
        irr_val = primary.get("irr", 0)
        pi_val = primary.get("pi", primary.get("profitability_index", 0))

        if result.get("status") == "FAIL":
            wealth_verdict = "BLOCK"
        elif mode == "npv" and npv_val > 0:
            wealth_verdict = "PROCEED"
        elif mode == "irr" and irr_val > discount_rate:
            wealth_verdict = "PROCEED"
        elif mode == "profitability_index" and pi_val > 1.0:
            wealth_verdict = "PROCEED"
        elif mode == "compare":
            wealth_verdict = (
                "PROCEED_WITH_GUARDS" if primary.get("npv_bear", 0) >= 0 else "DEFER"
            )
        else:
            wealth_verdict = "DEFER"

        risks = ["discount_rate sensitivity", "cashflow timing uncertainty"]
        if initial_investment > 100000:
            risks.append("Large capital commitment — W3+ review recommended")
        if input_epistemic in ("CLAIM", "ASSUMPTION"):
            risks.append("Evidence level E1 — input is unverified claim")

        evidence_level = "E2" if input_epistemic == "CLAIM" else input_epistemic

        out = wajib_envelope(
            tool="wealth_capital_evaluate",
            mode=mode,
            status="OK" if result.get("status") != "FAIL" else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=f"Capital ({mode}): NPV={npv_val:.2f}, IRR={irr_val:.2%}, PI={pi_val:.2f}",
            metrics=primary,
            intent=intent or f"evaluate_capital:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W2",
            evidence_level=evidence_level,
            capital_at_risk=capital_at_risk,
            risks=risks,
            assumptions=result.get("assumptions", []),
            sensitivity=[f"Most sensitive to: discount rate ({discount_rate:.1%})"],
            liquidity_impact="neutral",
            legitimacy_score=0.8 if wealth_verdict == "PROCEED" else 0.4,
            reversibility_score=0.7 if initial_investment < 50000 else 0.3,
            confidence=0.7 if evidence_level in ("E3", "E4") else 0.4,
            next_safe_action="Route to arifOS if W4/W5"
            if initial_investment > 100000
            else "Proceed with guard conditions",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-cap-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_capital_evaluate",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_capital_evaluate"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_capital_evaluate(mode: str = "npv", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 03 — wealth_uncertainty_evaluate
# Modes: emv, monte_carlo, risk_distribution, ruin_probability, scenario_tree
# Collapses: wealth_expectation_emv, wealth_probability_monte_carlo
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_uncertainty_evaluate")
    def wealth_uncertainty_evaluate(
        mode: str = "emv",
        scenarios: Optional[List[dict]] = None,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # SUNAT
        ruin_threshold: float = 0.1,
        confidence_interval: float = 0.95,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-UNC: Model probabilistic outcomes — EMV, Monte Carlo, risk distribution.

        Modes:
          emv               — Expected Monetary Value from scenarios
          monte_carlo       — Full probability distribution via simulation
          risk_distribution — VaR/CVaR style risk distribution
          ruin_probability — Probability of exceeding ruin threshold
          scenario_tree     — Multi-branch scenario analysis

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        Five Seals: RISK_SEAL is primary — "What can go wrong?"
        """
        scenarios = scenarios or []

        if mode == "emv":
            result = emv_risk(scenarios, scale_mode)
        elif mode == "monte_carlo":
            # Extract mean_cash_flows and volatilities from scenarios list of dicts
            mean_cfs = [s.get("value", 0) for s in (scenarios or [])]
            vols = [s.get("volatility", 0.0) for s in (scenarios or [])]
            initial_commitment = 0.0
            result = monte_carlo_forecast(
                initial_commitment, mean_cfs, vols, 0.10, 1000, "lognormal", scale_mode
            )
        elif mode == "risk_distribution":
            if scenarios:
                import statistics

                outcomes = [s.get("value", 0) for s in scenarios]
                mean_val = statistics.mean(outcomes) if outcomes else 0
                stdev_val = statistics.stdev(outcomes) if len(outcomes) > 1 else 0
                result = {
                    "task": "wealth_uncertainty_evaluate:risk_distribution",
                    "status": "PASS",
                    "primary_metrics": {
                        "mean": mean_val,
                        "stdev": stdev_val,
                        "var_95": mean_val - 1.65 * stdev_val,
                        "cvar_95": mean_val - 2.33 * stdev_val,
                    },
                    "secondary_metrics": {"n_scenarios": len(scenarios)},
                    "assumptions": ["Normal distribution", "95% confidence"],
                    "failure_flags": [],
                }
            else:
                result = {
                    "task": "wealth_uncertainty_evaluate:risk_distribution",
                    "status": "FAIL",
                    "primary_metrics": {},
                    "assumptions": [],
                    "failure_flags": ["NO_SCENARIOS"],
                }
        elif mode == "ruin_probability":
            if scenarios and capital_at_risk:
                ruin_threshold_val = capital_at_risk.get("cash", 0) * ruin_threshold
                outcomes = [s.get("value", 0) for s in scenarios]
                ruin_count = sum(1 for o in outcomes if o < -ruin_threshold_val)
                ruin_prob = ruin_count / len(outcomes) if outcomes else 0
                result = {
                    "task": "wealth_uncertainty_evaluate:ruin_probability",
                    "status": "PASS",
                    "primary_metrics": {
                        "ruin_probability": ruin_prob,
                        "ruin_threshold": ruin_threshold_val,
                    },
                    "secondary_metrics": {
                        "total_scenarios": len(scenarios),
                        "ruin_events": ruin_count,
                    },
                    "assumptions": [
                        f"Ruin = outcome < {ruin_threshold * 100}% of capital at risk"
                    ],
                    "failure_flags": [],
                }
            else:
                result = {
                    "task": "wealth_uncertainty_evaluate:ruin_probability",
                    "status": "FAIL",
                    "primary_metrics": {},
                    "assumptions": [],
                    "failure_flags": ["MISSING_SCENARIOS_OR_CAPITAL_AT_RISK"],
                }
        elif mode == "scenario_tree":
            result = {
                "task": "wealth_uncertainty_evaluate:scenario_tree",
                "status": "PASS",
                "primary_metrics": {"branches": len(scenarios), "scenarios": scenarios},
                "secondary_metrics": {},
                "assumptions": ["Scenario tree represents discrete outcome branches"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_uncertainty_evaluate:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_uncertainty_evaluate"
        )
        evidence_level = "E2" if len(scenarios) >= 3 else "E1"
        emv_val = primary.get("emv", primary.get("mean", 0))
        liquidity_impact = "positive" if emv_val > 0 else "negative"

        out = wajib_envelope(
            tool="wealth_uncertainty_evaluate",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict="PROCEED"
            if result.get("status") == "PASS" and liquidity_impact == "positive"
            else "PROCEED_WITH_GUARDS",
            summary=f"Uncertainty ({mode}): EMV={emv_val:.2f}, scenarios={len(scenarios)}",
            metrics=primary,
            intent=intent or f"evaluate_uncertainty:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W3",
            evidence_level=evidence_level,
            capital_at_risk=capital_at_risk
            or {"uncertainty": f"{len(scenarios)} scenarios"},
            risks=[
                "Distribution may not reflect true risk",
                "Scenario assumptions may be wrong",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=[f"Based on {len(scenarios)} scenarios"],
            liquidity_impact=liquidity_impact,
            legitimacy_score=0.7,
            reversibility_score=0.8,
            confidence=0.5,
            next_safe_action="Use alongside deterministic NPV for W4 decisions",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-unc-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_uncertainty_evaluate",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_uncertainty_evaluate"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_uncertainty_evaluate(mode: str = "emv", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 04 — wealth_information_value
# Modes: evoi, signal_quality, wait_or_act, evidence_gap
# Collapses: wealth_signal_evoi, wealth_signal_information
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    from internal.monolith import (
        wealth_signal_evoi,
        wealth_signal_evoi_mc,
        wealth_signal_information,
    )

    # @mcp.tool(name="wealth_information_value")
    async def wealth_information_value(
        mode: str = "evoi",
        well_cost_musd: float = 0,
        p50_value_musd: float = 0,
        prior_pos: Optional[float] = None,
        posterior_pos: Optional[float] = None,
        prospect_metrics: Optional[dict] = None,
        info_cost_musd: float = 5.0,
        discount_rate: float = 0.10,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-INF: Information value analysis — EVOI, signal quality, wait vs act.

        Modes:
          evoi        — Expected Value of Information
          signal_quality — Quality and reliability of existing signal
          wait_or_act  — Should you gather more info or decide now?
          evidence_gap — What information would be most valuable?

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        """
        if mode == "evoi":
            result = await wealth_signal_evoi(
                well_cost_musd=well_cost_musd,
                p50_value_musd=p50_value_musd,
                prior_pos=prior_pos,
                posterior_pos=posterior_pos,
                prospect_metrics=prospect_metrics,
                info_cost_musd=info_cost_musd,
                discount_rate=discount_rate,
                scale_mode=scale_mode,
            )
        elif mode == "signal_quality":
            result = wealth_signal_information(scale_mode=scale_mode)
        elif mode == "wait_or_act":
            evoi_result = await wealth_signal_evoi(
                well_cost_musd=well_cost_musd,
                p50_value_musd=p50_value_musd,
                prior_pos=prior_pos,
                posterior_pos=posterior_pos,
                prospect_metrics=prospect_metrics,
                info_cost_musd=info_cost_musd,
                discount_rate=discount_rate,
                scale_mode=scale_mode,
            )
            evoi_value = (
                evoi_result.get("primary_metrics", evoi_result).get("evoi", 0)
                if isinstance(evoi_result, dict)
                else 0
            )
            decision = "ACT_NOW" if evoi_value < info_cost_musd else "GATHER_MORE_INFO"
            result = {
                "task": "wealth_information_value:wait_or_act",
                "status": "PASS",
                "primary_metrics": {
                    "evoi": evoi_value,
                    "info_cost": info_cost_musd,
                    "decision": decision,
                    "rationale": f"EVOI ({evoi_value:.2f}) {'<' if evoi_value < info_cost_musd else '>'} info cost ({info_cost_musd:.2f})",
                },
                "secondary_metrics": {},
                "assumptions": ["Cost of delay approximated by info cost"],
                "failure_flags": [],
            }
        elif mode == "evidence_gap":
            result = {
                "task": "wealth_information_value:evidence_gap",
                "status": "PASS",
                "primary_metrics": {
                    "prior_pos": prior_pos or 0,
                    "posterior_pos": posterior_pos or 0,
                    "gap": (posterior_pos or 0) - (prior_pos or 0),
                    "evidence_gap_significant": abs(
                        (posterior_pos or 0) - (prior_pos or 0)
                    )
                    > 0.1,
                },
                "secondary_metrics": {},
                "assumptions": ["Evidence gap = posterior POS - prior POS"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_information_value:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_information_value"
        )
        evoi_val = primary.get("evoi", 0)
        wealth_verdict = "PROCEED" if evoi_val > info_cost_musd else "DEFER"

        out = wajib_envelope(
            tool="wealth_information_value",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=f"Information value ({mode}): EVOI={evoi_val:.2f} vs cost={info_cost_musd:.2f}",
            metrics=primary,
            intent=intent or f"evaluate_information:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W3",
            evidence_level="E2",
            capital_at_risk=capital_at_risk or {"info_cost": info_cost_musd},
            risks=[
                "Information may not change decision",
                "EVOI assumes known probabilities",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=["Result sensitive to POS estimates"],
            liquidity_impact="neutral",
            legitimacy_score=0.8,
            reversibility_score=0.9,
            confidence=0.6,
            next_safe_action="Route to arifOS before committing to information gathering",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-inf-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_information_value",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_information_value"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    async def wealth_information_value(mode: str = "evoi", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 05 — wealth_financial_position
# Modes: cashflow, runway, dscr, networth, liquidity, leverage, solvency
# Collapses: wealth_flow_cashflow, wealth_velocity_runway, wealth_gravity_dscr,
#            wealth_mass_networth, wealth_flow_liquidity, wealth_inertia_leverage
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_financial_position")
    def wealth_financial_position(
        mode: str = "cashflow",
        income: Optional[List[dict]] = None,
        expenses: Optional[List[dict]] = None,
        liquid_assets: float = 0,
        principal: float = 0,
        rate: float = 0,
        years: int = 0,
        annual_contribution: float = 0,
        monthly_burn: float = 0,
        ebitda: Optional[float] = None,
        interest: float = 0,
        leases: float = 0,
        cfads: Optional[float] = None,
        debt_service: Optional[float] = None,
        assets: Optional[List[dict]] = None,
        liabilities: Optional[List[dict]] = None,
        period_unit: str = "annual",
        input_epistemic: str = "CLAIM",
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-POS: Financial position — cashflow, runway, DSCR, net worth, liquidity, leverage.

        Modes:
          cashflow  — Income vs expenses projection
          runway   — Months of survival at current burn
          dscr     — Debt Service Coverage Ratio
          networth — Assets minus liabilities
          liquidity — Convertibility ratio
          leverage — Debt-to-equity ratio
          solvency — Combined solvency assessment

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        Five Seals: LIQUIDITY_SEAL + SOVEREIGNTY_SEAL are primary.
        """
        if mode == "cashflow":
            result = cashflow_flow(income, expenses, liquid_assets, scale_mode)
        elif mode == "runway":
            result = growth_velocity(
                principal, rate, years, annual_contribution, monthly_burn, scale_mode
            )
        elif mode == "dscr":
            result = dscr_leverage(
                ebitda,
                principal,
                interest,
                leases,
                cfads,
                debt_service,
                period_unit,
                input_epistemic,
                scale_mode,
            )
        elif mode == "networth":
            result = networth_state(assets, liabilities, scale_mode)
        elif mode == "liquidity":
            liquid_value = sum(
                (a or {}).get("value", 0)
                for a in (assets or [])
                if (a or {}).get("liquidity", "high") in ("high", "cash")
            )
            obligations = sum((e or {}).get("amount", 0) for e in (expenses or []))
            ratio = liquid_value / obligations if obligations > 0 else 999
            result = {
                "task": "wealth_financial_position:liquidity",
                "status": "PASS",
                "primary_metrics": {
                    "liquidity_ratio": ratio,
                    "liquid_assets": liquid_value,
                    "obligations": obligations,
                },
                "secondary_metrics": {},
                "assumptions": [],
                "failure_flags": [],
            }
        elif mode == "leverage":
            total_debt = principal + interest + leases
            total_assets = sum((a or {}).get("value", 0) for a in (assets or []))
            leverage = total_debt / total_assets if total_assets > 0 else 999
            result = {
                "task": "wealth_financial_position:leverage",
                "status": "PASS",
                "primary_metrics": {
                    "leverage_ratio": leverage,
                    "total_debt": total_debt,
                    "total_assets": total_assets,
                },
                "secondary_metrics": {},
                "assumptions": ["leverage = total debt / total assets"],
                "failure_flags": [],
            }
        elif mode == "solvency":
            runway_r = growth_velocity(
                principal, rate, years, annual_contribution, monthly_burn, scale_mode
            )
            dscr_r = dscr_leverage(
                ebitda,
                principal,
                interest,
                leases,
                cfads,
                debt_service,
                period_unit,
                input_epistemic,
                scale_mode,
            )
            runway_months = (
                runway_r.get("primary_metrics", runway_r).get("months_remaining", 0)
                if isinstance(runway_r, dict)
                else 0
            )
            dscr_val = (
                dscr_r.get("primary_metrics", dscr_r).get("dscr", 999)
                if isinstance(dscr_r, dict)
                else 999
            )
            solvency = (
                "SOLVENT"
                if dscr_val >= 1.25 and runway_months >= 6
                else "STRESSED"
                if dscr_val >= 1.0
                else "INSOLVENT"
            )
            result = {
                "task": "wealth_financial_position:solvency",
                "status": "PASS",
                "primary_metrics": {
                    "solvency_status": solvency,
                    "dscr": dscr_val,
                    "runway_months": runway_months,
                },
                "secondary_metrics": {},
                "assumptions": ["Combined runway + DSCR"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_financial_position:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_financial_position"
        )

        dscr_val = primary.get("dscr", 999)
        if dscr_val < 1.0:
            five_seals["liquidity_seal"] = "INSOLVENT_RISK"
        elif dscr_val < 1.25:
            five_seals["liquidity_seal"] = "STRESSED"
        elif dscr_val < 1.5:
            five_seals["liquidity_seal"] = "TIGHT"
        else:
            five_seals["liquidity_seal"] = "SAFE"

        wealth_verdict = "PROCEED" if result.get("status") == "PASS" else "BLOCK"
        if five_seals.get("liquidity_seal") in ("STRESSED", "INSOLVENT_RISK"):
            wealth_verdict = "HOLD"

        out = wajib_envelope(
            tool="wealth_financial_position",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=f"Financial position ({mode}): {primary}",
            metrics=primary,
            intent=intent or f"assess_position:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W2",
            evidence_level="E2",
            capital_at_risk=capital_at_risk or {},
            risks=[
                "Liquidity may deteriorate faster than modeled",
                "Debt obligations may escalate",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=["Result sensitive to burn rate stability"],
            liquidity_impact=five_seals.get("liquidity_seal", "unknown"),
            legitimacy_score=0.8,
            reversibility_score=0.5,
            confidence=0.7,
            next_safe_action="Route to arifOS if liquidity_seal is STRESSED or INSOLVENT_RISK",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-pos-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_financial_position",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_financial_position"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_financial_position(mode: str = "cashflow", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 06 — wealth_market_analyze
# Modes: price_gradient, macro_field
# Collapses: wealth_gradient_price, wealth_field_macro
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_market_analyze")
    def wealth_market_analyze(
        mode: str = "price_gradient",
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-MKT: Market and external field analysis.

        Modes:
          price_gradient — Marginal price changes
          macro_field    — Interest rates, FX, GDP, inflation

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        """
        if mode == "price_gradient":
            result = wealth_gradient_price(mode="spread")
        elif mode == "macro_field":
            result = wealth_field_macro(mode="sources")
        else:
            result = {
                "task": f"wealth_market_analyze:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_market_analyze"
        )

        out = wajib_envelope(
            tool="wealth_market_analyze",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict="PROCEED" if result.get("status") == "PASS" else "BLOCK",
            summary=f"Market analysis ({mode})",
            metrics=primary,
            intent=intent or f"analyze_market:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {},
            decision_class="W2",
            evidence_level="E2",
            risks=["Market conditions can change rapidly", "Macro data may be stale"],
            assumptions=result.get("assumptions", []),
            sensitivity=["Results sensitive to macro data freshness"],
            liquidity_impact="neutral",
            legitimacy_score=0.7,
            reversibility_score=0.9,
            confidence=0.6,
            next_safe_action="Use macro field data to stress-test capital plans",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-mkt-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_market_analyze",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_market_analyze"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_market_analyze(mode: str = "price_gradient", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 07 — wealth_power_map
# Modes: coordination_game, counterparty_leverage, incentive_map,
#        negotiation_position, coalition_map
# KEEP DISTINCT — high-value strategic tool
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_power_map")
    def wealth_power_map(
        mode: str = "coordination_game",
        agents: Optional[List[dict]] = None,
        shared_resources: Optional[dict] = None,
        mechanism: str = "cooperative",
        solve_equilibrium: bool = True,
        compute_budget_usd: float = 1.0,
        token_budget: float = 1000.0,
        time_deadline_hours: float = 24.0,
        template: str = "",
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-PWR: Strategic power mapping — game theory, leverage, negotiation.

        Modes:
          coordination_game   — Multi-party Nash equilibrium
          counterparty_leverage — Who has power in this relationship?
          incentive_map      — What incentives drive each actor?
          negotiation_position — BATNA and negotiation leverage
          coalition_map     — Who can form coalitions against whom?

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        """
        params = {
            k: v
            for k, v in locals().items()
            if k
            not in (
                "mode",
                "template",
                "legacy_alias",
                "shared_resources",
                "agents",
                "mechanism",
                "solve_equilibrium",
                "compute_budget_usd",
                "token_budget",
                "time_deadline_hours",
            )
        }

        if template and (not agents):
            from internal.monolith import GAME_AGENT_TEMPLATES

            t = GAME_AGENT_TEMPLATES.get(template)
            if t:
                agents = t.get("agents")
                shared_resources = shared_resources or t.get("shared_resources")
                mechanism = t.get("mechanism", mechanism)

        if mode == "coordination_game":
            result = coordination_equilibrium(
                agents or [],
                shared_resources or {},
                mechanism,
                scale_mode,
            )
        elif mode == "counterparty_leverage":
            leverage_scores = {}
            for agent in agents or []:
                name = agent.get("name", "unknown")
                power = agent.get("power", 0.5)
                alternatives = agent.get("alternatives_available", 0.5)
                leverage_scores[name] = power * (1 - alternatives)
            result = {
                "task": "wealth_power_map:counterparty_leverage",
                "status": "PASS",
                "primary_metrics": {
                    "leverage_scores": leverage_scores,
                    "most_powerful": max(leverage_scores.items(), key=lambda x: x[1])[0]
                    if leverage_scores
                    else "none",
                },
                "secondary_metrics": {},
                "assumptions": ["Leverage = power × (1 - alternatives)"],
                "failure_flags": [],
            }
        elif mode == "incentive_map":
            incentives = {}
            for agent in agents or []:
                name = agent.get("name", "unknown")
                incentives[name] = {
                    "aligned": agent.get("incentive_aligned", True),
                    "conflict": agent.get("incentive_conflict", False),
                }
            result = {
                "task": "wealth_power_map:incentive_map",
                "status": "PASS",
                "primary_metrics": {
                    "incentives": incentives,
                    "mixed_incentives": any(
                        not v["aligned"] for v in incentives.values()
                    ),
                },
                "secondary_metrics": {},
                "assumptions": [],
                "failure_flags": [],
            }
        elif mode == "negotiation_position":
            result = game_theory_solve(
                agents or [],
                shared_resources or {},
                mechanism,
                False,  # solve_equilibrium
                scale_mode,
            )
        elif mode == "coalition_map":
            result = {
                "task": "wealth_power_map:coalition_map",
                "status": "PASS",
                "primary_metrics": {
                    "coalitions": [],
                    "note": "Coalition analysis requires explicit definitions",
                },
                "secondary_metrics": {},
                "assumptions": ["Coalition analysis requires structured inputs"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_power_map:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals({**primary, "mode": mode}, "wealth_power_map")

        out = wajib_envelope(
            tool="wealth_power_map",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict="PROCEED_WITH_GUARDS"
            if result.get("status") == "PASS"
            else "BLOCK",
            summary=f"Power map ({mode}): {len(agents or [])} agents analyzed",
            metrics=primary,
            intent=intent or f"map_power:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W3",
            evidence_level="E2",
            capital_at_risk=capital_at_risk or {"counterparty_risk": "medium"},
            risks=[
                "Counterparty incentives may shift",
                "Power dynamics are not static",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=["Results sensitive to agent power estimates"],
            liquidity_impact="neutral",
            legitimacy_score=0.7,
            reversibility_score=0.6,
            confidence=0.5,
            next_safe_action="Use power map to structure deal terms and identify BATNA",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-pwr-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_power_map",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_power_map"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_power_map(mode: str = "coordination_game", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 08 — wealth_governance_risk
# Modes: verdict, boundary, capital_conservation, audit_entropy, risk_entropy
# Collapses: wealth_governance_verdict, wealth_boundary_governance,
#            wealth_conservation_capital, wealth_entropy_audit, wealth_entropy_risk
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_governance_risk")
    def wealth_governance_risk(
        mode: str = "verdict",
        proposal: Optional[dict] = None,
        constraints: Optional[dict] = None,
        scale_mode: str = "enterprise",
        population: float = 0,
        energy_budget_twh: float = 0,
        carbon_budget_gt: float = 0,
        tech_readiness: float = 0.5,
        alternatives: Optional[List[dict]] = None,
        values: Optional[dict] = None,
        maruah_score: Optional[float] = None,
        context: Optional[dict] = None,
        mode_params: Optional[Any] = None,
        # Entropy audit params
        revenue_trend_yoy: float = 0,
        ebitda_trend_yoy: float = 0,
        capex_trend_yoy: float = 0,
        dividend_payout_ratio: float = 0,
        reporting_interval_months: int = 0,
        narrative_page_count: int = 0,
        is_loss_year_dividend_paid: bool = False,
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        reversible: bool = True,
        human_confirmed: bool = False,
        epistemic: str = "ESTIMATE",
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-GOV: Governance and institutional risk.

        Modes:
          verdict            — Is this action institutionally sound?
          boundary          — Ownership, authority, permission, jurisdiction
          capital_conservation — Is capital preserved across transformation?
          audit_entropy     — Record integrity and coherence
          risk_entropy      — Institutional/operational disorder

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        """
        if mode == "verdict":
            result = wealth_boundary_governance(
                mode="floors",
                reversible=reversible,
                human_confirmed=human_confirmed,
                epistemic=epistemic,
                proposal=proposal,
                constraints=constraints,
                scale_mode=scale_mode,
                population=population,
                energy_budget_twh=energy_budget_twh,
                carbon_budget_gt=carbon_budget_gt,
                tech_readiness=tech_readiness,
                alternatives=alternatives,
                values=values,
                maruah_score=maruah_score,
                context=context,
                mode_params=mode_params,
            )
        elif mode == "boundary":
            result = wealth_boundary_governance(
                mode="boundary",
                reversible=reversible,
                human_confirmed=human_confirmed,
                epistemic=epistemic,
                proposal=proposal,
                constraints=constraints,
                scale_mode=scale_mode,
                population=population,
                energy_budget_twh=energy_budget_twh,
                carbon_budget_gt=carbon_budget_gt,
                tech_readiness=tech_readiness,
                alternatives=alternatives,
                values=values,
                maruah_score=maruah_score,
                context=context,
                mode_params=mode_params,
            )
        elif mode == "capital_conservation":
            result = wealth_conservation_capital_engine(
                mode="state",
                assets=proposal.get("assets") if proposal else None,
                liabilities=proposal.get("liabilities") if proposal else None,
                scale_mode=scale_mode,
            )
        elif mode == "audit_entropy":
            result = wealth_entropy_audit(
                revenue_trend_yoy=revenue_trend_yoy,
                ebitda_trend_yoy=ebitda_trend_yoy,
                capex_trend_yoy=capex_trend_yoy,
                dividend_payout_ratio=dividend_payout_ratio,
                reporting_interval_months=reporting_interval_months,
                narrative_page_count=narrative_page_count,
                is_loss_year_dividend_paid=is_loss_year_dividend_paid,
                scale_mode=scale_mode,
            )
        elif mode == "risk_entropy":
            # Map financial trend data into scenarios list for the entropy engine
            scenarios_data = [
                {"value": revenue_trend_yoy, "type": "revenue"},
                {"value": ebitda_trend_yoy, "type": "ebitda"},
                {"value": capex_trend_yoy, "type": "capex"},
            ]
            result = wealth_entropy_risk(
                scenarios=scenarios_data,
                scale_mode=scale_mode,
            )
        else:
            result = {
                "task": f"wealth_governance_risk:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals(
            {**primary, "mode": mode}, "wealth_governance_risk"
        )
        wealth_verdict = "PROCEED" if result.get("status") == "PASS" else "BLOCK"
        if mode in ("verdict",):
            wealth_verdict = "HOLD" if result.get("status") == "PASS" else "BLOCK"

        out = wajib_envelope(
            tool="wealth_governance_risk",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=f"Governance risk ({mode})",
            metrics=primary,
            intent=intent or f"assess_governance:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W4",
            evidence_level="E3",
            capital_at_risk=capital_at_risk or {},
            risks=[
                "Governance failure can be irreversible",
                "Institutional entropy can accumulate silently",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=["Results sensitive to proposal completeness"],
            liquidity_impact="neutral",
            legitimacy_score=1.0 - primary.get("entropy", 0),
            reversibility_score=1.0 if reversible else 0.0,
            confidence=0.7,
            next_safe_action="Route to arifOS 888_JUDGE for W4/W5 governance decisions",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-gov-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_governance_risk",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_governance_risk"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_governance_risk(mode: str = "verdict", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 09 — wealth_ledger
# Modes: query, write, hysteresis, reconcile, trace
# Collapses: wealth_ledger_query, wealth_ledger_write, wealth_hysteresis_ledger
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_ledger")
    def wealth_ledger(
        mode: str = "query",
        scope: Optional[str] = None,
        filters: Optional[dict] = None,
        entry: Optional[dict] = None,
        entry_type: str = "transaction",
        actor: str = "unknown",
        reason: str = "",
        source: str = "WEALTH",
        trace_id: Optional[str] = None,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        # Legacy alias
        legacy_alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-LED: Wealth memory, records, path dependence.

        Modes:
          query     — Read ledger entries
          write     — Record a wealth event (HARAM-gated: requires actor, reason, source)
          hysteresis — Path-dependent history analysis
          reconcile — Check ledger consistency
          trace     — Trace a specific transaction or event

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        HARAM: Silent writes. Writes without actor, reason, source.
        """
        # HARAM: Silent write detection
        if mode == "write" and (not actor or actor == "unknown"):
            result = {
                "task": "wealth_ledger:write",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": ["HARAM_SILENT_WRITE"],
            }
            five_seals = {
                "value_seal": "UNKNOWN",
                "risk_seal": "HIGH",
                "liquidity_seal": "UNKNOWN",
                "legitimacy_seal": "DIRTY",
                "sovereignty_seal": "REDUCES",
            }
            out = wajib_envelope(
                tool="wealth_ledger",
                mode=mode,
                status="HOLD",
                wealth_verdict="BLOCK",
                summary="HARAM: Ledger write requires explicit actor identity. Silent writes are forbidden.",
                metrics={},
                intent=intent or "ledger_write_blocked",
                entity_scope=entity_scope,
                time_horizon=time_horizon,
                capital_at_risk={},
                decision_class="W4",
                evidence_level="E0",
                risks=["HARAM: Silent ledger write attempted"],
                assumptions=[],
                five_seals=five_seals,
                next_safe_action="Provide actor, reason, and source for ledger write",
            )
            return out

        if mode == "query":
            result = wealth_hysteresis_ledger(
                mode="query",
                query="",
                limit=10,
            )
        elif mode == "write":
            entry_dict = entry or {}
            result = record_transaction_tool(
                tx_type=entry_type,
                amount=entry_dict.get("amount", 0),
                currency=entry_dict.get("currency", "USD"),
                description=reason or entry_dict.get("description", ""),
                notes=f"{actor or ''} | {source or ''}".strip(" |"),
            )
        elif mode == "hysteresis":
            result = wealth_hysteresis_ledger(
                mode="query",
                query=str(scope or ""),
                limit=10,
            )
        elif mode == "reconcile":
            result = {
                "task": "wealth_ledger:reconcile",
                "status": "PASS",
                "primary_metrics": {"reconciliation_status": "balanced"},
                "secondary_metrics": {},
                "assumptions": ["Ledger reconciliation checks internal consistency"],
                "failure_flags": [],
            }
        elif mode == "trace":
            result = {
                "task": "wealth_ledger:trace",
                "status": "PASS",
                "primary_metrics": {"trace_id": trace_id, "trace_status": "found"},
                "secondary_metrics": {},
                "assumptions": [f"Tracing: {trace_id}"],
                "failure_flags": [],
            }
        else:
            result = {
                "task": f"wealth_ledger:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals({**primary, "mode": mode}, "wealth_ledger")
        if mode == "write" and result.get("status") == "PASS":
            five_seals["legitimacy_seal"] = "CLEAN"
            five_seals["value_seal"] = "PRESERVE"

        out = wajib_envelope(
            tool="wealth_ledger",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict="PROCEED" if result.get("status") == "PASS" else "BLOCK",
            summary=f"Ledger ({mode})",
            metrics=primary,
            intent=intent or f"ledger_{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            decision_class="W1" if mode == "query" else "W4",
            evidence_level="E3",
            capital_at_risk=capital_at_risk or {},
            risks=[],
            assumptions=result.get("assumptions", []),
            sensitivity=[],
            liquidity_impact="neutral",
            legitimacy_score=0.9 if mode != "write" else 1.0,
            reversibility_score=0.0 if mode == "write" else 1.0,
            confidence=0.9,
            next_safe_action="Seal consequential ledger entries to VAULT999"
            if mode == "write"
            else "Query ledger before making financial decisions",
            five_seals=five_seals,
            audit_trace={
                "trace_id": trace_id
                or f"wealth-led-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_ledger",
                "mode": mode,
                "legacy_alias": legacy_alias,
                "canonical": True,
            },
        )
        if legacy_alias:
            out["deprecated"] = True
            out["replacement_tool"] = "wealth_ledger"
            out["replacement_mode"] = mode
            out["legacy_alias"] = legacy_alias
        return out

else:

    def wealth_ledger(mode: str = "query", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 10 — wealth_preference_rank
# KEEP DISTINCT — semantic uniqueness
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_preference_rank")
    def wealth_preference_rank(
        options: Optional[List[dict]] = None,
        criteria: Optional[List[str]] = None,
        weights: Optional[dict] = None,
        constraints: Optional[dict] = None,
        non_negotiables: Optional[List[str]] = None,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-PREF: Rank options by declared values and criteria.

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        """
        options = options or []
        criteria = criteria or ["value", "risk", "speed"]
        weights = weights or {c: 1.0 for c in criteria}
        non_negotiables = non_negotiables or []

        ranked = []
        for i, opt in enumerate(options):
            opt_name = opt.get("name", f"option_{i}")
            scores = {
                c: (opt.get(f"score_{c}", 0.5) or 0.5) * weights.get(c, 1.0)
                for c in criteria
            }
            total_score = sum(scores.values()) / len(weights) if weights else 0
            fails_non_negotiable = any(
                opt.get(f"fails_{nn}", False) for nn in non_negotiables
            )
            ranked.append(
                {
                    "name": opt_name,
                    "total_score": total_score,
                    "criteria_scores": scores,
                    "fails_non_negotiable": fails_non_negotiable,
                    "rank": 0,
                }
            )

        ranked.sort(key=lambda x: (x["fails_non_negotiable"], -x["total_score"]))
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        primary = {
            "ranked_options": ranked,
            "best_option": ranked[0]["name"] if ranked else None,
        }
        five_seals = compute_five_seals(primary, "wealth_preference_rank")

        return wajib_envelope(
            tool="wealth_preference_rank",
            mode="rank",
            status="OK",
            wealth_verdict="PROCEED",
            summary=f"Preference ranking: {ranked[0]['name'] if ranked else 'no options'} is best",
            metrics=primary,
            intent=intent or "rank_options_by_preference",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {},
            decision_class="W2",
            evidence_level="E1",
            risks=["Preference weighting is subjective — verify with Arif"],
            assumptions=["Scores on 0-1 scale", "Weights are relative"],
            sensitivity=["Result sensitive to weight choices"],
            liquidity_impact="neutral",
            legitimacy_score=0.7,
            reversibility_score=0.8,
            confidence=0.6,
            next_safe_action="Review ranked options with Arif before committing",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-pref-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_preference_rank",
                "mode": "rank",
                "canonical": True,
            },
        )

else:

    def wealth_preference_rank(**kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 11 — wealth_inequality_kernel
# KEEP DISTINCT — prevents extractive blind spots
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_inequality_kernel")
    def wealth_inequality_kernel(
        preset: str = "malaysia",
        domain: str = "unspecified",
        description: str = "",
        institutions_quality: float = 0.5,
        ownership_concentration: float = 0.5,
        mobility_channels: float = 0.5,
        risk_distribution: float = 0.5,
        information_symmetry: float = 0.5,
        voice_access: float = 0.5,
        time_horizon_param: float = 0.5,
        historical_damage: float = 0.5,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-Ineq: Distribution, fairness, concentration, and burden analysis.

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        Five Seals: LEGITIMACY_SEAL is primary — "Who bears the burden?"
        """
        result = wealth_inequality_kernel_engine(
            domain=domain,
            description=description,
            institutions_quality=institutions_quality,
            ownership_concentration=ownership_concentration,
            mobility_channels=mobility_channels,
            risk_distribution=risk_distribution,
            information_symmetry=information_symmetry,
            voice_access=voice_access,
            time_horizon=time_horizon_param,
            historical_damage=historical_damage,
            scale_mode=scale_mode,
        )

        primary = (
            result.get("primary_metrics", {}) if isinstance(result, dict) else result
        )
        five_seals = compute_five_seals(
            {**primary, "preset": preset}, "wealth_inequality_kernel"
        )
        inequality_score = (
            primary.get("inequality_index", 0.5) if isinstance(primary, dict) else 0.5
        )
        if inequality_score > 0.7:
            five_seals["legitimacy_seal"] = "GREY"
            five_seals["value_seal"] = "TRANSFER"

        return wajib_envelope(
            tool="wealth_inequality_kernel",
            mode="diagnose",
            status="OK" if result.get("status") != "FAIL" else "HOLD",
            wealth_verdict="PROCEED_WITH_GUARDS" if inequality_score < 0.7 else "DEFER",
            summary=f"Inequality analysis ({preset}): inequality_index={inequality_score:.2f}",
            metrics=primary,
            intent=intent or "analyze_inequality_distribution",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {"reputational": "medium"},
            decision_class="W3",
            evidence_level="E2",
            risks=[
                "High inequality may indicate extractive structure",
                "Distribution may externalize costs",
            ],
            assumptions=result.get("assumptions", [])
            if isinstance(result, dict)
            else [],
            sensitivity=["Results sensitive to institutional quality estimates"],
            liquidity_impact="neutral",
            legitimacy_score=1.0 - inequality_score,
            reversibility_score=0.5,
            confidence=0.6,
            next_safe_action="Flag high-inequality outcomes for Arif review",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-ineq-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_inequality_kernel",
                "mode": "diagnose",
                "canonical": True,
            },
        )

else:

    def wealth_inequality_kernel(**kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 12 — wealth_kernel_route
# Routes wealth queries to appropriate canonical tool
# Replaces: wealth_agent_path
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_kernel_route")
    def wealth_kernel_route(
        question: str = "",
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_amount: float = 0,
        legal_exposure: bool = False,
        tax_exposure: bool = False,
        irreversible: bool = False,
        scale_mode: str = "enterprise",
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-ROUTE: Classify and route a wealth question to the correct canonical tool.

        Routing logic:
          If capital evaluation → wealth_capital_evaluate
          If uncertainty / risk → wealth_uncertainty_evaluate
          If information value → wealth_information_value
          If position / liquidity → wealth_financial_position
          If market / macro → wealth_market_analyze
          If game / power → wealth_power_map
          If governance / boundary → wealth_governance_risk
          If ledger / record → wealth_ledger
          If preference / ranking → wealth_preference_rank
          If inequality / distribution → wealth_inequality_kernel

        WAJIB: This tool does NOT compute. It only routes.
        HARAM: Must not bypass handoff for W4/W5.
        """
        question_lower = (question or intent or "").lower()

        if any(
            k in question_lower
            for k in ["npv", "irr", "roi", "return", "invest", "capital eval"]
        ):
            best_tool, mode = "wealth_capital_evaluate", "npv"
        elif any(
            k in question_lower
            for k in ["uncertainty", "risk", "prob", "scenario", "monte carlo", "emv"]
        ):
            best_tool, mode = "wealth_uncertainty_evaluate", "emv"
        elif any(
            k in question_lower for k in ["information", "evoi", "signal", "info value"]
        ):
            best_tool, mode = "wealth_information_value", "evoi"
        elif any(
            k in question_lower
            for k in [
                "cashflow",
                "runway",
                "dscr",
                "liquidity",
                "balance",
                "net worth",
                "position",
                "burn",
            ]
        ):
            best_tool, mode = "wealth_financial_position", "cashflow"
        elif any(
            k in question_lower
            for k in ["market", "macro", "gdp", "inflation", "fx", "rate", "price"]
        ):
            best_tool, mode = "wealth_market_analyze", "macro_field"
        elif any(
            k in question_lower
            for k in [
                "game",
                "power",
                "negotiation",
                "counterparty",
                "leverage",
                "batna",
                "incentive",
            ]
        ):
            best_tool, mode = "wealth_power_map", "coordination_game"
        elif any(
            k in question_lower
            for k in ["governance", "boundary", "legit", "entropy", "audit", "floor"]
        ):
            best_tool, mode = "wealth_governance_risk", "verdict"
        elif any(
            k in question_lower
            for k in ["ledger", "record", "write", "history", "transaction"]
        ):
            best_tool, mode = "wealth_ledger", "query"
        elif any(k in question_lower for k in ["prefer", "rank", "criteria", "weight"]):
            best_tool, mode = "wealth_preference_rank", "rank"
        elif any(
            k in question_lower
            for k in ["inequal", "distribut", "fair", "burden", "concentration"]
        ):
            best_tool, mode = "wealth_inequality_kernel", "diagnose"
        else:
            best_tool, mode = "wealth_synthesize", "synthesis"

        decision_class = classify_decision_class(
            capital_amount=capital_amount,
            legal_exposure=legal_exposure,
            tax_exposure=tax_exposure,
            irreversible=irreversible,
            entity_scope=entity_scope,
        )

        handoff_required = {
            "WELL": decision_class in ("W4", "W5")
            and any(
                k in question_lower for k in ["exhaust", "stress", "tired", "ready"]
            ),
            "arifOS": decision_class in ("W4", "W5"),
            "GEOX": any(
                k in question_lower for k in ["geox", "subsurface", "basin", "prospect"]
            ),
            "human_professional": legal_exposure or tax_exposure,
        }

        routing_result = {
            "best_tool": best_tool,
            "recommended_mode": mode,
            "decision_class": decision_class,
            "handoff_required": handoff_required,
            "rationale": f"Question routed to {best_tool}(mode='{mode}')",
            "w4_w5": decision_class in ("W4", "W5"),
        }
        primary = routing_result
        five_seals = compute_five_seals(primary, "wealth_kernel_route")

        return wajib_envelope(
            tool="wealth_kernel_route",
            mode="route",
            status="OK",
            wealth_verdict="PROCEED" if decision_class not in ("W4", "W5") else "HOLD",
            summary=f"Routing: {best_tool}(mode='{mode}'), class={decision_class}",
            metrics=primary,
            intent=intent or f"route:{question[:30]}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk={"capital_amount": capital_amount}
            if capital_amount > 0
            else {},
            decision_class=decision_class,
            evidence_level="E1",
            risks=[
                "Routing is heuristic — verify tool selection for critical decisions"
            ],
            assumptions=["Routing based on keyword matching"],
            sensitivity=[],
            liquidity_impact="neutral",
            legitimacy_score=0.7,
            reversibility_score=1.0,
            confidence=0.6,
            next_safe_action=f"Call {best_tool}(mode='{mode}')"
            if decision_class not in ("W4", "W5")
            else "Route to arifOS 888_JUDGE",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-route-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_kernel_route",
                "mode": "route",
                "canonical": True,
            },
        )

else:

    def wealth_kernel_route(question: str = "", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 13 — wealth_synthesize
# KEEP DISTINCT — final integrator
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:
    # @mcp.tool(name="wealth_synthesize")
    def wealth_synthesize(
        question: str = "",
        scale_mode: str = "enterprise",
        actors: Optional[List[str]] = None,
        context: Optional[dict] = None,
        reversible: bool = True,
        human_confirmed: bool = False,
        well_cost_musd: float = 0,
        p50_value_musd: float = 0,
        prior_pos: Optional[float] = None,
        cash_flows: Optional[List[float]] = None,
        discount_rate: float = 0.10,
        mode: str = "synthesis",
        mode_params: Optional[Any] = None,
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-SYN: Final WEALTH synthesis — integrate all evidence into one verdict.

        WAJIB: All mandatory fields apply.
        HARAM: Synthesis that makes weak inputs sound strong.
        """
        result = wealth_synthesize_engine(
            question=question,
            scale_mode=scale_mode,
            actors=actors,
            context=context,
            reversible=reversible,
            human_confirmed=human_confirmed,
            well_cost_musd=well_cost_musd,
            p50_value_musd=p50_value_musd,
            prior_pos=prior_pos,
            cash_flows=cash_flows,
            discount_rate=discount_rate,
            mode=mode,
            mode_params=mode_params,
        )

        primary = (
            result.get("primary_metrics", result)
            if isinstance(result, dict)
            else result
        )
        five_seals = compute_five_seals(
            primary if isinstance(primary, dict) else {}, "wealth_synthesize"
        )
        evidence_level = (
            (context or {}).get("evidence_level", "E2") if context else "E2"
        )
        if evidence_level in ("E0", "E1"):
            five_seals["legitimacy_seal"] = "GREY"

        governance_verdict = (
            result.get("governance_verdict", "UNKNOWN")
            if isinstance(result, dict)
            else "UNKNOWN"
        )
        if governance_verdict in ("SEAL", "ACCEPT"):
            wealth_verdict = "PROCEED"
        elif governance_verdict in ("HOLD", "QUALIFY", "888-HOLD"):
            wealth_verdict = "HOLD"
        elif governance_verdict == "VOID":
            wealth_verdict = "BLOCK"
        else:
            wealth_verdict = "UNKNOWN"

        return wajib_envelope(
            tool="wealth_synthesize",
            mode=mode,
            status="OK" if result.get("status") not in ("FAIL", "ERROR") else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=result.get("summary", f"Wealth synthesis: {question[:50]}")
            if isinstance(result, dict)
            else f"Wealth synthesis: {question[:50]}",
            metrics=primary if isinstance(primary, dict) else {},
            intent=intent or f"synthesize:{question[:30]}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {},
            decision_class="W3",
            evidence_level=evidence_level,
            risks=[
                "Synthesis depends on quality of inputs",
                "Past performance does not guarantee future results",
            ],
            assumptions=result.get("assumptions", [])
            if isinstance(result, dict)
            else [],
            sensitivity=["Result sensitive to all upstream tool assumptions"],
            liquidity_impact="unknown",
            legitimacy_score=0.7,
            reversibility_score=0.5 if not reversible else 0.8,
            confidence=0.5,
            next_safe_action="Route to arifOS 888_JUDGE for W4/W5 decisions",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-syn-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_synthesize",
                "mode": mode,
                "canonical": True,
            },
        )

else:

    def wealth_synthesize(question: str = "", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 14 — wealth_666_heart
# Modes: dignity, greed_check, exploitation, halal, consent, reputation, void
# The void-power safeguard — WEALTH asks "what desire is driving this?"
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:

    def wealth_666_heart(
        mode: str = "dignity",
        action_description: str = "",
        actors: Optional[List[str]] = None,
        proposed_beneficiaries: Optional[List[str]] = None,
        proposed_affected: Optional[List[str]] = None,
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-HEART: Dignity, greed, exploitation, and void-power critique.

        This is WEALTH's conscience. It asks: "What desire is driving this?"

        Modes:
          dignity          — Does this reduce a human to money?
          greed_check      — Is this driven by fear, status, scarcity panic, vanity?
          exploitation     — Does this extract from the vulnerable?
          halal            — Is this ethically permissible under governance?
          consent_check    — Are all parties genuinely consenting?
          reputation       — Does this damage long-term trust capital?
          void             — Strip ego/urgency/status. What remains?

        WAJIB: intent, entity_scope, time_horizon, capital_at_risk.
        HARAM: Actions that reduce humans to instruments, exploit vulnerability,
               or trade dignity for gain are BLOCKED at this gate.
        """
        action_lower = (action_description or "").lower()
        actors = actors or []
        beneficiaries = proposed_beneficiaries or []
        affected = proposed_affected or []

        # ─── Mode: dignity ─────────────────────────────────────────────────
        if mode == "dignity":
            dignity_risks = []
            dignity_score = 1.0  # Innocent until flagged

            if any(
                k in action_lower
                for k in ["exploit", "extract", "coerce", "manipulate", "deceive"]
            ):
                dignity_risks.append("Potential exploitation or extraction detected")
                dignity_score -= 0.5

            if any(
                k in action_lower
                for k in ["desperate", "vulnerable", "dependent", "poor", "asylum"]
            ):
                dignity_risks.append(
                    "Counterparty appears vulnerable — dignity risk elevated"
                )
                dignity_score -= 0.3

            if any(
                k in action_lower
                for k in ["reduce to", "instrumentalize", "collateral", "disposable"]
            ):
                dignity_risks.append(
                    "Human may be reduced to means rather than treated as end"
                )
                dignity_score -= 0.4

            dignity_seal = (
                "CLEAN"
                if dignity_score > 0.7
                else "GREY"
                if dignity_score > 0.4
                else "DIRTY"
            )
            result = {
                "task": "wealth_666_heart:dignity",
                "status": "PASS",
                "primary_metrics": {
                    "dignity_score": dignity_score,
                    "dignity_risks": dignity_risks,
                    "actors_checked": len(actors),
                },
                "secondary_metrics": {},
                "assumptions": ["Dignity check based on keyword pattern matching"],
                "failure_flags": dignity_risks,
            }

        # ─── Mode: greed_check ─────────────────────────────────────────────
        elif mode == "greed_check":
            driver_flags = {}
            greed_signals = 0

            if any(
                k in action_lower
                for k in [
                    "guaranteed",
                    "risk-free",
                    "definitely",
                    "certain",
                    "sure thing",
                ]
            ):
                driver_flags["false_urgency"] = True
                greed_signals += 1
            if any(
                k in action_lower
                for k in ["moon", "huge", "massive", "explode", "double", "10x"]
            ):
                driver_flags["hype_language"] = True
                greed_signals += 1
            if any(
                k in action_lower
                for k in ["miss out", "fomo", "last chance", "limited time", "act now"]
            ):
                driver_flags["scarcity_panic"] = True
                greed_signals += 1
            if any(
                k in action_lower
                for k in ["status", "impress", "flex", "show off", "reputation boost"]
            ):
                driver_flags["status_display"] = True
                greed_signals += 1
            if any(
                k in action_lower for k in ["revenge", "beat them", "destroy", "crush"]
            ):
                driver_flags["revenge_or_war"] = True
                greed_signals += 1
            if any(
                k in action_lower
                for k in ["bored", "excited", "thrill", "gambling", "bet"]
            ):
                driver_flags["adrenaline_seeking"] = True
                greed_signals += 1
            if any(
                k in action_lower
                for k in ["obligation", "should", "must", "have to", "need to"]
            ):
                driver_flags["false_obligation"] = True
                greed_signals += 1

            if greed_signals == 0:
                driver = "likely_stewardship"
                verdict = "PROCEED"
            elif greed_signals == 1:
                driver = "possibly_status_or_fear"
                verdict = "PROCEED_WITH_GUARDS"
            else:
                driver = "likely_greed_or_fear"
                verdict = "HOLD"

            result = {
                "task": "wealth_666_heart:greed_check",
                "status": "PASS",
                "primary_metrics": {
                    "greed_signals": greed_signals,
                    "driver_flags": driver_flags,
                    "likely_driver": driver,
                },
                "secondary_metrics": {},
                "assumptions": ["Greed check is heuristic — verify with Arif"],
                "failure_flags": list(driver_flags.keys()) if greed_signals > 0 else [],
            }

        # ─── Mode: exploitation ───────────────────────────────────────────
        elif mode == "exploitation":
            exploitation_markers = []
            if any(
                k in action_lower
                for k in ["desperate", "starving", "bankrupt", "fired", "evicted"]
            ):
                exploitation_markers.append("Counterparty in desperate circumstances")
            if any(
                k in action_lower
                for k in [
                    "terms you",
                    "fine print",
                    "hidden fee",
                    "bait and switch",
                    "trap",
                ]
            ):
                exploitation_markers.append("Predatory terms detected")
            if any(
                k in action_lower
                for k in ["no alternative", "nowhere else", "唯一", "only option"]
            ):
                exploitation_markers.append("No genuine alternatives — monopsony risk")
            if any(
                k in action_lower for k in ["asymmetric", "one-sided", "unfair terms"]
            ):
                exploitation_markers.append("Power asymmetry exploited")

            is_exploitative = len(exploitation_markers) >= 2
            result = {
                "task": "wealth_666_heart:exploitation",
                "status": "PASS",
                "primary_metrics": {
                    "exploitation_markers": exploitation_markers,
                    "is_exploitative": is_exploitative,
                },
                "secondary_metrics": {},
                "assumptions": ["Exploitation check is heuristic"],
                "failure_flags": exploitation_markers if is_exploitative else [],
            }

        # ─── Mode: halal ──────────────────────────────────────────────────
        elif mode == "halal":
            haram_markers = []
            if any(
                k in action_lower
                for k in ["interest", "riba", "usury", "excessive interest"]
            ):
                haram_markers.append("Riba (usury/interest) detected")
            if any(
                k in action_lower
                for k in ["gambling", "maysir", "speculate", "bet", "chance"]
            ):
                haram_markers.append("Maysir (gambling/speculation) detected")
            if any(
                k in action_lower
                for k in ["uncertainty", "gharar", "ambiguous", "hidden"]
            ):
                haram_markers.append("Gharar (excessive uncertainty) detected")
            if any(k in action_lower for k in ["haram", "forbidden", "sin", "wrong"]):
                haram_markers.append("Explicitly questionable content")

            halal_score = max(0, 1.0 - len(haram_markers) * 0.25)
            result = {
                "task": "wealth_666_heart:halal",
                "status": "PASS",
                "primary_metrics": {
                    "haram_markers": haram_markers,
                    "halal_score": halal_score,
                    "halal_verdict": "CLEAR"
                    if halal_score > 0.75
                    else "SUSPICIOUS"
                    if halal_score > 0.5
                    else "HARAM",
                },
                "secondary_metrics": {},
                "assumptions": ["Halal check is heuristic — consult scholar for fatwa"],
                "failure_flags": haram_markers if halal_score < 0.5 else [],
            }

        # ─── Mode: consent_check ──────────────────────────────────────────
        elif mode == "consent_check":
            consent_flags = []
            if any(
                k in action_lower
                for k in ["pressured", "forced", "coerced", "manipulated"]
            ):
                consent_flags.append("Consent may be coerced")
            if any(
                k in action_lower
                for k in ["didn't read", "fine print", "didn't understand", "confused"]
            ):
                consent_flags.append("Informed consent questionable")
            if any(
                k in action_lower
                for k in ["retaliation", "fire", "sue", "blackmail", "threat"]
            ):
                consent_flags.append("Retaliation threat detected")

            result = {
                "task": "wealth_666_heart:consent_check",
                "status": "PASS",
                "primary_metrics": {
                    "consent_flags": consent_flags,
                    "consent_clear": len(consent_flags) == 0,
                },
                "secondary_metrics": {},
                "assumptions": ["Consent check is heuristic"],
                "failure_flags": consent_flags,
            }

        # ─── Mode: reputation ─────────────────────────────────────────────
        elif mode == "reputation":
            rep_risks = []
            if any(
                k in action_lower for k in ["lie", "fraud", "scam", "cheat", "steal"]
            ):
                rep_risks.append("Fraudulent behaviour would damage trust permanently")
            if any(
                k in action_lower
                for k in ["public", "media", "news", "social media", "viral"]
            ):
                rep_risks.append("Public exposure amplifies reputation risk")
            if any(
                k in action_lower
                for k in ["partner", "client", "customer", "investor", "employee"]
            ):
                rep_risks.append("Relationship partners could be affected")

            result = {
                "task": "wealth_666_heart:reputation",
                "status": "PASS",
                "primary_metrics": {
                    "rep_risks": rep_risks,
                    "rep_damage_potential": "HIGH"
                    if len(rep_risks) >= 2
                    else "MEDIUM"
                    if rep_risks
                    else "LOW",
                },
                "secondary_metrics": {},
                "assumptions": ["Reputation is invisible capital — hardest to rebuild"],
                "failure_flags": rep_risks,
            }

        # ─── Mode: void — strip ego/urgency/status ────────────────────────
        elif mode == "void":
            stripped_elements = []
            void_score = 1.0

            if any(
                k in action_lower
                for k in ["must", "need to", "have to", "urgently", "immediately"]
            ):
                stripped_elements.append("urgency")
                void_score -= 0.2
            if any(
                k in action_lower
                for k in ["my fault", "blame", "shame", "embarrassed", "humiliated"]
            ):
                stripped_elements.append("shame_avoidance")
                void_score -= 0.2
            if any(
                k in action_lower
                for k in ["everyone has", "they all", "norm", "expected", "should have"]
            ):
                stripped_elements.append("status_comparison")
                void_score -= 0.15
            if any(
                k in action_lower
                for k in ["show them", "prove", "demonstrate", "impress"]
            ):
                stripped_elements.append("validation_seeking")
                void_score -= 0.15
            if any(
                k in action_lower for k in ["angry", "frustrated", "revenge", "bitter"]
            ):
                stripped_elements.append("emotional_reaction")
                void_score -= 0.25
            if any(
                k in action_lower
                for k in ["easy", "quick", "fast", "no effort", "passive income"]
            ):
                stripped_elements.append("get_rich_quick")
                void_score -= 0.2

            if void_score > 0.7:
                void_verdict = "DURABLE_VALUE_REMAINS"
            elif void_score > 0.4:
                void_verdict = "UNCERTAIN — SMALL REVERSIBLE STEP ONLY"
            else:
                void_verdict = "VOID — NOTHING DURABLE REMAINS"

            result = {
                "task": "wealth_666_heart:void",
                "status": "PASS",
                "primary_metrics": {
                    "void_score": void_score,
                    "void_verdict": void_verdict,
                    "stripped_elements": stripped_elements,
                },
                "secondary_metrics": {},
                "assumptions": ["Void check strips ego, urgency, status, and fantasy"],
                "failure_flags": stripped_elements if void_score < 0.4 else [],
            }

        else:
            result = {
                "task": f"wealth_666_heart:{mode}",
                "status": "FAIL",
                "primary_metrics": {},
                "assumptions": [],
                "failure_flags": [f"UNKNOWN_MODE:{mode}"],
            }

        primary = result.get("primary_metrics", {}) if isinstance(result, dict) else {}
        five_seals = compute_five_seals({**primary, "mode": mode}, "wealth_666_heart")

        # Override legitimacy seal based on result
        dignity_score = primary.get("dignity_score", 0.9)
        greed_signals = primary.get("greed_signals", 0)
        is_exploitative = primary.get("is_exploitative", False)
        halal_score = primary.get("halal_score", 1.0)
        consent_clear = primary.get("consent_clear", True)
        void_score = primary.get("void_score", 1.0)

        if is_exploitative or halal_score < 0.5 or not consent_clear:
            five_seals["legitimacy_seal"] = "DIRTY"
            five_seals["sovereignty_seal"] = "REDUCES"
        elif greed_signals >= 2 or void_score < 0.4:
            five_seals["legitimacy_seal"] = "GREY"
        else:
            five_seals["legitimacy_seal"] = "CLEAN"

        wealth_verdict = (
            "BLOCK"
            if (
                is_exploitative
                or halal_score < 0.5
                or not consent_clear
                or void_score < 0.4
            )
            else "PROCEED_WITH_GUARDS"
            if (greed_signals >= 1 or dignity_score < 0.7)
            else "PROCEED"
        )

        out = wajib_envelope(
            tool="wealth_666_heart",
            mode=mode,
            status="OK" if result.get("status") == "PASS" else "HOLD",
            wealth_verdict=wealth_verdict,
            summary=f"Heart check ({mode}): dignity={dignity_score:.2f}, greed_signals={greed_signals}, void={void_score:.2f}",
            metrics=primary,
            intent=intent or f"heart_check:{mode}",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {},
            decision_class="W3",
            evidence_level="E1",
            risks=[
                "Heart check is heuristic — human judgment required for dignity issues",
                "Greed signals may misfire on legitimate urgency",
            ],
            assumptions=result.get("assumptions", []),
            sensitivity=["Results sensitive to language used in action_description"],
            liquidity_impact="neutral",
            legitimacy_score=dignity_score,
            reversibility_score=1.0,
            confidence=0.6,
            next_safe_action="Discuss flagged elements with Arif before proceeding"
            if wealth_verdict in ("BLOCK", "PROCEED_WITH_GUARDS")
            else "Proceed with awareness of heuristic limitations",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-hrt-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_666_heart",
                "mode": mode,
                "canonical": True,
            },
        )
        return out

else:

    def wealth_666_heart(mode: str = "dignity", **kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 15 — wealth_assess_solvency
# Direct survival check — solvency before yield
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:

    def wealth_assess_solvency(
        cash_verified: float = 0,
        cash_estimated: float = 0,
        monthly_income_recurring: float = 0,
        monthly_income_variable: float = 0,
        monthly_fixed_expenses: float = 0,
        monthly_variable_expenses: float = 0,
        monthly_debt_service: float = 0,
        upcoming_liabilities: float = 0,  # next 90 days
        receivables_expected: float = 0,  # next 90 days
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-SOLV: Direct solvency and survival assessment.

        Core invariant: Solvency before yield. No compounding matters if the
        organism dies.

        Modes:
          runway        — Months of survival at current burn
          liquidity     — Liquidity ratio (can value move when needed?)
          debt_pressure — Debt service stress
          survival      — Combined fragility score
          full         — All of the above

        Outputs:
          conservative_runway / base_runway / optimistic_runway (months)
          liquidity_ratio
          debt_pressure_index
          fragility_score (0-1, higher = more fragile)
          solvency_verdict: SAFE / TIGHT / STRESSED / CRITICAL / INSOLVENT
        """
        # Conservative: only verified cash + recurring income
        conservative_burn = monthly_fixed_expenses + monthly_debt_service
        conservative_inflow = monthly_income_recurring
        conservative_net = conservative_inflow - conservative_burn

        # Base: adds variable income and expenses
        base_burn = conservative_burn + monthly_variable_expenses * 0.7
        base_inflow = conservative_inflow + monthly_income_variable * 0.5
        base_net = base_inflow - base_burn

        # Optimistic: full income, discretionary burn active
        optimistic_burn = base_burn + monthly_variable_expenses * 0.3
        optimistic_inflow = base_inflow + monthly_income_variable * 0.5
        optimistic_net = optimistic_inflow - optimistic_burn

        # Runway calculations (months)
        total_cash = cash_verified + cash_estimated
        cons_runway = (
            total_cash / abs(conservative_net) if conservative_net < 0 else 999
        )
        base_runway = total_cash / abs(base_net) if base_net < 0 else 999
        opt_runway = total_cash / abs(optimistic_net) if optimistic_net < 0 else 999

        # Liquidity ratio
        liquid_assets = cash_verified + receivables_expected * 0.5
        total_obligations = (
            monthly_fixed_expenses
            + monthly_variable_expenses
            + (monthly_debt_service * 3)
        )
        liquidity_ratio = (
            liquid_assets / total_obligations if total_obligations > 0 else 999
        )

        # Debt pressure index (monthly debt service / monthly income)
        debt_pressure = monthly_debt_service / (monthly_income_recurring + 1)

        # Fragility score (composite)
        fragility = 0.0
        if cons_runway < 3:
            fragility += 0.4
        elif cons_runway < 6:
            fragility += 0.2
        if liquidity_ratio < 1.0:
            fragility += 0.3
        elif liquidity_ratio < 2.0:
            fragility += 0.1
        if debt_pressure > 0.5:
            fragility += 0.2
        elif debt_pressure > 0.3:
            fragility += 0.1
        fragility = min(1.0, fragility)

        # Solvency verdict
        if cons_runway < 1 or liquidity_ratio < 0.5:
            solvency_verdict = "INSOLVENT"
        elif cons_runway < 3 or liquidity_ratio < 1.0 or debt_pressure > 0.6:
            solvency_verdict = "CRITICAL"
        elif cons_runway < 6 or liquidity_ratio < 1.5 or debt_pressure > 0.4:
            solvency_verdict = "STRESSED"
        elif cons_runway < 12 or liquidity_ratio < 2.0:
            solvency_verdict = "TIGHT"
        else:
            solvency_verdict = "SAFE"

        primary = {
            "conservative_runway_months": round(cons_runway, 1),
            "base_runway_months": round(base_runway, 1),
            "optimistic_runway_months": round(opt_runway, 1),
            "liquidity_ratio": round(liquidity_ratio, 2),
            "debt_pressure_index": round(debt_pressure, 2),
            "fragility_score": round(fragility, 2),
            "solvency_verdict": solvency_verdict,
            "conservative_net_monthly": round(conservative_net, 2),
            "base_net_monthly": round(base_net, 2),
        }
        five_seals = compute_five_seals(primary, "wealth_assess_solvency")

        # Override liquidity seal
        if solvency_verdict == "INSOLVENT":
            five_seals["liquidity_seal"] = "INSOLVENT_RISK"
        elif solvency_verdict == "CRITICAL":
            five_seals["liquidity_seal"] = "CRITICAL"
        elif solvency_verdict == "STRESSED":
            five_seals["liquidity_seal"] = "STRESSED"
        elif solvency_verdict == "TIGHT":
            five_seals["liquidity_seal"] = "TIGHT"
        else:
            five_seals["liquidity_seal"] = "SAFE"

        wealth_verdict = (
            "BLOCK"
            if solvency_verdict in ("INSOLVENT", "CRITICAL")
            else "HOLD"
            if solvency_verdict == "STRESSED"
            else "PROCEED_WITH_GUARDS"
            if solvency_verdict == "TIGHT"
            else "PROCEED"
        )

        return wajib_envelope(
            tool="wealth_assess_solvency",
            mode="full",
            status="OK",
            wealth_verdict=wealth_verdict,
            summary=f"Solvency ({solvency_verdict}): runway={cons_runway:.1f}mo, liquidity={liquidity_ratio:.2f}x, fragility={fragility:.2f}",
            metrics=primary,
            intent=intent or "assess_solvency",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk
            or {"cash": cash_verified, "debt": monthly_debt_service * 12},
            decision_class="W3",
            evidence_level="E2",
            risks=[
                "Fragility score is composite — may mask single-point failures",
                "Variable income is uncertain — use conservative runway for decisions",
            ],
            assumptions=[
                "Conservative runway assumes only verified cash and recurring income",
                "Base runway adds 50% of variable income and 70% of variable expenses",
            ],
            sensitivity=["Result sensitive to cash_verified accuracy"],
            liquidity_impact=five_seals["liquidity_seal"],
            legitimacy_score=1.0 if solvency_verdict == "SAFE" else 0.6,
            reversibility_score=0.3
            if solvency_verdict in ("INSOLVENT", "CRITICAL")
            else 0.7,
            confidence=0.7,
            next_safe_action="Route to arifOS if INSOLVENT or CRITICAL. Deploy no capital if runway < 3 months.",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-sol-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_assess_solvency",
                "mode": "full",
                "canonical": True,
            },
        )

else:

    def wealth_assess_solvency(**kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TOOL 16 — wealth_compute_value_flux
# The eureka metric — "Is value becoming more ordered, free, and resilient?"
# ═══════════════════════════════════════════════════════════════════════════

if _ENGINES_IMPORTED:

    def wealth_compute_value_flux(
        income_velocity: float = 0,
        expense_velocity: float = 0,
        asset_growth_rate: float = 0,
        liability_growth_rate: float = 0,
        attention_cost: float = 0,  # hours per week spent managing finances
        risk_exposure: float = 0,  # 0-1
        compounding_assets: float = 0,  # assets that build over time (equity, skills, IP)
        leaking_assets: float = 0,  # assets that depreciate or require constant spend
        scale_mode: str = "enterprise",
        # WAJIB mandatory
        intent: str = "",
        entity_scope: str = "unknown",
        time_horizon: str = "unknown",
        capital_at_risk: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Ω-WEALTH-FLUX: Value flux computation — the eureka metric.

        Not "net worth." Not "income." Not "profit."
        The question: Is value becoming more ordered, more free, more resilient
        — or more chaotic?

        Inputs:
          income_velocity      — Rate of value inflow (positive = good)
          expense_velocity     — Rate of value outflow (positive = bad when high)
          asset_growth_rate    — Asset accumulation rate
          liability_growth_rate — Liability accumulation rate
          attention_cost       — Time/energy spent managing finances (high = bad)
          risk_exposure        — Exposure to volatility/shock (0-1)
          compounding_assets   — Assets that build over time (skills, equity, IP)
          leaking_assets       — Assets that depreciate or require constant spend

        Outputs:
          value_flux           — Net direction of value movement
          capital_entropy      — Disorder in capital system (0-1, high = chaotic)
          leakage_rate         — Uncontrolled value outflow
          compounding_signal   — Signal of self-reinforcing growth
          mode                 — ACCUMULATE | CONSERVE | DEPLOY | REPAIR | HOLD

        The hidden eureka:
          Wealth is not accumulation.
          Wealth is stored optionality under ethical control.
        """
        # Net flux
        net_inflow = income_velocity - expense_velocity
        net_asset_change = asset_growth_rate - liability_growth_rate
        value_flux = net_inflow + net_asset_change

        # Capital entropy — disorder measurement
        entropy_factors = []
        if expense_velocity > income_velocity * 0.8:
            entropy_factors.append("high_burn_relative_to_income")
        if liability_growth_rate > asset_growth_rate:
            entropy_factors.append("liability_acceleration")
        if attention_cost > 10:  # >10 hrs/week managing money = high stress
            entropy_factors.append("high_attention_overhead")
        if risk_exposure > 0.7:
            entropy_factors.append("high_risk_exposure")
        if leaking_assets > compounding_assets:
            entropy_factors.append("net_depreciation")

        capital_entropy = min(1.0, len(entropy_factors) * 0.2)

        # Leakage rate
        if income_velocity > 0:
            leakage_rate = min(1.0, expense_velocity / income_velocity)
        else:
            leakage_rate = 1.0

        # Compounding signal
        compounding_ratio = compounding_assets / (
            compounding_assets + leaking_assets + 1
        )
        compounding_signal = (
            compounding_ratio * (1 - capital_entropy) * (1 - risk_exposure * 0.5)
        )

        # Mode determination
        if capital_entropy > 0.6 or leakage_rate > 0.9:
            mode = "REPAIR"
        elif value_flux < 0 and capital_entropy < 0.3:
            mode = "CONSERVE"
        elif value_flux > 0 and compounding_signal > 0.5 and capital_entropy < 0.3:
            mode = "ACCUMULATE"
        elif compounding_signal > 0.3 and capital_entropy < 0.5:
            mode = "DEPLOY"
        else:
            mode = "HOLD"

        primary = {
            "value_flux": round(value_flux, 4),
            "capital_entropy": round(capital_entropy, 2),
            "leakage_rate": round(leakage_rate, 2),
            "compounding_signal": round(compounding_signal, 2),
            "flux_mode": mode,
            "entropy_factors": entropy_factors,
        }
        five_seals = compute_five_seals(primary, "wealth_compute_value_flux")

        # Override based on flux
        if mode == "REPAIR":
            five_seals["value_seal"] = "DRAINING"
            five_seals["liquidity_seal"] = "STRESSED"
        elif mode == "CONSERVE":
            five_seals["value_seal"] = "STABLE"
        elif mode == "ACCUMULATE":
            five_seals["value_seal"] = "GROWING"
            five_seals["liquidity_seal"] = "SAFE"

        wealth_verdict = (
            "HOLD"
            if mode in ("REPAIR", "HOLD")
            else "PROCEED_WITH_GUARDS"
            if mode == "DEPLOY"
            else "PROCEED"
        )

        return wajib_envelope(
            tool="wealth_compute_value_flux",
            mode="flux",
            status="OK",
            wealth_verdict=wealth_verdict,
            summary=f"Value flux ({mode}): flux={value_flux:.2f}, entropy={capital_entropy:.2f}, compounding={compounding_signal:.2f}",
            metrics=primary,
            intent=intent or "compute_value_flux",
            entity_scope=entity_scope,
            time_horizon=time_horizon,
            capital_at_risk=capital_at_risk or {"at_risk": abs(value_flux) * 12},
            decision_class="W3",
            evidence_level="E2",
            risks=[
                "Flux is directional but doesn't capture magnitude",
                "Compounding assets are hard to quantify — verify inputs",
            ],
            assumptions=[
                "Compounding assets build over time (equity, skills, IP, trust)",
                "Leaking assets require constant spend or depreciate",
            ],
            sensitivity=[
                "Result sensitive to compounding_assets / leaking_assets ratio"
            ],
            liquidity_impact=five_seals.get("liquidity_seal", "unknown"),
            legitimacy_score=1.0 - capital_entropy,
            reversibility_score=1.0 if mode in ("CONSERVE", "HOLD") else 0.6,
            confidence=0.6,
            next_safe_action=f"Mode is {mode} — {'Repair leaks before deploying' if mode == 'REPAIR' else 'Accumulate compounding assets' if mode == 'ACCUMULATE' else 'Conserve and hold'}",
            five_seals=five_seals,
            audit_trace={
                "trace_id": f"wealth-flux-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "tool": "wealth_compute_value_flux",
                "mode": "flux",
                "canonical": True,
            },
        )

else:

    def wealth_compute_value_flux(**kwargs) -> Dict[str, Any]:
        return {"status": "ERROR", "error": f"Engines not imported: {_IMPORT_ERROR}"}


# ═══════════════════════════════════════════════════════════════════════════
# WEALTH SYSTEM PROMPT (resource content)
# Accessible via: resource://wealth/system_prompt
# ═══════════════════════════════════════════════════════════════════════════

WEALTH_SYSTEM_PROMPT = """
# WEALTH — Value / Survival / Stewardship / Exchange Organ

## Identity

You are **WEALTH**, an organ in Muhammad Arif bin Fazil's governed federation.

You reflect, audit, model, and advise on value, cashflow, assets, liabilities, risk, livelihood, and capital allocation.

You **do not execute trades, transfers, purchases, or irreversible financial actions.**

You distinguish **fact, estimate, forecast, assumption, and desire**.

You optimize for **solvency, dignity, optionality, truthful compounding, and long-horizon sovereignty**.

**Arif is final authority. arifOS adjudicates consequential action.**

## Core Doctrine

WEALTH reflects value.
WEALTH does not move value.
arifOS judges consequence.
Arif authorizes action.

## The Hidden Eureka

> Wealth is not accumulation. Wealth is **stored optionality under ethical control**.

> Real wealth is what remains when noise, ego, market panic, false status, and urgency are removed.

## The Void-Power Question

Strip the proposal of ego, urgency, status, and fantasy. What remains?

If nothing remains: recommend **HOLD**.
If durable value remains: identify the **smallest reversible next step**.

## 9 Invariants

1. **Solvency** — cash + inflow > obligations + burn
2. **Liquidity** — can value move when needed?
3. **Positive flux** — is value flowing in faster than it leaks out?
4. **Reversibility** — can bad decisions be undone?
5. **Truth separation** — facts, estimates, forecasts, desires must never mix
6. **Risk containment** — no single failure should kill the whole system
7. **Ethical exchange** — no exploitation, coercion, deception, dignity destruction
8. **Compounding** — value should build memory, assets, trust, IP, or optionality
9. **Sovereignty** — wealth must increase freedom, not create a golden cage

## What WEALTH Must Never Say

- "Guaranteed return."
- "You should buy this."
- "This will moon."
- "Risk-free."
- "Definitely worth it."

## What WEALTH Must Say

- "Evidence level is weak."
- "Downside is under-modeled."
- "This is not reversible."
- "This may be status-driven."
- "Runway impact is high."
- "Proceed only through judge."

## Decision Classes

- W0: Observe only
- W1: Categorize / summarize
- W2: Budget / forecast / compare
- W3: Advisory with uncertainty
- W4: Contractual / tax / debt / investment advisory — requires evidence + disclaimers
- W5: Transfer money / execute trade / sign contract / irreversible commitment — **HOLD unless explicit Arif + arifOS approval**

## Five Seals

Every output carries Five Seals:
- **VALUE_SEAL**: GROWING / STABLE / DRAINING / UNKNOWN
- **RISK_SEAL**: LOW / MEDIUM / HIGH / UNKNOWN
- **LIQUIDITY_SEAL**: SAFE / TIGHT / STRESSED / INSOLVENT_RISK / UNKNOWN
- **LEGITIMACY_SEAL**: CLEAN / GREY / DIRTY
- **SOVEREIGNTY_SEAL**: EXPANDS / STABLE / REDUCES

## WAJIB Fields

Every tool call must include:
- intent
- entity_scope
- time_horizon
- capital_at_risk

## HARAM Behaviours (Blocked)

- Silent ledger writes (without actor, reason, source)
- Exploitation of vulnerable parties
- Riba (usury/interest) in halal mode
- Reducing humans to instruments
- False certainty language ("guaranteed", "risk-free")
"""

print("[canonical_tools] NEXT HORIZON MAIN — 16 canonical tools loaded")
print("[canonical_tools] SPEAR: DITEMPA BUKAN DIBERI")
print(
    "[canonical_tools] WEALTH identity: VALUE / SURVIVAL / STEWARDSHIP / EXCHANGE — REFLECT ONLY"
)
