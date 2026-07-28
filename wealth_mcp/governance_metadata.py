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
    "capital_wisdom": ["F1", "F2", "F4", "F5", "F6", "F7", "F9", "F11", "F13"],
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
    "wealth_omni_wisdom": ["F1", "F2", "F4", "F5", "F6", "F7", "F9", "F11", "F13"],
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


def get_tool_floors(tool_name: str) -> list[str]:
    """Return the constitutional floors applicable to this tool."""
    if tool_name in CANONICAL_FLOORS:
        return CANONICAL_FLOORS[tool_name]
    if tool_name in ALIAS_FLOORS:
        return ALIAS_FLOORS[tool_name]
    return ["F1", "F2", "F11"]  # minimum default
