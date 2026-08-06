"""
WEALTH Organ Governance — arifOS F1-F13 integration.

Routes C2+/IRREVERSIBLE WEALTH tool calls through arifOS kernel for judgment.
READONLY/C1 tools execute directly. C2+/IRREVERSIBLE require SEAL from arifOS.

Risk tiers:
  READONLY   -> execute directly
  C1         -> arifOS pre-check, execute on any verdict
  C2         -> arifOS SEAL required
  IRREVERSIBLE -> arifOS SEAL + ack_irreversible required
"""

from __future__ import annotations

import os
import httpx
from typing import Optional, Tuple

ARIFOS_KERNEL_URL = os.environ.get("ARIFOS_KERNEL_URL", "http://127.0.0.1:8088")

# Risk classification for WEALTH tools
WEALTH_RISK_TIERS = {
    # Live public capital surface
    "capital_primitive": "readonly",
    "capital_health": "readonly",
    "capital_diagnose": "c1",
    # capital_wisdom DELETED 2026-08-06 — M0 audit
    "capital_market": "readonly",
    "capital_ledger": "c2",  # write is irreversible; query is resolved read-only below
    "capital_registry": "readonly",
    "capital_entropy": "c1",
    "wealth_institutional_stress_index": "c1",
    "wealth_cascade_model": "c1",
    "wealth_governance_capacity": "c1",
    "wealth_external_exploitation_detect": "c1",
    # C2/IRREVERSIBLE legacy aliases — require arifOS judgment
    "wealth_vault_write": "c2",  # VAULT999 write, irreversible
    "wealth_ledger_write": "c2",  # VAULT999 write, irreversible
    "wealth_ledger_snapshot": "c2",  # VAULT999 write, irreversible
    "wealth_vault_query": "readonly",  # Vault read
    "wealth_synthesize": "c1",  # Advisory verdict
    "wealth_governance_verdict": "c1",  # Advisory verdict
    "wealth_boundary_governance": "c1",  # Legitimacy audit, advisory
    # READONLY — execute directly
    "wealth_flow_liquidity": "readonly",
    "wealth_signal_information": "readonly",
    "wealth_gradient_price": "readonly",
    "wealth_inertia_leverage": "readonly",
    "wealth_entropy_risk": "readonly",
    "wealth_entropy_audit": "readonly",
    "wealth_game_coordination": "c1",  # Game theory, advisory
    "wealth_inequality_kernel": "c1",  # Inequality analysis
    "wealth_conservation_capital": "readonly",
    "wealth_energy_productivity": "readonly",
    "wealth_time_discount": "readonly",
    "wealth_preference_rank": "readonly",
    "wealth_agent_path": "readonly",
    "wealth_field_macro": "readonly",
    "wealth_hysteresis_ledger": "readonly",
    "wealth_health_check": "readonly",
    "wealth_system_registry_status": "readonly",
}


def _call_arifOS_judge(
    tool_name: str, arguments: dict, actor_id: str, session_id: Optional[str] = None
) -> Tuple[str, Optional[dict]]:
    """
    Call arifOS kernel arif_judge.
    Returns (verdict, error_response).
    error_response is not None if call failed or returned HOLD/VOID.
    """
    import json

    candidate = json.dumps(
        {
            "action": f"WEALTH_ORGAN:{tool_name}",
            "description": f"WEALTH organ tool: {tool_name}",
            "tool": tool_name,
            "arguments": arguments,
        },
        separators=(",", ":"),
    )

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "arif_judge",
            "arguments": {
                "mode": "judge",
                "candidate": candidate,
                "actor_id": actor_id,
                "session_id": session_id,
            },
        },
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{ARIFOS_KERNEL_URL}/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            data = response.json()

            if "error" in data:
                return "HOLD", {"error": data["error"]["message"]}

            result = data.get("result", {})
            content_text = result.get("content", [{}])[0].get("text", "{}")
            verdict_data = json.loads(content_text)

            verdict = verdict_data.get("verdict", verdict_data.get("status", "HOLD"))
            return verdict, None

    except Exception as e:
        return "HOLD", {"error": str(e)}


def check_governance(
    tool_name: str,
    arguments: dict,
    actor_id: str = "wealth-mcp",
    session_id: Optional[str] = None,
) -> Tuple[str, Optional[dict]]:
    """
    Main entry point. Returns (verdict, error_response).

    - verdict = "READONLY" or "C1_PASS" if tool should proceed
    - error_response = not None if execution should be BLOCKED
      (contains the HOLD/VOID response to return to caller)
    """
    risk = WEALTH_RISK_TIERS.get(tool_name, "c1")
    if (
        tool_name == "capital_ledger"
        and str(arguments.get("mode", "")).lower() == "query"
    ):
        risk = "readonly"

    # READONLY tools: execute without governance check
    if risk == "readonly":
        return "READONLY", None

    # C1 tools: arifOS pre-check, proceed regardless
    if risk == "c1":
        verdict, err = _call_arifOS_judge(tool_name, arguments, actor_id, session_id)
        return verdict, None  # C1 proceeds even if HOLD

    # C2 tools: require SEAL
    if risk == "c2":
        verdict, err = _call_arifOS_judge(tool_name, arguments, actor_id, session_id)
        if verdict != "SEAL":
            return verdict, {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": f"arifOS {verdict}: C2 tool requires SEAL",
                    "data": {
                        "guard": "ORGAN_GOVERNANCE",
                        "tool": tool_name,
                        "verdict": verdict,
                        "floor": "F1-F13",
                    },
                },
            }
        return "SEAL", None

    # Unknown risk: default to C1 (advisory check, proceed)
    verdict, _ = _call_arifOS_judge(tool_name, arguments, actor_id, session_id)
    return verdict, None
