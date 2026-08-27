"""
WEALTH capital_registry — WEALTH meta/introspection — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality
from wealth_mcp import (
    CAPITAL_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
    WEALTH_VERSION,
)



def register_registry(mcp):
    """Register the registry tool on the given FastMCP instance."""
# ═══════════════════════════════════════════════════════════════════
# 7. capital_registry — Meta and introspection
# ═══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="capital_registry",
    output_schema=WEALTH_OUTPUT_SCHEMA,
    description="WEALTH meta/introspection — registry status, tool schema, domain index, health check. Observational only. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
    tags={"domain": "meta", "kind": "observational", "canonical": "v1"},
)
async def capital_registry(
    mode: str = "status",
    tool_name: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    del tool_name  # Reserved for schema lookup compatibility.
    m = mode.lower()
    canonical_tools = list(CAPITAL_TOOL_NAMES)
    public_tools = list(PUBLIC_TOOL_NAMES)
    architecture = f"federated-{len(canonical_tools)}-canonical"

    # Live Probe of all canonical & public tool modules (Fix W6)
    probe_failures = []
    for t_name in public_tools:
        try:
            if t_name == "capital_entropy":
                # Zen Phase 3.2: use the same importlib path as capital_entropy tool,
                # not the broken 'from entropy_integrity.mcp.wealth' import
                import importlib.util as _iu
                from pathlib import Path as _P

                _ent_base = (
                    _P(__file__).resolve().parents[2]
                    / "entropy-integrity"
                    / "mcp"
                    / "wealth"
                )
                _ent_file = _ent_base / "power_consequence_map.py"
                if _ent_file.is_file():
                    _ent_spec = _iu.spec_from_file_location("pcm_probe", _ent_file)
                    if _ent_spec and _ent_spec.loader:
                        _ent_mod = _iu.module_from_spec(_ent_spec)
                        _ent_spec.loader.exec_module(_ent_mod)
                else:
                    raise ImportError(
                        f"entropy-integrity module absent: {_ent_file}"
                    )
            elif t_name == "wealth_judge_handoff":
                from wealth_contracts.envelope import ClaimState
        except Exception as _p_exc:
            probe_failures.append(f"{t_name}: {type(_p_exc).__name__} ({_p_exc})")

    reg_truth = "PASS" if not probe_failures else "DEGRADED"

    if m == "status":
        return wrap_result(
            tool_name="capital_registry",
            domain="meta",
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            result={
                "status": "OK" if not probe_failures else "DEGRADED",
                "organ": "WEALTH",
                "version": WEALTH_VERSION,
                "architecture": architecture,
                "canonical_tools": canonical_tools,
                "canonical_tool_count": len(canonical_tools),
                "public_tools": public_tools,
                "public_tool_count": len(public_tools),
                "registry_truth": reg_truth,
                "probe_failures": probe_failures,
                "legacy_dispatch": "direct_import",
                "final_authority": "ARIF",
                "read_only": True,
            },
        )

    if m == "schema":
        # This mapping is deliberately limited to PUBLIC_TOOL_NAMES.  Legacy
        # engines remain callable through internal dispatch, but they are not
        # public MCP tools and must not appear in the registry schema.
        tool_schemas = {
            "capital_primitive": {
                "modes": [
                    "npv",
                    "irr",
                    "emv",
                    "evoi",
                    "mc",
                    "kelly",
                    "markowitz",
                    "robust",
                    "chance_constrained",
                    "two_stage",
                ],
                "description": "Financial mathematics and decision analysis primitives",
            },
            "capital_health": {
                "modes": [
                    "conservation",
                    "flow",
                    "runway",
                    "survival",
                    "fiscal_breakeven",
                    "confluence",
                    "asymmetry",
                ],
                "survival_submodes": [
                    "personal_finance",
                    "corporate_runway",
                    "sovereign_fiscal",
                ],
                "description": "Financial health, runway, and survival computation",
            },
            "capital_diagnose": {
                "modes": [
                    "stress_index",
                    "governance_capacity",
                    "cascade_model",
                    "exploitation_detect",
                    "collapse_signature",
                    "beautiful_mouse",
                    "capture_scan",
                    "power_audit",
                    "bid_surface",
                    "optimize_mwc",
                    "cadence_monitor",
                    "crisis_reflex",
                ],
                "description": "Abductive institutional diagnosis and governance capacity",
            },
            "capital_market": {
                "modes": [
                    "fx",
                    "commodity",
                    "indicator",
                    "stock",
                    "gold",
                    "oil",
                    "gas",
                ],
                "description": "Live commodity, FX, and country market indicators",
            },
            "capital_ledger": {
                "modes": ["query", "write"],
                "description": "VAULT999 immutable append-only ledger",
            },
            "capital_registry": {
                "modes": ["status", "schema", "domains", "health"],
                "description": "WEALTH organ self-introspection and registry status",
            },
            "capital_entropy": {
                "modes": [
                    "power_consequence_map",
                    "metric_purpose_audit",
                    "responsibility_ledger",
                    "trust_capital_decay",
                    "coercive_order_cost",
                    "entropy_externality",
                ],
                "description": "Thermodynamic power/consequence and metric-purpose drift",
            },
            "wealth_judge_handoff": {
                "modes": ["prepare", "submit"],
                "description": "Sovereign 888_HOLD judge handoff envelope",
            },
        }
        return wrap_result(
            tool_name="capital_registry",
            domain="meta",
            result={
                "version": WEALTH_VERSION,
                "architecture": architecture,
                "tools": tool_schemas,
                "canonical_tool_count": len(canonical_tools),
                "public_tool_count": len(public_tools),
            },
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
        )

    if m == "domains":
        return wrap_result(
            tool_name="capital_registry",
            domain="meta",
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            result={
                "version": WEALTH_VERSION,
                "domains": [
                    {
                        "name": "capital",
                        "kind": "deductive",
                        "tools": ["capital_primitive", "capital_health"],
                    },
                    {
                        "name": "institutional",
                        "kind": "abductive",
                        "tools": ["capital_diagnose", "capital_entropy"],
                    },
                    {
                        "name": "market",
                        "kind": "observational",
                        "tools": ["capital_market"],
                    },
                    {
                        "name": "vault",
                        "kind": "mutating",
                        "tools": ["capital_ledger"],
                    },
                    {
                        "name": "governance",
                        "kind": "advisory",
                        "tools": ["wealth_judge_handoff"],
                    },
                    {
                        "name": "meta",
                        "kind": "observational",
                        "tools": ["capital_registry"],
                    },
                ],
                "canonical_tool_count": len(canonical_tools),
                "public_tool_count": len(public_tools),
                "legacy_dispatch": "direct_import",
            },
        )

    if m == "health":
        return wrap_result(
            tool_name="capital_registry",
            domain="meta",
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            result={
                "status": "ALIVE",
                "version": WEALTH_VERSION,
                "domain": "WEALTH Federated Domain",
                "architecture": architecture,
                "canonical_tools": len(canonical_tools),
                "public_tools": len(public_tools),
            },
        )

    # Zen Phase 2: unknown mode → structured error, never MCP -32602
    return wrap_result(
        tool_name="capital_registry",
        domain="meta",
        result={
            "status": "ERROR",
            "error_code": "UNKNOWN_MODE",
            "message": f"Unknown mode '{mode}'. Valid: status, schema, domains, health",
        },
        epistemic_tag=EpistemicTag.ASSUMED,
        evidence_quality=EvidenceQuality.MISSING,
        claim_state=ClaimState.VOID,
        errors=[f"Unknown mode '{mode}'. Valid: status, schema, domains, health"],
        session_id=session_id,
        actor_id=actor_id,
    )

