"""
WEALTH OPA Wiring — Evaluate OPA policy before any WEALTH mutation.

Phase 2 substrate: every WEALTH tool that can mutate state should call
`evaluate_opa_policy()` first. Fail-closed on OPA failure.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional


# Default OPA endpoint (localhost per ADR-001)
OPA_DEFAULT_ENDPOINT = os.environ.get("WEALTH_OPA_ENDPOINT", "http://127.0.0.1:8181")


def evaluate_opa_policy(
    policy_path: str,
    actor_id: str,
    action_class: str,
    tool: str,
    session_id: Optional[str] = None,
    resource: Optional[str] = None,
    reversible: bool = True,
    endpoint: Optional[str] = None,
) -> dict:
    """
    Evaluate an OPA policy before a WEALTH tool call.

    Returns dict with: recommendation (ALLOW/DENY/SABAR), override, confidence, evidence, input_hash.

    Phase 2 stub: synchronously HTTP POST to OPA. Phase 3: async + cache.
    """
    import json

    try:
        import httpx
        import httpx2  # FastMCP 4 migration
    except ImportError:
        return {
            "recommendation": "DENY" if action_class in ("MUTATE", "SEAL") else "SABAR",
            "override": True,
            "confidence": 0.5,
            "evidence": {"opa_error": "httpx not installed"},
            "input_hash": "",
            "fail_closed": True,
        }

    endpoint = endpoint or OPA_DEFAULT_ENDPOINT
    input_data = {
        "actor_id": actor_id,
        "action_class": action_class,
        "tool": tool,
        "session_id": session_id or "",
        "resource": resource or "",
        "reversible": reversible,
        "organ": "WEALTH",
    }
    input_hash = (
        "sha256:"
        + hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()
    )

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{endpoint}/v1/data/{policy_path}",
                json={"input": input_data},
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result", {})

            return {
                "recommendation": "ALLOW"
                if result.get("allow", False)
                else ("DENY" if result.get("deny", False) else "SABAR"),
                "override": result.get("override", True),
                "confidence": min(0.90, float(result.get("confidence", 0.85))),
                "evidence": result,
                "input_hash": input_hash,
                "fail_closed": False,
            }
    except (
        httpx.HTTPError,
        httpx2.HTTPError,
        httpx.RequestError,
        httpx2.RequestError,
        Exception,
    ) as e:
        # F1 AMANAH: fail-closed for mutations
        return {
            "recommendation": "DENY" if action_class in ("MUTATE", "SEAL") else "SABAR",
            "override": True,
            "confidence": 0.5,
            "evidence": {"opa_error": str(e)},
            "input_hash": input_hash,
            "fail_closed": True,
        }
