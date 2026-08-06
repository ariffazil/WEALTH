"""
W0 — WealthEvidenceMiddleware.
DITEMPA BUKAN DIBERI — Forged 2026-08-06.

Four gates enforced on every tool call:
  1. PRE-CALL: Count material arguments → coverage denominator.
  2. POST-CALL: Stamp coverage = (fields reflected / fields provided).
  3. POST-CALL: Detect verdict conflicts (MISSING/WEAK evidence + affirmative
     verdict → CAUTION).
  4. POST-CALL: Detect empty/zero results with material inputs → flag incomplete.

Fixes the Enron/Holocaust defect: silent input dropping → GREEN.
With W0: zero coverage + affirmative verdict → downgraded to CAUTION + flag.

Pattern: FastMCP Middleware.on_call_tool — runs inside the governance wrapper
before ToolResult wrapping. Receives raw dict from tool functions.
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp.server.middleware import Middleware

from wealth_contracts.epistemic import (
    UNMEASURED,
    MIN_COVERAGE_THRESHOLD,
    coverage_ratio,
    geometric_mean_known,
    is_unmeasured,
)

# Re-export for server.py
__all__ = [
    "WealthEvidenceMiddleware",
    "_estimate_coverage",
    "_material_args",
    "_result_is_empty",
    "_scan_verdict_conflict",
    "MIN_COVERAGE_THRESHOLD",
]

# ── Known non-material (administrative) argument names ───────────────────
_ADMIN_ARGS: frozenset[str] = frozenset(
    {
        "session_id",
        "session_token",
        "sct",
        "trace_id",
        "actor_id",
        "lease_id",
        "_meta",
        "ack_irreversible",
        "mode",
    }
)

# ── Default sentinel values (not material input) ─────────────────────────
_DEFAULT_VALS: tuple = (
    None,
    "",
    0,
    0.0,
    False,
    "USD",
    "MYR",
    "brent_crude",
    "MYS",
    "usd_myr",
)


def _is_default(val: Any) -> bool:
    """Check if value is a default/non-material sentinel."""
    if val in _DEFAULT_VALS:
        return True
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    return False


def _material_args(arguments: dict[str, Any]) -> dict[str, Any]:
    """Filter to only material (non-administrative, non-default) arguments."""
    material: dict[str, Any] = {}
    for k, v in (arguments or {}).items():
        if k in _ADMIN_ARGS or k.startswith("_"):
            continue
        if _is_default(v):
            continue
        material[k] = v
    return material


def _result_is_empty(result: Any) -> bool:
    """Detect results that are structurally empty or all-zeros with no
    warnings/errors to explain why."""
    if result is None:
        return True
    if not isinstance(result, dict):
        return False
    # If there are warnings or errors, it's not silent — it's informative
    if result.get("warnings") or result.get("errors"):
        return False
    numeric_vals = [v for v in result.values() if isinstance(v, (int, float))]
    if numeric_vals and all(v == 0 for v in numeric_vals):
        return True
    return False


def _scan_verdict_conflict(envelope: dict) -> list[str]:
    """Detect verdict conflicts: MISSING/WEAK evidence but affirmative verdict.

    Returns list of conflict descriptions, empty if none found.
    """
    conflicts: list[str] = []
    evidence_q = str(envelope.get("evidence_quality", "")).upper()
    result = envelope.get("result", {})

    if evidence_q in ("MISSING", "WEAK", "SPECULATED"):
        if not isinstance(result, dict):
            return conflicts
        risk = str(
            result.get("risk_level", result.get("overall_capture_risk", ""))
        ).upper()
        interpretation = str(result.get("interpretation", "")).upper()
        positive = {
            "LOW",
            "GREEN",
            "SAFE",
            "STABLE",
            "ADEQUATE",
            "OK",
            "PASS",
            "MINIMAL",
        }
        if risk in positive:
            conflicts.append(f"risk_level={risk} on evidence_quality={evidence_q}")
        if any(p in interpretation for p in ["LOW", "ORGANIC", "WELL-INTEGRATED"]):
            conflicts.append(
                f"positive_interpretation on evidence_quality={evidence_q}"
            )
    return conflicts


def _estimate_coverage(material: dict[str, Any], result: Any) -> float:
    """Estimate coverage ratio from tool output.

    Prefers tool-reported fields_present/fields_missing when available.
    Falls back to heuristic substring matching.
    """
    # If tool reports its own coverage, trust it
    if isinstance(result, dict):
        fields_present = result.get("fields_present", [])
        fields_missing = result.get("fields_missing", [])
        total = len(fields_present) + len(fields_missing)
        if total > 0:
            return coverage_ratio(len(fields_present), total)

    # Heuristic fallback
    if not material:
        return 1.0
    if result is None:
        return 0.0
    if not isinstance(result, dict):
        return 0.5

    result_str = json.dumps(result, default=str).lower()
    result_keys_lower = {k.lower() for k in result.keys()}
    matched = 0
    for k in material:
        k_lower = k.lower()
        if k_lower in result_str:
            matched += 1
        elif any(k_lower in rk for rk in result_keys_lower):
            matched += 1
    return coverage_ratio(matched, len(material))


class WealthEvidenceMiddleware(Middleware):
    """W0 — Enforces verification integrity on every WEALTH tool call.

    Catches: silent input dropping, verdict conflicts, null→green coercion.
    """

    async def on_call_tool(self, context, call_next):
        # ── PRE-CALL ──────────────────────────────────────────────────
        name = getattr(context, "name", getattr(context, "tool_name", "unknown"))
        arguments: dict[str, Any] = dict(getattr(context, "arguments", {}) or {})
        material = _material_args(arguments)

        # ── EXECUTE ───────────────────────────────────────────────────
        result = await call_next(context)

        # ── POST-CALL — result is the tool's raw dict (envelope) ──────
        if not isinstance(result, dict):
            return result

        result_data = result.get("result", {})
        coverage = _estimate_coverage(material, result_data)
        verdict_conflicts = _scan_verdict_conflict(result)
        is_empty = _result_is_empty(result_data) if material else False

        # Build W0 witness block
        w0: dict[str, Any] = {
            "coverage": coverage,
            "material_args_count": len(material),
            "material_args": sorted(material.keys()),
            "gate": "PASS",
            "warnings": [],
        }

        # Gate 1: zero coverage + material inputs provided
        if coverage == 0.0 and material:
            w0["gate"] = "CAUTION"
            w0["warnings"].append(
                f"COVERAGE_ZERO: {len(material)} material fields provided "
                f"({sorted(material.keys())}) but none reflected in result. "
                "Silent input dropping suspected."
            )

        # Gate 2: verdict conflicts
        if verdict_conflicts:
            if w0["gate"] == "PASS":
                w0["gate"] = "CAUTION"
            w0["warnings"].extend(f"VERDICT_CONFLICT: {c}" for c in verdict_conflicts)

        # Gate 3: empty result despite material inputs
        if is_empty:
            if w0["gate"] == "PASS":
                w0["gate"] = "CAUTION"
            w0["warnings"].append(
                "EMPTY_RESULT: material inputs provided but result is "
                "all-zeros with no errors or warnings. "
                "Possible silent coercion to zero."
            )

        # Inject W0 witness
        result["_w0_evidence_middleware"] = w0

        # If CAUTION, inject into warnings array
        if w0["gate"] == "CAUTION" and w0["warnings"]:
            existing = result.get("warnings", [])
            if isinstance(existing, list):
                result["warnings"] = existing + [f"[W0] {w}" for w in w0["warnings"]]

        return result
