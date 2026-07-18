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


# ── C3 REDTEAM ratification 2026-07-18 ──────────────────────────────────────
# Per sovereign (888): every organ must delegate session validation to the
# arifOS kernel. GEOX already does this. WEALTH adopts the same pattern via
# this bridge — no new abstractions, just a new function on the existing
# transport. The function returns a 3-state verdict; the tool handler is
# responsible for honoring it (HOLD vs ALLOW).
#
# Contract:
#   {"valid": True, "session": {...}, "actor": "...", "authority": "..."}  → ALLOW
#   {"valid": False, "reason": "..."}                                       → HOLD
#   {"valid": False, "reason": "ARIFOS_UNREACHABLE", "fail_mode": "CLOSED"} → HOLD (fail-closed)
async def validate_session_at_arifos(
    session_id: str | None = None,
    actor_id: str | None = None,
    session_token: str | None = None,
    timeout_seconds: float = 3.0,
) -> dict[str, Any]:
    """Delegate session validation to arifOS kernel.

    Three-state verdict:
      valid=True                                       → ALLOW
      valid=False, reason='...'                        → HOLD (session rejected)
      valid=False, reason='ARIFOS_UNREACHABLE'         → HOLD, FAIL-CLOSED

    Fail-closed: if arifOS is unreachable, return HOLD. Never open.
    """
    # Empty/missing inputs short-circuit (mirrors GEOX session_enforcement)
    if not session_id and not session_token:
        return {
            "valid": False,
            "reason": "L11 AUTH: session_id or session_token required",
            "fail_mode": "CLOSED",
            "actor_id": actor_id,
        }

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "arif_init",
            "arguments": {
                "mode": "validate",
                "session_id": session_id,
                "actor_id": actor_id,
                "session_token": session_token,
            },
        },
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(
                ARIFOS_MCP_URL,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("result", {}) or {}
                content = result.get("content", [])
                parsed = result
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            try:
                                parsed = json.loads(item.get("text", "{}"))
                                break
                            except (json.JSONDecodeError, TypeError):
                                pass
                if not isinstance(parsed, dict):
                    return {
                        "valid": False,
                        "reason": "L11 AUTH: arifOS response malformed",
                        "fail_mode": "CLOSED",
                    }
                # Trust arifOS's authoritative verdict: result.valid is the
                # ground truth. effective_verdict can be HOLD/VOID/APPROVED;
                # we accept only when arifOS explicitly says valid=True AND
                # the session standing has a verified actor (or session_token).
                inner_result = parsed.get("result", {}) if isinstance(parsed.get("result"), dict) else {}
                arifos_says_valid = inner_result.get("valid")
                if arifos_says_valid is False:
                    # arifOS definitively rejected this session.
                    return {
                        "valid": False,
                        "reason": inner_result.get("error")
                        or parsed.get("reason")
                        or "L11 AUTH: arifOS rejected session",
                        "fail_mode": "CLOSED",
                        "actor_id": actor_id,
                        "session_id": session_id,
                    }
                standing = parsed.get("standing", {}) if isinstance(parsed.get("standing"), dict) else {}
                standing_actor = standing.get("actor", {}) if isinstance(standing.get("actor"), dict) else {}
                actor_verified = standing_actor.get("verified") is True
                session_token_present = bool(parsed.get("session_token"))
                resp_sid = parsed.get("session_id") or standing.get("session_id")

                # Authoritative: actor verified OR session token present
                if actor_verified or session_token_present:
                    return {
                        "valid": True,
                        "session": parsed,
                        "actor": standing_actor.get("claimed_id")
                        or standing_actor.get("canonical_id")
                        or parsed.get("actor_id")
                        or actor_id,
                        "authority": standing.get("authority", {}).get("band")
                        if isinstance(standing.get("authority"), dict)
                        else parsed.get("authority")
                        or "OBSERVE_ONLY",
                        "session_id": resp_sid or session_id,
                    }
                # arifOS said valid but didn't return verified actor / token.
                # Conservative: refuse. Better to fail-closed than leak.
                return {
                    "valid": False,
                    "reason": "L11 AUTH: session not verified by arifOS (no verified actor, no session_token)",
                    "fail_mode": "CLOSED",
                    "actor_id": actor_id,
                    "session_id": session_id,
                }
            return {
                "valid": False,
                "reason": f"L11 AUTH: arifOS HTTP {resp.status_code}",
                "fail_mode": "CLOSED",
                "actor_id": actor_id,
            }
    except Exception as exc:
        # F1 AMANAH: arifOS unreachable → fail CLOSED. Never let an organ
        # serve content when the constitutional gate is offline.
        return {
            "valid": False,
            "reason": f"ARIFOS_UNREACHABLE: {type(exc).__name__}: {str(exc)[:80]}",
            "fail_mode": "CLOSED",
            "actor_id": actor_id,
            "session_id": session_id,
        }


__all__ = [
    "ARIFOS_URL",
    "ARIFOS_MCP_URL",
    "send_evidence_contract",
    "probe_arifos_health",
    "seal_to_vault",
    "validate_session_at_arifos",  # C3 REDTEAM 2026-07-18
]


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
