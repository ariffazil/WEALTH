"""
WEALTH Core — Pipeline Enforcement.

Ensures tool calls follow the canonical pipeline order:
  sense → mind → survival → reason → judge → vault

Blocks vaultwrite before 888 JUDGE.
Soft-warns on other out-of-order calls.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Optional

# Canonical pipeline stages in order
PIPELINE_STAGES = ["sense", "mind", "survival", "reason", "judge", "vault"]

# Tool → stage mapping
TOOL_STAGE_MAP = {
    # sense
    "wealth_system_registry_status": "sense",
    "wealth_market_data": "sense",
    "wealth_field_macro": "sense",
    # mind
    "wealth_agent_path": "mind",
    "wealth_confluence_check": "mind",
    # survival
    "wealth_flow_check": "survival",
    "wealth_runway_check": "survival",
    "wealth_conservation_check": "survival",
    # reason
    "wealth_compute_npv": "reason",
    "wealth_compute_irr": "reason",
    "wealth_emv_compute": "reason",
    "wealth_monte_carlo": "reason",
    "wealth_evoi_compute": "reason",
    "wealth_asymmetry_check": "reason",
    "wealth_wisdom_evaluate": "reason",
    "wealth_power_audit": "reason",
    "wealth_capture_scan": "reason",
    "wealth_stock_analysis": "reason",
    "wealth_personal_finance": "reason",
    "wealth_omni_wisdom": "reason",
    # judge
    # (no WEALTH tools — judge is arifOS's job)
    # vault
    "wealth_vault_write": "vault",
    "wealth_vault_query": "vault",
}

# Hard blocks: these must not execute before their prerequisite stage
HARD_BLOCKS = {
    "vault": "judge",  # vaultwrite must not execute before judge
}


def get_tool_stage(tool_name: str) -> Optional[str]:
    """Get the pipeline stage for a tool."""
    return TOOL_STAGE_MAP.get(tool_name)


def check_pipeline_order(
    tool_name: str,
    session_history: list[str],
) -> dict:
    """
    Check if a tool call respects pipeline order.
    
    Returns:
        allowed: bool — whether the call should proceed
        warning: str — soft warning (may proceed with warning)
        block: str — hard block (must not proceed)
        stage: str — the stage of this tool
        history_stages: list — stages seen so far
    """
    stage = get_tool_stage(tool_name)
    if stage is None:
        return {"allowed": True, "warning": "", "block": "", "stage": "unknown", "history_stages": []}

    # Map session history to stages
    history_stages = []
    for h_tool in session_history:
        h_stage = get_tool_stage(h_tool)
        if h_stage and h_stage not in history_stages:
            history_stages.append(h_stage)

    # Check hard blocks
    if stage in HARD_BLOCKS:
        required_stage = HARD_BLOCKS[stage]
        if required_stage not in history_stages:
            return {
                "allowed": False,
                "warning": "",
                "block": f"HARD BLOCK: {tool_name} (stage={stage}) requires {required_stage} to have been called first. "
                         f"History stages: {history_stages}",
                "stage": stage,
                "history_stages": history_stages,
            }

    # Check soft order
    stage_idx = PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else -1
    if stage_idx > 0:
        prev_stage = PIPELINE_STAGES[stage_idx - 1]
        if prev_stage not in history_stages and prev_stage != "judge":
            return {
                "allowed": True,
                "warning": f"SOFT WARN: {tool_name} (stage={stage}) called before {prev_stage}. "
                           f"Results may be incomplete.",
                "block": "",
                "stage": stage,
                "history_stages": history_stages,
            }

    return {"allowed": True, "warning": "", "block": "", "stage": stage, "history_stages": history_stages}
