"""
WEALTH capital_entropy — Entropy Integrity Mesh — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.authority import ExecutionAuthority
from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import (
    CoercedDict, CoercedDictListStrict, CoercedStrList,
)


def register_entropy(mcp):
    """Register the entropy tool on the given FastMCP instance."""
    # ── Entropy Integrity Mesh — WEALTH Extensions (Phase 2) ─────────────
    @mcp.tool(
        name="capital_entropy",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Capital and institutional entropy analysis — measures information loss, consequence displacement, and metric drift. Computes, never allocates. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={
            "domain": "institutional",
            "kind": "abductive",
            "canonical": "v1",
            "entropy": "mesh",
        },
    )
    async def capital_entropy(
        mode: str,
        decision_makers: CoercedDictListStrict = None,
        beneficiaries: CoercedDictListStrict = None,
        cost_bearers: CoercedDictListStrict = None,
        veto_holders: CoercedStrList = None,
        declared_purpose: str | None = None,
        current_kpis: CoercedDictListStrict = None,
        actual_behaviors: CoercedStrList = None,
        excluded_outcomes: CoercedStrList = None,
        decision_ref: str | None = None,
        actors: CoercedDictListStrict = None,
        trust_events: CoercedDictListStrict = None,
        current_trust_balance: float = 0.5,
        order_indicators: CoercedDict = None,
        suppression_indicators: CoercedDict = None,
        actor_ref: str | None = None,
        local_efficiency_claims: CoercedDict = None,
        exported_costs: CoercedDictListStrict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
        shadow: bool = False,
    ) -> dict:
        """Entropy Integrity Mesh — WEALTH domain witness."""
        # Parameters are coerced by the Pydantic BeforeValidator annotations.
        if veto_holders is not None:
            veto_holders = [
                {"name": value} if isinstance(value, str) else value
                for value in veto_holders
            ]

        def _wrap_entropy(result: dict) -> dict:
            return wrap_result(
                tool_name="capital_entropy",
                domain="institutional",
                result=result,
                source_attribution=["entropy_integrity_local_dependency"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                shadow=shadow,
            )

        def _entropy_failure(
            code: str,
            message: str,
            *,
            action: str,
            hold: bool,
        ) -> dict:
            result = {
                "status": "UNAVAILABLE" if hold else "ERROR",
                "error_code": code,
                "message": message,
                "tool": "capital_entropy",
                "mode": m,
                "action": action,
            }
            if hold:
                result["holds"] = [code]
            return wrap_result(
                tool_name="capital_entropy",
                domain="institutional",
                result=result,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.SPECULATED,
                execution_authority=ExecutionAuthority.BLOCKED,
                requires_888_hold=False,
                source_attribution=["entropy_integrity_dependency_check"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                shadow=shadow,
                errors=[message],
            )

        m = str(mode).lower().strip()
        try:
            import importlib.util
            from pathlib import Path

            base = (
                Path(__file__).resolve().parents[2]
                / "entropy-integrity"
                / "mcp"
                / "wealth"
            )

            def _safe_load_module(name: str, filename: str):
                if not base.is_dir():
                    raise ImportError(
                        f"optional dependency directory is absent from this repository: {base}"
                    )
                filepath = base / filename
                if not filepath.is_file():
                    raise ImportError(
                        f"optional dependency module is absent: {filepath}"
                    )
                spec = importlib.util.spec_from_file_location(name, filepath)
                if spec is None or spec.loader is None:
                    raise ImportError(
                        f"cannot load optional dependency module: {filepath}"
                    )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module

            if m == "power_consequence_map":
                module = _safe_load_module("pcm", "power_consequence_map.py")
                return _wrap_entropy(
                    module.wealth_power_consequence_map(
                        decision_makers=decision_makers or [],
                        beneficiaries=beneficiaries or [],
                        cost_bearers=cost_bearers or [],
                        veto_holders=veto_holders,
                    )
                )

            if m == "metric_purpose_audit":
                # Zen Phase 3: keyword overlap is not semantic analysis.
                # This tool computes token-set Jaccard similarity only.
                # Output tagged SPECULATED/MISSING to prevent false precision.
                module = _safe_load_module("mpa", "metric_purpose_audit.py")
                raw_result = module.wealth_metric_purpose_audit(
                    declared_purpose=declared_purpose or "",
                    current_kpis=current_kpis or [],
                    actual_behaviors=actual_behaviors or [],
                    excluded_outcomes=excluded_outcomes,
                )
                # Strip the machine-generated interpretation verdict
                raw_result.pop("interpretation", None)
                raw_result["_zen_note"] = (
                    "Interpretation removed per Phase 3. "
                    "Keyword-overlap alignment scores are token-set Jaccard similarity — "
                    "NOT semantic analysis. Use the reflection questions, not the numbers."
                )
                return _wrap_entropy(
                    {
                        "audit_id": raw_result.get("audit_id"),
                        "declared_purpose": raw_result.get("declared_purpose"),
                        "kpi_alignment": raw_result.get("kpi_alignment", []),
                        "purpose_fidelity": raw_result.get("purpose_fidelity"),
                        "gaming_signals": raw_result.get("gaming_signals", []),
                        "externality_count": raw_result.get("externality_count", 0),
                        "excluded_outcomes": raw_result.get("excluded_outcomes", []),
                        "reflection": raw_result.get("reflection", []),
                        "metadata": raw_result.get("metadata", {}),
                        "_zen_note": (
                            "Interpretation removed per Phase 3. "
                            "Keyword-overlap alignment scores are token-set Jaccard similarity — "
                            "NOT semantic analysis. Use the reflection questions, not the numbers."
                        ),
                    }
                )

            if m == "responsibility_ledger":
                module = _safe_load_module("rl", "responsibility_ledger.py")
                return _wrap_entropy(
                    module.wealth_responsibility_ledger(
                        decision_ref=decision_ref or "", actors=actors or []
                    )
                )

            if m == "trust_capital_decay":
                module = _safe_load_module("tcd", "trust_capital_decay.py")
                return _wrap_entropy(
                    module.wealth_trust_capital_decay(
                        trust_events=trust_events or [],
                        current_trust_balance=current_trust_balance,
                    )
                )

            if m == "coercive_order_cost":
                module = _safe_load_module("coc", "coercive_order_cost.py")
                return _wrap_entropy(
                    module.wealth_coercive_order_cost(
                        order_indicators=order_indicators or {},
                        suppression_indicators=suppression_indicators or {},
                    )
                )

            if m == "entropy_externality":
                module = _safe_load_module("ee", "entropy_externality.py")
                return _wrap_entropy(
                    module.wealth_entropy_externality(
                        actor_ref=actor_ref or "",
                        local_efficiency_claims=local_efficiency_claims or {},
                        exported_costs=exported_costs or [],
                    )
                )

            return _entropy_failure(
                "UNKNOWN_MODE",
                f"Unknown mode '{mode}'.",
                action=(
                    "Use one of: power_consequence_map, metric_purpose_audit, "
                    "responsibility_ledger, trust_capital_decay, "
                    "coercive_order_cost, entropy_externality"
                ),
                hold=False,
            )
        except ImportError as exc:
            return _entropy_failure(
                "ENTROPY_MODULE_MISSING",
                str(exc),
                action=(
                    "Declare and vendor the optional entropy-integrity dependency "
                    "inside this repository before enabling this mode."
                ),
                hold=True,
            )
        except Exception as exc:
            return _entropy_failure(
                "ENTROPY_COMPUTE_ERROR",
                f"{type(exc).__name__}: {exc}",
                action="Inspect the named local dependency module and retry.",
                hold=True,
            )

