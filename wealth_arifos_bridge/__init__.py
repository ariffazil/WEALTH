"""
WEALTH arifOS Bridge — Transport to arifOS kernel.

Connects WEALTH to arifOS 888_JUDGE / VAULT999.
Evidence Contract sender, health probe, vault writer.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

# arifOS kernel endpoint
ARIFOS_URL = "http://127.0.0.1:8088"
ARIFOS_MCP_URL = f"{ARIFOS_URL}/mcp"


async def send_evidence_contract(
    tool_name: str,
    domain: str,
    result: dict,
    epistemic_tag: str = "DERIVED",
    claim_state: str = "DRAFT",
    evidence_quality: str = "MODERATE",
    session_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    """
    Send an Evidence Contract to arifOS.
    This is what WEALTH sends after computing a judgment-eligible result.
    """
    contract = {
        "tool_name": tool_name,
        "domain": domain,
        "epistemic_tag": epistemic_tag,
        "claim_state": claim_state,
        "evidence_quality": evidence_quality,
        "result_summary": json.dumps(result, default=str)[:500],
        "numerical_claims": _extract_numerical(result),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requires_888_hold": _requires_hold(result, epistemic_tag),
    }
    if session_id:
        contract["session_id"] = session_id
    if actor_id:
        contract["actor_id"] = actor_id

    return contract


async def probe_arifos_health() -> dict:
    """
    Probe arifOS kernel health.
    Returns status: ALIVE, DEGRADED_NOT_FAILED, or UNREACHABLE.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{ARIFOS_URL}/health")
            if resp.status_code == 200:
                return {"status": "ALIVE", "details": resp.json()}
            else:
                return {"status": "DEGRADED_NOT_FAILED", "http_status": resp.status_code}
    except Exception as e:
        return {"status": "UNREACHABLE", "error": str(e)}


async def seal_to_vault(
    payload: str,
    actor_id: str = "WEALTH",
    session_id: str | None = None,
    ack_irreversible: bool = False,
) -> dict:
    """
    Seal a computation result to VAULT999.
    Only for SEALED claims. Requires ack_irreversible=True.
    Routes to arifOS arif_vault_seal tool.
    """
    if not ack_irreversible:
        return {
            "status": "BLOCKED",
            "reason": "ack_irreversible=False — F1 AMANAH gate",
        }

    # This would route to arifOS via MCP
    # For now, return the contract that would be sent
    return {
        "status": "READY_TO_SEAL",
        "payload": payload[:200],
        "actor_id": actor_id,
        "session_id": session_id,
        "ack_irreversible": ack_irreversible,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "Route to arifOS arif_vault_seal for actual sealing",
    }


def _extract_numerical(result: dict) -> dict:
    """Extract numerical claims from result for evidence contract."""
    numerical = {}
    if isinstance(result, dict):
        for k, v in result.items():
            if isinstance(v, (int, float)):
                numerical[k] = v
    return numerical


def _requires_hold(result: dict, epistemic_tag: str) -> bool:
    """Determine if this result requires 888_HOLD review."""
    # SPECULATED or ASSUMED claims need review
    if epistemic_tag in ("SPECULATED", "ASSUMED"):
        return True
    # Large numbers need review
    if isinstance(result, dict):
        for v in result.values():
            if isinstance(v, (int, float)) and abs(v) > 1_000_000:
                return True
    return False
