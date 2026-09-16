"""HERMES semantic gate — meaning preconditions capital compute.

F13 directive 2026-09-16: "wire hermes semantic gate as precondition for
wealth compute". Before a WEALTH tool executes on free-text claims, the
claims are validated upstream by the HERMES Meaning Integrity Organ
(`hermes_claim_validate` on :18087). WEALTH calls HERMES; HERMES never
reaches into WEALTH — the arrow stays one-directional: meaning gates
money, money never gates meaning.

Authority posture: this gate BLOCKS on semantically invalid claims; it
never authorizes anything (CAPABILITY ≠ AUTHORITY). Failure of the gate
service is governed by WEALTH_HERMES_GATE_MODE:
  enforce (default) — HERMES unreachable ⇒ compute HELD (fail-closed)
  warn               — compute proceeds with a SKIPPED receipt field
Degradation is a sovereign choice made via env, never a silent fallback.

Wire contract (pinned by live probe 2026-09-16): FastMCP streamable-http,
stateful. initialize → Mcp-Session-Id header → notifications/initialized
(202) → tools/call. Responses may be application/json or SSE-framed;
both are parsed. Verdict vocabulary: PASS | 888_HOLD | REWRITE_REQUIRED
| BLOCKED, plus injection_scan.injection_detected as an independent
hard gate.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

GATE_NAME = "hermes_semantic"

DEFAULT_HERMES_URL = "http://127.0.0.1:18087/mcp"
DEFAULT_TIMEOUT = 8.0

# Tools whose string inputs are symbols/enums/numbers only — no semantic
# content to validate. Everything else is scanned; the gate only calls
# HERMES when prose is actually present (meaning gates money — but only
# when meaning is present).
EXEMPT_TOOLS = frozenset(
    {
        "capital_registry",  # meta / status
        "capital_indicator",  # pure data fetch (symbol, interval, lookback)
        "capital_primitive",  # pure math on numbers
    }
)

# Argument keys that are transport/identity plumbing, never claims.
_SKIP_KEYS = frozenset(
    {
        "_meta",
        "session_id",
        "actor_id",
        "trace_id",
        "session_token",
        "sct",
        "arifos_sct",
        "actor_signature",
        "nonce",
        "idempotency_key",
        "callback",
    }
)

# A string counts as semantic content when it is prose-shaped: long
# enough to carry a claim and contains word separation. Enum tokens,
# tickers, dates, and numeric strings pass through untouched.
_MIN_PROSE_LEN = 24
_MAX_FIELDS = 8
_MAX_FIELD_CHARS = 500


class GateTransportError(RuntimeError):
    """HERMES unreachable or wire-level failure."""


class GateProtocolError(RuntimeError):
    """HERMES answered, but the answer is not a parseable claim verdict."""


def _cfg() -> dict[str, Any]:
    return {
        "enabled": os.environ.get("WEALTH_HERMES_GATE", "on").strip().lower()
        not in {"off", "0", "false", "disabled"},
        "mode": os.environ.get("WEALTH_HERMES_GATE_MODE", "enforce").strip().lower(),
        "url": os.environ.get("WEALTH_HERMES_URL", DEFAULT_HERMES_URL).rstrip("/"),
        "timeout": float(os.environ.get("WEALTH_HERMES_TIMEOUT", str(DEFAULT_TIMEOUT))),
    }


def extract_semantic_fields(arguments: dict[str, Any] | None) -> dict[str, str]:
    """Collect prose-shaped string values from tool arguments.

    Returns {} when the call carries no semantic content (pure numbers,
    enums, symbols) — the gate then no-ops without touching HERMES.
    """

    def is_prose(s: str) -> bool:
        return len(s) >= _MIN_PROSE_LEN and " " in s

    def walk(node: Any, path: str, out: dict[str, str]) -> None:
        if len(out) >= _MAX_FIELDS:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k in _SKIP_KEYS:
                    continue
                walk(v, f"{path}.{k}" if path else str(k), out)
        elif isinstance(node, (list, tuple)):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]", out)
        elif isinstance(node, str) and is_prose(node):
            out[path or "claim"] = node[:_MAX_FIELD_CHARS]

    out: dict[str, str] = {}
    if isinstance(arguments, dict):
        walk(arguments, "", out)
    return out


def build_claim(tool_name: str, fields: dict[str, str]) -> str:
    """Compose the claim bundle HERMES validates — one line per field."""
    lines = [f"[{tool_name}] claims submitted for capital compute:"]
    for key, value in fields.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _post(
    url: str,
    payload: dict[str, Any],
    timeout: float,
    session_id: str | None = None,
) -> tuple[int, Any, str | None]:
    """One JSON-RPC POST. Returns (status, parsed_body_or_None, session_header)."""
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            sid = resp.headers.get("Mcp-Session-Id")
            parsed: Any = None
            ctype = resp.headers.get("Content-Type", "")
            if "text/event-stream" in ctype:
                for line in body.splitlines():
                    if line.startswith("data:"):
                        chunk = line[len("data:") :].strip()
                        if chunk:
                            try:
                                candidate = json.loads(chunk)
                            except json.JSONDecodeError:
                                continue
                            if isinstance(candidate, dict) and "result" in candidate:
                                parsed = candidate
            elif body:
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = None
            return resp.status, parsed, sid
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise GateTransportError(f"HERMES HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GateTransportError(f"HERMES unreachable: {exc!r}") from exc


def _mcp_claim_validate(url: str, timeout: float, claim: str, tool_name: str) -> dict[str, Any]:
    """Full MCP round-trip: initialize → initialized → tools/call.

    Returns the inner `result` dict from hermes_claim_validate
    (verdict, violations, injection_scan, permitted_statement, ...).
    """
    init = _post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "wealth-hermes-gate", "version": "1.0"},
            },
        },
        timeout,
    )
    if init[0] != 200:
        raise GateTransportError(f"HERMES initialize returned HTTP {init[0]}")
    sid = init[2]
    if not sid:
        # Stateless deployments answer without a session header; stateful
        # ones require it. Absence is only fatal if tools/call then fails.
        sid = None
    _post(
        url,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        timeout,
        session_id=sid,
    )
    call = _post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "hermes_claim_validate",
                "arguments": {
                    "claim": claim,
                    "claimant": "wealth-mcp",
                    "context": {
                        "domain": "capital_compute",
                        "calling_tool": tool_name,
                        "purpose": "semantic precondition gate",
                    },
                },
            },
        },
        timeout,
        session_id=sid,
    )
    body = call[1]
    if not isinstance(body, dict) or "result" not in body:
        raise GateProtocolError(f"HERMES tools/call yielded no JSON-RPC result (HTTP {call[0]})")
    rpc_result = body["result"]
    if rpc_result.get("isError"):
        raise GateProtocolError(f"HERMES tool errored: {str(rpc_result)[:300]}")
    inner = None
    structured = rpc_result.get("structuredContent")
    if isinstance(structured, dict) and isinstance(structured.get("result"), dict):
        inner = structured["result"]
    else:
        for content in rpc_result.get("content", []) or []:
            if isinstance(content, dict) and "text" in content:
                try:
                    parsed_text = json.loads(content["text"])
                except (json.JSONDecodeError, TypeError):
                    continue
                if isinstance(parsed_text, dict) and isinstance(
                    parsed_text.get("result"), dict
                ):
                    inner = parsed_text["result"]
                    break
    if not isinstance(inner, dict):
        raise GateProtocolError("HERMES verdict payload missing `result` object")
    return inner


def _outcome_from_verdict(inner: dict[str, Any]) -> tuple[str, str, list[str]]:
    """Map the HERMES verdict to (outcome, error_code, violation_rules).

    outcome ∈ {PASS, INJECTION, HOLD, REWRITE_REQUIRED, BLOCKED}
    """
    violations = inner.get("violations") or []
    rules = [
        str(v.get("rule")) for v in violations if isinstance(v, dict) and v.get("rule")
    ]
    injection = (inner.get("injection_scan") or {}).get("injection_detected")
    if injection:
        categories = (inner.get("injection_scan") or {}).get("categories") or []
        rules = ["INJECTION"] + [str(c) for c in categories] + rules
        return "INJECTION", "SEMANTIC_GATE_INJECTION", rules
    verdict = str(inner.get("verdict", "")).upper()
    if verdict == "PASS":
        return "PASS", "", rules
    if verdict == "888_HOLD":
        return "HOLD", "SEMANTIC_GATE_HOLD", rules
    if verdict == "REWRITE_REQUIRED":
        return "REWRITE_REQUIRED", "SEMANTIC_GATE_REWRITE", rules
    if verdict == "BLOCKED":
        return "BLOCKED", "SEMANTIC_GATE_BLOCKED", rules
    raise GateProtocolError(f"HERMES returned unknown verdict {verdict!r}")


def gate_status() -> dict[str, Any]:
    """Public gate configuration snapshot for the /health plane.

    A fail-closed precondition must never be invisible: if HERMES dies,
    capital compute holds, and operators must see the cause at /health.
    """
    cfg = _cfg()
    return {
        "gate": GATE_NAME,
        "enabled": cfg["enabled"],
        "mode": cfg["mode"],
        "upstream": cfg["url"],
        "verdicts": ["PASS", "888_HOLD", "REWRITE_REQUIRED", "BLOCKED"],
        "fail_closed": cfg["mode"] == "enforce",
    }


async def run_semantic_gate(
    tool_name: str,
    arguments: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run the HERMES semantic precondition for one tool call.

    Returns a gate state dict — always, on every path:

      status    "PASS" | "BLOCKED" | "SKIPPED"
      outcome   NO_SEMANTIC_CONTENT | PASS | PASS_WARN_UNAVAILABLE |
                PASS_WARN_PROTOCOL | INJECTION | HOLD | REWRITE_REQUIRED |
                BLOCKED | UNAVAILABLE | PROTOCOL | GATE_OFF | GATE_EXEMPT
      error_code  set when blocked (matches WEALTH block vocabulary)
    """
    cfg = _cfg()
    base = {
        "gate": GATE_NAME,
        "gate_mode": cfg["mode"],
        "hermes_url": cfg["url"],
        "tool": tool_name,
    }
    if not cfg["enabled"]:
        return {**base, "status": "SKIPPED", "outcome": "GATE_OFF", "error_code": ""}
    if tool_name in EXEMPT_TOOLS:
        return {**base, "status": "SKIPPED", "outcome": "GATE_EXEMPT", "error_code": ""}

    fields = extract_semantic_fields(arguments)
    if not fields:
        return {
            **base,
            "status": "PASS",
            "outcome": "NO_SEMANTIC_CONTENT",
            "semantic_fields": [],
            "error_code": "",
        }

    claim = build_claim(tool_name, fields)
    started = time.monotonic()
    try:
        inner = await asyncio.to_thread(
            _mcp_claim_validate, cfg["url"], cfg["timeout"], claim, tool_name
        )
        outcome, error_code, rules = _outcome_from_verdict(inner)
        latency_ms = round((time.monotonic() - started) * 1000.0, 1)
        blocked = outcome != "PASS"
        return {
            **base,
            "status": "BLOCKED" if blocked else "PASS",
            "outcome": outcome,
            "error_code": error_code,
            "claim_id": inner.get("claim_id"),
            "semantic_fields": sorted(fields.keys()),
            "violations": rules,
            "permitted_statement": inner.get("permitted_statement"),
            "required_evidence": inner.get("required_evidence"),
            "latency_ms": latency_ms,
        }
    except GateTransportError as exc:
        latency_ms = round((time.monotonic() - started) * 1000.0, 1)
        if cfg["mode"] == "warn":
            return {
                **base,
                "status": "PASS",
                "outcome": "PASS_WARN_UNAVAILABLE",
                "error_code": "",
                "detail": str(exc),
                "semantic_fields": sorted(fields.keys()),
                "latency_ms": latency_ms,
            }
        return {
            **base,
            "status": "BLOCKED",
            "outcome": "UNAVAILABLE",
            "error_code": "SEMANTIC_GATE_UNAVAILABLE",
            "detail": str(exc),
            "semantic_fields": sorted(fields.keys()),
            "latency_ms": latency_ms,
        }
    except GateProtocolError as exc:
        latency_ms = round((time.monotonic() - started) * 1000.0, 1)
        if cfg["mode"] == "warn":
            return {
                **base,
                "status": "PASS",
                "outcome": "PASS_WARN_PROTOCOL",
                "error_code": "",
                "detail": str(exc),
                "semantic_fields": sorted(fields.keys()),
                "latency_ms": latency_ms,
            }
        return {
            **base,
            "status": "BLOCKED",
            "outcome": "PROTOCOL",
            "error_code": "SEMANTIC_GATE_PROTOCOL",
            "detail": str(exc),
            "semantic_fields": sorted(fields.keys()),
            "latency_ms": latency_ms,
        }
