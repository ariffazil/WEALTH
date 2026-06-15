"""
WEALTH Compatibility Layer — Legacy aliases and deprecated wrappers.

Provides backward compatibility during migration.
These tools delegate to the new wealth_core/ engines.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Any

# Map of legacy tool names to new canonical tools
LEGACY_ALIAS_MAP = {
    # v1 aliases → v2 canonical
    "wealth_health_check": "wealth_system_registry_status",
    "wealth_future_value": "wealth_time_discount",
    "wealth_present_expect": "wealth_emv_compute",
    "wealth_future_simulate": "wealth_monte_carlo",
    "wealth_survival_liquidity": "wealth_flow_check",
    "wealth_survival_leverage": "wealth_conservation_check",
    "wealth_info_value": "wealth_evoi_compute",
    "wealth_truth_validate": "wealth_asymmetry_check",
    "wealth_rule_enforce": "wealth_conservation_check",
    "wealth_allocate_optimize": "wealth_conservation_check",
    "wealth_game_coordinate": "wealth_power_audit",
    "wealth_sense_ingest": "wealth_system_registry_status",
    "wealth_past_record": "wealth_conservation_check",
    "wealth_future_steward": "wealth_wisdom_evaluate",
    "vault_write": "wealth_conservation_check",
    "vault_query": "wealth_conservation_check",
    # Domain-specific aliases
    "wealth_fx_rate": "wealth_system_registry_status",
    "wealth_commodity_price": "wealth_system_registry_status",
    "wealth_macro_indicator": "wealth_system_registry_status",
    "wealth_cashflow_track": "wealth_flow_check",
    "wealth_cashflow_summary": "wealth_flow_check",
    "wealth_runway_calculate": "wealth_runway_check",
    "wealth_net_worth_snapshot": "wealth_conservation_check",
    "wealth_epf_project": "wealth_conservation_check",
    "wealth_zakat_calculate": "wealth_conservation_check",
}


def resolve_alias(legacy_name: str) -> str | None:
    """Resolve a legacy tool name to its canonical equivalent."""
    return LEGACY_ALIAS_MAP.get(legacy_name)


def list_aliases() -> dict[str, str]:
    """List all legacy aliases and their canonical targets."""
    return dict(LEGACY_ALIAS_MAP)
