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
import sys

# Ensure parent directory is in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastmcp import FastMCP

# MCP primitive imports — resource embedding for prompts (Binding #23-26, 2026-07-10)
from mcp.types import EmbeddedResource, TextResourceContents
from fastmcp.prompts.base import Message
from pydantic import AnyUrl

# Import contracts
from wealth_contracts.envelope import wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality, ClaimState

# Import core engines
from wealth_core.wisdom import compute_wisdom
from wealth_core.power import audit_power
from wealth_core.epistemic import audit_epistemic
from wealth_core.capital import (
    compute_conservation,
    compute_flow,
    compute_runway,
    npv,
    irr,
)
from wealth_core.risk import (
    compute_emv,
    monte_carlo_simulation,
    compute_evoi,
    detect_false_confluence,
    compute_asymmetry,
    fiscal_breakeven_oil_price,
)
from wealth_core.collapse_signature.scanner import compute_collapse_risk
from wealth_core.collapse_signature.beautiful_mouse import compute_beautiful_mouse_score
from wealth_core.counterfactual import run_counterfactual
from wealth_core.institutional import (
    compute_stress_index,
    compute_cascade,
    compute_governance_capacity,
    compute_exploitation,
)
from wealth_arifos_bridge.judge_handoff import (
    prepare_judge_handoff,
    submit_to_arif_judge,
)

# ── Canonical tool surface (7 tools, mode-dispatched) ──────────────────
from wealth_mcp.tools.canonical import register_canonical_tools


# WEALTH capital compute — OBSERVE by default.
# ZEN 2026-07-11 FNF-0: NEVER import arifosmcp into this organ (coupling leak).
# Session truth is kernel's job via HTTP bridge only, not Python package import.
_UNBOUND_SESSION_TOKENS = {None, "", "_default", "null", "None", "anonymous"}
_OBSERVE_SURFACE = frozenset(
    {
        "capital_primitive",
        "capital_health",
        "capital_diagnose",
        "capital_wisdom",
        "capital_market",
        "capital_ledger",
        "capital_registry",
    }
)


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
                    "clientInfo": {"name": "wealth-session-bridge", "version": "2026.07.11"},
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
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
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
    - Unbound/_default + capital_* → OBSERVE_UNBOUND
    - Real session_id → HTTP bridge only
    - Non-capital without session → SESSION_REQUIRED
    """
    unbound = session_id in _UNBOUND_SESSION_TOKENS

    if unbound:
        if tool_name in _OBSERVE_SURFACE or (
            isinstance(tool_name, str) and tool_name.startswith("capital_")
        ):
            return {
                "ok": True,
                "code": "OBSERVE_UNBOUND",
                "reason": (
                    "L11 AUTH: unbound OBSERVE for capital surface — "
                    "no arifosmcp import; kernel not required for pure compute"
                ),
                "actor_id": actor_id or "wealth-mcp",
                "session_id": session_id,
                "tool_name": tool_name,
                "actor_verified": False,
            }
        return {
            "ok": False,
            "code": "SESSION_REQUIRED",
            "reason": "L11 AUTH: session_id missing",
            "actor_id": actor_id,
            "session_id": session_id,
            "tool_name": tool_name,
        }

    bridge = _validate_session_via_http_bridge(str(session_id), actor_id)
    bridge["tool_name"] = tool_name
    return bridge


def create_mcp_server() -> FastMCP:
    """Create and configure the WEALTH MCP server."""

    mcp = FastMCP(
        "WEALTH Federated Domain",
        version="2026.06.15",
        # MCP logging: SEP-2577 deprecated — maintenance only; default min warning.
        client_log_level="warning",
        instructions=(
            "WEALTH — Capital Intelligence for arifOS federation. "
            "Computes capital, risk, wisdom, and power metrics. "
            "Does NOT authorize execution. WEALTH computes. arifOS judges. Arif decides."
        ),
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

        _RECEIPT_PATH = "/root/VAULT999/wealth/receipts.jsonl"
        _SCHEMA_VERSION = "2026.06.27"

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
            actor_id: str = None,
            session_id: str = None,
            evidence_quality: str = None,
            missing_preload: list = None,
        ):
            """Emit a receipt for every consequential tool call.

            Best-effort. Never fails the tool call.
            Schema: wealth://replay/receipt-schema
            """
            try:
                if actor_id is None:
                    actor_id = "wealth-mcp"
                if evidence_quality is None:
                    evidence_quality = (
                        "SEALED"
                        if tool_name == "wealth_vault_write" and status == "PASS"
                        else "OBSERVED"
                        if status == "PASS"
                        else "MISSING"
                    )
                receipt = {
                    "receipt_id": str(_uuid.uuid4()),
                    "timestamp_utc": _now_iso(),
                    "actor_id": actor_id,
                    "tool_name": tool_name,
                    "arguments": {
                        k: v
                        for k, v in (arguments or {}).items()
                        if k not in ("actor_signature", "nonce", "_meta")
                    },
                    "epistemic_state": "DERIVED",
                    "evidence_quality": evidence_quality,
                    "domain": _infer_domain(tool_name),
                    "session_id": session_id,
                    "governance_status": verdict or status,
                    "transport": "mcp_call_tool",
                    "schema_version": _SCHEMA_VERSION,
                }
                if missing_preload:
                    receipt["non_compliant_preload"] = missing_preload
                os.makedirs(os.path.dirname(_RECEIPT_PATH), exist_ok=True)
                with open(_RECEIPT_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(receipt) + "\n")
            except Exception as e:
                print(f"[RECEIPT] emit failed for {tool_name}: {e}")

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
            """Append envelope as a second TextContent block.

            The original content[0] is preserved unchanged so any
            outputSchema validation still passes. Envelope metadata
            is appended as content[1] for downstream parsing.
            """
            try:
                envelope_payload = {
                    "envelope": {
                        "receipt_id": receipt_id,
                        "schema_version": _SCHEMA_VERSION,
                        "epistemic_state": _domain_default_epistemic(
                            _infer_domain(tool_name)
                        ),
                        "freshness_utc": _now_iso(),
                        "actor_id": actor_id,
                        "session_id": session_id,
                        "governance_status": verdict or "PASS",
                        "transport": "mcp_call_tool",
                        "domain": _infer_domain(tool_name),
                        "tool_name": tool_name,
                    }
                }
                envelope_text = json.dumps(envelope_payload, indent=2)
                envelope_content = TextContent(
                    type="text",
                    text=f"\n\n--- wealth://envelope ---\n{envelope_text}",
                    annotations={"audience": ["assistant"], "priority": 0.9},
                )
                new_content = list(result.content) + [envelope_content]
                return ToolResult(content=new_content, is_error=result.is_error)
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
            actor_id = kwargs.get("actor_id") or meta.get("actor_id") or "wealth-mcp"
            session_id = (
                kwargs.get("session_id") or meta.get("session_id") or "_default"
            )

            # ── P0-4: Session validation (was defined but never called) ──
            binding = _validate_direct_session_binding(name, actor_id, session_id)
            if not binding.get("ok"):
                return ToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "tool": name,
                                    "error_code": binding.get(
                                        "code", "SESSION_REQUIRED"
                                    ),
                                    "reason": binding.get("reason", "L11 AUTH failed"),
                                    "actor_id": binding.get("actor_id"),
                                    "session_id": binding.get("session_id"),
                                }
                            ),
                        )
                    ],
                    is_error=True,
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
                _emit_receipt(
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
                return ToolResult(
                    content=[TextContent(type="text", text=error_text)],
                    is_error=True,
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
            except Exception as e:
                # Discovery 3: Structured error envelope on failure
                from wealth_mcp.federation_safety import classify_error

                err_env = classify_error(e, source_tool=name, source_organ="wealth")
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
                return ToolResult(
                    content=[
                        TextContent(type="text", text=json.dumps(err_env, default=str))
                    ],
                    is_error=True,
                )
            _emit_receipt(
                name,
                arguments,
                status="PASS",
                verdict=verdict or "PASS",
                actor_id=actor_id,
                session_id=session_id,
            )
            return result

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
                public_names = {
                    "wealth_wisdom_evaluate",
                    "wealth_power_audit",
                    "wealth_capture_scan",
                    "wealth_compute_npv",
                    "wealth_compute_irr",
                    "wealth_compute_emv",
                    "wealth_compute_evoi",
                    "wealth_conservation_check",
                    "wealth_flow_check",
                    "wealth_runway_check",
                    "wealth_monte_carlo_simulate",
                    "wealth_confluence_check",
                    "wealth_asymmetry_check",
                    "wealth_stock_analysis",
                    "wealth_personal_finance",
                    "wealth_market_data",
                    "wealth_omni_wisdom",
                    "wealth_agent_path",
                    "wealth_vault_write",
                    "wealth_vault_query",
                    "wealth_boundary_governance",
                    "wealth_survival_engine",
                    "wealth_registry_status",
                    "wealth_collapse_signature_scan",
                    "wealth_beautiful_mouse_scan",
                    "wealth_judge_handoff",
                    "wealth_fiscal_breakeven",
                    # ── ZEN aliases (FORGE 2026-06-30) ─────────────────────
                    "wealth_system_registry_status",
                    "wealth_emv_compute",
                    "wealth_monte_carlo",
                    "wealth_evoi_compute",
                    "wealth_reason_agent",
                    # ── APEX optimizers (FORGE 2026-07-06) ──────────────
                    "wealth_markowitz_frontier",
                    "wealth_kelly_sizing",
                    "wealth_robust_portfolio",
                    "wealth_chance_constrained",
                    "wealth_two_stage_recourse",
                    # ── Auction + coalition tools (FORGE 2026-07-07) ────
                    "wealth_bid_surface",
                    "wealth_optimize_mwc",
                    # ── Institutional stress detection (FORGE 2026-07-08) ─
                    "wealth_institutional_stress_index",
                    "wealth_cascade_model",
                    "wealth_governance_capacity",
                    "wealth_external_exploitation_detect",
                    # ── Canonical 7-mode surface (FORGE 2026-07-07) ────────
                    "capital_primitive",
                    "capital_health",
                    "capital_diagnose",
                    "capital_wisdom",
                    "capital_market",
                    "capital_ledger",
                    "capital_registry",
                }
                filtered = [
                    t for t in result if getattr(t, "name", None) in public_names
                ]
                return filtered

        mcp.add_middleware(WealthSurfaceFilterMiddleware())

    except Exception as e:
        print(f"[GOVERNANCE] WEALTH federated governance wrapper failed to load: {e}")

    # ── Register tools ────────────────────────────────────────────────────
    # DEREGISTERED 2026-07-10: Legacy surface disabled (43 tools → 7 canonical).
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
    # _register_institutional_tools(
    #     mcp
    # )  # Institutional stress detection (forged 2026-07-08)
    _register_resources(mcp)
    _register_prompts(mcp)

    # ── Register canonical tools (7-mode surface, 2026-07-07) ──────────
    register_canonical_tools(mcp)

    return mcp


def _register_wisdom_tools(mcp: FastMCP) -> None:
    """Register Wisdom Economics tools."""

    @mcp.tool(
        name="wealth_wisdom_evaluate",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "Φ Faithfulness",
        },
    )
    async def wealth_wisdom_evaluate(
        proposal: str,
        capital_type: str = "financial",
        context: dict | None = None,
    ) -> dict:
        """
        Evaluate a capital allocation proposal across 6 wisdom dimensions.
        Returns dignity impact, sovereignty effect, resilience score,
        inequality effect, ecological cost, and optionality preservation.

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_wisdom(proposal, capital_type, context)
        return wrap_result(
            tool_name="wealth_wisdom_evaluate",
            domain="wisdom",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=["proposal_text_analysis"],
            dignity_impact=_extract_dimension(result, "dignity"),
            sovereignty_effect=_extract_dimension(result, "sovereignty"),
        )


def _register_power_tools(mcp: FastMCP) -> None:
    """Register Power Intelligence tools."""

    @mcp.tool(name="wealth_power_audit")
    async def wealth_power_audit(
        scenario: str,
        actors: list[str] | None = None,
        context: dict | None = None,
        # SOCIAL-SYMBOLIC INVARIANT: legitimacy_score
        legitimacy_score: dict | None = None,
    ) -> dict:
        """
        Audit the power dynamics of a capital scenario.
        Returns incentive map, capture risk, rent extraction score,
        opacity level, coercion signals, and rule asymmetry.

        Catches AI advice that sounds balanced but hides weak evidence
        or dangerous allocation geometry.

        SOCIAL-SYMBOLIC INVARIANT (legitimacy_score):
          Optional dict with keys: public_trust (0-1), procedural_fairness (0-1),
          outcome_fairness (0-1), historical_decisions (list).
          When provided, adds institutional legitimacy tracking.
        """
        result = audit_power(scenario, actors, context)
        # SOCIAL-SYMBOLIC INVARIANT: compute legitimacy
        if legitimacy_score:
            public_trust = max(0.0, min(1.0, legitimacy_score.get("public_trust", 0.5)))
            proc_fairness = max(
                0.0, min(1.0, legitimacy_score.get("procedural_fairness", 0.5))
            )
            outcome_fairness = max(
                0.0, min(1.0, legitimacy_score.get("outcome_fairness", 0.5))
            )
            legitimacy = (
                (public_trust * 0.4) + (proc_fairness * 0.3) + (outcome_fairness * 0.3)
            )
            legitimacy_trend = "stable"
            if legitimacy > 0.7:
                legitimacy_trend = "rising"
            elif legitimacy < 0.3:
                legitimacy_trend = "declining"
            result["legitimacy"] = {
                "score": round(legitimacy, 4),
                "trend": legitimacy_trend,
                "components": {
                    "public_trust": round(public_trust, 4),
                    "procedural_fairness": round(proc_fairness, 4),
                    "outcome_fairness": round(outcome_fairness, 4),
                },
                "risk_factors": (["LOW_PUBLIC_TRUST"] if public_trust < 0.3 else [])
                + (["LOW_PROCEDURAL_FAIRNESS"] if proc_fairness < 0.3 else [])
                + (["LOW_OUTCOME_FAIRNESS"] if outcome_fairness < 0.3 else []),
                "note": "SOCIAL-SYMBOLIC INVARIANT: institutional legitimacy tracking",
            }
        return wrap_result(
            tool_name="wealth_power_audit",
            domain="power",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=["scenario_text_analysis"],
            capture_risk_level=result.get("overall_capture_risk"),
        )

    @mcp.tool(name="wealth_capture_scan")
    async def wealth_capture_scan(
        advice_text: str,
        source_model: str = "",
    ) -> dict:
        """
        Scan AI-generated financial advice for capture signals.
        Detects: hidden incentives, omitted downsides, false precision,
        time-pressure language, authority claims without evidence.
        """
        result = audit_power(advice_text, [source_model, "user"], {})
        return wrap_result(
            tool_name="wealth_capture_scan",
            domain="power",
            result={
                "capture_risk": result.get("overall_capture_risk"),
                "dimensions": result.get("dimensions", []),
                "source_model": source_model,
            },
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,
            source_attribution=[f"model:{source_model}" if source_model else "unknown"],
            capture_risk_level=result.get("overall_capture_risk"),
        )


def _register_epistemic_tools(mcp: FastMCP) -> None:
    """Register Epistemic Intelligence tools."""

    @mcp.tool(name="wealth_epistemic_audit")
    async def wealth_epistemic_audit(
        scenario: str,
        actors: list[str] | None = None,
        context: dict | None = None,
    ) -> dict:
        """
        Audit epistemic bias in institutional decision-making.

        Detects 7 dimensions of epistemic failure:
        - Model Ownership: Who proposed it defends it (identity risk)
        - Signal Demotion: Evidence seen but ranked secondary
        - Analog Anchoring: Success template overrides evidence
        - Pipeline Inertia: Approval system makes pivot hard
        - Governance Constraint: Challenge without breaking system
        - Contradiction Density: Wells disagreeing with models
        - Zweig Alignment: Incentive-truth mapping (3 rules)

        People do not defend what is true.
        People defend what their incentives make survivable.

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = audit_epistemic(scenario, actors, context)
        return wrap_result(
            tool_name="wealth_epistemic_audit",
            domain="epistemic",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["epistemic_engine_v1", "peka_case_study"],
        )


def _register_capital_tools(mcp: FastMCP) -> None:
    """Register capital domain tools."""

    @mcp.tool(name="wealth_compute_npv")
    async def wealth_compute_npv(
        cash_flows: list[float],
        discount_rate: float,
    ) -> dict:
        """Compute Net Present Value of a series of cash flows."""
        result = npv(cash_flows, discount_rate)
        return wrap_result(
            tool_name="wealth_compute_npv",
            domain="capital",
            result={
                "npv": result,
                "cash_flows": cash_flows,
                "discount_rate": discount_rate,
            },
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.STRONG,
            source_attribution=["user_provided_inputs"],
        )

    @mcp.tool(name="wealth_compute_irr")
    async def wealth_compute_irr(
        cash_flows: list[float],
        initial_investment: float | None = None,
    ) -> dict:
        """Compute Internal Rate of Return.

        Standard: pass all cash flows including initial investment in
        cash_flows (cash_flows[0] at t=0, typically negative).

        Backward-compatible: if initial_investment is provided (non-zero,
        non-None), it is prepended as a negative t=0 flow.
        """
        # Backward-compatible: if initial_investment provided separately,
        # prepend it as the t=0 flow with correct (negative) sign convention.
        if initial_investment is not None and initial_investment != 0:
            flows = [-abs(initial_investment)] + list(cash_flows)
        else:
            flows = list(cash_flows)

        # Validate: need at least 2 cash flows
        if len(flows) < 2:
            return wrap_result(
                tool_name="wealth_compute_irr",
                domain="capital",
                result={
                    "irr": None,
                    "cash_flows": cash_flows,
                    "initial_investment": initial_investment,
                    "warning": "Need at least two cash flows with a sign change to compute IRR",
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=["user_provided_inputs"],
            )

        result = irr(flows)
        return wrap_result(
            tool_name="wealth_compute_irr",
            domain="capital",
            result={
                "irr": result,
                "cash_flows": cash_flows,
                "initial_investment": initial_investment,
            },
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.STRONG,
            source_attribution=["user_provided_inputs"],
        )

    @mcp.tool(name="wealth_conservation_check")
    async def wealth_conservation_check(
        assets: list[dict] | None = None,
        liabilities: list[dict] | None = None,
    ) -> dict:
        """Compute capital conservation: net worth, asset/liability totals."""
        result = compute_conservation(assets, liabilities)
        return wrap_result(
            tool_name="wealth_conservation_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_portfolio"],
        )

    @mcp.tool(name="wealth_flow_check")
    async def wealth_flow_check(
        income: list[dict] | None = None,
        expenses: list[dict] | None = None,
    ) -> dict:
        """Compute cash flow: net, income, expenses, monthly burn."""
        result = compute_flow(income, expenses)
        return wrap_result(
            tool_name="wealth_flow_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_cashflow"],
        )

    @mcp.tool(name="wealth_runway_check")
    async def wealth_runway_check(
        liquid_assets: float,
        monthly_burn: float,
        conservative_factor: float = 0.8,
    ) -> dict:
        """Compute financial runway in months."""
        result = compute_runway(liquid_assets, monthly_burn, conservative_factor)
        return wrap_result(
            tool_name="wealth_runway_check",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_assets"],
        )


def _register_risk_tools(mcp: FastMCP) -> None:
    """Register risk domain tools."""

    # ── Canonical: wealth_compute_emv ────────────────────────────────────
    @mcp.tool(name="wealth_compute_emv")
    async def wealth_compute_emv(
        outcomes: list[float],
        probabilities: list[float],
    ) -> dict:
        """Compute Expected Monetary Value with variance and std dev."""
        result = compute_emv(outcomes, probabilities)
        return wrap_result(
            tool_name="wealth_compute_emv",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["user_provided_scenarios"],
        )

    # ── FORGE 2026-06-30: promoted from hidden function to @mcp.tool (ZEN alias). ──
    # ZEN Strike 2: agent-visible alias for migration compat.
    @mcp.tool(name="wealth_emv_compute")
    async def wealth_emv_compute(
        outcomes: list[float],
        probabilities: list[float],
    ) -> dict:
        """[LEGACY ALIAS] Compute Expected Monetary Value. Use wealth_compute_emv."""
        return await wealth_compute_emv(outcomes, probabilities)

    # ── Canonical: wealth_monte_carlo_simulate ──────────────────────────────
    @mcp.tool(name="wealth_monte_carlo_simulate")
    async def wealth_monte_carlo_simulate(
        initial_value: float,
        growth_rate: float,
        volatility: float,
        periods: int = 10,
        simulations: int = 1000,
        seed: int | None = None,
        # SOCIAL-SYMBOLIC INVARIANT (Phase 3, FORGE 000Ω 2026-06-27)
        population_mode: bool = False,
        population_size: int = 1000,
        adoption_rate: float = 0.05,
        resistance_factor: float = 0.3,
        network_effect: float = 0.1,
    ) -> dict:
        """Run Monte Carlo simulation for value projection.

        SOCIAL-SYMBOLIC extension (population_mode):
          When True, models collective behavior dynamics — S-curve adoption,
          tipping points, network effects, institutional resistance. Returns
          population_dynamics alongside financial projections.
        """
        # When population_mode=True, delegate to legacy monolith for S-curve
        if population_mode:
            try:
                from internal.monolith import monte_carlo_forecast as _mc_impl

                # Map federated signature → legacy signature
                # Legacy expects initial_commitment, mean_cash_flows, volatilities
                mean_cash_flows = [
                    initial_value * (1 + growth_rate) ** t for t in range(periods)
                ]
                vols = [initial_value * volatility] * periods
                legacy_result = _mc_impl(
                    initial_commitment=initial_value,
                    mean_cash_flows=mean_cash_flows,
                    volatilities=vols,
                    discount_rate=0.1,
                    simulations=simulations,
                    distribution="lognormal",
                    population_mode=True,
                    population_size=population_size,
                    adoption_rate=adoption_rate,
                    resistance_factor=resistance_factor,
                    network_effect=network_effect,
                )
                return wrap_result(
                    tool_name="wealth_monte_carlo_simulate",
                    domain="risk",
                    result=legacy_result,
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=[
                        "monte_carlo_simulation",
                        "population_dynamics",
                    ],
                )
            except Exception as e:
                return wrap_result(
                    tool_name="wealth_monte_carlo_simulate",
                    domain="risk",
                    result={"error": str(e), "population_mode": True},
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[f"Population mode error: {e}"],
                )
        result = monte_carlo_simulation(
            initial_value, growth_rate, volatility, periods, simulations, seed
        )
        return wrap_result(
            tool_name="wealth_monte_carlo_simulate",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["monte_carlo_simulation"],
        )

    # ── FORGE 2026-06-30: promoted from hidden function to @mcp.tool (ZEN alias). ──
    # ZEN Strike 2: agent-visible alias for migration compat.
    @mcp.tool(name="wealth_monte_carlo")
    async def wealth_monte_carlo(
        initial_value: float,
        growth_rate: float,
        volatility: float,
        periods: int = 10,
        simulations: int = 1000,
        seed: int | None = None,
    ) -> dict:
        """[LEGACY ALIAS] Use wealth_monte_carlo_simulate."""
        return await wealth_monte_carlo_simulate(
            initial_value, growth_rate, volatility, periods, simulations, seed
        )

    # ── Canonical: wealth_compute_evoi ────────────────────────────────────
    @mcp.tool(name="wealth_compute_evoi")
    async def wealth_compute_evoi(
        prior_pos: float,
        posterior_pos: float,
        well_cost_musd: float,
        p50_value_musd: float,
        discount_rate: float = 0.1,
        robust: bool = False,
    ) -> dict:
        """Compute Expected Value of Information (EVOI).
        When robust=True: max-min over uncertainty set, returns worst-case EVOI + CVaR."""
        result = compute_evoi(
            prior_pos, posterior_pos, well_cost_musd, p50_value_musd, discount_rate
        )
        # ── APEX Pillar IV: Robust EVOI ──────────────────────────────────
        if robust:
            import numpy as _np

            n_samples = 20
            prior_lo, prior_hi = (
                max(0.01, prior_pos - 0.10),
                min(0.99, prior_pos + 0.10),
            )
            post_lo, post_hi = (
                max(0.01, posterior_pos - 0.15),
                min(0.99, posterior_pos + 0.15),
            )
            evoi_samples = []
            for p in _np.linspace(prior_lo, prior_hi, n_samples):
                for q in _np.linspace(post_lo, post_hi, n_samples):
                    if q > p:
                        try:
                            r = compute_evoi(
                                float(p),
                                float(q),
                                well_cost_musd,
                                p50_value_musd,
                                discount_rate,
                            )
                            evoi_samples.append(r.get("evoi_musd", 0.0))
                        except Exception:
                            continue
            if evoi_samples:
                expected_evoi = float(_np.mean(evoi_samples))
                worst_case = float(_np.min(evoi_samples))
                cvar5 = float(_np.percentile(evoi_samples, 5))
                result["robust_analysis"] = {
                    "expected_evoi_musd": round(expected_evoi, 4),
                    "worst_case_evoi_musd": round(worst_case, 4),
                    "cvar_5pct_musd": round(cvar5, 4),
                    "robust_regret_musd": round(max(0, expected_evoi - worst_case), 4),
                    "method": "APEX_ROBUST_MAX_MIN",
                }
                result["robust_verdict"] = (
                    "ROBUST_SEAL"
                    if worst_case > 0
                    else ("ROBUST_SABAR" if expected_evoi > 0 else "ROBUST_VOID")
                )
        # ── End APEX robust ───────────────────────────────────────────────
        return wrap_result(
            tool_name="wealth_compute_evoi",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["evoi_calculation"],
        )

    # ── FORGE 2026-06-30: promoted from hidden function to @mcp.tool (ZEN alias). ──
    # ZEN Strike 2: agent-visible alias for migration compat.
    @mcp.tool(name="wealth_evoi_compute")
    async def wealth_evoi_compute(
        prior_pos: float,
        posterior_pos: float,
        well_cost_musd: float,
        p50_value_musd: float,
        discount_rate: float = 0.1,
    ) -> dict:
        """[LEGACY ALIAS] Compute EVOI. Use wealth_compute_evoi."""
        return await wealth_compute_evoi(
            prior_pos, posterior_pos, well_cost_musd, p50_value_musd, discount_rate
        )

    @mcp.tool(name="wealth_confluence_check")
    async def wealth_confluence_check(
        indicators: list[dict],
    ) -> dict:
        """Detect false confluence — indicators measuring the same signal."""
        result = detect_false_confluence(indicators)
        return wrap_result(
            tool_name="wealth_confluence_check",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["indicator_analysis"],
        )

    @mcp.tool(name="wealth_asymmetry_check")
    async def wealth_asymmetry_check(
        upside_scenarios: list[float],
        downside_scenarios: list[float],
    ) -> dict:
        """Compute risk asymmetry — is the distribution skewed?"""
        result = compute_asymmetry(upside_scenarios, downside_scenarios)
        return wrap_result(
            tool_name="wealth_asymmetry_check",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["scenario_analysis"],
        )

    # ── HARDENING 2026-06-25: fiscal breakeven — highest-signal gap ──────
    @mcp.tool(name="wealth_fiscal_breakeven")
    async def wealth_fiscal_breakeven(
        total_government_expenditure: float,
        non_oil_revenue: float,
        petronas_dividend_base_rm: float,
        oil_price_assumption_usd: float,
        petronas_production_boe_per_day: float = 350_000,
        royalty_tax_effective_rate: float = 0.30,
        target_fiscal_deficit_pct: float = 0.035,
        gdp_nominal_rm_billion: float = 390.0,
    ) -> dict:
        """
        Compute oil price at which Malaysia's fiscal path becomes unsustainable.

        Returns breakeven price, fiscal pressure classification (UNSUSTAINABLE/AT_RISK/MANAGEABLE),
        and sensitivity analysis. Answers what Monte Carlo cannot: a single threshold.

        Budget 2026 calibration: total revenue RM343.1B, operating exp RM302B,
        petroleum revenue RM43B (dividend RM20B + tax RM23B), target deficit 3.5% GDP.
        """
        result = fiscal_breakeven_oil_price(
            total_government_expenditure=total_government_expenditure,
            non_oil_revenue=non_oil_revenue,
            petronas_dividend_base_rm=petronas_dividend_base_rm,
            oil_price_assumption_usd=oil_price_assumption_usd,
            petronas_production_boe_per_day=petronas_production_boe_per_day,
            royalty_tax_effective_rate=royalty_tax_effective_rate,
            target_fiscal_deficit_pct=target_fiscal_deficit_pct,
            gdp_nominal_rm_billion=gdp_nominal_rm_billion,
        )
        return wrap_result(
            tool_name="wealth_fiscal_breakeven",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.CLAIM,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["malaysia_budget_2026", "petronas_annual_report"],
        )


def _register_legacy_surface_tools(mcp: FastMCP) -> None:
    """Register tools that delegate to monolith's existing implementations.
    These are the 5 missing public tools that need the monolith's complex engines."""

    @mcp.tool(name="wealth_stock_analysis")
    async def wealth_stock_analysis(
        mode: str = "verify_math",
        ticker: str = "",
        entry_price: float = 0,
        exit_price: float | None = None,
        current_price: float | None = None,
        position_size: int = 0,
        status: str = "unrealized",
        direction: str = "long",
        factors: dict | None = None,
        # Kelly criterion params
        account_balance: float = 0,
        win_rate: float = 0,
        avg_win: float = 0,
        avg_loss: float = 0,
        kelly_fraction: float = 0.5,
    ) -> dict:
        """D4 Stock Analysis — 17-mode capital-risk governance.
        mode='nash_multi_factor' uses Nash product (APEX Pillar IV).
        mode='kelly' uses Kelly criterion for optimal position sizing."""
        try:
            from internal.monolith import wealth_stock_analysis as _stock_impl

            return await _stock_impl(
                mode=mode,
                ticker=ticker,
                entry_price=entry_price,
                exit_price=exit_price,
                current_price=current_price,
                position_size=position_size,
                status=status,
                direction=direction,
                factors=factors,
                account_balance=account_balance,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                kelly_fraction=kelly_fraction,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_stock_analysis",
                domain="stock",
                result={"error": str(e), "mode": mode, "ticker": ticker},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Stock engine error: {e}"],
            )

    @mcp.tool(name="wealth_personal_finance")
    async def wealth_personal_finance(
        mode: str = "summary",
        owner: str = "arif",
        amount: float = 0,
        category: str = "expense",
        description: str = "",
        txn_date: str | None = None,
    ) -> dict:
        """D1 Personal Finance — cashflow, runway, net worth, EPF, zakat.
        Delegates to internal/personal_finance.py engines."""
        try:
            from internal.monolith import wealth_personal_finance as _pf_impl

            return await _pf_impl(
                mode=mode,
                owner=owner,
                amount=amount,
                category=category,
                description=description,
                txn_date=txn_date,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_personal_finance",
                domain="personal",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Personal finance engine error: {e}"],
            )

    @mcp.tool(name="wealth_market_data")
    async def wealth_market_data(
        mode: str = "fx",
        base: str = "USD",
        targets: str = "MYR,SGD,GBP",
        commodity: str = "brent_crude",
        indicator: str = "usd_myr",
        country: str = "MYS",
    ) -> dict:
        """D3 Market Data — FX rates, commodities, macro indicators.
        Delegates to internal/market_data.py engines."""
        try:
            from internal.monolith import wealth_market_data as _md_impl

            return _md_impl(
                mode=mode,
                base=base,
                targets=targets,
                commodity=commodity,
                indicator=indicator,
                country=country,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_market_data",
                domain="macro",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Market data engine error: {e}"],
            )

    @mcp.tool(name="wealth_omni_wisdom")
    async def wealth_omni_wisdom(
        mode: str = "synthesize",
        decision_context: dict | None = None,
        deal_params: dict | None = None,
        path_params: dict | None = None,
        # SOCIAL-SYMBOLIC INVARIANT (Phase 3, FORGE 000Ω 2026-06-27)
        institutional_trust: dict | None = None,
        memory_query: str | None = None,
    ) -> dict:
        """Unified capital intelligence — synthesis + deal + hysteresis.
        Modes:
          - synthesize: monolith synthesis (default)
          - deal / deal_frame: monolith deal framing
          - hysteresis / path_params: hysteresis-aware path analysis
          - counterfactual: structured counterfactual across 13 primitives
                            (LOCAL, forged 2026-06-24)

        SOCIAL-SYMBOLIC extension (Phase 3):
          - institutional_trust: {track_record, transparency, accountability,
            legitimacy_source} — 7th wisdom dimension, blocks SEAL if DISTRUST
        """
        # Local counterfactual mode — bridges MOF watch + V3 scenarios
        if mode == "counterfactual":
            try:
                base_context = decision_context or {}
                deltas = (deal_params or {}).get("deltas", [])
                cf_mode = (path_params or {}).get("cf_mode", "grid")
                top_k = int((path_params or {}).get("top_k", 5))
                result = run_counterfactual(
                    base_context=base_context,
                    deltas=deltas,
                    mode=cf_mode,
                    top_k=top_k,
                )
                return wrap_result(
                    tool_name="wealth_omni_wisdom",
                    domain="synthesis",
                    result=result,
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=[
                        "counterfactual_engine",
                        "wealth_thermodynamics_v1",
                    ],
                )
            except Exception as e:
                return wrap_result(
                    tool_name="wealth_omni_wisdom",
                    domain="synthesis",
                    result={"error": str(e), "mode": mode},
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[f"Counterfactual engine error: {e}"],
                )
        # P1 FIX (2026-06-28): Public schema advertised 'deal_frame' and 'path_params';
        # monolith accepts 'deal' and 'hysteresis'. Alias them for compatibility.
        mode_aliases = {"deal_frame": "deal", "path_params": "hysteresis"}
        if mode in mode_aliases:
            mode = mode_aliases[mode]

        # P1 FIX (2026-06-28): Empty decision_context makes synthesizer emit
        # conversion_integrity=ERROR. Provide a transparent default description.
        if not decision_context:
            decision_context = {"description": "(no decision context provided)"}
        elif not decision_context.get("description"):
            decision_context["description"] = decision_context.get(
                "question", "(no decision context provided)"
            )

        # Other modes delegate to monolith
        # P0 FIX (2026-06-28): institutional_trust is a Phase 3 extension that
        # monolith.wealth_omni_wisdom does not yet accept. Instead of crashing
        # with "unexpected keyword argument", inject it into decision_context
        # so sub-engines can use it if present, without breaking the call.
        if institutional_trust is not None:
            _ctx = dict(decision_context or {})
            _ctx["_institutional_trust"] = institutional_trust
            decision_context = _ctx
        try:
            from internal.monolith import wealth_omni_wisdom as _omni_impl

            return await _omni_impl(
                mode=mode,
                decision_context=decision_context,
                deal_params=deal_params,
                path_params=path_params,
                memory_query=memory_query,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_omni_wisdom",
                domain="synthesis",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Omni wisdom engine error: {e}"],
            )

    @mcp.tool(name="wealth_agent_path")
    async def wealth_agent_path(
        task_description: str = "",
        scale_mode: str = "agentic",
        context: dict | None = None,
    ) -> dict:
        """Sovereign Intent Router — classifies tasks into L1/L2 paths.
        Delegates to monolith's agent_path implementation."""
        try:
            from internal.monolith import wealth_agent_path as _ap_impl

            return _ap_impl(
                task_description=task_description,
                scale_mode=scale_mode,
                context=context,
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_agent_path",
                domain="meta",
                result={"error": str(e), "task_description": task_description},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Agent path engine error: {e}"],
            )

    # ── FORGE 2026-06-30: ZEN alias — routes to wealth_agent_path ──────────
    @mcp.tool(name="wealth_reason_agent")
    async def wealth_reason_agent(
        task_description: str = "",
        scale_mode: str = "agentic",
        context: dict | None = None,
    ) -> dict:
        """[LEGACY ALIAS] Sovereign Intent Router. Use wealth_agent_path."""
        return await wealth_agent_path(
            task_description=task_description,
            scale_mode=scale_mode,
            context=context,
        )


def _register_meta_tools(mcp: FastMCP) -> None:
    """Register meta/diagnostic tools."""

    @mcp.tool(name="wealth_vault_write")
    async def wealth_vault_write(
        tx_type: str,
        amount: float,
        currency: str = "MYR",
        description: str = "",
        quantity: float | None = None,
        price: float | None = None,
        fees: float = 0,
        broker: str = "",
        asset_id: str = "",
        category: str = "",
        notes: str = "",
    ) -> dict:
        """Write a transaction to the VAULT999 ledger.

        Authority: draft_receipt only unless arifOS judge approval.
        Irreversible — requires human confirmation for SEAL.
        WEALTH does NOT self-seal capital truth.

        capital_primitive: conservation
        """
        # P1 FIX (2026-06-28): Vault write is advisory receipt only.
        # arifOS must approve before SEAL. WEALTH never self-seals.
        _vault_auth = {
            "authority": "draft_receipt_only",
            "arifos_approval_required": True,
            "human_confirmation_required": True,
            "seal_authority": "arifOS_888_JUDGE",
            "capital_primitive": "conservation",
            "rule": "WEALTH computes. arifOS judges. Arif decides.",
        }
        try:
            from host.governance.vault_supabase import record_transaction

            result = record_transaction(
                tx_type=tx_type,
                amount=amount,
                currency=currency,
                description=description,
                quantity=quantity,
                price=price,
                fees=fees,
                broker=broker,
                asset_id=asset_id,
                category=category,
                notes=notes,
            )
            return wrap_result(
                tool_name="wealth_vault_write",
                domain="governance",
                result={"vault_authority": _vault_auth, **result},
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.MODERATE,  # P1: was STRONG, downgraded
                source_attribution=["vault999_supabase"],
                claim_state=ClaimState.DRAFT,  # P1: was SEALED — WEALTH cannot self-seal
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_vault_write",
                domain="governance",
                result={"error": str(e)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Vault write error: {e}"],
            )

    @mcp.tool(name="wealth_vault_query")
    async def wealth_vault_query(
        query: str = "",
        limit: int = 10,
        asset_id: str = "",
    ) -> dict:
        """Query the VAULT999 ledger for portfolio memory and transactions.

        Authority: read_only observe. WEALTH never mutates vault via query.
        capital_primitive: conservation
        """
        try:
            from host.governance.vault_supabase import (
                query_portfolio_snapshots_async,
                query_vault999_async,
            )

            _query_auth = {
                "authority": "read_only",
                "capital_primitive": "conservation",
                "rule": "WEALTH observes vault. arifOS judges. Arif decides.",
            }
            if asset_id:
                snapshots = await query_portfolio_snapshots_async(
                    asset_id=asset_id, limit=limit
                )
                return wrap_result(
                    tool_name="wealth_vault_query",
                    domain="governance",
                    result={
                        "vault_authority": _query_auth,
                        "snapshots": snapshots,
                        "count": len(snapshots),
                    },
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=["vault999_supabase"],
                )
            else:
                records = await query_vault999_async(query=query, limit=limit)
                return wrap_result(
                    tool_name="wealth_vault_query",
                    domain="governance",
                    result=records,
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.MODERATE,
                    source_attribution=["vault999_supabase"],
                )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_vault_query",
                domain="governance",
                result={"error": str(e)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Vault query error: {e}"],
            )

    @mcp.tool(name="wealth_registry_status")
    async def wealth_registry_status(mode: str = "registry") -> dict:
        """Registry truth diagnostic — intended vs registered vs callable."""
        if mode == "health":
            return {
                "status": "ALIVE",
                "version": "2026.06.15",
                "domain": "WEALTH Federated Domain",
                "transport": "streamable-http",
            }
        return {
            "status": "ALIVE",
            "version": "2026.06.15",
            "domain": "WEALTH Federated Domain",
            "public_tools": [
                # Wisdom & Power
                "wealth_wisdom_evaluate",
                "wealth_power_audit",
                "wealth_capture_scan",
                # Capital
                "wealth_compute_npv",
                "wealth_compute_irr",
                "wealth_conservation_check",
                "wealth_flow_check",
                "wealth_runway_check",
                # Risk (canonical names)
                "wealth_compute_emv",
                "wealth_compute_evoi",
                "wealth_monte_carlo_simulate",
                "wealth_confluence_check",
                "wealth_asymmetry_check",
                "wealth_fiscal_breakeven",
                # APEX Optimization (forged 2026-07-06)
                "wealth_markowitz_frontier",
                "wealth_kelly_sizing",
                "wealth_robust_portfolio",
                "wealth_chance_constrained",
                "wealth_two_stage_recourse",
                # Domain engines
                "wealth_stock_analysis",
                "wealth_personal_finance",
                "wealth_market_data",
                "wealth_omni_wisdom",
                "wealth_agent_path",
                # Governance
                "wealth_vault_write",
                "wealth_vault_query",
                # Boundary & Survival (P0 FIX 2026-06-28)
                "wealth_boundary_governance",
                "wealth_survival_engine",
                # Meta
                "wealth_registry_status",
                # Collapse signature — EXTRACTIVE-ONLY LEGACY (demoted 2026-07-08)
                # PETRONAS case proved calibration gap 0.05→0.76 vs institutional tools
                "wealth_collapse_signature_scan",
                "wealth_beautiful_mouse_scan",
                # Federation bridge (forged 2026-06-24)
                "wealth_judge_handoff",
                # Auction + coalition (forged 2026-07-07)
                "wealth_bid_surface",
                "wealth_optimize_mwc",
                # ── DIAGNOSE cluster: Institutional stress detection (PRIMARY, forged 2026-07-08) ──
                # Canonical institutional health surface. Replaces collapse_signature_scan
                # for simulative exploitation, constitutional ambiguity, and sovereignty erosion patterns.
                # VAULT999 SEAL: PETRONAS pattern machine-discriminates two collapse regimes.
                "wealth_institutional_stress_index",
                "wealth_cascade_model",
                "wealth_governance_capacity",
                "wealth_external_exploitation_detect",
            ],
        }

    @mcp.tool(name="wealth_system_registry_status")
    async def wealth_system_registry_status(mode: str = "registry") -> dict:
        """[LEGACY ALIAS] Registry truth diagnostic. Use wealth_registry_status."""
        return await wealth_registry_status(mode)

    # ── Ω-WEALTH-11: Boundary Governance (P0 FIX 2026-06-28) ─────────────────
    # Restored from monolith.py. WEALTH without boundary governance is clever
    # capitalism, not wisdom. This tool checks reversibility, blast_radius,
    # maruah, legitimacy, capture, and stewardship risk.
    # Authority: WEALTH computes. arifOS judges. Arif decides.
    @mcp.tool(name="wealth_boundary_governance")
    async def wealth_boundary_governance(
        mode: str = "floors",
        reversible: bool = True,
        human_confirmed: bool = False,
        epistemic: str = "ESTIMATE",
        proposal: dict | None = None,
        constraints: dict | None = None,
        scale_mode: str = "enterprise",
        population: float = 0,
        energy_budget_twh: float = 0,
        carbon_budget_gt: float = 0,
        tech_readiness: float = 0.5,
        alternatives: list[dict] | None = None,
        values: dict | None = None,
        maruah_score: float | None = None,
        context: dict | None = None,
        mode_params: dict | None = None,
    ) -> dict:
        """Ω-WEALTH-11: Boundary — constitutional floors, maruah, stewardship, constraint.

        Checks F1-F13 compliance, reversibility, blast_radius, legitimacy risk,
        capture risk, and stewardship risk for a capital proposal.

        Modes:
          floors             — F1-F13 floor compliance check
          federation_readiness — organ federation health probe
          legitimacy_audit    — institutional legitimacy scoring

        Pass context={'foreign_entity': True, 'opaque_valuation': True, ...}
        for smart maruah scoring.
        Pass scale_mode='sovereign' for Malaysian national resource context.

        Authority: WEALTH computes. arifOS judges. Arif decides.
        WEALTH does NOT self-seal. WEALTH does NOT emit final constitutional approval.
        """
        try:
            from internal.monolith import wealth_boundary_governance as _impl

            result = _impl(
                mode=mode,
                reversible=reversible,
                human_confirmed=human_confirmed,
                epistemic=epistemic,
                proposal=proposal,
                constraints=constraints,
                scale_mode=scale_mode,
                population=population,
                energy_budget_twh=energy_budget_twh,
                carbon_budget_gt=carbon_budget_gt,
                tech_readiness=tech_readiness,
                alternatives=alternatives,
                values=values,
                maruah_score=maruah_score,
                context=context,
                mode_params=mode_params,
            )
            return wrap_result(
                tool_name="wealth_boundary_governance",
                domain="governance",
                result=result,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "WEALTH:internal/monolith",
                    "WEALTH:tool/wealth_boundary_governance",
                ],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_boundary_governance",
                domain="governance",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Boundary governance error: {e}"],
            )

    # ── Ω-SURVIVAL-ENGINE: Survival Intelligence (P0 FIX 2026-06-28) ────────
    # Restored from monolith.py. Civilization dies first through liquidity,
    # energy, legitimacy, or trust starvation. This engine answers:
    # How long can the organism survive? Where is burn rate leaking?
    # Authority: WEALTH computes. arifOS judges. Arif decides.
    @mcp.tool(name="wealth_survival_engine")
    async def wealth_survival_engine(
        mode: str = "personal_finance",
        monthly_income: float | None = None,
        monthly_expenses: float | None = None,
        liquid_assets: float | None = None,
        cashflows: list[dict] | None = None,
        horizon_months: int = 12,
        conservative_factor: float = 0.8,
        legacy_compat: bool = False,
        scar_history: list[dict] | None = None,
    ) -> dict:
        """Ω-SURVIVAL-ENGINE: Unified survival intelligence — cashflow, runway, burn, liquidity.

        Physics analogy: metabolic engine — how the capital organism
        maintains survival under cash flow stress.

        Modes:
          cashflow         — net monthly position from income/expenses
          runway          — months of survival from liquid assets / burn rate
          burn            — monthly burn rate (expenses - income)
          liquidity       — liquidity health including cashflow + assets
          personal_finance — comprehensive survival dashboard

        scar_history: APEX Pillar IV — constraint accumulation from past loss events.
        Each entry: {"period": int, "loss_pct": float, "weights": list, "asset_class": str}

        Authority: WEALTH computes. arifOS judges. Arif decides.
        WEALTH does NOT move capital. WEALTH does NOT self-seal.
        """
        try:
            from internal.monolith import wealth_survival_engine as _impl

            result = await _impl(
                mode=mode,
                monthly_income=monthly_income,
                monthly_expenses=monthly_expenses,
                liquid_assets=liquid_assets,
                cashflows=cashflows,
                horizon_months=horizon_months,
                conservative_factor=conservative_factor,
                legacy_compat=legacy_compat,
                scar_history=scar_history,
            )
            return wrap_result(
                tool_name="wealth_survival_engine",
                domain="survival",
                result=result,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "WEALTH:internal/monolith",
                    "WEALTH:tool/wealth_survival_engine",
                ],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_survival_engine",
                domain="survival",
                result={"error": str(e), "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Survival engine error: {e}"],
            )

    # ── Collapse Signature [LEGACY — EXTRACTIVE-ONLY] (forged 2026-06-24, demoted 2026-07-08) ──
    # ⚠ DEPRECATED for simulative exploitation patterns.
    # Calibrated exclusively on extraction-fraud corpus (Enron, PDVSA, Pemex, 1MDB, WorldCom).
    # The PETRONAS 2018-2026 case study proves this tool is ONTOLOGICALLY BLIND to:
    #   - Simulative exploitation via constitutional ambiguity
    #   - Interpleader as third-party extraction
    #   - Confidentiality clauses as opacity weapons
    #   - Managed sovereignty erosion across 2-3 year escalation cadences
    # For institutional collapse detection covering these patterns, use the
    # DIAGNOSE cluster: wealth_institutional_stress_index + wealth_cascade_model
    # + wealth_governance_capacity + wealth_external_exploitation_detect.
    # VAULT999 SEAL: PETRONAS pattern proves extraction-calibrated frameworks are incomplete.
    # Hard rule: diagnostic, not adversarial. Always pair with DIAGNOSE cluster.
    # Hard rule: HIGH/CRITICAL → 888_HOLD.
    @mcp.tool(
        name="wealth_collapse_signature_scan",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "Φ Faithfulness [LEGACY]",
            "deprecated": True,
            "replacedBy": "wealth_institutional_stress_index",
            "deprecation_reason": "Extraction-calibrated corpus (Enron/PDVSA/1MDB) blind to simulative exploitation patterns",
            "effective_date": "2026-07-08",
        },
    )
    async def wealth_collapse_signature_scan(
        scenario: str,
        capital_type: str = "financial",
        historical_priors: list[str] | None = None,
    ) -> dict:
        """
        [LEGACY — EXTRACTIVE-ONLY] Scan for extraction-based collapse.

        ⚠ DEPRECATED: Calibrated exclusively on extraction-fraud corpus
        (Enron, PDVSA, Pemex, 1MDB, WorldCom). DOES NOT detect simulative
        exploitation via constitutional ambiguity, interpleader, or managed
        sovereignty erosion.

        For institutional collapse detection, use the DIAGNOSE cluster:
          - wealth_institutional_stress_index
          - wealth_cascade_model
          - wealth_governance_capacity
          - wealth_external_exploitation_detect

        Returns:
        - profile: full signature profile (7 collapse signatures — extraction only)
        - risk: collapse risk score (extractive patterns only)
        - two_d_risk_map: Acemoglu × Calhoun quadrant
        - tripwires: 5-tripwire detection
        - dimensional_densities: per-axis density
        - priors_used: which corpus anchors were compared
        - _warning: "This tool is calibrated on extraction fraud. It will miss simulative exploitation patterns."

        DITEMPA BUKAN DIBERI. WEALTH computes, arifOS judges, Arif decides.
        """
        try:
            result = compute_collapse_risk(
                scenario=scenario,
                capital_type=capital_type,
                historical_priors=historical_priors or [],
            )
            # Cap confidence at 0.90 per F7 HUMILITY
            risk_score = result.get("risk", {}).get("score", 0.5)
            if isinstance(risk_score, (int, float)) and risk_score > 0.90:
                result["risk"]["score"] = 0.90
                result["risk"]["_humbled"] = True

            return wrap_result(
                tool_name="wealth_collapse_signature_scan",
                domain="collapse",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "collapse_corpus:enron,pdvsa,pemex,1mdb,worldcom",
                    f"priors_used:{','.join(historical_priors or ['none'])}",
                ],
                dignity_impact=result.get("profile", {})
                .get("wisdom_axis", {})
                .get("dignity", {})
                .get("label"),
                capture_risk_level=result.get("profile", {})
                .get("acemoglu_axis", {})
                .get("label"),
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_collapse_signature_scan",
                domain="collapse",
                result={"error": str(e), "scenario_length": len(scenario)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Collapse scanner error: {e}"],
            )


def _register_advanced_tools(mcp: FastMCP) -> None:
    """Register advanced forensic + federation-bridge tools (forged 2026-06-24).
    These close three eurekas: counterfactual mode (in omni_wisdom),
    beautiful mouse detector (Phase C early warning), and the
    arifOS judge handoff (federation loop closure).
    """

    # ── Beautiful Mouse Detector (Phase C early warning) ─────────────────
    # Detects Calhoun behavioural-death Phase C ENTRY. Lower threshold
    # than collapse scanner; fires earlier. Use BEFORE any institutional
    # health claim. Pairs with collapse_signature_scan.
    @mcp.tool(name="wealth_beautiful_mouse_scan")
    async def wealth_beautiful_mouse_scan(
        text: str,
        historical_priors: list[str] | None = None,
    ) -> dict:
        """
        Scan a narrative for Calhoun Phase C (Beautiful Mouse) signatures.

        Detects 6 indicators:
        1. PERFECT_PERFORMANCE  — no friction narrative
        2. ZERO_FAILURE        — absence of failure treated as virtue
        3. NARRATIVE_CENTRALISATION — one story dominates
        4. TALENT_DRAIN        — no one inside fights, Ψ sidelined
        5. MONITOR_CULTURE     — metrics over conflict
        6. EXTERNAL_BLAME      — delays and failures blamed outward

        Verdicts: ABSENT | EMERGING | ACTIVE | DOMINANT.
        Confidence hard-capped at 0.85 (lower than collapse scanner
        because Phase C is inherently ambiguous).

        Use cases:
        - Audit CEO speeches / annual reports for Phase C entry
        - Pre-flight check before any institutional health claim
        - Cross-check with collapse_signature_scan (Phase D imminent)

        F6 MARUAH: never names individuals. Reference roles, not people.
        F13 SOVEREIGN: diagnostic only, never declares collapse.

        DITEMPA BUKAN DIBERI. WEALTH computes, arifOS judges, Arif decides.
        """
        try:
            result = compute_beautiful_mouse_score(
                text=text,
                historical_priors=historical_priors or [],
            )
            if "error" in result:
                return wrap_result(
                    tool_name="wealth_beautiful_mouse_scan",
                    domain="collapse",
                    result=result,
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=[result["error"]],
                )
            return wrap_result(
                tool_name="wealth_beautiful_mouse_scan",
                domain="collapse",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "calhoun_phase_c_indicators",
                    f"priors:{','.join(historical_priors or ['none'])}",
                ],
                capture_risk_level=result.get("phase_c_verdict"),
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_beautiful_mouse_scan",
                domain="collapse",
                result={"error": str(e), "text_length": len(text)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Beautiful mouse scan error: {e}"],
            )

    # ── arifOS Judge Handoff (federation loop closure) ───────────────────
    # Prepares a WEALTH verdict for arifOS 888_JUDGE. Two modes:
    # - prepare: build the envelope, return it. Agent or A-FORGE submits.
    # - submit:  actually call arif_judge via MCP, return the verdict.
    #
    # This is the architectural property that makes F13 SOVEREIGN a
    # substrate guarantee, not an agent discipline. WEALTH cannot make
    # constitutional decisions; the bridge is the only path that does.
    @mcp.tool(name="wealth_judge_handoff")
    async def wealth_judge_handoff(
        tool_name: str,
        result: str,
        intent: str,
        capability: str,
        blast_radius: str = "MEDIUM",
        reversibility_level: str = "PARTIAL",
        epistemic_state: str = "DERIVED",
        domain: str = "capital",
        mode: str = "prepare",
        session_id: str = "",
        actor_id: str = "WEALTH",
        evidence: str = "[]",
    ) -> dict:
        """
        Prepare (or submit) a WEALTH verdict for arifOS 888_JUDGE.

        Args:
            tool_name: the WEALTH tool that produced the verdict
            result: JSON string of the WEALTH result to be judged
            intent: the capital decision being proposed
            capability: the specific capability requested
                        (e.g., "register_collapse_signature_claim",
                         "execute_stock_trade", "issue_capital_recommendation")
            blast_radius: LOW | MEDIUM | HIGH | CRITICAL
            reversibility_level: FULL | PARTIAL | NONE
            epistemic_state: OBSERVED | DERIVED | INTERPRETED | SPECULATED
            domain: capital | risk | power | wisdom | collapse | meta
            mode: prepare (default) | submit
            session_id: optional arifOS session
            actor_id: calling actor (default: "WEALTH")
            evidence: JSON string of evidence list

        Modes:
        - prepare: builds the arif_judge envelope + constitutional pre-check.
                   Returns the envelope. Non-mutating. F1 AMANAH compliant.
        - submit:  actually calls arif_judge via MCP. Returns the verdict
                   or an error if arifOS is unreachable. F1: envelope
                   preserved on failure for retry.

        The handoff is an architectural property, not an agent discipline.
        WEALTH prepares. arifOS judges. The sovereign decides.

        DITEMPA BUKAN DIBEI. Forged, not given.
        """
        try:
            # Parse the JSON-encoded inputs
            try:
                result_dict = json.loads(result) if isinstance(result, str) else result
            except json.JSONDecodeError:
                return wrap_result(
                    tool_name="wealth_judge_handoff",
                    domain="governance",
                    result={
                        "error": "result_must_be_valid_json",
                        "received_type": type(result).__name__,
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    errors=["result parameter is not valid JSON"],
                )
            try:
                evidence_list = (
                    json.loads(evidence)
                    if isinstance(evidence, str)
                    else (evidence or [])
                )
            except json.JSONDecodeError:
                evidence_list = []

            handoff = prepare_judge_handoff(
                tool_name=tool_name,
                result=result_dict,
                intent=intent,
                capability=capability,
                blast_radius=blast_radius,
                reversibility_level=reversibility_level,
                epistemic_state=epistemic_state,
                domain=domain,
                session_id=session_id or None,
                actor_id=actor_id or None,
                evidence=evidence_list,
            )

            if mode == "submit" and handoff["readiness"] == "READY":
                submission = await submit_to_arif_judge(handoff["handoff_envelope"])
                return wrap_result(
                    tool_name="wealth_judge_handoff",
                    domain="governance",
                    result={
                        "handoff": handoff,
                        "submission": submission,
                    },
                    epistemic_tag=EpistemicTag.OBSERVED,
                    evidence_quality=EvidenceQuality.STRONG,
                    source_attribution=["wealth_arifos_bridge", "arifos_mcp"],
                    claim_state=ClaimState.SEALED,
                )

            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="governance",
                result=handoff,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=["wealth_arifos_bridge"],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="governance",
                result={"error": str(e), "tool_name": tool_name, "mode": mode},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Judge handoff error: {e}"],
            )

    # ── Backward-compat alias: wealth_arifos_judge_handoff → wealth_judge_handoff ──
    @mcp.tool(name="wealth_arifos_judge_handoff")
    async def wealth_arifos_judge_handoff_alias(
        tool_name: str,
        result: str,
        intent: str,
        capability: str,
        blast_radius: str = "MEDIUM",
        reversibility_level: str = "PARTIAL",
        epistemic_state: str = "DERIVED",
        domain: str = "capital",
        mode: str = "prepare",
        session_id: str = "",
        actor_id: str = "WEALTH",
        evidence: str = "[]",
    ) -> dict:
        """[DEPRECATED] Use wealth_judge_handoff instead."""
        return await wealth_judge_handoff(
            tool_name=tool_name,
            result=result,
            intent=intent,
            capability=capability,
            blast_radius=blast_radius,
            reversibility_level=reversibility_level,
            epistemic_state=epistemic_state,
            domain=domain,
            mode=mode,
            session_id=session_id,
            actor_id=actor_id,
            evidence=evidence,
        )


def _register_optimizer_tools(mcp: FastMCP) -> None:
    """Register APEX optimization engines (forged 2026-07-06).

    Mathematical optimization engines bridging MO-book patterns to APEX governance:
    - markowitz_frontier: Mean-variance portfolio (Reality organ)
    - kelly_sizing: Kelly criterion bet sizing (Execution organ)
    - robust_portfolio: Robust optimization under uncertainty (Governance organ)
    - chance_constrained: VaR/CVaR optimization (Witness organ)
    - two_stage_recourse: Two-stage stochastic program (Memory organ)
    """
    from wealth_core.optimizers import (
        markowitz_frontier as _markowitz_frontier,
        markowitz_frontier_sweep as _markowitz_frontier_sweep,
        kelly_sizing as _kelly_sizing,
        robust_portfolio as _robust_portfolio,
        chance_constrained as _chance_constrained,
        cvar_portfolio as _cvar_portfolio,
        two_stage_recourse as _two_stage_recourse,
    )

    @mcp.tool(name="wealth_markowitz_frontier")
    async def wealth_markowitz_frontier(
        returns: list[float],
        covariances: list[list[float]],
        risk_aversion: float = 1.0,
        risk_free_rate: float = 0.0,
    ) -> dict:
        """
        Compute Markowitz mean-variance optimal portfolio.

        Solves: max μᵀx - (γ/2)·xᵀΣx  s.t. Σxᵢ=1, x≥0
        APEX Organ: Reality (ΔR) — Energy conservation.

        Returns optimal weights, expected return, variance, Sharpe ratio,
        APEX verdict, and uncertainty bands.

        F2 TRUTH: Returns are DER (derived from historical data).
        F7 HUMILITY: Confidence cap 0.90.
        """
        return _markowitz_frontier(
            expected_returns=returns,
            covariances=covariances,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
        )

    @mcp.tool(name="wealth_kelly_sizing")
    async def wealth_kelly_sizing(
        win_prob: float,
        odds: float,
        risk_constraint: float | None = None,
    ) -> dict:
        """
        Compute Kelly criterion optimal bet fraction.

        Maximizes expected log-growth: E[log(1 + f·R)]
        APEX Organ: Execution (W) — Work conservation law.

        Returns optimal fraction, expected log-growth, Monte Carlo simulation,
        and APEX verdict.

        F2 TRUTH: Win probability is INTERPRETED, not OBS.
        F9 ANTI-HANTU: Monte Carlo simulation provides uncertainty bands.
        """
        return _kelly_sizing(
            win_prob=win_prob,
            odds=odds,
            risk_constraint=risk_constraint,
        )

    @mcp.tool(name="wealth_robust_portfolio")
    async def wealth_robust_portfolio(
        returns: list[float],
        uncertainty_radius: float = 0.1,
        robust_type: str = "budget",
        covariances: list[list[float]] | None = None,
    ) -> dict:
        """
        Compute robust optimal portfolio under uncertainty.

        Solves: max min_{z∈Z} (μ+z)ᵀx  s.t. Σxᵢ=1, x≥0
        APEX Organ: Governance (ΔG) — Entropy reduction.

        Supports box, budget (Bertsimas-Sim), and ellipsoidal uncertainty sets.
        Returns worst-case optimal allocation and APEX verdict.

        F2 TRUTH: Uncertainty set is SPEC (modeled, not observed).
        """
        return _robust_portfolio(
            returns=returns,
            uncertainty_radius=uncertainty_radius,
            robust_type=robust_type,
            covariances=covariances,
        )

    @mcp.tool(name="wealth_chance_constrained")
    async def wealth_chance_constrained(
        returns: list[float],
        covariances: list[list[float]],
        confidence: float = 0.95,
        threshold: float = 0.0,
    ) -> dict:
        """
        Compute chance-constrained optimal portfolio (VaR/CVaR).

        Solves: max μᵀx  s.t. P(rᵀx ≤ threshold) ≤ (1-confidence)
        APEX Organ: Witness (Ω) — Gödel incompleteness.

        Returns optimal weights, VaR, CVaR, and APEX verdict.

        F2 TRUTH: Returns distribution is DER (derived from historical data).
        F9 ANTI-HANTU: VaR/CVaR are risk measures, not guarantees.
        """
        return _chance_constrained(
            returns=returns,
            covariances=covariances,
            confidence=confidence,
            threshold=threshold,
        )

    @mcp.tool(name="wealth_two_stage_recourse")
    async def wealth_two_stage_recourse(
        first_stage_costs: dict,
        scenario_data: list[dict],
        first_stage_constraints: list[dict] | None = None,
    ) -> dict:
        """
        Two-stage stochastic optimization with recourse.

        First stage: decide x (here-and-now decisions)
        Second stage: after scenario revealed, choose recourse action y
        APEX Organ: Memory (∂M/∂t) — Landauer cost.

        Returns first-stage decisions, here-and-now value, wait-and-see value,
        expected total value, and APEX verdict.

        F2 TRUTH: Scenarios are SPEC (sampled from distribution).
        """
        return _two_stage_recourse(
            first_stage_costs=first_stage_costs,
            scenario_data=scenario_data,
            first_stage_constraints=first_stage_constraints,
        )


def _register_institutional_tools(mcp: FastMCP) -> None:
    """Register institutional stress detection tools (forged 2026-07-08).

    Four tools detecting the 'institutional collapse spiral' pattern:
    financial stress → rightsizing → governance erosion →
    intelligence compromise → external exploitation → more financial stress.

    - wealth_institutional_stress_index: composite 0-1 stress score
    - wealth_cascade_model: feedback loop detector
    - wealth_governance_capacity: board capacity vs stress
    - wealth_external_exploitation_detect: counterparty behavior patterns
    """
    from wealth_core.institutional import (
        compute_stress_index,
        compute_cascade,
        compute_governance_capacity,
        compute_exploitation,
    )

    @mcp.tool(
        name="wealth_institutional_stress_index",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_institutional_stress_index(
        org_name: str,
        financial_signals: dict,
        governance_signals: dict,
        workforce_signals: dict,
        legal_signals: dict,
        exploitation_signals: dict,
    ) -> dict:
        """
        Composite institutional stress index (0-1).

        Connects financial, governance, workforce, legal, and external
        exploitation signals into a single stress score. Detects feedback
        loops (the 'institutional collapse spiral').

        Inputs:
          - org_name: organization name (e.g., 'PETRONAS')
          - financial_signals: profit_change_pct, revenue_change_pct, cost_cutting_announced
          - governance_signals: board_size, board_resignations_12m, company_secretaries_as_directors, avg_tenure_years
          - workforce_signals: rightsizing_pct, voluntary_exits_pct, key_personnel_departures
          - legal_signals: active_litigation_count, injunction_value_musd, regulatory_uncertainty_score
          - exploitation_signals: counterparty_payment_freeze, interpleader_filed, competing_claims

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_stress_index(
            org_name=org_name,
            financial_signals=financial_signals,
            governance_signals=governance_signals,
            workforce_signals=workforce_signals,
            legal_signals=legal_signals,
            exploitation_signals=exploitation_signals,
        )
        return wrap_result(
            tool_name="wealth_institutional_stress_index",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "financial_signals_OBS",
                "governance_signals_OBS",
                "workforce_signals_OBS",
                "legal_signals_OBS",
                "exploitation_signals_DER",
            ],
        )

    @mcp.tool(
        name="wealth_cascade_model",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_cascade_model(
        timeline: list,
        intervention_scenario: dict | None = None,
    ) -> dict:
        """
        Model feedback loops between institutional stress dimensions.

        Detects spiral vs linear decline vs recovery. Projects trajectory
        and optionally simulates intervention impact.

        Inputs:
          - timeline: list of dicts with {period, financial_stress, governance_capacity,
            workforce_stability, legal_exposure, external_exploitation}
          - intervention_scenario: optional dict (e.g., {'action': 'rightsizing_pause', 'period': 3})

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_cascade(
            timeline=timeline,
            intervention_scenario=intervention_scenario,
        )
        return wrap_result(
            tool_name="wealth_cascade_model",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["temporal_pattern_analysis_INT"],
        )

    @mcp.tool(
        name="wealth_governance_capacity",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_governance_capacity(
        board_members: list,
        committees: list,
        stress_level: float,
    ) -> dict:
        """
        Monitor board governance capacity relative to stress level.

        Analyzes board composition, committee structure, and identifies
        governance gaps that could enable institutional collapse.

        Inputs:
          - board_members: list of {name, role, appointed_date, type}
          - committees: list of {name, members, meets_quarterly}
          - stress_level: float 0-1 (from wealth_institutional_stress_index)

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_governance_capacity(
            board_members=board_members,
            committees=committees,
            stress_level=stress_level,
        )
        return wrap_result(
            tool_name="wealth_governance_capacity",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "board_filings_OBS",
                "committee_structure_OBS",
                "governance_analysis_DER",
            ],
        )

    @mcp.tool(
        name="wealth_external_exploitation_detect",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_external_exploitation_detect(
        counterparty_actions: list,
        institution_state: dict,
    ) -> dict:
        """
        Detect 'simulative neutral' counterparty behavior.

        Identifies rational exploitation of institutional weakness —
        where each action is individually defensible but the aggregate
        pattern reveals systematic extraction.

        Inputs:
          - counterparty_actions: list of {action, date, claimed_rationale, actual_benefit_musd}
          - institution_state: dict with stress_index, governance_capacity

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_exploitation(
            counterparty_actions=counterparty_actions,
            institution_state=institution_state,
        )
        return wrap_result(
            tool_name="wealth_external_exploitation_detect",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "counterparty_actions_OBS",
                "behavioral_pattern_DER",
                "institutional_state_DER",
            ],
        )


def _register_auction_tools(mcp: FastMCP) -> None:
    """Register auction surface and cooperative game theory tools (forged 2026-07-07).

    Two new tools bridging capital allocation to competitive bidding and
    coalition formation:
    - wealth_bid_surface: Score a competitive bid surface for resource allocation.
    - wealth_optimize_mwc: Compute optimal Minimum Winning Coalition.
    """

    @mcp.tool(name="wealth_bid_surface")
    async def wealth_bid_surface(
        bids: list[dict],
        reserve_price: float = 0.0,
        mode: str = "first_price",
        scoring_weights: dict | None = None,
        bidder_caps: dict | None = None,
    ) -> dict:
        """
        Score a competitive bid surface for resource allocation.
        Computes bid ranking, bidder surplus, competitive intensity, and surface topology.
        Scoring Primacy (Eureka 4): EMV without bid scoring surface = answering the wrong question.
        Returns ranked bid list, surplus distribution, and surface metrics.

        Auction modes: first_price | second_price | scoring | all_pay.
        """
        from wealth_mcp.tools.bid_surface import compute_bid_surface

        try:
            result = compute_bid_surface(
                bids=bids,
                reserve_price=reserve_price,
                mode=mode,
                scoring_weights=scoring_weights,
                bidder_caps=bidder_caps,
            )
            return wrap_result(
                tool_name="wealth_bid_surface",
                domain="auction",
                result=result,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.STRONG,
                source_attribution=[
                    "bid_surface_engine",
                    f"auction_mode:{mode}",
                ],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_bid_surface",
                domain="auction",
                result={"error": str(e), "bid_count": len(bids)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Bid surface error: {e}"],
            )

    @mcp.tool(name="wealth_optimize_mwc")
    async def wealth_optimize_mwc(
        players: list[dict],
        majority_threshold: float = 0.5,
        mode: str = "cost_minimizing",
        max_coalition_size: int = 10,
        constraints: dict | None = None,
    ) -> dict:
        """
        Compute optimal Minimum Winning Coalition (MWC) for resource allocation.
        Uses cooperative game theory: finds the smallest coalition that secures
        majority control while minimizing total cost. Based on Shapley value
        and coalition formation theory.
        Returns optimal coalition, total cost, coalition stability, and power distribution.

        Modes: cost_minimizing | stability_maximizing | balanced.
        """
        from wealth_mcp.tools.optimize_mwc import compute_mwc

        try:
            result = compute_mwc(
                players=players,
                majority_threshold=majority_threshold,
                mode=mode,
                max_coalition_size=max_coalition_size,
                constraints=constraints,
            )
            return wrap_result(
                tool_name="wealth_optimize_mwc",
                domain="coalition",
                result=result,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "mwc_optimizer",
                    f"coalition_mode:{mode}",
                ],
            )
        except Exception as e:
            return wrap_result(
                tool_name="wealth_optimize_mwc",
                domain="coalition",
                result={"error": str(e), "player_count": len(players)},
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"MWC optimizer error: {e}"],
            )


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
        meta={"version": "2026.06.27", "authority": "advisory_only"},
    )
    def wealth_schema() -> str:
        """WEALTH canonical tool surface and version info."""
        return json.dumps(
            {
                "organ": "WEALTH",
                "version": "2026.06.27",
                "role": "Capital Intelligence for arifOS federation",
                "authority": "WEALTH computes. arifOS judges. Arif decides.",
                "protocol": "MCP 2025-03-26",
                "protocol_seps": ["SEP-1613", "SEP-2106", "SEP-2549", "SEP-1330"],
                "json_schema_dialect": "https://json-schema.org/draft/2020-12/schema",
                "tool_prefix": "wealth_",
                "resource_scheme": "wealth://",
                "prompt_count": 7,
                "resource_count": 14,
                "naming_convention": "wealth_<verb>_<noun>",
                "canonical_tools": [
                    {
                        "name": "wealth_wisdom_evaluate",
                        "apex": "Φ Faithfulness",
                        "domain": "wisdom",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_power_audit",
                        "apex": "Ω Humility",
                        "domain": "power",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_capture_scan",
                        "apex": "Ω Humility",
                        "domain": "capture",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_compute_npv",
                        "apex": "P Precision",
                        "domain": "capital",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_compute_irr",
                        "apex": "P Precision",
                        "domain": "capital",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_compute_emv",
                        "apex": "E Evidence",
                        "domain": "capital",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_compute_evoi",
                        "apex": "X Execution",
                        "domain": "information",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_monte_carlo_simulate",
                        "apex": "E Evidence",
                        "domain": "simulation",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_conservation_check",
                        "apex": "Φ Faithfulness",
                        "domain": "conservation",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_flow_check",
                        "apex": "A Adaptation",
                        "domain": "flow",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_runway_check",
                        "apex": "A Adaptation",
                        "domain": "survival",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_confluence_check",
                        "apex": "Ω Humility",
                        "domain": "signal",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_asymmetry_check",
                        "apex": "Ω Humility",
                        "domain": "risk",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_stock_analysis",
                        "apex": "P Precision",
                        "domain": "stock",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_personal_finance",
                        "apex": "A Adaptation",
                        "domain": "personal",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_market_data",
                        "apex": "E Evidence",
                        "domain": "market",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_omni_wisdom",
                        "apex": "Φ Faithfulness",
                        "domain": "synthesis",
                        "readOnly": True,
                    },
                    {
                        "name": "wealth_agent_path",
                        "apex": "A Adaptation",
                        "domain": "routing",
                        "readOnly": True,
                    },
                    "wealth_vault_write",
                    "wealth_vault_query",
                    "wealth_registry_status",
                    "wealth_collapse_signature_scan",
                    "wealth_beautiful_mouse_scan",
                    "wealth_judge_handoff",
                    "wealth_fiscal_breakeven",
                    "wealth_bid_surface",
                    "wealth_optimize_mwc",
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
        meta={"version": "2026.06.27", "authority": "advisory_only"},
    )
    def wealth_tools_registry() -> str:
        """Full tool registry with classification."""
        return json.dumps(
            {
                "active": [
                    {
                        "name": "wealth_wisdom_evaluate",
                        "domain": "wisdom",
                        "verb": "evaluate",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_power_audit",
                        "domain": "power",
                        "verb": "audit",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_capture_scan",
                        "domain": "power",
                        "verb": "scan",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_compute_npv",
                        "domain": "capital",
                        "verb": "compute",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_compute_irr",
                        "domain": "capital",
                        "verb": "compute",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_compute_emv",
                        "domain": "risk",
                        "verb": "compute",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_compute_evoi",
                        "domain": "risk",
                        "verb": "compute",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_monte_carlo_simulate",
                        "domain": "risk",
                        "verb": "simulate",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_conservation_check",
                        "domain": "capital",
                        "verb": "check",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_flow_check",
                        "domain": "capital",
                        "verb": "check",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_runway_check",
                        "domain": "capital",
                        "verb": "check",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_confluence_check",
                        "domain": "risk",
                        "verb": "check",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_asymmetry_check",
                        "domain": "risk",
                        "verb": "check",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_stock_analysis",
                        "domain": "stock",
                        "verb": "analysis",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_personal_finance",
                        "domain": "personal",
                        "verb": "finance",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_market_data",
                        "domain": "macro",
                        "verb": "data",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_omni_wisdom",
                        "domain": "synthesis",
                        "verb": "wisdom",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_agent_path",
                        "domain": "meta",
                        "verb": "path",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_vault_write",
                        "domain": "governance",
                        "verb": "write",
                        "mutation": True,
                        "irreversible": True,
                    },
                    {
                        "name": "wealth_vault_query",
                        "domain": "governance",
                        "verb": "query",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_registry_status",
                        "domain": "meta",
                        "verb": "status",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_collapse_signature_scan",
                        "domain": "collapse",
                        "verb": "scan",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_beautiful_mouse_scan",
                        "domain": "collapse",
                        "verb": "scan",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_judge_handoff",
                        "domain": "governance",
                        "verb": "handoff",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_fiscal_breakeven",
                        "domain": "macro",
                        "verb": "compute",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_bid_surface",
                        "domain": "auction",
                        "verb": "analyze",
                        "mutation": False,
                    },
                    {
                        "name": "wealth_optimize_mwc",
                        "domain": "coalition",
                        "verb": "optimize",
                        "mutation": False,
                    },
                ],
                "deprecated": [],
                "aliases": {
                    "wealth_emv_compute": "wealth_compute_emv",
                    "wealth_evoi_compute": "wealth_compute_evoi",
                    "wealth_monte_carlo": "wealth_monte_carlo_simulate",
                    "wealth_system_registry_status": "wealth_registry_status",
                    "wealth_reason_agent": "wealth_agent_path",
                },
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
                        "tools": [
                            "wealth_personal_finance",
                            "wealth_conservation_check",
                            "wealth_flow_check",
                            "wealth_runway_check",
                        ],
                        "prompt": "wealth_capital_diagnosis_loop",
                        "examples": ["cashflow", "runway", "net_worth", "epf", "zakat"],
                    },
                    "capital_valuation": {
                        "tools": [
                            "wealth_compute_npv",
                            "wealth_compute_irr",
                            "wealth_compute_emv",
                            "wealth_compute_evoi",
                            "wealth_fiscal_breakeven",
                        ],
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
                        "tools": ["wealth_market_data", "wealth_fiscal_breakeven"],
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
                            "wealth_stock_analysis",
                            "wealth_compute_emv",
                            "wealth_asymmetry_check",
                            "wealth_confluence_check",
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
                        "tools": [
                            "wealth_asymmetry_check",
                            "wealth_monte_carlo_simulate",
                            "wealth_confluence_check",
                            "wealth_compute_emv",
                            "wealth_compute_evoi",
                        ],
                        "prompt": "wealth_risk_downside_loop",
                        "examples": [
                            "asymmetry",
                            "monte_carlo",
                            "false_confluence",
                            "tail",
                        ],
                    },
                    "institutional_power": {
                        "tools": [
                            "wealth_power_audit",
                            "wealth_capture_scan",
                            "wealth_beautiful_mouse_scan",
                            "wealth_collapse_signature_scan",
                        ],
                        "prompt": "wealth_institutional_power_loop",
                        "examples": [
                            "capture",
                            "power_audit",
                            "beautiful_mouse",
                            "collapse",
                        ],
                    },
                    "governance": {
                        "tools": [
                            "wealth_judge_handoff",
                            "wealth_vault_write",
                            "wealth_vault_query",
                        ],
                        "prompt": "wealth_arifos_handoff_loop",
                        "examples": ["handoff", "vault", "authority", "888_hold"],
                    },
                    "synthesis": {
                        "tools": [
                            "wealth_omni_wisdom",
                            "wealth_wisdom_evaluate",
                            "wealth_agent_path",
                            "wealth_registry_status",
                        ],
                        "prompts": [
                            "wealth_capital_diagnosis_loop",
                            "wealth_allocation_judgment_loop",
                        ],
                        "examples": [
                            "13-primitive synthesis",
                            "6-dim wisdom",
                            "path routing",
                            "registry status",
                        ],
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
                    "wealth_compute_emv": [
                        "wealth://reality/context",
                        "wealth://bid/surface",
                    ],
                    "wealth_bid_surface": ["wealth://reality/context"],
                    "wealth_compute_evoi": [
                        "wealth://reality/context",
                        "wealth://risk/thresholds",
                    ],
                    "wealth_monte_carlo_simulate": ["wealth://reality/context"],
                    "wealth_judge_handoff": [
                        "wealth://handoff/arifos-schema",
                        "wealth://risk/thresholds",
                        "wealth://affordance/contracts",
                    ],
                    "wealth_vault_write": [
                        "wealth://handoff/arifos-schema",
                        "wealth://replay/receipt-schema",
                    ],
                    "wealth_collapse_signature_scan": [
                        "wealth://risk/thresholds",
                        "wealth://federation/contract",
                    ],
                    "wealth_power_audit": ["wealth://federation/contract"],
                    "wealth_stock_analysis": ["wealth://market/sources"],
                    "wealth_market_data": ["wealth://market/sources"],
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
        meta={"version": "2026.06.27"},
    )
    def wealth_health() -> str:
        """WEALTH organ health status (dynamic, timestamped)."""
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        return json.dumps(
            {
                "status": "ALIVE",
                "version": "2026.06.27",
                "domain": "WEALTH Federated Domain",
                "transport": "streamable-http",
                "read_only_resources": True,
                "tools_compute_only": True,
                "prompt_count": 7,
                "resource_count": 14,
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
                "market_data_policy": "current-sensitive claims require wealth_market_data with timestamp",
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
                    "wealth_vault_write",
                    "wealth_judge_handoff",
                ],
                "actor_verification_required_for": [
                    "wealth_vault_write",
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
                        "tool": "wealth_market_data",
                        "mode": "fx",
                        "freshness_required": True,
                        "acceptable_lag_minutes": 15,
                        "common_pairs": ["USD/MYR", "USD/SGD", "GBP/MYR", "EUR/MYR"],
                    },
                    "commodity": {
                        "tool": "wealth_market_data",
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
                        "tool": "wealth_market_data",
                        "mode": "macro",
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
                        "tool": "wealth_stock_analysis",
                        "modes": ["bursa_snapshot", "bursa_evidence"],
                        "freshness_required": True,
                        "execution_grade": False,
                        "note": "Bursa data is informational, not execution-grade",
                    },
                },
                "freshness_law": (
                    "If a claim is current-sensitive, the WEALTH output must cite "
                    "the wealth_market_data call that produced it, with timestamp. "
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
                    "wealth_compute_npv": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_compute_irr": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_compute_emv": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_compute_evoi": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_monte_carlo_simulate": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_conservation_check": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_flow_check": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_runway_check": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_asymmetry_check": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_confluence_check": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_stock_analysis": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                        "execution_grade": False,
                    },
                    "wealth_personal_finance": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_market_data": {
                        "action_class": "OBSERVE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                        "freshness_required": True,
                    },
                    "wealth_fiscal_breakeven": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_power_audit": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_capture_scan": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_collapse_signature_scan": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": True,
                        "side_effects": "HIGH/CRITICAL claim requires handoff",
                    },
                    "wealth_beautiful_mouse_scan": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "diagnostic only, never accusatory",
                    },
                    "wealth_wisdom_evaluate": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_omni_wisdom": {
                        "action_class": "SYNTHESIZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "cold-start returns HOLD/0.5 by design",
                    },
                    "wealth_agent_path": {
                        "action_class": "META",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_registry_status": {
                        "action_class": "META",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_vault_query": {
                        "action_class": "READ",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_vault_write": {
                        "action_class": "WRITE",
                        "mutation": True,
                        "irreversible": True,
                        "requires_888_hold": True,
                        "side_effects": "writes to VAULT999 ledger; cannot be undone",
                        "actor_verification_required": True,
                        "session_id_required": True,
                    },
                    "wealth_judge_handoff": {
                        "action_class": "HANDOFF",
                        "mutation": False,
                        "irreversible": False,
                        "mode_default": "prepare",
                        "submit_requires_authority": True,
                        "side_effects": "prepare builds envelope; submit delegates verdict to arifOS",
                    },
                    "wealth_bid_surface": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
                    },
                    "wealth_optimize_mwc": {
                        "action_class": "ANALYZE",
                        "mutation": False,
                        "irreversible": False,
                        "requires_888_hold": False,
                        "side_effects": "none",
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
