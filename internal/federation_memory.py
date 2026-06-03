"""
WEALTH Federation Memory Client
═══════════════════════════════════════════════════════════════════════════
Adoption of FEDERATION_MEMORY_CONTRACT.md (2026-06-03, R1: single write
surface). All WEALTH memory writes route through arifOS MCP
`arif_memory_recall(mode="store")`. No direct Qdrant / Supabase / Graphiti
writes from WEALTH tools.

L5 Graphiti: advisory only (worker neutralized; 888 injects via raw Cypher).

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError

ARIFOS_MCP_URL = os.getenv("ARIFOS_MCP_URL", "http://localhost:8088")
ACTOR_ID = "wealth"
DEFAULT_TIMEOUT_S = 30.0

_session_id: str | None = None
_session_ts: float = 0.0
_SESSION_TTL_S = 300.0


def _ensure_session() -> str | None:
    """Ensure we have a fresh arifOS MCP session-id (5min TTL)."""
    global _session_id, _session_ts
    now = time.time()
    if _session_id and (now - _session_ts) < _SESSION_TTL_S:
        return _session_id
    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "WEALTH", "version": "0.1"},
                    },
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        with urlrequest.urlopen(req, timeout=5) as resp:
            sid = resp.headers.get("mcp-session-id")
            if sid:
                _session_id = sid
                _session_ts = now
                return sid
    except (URLError, HTTPError, TimeoutError, OSError):
        return None
    return None


def remember(
    content: str,
    *,
    tags: list[str] | None = None,
    tier: str = "canon",
    session_id: str | None = None,
    summary: str | None = None,
    context: str = "normal",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Federation memory write via arifOS MCP. Never raises.

    Returns a status dict with: stored, memory_id, point_id, pg_id, l5_status,
    backends, _degraded (if any). Failure modes are non-fatal — local
    computation succeeds regardless of memory write outcome.
    """
    if not content:
        return {"stored": False, "error": "empty_content"}

    sid = _ensure_session()
    if not sid:
        return {
            "stored": False,
            "error": "session_unavailable",
            "_degraded": "arifOS MCP session init failed",
        }

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": "tools/call",
        "params": {
            "name": "arif_memory_recall",
            "arguments": {
                "mode": "store",
                "metadata": {
                    "content": content,
                    "tags": tags or [],
                    "summary": summary,
                    "context": context,
                    "writer_bot": "WEALTH",
                    **(metadata or {}),
                },
                "actor_id": ACTOR_ID,
                "session_id": session_id or "wealth-default-session",
                "tier": tier,
            },
        },
    }

    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": sid,
            },
        )
        with urlrequest.urlopen(req, timeout=DEFAULT_TIMEOUT_S) as resp:
            body = resp.read().decode()
            for line in body.split("\n"):
                if line.startswith("data: "):
                    rpc = json.loads(line[6:])
                    sc = rpc.get("result", {}).get("structuredContent", {})
                    if sc.get("verdict") and sc["verdict"] != "SEAL":
                        return {
                            "stored": False,
                            "verdict": sc.get("verdict"),
                            "reasons": sc.get("reasons"),
                            "failed_floors": sc.get("failed_floors"),
                            "_degraded": f"arifOS returned {sc['verdict']}",
                        }
                    return {
                        "stored": True,
                        "memory_id": sc.get("memory_id"),
                        "point_id": sc.get("point_id"),
                        "pg_id": sc.get("pg_id"),
                        "pg_ok": sc.get("pg_ok"),
                        "l5_status": sc.get("l5_status"),
                        "backends": sc.get("backends"),
                    }
            return {"stored": False, "error": "no_data_in_response"}
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        return {
            "stored": False,
            "error": f"{type(e).__name__}: {e}",
            "_degraded": "arifOS MCP call failed",
        }


def recall(
    query: str,
    *,
    session_id: str | None = None,
    limit: int = 5,
    context: str = "normal",
) -> dict[str, Any]:
    """Federation memory read via arifOS MCP."""
    sid = _ensure_session()
    if not sid:
        return {"status": "session_unavailable", "results": []}
    try:
        req = urlrequest.Request(
            f"{ARIFOS_MCP_URL}/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": int(time.time() * 1000) % 1_000_000,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_memory_recall",
                        "arguments": {
                            "mode": "search",
                            "query": query,
                            "session_id": session_id or "wealth-default-session",
                            "actor_id": ACTOR_ID,
                            "limit": limit,
                            "context": context,
                        },
                    },
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": sid,
            },
        )
        with urlrequest.urlopen(req, timeout=DEFAULT_TIMEOUT_S) as resp:
            body = resp.read().decode()
            for line in body.split("\n"):
                if line.startswith("data: "):
                    rpc = json.loads(line[6:])
                    sc = rpc.get("result", {}).get("structuredContent", {})
                    return {
                        "status": "ok",
                        "results": sc.get("results", []),
                    }
        return {"status": "no_data", "results": []}
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        return {"status": "exception", "error": str(e), "results": []}


def get_contract_surface() -> dict[str, str]:
    """Returns the canonical federation contract surface this client targets."""
    return {
        "mcpUrl": ARIFOS_MCP_URL,
        "actor": ACTOR_ID,
        "contract": "FEDERATION_MEMORY_CONTRACT.md (R1: single write surface)",
        "l5_status": "advisory_only (worker neutralized; 888 injects via raw Cypher)",
    }
