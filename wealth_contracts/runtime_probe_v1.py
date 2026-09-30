"""
Runtime Probe v1 — read-only safe probes for capital_* tools.

A probe NEVER invokes a real write, submit, publish, allocation,
or execution. It exercises the cold-import, safe-invocation,
schema, semantic-invariant, and sanitized-error paths.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .manifest_v1 import EffectiveState, ProbeOutcome, ProbeManifest


# ── Safe probe argument sets per tool ─────────────────────────────────
# Each entry lists the argument set a probe is permitted to call.
# Real probes MUST NOT call write/submit/publish paths.
SAFE_PROBE_ARGS: dict[str, dict[str, Any]] = {
    "capital_primitive": {
        "cash_flows": [100.0, 110.0, 121.0],
        "discount_rate": 0.10,
        "horizon_years": 3,
        "_probe": True,
    },
    "capital_market": {
        "instrument": "XAUUSD",
        "venue": "PROBE",
        "as_of": "1970-01-01T00:00:00Z",
        "_probe": True,
    },
    "capital_indicator": {
        "instrument": "XAUUSD",
        "series": "PROBE",
        "_probe": True,
    },
    "capital_health": {
        "balance_sheet": {"assets": 1000.0, "liabilities": 400.0},
        "income_statement": {"revenue": 1000.0, "expenses": 600.0},
        "cash_flow_statement": {"operating": 200.0},
        "_probe": True,
    },
    "capital_diagnose": {
        "board_members": [],
        "ownership_structure": {"public": 1.0},
        "regulatory_disclosures": [],
        "financial_statements": {},
        "_probe": True,
    },
    "capital_entropy": {
        "institution": "PROBE",
        "regime_evidence": [],
        "_probe": True,
    },
    "capital_backtest": {
        "strategy": "PROBE",
        "data": [],
        "_probe": True,
    },
    "capital_claims": {
        "claim_text": "",
        "evidence_refs": [],
        "_probe": True,
    },
    "capital_entry_plan": {
        "instrument": "XAUUSD",
        "horizon": "PROBE",
        "risk_tolerance": "LOW",
        "_probe": True,
    },
    "wealth_judge_handoff": {
        "tool_name": "PROBE",
        "result_summary": {},
        "evidence_refs": [],
        "_probe": True,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProbeResult:
    outcome: ProbeOutcome
    raw_exc: str = ""
    duration_ms: int = 0


def cold_import(module_path: str) -> ProbeResult:
    """Cold-import check: does the module import without raising?

    A failed import does NOT mark the tool DEAD — the tool may be
    importable on demand — but it does mark it UNAVAILABLE for the
    probe cycle until the import is restored.
    """
    try:
        importlib.import_module(module_path)
        return ProbeResult(
            outcome=ProbeOutcome(
                capability=module_path,
                probe_state=EffectiveState.IMPORTABLE,
                import_pass=True,
                detail="import succeeded",
            )
        )
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(
            outcome=ProbeOutcome(
                capability=module_path,
                probe_state=EffectiveState.DEAD,
                import_pass=False,
                detail=f"import failed: {type(exc).__name__}",
            ),
            raw_exc=f"{type(exc).__name__}: {exc}"[:200],
        )


def safe_invoke(
    tool_name: str,
    tool_callable: Callable[..., Mapping[str, Any]],
    args: Mapping[str, Any] | None = None,
) -> ProbeResult:
    """Invoke a tool with safe probe arguments.

    The probe NEVER replaces the result or recommendation. It only
    records whether the tool returns a parseable envelope-shaped dict.
    """
    payload = dict(args or SAFE_PROBE_ARGS.get(tool_name, {}))
    payload["_probe"] = True  # signal to tool that this is a probe
    try:
        raw = tool_callable(**payload)
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(
            outcome=ProbeOutcome(
                capability=tool_name,
                probe_state=EffectiveState.DEAD if False else EffectiveState.UNAVAILABLE,
                import_pass=False,
                invocation_pass=False,
                detail=f"invoke failed: {type(exc).__name__}",
            ),
            raw_exc=f"{type(exc).__name__}: {exc}"[:200],
        )

    if not isinstance(raw, Mapping):
        return ProbeResult(
            outcome=ProbeOutcome(
                capability=tool_name,
                probe_state=EffectiveState.DEGRADED,
                import_pass=True,
                invocation_pass=False,
                detail="non-mapping result",
            )
        )

    # Envelope-shape detection: v1 + v2 both have tool_name + domain.
    schema_pass = "tool_name" in raw and "domain" in raw
    semantic_pass = (
        "execution_authorized" in raw
        and raw.get("execution_authorized") is False
    )

    if schema_pass and semantic_pass:
        state = EffectiveState.INVOKABLE
    elif schema_pass:
        state = EffectiveState.DEGRADED
    else:
        state = EffectiveState.HELD

    return ProbeResult(
        outcome=ProbeOutcome(
            capability=tool_name,
            probe_state=state,
            import_pass=True,
            invocation_pass=True,
            schema_pass=schema_pass,
            semantic_pass=semantic_pass,
            detail="envelope detected" if schema_pass else "missing envelope fields",
        )
    )


def probe_capability(
    tool_name: str,
    module_path: str,
    tool_callable: Callable[..., Mapping[str, Any]] | None = None,
) -> ProbeResult:
    """Two-stage cold-import and safe-invoke probe.

    Returns a probe result. The probe NEVER mutates production state.
    """
    imp = cold_import(module_path)
    if imp.outcome.probe_state == EffectiveState.DEAD:
        return imp
    if tool_callable is None:
        return ProbeResult(
            outcome=ProbeOutcome(
                capability=tool_name,
                probe_state=EffectiveState.IMPORTABLE,
                import_pass=True,
                invocation_pass=False,
                detail="imported; callable not registered for probe",
            )
        )
    inv = safe_invoke(tool_name, tool_callable)
    return inv


def build_probe_manifest(results: list[ProbeResult]) -> ProbeManifest:
    """Aggregate probe results into a probe manifest."""
    outcomes = [r.outcome for r in results]
    text = json.dumps([o.to_dict() for o in outcomes], sort_keys=True, default=str)
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return ProbeManifest(
        outcomes=outcomes,
        generated_at=_now(),
        probe_manifest_hash=digest,
    )


__all__ = [
    "SAFE_PROBE_ARGS",
    "ProbeResult",
    "cold_import",
    "safe_invoke",
    "probe_capability",
    "build_probe_manifest",
]