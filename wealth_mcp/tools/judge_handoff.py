"""
WEALTH wealth_judge_handoff — Handoff envelope validation — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import CoercedDict


def register_judge_handoff(mcp):
    """Register the judge_handoff tool on the given FastMCP instance."""
    # 9. wealth_judge_handoff — Handoff envelope validation and submission
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="wealth_judge_handoff",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Build or validate structured handoff envelope for arifOS governance review and 888_HOLD judgment. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain": "meta", "kind": "governance", "canonical": "v1"},
    )
    async def wealth_judge_handoff(
        mode: str = "prepare",
        intent: str = "",
        reversibility: str = "REVERSIBLE",
        blast_radius: str = "low",
        actor_id: str | None = None,
        # C10 2026-08-06: This flag is CALLER-DECLARED. WEALTH has no independent
        # cryptographic verification of actor identity. Gate policy (blast_radius=
        # critical → 888_HOLD) is enforceable only when this flag is externally
        # verified (e.g., via SCT token validation in the governance wrapper).
        # Until C10 hardening, do not treat this as a security boundary.
        actor_cryptographically_verified: bool = False,
        payload: CoercedDict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """Validate and prepare handoff envelope for arifOS governance."""
        m = str(mode).lower().strip()
        p = payload or {}

        # 0. Unknown mode gate — never silently accept invalid modes (loop 10 fix)
        if m not in ("prepare", "submit"):
            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="meta",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_MODE",
                    "message": f"Unknown mode '{mode}'. Valid modes: prepare, submit.",
                    "valid_modes": ["prepare", "submit"],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                errors=[f"Unknown mode '{mode}'. Valid: prepare, submit."],
                session_id=session_id,
                actor_id=actor_id,
            )

        # 1. Intent validation: reject vague/unbounded intents
        intent_clean = str(intent or p.get("intent", "")).strip()
        vague_intents = [
            "aku nak tau semua truth",
            "everything",
            "all truth",
            "tau semua",
            "test",
        ]
        is_unbounded = (
            not intent_clean
            or any(v in intent_clean.lower() for v in vague_intents)
            or len(intent_clean) < 5
        )

        # 2. Reversibility validation: enforce standard enum
        rev_raw = (
            str(reversibility or p.get("reversibility", "REVERSIBLE")).strip().upper()
        )
        valid_reversibility = {"REVERSIBLE", "IRREVERSIBLE", "SEALED_GATE", "READ_ONLY"}
        is_invalid_reversibility = rev_raw not in valid_reversibility

        # 3. Blast radius & authentication check
        blast = str(blast_radius or p.get("blast_radius", "low")).lower().strip()
        is_critical = blast == "critical"
        auth_verified = bool(
            actor_cryptographically_verified
            or p.get("actor_cryptographically_verified")
        )

        # Rule: blast_radius=critical without cryptographic actor verification requires 888_HOLD
        requires_888 = is_critical and not auth_verified

        errors = []
        warnings = []
        if is_unbounded:
            errors.append(
                f"INADMISSIBLE_INTENT: Intent '{intent_clean}' is unbounded/vague. Provide bounded, specific intent."
            )
        if is_invalid_reversibility:
            errors.append(
                f"INVALID_REVERSIBILITY: '{reversibility}' is not a valid reversibility level. Must be one of {sorted(list(valid_reversibility))}."
            )
        if requires_888:
            warnings.append(
                "888_HOLD_REQUIRED: Critical blast radius requires 888_HOLD or cryptographic actor verification."
            )

        if m == "submit" and (errors or requires_888):
            # Submission forbidden if validation errors exist or 888_HOLD required
            result = {
                "status": "REJECTED_BY_GOVERNANCE",
                "mode": "submit",
                "submitted": False,
                "hold_reason": "888_HOLD_REQUIRED"
                if requires_888
                else "VALIDATION_FAILED",
                "action": "PREPARE_ONLY",
                "validation_errors": errors,
                "warnings": warnings,
            }
            return wrap_result(
                tool_name="wealth_judge_handoff",
                domain="meta",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.SPECULATED,
                claim_state=ClaimState.VOID if errors else ClaimState.DRAFT,
                execution_authorized=False,
                requires_888_hold=True,
                errors=errors,
                warnings=warnings,
                session_id=session_id,
                actor_id=actor_id,
            )

        status = "PREPARED" if m == "prepare" else "SUBMITTED"
        result = {
            "status": status,
            "mode": m,
            "submitted": (status == "SUBMITTED"),
            "intent": intent_clean,
            "reversibility": rev_raw if not is_invalid_reversibility else "UNKNOWN",
            "blast_radius": blast,
            "actor_id": actor_id or "unverified",
            "actor_cryptographically_verified": auth_verified,
            "requires_888_hold": requires_888,
            "validation_errors": errors,
            "warnings": warnings,
        }
        return wrap_result(
            tool_name="wealth_judge_handoff",
            domain="meta",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED
            if not errors
            else EpistemicTag.SPECULATED,
            evidence_quality=EvidenceQuality.MODERATE
            if not errors
            else EvidenceQuality.WEAK,
            claim_state=ClaimState.DRAFT if m == "prepare" else ClaimState.QC_VERIFIED,
            execution_authorized=(status == "SUBMITTED" and not requires_888),
            requires_888_hold=requires_888,
            errors=errors,
            warnings=warnings,
            session_id=session_id,
            actor_id=actor_id,
        )

