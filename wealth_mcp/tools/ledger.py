"""
WEALTH capital_ledger — VAULT999 immutable ledger access — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations

from wealth_contracts.authority import ExecutionAuthority
from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import _call_legacy_tool


def register_ledger(mcp):
    """Register the ledger tool on the given FastMCP instance."""
    # ═══════════════════════════════════════════════════════════════════
    # 6. capital_ledger — Immutable vault
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_ledger",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="VAULT999 immutable ledger access — query read-only, write requires human acknowledgment. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain", "kind", "canonical", "action:irreversible", "risk:c2"},
    )
    async def capital_ledger(
        mode: str,
        query: str = "",
        limit: int = 10,
        asset_id: str = "",
        tx_type: str = "",
        amount: float = 0,
        currency: str = "MYR",
        description: str = "",
        amount_satoshi: int = 0,
        payment_hash: str = "",
        ack_irreversible: bool = False,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        m = mode.lower()

        if m == "query":
            raw = await _call_legacy_tool(
                "wealth_vault_query",
                {
                    "query": query,
                    "limit": limit,
                    "asset_id": asset_id,
                    "session_id": session_id,
                },
            )
            return wrap_result(
                tool_name="capital_ledger",
                domain="vault",
                result=raw,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.OBSERVED,
                source_attribution=["vault999_query"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
            )
        if m == "write":
            if not ack_irreversible:
                return wrap_result(
                    tool_name="capital_ledger",
                    domain="vault",
                    result={
                        "status": "HOLD",
                        "error_code": "F13_ACK_REQUIRED",
                        "message": (
                            "VAULT999 write blocked: requires explicit human "
                            "acknowledgment (ack_irreversible=true). This action "
                            "is IRREVERSIBLE — no undo is possible after commit."
                        ),
                        "write_blocked_reason": (
                            "ack_irreversible was not explicitly set to True. "
                            "VAULT999 writes are append-only and immutable."
                        ),
                    },
                    epistemic_tag=EpistemicTag.DERIVED,
                    evidence_quality=EvidenceQuality.MISSING,
                    execution_authority=ExecutionAuthority.BLOCKED,
                    requires_888_hold=True,
                    source_attribution=["ledger_write_gate"],
                    session_id=session_id,
                    trace_id=trace_id,
                    actor_id=actor_id,
                    warnings=["No ledger mutation was attempted."],
                )
            # ── P6 alpha-zen conformance: duplicate-payment guard (2026-09-22) ──
            # payment_hash MUST make retries idempotent: a second write carrying a
            # payment_hash already present is a DUPLICATE replay and is blocked.
            import json as _json

            seen_path = "/root/VAULT999/wealth/payment_hashes.seen.jsonl"
            if payment_hash and len(str(payment_hash).strip()) >= 8:
                dup_ref = None
                # belt 1: local seen-sidecar (deterministic, storage-independent)
                try:
                    with open(seen_path, "r", encoding="utf-8") as _fh:
                        for _i, _ln in enumerate(_fh, 1):
                            if str(payment_hash) in _ln:
                                dup_ref = f"payment_hashes.seen.jsonl:{_i}"
                                break
                except OSError:
                    pass
                # belt 2: VAULT999 full-record search
                if dup_ref is None:
                    _probe = await _call_legacy_tool(
                        "wealth_vault_query",
                        {"query": str(payment_hash), "limit": 5, "session_id": session_id},
                    )
                    if isinstance(_probe, dict):
                        try:
                            if int(_probe.get("count") or 0) >= 1:
                                dup_ref = f"vault999_search_count={_probe.get('count')}"
                        except (TypeError, ValueError):
                            pass
                if dup_ref is not None:
                    return wrap_result(
                        tool_name="capital_ledger",
                        domain="vault",
                        result={
                            "status": "DUPLICATE",
                            "error_code": "DUPLICATE_PAYMENT_HASH",
                            "duplicate_payment_hash": payment_hash,
                            "duplicate_evidence": dup_ref,
                            "message": (
                                "Duplicate payment blocked: payment_hash already recorded "
                                f"({dup_ref}). Idempotent replay — no new ledger write performed."
                            ),
                        },
                        epistemic_tag=EpistemicTag.OBSERVED,
                        evidence_quality=EvidenceQuality.OBSERVED,
                        execution_authority=ExecutionAuthority.BLOCKED,
                        requires_888_hold=False,
                        source_attribution=["ledger_duplicate_guard_p6"],
                        session_id=session_id,
                        trace_id=trace_id,
                        actor_id=actor_id,
                        warnings=["Retry suppressed: duplicate payment_hash."],
                    )
            raw = await _call_legacy_tool(
                "wealth_vault_write",
                {
                    "tx_type": tx_type,
                    "amount": amount,
                    "currency": currency,
                    "description": description,
                    "amount_satoshi": amount_satoshi,
                    "payment_hash": payment_hash,
                    "ack_irreversible": True,
                    "session_id": session_id,
                    "trace_id": trace_id,
                    "actor_id": actor_id,
                },
            )
            if raw.get("status") == "APPENDED" and payment_hash and len(str(payment_hash).strip()) >= 8:
                try:
                    with open(seen_path, "a", encoding="utf-8") as _fh:
                        _fh.write(
                            _json.dumps({"payment_hash": str(payment_hash), "tx_type": tx_type}) + "\n"
                        )
                except OSError:
                    pass
            persisted = raw.get("status") == "APPENDED"
            return wrap_result(
                tool_name="capital_ledger",
                domain="vault",
                result=raw,
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=(
                    EvidenceQuality.OBSERVED
                    if persisted
                    else EvidenceQuality.MISSING
                ),
                execution_authority=(
                    ExecutionAuthority.OBSERVATION
                    if persisted
                    else ExecutionAuthority.BLOCKED
                ),
                requires_888_hold=not persisted,
                source_attribution=["vault999_local_append"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
                errors=[] if persisted else ["Ledger persistence was not confirmed."],
            )

        raise ValueError(f"Unknown mode '{mode}'. Valid: query, write")
