"""
WEALTH Governance Metadata — per-tool constitutional floor binding.
ZEN 2026-06-30: Every canonical tool now has explicit floor metadata.
"""

from __future__ import annotations

# Maps tool_name -> list of floors that gate this tool.
# Derivation: arifOS F1-F13, WEALTH-specific risk profile per tool.
CANONICAL_FLOORS: dict[str, list[str]] = {
    # Live public capital surface
    "capital_primitive": ["F1", "F2", "F7", "F11"],
    "capital_health": ["F1", "F2", "F4", "F7", "F11", "F13"],
    "capital_diagnose": ["F1", "F2", "F4", "F6", "F7", "F9", "F11", "F13"],
    # capital_wisdom DELETED 2026-08-06 — M0 audit, F13 directive
    "capital_market": ["F1", "F2", "F7", "F11"],
    "capital_ledger": ["F1", "F2", "F4", "F7", "F11", "F13"],
    "capital_registry": ["F1", "F2", "F7", "F11"],
    "capital_entropy": ["F1", "F2", "F4", "F6", "F7", "F9", "F11", "F13"],
    "wealth_judge_handoff": ["F1", "F2", "F4", "F7", "F11", "F13"],
    "wealth_bid_surface": ["F1", "F2", "F4", "F7", "F11"],
    # Core primitives — computational only, low risk
    "wealth_compute_npv": ["F1", "F2", "F7", "F11"],
    "wealth_compute_irr": ["F1", "F2", "F7", "F11"],
    "wealth_compute_emv": ["F1", "F2", "F7", "F11"],
    "wealth_compute_evoi": ["F1", "F2", "F7", "F11"],
    "wealth_monte_carlo_simulate": ["F1", "F2", "F7", "F11"],
    # Capital health — medium risk
    "wealth_conservation_check": ["F1", "F2", "F4", "F7", "F11"],
    "wealth_flow_check": ["F1", "F2", "F4", "F7", "F11"],
    "wealth_runway_check": ["F1", "F2", "F4", "F7", "F11", "F13"],
    # Risk assessment — higher risk
    "wealth_asymmetry_check": ["F1", "F2", "F4", "F6", "F7", "F11"],
    "wealth_confluence_check": ["F1", "F2", "F4", "F7", "F11"],
    "wealth_fiscal_breakeven": ["F1", "F2", "F4", "F6", "F7", "F11", "F13"],
    # Wisdom and power — highest risk
    "wealth_wisdom_evaluate": ["F1", "F2", "F4", "F5", "F6", "F7", "F9", "F11", "F13"],
    "wealth_power_audit": ["F1", "F2", "F4", "F6", "F7", "F9", "F11", "F13"],
    "wealth_epistemic_audit": ["F1", "F2", "F4", "F7", "F11"],
    "wealth_capture_scan": ["F1", "F2", "F4", "F6", "F7", "F11"],
    # Collapse detection — critical
    "wealth_collapse_signature_scan": [
        "F1",
        "F2",
        "F4",
        "F6",
        "F7",
        "F9",
        "F11",
        "F13",
    ],
    "wealth_beautiful_mouse_scan": ["F1", "F2", "F4", "F6", "F7", "F9", "F11", "F13"],
    # Domain engines — medium risk
    "wealth_stock_analysis": ["F1", "F2", "F4", "F6", "F7", "F11", "F13"],
    "wealth_personal_finance": ["F1", "F2", "F4", "F6", "F7", "F11", "F13"],
    "wealth_market_data": ["F1", "F2", "F7", "F11"],
    "wealth_survival_engine": ["F1", "F2", "F4", "F6", "F7", "F11", "F13"],
    # Synthesis and governance — high risk, requires sovereignty
    # C8 2026-08-06: wealth_omni_wisdom — legacy alias, capital_wisdom deleted
    "wealth_boundary_governance": ["F1", "F2", "F4", "F6", "F7", "F9", "F11", "F13"],
    "wealth_arifos_judge_handoff": ["F1", "F2", "F4", "F7", "F11", "F13"],
    "wealth_vault_write": ["F1", "F2", "F4", "F7", "F11", "F13"],
    "wealth_vault_query": ["F1", "F2", "F7", "F11"],
    # Meta/introspection — low risk
    "wealth_registry_status": ["F1", "F2", "F7", "F11"],
    "wealth_agent_path": ["F1", "F2", "F7", "F11"],
}

# Alias floor binding — maps aliases to the floors of their canonical target
ALIAS_FLOORS: dict[str, list[str]] = {
    "wealth_system_registry_status": CANONICAL_FLOORS["wealth_registry_status"],
    "wealth_emv_compute": CANONICAL_FLOORS["wealth_compute_emv"],
    "wealth_monte_carlo": CANONICAL_FLOORS["wealth_monte_carlo_simulate"],
    "wealth_evoi_compute": CANONICAL_FLOORS["wealth_compute_evoi"],
    "wealth_reason_agent": CANONICAL_FLOORS["wealth_agent_path"],
}

# NAMING STANDARD (2026-07-31): wealth_* → capital_* canonical alias map.
# Tools prefixed with wealth_* are aliased under capital_* for agent discoverability.
# When tools/list returns, agents scanning for capital_* can also discover these.
# All new WEALTH tools MUST use capital_* prefix per /root/AAA/docs/MCP_NAMING_STANDARD.md.
WEALTH_ALIAS_MAP: dict[str, str] = {
    "wealth_judge_handoff": "capital_judge_handoff",
    "wealth_bid_surface": "capital_bid_surface",
    "wealth_institutional_stress_index": "capital_institutional_stress_index",
    "wealth_governance_capacity": "capital_governance_capacity",
    "wealth_cascade_model": "capital_cascade_model",
    "wealth_external_exploitation_detect": "capital_external_exploitation_detect",
    # C8 2026-08-06: wealth_omni_wisdom alias — capital_wisdom deleted
    "wealth_boundary_governance": "capital_boundary_governance",
    "wealth_stock_analysis": "capital_stock_analysis",
    "wealth_personal_finance": "capital_personal_finance",
    "wealth_market_data": "capital_market_data",
    "wealth_survival_engine": "capital_survival_engine",
    "wealth_collapse_signature_scan": "capital_collapse_signature_scan",
    "wealth_beautiful_mouse_scan": "capital_beautiful_mouse_scan",
    "wealth_power_audit": "capital_power_audit",
    "wealth_epistemic_audit": "capital_epistemic_audit",
    "wealth_capture_scan": "capital_capture_scan",
    # "wealth_wisdom_evaluate" DELETED 2026-08-06 — capital_wisdom removed
    "wealth_fiscal_breakeven": "capital_fiscal_breakeven",
    "wealth_asymmetry_check": "capital_asymmetry_check",
    "wealth_confluence_check": "capital_confluence_check",
    "wealth_conservation_check": "capital_conservation_check",
    "wealth_flow_check": "capital_flow_check",
    "wealth_runway_check": "capital_runway_check",
    "wealth_compute_npv": "capital_compute_npv",
    "wealth_compute_irr": "capital_compute_irr",
    "wealth_compute_emv": "capital_compute_emv",
    "wealth_compute_evoi": "capital_compute_evoi",
    "wealth_monte_carlo_simulate": "capital_monte_carlo_simulate",
    "wealth_arifos_judge_handoff": "capital_arifos_judge_handoff",
    "wealth_vault_write": "capital_vault_write",
    "wealth_vault_query": "capital_vault_query",
    "wealth_registry_status": "capital_registry_status",
    "wealth_agent_path": "capital_agent_path",
}

# Reverse map: canonical capital_* → source wealth_* name
CAPITAL_ALIAS_REVERSE: dict[str, str] = {v: k for k, v in WEALTH_ALIAS_MAP.items()}


def resolve_tool_name(name: str) -> str:
    """Resolve a tool name through the alias map. Returns canonical name if aliased."""
    return WEALTH_ALIAS_MAP.get(name, name)


def get_tool_floors(tool_name: str) -> list[str]:
    """Return the constitutional floors applicable to this tool."""
    if tool_name in CANONICAL_FLOORS:
        return CANONICAL_FLOORS[tool_name]
    if tool_name in ALIAS_FLOORS:
        return ALIAS_FLOORS[tool_name]
    return ["F1", "F2", "F11"]  # minimum default
