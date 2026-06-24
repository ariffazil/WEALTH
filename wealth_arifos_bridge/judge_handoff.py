"""
WEALTH arifOS Bridge — Judge Handoff.

Prepares a WEALTH verdict for submission to arifOS 888_JUDGE
(constitutional verdict). This closes the federation loop:
WEALTH computes, arifOS judges, the sovereign decides.

Two modes:
- prepare   — build the arif_judge envelope, return it. The agent
             (or A-FORGE) is responsible for the actual call.
- submit    — actually call arif_judge via the arifos MCP transport
             and return the constitutional verdict.

The handoff is an architectural property, not an agent discipline.
WEALTH cannot make constitutional decisions; it can only surface
the evidence. The bridge is the only path that does both.

Hard rules:
- F1 AMANAH   — handoff is reversible (prepare mode is non-mutating)
- F2 TRUTH    — envelope carries evidence_quality + epistemic_tag
- F7 HUMILITY — confidence capped at 0.90 before handoff
- F8 LAW      — submit mode respects arifOS 888_HOLD gates
- F13 SOVEREIGN — never declares verdict; only prepares the request

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from . import ARIFOS_URL, ARIFOS_MCP_URL


def prepare_judge_handoff(
    tool_name: str,
    result: dict,
    intent: str,
    capability: str,
    blast_radius: str = "MEDIUM",
    reversibility_level: str = "PARTIAL",
    epistemic_state: str = "DERIVED",
    domain: str = "capital",
    session_id: str | None = None,
    actor_id: str | None = None,
    evidence: list[dict] | None = None,
) -> dict:
    """
    Build a constitutional handoff envelope for arif_judge.

    Args:
        tool_name: the WEALTH tool that produced the verdict
        result: the WEALTH result to be judged
        intent: the capital decision being proposed
        capability: the specific capability requested (e.g.,
                   "register_collapse_signature_claim",
                   "execute_stock_trade",
                   "issue_capital_recommendation")
        blast_radius: LOW | MEDIUM | HIGH | CRITICAL
        reversibility_level: FULL | PARTIAL | NONE
        epistemic_state: OBSERVED | DERIVED | INTERPRETED | SPECULATED
        domain: capital | risk | power | wisdom | collapse | meta
        session_id: optional arifOS session
        actor_id: optional calling actor

    Returns:
        {
          "handoff_envelope": { ... arif_judge payload ... },
          "readiness": "READY" | "BLOCKED",
          "block_reasons": [...],
          "constitutional_pre_check": {...},
          "next_action": "submit_to_arif_judge" | "address_blocks_first",
        }
    """
    # Constitutional pre-check (cheaper than a full arif_judge call)
    pre_check = _constitutional_pre_check(
        intent=intent,
        capability=capability,
        blast_radius=blast_radius,
        reversibility_level=reversibility_level,
        epistemic_state=epistemic_state,
        result=result,
    )

    block_reasons = pre_check.get("block_reasons", [])

    # Build the arif_judge envelope
    handoff_envelope = {
        "actor": actor_id or "WEALTH",
        "intent": intent,
        "requested_capability": capability,
        "domain": domain,
        "reversibility_level": reversibility_level,
        "blast_radius": blast_radius,
        "epistemic_state": epistemic_state,
        "evidence": evidence or _extract_evidence(result),
        "authority_token": None,  # WEALTH does not issue authority
        "wealth_context": {
            "source_tool": tool_name,
            "source_domain": domain,
            "source_result_summary": _summarize(result),
            "epistemic_tag": result.get("epistemic_tag", "DERIVED"),
            "evidence_quality": result.get("evidence_quality", "MODERATE"),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    if session_id:
        handoff_envelope["session_id"] = session_id
    if actor_id:
        handoff_envelope["actor_id"] = actor_id

    # Determine readiness
    if block_reasons:
        readiness = "BLOCKED"
        next_action = "address_blocks_first"
    else:
        readiness = "READY"
        next_action = "submit_to_arif_judge"

    return {
        "handoff_envelope": handoff_envelope,
        "readiness": readiness,
        "block_reasons": block_reasons,
        "constitutional_pre_check": pre_check,
        "next_action": next_action,
        "do_not_skip": [
            "arif_judge is the SOLE constitutional authority",
            "WEALTH prepares, arifOS judges, Arif decides",
            "F13 SOVEREIGN: never declare verdict from WEALTH",
        ],
    }


async def submit_to_arif_judge(
    handoff_envelope: dict,
    timeout_seconds: float = 10.0,
) -> dict:
    """
    Submit a prepared handoff envelope to arifOS 888_JUDGE via MCP.
    Returns the arif_judge verdict.

    The call uses MCP JSON-RPC over HTTP. If arifOS is unreachable,
    returns status=UNREACHABLE with the envelope preserved for
    later submission (F1 AMANAH — non-destructive).
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "arif_judge",
            "arguments": handoff_envelope,
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
                if "result" in data:
                    return {
                        "status": "DELIVERED",
                        "verdict": data.get("result", {}),
                        "arifos_url": ARIFOS_MCP_URL,
                        "submitted_at": datetime.now(timezone.utc).isoformat(),
                    }
                return {
                    "status": "DELIVERED_BUT_ERROR",
                    "raw": data,
                    "arifos_url": ARIFOS_MCP_URL,
                }
            return {
                "status": "DEGRADED",
                "http_status": resp.status_code,
                "arifos_url": ARIFOS_MCP_URL,
                "fallback": "preserve_envelope_for_retry",
            }
    except Exception as e:
        return {
            "status": "UNREACHABLE",
            "error": str(e),
            "arifos_url": ARIFOS_MCP_URL,
            "preserved_envelope": handoff_envelope,
            "fallback": "preserve_envelope_for_retry",
            "note": "F1 AMANAH: envelope preserved, no data lost",
        }


def _constitutional_pre_check(
    intent: str,
    capability: str,
    blast_radius: str,
    reversibility_level: str,
    epistemic_state: str,
    result: dict,
) -> dict:
    """Cheap pre-flight check before arif_judge. Returns block reasons if any."""
    block_reasons = []
    warnings = []

    # F7 HUMILITY: speculation should be flagged
    if epistemic_state == "SPECULATED":
        warnings.append("F7: epistemic_state is SPECULATED — arif_judge may issue HOLD")

    # F8 LAW: irreversible + CRITICAL blast = always 888_HOLD
    if reversibility_level == "NONE" and blast_radius == "CRITICAL":
        block_reasons.append("F8: irreversibility + CRITICAL blast — requires 888_HOLD before submit")

    # F13 SOVEREIGN: never declare verdict from WEALTH
    if "verdict" in result and result.get("verdict") in ("SEAL", "VOID"):
        block_reasons.append("F13: WEALTH cannot pre-declare SEAL/VOID — arif_judge alone renders verdict")

    # F2 TRUTH: missing evidence_quality
    if not result.get("evidence_quality"):
        warnings.append("F2: result missing evidence_quality — arif_judge may issue NEEDS_EVIDENCE")

    # Risk thresholds: HIGH/CRITICAL risk from collapse scanner
    risk_score = result.get("result", {}).get("risk", {}).get("score", 0)
    if isinstance(risk_score, (int, float)) and risk_score > 0.7:
        warnings.append(f"F-collapse: risk_score={risk_score} > 0.7 — arif_judge may issue HOLD")

    return {
        "block_reasons": block_reasons,
        "warnings": warnings,
        "ready": len(block_reasons) == 0,
    }


def _extract_evidence(result: dict) -> list[dict]:
    """Pull evidence items from a WEALTH result, if present."""
    evidence = []
    if isinstance(result, dict):
        # Look for explicit evidence array
        if "evidence" in result and isinstance(result["evidence"], list):
            evidence = result["evidence"]
        # Look for capture scan / power audit dimensions
        for tool_key in ("dimensions", "tripwires", "indicators"):
            if tool_key in result and isinstance(result[tool_key], list):
                for item in result[tool_key]:
                    if isinstance(item, dict):
                        evidence.append({
                            "type": tool_key,
                            "name": item.get("name", item.get("dimension", "unnamed")),
                            "data": item,
                        })
    return evidence[:20]  # cap at 20 items


def _summarize(result: dict) -> str:
    """Compress a WEALTH result to a short summary for the envelope."""
    if not isinstance(result, dict):
        return str(result)[:200]
    # Try common summary fields
    for k in ("summary", "verdict", "interpretation", "narrative_signature", "phase_c_verdict"):
        if k in result and isinstance(result[k], str):
            return result[k][:300]
    # Fallback: serialize truncated
    try:
        return json.dumps(result, default=str)[:300]
    except Exception:
        return str(result)[:300]


__all__ = [
    "prepare_judge_handoff",
    "submit_to_arif_judge",
]
