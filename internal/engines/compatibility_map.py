# WEALTH MCP — Legacy Surface Compatibility Map
# Phase 1: Freeze legacy surface, map to canonical organs
# SPEAR: DITEMPA BUKAN DIBERI

LEGACY_TO_CANONICAL = {
    # ─── SYSTEM ────────────────────────────────────────────────────────────
    "mcp_health_check": {
        "canonical": "wealth_system_status",
        "mode": "health",
        "decision_class": "W0",
        "new_schema": "wealth_system_status(mode='health')",
        "sunset": "v2",
    },
    "wealth_system_registry_status": {
        "canonical": "wealth_system_status",
        "mode": "registry",
        "decision_class": "W0",
        "new_schema": "wealth_system_status(mode='registry')",
        "sunset": "v2",
    },
    # ─── CAPITAL EVALUATE ──────────────────────────────────────────────────
    "wealth_value_npv": {
        "canonical": "wealth_capital_evaluate",
        "mode": "npv",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='npv', ...)",
        "sunset": "v2",
    },
    "wealth_energy_irr": {
        "canonical": "wealth_capital_evaluate",
        "mode": "irr",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='irr', ...)",
        "sunset": "v2",
    },
    "wealth_density_pi": {
        "canonical": "wealth_capital_evaluate",
        "mode": "profitability_index",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='profitability_index', ...)",
        "sunset": "v2",
    },
    "wealth_time_payback": {
        "canonical": "wealth_capital_evaluate",
        "mode": "payback",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='payback', ...)",
        "sunset": "v2",
    },
    "wealth_time_discount": {
        "canonical": "wealth_capital_evaluate",
        "mode": "discount",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='discount', ...)",
        "sunset": "v2",
    },
    "wealth_energy_productivity": {
        "canonical": "wealth_capital_evaluate",
        "mode": "productivity",
        "decision_class": "W2",
        "new_schema": "wealth_capital_evaluate(mode='productivity', ...)",
        "sunset": "v2",
    },
    # ─── UNCERTAINTY EVALUATE ─────────────────────────────────────────────
    "wealth_expectation_emv": {
        "canonical": "wealth_uncertainty_evaluate",
        "mode": "emv",
        "decision_class": "W3",
        "new_schema": "wealth_uncertainty_evaluate(mode='emv', ...)",
        "sunset": "v2",
    },
    "wealth_probability_monte_carlo": {
        "canonical": "wealth_uncertainty_evaluate",
        "mode": "monte_carlo",
        "decision_class": "W3",
        "new_schema": "wealth_uncertainty_evaluate(mode='monte_carlo', ...)",
        "sunset": "v2",
    },
    "wealth_entropy_risk": {
        "canonical": "wealth_governance_risk",
        "mode": "risk_entropy",
        "decision_class": "W3",
        "new_schema": "wealth_governance_risk(mode='risk_entropy', ...)",
        "sunset": "v2",
    },
    # ─── INFORMATION VALUE ────────────────────────────────────────────────
    "wealth_signal_evoi": {
        "canonical": "wealth_information_value",
        "mode": "evoi",
        "decision_class": "W3",
        "new_schema": "wealth_information_value(mode='evoi', ...)",
        "sunset": "v2",
    },
    "wealth_signal_information": {
        "canonical": "wealth_information_value",
        "mode": "signal_quality",
        "decision_class": "W2",
        "new_schema": "wealth_information_value(mode='signal_quality', ...)",
        "sunset": "v2",
    },
    # ─── FINANCIAL POSITION ────────────────────────────────────────────────
    "wealth_flow_cashflow": {
        "canonical": "wealth_financial_position",
        "mode": "cashflow",
        "decision_class": "W2",
        "new_schema": "wealth_financial_position(mode='cashflow', ...)",
        "sunset": "v2",
    },
    "wealth_velocity_runway": {
        "canonical": "wealth_financial_position",
        "mode": "runway",
        "decision_class": "W2",
        "new_schema": "wealth_financial_position(mode='runway', ...)",
        "sunset": "v2",
    },
    "wealth_gravity_dscr": {
        "canonical": "wealth_financial_position",
        "mode": "dscr",
        "decision_class": "W2",
        "new_schema": "wealth_financial_position(mode='dscr', ...)",
        "sunset": "v2",
    },
    "wealth_mass_networth": {
        "canonical": "wealth_financial_position",
        "mode": "networth",
        "decision_class": "W2",
        "new_schema": "wealth_financial_position(mode='networth', ...)",
        "sunset": "v2",
    },
    "wealth_flow_liquidity": {
        "canonical": "wealth_financial_position",
        "mode": "liquidity",
        "decision_class": "W2",
        "new_schema": "wealth_financial_position(mode='liquidity', ...)",
        "sunset": "v2",
    },
    "wealth_inertia_leverage": {
        "canonical": "wealth_financial_position",
        "mode": "leverage",
        "decision_class": "W3",
        "new_schema": "wealth_financial_position(mode='leverage', ...)",
        "sunset": "v2",
    },
    # ─── MARKET ANALYZE ───────────────────────────────────────────────────
    "wealth_gradient_price": {
        "canonical": "wealth_market_analyze",
        "mode": "price_gradient",
        "decision_class": "W2",
        "new_schema": "wealth_market_analyze(mode='price_gradient', ...)",
        "sunset": "v2",
    },
    "wealth_field_macro": {
        "canonical": "wealth_market_analyze",
        "mode": "macro_field",
        "decision_class": "W2",
        "new_schema": "wealth_market_analyze(mode='macro_field', ...)",
        "sunset": "v2",
    },
    # ─── POWER MAP ────────────────────────────────────────────────────────
    "wealth_game_coordination": {
        "canonical": "wealth_power_map",
        "mode": "coordination_game",
        "decision_class": "W3",
        "new_schema": "wealth_power_map(mode='coordination_game', ...)",
        "sunset": "v2",
    },
    # ─── GOVERNANCE RISK ──────────────────────────────────────────────────
    "wealth_governance_verdict": {
        "canonical": "wealth_governance_risk",
        "mode": "verdict",
        "decision_class": "W4",
        "new_schema": "wealth_governance_risk(mode='verdict', ...)",
        "sunset": "v2",
    },
    "wealth_boundary_governance": {
        "canonical": "wealth_governance_risk",
        "mode": "boundary",
        "decision_class": "W4",
        "new_schema": "wealth_governance_risk(mode='boundary', ...)",
        "sunset": "v2",
    },
    "wealth_conservation_capital": {
        "canonical": "wealth_governance_risk",
        "mode": "capital_conservation",
        "decision_class": "W3",
        "new_schema": "wealth_governance_risk(mode='capital_conservation', ...)",
        "sunset": "v2",
    },
    "wealth_entropy_audit": {
        "canonical": "wealth_governance_risk",
        "mode": "audit_entropy",
        "decision_class": "W3",
        "new_schema": "wealth_governance_risk(mode='audit_entropy', ...)",
        "sunset": "v2",
    },
    "wealth_boundary_floors": {
        "canonical": "wealth_governance_risk",
        "mode": "boundary",
        "decision_class": "W4",
        "new_schema": "wealth_governance_risk(mode='boundary', ...)",
        "sunset": "v2",
    },
    # ─── LEDGER ──────────────────────────────────────────────────────────
    "wealth_ledger_query": {
        "canonical": "wealth_ledger",
        "mode": "query",
        "decision_class": "W1",
        "new_schema": "wealth_ledger(mode='query', ...)",
        "sunset": "v2",
    },
    "wealth_ledger_write": {
        "canonical": "wealth_ledger",
        "mode": "write",
        "decision_class": "W4",
        "new_schema": "wealth_ledger(mode='write', ...)",
        "sunset": "v2",
    },
    "wealth_hysteresis_ledger": {
        "canonical": "wealth_ledger",
        "mode": "hysteresis",
        "decision_class": "W2",
        "new_schema": "wealth_ledger(mode='hysteresis', ...)",
        "sunset": "v2",
    },
    "wealth_ledger_init": {
        "canonical": "wealth_ledger",
        "mode": "init",
        "decision_class": "W0",
        "new_schema": "wealth_ledger(mode='init', ...)",
        "sunset": "v2",
    },
    "wealth_ledger_record": {
        "canonical": "wealth_ledger",
        "mode": "record",
        "decision_class": "W3",
        "new_schema": "wealth_ledger(mode='record', ...)",
        "sunset": "v2",
    },
    "wealth_ledger_snapshot": {
        "canonical": "wealth_ledger",
        "mode": "snapshot",
        "decision_class": "W2",
        "new_schema": "wealth_ledger(mode='snapshot', ...)",
        "sunset": "v2",
    },
    # ─── PREFERENCE RANK ──────────────────────────────────────────────────
    "wealth_preference_rank": {
        "canonical": "wealth_preference_rank",
        "mode": "rank",
        "decision_class": "W2",
        "new_schema": "wealth_preference_rank(mode='rank', ...)",
        "sunset": "v2",
    },
    # ─── INEQUALITY KERNEL ────────────────────────────────────────────────
    "wealth_inequality_kernel": {
        "canonical": "wealth_inequality_kernel",
        "mode": "diagnose",
        "decision_class": "W3",
        "new_schema": "wealth_inequality_kernel(mode='diagnose', ...)",
        "sunset": "v2",
    },
    # ─── KERNEL ROUTE ─────────────────────────────────────────────────────
    "wealth_agent_path": {
        "canonical": "wealth_kernel_route",
        "mode": "path",
        "decision_class": "W1",
        "new_schema": "wealth_kernel_route(mode='path', ...)",
        "sunset": "v2",
    },
    # ─── SYNTHESIZE ──────────────────────────────────────────────────────
    "wealth_synthesize": {
        "canonical": "wealth_synthesize",
        "mode": "synthesis",
        "decision_class": "W3",
        "new_schema": "wealth_synthesize(mode='synthesis', ...)",
        "sunset": None,  # Keep permanently — final integrator
    },
}

# ─── CANONICAL 13-TOOL SURFACE ────────────────────────────────────────────
CANONICAL_SURFACE = [
    "wealth_system_status",
    "wealth_capital_evaluate",
    "wealth_uncertainty_evaluate",
    "wealth_information_value",
    "wealth_financial_position",
    "wealth_market_analyze",
    "wealth_power_map",
    "wealth_governance_risk",
    "wealth_ledger",
    "wealth_preference_rank",
    "wealth_inequality_kernel",
    "wealth_kernel_route",
    "wealth_synthesize",
]

# ─── DECISION CLASS THRESHOLDS ────────────────────────────────────────────
# W0-W1: answer directly
# W2: answer with assumptions and guards
# W3: require risk register and alternatives
# W4: require governance handoff and review framing
# W5: HOLD unless arifOS JUDGE and explicit Arif approval
DECISION_CLASS_THRESHOLDS = {
    "W0": {"self_authority": True, "handoff": False, "arif_approval": False},
    "W1": {"self_authority": True, "handoff": False, "arif_approval": False},
    "W2": {"self_authority": True, "handoff": False, "arif_approval": False},
    "W3": {"self_authority": True, "handoff": True, "arif_approval": False},
    "W4": {"self_authority": False, "handoff": True, "arif_approval": True},
    "W5": {"self_authority": False, "handoff": True, "arif_approval": True},
}

# ─── FIVE SEALS DEFINITION ────────────────────────────────────────────────
FIVE_SEALS = {
    "VALUE_SEAL": {
        "CREATE": "value created by this action",
        "PRESERVE": "existing value maintained",
        "TRANSFER": "value moved, not created or destroyed",
        "DESTROY": "value intentionally or unintentionally destroyed",
        "UNKNOWN": "insufficient information to determine",
    },
    "RISK_SEAL": {
        "LOW": "downside is bounded and acceptable",
        "MEDIUM": "downside is meaningful but manageable",
        "HIGH": "significant downside possible",
        "CRITICAL": "existential or irreversible downside risk",
        "UNKNOWN": "risk cannot be assessed with available evidence",
    },
    "LIQUIDITY_SEAL": {
        "SAFE": "cash timing comfortably met",
        "TIGHT": "cash timing achievable with care",
        "STRESSED": "cash timing uncertain, may need intervention",
        "INSOLVENT_RISK": "unable to meet obligations as they fall due",
        "UNKNOWN": "liquidity position cannot be determined",
    },
    "LEGITIMACY_SEAL": {
        "CLEAN": "transparent, consent-based, auditable, institutionally defensible",
        "GREY": "ambiguous legitimacy, requires review before proceeding",
        "DIRTY": "deceptive, coercive, hidden liability, or illegitimate",
        "UNKNOWN": "legitimacy cannot be assessed with available evidence",
    },
    "SOVEREIGNTY_SEAL": {
        "INCREASES": "increases freedom of action",
        "PRESERVES": "maintains existing freedom of action",
        "REDUCES": "reduces freedom of action without adequate compensation",
        "CAPTURES": "creates lock-in, dependency, or obligation that reduces future choices",
        "UNKNOWN": "impact on sovereignty cannot be determined",
    },
}

# ─── WAJIB OUTPUT ENVELOPE ────────────────────────────────────────────────
WAJIB_OUTPUT_FIELDS = [
    "status",
    "wealth_verdict",
    "summary",
    "metrics",
    "risks",
    "assumptions_used",
    "sensitivity",
    "liquidity_impact",
    "legitimacy_score",
    "reversibility_score",
    "confidence",
    "next_safe_action",
    "handoff_recommendation",
    "audit_trace",
    # Five Seals
    "value_seal",
    "risk_seal",
    "liquidity_seal",
    "legitimacy_seal",
    "sovereignty_seal",
    # WAJIB mandatory fields
    "decision_class",
    "evidence_level",
    "entity_scope",
    "time_horizon",
    "capital_at_risk",
    "reversibility",
    "counterparty_map",
    "handoff_required",
]

EVIDENCE_LEVELS = {
    "E0": "assumption — no verification",
    "E1": "user-stated — claimed but not documented",
    "E2": "document-backed — supported by documents",
    "E3": "ledger-backed — confirmed by financial records",
    "E4": "externally verified — third-party confirmed",
    "E5": "audited — legally/ professionally confirmed",
}

REVERSIBILITY_LEVELS = {
    "R1.0": "fully reversible — no residual cost or trace",
    "R0.7": "mostly reversible — minor cost or effort to undo",
    "R0.3": "costly to reverse — significant time, cost, or effort required",
    "R0.0": "irreversible — cannot be undone, permanent effect",
    "unknown": "reversibility cannot be determined",
}

VERDICTS = ["PROCEED", "PROCEED_WITH_GUARDS", "DEFER", "HOLD", "BLOCK", "UNKNOWN"]

print(
    f"[COMPAT] {len(LEGACY_TO_CANONICAL)} legacy tools mapped to {len(CANONICAL_SURFACE)} canonical tools"
)
print(f"[COMPAT] Canonical surface: {', '.join(CANONICAL_SURFACE)}")
