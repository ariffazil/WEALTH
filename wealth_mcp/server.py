"""
WEALTH Federated Domain — MCP Server.

Replaces internal/monolith.py as the canonical entry point.
Imports from wealth_core/ and wealth_contracts/.
Exposes the same MCP surface with clean architecture.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.prompts.base import Message
from mcp.types import EmbeddedResource, TextResourceContents
from pydantic import AnyUrl

from wealth_mcp import (
    CAPITAL_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
    WEALTH_VERSION,
    WEALTH_RESOURCE_URIS,
    WEALTH_PROMPT_NAMES,
)

# register_institutional_tools DELETED 2026-08-06 — C6: INSTITUTIONAL_TOOL_NAMES empty tuple since Phase 1a. Dead import.
from wealth_mcp.tools.canonical import register_canonical_tools

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# WEALTH capital compute — OBSERVE by default.
# ZEN 2026-07-11 FNF-0: NEVER import arifosmcp into this organ (coupling leak).
_UNBOUND_SESSION_TOKENS = {None, "", "_default", "null", "None", "anonymous"}
_OBSERVE_SURFACE = frozenset(PUBLIC_TOOL_NAMES)

# These names are resolved only by canonical.py's direct-import compatibility
# dispatcher. They are deliberately not FastMCP registrations or public SOT.
_INTERNAL_LEGACY_ALIASES = {
    "wealth_market_data": "capital_market",
    "market_data": "capital_market",
    "wealth_stock_analysis": "capital_market",
    "stock_analysis": "capital_market",
    "wealth_vault_query": "capital_ledger",
    "vault_query": "capital_ledger",
    "wealth_vault_write": "capital_ledger",
    "vault_write": "capital_ledger",
    "wealth_registry_status": "capital_registry",
    "wealth_system_registry_status": "capital_registry",
    "registry_status": "capital_registry",
    "wealth_schema": "capital_registry",
    "schema": "capital_registry",
    "wealth_survival_engine": "capital_health",
    "survival_engine": "capital_health",
    # C8 2026-08-06: omni_wisdom aliases unresolved. capital_wisdom deleted
    # (F13 directive). Legacy dispatch still resolves via _call_legacy_tool
    # if needed internally, but no public path reaches it.
    # "wealth_omni_wisdom": "internal_wisdom_engine",
    # "omni_wisdom": "internal_wisdom_engine",
}


def _append_existing_jsonl(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append to a provisioned JSONL target without creating files or directories."""
    target = Path(path)
    state: dict[str, Any] = {"persisted": False, "path": str(target)}
    if not target.is_file():
        state["error"] = "receipt target is not provisioned; no file was created"
        return state
    try:
        with target.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, default=str) + "\n")
    except OSError as exc:
        state["error"] = str(exc)
        return state
    state["persisted"] = True
    return state


def _tool_result_status(result: Any) -> str:
    """Derive receipt status from the actual FastMCP result, not mere return."""
    if getattr(result, "is_error", False):
        return "ERROR"
    payload = getattr(result, "structured_content", None)
    if not isinstance(payload, dict):
        return "PASS"
    candidates = [payload.get("result"), payload]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        status = candidate.get("status")
        if not status:
            continue
        normalized = str(status).upper()
        if normalized in {"OK", "ALIVE", "PASS", "APPENDED", "INSERTED"}:
            return "PASS"
        return normalized
    return "PASS"


def _attach_receipt_meta(result: Any, receipt_state: dict[str, Any]) -> Any:
    """Expose receipt persistence state to MCP callers."""
    meta = dict(getattr(result, "meta", None) or {})
    meta["wealth_receipt"] = receipt_state
    result.meta = meta
    return result


def _validate_session_via_http_bridge(
    session_id: str,
    actor_id: str | None,
) -> dict[str, object]:
    """HTTP check against arifOS — no package import."""
    import json
    import os
    import urllib.error
    import urllib.request

    kernel = os.environ.get("ARIFOS_KERNEL_URL", "http://127.0.0.1:8088").rstrip("/")
    url = f"{kernel}/mcp"
    try:
        init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "wealth-session-bridge",
                        "version": "2026.07.11",
                    },
                },
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=init_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get(
                "mcp-session-id"
            )
            resp.read()
        return {
            "ok": True,
            "code": "BRIDGE_OBSERVE",
            "reason": "L11 AUTH: kernel bridge reachable; WEALTH OBSERVE-only (no arifosmcp import)",
            "actor_id": actor_id or "wealth-mcp",
            "session_id": session_id,
            "actor_verified": False,
            "bridge_mcp_session": sid,
            "tool_name": None,
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "code": "SESSION_BRIDGE_UNAVAILABLE",
            "reason": f"L11 AUTH: arifOS bridge unreachable: {exc}",
            "actor_id": actor_id,
            "session_id": session_id,
            "tool_name": None,
        }


def _validate_direct_session_binding(
    tool_name: str,
    actor_id: str | None,
    session_id: str | None,
) -> dict[str, object]:
    """Session binding without importing the kernel package.

    Coupling rule: WEALTH must not `import arifosmcp`.
    - Unbound/_default + OBSERVE tools → pass-through with WARNING (2026-08-06 fix)
    - Unbound/_default + MUTATE tools → SESSION_REQUIRED
    - Real session_id → HTTP bridge only

    FORGED 2026-07-18: Anonymous reads removed.
    AMENDED 2026-08-06: OBSERVE-class tools (market, registry, primitive, entropy)
    restored to OBSERVE_UNBOUND — these compute but never mutate. MUTATE tools
    (ledger, handoff, diagnose) still require valid session_id.
    """
    _OBSERVE_TOOLS = {
        "capital_market",
        "capital_registry",
        "capital_primitive",
        "capital_entropy",
        "capital_wisdom",
    }
    unbound = session_id in _UNBOUND_SESSION_TOKENS

    if unbound:
        # 2026-08-06: Restore OBSERVE_UNBOUND for read-only tools.
        # WEALTH is COMPUTE_ONLY — the worst case from a missing session
        # is lack of audit trail, not unauthorized mutation.
        if tool_name in _OBSERVE_TOOLS:
            import datetime as _dt

            return {
                "ok": True,
                "code": "OBSERVE_UNBOUND",
                "reason": "OBSERVE-class tool — session optional",
                "actor_id": actor_id or "wealth-mcp",
                "session_id": session_id or "_default",
                "tool_name": tool_name,
                "_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }

        import datetime as _dt

        return {
            "ok": False,
            "code": "SESSION_REQUIRED",
            "reason": (
                "L11 AUTH: session_id required for all WEALTH tools "
                "(FORGE 2026-07-18: anonymous reads blocked)"
            ),
            "actor_id": actor_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }

    bridge = _validate_session_via_http_bridge(str(session_id), actor_id)
    bridge["tool_name"] = tool_name
    return bridge


def create_mcp_server() -> FastMCP:
    """Create and configure the WEALTH MCP server."""

    from wealth_mcp.middleware import WealthEvidenceMiddleware

    mcp = FastMCP(
        "WEALTH Federated Domain",
        version=(
            f"v{WEALTH_VERSION}" if WEALTH_VERSION != "UNAVAILABLE" else WEALTH_VERSION
        ),
        # MCP logging: SEP-2577 deprecated — maintenance only; default min warning.
        client_log_level="warning",
        instructions=(
            "WEALTH — Capital Intelligence for arifOS federation. "
            "Computes capital, risk, wisdom, and power metrics. "
            "Does NOT authorize execution. WEALTH computes. arifOS judges. Arif decides."
        ),
        # W0 2026-08-06: Evidence middleware — enforces verification integrity
        # on every tool call. Detects silent input dropping, verdict conflicts,
        # and byte-identical outputs on different inputs.
        middleware=[WealthEvidenceMiddleware()],
    )

    # Completions CANCELLED 2026-07-09 — agent surface uses full tool JSON.

    # ── Wire arifOS organ governance wrapper around tool calls ─────────────
    try:
        from internal.organ_governance import check_governance as _check_governance
        from fastmcp.server.server import ToolResult
        from mcp.types import TextContent

        _original_call_tool = mcp.call_tool
        _original_read_resource = mcp.read_resource
        import datetime as _dt
        import uuid as _uuid

        _RECEIPT_PATH = os.environ.get(
            "WEALTH_RECEIPT_PATH", "/root/VAULT999/wealth/receipts.jsonl"
        )
        _SCHEMA_VERSION = "2026.07.24"

        # ── Preload mechanism REMOVED (2026-07-07) ──────────────────────
        # Resources are now direct @mcp.resource() URIs with no gating.
        # Tools that need resource data read the file directly or call
        # the resource function inline. See SVB backtest findings:
        # all 3 wealth:// URIs returned "Failed to read MCP resource"
        # because clients couldn't populate the session preload cache.
        pass

        def _now_iso() -> str:
            return _dt.datetime.now(_dt.timezone.utc).isoformat()

        def _emit_receipt(
            tool_name: str,
            arguments: dict,
            status: str,
            verdict: str = "",
            actor_id: str | None = None,
            session_id: str | None = None,
            evidence_quality: str | None = None,
            missing_preload: list | None = None,
        ) -> dict[str, Any]:
            """Persist an audit receipt and return observable persistence state."""
            actor_id = actor_id or "wealth-mcp"
            evidence_quality = evidence_quality or (
                "OBSERVED" if status == "PASS" else "MISSING"
            )
            receipt_id = str(_uuid.uuid4())
            receipt = {
                "receipt_id": receipt_id,
                "timestamp_utc": _now_iso(),
                "actor_id": actor_id,
                "tool_name": tool_name,
                "arguments": {
                    key: value
                    for key, value in (arguments or {}).items()
                    if key not in ("actor_signature", "nonce", "_meta")
                },
                "epistemic_state": "DERIVED",
                "evidence_quality": evidence_quality,
                "domain": _infer_domain(tool_name),
                "session_id": session_id,
                "trace_id": (arguments or {}).get("trace_id"),
                "call_status": status,
                "governance_status": verdict or "UNAVAILABLE",
                "transport": "mcp_call_tool",
                "schema_version": _SCHEMA_VERSION,
            }
            if missing_preload:
                receipt["non_compliant_preload"] = missing_preload

            state = _append_existing_jsonl(_RECEIPT_PATH, receipt)
            state["receipt_id"] = receipt_id
            state["call_status"] = status
            if not state["persisted"]:
                print(
                    f"[RECEIPT] persistence failed for {tool_name} "
                    f"({receipt_id}): {state.get('error', 'unknown error')}"
                )
            return state

        def _infer_domain(tool_name: str) -> str:
            t = tool_name.lower()
            if any(k in t for k in ("vault_write", "vault_query", "ledger")):
                return "governance"
            if any(
                k in t
                for k in ("personal_finance", "cashflow", "runway", "zakat", "epf")
            ):
                return "personal"
            if any(k in t for k in ("market", "fx", "commodity", "macro")):
                return "market"
            if any(k in t for k in ("stock",)):
                return "stock"
            if any(
                k in t
                for k in (
                    "markowitz",
                    "kelly",
                    "robust_portfolio",
                    "chance_constrained",
                    "two_stage_recourse",
                    "optimizer",
                )
            ):
                return "optimization"
            if any(
                k in t
                for k in (
                    "power",
                    "capture",
                    "collapse",
                    "beautiful_mouse",
                    "institutional",
                    "wisdom",
                )
            ):
                return "institutional" if "institutional" in t else "wisdom"
            if any(k in t for k in ("handoff", "judge", "arifos")):
                return "governance"
            if any(k in t for k in ("bid_surface",)):
                return "auction"
            if any(k in t for k in ("optimize_mwc", "mwc")):
                return "coalition"
            if any(
                k in t
                for k in ("evoi", "emv", "asymmetry", "confluence", "monte_carlo")
            ):
                return "risk"
            if any(
                k in t
                for k in ("npv", "irr", "conservation", "flow", "fiscal", "breakeven")
            ):
                return "capital"
            return "meta"

        def _wrap_envelope(
            tool_name: str,
            arguments: dict,
            result: ToolResult,
            verdict: str,
            actor_id: str,
            session_id: str,
            receipt_id: str,
        ) -> ToolResult:
            """Ensure every WEALTH response carries the canonical output envelope.

            The tools already produce `WealthEnvelope` via `wrap_result()` which
            matches `WEALTH_OUTPUT_SCHEMA`. This wrapper:
            1. Preserves existing structured_content from the tool
            2. Adds governance verdict + identity if not already present
            3. Returns exactly ONE content block

            PARSER-SAFE: single TextContent, single structured_content.
            No second text attachment. No parser-dependent metadata block.
            """
            try:
                existing_structured = getattr(result, "structured_content", None)

                if existing_structured and isinstance(existing_structured, dict):
                    enriched = dict(existing_structured)
                else:
                    original_text = ""
                    if result.content and len(result.content) > 0:
                        first = result.content[0]
                        if hasattr(first, "text"):
                            original_text = first.text
                    try:
                        enriched = json.loads(original_text)
                        if not isinstance(enriched, dict):
                            enriched = {"raw": str(enriched)}
                    except (json.JSONDecodeError, TypeError):
                        enriched = {"raw": str(original_text)[:2000]}

                if "session_id" not in enriched or not enriched["session_id"]:
                    enriched["session_id"] = session_id
                if "actor_id" not in enriched or not enriched["actor_id"]:
                    enriched["actor_id"] = actor_id
                if "trace_id" not in enriched:
                    enriched["trace_id"] = receipt_id or ""

                enriched["execution_authorized"] = enriched.get(
                    "execution_authorized", False
                )
                enriched.setdefault("human_final_authority", "Arif")

                # ── W-005: Required output fields (2026-08-06) ────────
                enriched.setdefault("verdict", str(verdict or "PARTIAL").upper())
                enriched.setdefault("coverage", {"known": 0, "total": 0, "ratio": 0.0})
                enriched.setdefault(
                    "epistemic",
                    {
                        "tag": enriched.get("epistemic_tag", "DERIVED"),
                        "quality": enriched.get("evidence_quality", "MODERATE"),
                        "confidence": 0.50,
                    },
                )

                # ── Single Verdict Resolution (W4 Fix) ────────────────
                # Lowest verdict wins: VOID > HOLD > SABAR > PASS/SEAL
                apex_v = str((enriched.get("apex") or {}).get("verdict", "")).upper()
                apex_pass = (
                    (enriched.get("apex") or {}).get("authority", {}).get("pass")
                )
                dom_v = str(
                    enriched.get("domain_verdict") or enriched.get("verdict") or ""
                ).upper()
                if (
                    apex_v in ("HOLD", "VOID", "BLOCKED")
                    or apex_pass is False
                    or dom_v in ("HOLD", "VOID", "BLOCKED")
                ):
                    winning_v = (
                        "VOID"
                        if ("VOID" in (apex_v, dom_v) or "BLOCKED" in (apex_v, dom_v))
                        else "HOLD"
                    )
                    enriched["domain_verdict"] = winning_v
                    enriched["verdict"] = winning_v
                    if isinstance(enriched.get("result"), dict):
                        enriched["result"]["verdict"] = winning_v

                enriched_text = json.dumps(enriched, default=str)
                wrapped = ToolResult(
                    content=[TextContent(type="text", text=enriched_text)],
                    is_error=result.is_error,
                    meta=dict(getattr(result, "meta", None) or {}),
                )
                wrapped.structured_content = enriched
                return wrapped
            except Exception as e:
                print(f"[ENVELOPE] wrap failed for {tool_name}: {e}")
                return result

        def _domain_default_epistemic(domain: str) -> str:
            return {
                "capital": "DERIVED",
                "risk": "DERIVED",
                "market": "RETRIEVED",
                "personal": "OBSERVED",
                "stock": "RETRIEVED",
                "wisdom": "INTERPRETED",
                "governance": "DERIVED",
                "meta": "OBSERVED",
            }.get(domain, "DERIVED")

        async def _governance_call_tool(name, arguments=None, **kwargs):
            if arguments is None:
                arguments = {}

            # ── Pull _meta for actor_id / session_id binding ──────────
            meta = arguments.get("_meta", {}) if isinstance(arguments, dict) else {}
            # Prioritize verified system kwargs over self-reported _meta to prevent spoofing (P0)
            _top_level_actor = (
                arguments.get("actor_id") if isinstance(arguments, dict) else None
            )
            _top_level_session = (
                arguments.get("session_id") if isinstance(arguments, dict) else None
            )
            actor_id = (
                kwargs.get("actor_id")
                or _top_level_actor
                or meta.get("actor_id")
                or "wealth-mcp"
            )
            session_id = (
                kwargs.get("session_id")
                or _top_level_session
                or meta.get("session_id")
                or "_default"
            )

            # ── RESULT FINALIZER — wraps ALL return paths with envelope ─
            def _finalize(
                raw_result: ToolResult,
                verdict_str: str,
                is_err: bool | None = None,
            ) -> ToolResult:
                """Apply envelope on success, error, blocked, and timeout paths.
                All returns go through this gate — no bare ToolResult escapes."""
                _err = is_err if is_err is not None else raw_result.is_error
                _r = ToolResult(
                    content=raw_result.content,
                    is_error=_err,
                    meta=raw_result.meta if hasattr(raw_result, "meta") else None,
                )
                return _wrap_envelope(
                    name, arguments, _r, verdict_str, actor_id, session_id, ""
                )

            # ── SCT ingress gate (2026-07-17) ─────────────────────────
            # Present SCT must verify; absent allowed for OBSERVE (capital compute).
            try:
                import sys as _sys

                if "/root/AAA" not in _sys.path:
                    _sys.path.insert(0, "/root/AAA")
                from governance.federation_sct import gate_tool_ingress

                # Inject actor into args for expected_actor check
                _args_for_sct = dict(arguments) if isinstance(arguments, dict) else {}
                if actor_id and "actor_id" not in _args_for_sct:
                    _args_for_sct["actor_id"] = actor_id
                _sct_rej = gate_tool_ingress(
                    name,
                    _args_for_sct,
                    meta=meta if isinstance(meta, dict) else None,
                    organ="wealth",
                    require_sct=False,
                )
                if _sct_rej is not None:
                    return _finalize(
                        ToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=json.dumps(_sct_rej, default=str),
                                )
                            ],
                            is_error=True,
                        ),
                        "BLOCKED",
                        is_err=True,
                    )
                # Strip SCT transport fields before tool schema validation
                if isinstance(arguments, dict):
                    for _sk in ("session_token", "sct", "arifos_sct"):
                        arguments.pop(_sk, None)
            except Exception as _sct_exc:
                # If caller sent a token but gate infrastructure failed, fail closed
                _tok = None
                if isinstance(arguments, dict):
                    _tok = (
                        arguments.get("session_token")
                        or arguments.get("sct")
                        or (meta.get("sct") if isinstance(meta, dict) else None)
                    )
                if _tok:
                    return _finalize(
                        ToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=json.dumps(
                                        {
                                            "error": "SCT_GATE_INFRA",
                                            "message": f"SCT present but gate failed: {_sct_exc!r}",
                                            "tool": name,
                                            "organ": "wealth",
                                        },
                                        default=str,
                                    ),
                                )
                            ],
                            is_error=True,
                        ),
                        "BLOCKED",
                        is_err=True,
                    )

            # ── P0-4: Session validation (was defined but never called) ──
            # C3 2026-08-06: Tool schemas declare session_id as Optional but
            # this gate enforces it. Gap: schema says optional, runtime says
            # mandatory. Until resolved, clients MUST send session_id or accept
            # SESSION_REQUIRED block. Fix: either add session_id to required[]
            # in every tool schema, or make this gate optional for OBSERVE-class.
            binding = _validate_direct_session_binding(name, actor_id, session_id)
            if not binding.get("ok"):
                # MUST return schema-conformant response matching WEALTH_OUTPUT_SCHEMA
                # All 9 required fields included to prevent FastMCP -32602 rejection.
                return _finalize(
                    ToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=json.dumps(
                                    {
                                        "tool_name": name,
                                        "tool_version": WEALTH_VERSION,
                                        "domain": "capital",
                                        "result": {},
                                        "result_type": "ERROR",
                                        "epistemic_tag": "ASSUMED",
                                        "claim_state": "UNPROVEN",
                                        "evidence_quality": "MISSING",
                                        "epistemic": {
                                            "tag": "ASSUMED",
                                            "quality": "MISSING",
                                            "confidence": 0.0,
                                        },
                                        "execution_authorized": False,
                                        "execution_authority": "OBSERVATION",
                                        "human_final_authority": "ARIF",
                                        "requires_888_hold": False,
                                        "source_attribution": ["wealth-session-gate"],
                                        "computation_timestamp": binding.get("_ts", ""),
                                        "session_id": binding.get("session_id"),
                                        "actor_id": binding.get("actor_id"),
                                        "errors": [
                                            binding.get(
                                                "reason",
                                                "L11 AUTH: session_id required",
                                            )
                                        ],
                                        "error_code": binding.get(
                                            "code", "SESSION_REQUIRED"
                                        ),
                                    },
                                    default=str,
                                ),
                            )
                        ],
                        is_error=True,
                    ),
                    "BLOCKED",
                    is_err=True,
                )

            # Use resolved actor from binding
            actor_id = str(binding.get("actor_id") or actor_id or "wealth-mcp")

            # ── arifOS governance check ────────────────────────────────
            # Pass extracted system actor_id and session_id (Gap-C alignment)
            verdict, error = _check_governance(
                name,
                arguments,
                actor_id=actor_id,
                session_id=session_id,
            )
            if error is not None:
                error_text = json.dumps(
                    {
                        "tool": name,
                        "governance_status": verdict,
                        "error_code": "ORGAN_GOVERNANCE_BLOCKED",
                        "message": f"arifOS {verdict}: governance check blocked execution",
                        "guard": "ORGAN_GOVERNANCE",
                        "floor": "L1-L13",
                    }
                )
                receipt_state = _emit_receipt(
                    name,
                    arguments,
                    status="BLOCKED",
                    verdict=verdict,
                    actor_id=actor_id,
                    session_id=session_id,
                )
                # MCP logging — governance block (transport only; arifOS owns enforcement)
                try:
                    from wealth_mcp.mcp_logging import (
                        emit_mcp_log,
                        floor_event_to_level,
                    )

                    _lvl = floor_event_to_level(
                        "BLOCK"
                        if str(verdict).upper() in ("BLOCK", "BLOCKED", "VOID")
                        else "HOLD"
                    )
                    await emit_mcp_log(
                        _lvl,
                        f"WEALTH governance {verdict} on {name}",
                        tool=name,
                        floor="L1-L13",
                        verdict=str(verdict).upper(),
                        logger_name="wealth.envelope",
                        rate_key=f"wealth:{name}:GOV:{verdict}",
                        extra={
                            "error_code": "ORGAN_GOVERNANCE_BLOCKED",
                            "session_id": session_id,
                        },
                    )
                except Exception:
                    pass
                return _finalize(
                    ToolResult(
                        content=[TextContent(type="text", text=error_text)],
                        meta={"wealth_receipt": receipt_state},
                        is_error=True,
                    ),
                    "BLOCKED",
                    is_err=True,
                )

            # ── Execute + envelope + receipt ───────────────────────────
            # Strip _meta before passing to original tool — Pydantic tool
            # signatures reject unknown kwargs. _meta was already extracted
            # above for actor/session binding.
            clean_arguments = (
                {k: v for k, v in arguments.items() if k != "_meta"}
                if isinstance(arguments, dict)
                else arguments
            )
            try:
                result = await _original_call_tool(name, clean_arguments, **kwargs)

                # ── W0 Evidence Gate (2026-08-06) ──────────────────────
                # Inspect structured_content from CallToolResult.
                # Catches: silent input dropping, verdict conflicts,
                # null→green coercion.
                sc = getattr(result, "structured_content", None)
                if isinstance(sc, dict):
                    from wealth_mcp.middleware.evidence_middleware import (
                        _estimate_coverage,
                        _material_args,
                        _result_is_empty,
                        _scan_verdict_conflict,
                        MIN_COVERAGE_THRESHOLD,
                    )

                    material = _material_args(clean_arguments)
                    coverage = _estimate_coverage(material, sc.get("result", {}))
                    conflicts = _scan_verdict_conflict(sc)
                    is_empty = (
                        _result_is_empty(sc.get("result", {})) if material else False
                    )

                    w0_gate = "PASS"
                    w0_warnings: list = []
                    material_count = len(material)
                    material_empty = material_count == 0

                    # D1 fix (2026-08-06): zero material args → UNMEASURED, gate FAIL
                    if coverage < 0.0:
                        # -1.0 sentinel from coverage_ratio / _estimate_coverage
                        w0_gate = "FAIL"
                        w0_warnings.append(
                            "UNMEASURED: zero material arguments — coverage cannot be computed. "
                            "No verdict is valid on empty input."
                        )
                    elif coverage < MIN_COVERAGE_THRESHOLD and material:
                        w0_gate = "CAUTION"
                        if coverage == 0.0:
                            w0_warnings.append(
                                f"INSUFFICIENT_EVIDENCE: {material_count} material fields "
                                f"({sorted(material.keys())}) provided but ZERO reflected in result. "
                                "Interpretation prose blocked."
                            )
                        else:
                            w0_warnings.append(
                                f"LOW_COVERAGE: {coverage:.0%} < {MIN_COVERAGE_THRESHOLD:.0%} threshold. "
                                f"{material_count} material fields "
                                f"({sorted(material.keys())}) not reflected in result"
                            )
                    if conflicts:
                        if w0_gate == "PASS":
                            w0_gate = "CAUTION"
                        w0_warnings.extend(f"VERDICT_CONFLICT: {c}" for c in conflicts)
                    if is_empty:
                        if w0_gate == "PASS":
                            w0_gate = "CAUTION"
                        w0_warnings.append(
                            "EMPTY_RESULT: material inputs but all-zeros result"
                        )

                    sc["_w0_evidence_gate"] = {
                        "coverage": coverage if coverage >= 0.0 else "UNMEASURED",
                        "material_args_count": material_count,
                        "material_args": sorted(material.keys()) if material else [],
                        "gate": w0_gate,
                        "warnings": w0_warnings,
                    }
                    if w0_gate in ("CAUTION", "FAIL") and w0_warnings:
                        existing = sc.get("warnings", [])
                        if isinstance(existing, list):
                            sc["warnings"] = existing + [
                                f"[W0] {w}" for w in w0_warnings
                            ]
                    # ── W-005: Inject verdict + coverage into envelope ─
                    if w0_gate == "FAIL":
                        # No verdict — coverage was UNMEASURED
                        sc.pop("verdict", None)
                    elif coverage == 0.0 and material:
                        sc["verdict"] = "INSUFFICIENT_EVIDENCE"
                    elif w0_gate == "CAUTION":
                        sc["verdict"] = "HOLD"
                    else:
                        sc["verdict"] = "PARTIAL"
                    # D4 fix (2026-08-06): derive known from estimated coverage match count
                    _known_estimate = (
                        max(0, round(coverage * material_count))
                        if coverage >= 0.0 and material_count > 0
                        else 0
                    )
                    sc["coverage"] = {
                        "known": _known_estimate,
                        "total": material_count,
                        "ratio": coverage if coverage >= 0.0 else "UNMEASURED",
                    }
                    sc.setdefault(
                        "epistemic",
                        {
                            "tag": sc.get("epistemic_tag", "DERIVED"),
                            "quality": sc.get("evidence_quality", "MODERATE"),
                            "confidence": 0.50,
                        },
                    )
                    # Sync content text blocks so _finalize sees updates
                    if hasattr(result, "content") and result.content:
                        for block in result.content:
                            if hasattr(block, "text"):
                                try:
                                    block.text = json.dumps(sc, default=str)
                                except Exception:
                                    pass
            except Exception as e:
                # Discovery 3: Structured error envelope on failure
                from wealth_mcp.federation_safety import classify_error

                err_env = classify_error(e, source_tool=name, source_organ="wealth")
                receipt_state = _emit_receipt(
                    name,
                    arguments,
                    status="ERROR",
                    verdict=verdict,
                    actor_id=actor_id,
                    session_id=session_id,
                )
                try:
                    from wealth_mcp.mcp_logging import emit_mcp_log

                    await emit_mcp_log(
                        "error",
                        f"WEALTH tool failure on {name}: {type(e).__name__}",
                        tool=name,
                        floor="RUNTIME",
                        verdict="ERROR",
                        logger_name="wealth.envelope",
                        rate_key=f"wealth:{name}:FAIL",
                        extra={
                            "error_type": type(e).__name__,
                            "session_id": session_id,
                        },
                    )
                except Exception:
                    pass
                return _finalize(
                    ToolResult(
                        content=[
                            TextContent(
                                type="text", text=json.dumps(err_env, default=str)
                            )
                        ],
                        meta={"wealth_receipt": receipt_state},
                        is_error=True,
                    ),
                    "ERROR",
                    is_err=True,
                )

            call_status = _tool_result_status(result)
            receipt_state = _emit_receipt(
                name,
                arguments,
                status=call_status,
                verdict=verdict,
                actor_id=actor_id,
                session_id=session_id,
            )
            return _finalize(
                _attach_receipt_meta(result, receipt_state),
                verdict,
                is_err=False,
            )

        mcp.call_tool = _governance_call_tool

        # ── read_resource tracking REMOVED (2026-07-07) ──────────────────
        # Preload mechanism decommissioned. Resources are direct URIs.

        # ── Wealth Surface Filtering Middleware ───────────────────────
        from fastmcp.server.middleware import Middleware

        class WealthSurfaceFilterMiddleware(Middleware):
            async def on_list_tools(self, context, call_next):
                result = await call_next(context)
                if result is None:
                    return result
                public_names = set(PUBLIC_TOOL_NAMES)
                filtered = [
                    t for t in result if getattr(t, "name", None) in public_names
                ]
                return filtered

        mcp.add_middleware(WealthSurfaceFilterMiddleware())

    except Exception as e:
        print(f"[GOVERNANCE] WEALTH federated governance wrapper failed to load: {e}")

    # ── Register tools ────────────────────────────────────────────────────
    # DEREGISTERED 2026-07-10: Legacy surface disabled (43 tools → 8 canonical).
    # Code preserved below for backward compat. Re-enable by uncommenting.
    # See: forge_work/2026-07-10/WEALTH-DEREGISTRATION.md
    # _register_wisdom_tools(mcp)
    # _register_power_tools(mcp)
    # _register_epistemic_tools(mcp)
    # _register_capital_tools(mcp)
    # _register_risk_tools(mcp)
    # _register_legacy_surface_tools(mcp)  # stock, personal, market, omni, agent_path
    # _register_meta_tools(mcp)
    # _register_advanced_tools(mcp)  # beautiful mouse, judge handoff (forged 2026-06-24)
    # _register_optimizer_tools(mcp)  # APEX optimization engines (forged 2026-07-06)
    # _register_auction_tools(
    #     mcp
    # )  # Auction surfaces + coalition games (forged 2026-07-07)
    # register_institutional_tools DELETED 2026-08-06 — C6: INSTITUTIONAL_TOOL_NAMES
    # is empty tuple since Phase 1a. Function is a no-op. All institutional access
    # is now via capital_diagnose(mode=...).
    _register_resources(mcp)
    _register_prompts(mcp)

    # ── Register canonical tools (8-mode surface, 2026-07-07) ──────────
    register_canonical_tools(mcp)

    return mcp


def _register_resources(mcp: FastMCP) -> None:
    """
    Register WEALTH canonical resources (14-resource intelligence substrate).

    RSI refactor (2026-06-27):
    - Renamed URI scheme: afwealth:// → wealth://
    - Renamed functions: afwealth_X → wealth_X
    - Unified metadata: every resource carries name, description, mime_type,
      tags, annotations (readOnlyHint, idempotentHint), and meta.version.
    - Promoted health to dynamic (timestamped).
    - Added 8 new resources: prompts/index, domains/index, reality/context,
      market/sources, risk/thresholds, affordance/contracts,
      handoff/arifos-schema, replay/receipt-schema.
    - Schema now exposes prompt_count, resource_count, full tool surface
      including wealth_fiscal_breakeven and aliases map.

    Resource transport law:
    - Resources move context, not decisions.
    - Prompts move discipline.
    - Tools compute.
    - arifOS judges.
    - Arif decides.

    Architecture (14 resources, 2 layers):

    STATIC SOT (7)              — identity, doctrine, ontology
      1.  wealth://schema
      2.  wealth://tools/registry
      3.  wealth://prompts/index
      4.  wealth://domains/index
      5.  wealth://canon/002-human-law
      6.  wealth://glossary
      7.  wealth://federation/contract

    DYNAMIC REALITY (7)         — live frame for safe intelligence
      8.  wealth://health
      9.  wealth://reality/context
      10. wealth://market/sources
      11. wealth://risk/thresholds
      12. wealth://affordance/contracts
      13. wealth://handoff/arifos-schema
      14. wealth://replay/receipt-schema

    DITEMPA BUKAN DIBERI — Forged, not given.
    """

    # ════════════════════════════════════════════════════════════════════
    # LAYER 1 — STATIC SOT RESOURCES (7)
    # ════════════════════════════════════════════════════════════════════

    # 1. wealth://schema — Organ identity, version, canonical tool surface
    @mcp.resource(
        uri="wealth://schema",
        name="WEALTH Schema",
        description="WEALTH organ identity, version, protocol, and canonical tool surface.",
        mime_type="application/json",
        tags={"wealth", "schema", "sot", "identity"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION, "authority": "advisory_only"},
    )
    def wealth_schema() -> str:
        """WEALTH canonical tool surface and version info."""
        return json.dumps(
            {
                "organ": "WEALTH",
                "version": WEALTH_VERSION,
                "role": "Capital Intelligence for arifOS federation",
                "authority": "WEALTH computes. arifOS judges. Arif decides.",
                "protocol": "MCP 2025-03-26",
                "protocol_seps": ["SEP-1613", "SEP-2106", "SEP-2549", "SEP-1330"],
                "json_schema_dialect": "https://json-schema.org/draft/2020-12/schema",
                "tool_prefixes": ["capital_", "wealth_"],
                "resource_scheme": "wealth://",
                "prompt_count": len(WEALTH_PROMPT_NAMES),
                "resource_count": len(WEALTH_RESOURCE_URIS),
                "naming_convention": "mode-dispatched public tools",
                "public_tool_count": len(PUBLIC_TOOL_NAMES),
                "public_tools": list(PUBLIC_TOOL_NAMES),
                "legacy_tools_reference": [
                    {
                        "name": name,
                        "canonical": canonical,
                        "visibility": "internal_only",
                    }
                    for name, canonical in _INTERNAL_LEGACY_ALIASES.items()
                ],
            },
            indent=2,
        )

    # 2. wealth://tools/registry — Full tool inventory
    @mcp.resource(
        uri="wealth://tools/registry",
        name="WEALTH Tools Registry",
        description="Full tool registry grouped by domain and verb. Includes mutation/irreversibility flags and legacy aliases.",
        mime_type="application/json",
        tags={"wealth", "tools", "registry", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION, "authority": "advisory_only"},
    )
    def wealth_tools_registry() -> str:
        """Full tool registry with classification."""
        return json.dumps(
            {
                "public_tool_count": len(PUBLIC_TOOL_NAMES),
                "public_tools": list(PUBLIC_TOOL_NAMES),
                "legacy_reference": [
                    {
                        "name": name,
                        "canonical": canonical,
                        "visibility": "internal_only",
                    }
                    for name, canonical in _INTERNAL_LEGACY_ALIASES.items()
                ],
                "deprecated": [],
                "aliases": dict(_INTERNAL_LEGACY_ALIASES),
            },
            indent=2,
        )

    # 3. wealth://prompts/index — 7-prompt routing map
    @mcp.resource(
        uri="wealth://prompts/index",
        name="WEALTH Prompts Index",
        description="7 canonical WEALTH prompts — when to use each one. Routing map for prompt selection.",
        mime_type="application/json",
        tags={"wealth", "prompts", "index", "routing", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "count": 7},
    )
    def wealth_prompts_index() -> str:
        """7-prompt routing map."""
        return json.dumps(
            {
                "loop_law": "OBSERVE → CLASSIFY → COMPUTE → CHALLENGE → BOUNDARY → HANDOFF",
                "prompts": [
                    {
                        "name": "wealth_reality_intake_loop",
                        "order": 1,
                        "purpose": "Universal entry point for any WEALTH query",
                        "use_when": [
                            "user query is ambiguous or messy",
                            "first contact on a capital question",
                            "need to separate facts from assumptions",
                        ],
                        "forbidden_outputs": [
                            "buy/sell instruction",
                            "guaranteed return",
                            "legal verdict",
                            "SEAL/VOID as WEALTH verdict",
                        ],
                    },
                    {
                        "name": "wealth_capital_diagnosis_loop",
                        "order": 2,
                        "purpose": "Cashflow / runway / net worth / NPV / IRR / EPF / zakat",
                        "use_when": [
                            "personal finance question",
                            "project valuation",
                            "balance sheet health check",
                            "Malaysian duty calculation",
                        ],
                    },
                    {
                        "name": "wealth_risk_downside_loop",
                        "order": 3,
                        "purpose": "EMV / EVOI / Monte Carlo / asymmetry / false confluence",
                        "use_when": [
                            "downside-first analysis required",
                            "stock pre-trade (folded from wealth_d4_stock_pre_trade)",
                            "irreversible decision pending",
                        ],
                    },
                    {
                        "name": "wealth_market_reality_loop",
                        "order": 4,
                        "purpose": "FX / commodities / macro / Bursa — bind every number to source + timestamp",
                        "use_when": [
                            "any market-sensitive claim",
                            "current data required",
                            "FX, commodity, or Bursa reference",
                        ],
                        "hard_rule": "no live quote without wealth_market_data",
                    },
                    {
                        "name": "wealth_allocation_judgment_loop",
                        "order": 5,
                        "purpose": "Compare options without authorizing capital movement",
                        "use_when": [
                            "A vs B option choice",
                            "portfolio allocation framing",
                            "should I allocate?",
                        ],
                        "hard_rule": "advisory only — never authorizes",
                    },
                    {
                        "name": "wealth_institutional_power_loop",
                        "order": 6,
                        "purpose": "Capture / power audit / Beautiful Mouse / collapse signature",
                        "use_when": [
                            "institutional narrative analysis",
                            "CEO speech / annual report audit",
                            "PETRONAS / MOF / sovereign wealth concerns",
                        ],
                        "hard_rule": "roles not people; diagnostic not accusatory",
                    },
                    {
                        "name": "wealth_arifos_handoff_loop",
                        "order": 7,
                        "purpose": "Prepare clean arifOS judge envelope",
                        "use_when": [
                            "irreversible action pending",
                            "HIGH/CRITICAL risk verdict",
                            "vault write required",
                            "legal or jurisdictional consequence",
                        ],
                        "hard_rule": "default mode = prepare; submit requires explicit authority",
                    },
                ],
            },
            indent=2,
        )

    # 4. wealth://domains/index — WEALTH domain ontology
    @mcp.resource(
        uri="wealth://domains/index",
        name="WEALTH Domains Index",
        description="WEALTH domain ontology — which tools and prompts serve which capital question.",
        mime_type="application/json",
        tags={"wealth", "domains", "ontology", "routing", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27"},
    )
    def wealth_domains_index() -> str:
        """Domain ontology for routing."""
        return json.dumps(
            {
                "domains": {
                    "personal_finance": {
                        "tools": ["capital_health", "capital_primitive"],
                        "prompt": "wealth_capital_diagnosis_loop",
                        "examples": ["cashflow", "runway", "net_worth", "epf", "zakat"],
                    },
                    "capital_valuation": {
                        "tools": ["capital_primitive", "capital_health"],
                        "prompt": "wealth_capital_diagnosis_loop",
                        "examples": [
                            "npv",
                            "irr",
                            "emv",
                            "evoi",
                            "payback",
                            "fiscal_breakeven",
                        ],
                    },
                    "market_macro": {
                        "tools": ["capital_market", "capital_health"],
                        "prompt": "wealth_market_reality_loop",
                        "examples": [
                            "fx",
                            "commodities",
                            "inflation",
                            "rates",
                            "macro",
                        ],
                    },
                    "stock_safety": {
                        "tools": [
                            "capital_market",
                            "capital_primitive",
                            "capital_diagnose",
                        ],
                        "prompts": [
                            "wealth_risk_downside_loop",
                            "wealth_market_reality_loop",
                            "wealth_allocation_judgment_loop",
                        ],
                        "examples": [
                            "verify_math",
                            "pre_trade",
                            "fundamentals",
                            "contrast",
                            "bursa_snapshot",
                        ],
                    },
                    "risk_downside": {
                        "tools": ["capital_primitive", "capital_diagnose"],
                        "prompt": "wealth_risk_downside_loop",
                        "examples": [
                            "asymmetry",
                            "monte_carlo",
                            "false_confluence",
                            "tail",
                        ],
                    },
                    "institutional_power": {
                        "tools": ["capital_diagnose"],
                        "prompt": "wealth_institutional_power_loop",
                        "examples": [
                            "capture",
                            "power_audit",
                            "beautiful_mouse",
                            "collapse",
                        ],
                    },
                    "governance": {
                        "tools": ["wealth_judge_handoff", "capital_ledger"],
                        "prompt": "wealth_arifos_handoff_loop",
                        "examples": ["handoff", "vault", "authority", "888_hold"],
                    },
                    "meta": {
                        "tools": ["capital_registry"],
                        "prompt": "wealth_reality_intake_loop",
                        "examples": ["registry status", "schema", "domains", "health"],
                    },
                },
            },
            indent=2,
        )

    # 4b. wealth://runtime/policy — Discipline contract for tool callers (SOT)
    @mcp.resource(
        uri="wealth://runtime/policy",
        name="WEALTH Runtime Policy",
        description="Discipline contract — required resources per tool class, freshness TTL per dynamic resource, default epistemic state. Read before calling HIGH-risk tools.",
        mime_type="application/json",
        tags={"wealth", "policy", "discipline", "sot", "runtime"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "authority": "WEALTH_RUNTIME"},
    )
    def wealth_runtime_policy() -> str:
        """Discipline contract — what agents MUST do before tool calls."""
        return json.dumps(
            {
                "law": (
                    "WEALTH transports the catalog (tools/resources/prompts). "
                    "WEALTH does NOT enforce prompt→tool sequencing server-side. "
                    "Agents that skip policy are non-compliant."
                ),
                "required_preload": {
                    "capital_primitive": [
                        "wealth://reality/context",
                        "wealth://risk/thresholds",
                    ],
                    "capital_health": ["wealth://reality/context"],
                    "capital_market": ["wealth://market/sources"],
                    "capital_diagnose": [
                        "wealth://risk/thresholds",
                        "wealth://federation/contract",
                    ],
                    "wealth_judge_handoff": [
                        "wealth://handoff/arifos-schema",
                        "wealth://risk/thresholds",
                        "wealth://affordance/contracts",
                    ],
                    "capital_ledger": [
                        "wealth://handoff/arifos-schema",
                        "wealth://replay/receipt-schema",
                    ],
                    "capital_entropy": ["wealth://reality/context"],
                },
                "freshness_ttl_seconds": {
                    "wealth://health": 60,
                    "wealth://reality/context": 3600,
                    "wealth://market/sources": 300,
                    "wealth://risk/thresholds": 86400,
                    "wealth://affordance/contracts": 86400,
                    "wealth://handoff/arifos-schema": 86400,
                    "wealth://replay/receipt-schema": 86400,
                },
                "default_epistemic_state_per_domain": {
                    "capital": "DERIVED",
                    "risk": "DERIVED",
                    "market": "RETRIEVED",
                    "personal": "OBSERVED",
                    "stock": "RETRIEVED",
                    "wisdom": "INTERPRETED",
                    "governance": "DERIVED",
                    "meta": "OBSERVED",
                },
                "receipt_emission": {
                    "path": "/root/VAULT999/wealth/receipts.jsonl",
                    "scope": "every tool call (PASS + BLOCKED)",
                    "schema": "wealth://replay/receipt-schema",
                },
                "non_compliant_behavior": (
                    "Calling a tool without required preload is allowed by MCP "
                    "but produces a NON-COMPLIANT receipt with epistemic_state=DESPITE_RISK."
                ),
                "compliant_receipt_default": (
                    "Receipts auto-emitted on every call. "
                    "Agents can pass actor_id+session_id to bind receipt to session."
                ),
            },
            indent=2,
        )

    # 5. wealth://canon/002-human-law — CANON 002 (markdown)
    @mcp.resource(
        uri="wealth://canon/002-human-law",
        name="WEALTH Canon 002 — Human Law",
        description="CANON 002 — Human Law as Capital Geometry. Draft, pending 888 ratification.",
        mime_type="text/markdown",
        tags={"wealth", "canon", "human-law", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "canon_id": "002"},
    )
    def wealth_canon_002_human_law() -> str:
        """CANON 002 — Human Law as Capital Geometry."""
        canon_path = os.path.join(base_dir, "canon", "002_HUMAN_LAW.md")
        try:
            with open(canon_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps(
                {
                    "error": "canon_002_not_found",
                    "expected_path": canon_path,
                    "fallback": "Law is capital geometry. No value without jurisdiction.",
                },
                indent=2,
            )

    # 6. wealth://glossary — Canonical glossary (markdown)
    @mcp.resource(
        uri="wealth://glossary",
        name="WEALTH Glossary",
        description="WEALTH/arifOS canonical glossary. 999 SEAL ALIVE.",
        mime_type="text/markdown",
        tags={"wealth", "glossary", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "seal": "999_ALIVE"},
    )
    def wealth_glossary() -> str:
        """WEALTH/ArifOS canonical glossary."""
        glossary_path = os.path.join(base_dir, "canon", "GLOSSARY.md")
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps(
                {
                    "error": "glossary_not_found",
                    "expected_path": glossary_path,
                    "fallback_terms": [
                        {"term": "888_HOLD", "def": "Human sovereignty gate"},
                        {"term": "999_SEAL", "def": "Final legitimacy stamp"},
                        {"term": "ΔS", "def": "Entropy delta, must be ≤ 0"},
                        {"term": "F1-F13", "def": "Thirteen constitutional floors"},
                        {"term": "VAULT999", "def": "Append-only immutable ledger"},
                    ],
                },
                indent=2,
            )

    # 7. wealth://federation/contract — Federation contract (markdown)
    @mcp.resource(
        uri="wealth://federation/contract",
        name="WEALTH Federation Contract",
        description="WEALTH federation contract — position, authority, handoffs.",
        mime_type="text/markdown",
        tags={"wealth", "federation", "contract", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "signed_by": "arifOS_888_JUDGE"},
    )
    def wealth_federation_contract() -> str:
        """WEALTH federation contract — position, authority, handoffs."""
        contract_path = os.path.join(base_dir, "FEDERATION_CONTRACT.md")
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps(
                {
                    "organ": "WEALTH",
                    "role": "Capital intelligence — compute, never allocate",
                    "authority_chain": "arifOS (8088) → WEALTH (18082) → A-FORGE (7071) → VAULT999",
                    "owns": [
                        "NPV, IRR, EMV, EVOI, DSCR, payback",
                        "Portfolio allocation modeling",
                        "Market data (FX, commodities, equities)",
                        "D4 stock analysis",
                        "Capital-readiness feeds from GEOX",
                    ],
                    "never": [
                        "Moves capital or executes trades",
                        "Authorizes investment decisions",
                        "Adjudicates constitutional verdicts",
                    ],
                    "verdict": "WEALTH tells you what the capital looks like. It does not move the money. The sovereign decides.",
                },
                indent=2,
            )

    # ════════════════════════════════════════════════════════════════════
    # LAYER 2 — DYNAMIC REALITY RESOURCES (7)
    # ════════════════════════════════════════════════════════════════════

    # 8. wealth://health — Liveness (DYNAMIC — timestamped)
    @mcp.resource(
        uri="wealth://health",
        name="WEALTH Health",
        description="WEALTH organ liveness, transport mode, and final-authority pointer. Dynamic — timestamped on each read.",
        mime_type="application/json",
        tags={"wealth", "health", "liveness", "dynamic"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION},
    )
    def wealth_health() -> str:
        """WEALTH organ health status (dynamic, timestamped)."""
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        return json.dumps(
            {
                "status": "ALIVE",
                "version": WEALTH_VERSION,
                "domain": "WEALTH Federated Domain",
                "transport": "streamable-http",
                "read_only_resources": True,
                "default_authority": "compute_only",
                "mutation_tools": ["capital_ledger"],
                "canonical_tool_count": len(CAPITAL_TOOL_NAMES),
                "public_tool_count": len(PUBLIC_TOOL_NAMES),
                "public_tools": list(PUBLIC_TOOL_NAMES),
                "prompt_count": len(WEALTH_PROMPT_NAMES),
                "resource_count": len(WEALTH_RESOURCE_URIS),
                "final_authority": "arifOS 888_JUDGE → Arif (F13 SOVEREIGN)",
                "timestamp_utc": now.isoformat(),
                "resource_scheme": "wealth://",
            },
            indent=2,
        )

    # 9. wealth://reality/context — Current reality frame (HIGHEST VALUE)
    @mcp.resource(
        uri="wealth://reality/context",
        name="WEALTH Reality Context",
        description="Current reality frame — timezone, market-data policy, advice policy, stale-data warnings. Load BEFORE computing.",
        mime_type="application/json",
        tags={"wealth", "reality", "context", "dynamic", "frame"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "load_order": "before_compute"},
    )
    def wealth_reality_context() -> str:
        """Reality frame — bind every WEALTH output to current policy."""
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        return json.dumps(
            {
                "as_of": now.strftime("%Y-%m-%d"),
                "as_of_utc": now.isoformat(),
                "timezone_primary": "Asia/Kuala_Lumpur",
                "actor_default": "ARIF",
                "market_data_policy": "current-sensitive claims require capital_market with timestamp",
                "financial_advice_policy": "advisory only — no buy/sell/move-money instruction from WEALTH",
                "epistemic_default": "DERIVED unless evidence is observed",
                "stale_data_warning_threshold_hours": 24,
                "hard_stops": [
                    "irreversible capital action without arifOS judgment",
                    "guaranteed-return language",
                    "live quote without source + timestamp",
                    "vault write without human confirmation",
                    "legal or jurisdictional verdict",
                    "SEAL/VOID issued by WEALTH (must come from arifOS)",
                ],
                "authority_chain": "WEALTH computes → arifOS judges → Arif decides",
                "session_id_required_for": [
                    "capital_ledger(mode='write')",
                    "wealth_judge_handoff",
                ],
                "actor_verification_required_for": [
                    "capital_ledger(mode='write')",
                    "wealth_judge_handoff(mode='submit')",
                ],
                "prompt_layer_count": 7,
                "resource_layer_count": 15,
                "law": "Resources store the reality frame that prevents bad answers.",
            },
            indent=2,
        )

    # 10. wealth://market/sources — Source map and freshness rules
    @mcp.resource(
        uri="wealth://market/sources",
        name="WEALTH Market Sources",
        description="Source map and freshness rules for FX, commodities, macro, and Bursa evidence. Prevents stale 'live' hallucination.",
        mime_type="application/json",
        tags={"wealth", "market", "sources", "freshness", "dynamic"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27"},
    )
    def wealth_market_sources() -> str:
        """Market source map with freshness rules."""
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        return json.dumps(
            {
                "as_of_utc": now.isoformat(),
                "freshness_enforcement": {
                    "fx_max_lag_minutes": 15,
                    "commodity_max_lag_minutes": 60,
                    "macro_max_lag_days": 30,
                    "bursa_max_lag_minutes": 15,
                },
                "sources": {
                    "fx": {
                        "tool": "capital_market",
                        "mode": "fx",
                        "freshness_required": True,
                        "acceptable_lag_minutes": 15,
                        "common_pairs": ["USD/MYR", "USD/SGD", "GBP/MYR", "EUR/MYR"],
                    },
                    "commodity": {
                        "tool": "capital_market",
                        "mode": "commodity",
                        "freshness_required": True,
                        "acceptable_lag_minutes": 60,
                        "tracked": [
                            "brent_crude",
                            "wti_crude",
                            "gold",
                            "palm_oil",
                            "natural_gas",
                        ],
                    },
                    "macro": {
                        "tool": "capital_market",
                        "mode": "indicator",
                        "freshness_required": False,
                        "lag_expected": True,
                        "typical_lag_days": 30,
                        "indicators": [
                            "usd_myr",
                            "inflation",
                            "interest_rate",
                            "gdp_growth",
                        ],
                    },
                    "bursa": {
                        "tool": "capital_market",
                        "mode": "stock",
                        "freshness_required": True,
                        "execution_grade": False,
                        "note": "Bursa data is informational, not execution-grade",
                    },
                },
                "freshness_law": (
                    "If a claim is current-sensitive, the WEALTH output must cite "
                    "the capital_market call that produced it, with timestamp. "
                    "Stale data → stale answer → 888_HOLD recommended."
                ),
            },
            indent=2,
        )

    # 11. wealth://risk/thresholds — LOW/MEDIUM/HIGH/CRITICAL thresholds
    @mcp.resource(
        uri="wealth://risk/thresholds",
        name="WEALTH Risk Thresholds",
        description="Canonical LOW/MEDIUM/HIGH/CRITICAL risk thresholds and 888_HOLD triggers. Shared by all prompts and tools.",
        mime_type="application/json",
        tags={"wealth", "risk", "thresholds", "governance", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "authority": "arifOS_888_JUDGE"},
    )
    def wealth_risk_thresholds() -> str:
        """Risk thresholds and hard stops."""
        return json.dumps(
            {
                "risk_thresholds": {
                    "LOW": [0.0, 0.24],
                    "MEDIUM": [0.25, 0.49],
                    "HIGH": [0.50, 0.74],
                    "CRITICAL": [0.75, 1.0],
                },
                "hard_stops": [
                    "irreversible capital action without arifOS judgment",
                    "missing downside case",
                    "HIGH or CRITICAL downside without handoff",
                    "vault write without human confirmation",
                    "legal or jurisdictional consequence",
                    "unverified market data for current-sensitive claim",
                ],
                "required_action": {
                    "LOW": "proceed with standard reporting",
                    "MEDIUM": "flag risk in output; consider handoff if other factors elevate",
                    "HIGH": "wealth_judge_handoff(mode='prepare')",
                    "CRITICAL": "888_HOLD — do not proceed without Arif",
                },
                "scope_note": (
                    "Thresholds apply to WEALTH-computed risk scores. "
                    "External signals (market shock, legal ruling, geopolitical event) "
                    "may independently trigger 888_HOLD regardless of computed score."
                ),
            },
            indent=2,
        )

    # 12. wealth://affordance/contracts — Tool authority map
    @mcp.resource(
        uri="wealth://affordance/contracts",
        name="WEALTH Affordance Contracts",
        description="Tool authority, mutation, and irreversibility map. Agents read this BEFORE calling tools to know what blast radius to expect.",
        mime_type="application/json",
        tags={"wealth", "affordance", "contracts", "tool-authority", "sot"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27"},
    )
    def wealth_affordance_contracts() -> str:
        """Tool authority contracts."""
        return json.dumps(
            {
                "contracts": {
                    "capital_primitive": {
                        "action_class": "COMPUTE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "capital_health": {
                        "action_class": "COMPUTE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "capital_diagnose": {
                        "action_class": "SIMULATE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "capital_market": {
                        "action_class": "OBSERVE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                        "freshness_required": True,
                    },
                    "capital_ledger": {
                        "action_class": "IRREVERSIBLE",
                        "mutation": True,
                        "irreversible": True,
                        "query_override": "READONLY",
                        "requires_888_hold": True,
                        "side_effects": "query is read-only; write requires arifOS SEAL and human acknowledgment",
                    },
                    "capital_registry": {
                        "action_class": "OBSERVE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "capital_entropy": {
                        "action_class": "SIMULATE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "optional local dependency; unavailable is reported explicitly",
                    },
                    "wealth_judge_handoff": {
                        "action_class": "HANDOFF",
                        "mutation": False,
                        "irreversible": False,
                        "mode_default": "prepare",
                        "submit_requires_authority": True,
                        "side_effects": "prepare builds envelope; submit delegates verdict to arifOS",
                    },
                },
                "law": (
                    "ANALYZE/OBSERVE/READ/META/SYNTHESIZE → safe to call. "
                    "WRITE/HANDOFF with submit=true → 888_HOLD + actor verification."
                ),
            },
            indent=2,
        )

    # 13. wealth://handoff/arifos-schema — Judge envelope schema
    @mcp.resource(
        uri="wealth://handoff/arifos-schema",
        name="WEALTH arifOS Handoff Schema",
        description="Required fields for wealth_judge_handoff envelope. Read before preparing any irreversible or governance-sensitive handoff.",
        mime_type="application/json",
        tags={"wealth", "handoff", "arifos", "schema", "governance"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "authority": "arifOS_888_JUDGE"},
    )
    def wealth_handoff_arifos_schema() -> str:
        """Handoff envelope schema."""
        return json.dumps(
            {
                "endpoint": "wealth_judge_handoff",
                "modes": ["prepare", "submit"],
                "mode_default": "prepare",
                "submit_requires_explicit_authority": True,
                "envelope": {
                    "required_fields": [
                        "tool_name",
                        "result",
                        "intent",
                        "capability",
                        "blast_radius",
                        "reversibility_level",
                        "epistemic_state",
                        "domain",
                        "evidence",
                    ],
                    "field_types": {
                        "tool_name": "string — the WEALTH tool that produced the verdict",
                        "result": "object|string — the tool result, JSON-serializable",
                        "intent": "string — what capital decision is being proposed",
                        "capability": "string — the specific capability requested",
                        "blast_radius": "enum LOW|MEDIUM|HIGH|CRITICAL",
                        "reversibility_level": "enum FULL|PARTIAL|NONE",
                        "epistemic_state": "enum OBSERVED|DERIVED|INTERPRETED|SPECULATED",
                        "domain": "enum capital|risk|power|wisdom|collapse|meta",
                        "evidence": "array — list of evidence objects with source + rung",
                    },
                    "optional_fields": [
                        "session_id",
                        "actor_id",
                        "context",
                    ],
                },
                "common_capabilities": [
                    "register_collapse_signature_claim",
                    "execute_stock_trade",
                    "issue_capital_recommendation",
                    "vault_write",
                    "authorize_irreversible_action",
                ],
                "response_shape": {
                    "prepare": "envelope + readiness + missing_fields",
                    "submit": "verdict + constitutional_chain_id + judge_state_hash",
                },
                "law": (
                    "WEALTH prepares the envelope. arifOS judges. "
                    "WEALTH never claims a verdict before arifOS responds."
                ),
            },
            indent=2,
        )

    # 14. wealth://replay/receipt-schema — Replayable workflow receipt schema
    @mcp.resource(
        uri="wealth://replay/receipt-schema",
        name="WEALTH Replay Receipt Schema",
        description="Schema for replayable WEALTH workflow receipts. Every consequential WEALTH call should produce a receipt that can be replayed, audited, or sealed.",
        mime_type="application/json",
        tags={"wealth", "replay", "receipt", "schema", "audit"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": "2026.06.27", "authority": "VAULT999"},
    )
    def wealth_replay_receipt_schema() -> str:
        """Replay receipt schema."""
        return json.dumps(
            {
                "receipt_version": "2026.06.27",
                "purpose": "Replayable workflow receipt for WEALTH calls. Required for audit-grade outputs and any irreversible action.",
                "schema": {
                    "required_fields": [
                        "receipt_id",
                        "timestamp_utc",
                        "actor_id",
                        "tool_name",
                        "arguments",
                        "result",
                        "epistemic_state",
                        "evidence_quality",
                        "domain",
                    ],
                    "optional_fields": [
                        "session_id",
                        "trace_id",
                        "constitutional_chain_id",
                        "judge_state_hash",
                        "parent_receipt_id",
                    ],
                },
                "field_types": {
                    "receipt_id": "string — uuid v4 or hash-prefixed id",
                    "timestamp_utc": "string — ISO-8601 UTC",
                    "actor_id": "string — who triggered the call",
                    "tool_name": "string — WEALTH tool name",
                    "arguments": "object — sanitized arguments (no secrets)",
                    "result": "object|string — tool output, JSON-serializable",
                    "epistemic_state": "enum OBSERVED|DERIVED|INTERPRETED|SPECULATED",
                    "evidence_quality": "enum OBSERVED|RETRIEVED|MEMORY|INFERRED|MISSING",
                    "domain": "enum capital|risk|power|wisdom|collapse|meta|governance",
                },
                "replay_law": (
                    "Given the same tool_name + arguments + state, a WEALTH receipt "
                    "MUST be replayable and produce a comparable result (modulo live "
                    "market data which must be timestamped and re-validated)."
                ),
                "storage": {
                    "primary": "VAULT999 append-only ledger",
                    "secondary": "WEALTH local JSONL log at /root/VAULT999/wealth/receipts.jsonl",
                },
                "law": "No receipt, no authority. Receipts are the audit trail.",
            },
            indent=2,
        )

    # ── Zen Phase 5: New resources ──────────────────────────────────
    # 3 of 7 directive-specified resources. The remaining 4
    # (vitals/sealed, vitals/history, amendments/registry, methods/sensitivity)
    # require sealed PETRONAS data — gated on sovereign release.

    # 15. wealth://schema/field-dictionary
    @mcp.resource(
        uri="wealth://schema/field-dictionary",
        name="Field Dictionary",
        description="Per-mode required and optional fields for capital_diagnose and capital_health, with types, units, and aliases.",
        mime_type="application/json",
        tags={"wealth", "schema", "fields", "reference"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION, "authority": "advisory_only"},
    )
    def wealth_field_dictionary() -> str:
        """Field dictionary for capital_diagnose and capital_health modes."""
        return json.dumps(
            {
                "_description": "Field dictionary for WEALTH diagnostic tools. Each mode lists expected fields with aliases.",
                "capital_health": {
                    "survival": {
                        "submodes": {
                            "personal_finance": {
                                "monthly_income_v": "float USD",
                                "monthly_expenses_v": "float USD",
                                "liquid_assets": "float USD",
                                "horizon_months": "int",
                            },
                            "corporate_runway": {
                                "liquid_assets": "float RM",
                                "monthly_burn": "float RM",
                            },
                            "sovereign_fiscal": {
                                "total_govt_expenditure": "float RM",
                                "non_oil_revenue": "float RM",
                                "petronas_dividend_base_rm": "float RM",
                                "oil_price_assumption_usd": "float USD",
                            },
                        },
                        "note": "Unknown submode returns structured UNKNOWN_SUBMODE error. No silent default.",
                    },
                },
                "capital_diagnose": {
                    "stress_index": {
                        "required_fields": 16,
                        "fields": {
                            "financial": [
                                "profit_change_pct",
                                "revenue_change_pct",
                                "cost_cutting_announced",
                                "sovereign_extraction",
                                "cffo",
                                "fcf",
                                "gearing",
                            ],
                            "governance": [
                                "board_size",
                                "board_resignations_12m",
                                "company_secretaries_as_directors",
                                "avg_tenure_years",
                                "governance_separation_index",
                            ],
                            "workforce": [
                                "rightsizing_pct",
                                "voluntary_exits_pct",
                                "key_personnel_departures",
                            ],
                            "legal": [
                                "active_litigation_count",
                                "injunction_value_musd",
                                "regulatory_uncertainty_score",
                            ],
                            "exploitation": [
                                "counterparty_payment_freeze",
                                "interpleader_filed",
                                "competing_claims",
                            ],
                        },
                        "aliases": {
                            "financial.sovereign_extraction": [
                                "sovereign_extraction_pct",
                                "sovereign_extraction_gauge",
                            ],
                            "financial.cffo": ["cffo_rm_b"],
                            "financial.fcf": ["fcf_rm_b"],
                            "financial.gearing": ["gearing_ratio_pct"],
                            "governance.governance_separation_index": [
                                "governance_separation"
                            ],
                        },
                        "coverage_gate": "coverage < 15% → risk_level downgraded to INSUFFICIENT_DATA",
                        "confidence_cap": "0.90 per F7 HUMILITY",
                    },
                    "governance_capacity": {
                        "fields": [
                            "board_members (list of {name, independent})",
                            "committees (list of {name, members, independent_chair})",
                            "stress_level (float 0-1)",
                        ],
                    },
                },
                "common_rules": {
                    "sessions": "session_id required for all WEALTH tools",
                    "epistemic_tags": "OBS=observed, DER=derived, INT=interpreted, SPEC=speculated",
                    "confidence_cap": "0.90 per F7 HUMILITY",
                    "unknown_enum": "All tools return structured error for unknown modes/submodes, never MCP -32602",
                },
            },
            indent=2,
        )

    # 16. wealth://epistemic/tag-definitions
    @mcp.resource(
        uri="wealth://epistemic/tag-definitions",
        name="Epistemic Tag Definitions",
        description="OBS/DER/INT/SPEC definitions and the rules for assigning each in WEALTH responses.",
        mime_type="application/json",
        tags={"wealth", "epistemic", "governance", "reference"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION, "authority": "binding"},
    )
    def wealth_epistemic_tags() -> str:
        """Epistemic tag definitions and assignment rules."""
        return json.dumps(
            {
                "tags": {
                    "OBS": {
                        "label": "Observed",
                        "rule": "Direct measurement from live feed, sealed document, or audit trail. Source must be cited.",
                        "examples": [
                            "Brent price from live commodity engine",
                            "PAT from audited annual report",
                        ],
                    },
                    "DER": {
                        "label": "Derived",
                        "rule": "Computed from OBS inputs through a declared formula. Formula must be cited.",
                        "examples": [
                            "NPV from cash_flows × discount_rate",
                            "Stress index from 5 component scores",
                        ],
                    },
                    "INT": {
                        "label": "Interpreted",
                        "rule": "Pattern recognized from DER evidence. Must cite the pattern logic and confidence.",
                        "examples": [
                            "Cascade detection from temporal stress patterns",
                            "Governance capacity gap from board composition",
                        ],
                    },
                    "SPEC": {
                        "label": "Speculated",
                        "rule": "Extrapolation or analogy without verifiable evidence. Must NOT carry evidence_quality >= MODERATE.",
                        "examples": [
                            "Keyword-overlap alignment scores",
                            "Scenario projections without held-out validation",
                        ],
                    },
                },
                "assignment_rules": {
                    "SPEC may never carry evidence_quality >= MODERATE": "Enforced at wrap_result level",
                    "DER and INT require source_attribution": "Non-empty list",
                    "Confidence capped at 0.90": "Per F7 HUMILITY, enforced at engine level",
                    "metric_purpose_audit is SPEC/MISSING": "Keyword overlap is not semantic analysis (Phase 3, 2026-08-03)",
                },
            },
            indent=2,
        )

    # 17. wealth://provenance/feeds
    @mcp.resource(
        uri="wealth://provenance/feeds",
        name="Market Feed Provenance",
        description="Every market feed: source, update cadence, licence, known lag, and routing.",
        mime_type="application/json",
        tags={"wealth", "market", "provenance", "reference"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
        meta={"version": WEALTH_VERSION, "authority": "advisory_only"},
    )
    def wealth_feed_provenance() -> str:
        """Market feed provenance and routing."""
        return json.dumps(
            {
                "routing": {
                    "commodity_engine_live": "Used for: brent_crude, wti_crude, natural_gas, lng_asia, gold. Source: wealth_core.commodity_engines.get_snapshot(). Latency: <60s from exchange. Feed type: LIVE.",
                    "legacy_market_data": "Used for: FX, indicators, stocks, unmapped commodities. Source: wealth_market_data engine. Feed type: CACHED/ESTIMATE — check staleness_class.",
                },
                "feed_types": {
                    "LIVE": {"max_age": 300, "can_carry": "MODERATE or better"},
                    "AGING": {"max_age": 3600, "can_carry": "MODERATE"},
                    "STALE": {"max_age": 86400, "can_carry": "WEAK only"},
                    "EXPIRED": {
                        "min_age": 86400,
                        "action": "ERROR — no value returned",
                    },
                    "ESTIMATE": {
                        "action": "May never carry evidence_quality >= MODERATE"
                    },
                },
                "commodity_sources": {
                    "brent_crude": {
                        "symbol": "XBRENT",
                        "source": "ICE via commodity engine (live)",
                        "as_of": "streaming",
                    },
                    "gold": {
                        "symbol": "XAUUSD",
                        "source": "COMEX via commodity engine (live)",
                        "as_of": "streaming",
                    },
                    "natural_gas": {
                        "symbol": "XNATGAS",
                        "source": "NYMEX via commodity engine (live)",
                        "as_of": "streaming",
                    },
                },
                "cross_witness_rule": "One feed is not a witness. Two independent sources with delta > 3% → WITNESS_DIVERGENCE warning.",
            },
            indent=2,
        )


def _register_prompts(mcp: FastMCP) -> None:
    """
    Register WEALTH canonical prompts (7-prompt intelligence layer).

    Prompt transport law:
    - Prompts move discipline, not data.
    - Resources move context.
    - Tools compute.
    - arifOS judges.
    - Arif decides.

    These 7 prompts cover general WEALTH intelligence:
      1. wealth_reality_intake_loop        — universal entry
      2. wealth_capital_diagnosis_loop     — cashflow / runway / valuation
      3. wealth_risk_downside_loop         — EMV / EVOI / asymmetry
      4. wealth_market_reality_loop        — FX / commodities / macro
      5. wealth_allocation_judgment_loop   — compare options (advisory only)
      6. wealth_institutional_power_loop   — capture / collapse
      7. wealth_arifos_handoff_loop        — prepare arifOS judge envelope

    Replaces the prior 2-prompt layer (wealth_capital_deal_brief and
    wealth_d4_stock_pre_trade). Stock intelligence is folded under
    wealth_risk_downside_loop + wealth_market_reality_loop +
    wealth_allocation_judgment_loop. Stock is a use case, not a top-level
    WEALTH loop.

    v2026.07.10: All prompts upgraded to return messages[] with embedded
    resource context (MCP Bindings #23–26). FastMCP infers PromptArgument[]
    from function signature; docstring Args: drives completion API.

    DITEMPA BUKAN DIBERI — Forged, not given.
    """

    # ── Prompt helper: text message (Binding #23) ──
    def _msg_text(text: str, role: str = "user") -> Message:
        return Message(text, role=role)

    # ── Prompt helper: embedded resource message (Binding #23) ──
    def _msg_resource(uri: str, text: str, mime: str = "text/plain") -> Message:
        return Message(
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=AnyUrl(uri),
                    mimeType=mime,
                    text=text,
                ),
            ),
            role="user",
        )

    # ────────────────────────────────────────────────────────────────────
    # 1. wealth_reality_intake_loop
    # Universal WEALTH intake. First prompt for any capital/market/risk/
    # personal finance / institutional query.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_reality_intake_loop",
        description=(
            "Universal WEALTH intake loop for any capital, market, risk, "
            "personal finance, or institutional query. Separates facts from "
            "assumptions, classifies domain, routes to minimum tools, blocks "
            "premature conclusions."
        ),
        tags={"wealth", "intake", "reality", "routing"},
        meta={
            "version": "2026.07.10",
            "loop": "observe-classify-compute-challenge-boundary-handoff",
        },
    )
    def wealth_reality_intake_loop(
        query: str,
        actor_context: str = "ARIF",
        known_facts: str = "",
        constraints: str = "",
    ) -> list[Message]:
        """
        Convert messy human intent into structured WEALTH context.
        Separate facts, assumptions, missing data, and forbidden conclusions.
        Route to the right WEALTH tools.

        Args:
            query: The user's capital/market/risk query text
            actor_context: Who is asking (default "ARIF")
            known_facts: Facts already known about the situation
            constraints: Constraints on the analysis
        """
        body = (
            "# WEALTH Reality Intake Loop\n\n"
            "## User query\n"
            f"{query}\n\n"
            "## Actor context\n"
            f"{actor_context}\n\n"
            "## Known facts\n"
            f"{known_facts}\n\n"
            "## Constraints\n"
            f"{constraints}\n\n"
            "## Required loop\n\n"
            "1. **OBSERVE** — separate:\n"
            "   - facts given by user\n"
            "   - assumptions\n"
            "   - missing data\n"
            "   - time-sensitive claims\n"
            "   - claims requiring live data\n\n"
            "2. **CLASSIFY** — choose the primary WEALTH domain:\n"
            "   - personal_finance\n"
            "   - capital_valuation\n"
            "   - project_deal\n"
            "   - market_macro\n"
            "   - stock_safety\n"
            "   - risk_downside\n"
            "   - power_capture\n"
            "   - institutional_collapse\n"
            "   - governance_handoff\n\n"
            "3. **ROUTE** — select the minimum necessary WEALTH tools. "
            "Do not over-call tools.\n\n"
            "4. **REALITY CHECK** — if data is missing, say exactly what is "
            "missing. If market data is current-sensitive, require "
            "`wealth_market_data`. If the query asks for action, separate "
            "analysis from authorization.\n\n"
            "5. **BOUNDARY** — never output:\n"
            "   - buy/sell instruction\n"
            "   - guaranteed return\n"
            "   - legal verdict\n"
            "   - capital authorization\n"
            "   - SEAL / VOID as WEALTH verdict\n\n"
            "6. **NEXT SAFE STEP** — return:\n"
            "   - best tool route\n"
            "   - expected output\n"
            "   - missing data\n"
            "   - whether arifOS handoff is required\n"
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://capabilities",
                "Load WEALTH tool registry for available tools.",
                "application/json",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 2. wealth_capital_diagnosis_loop
    # Balance sheet, cashflow, runway, NPV/IRR, personal + project capital.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_capital_diagnosis_loop",
        description=(
            "General capital diagnosis loop for cashflow, runway, net worth, "
            "NPV, IRR, EPF, zakat, and project economics."
        ),
        tags={"wealth", "capital", "personal-finance", "valuation"},
        meta={"version": "2026.07.10"},
    )
    def wealth_capital_diagnosis_loop(
        case: str,
        scale: str = "personal",
        numbers_available: str = "",
        horizon: str = "",
    ) -> list[Message]:
        """
        Diagnose capital health across conservation, flow, survival, value,
        and Malaysian-specific duties (EPF, zakat).

        Args:
            case: Description of the capital situation
            scale: "personal" or "enterprise" or "sovereign"
            numbers_available: What financial numbers are known
            horizon: Time horizon for the diagnosis
        """
        body = (
            "# WEALTH Capital Diagnosis Loop\n\n"
            "## Case\n"
            f"{case}\n\n"
            "## Scale\n"
            f"{scale}\n\n"
            "## Numbers available\n"
            f"{numbers_available}\n\n"
            "## Horizon\n"
            f"{horizon}\n\n"
            "## Required sequence\n\n"
            "1. **CONSERVATION** — what assets, liabilities, reserves, and "
            "obligations exist? Use `wealth_conservation_check` or "
            "`wealth_personal_finance(mode='net_worth')`.\n\n"
            "2. **FLOW** — what income, expenses, burn, or cashflow exists? "
            "Use `wealth_flow_check` or "
            "`wealth_personal_finance(mode='summary')`.\n\n"
            "3. **SURVIVAL** — how long can the system survive under current "
            "burn? Use `wealth_runway_check` or "
            "`wealth_personal_finance(mode='runway')`.\n\n"
            "4. **VALUE** — if this is a project or deal, compute:\n"
            "   - NPV via `wealth_compute_npv`\n"
            "   - IRR via `wealth_compute_irr`\n"
            "   - EMV via `wealth_compute_emv` if scenarios exist\n\n"
            "5. **MALAYSIAN DUTIES** — if personal Malaysian wealth is "
            "involved, check:\n"
            "   - EPF readiness\n"
            "   - zakat if wealth is above nisab\n"
            "   Use `wealth_personal_finance(mode='epf'|'zakat')`.\n\n"
            "6. **OUTPUT FORMAT** — return:\n"
            "   - capital health\n"
            "   - weakest number\n"
            "   - missing data\n"
            "   - downside case\n"
            "   - next safe action\n\n"
            "## Forbidden\n"
            "Do not recommend moving money.\n"
            'Do not say "financially safe" without downside and uncertainty.\n'
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://diagnosis/case",
                f"Case: {case}\nScale: {scale}\nNumbers: {numbers_available}\nHorizon: {horizon}",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 3. wealth_risk_downside_loop
    # Downside-first risk intelligence. EMV, EVOI, Monte Carlo, asymmetry,
    # false confluence, tail risk, uncertainty.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_risk_downside_loop",
        description=(
            "Downside-first risk loop for EMV, EVOI, Monte Carlo, asymmetry, "
            "false confluence, and uncertainty."
        ),
        tags={"wealth", "risk", "downside", "uncertainty"},
        meta={"version": "2026.07.10"},
    )
    def wealth_risk_downside_loop(
        decision: str,
        scenarios: str = "",
        evidence_quality: str = "unknown",
        irreversible: str = "false",
    ) -> list[Message]:
        """
        Force downside-first analysis before any expected-value claim.
        Stock pre-trade logic folded here.

        Args:
            decision: The decision being evaluated
            scenarios: Known scenarios (base, upside, downside, ruin)
            evidence_quality: Quality of evidence available
            irreversible: Whether the decision is irreversible
        """
        body = (
            "# WEALTH Risk + Downside Loop\n\n"
            "## Decision\n"
            f"{decision}\n\n"
            "## Scenarios\n"
            f"{scenarios}\n\n"
            "## Evidence quality\n"
            f"{evidence_quality}\n\n"
            "## Irreversible?\n"
            f"{irreversible}\n\n"
            "## Required sequence\n\n"
            "1. **DOWNSIDE FIRST** — state the worst credible loss before "
            "the expected gain.\n\n"
            "2. **SCENARIO MAP** — identify:\n"
            "   - base case\n"
            "   - upside case\n"
            "   - downside case\n"
            "   - ruin case\n"
            "   - missing scenario\n\n"
            "3. **COMPUTE** — use only if inputs exist:\n"
            "   - `wealth_compute_emv`\n"
            "   - `wealth_compute_evoi`\n"
            "   - `wealth_monte_carlo_simulate`\n"
            "   - `wealth_asymmetry_check`\n"
            "   - `wealth_confluence_check`\n\n"
            "4. **CONTRADICTION** — ask:\n"
            "   - are indicators independent?\n"
            "   - is confluence fake?\n"
            "   - is one assumption carrying the whole thesis?\n"
            "   - what evidence would reverse the conclusion?\n\n"
            "5. **BOUNDARY** — if irreversible=true or downside is "
            "HIGH/CRITICAL: prepare `wealth_judge_handoff(mode='prepare')`.\n\n"
            "6. **OUTPUT** — return:\n"
            "   - risk verdict: LOW / MEDIUM / HIGH / CRITICAL\n"
            "   - dominant risk\n"
            "   - missing data\n"
            "   - whether 888_HOLD is required\n\n"
            "## Forbidden\n"
            "Do not hide downside behind expected value.\n"
            "Do not use precise decimals when evidence quality is weak.\n"
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://risk/decision",
                f"Decision: {decision}\nIrreversible: {irreversible}\nEvidence quality: {evidence_quality}",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 4. wealth_market_reality_loop
    # Force reality alignment before market/macro statements.
    # Hard rule: no "live" claim without market data source or timestamp.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_market_reality_loop",
        description=(
            "Reality-aligned market and macro prompt for FX, commodities, "
            "macro indicators, Bursa evidence, and time-sensitive claims."
        ),
        tags={"wealth", "market", "macro", "reality"},
        meta={"version": "2026.07.10"},
    )
    def wealth_market_reality_loop(
        market_question: str,
        geography: str = "Malaysia",
        asset_or_indicator: str = "",
        as_of_date: str = "",
    ) -> list[Message]:
        """
        Bind every market claim to a source + timestamp. No naked numbers.

        Args:
            market_question: What market data is being queried
            geography: Geographic context (default Malaysia)
            asset_or_indicator: Specific asset or indicator
            as_of_date: Date for time-sensitive claims
        """
        body = (
            "# WEALTH Market Reality Loop\n\n"
            "## Market question\n"
            f"{market_question}\n\n"
            "## Geography\n"
            f"{geography}\n\n"
            "## Asset or indicator\n"
            f"{asset_or_indicator}\n\n"
            "## As-of date\n"
            f"{as_of_date}\n\n"
            "## Required sequence\n\n"
            "1. **TIME LOCK** — determine whether the claim is "
            "current-sensitive. If yes, do not answer from memory.\n\n"
            "2. **SOURCE** — use `wealth_market_data` for:\n"
            "   - FX\n"
            "   - commodities\n"
            "   - macro indicators\n\n"
            "   Use `wealth_stock_analysis(mode='bursa_snapshot'|'bursa_evidence')` "
            "for Bursa stock evidence if available.\n\n"
            "3. **CONTEXT** — separate:\n"
            "   - latest data\n"
            "   - lagged data\n"
            "   - estimates\n"
            "   - stale assumptions\n\n"
            "4. **INTERPRETATION** — explain what the number means for:\n"
            "   - capital flow\n"
            "   - risk\n"
            "   - runway\n"
            "   - valuation\n"
            "   - sovereign exposure\n\n"
            "5. **OUTPUT** — return:\n"
            "   - value observed\n"
            "   - timestamp or as-of date\n"
            "   - source class\n"
            "   - confidence\n"
            "   - what cannot be concluded\n\n"
            "## Forbidden\n"
            'Do not call an old number "live."\n'
            "Do not infer investment action from market data alone.\n"
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://market/query",
                f"Market question: {market_question}\nGeography: {geography}\nAsset: {asset_or_indicator}\nAs-of: {as_of_date}",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 5. wealth_allocation_judgment_loop
    # Compare options without authorizing capital movement.
    # Hard rule: advisory only. No buy/sell/move-money instruction.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_allocation_judgment_loop",
        description=(
            "Advisory allocation judgment loop for comparing options without "
            "authorizing capital movement."
        ),
        tags={"wealth", "allocation", "judgment", "governance"},
        meta={"version": "2026.07.10"},
    )
    def wealth_allocation_judgment_loop(
        options: str,
        capital_available: str = "",
        objective: str = "",
        constraints: str = "",
    ) -> list[Message]:
        """
        Compare options. Output is advisory only — never authorizes capital
        movement. Stock-vs-stock and project-vs-project sit here.

        Args:
            options: The options being compared
            capital_available: How much capital is available
            objective: What the allocation aims to achieve
            constraints: Constraints on the allocation
        """
        body = (
            "# WEALTH Allocation Judgment Loop\n\n"
            "## Options\n"
            f"{options}\n\n"
            "## Capital available\n"
            f"{capital_available}\n\n"
            "## Objective\n"
            f"{objective}\n\n"
            "## Constraints\n"
            f"{constraints}\n\n"
            "## Required sequence\n\n"
            "1. **DEFINE THE GAME** — what is being allocated?\n"
            "   - money\n"
            "   - time\n"
            "   - attention\n"
            "   - debt capacity\n"
            "   - strategic option\n"
            "   - national resource\n\n"
            "2. **SCORE EACH OPTION** — for each option, evaluate:\n"
            "   - NPV / value\n"
            "   - risk\n"
            "   - reversibility\n"
            "   - time horizon\n"
            "   - liquidity\n"
            "   - dignity / maruah impact\n"
            "   - opportunity cost\n"
            "   - hidden dependency\n\n"
            "3. **COMPUTE WHERE POSSIBLE** — use:\n"
            "   - `wealth_compute_npv`\n"
            "   - `wealth_compute_irr`\n"
            "   - `wealth_compute_emv`\n"
            "   - `wealth_compute_evoi`\n"
            "   - `wealth_power_audit`\n"
            "   - `wealth_wisdom_evaluate`\n\n"
            "4. **COMPARE** — rank options by:\n"
            "   - survival first\n"
            "   - downside second\n"
            "   - expected value third\n"
            "   - optionality fourth\n"
            "   - dignity always\n\n"
            "5. **AUTHORITY** — if recommendation implies actual capital "
            "movement: do not authorize. Prepare "
            "`wealth_judge_handoff(mode='prepare')`.\n\n"
            "6. **OUTPUT** — return:\n"
            "   - preferred option for study\n"
            "   - rejected options and why\n"
            "   - missing data\n"
            "   - 888_HOLD status\n\n"
            "## Forbidden\n"
            'Do not say "allocate now."\n'
            'Say "best candidate for further study" unless arifOS has judged.\n'
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://allocation/options",
                f"Options: {options}\nCapital: {capital_available}\nObjective: {objective}\nConstraints: {constraints}",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 6. wealth_institutional_power_loop
    # Power, capture, institutional failure, Beautiful Mouse, collapse
    # signature. Diagnostic, not accusatory. Roles, not people.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_institutional_power_loop",
        description=(
            "Institutional power, capture, Beautiful Mouse, and "
            "collapse-signature intelligence loop."
        ),
        tags={"wealth", "power", "capture", "collapse", "institution"},
        meta={"version": "2026.07.10"},
    )
    def wealth_institutional_power_loop(
        institution: str,
        text_or_event: str,
        concern: str = "",
        historical_priors: str = "",
    ) -> list[Message]:
        """
        Force roles-not-people framing. Beautiful Mouse before collapse.

        Args:
            institution: Name of the institution
            text_or_event: The text/event to analyze
            concern: The specific concern
            historical_priors: Known historical patterns for comparison
        """
        body = (
            "# WEALTH Institutional Power Loop\n\n"
            "## Institution\n"
            f"{institution}\n\n"
            "## Text or event\n"
            f"{text_or_event}\n\n"
            "## Concern\n"
            f"{concern}\n\n"
            "## Historical priors\n"
            f"{historical_priors}\n\n"
            "## Required sequence\n\n"
            "1. **FRAME** — this is diagnostic, not accusatory. "
            "Do not name individuals as causes. Use roles, incentives, "
            "structures, and governance geometry.\n\n"
            "2. **POWER AUDIT** — run or recommend:\n"
            "   - `wealth_power_audit`\n"
            "   - `wealth_capture_scan`\n\n"
            "3. **BEAUTIFUL MOUSE FIRST** — if the question is early "
            "institutional decay: use `wealth_beautiful_mouse_scan` before "
            "collapse scanner.\n\n"
            "4. **COLLAPSE SIGNATURE** — if the question is late-stage "
            "failure pattern: use `wealth_collapse_signature_scan`.\n\n"
            "5. **CONTRADICTION** — ask:\n"
            "   - what evidence suggests health?\n"
            "   - what evidence suggests decay?\n"
            "   - what would falsify the concern?\n"
            "   - what is merely rhetoric?\n\n"
            "6. **BOUNDARY** — HIGH/CRITICAL institutional claim requires: "
            "`wealth_judge_handoff(mode='prepare')`.\n\n"
            "7. **OUTPUT** — return:\n"
            "   - diagnostic level: ABSENT / EMERGING / ACTIVE / DOMINANT\n"
            "   - evidence for\n"
            "   - evidence against\n"
            "   - missing tests\n"
            "   - dignity risk\n"
            "   - next safe action\n\n"
            "## Forbidden\n"
            "Do not declare collapse as fact from narrative alone.\n"
            "Do not attack named people.\n"
            "Do not convert pattern match into verdict.\n"
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://institution/power",
                f"Institution: {institution}\nConcern: {concern}\nPriors: {historical_priors}",
            ),
        ]

    # ────────────────────────────────────────────────────────────────────
    # 7. wealth_arifos_handoff_loop
    # Prepare a clean arifOS judge envelope. Never submit without explicit
    # authority. Never write to VAULT999 from this prompt.
    # ────────────────────────────────────────────────────────────────────
    @mcp.prompt(
        name="wealth_arifos_handoff_loop",
        description=(
            "Prepare a clean arifOS judge handoff envelope for irreversible, "
            "high-risk, or governance-sensitive WEALTH outputs."
        ),
        tags={"wealth", "arifos", "handoff", "governance"},
        meta={"version": "2026.07.10"},
    )
    def wealth_arifos_handoff_loop(
        source_tool: str,
        result_summary: str,
        intent: str,
        blast_radius: str = "MEDIUM",
        reversibility: str = "PARTIAL",
        domain: str = "capital",
    ) -> list[Message]:
        """
        Build a clean judge envelope. Default mode is prepare; submit only
        with explicit authority.

        Args:
            source_tool: The WEALTH tool that produced the result
            result_summary: Summary of the WEALTH computation result
            intent: The capital decision being proposed
            blast_radius: LOW / MEDIUM / HIGH / CRITICAL
            reversibility: FULL / PARTIAL / NONE
            domain: capital / risk / power / wisdom / collapse / meta
        """
        body = (
            "# WEALTH → arifOS Handoff Loop\n\n"
            "## Source tool\n"
            f"{source_tool}\n\n"
            "## Result summary\n"
            f"{result_summary}\n\n"
            "## Intent\n"
            f"{intent}\n\n"
            "## Blast radius\n"
            f"{blast_radius}\n\n"
            "## Reversibility\n"
            f"{reversibility}\n\n"
            "## Domain\n"
            f"{domain}\n\n"
            "## Required sequence\n\n"
            "1. **PREPARE ONLY** — default mode is `prepare`. Do not submit "
            "unless explicit authority exists.\n\n"
            "2. **ENVELOPE CHECK** — build:\n"
            "   - tool_name\n"
            "   - result\n"
            "   - intent\n"
            "   - capability\n"
            "   - blast_radius\n"
            "   - reversibility_level\n"
            "   - epistemic_state\n"
            "   - domain\n"
            "   - evidence\n\n"
            "3. **AUTHORITY CHECK**:\n"
            "   - if irreversible: requires 888_HOLD.\n"
            "   - if blast_radius is HIGH or CRITICAL: requires arifOS judge.\n"
            "   - if actor is not verified: observe-only or advisory-only.\n\n"
            "4. **CALL** — use:\n"
            "   `wealth_judge_handoff(mode='prepare')`\n\n"
            "5. **OUTPUT** — return:\n"
            "   - readiness\n"
            "   - missing fields\n"
            "   - constitutional risk\n"
            "   - next safe action\n"
            "   - whether submit is forbidden\n\n"
            "## Forbidden\n"
            "Do not call `mode='submit'` unless explicitly authorized.\n"
            "Do not claim arifOS verdict before arifOS responds.\n"
            "Do not write to VAULT999 from this prompt.\n"
        )
        return [
            _msg_text(body),
            _msg_resource(
                "wealth://handoff/envelope",
                f"Source: {source_tool}\nIntent: {intent}\nBlast: {blast_radius}\nReversibility: {reversibility}\nDomain: {domain}",
                "application/json",
            ),
        ]


def _extract_dimension(wisdom_result: dict, dimension: str) -> str | None:
    """Extract a single dimension score from wisdom result."""
    for dim in wisdom_result.get("dimensions", []):
        if dim.get("dimension") == dimension:
            score = dim.get("score", 0.5)
            if score > 0.7:
                return "positive"
            elif score < 0.3:
                return "negative"
            else:
                return "neutral"
    return None
