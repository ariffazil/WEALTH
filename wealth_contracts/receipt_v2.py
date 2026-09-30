"""
Receipt v2 — Four-truth witness envelope.

A WEALTH v2 receipt cannot record PASS unless all four truths hold:

  PASS  <=>  transport=RESPONDED
           AND execution=SUCCESS
           AND semantic=VALID
           AND policy IN {OBSERVATION_ONLY, PERMITTED}

A receipt must never label a transport failure, runtime failure,
malformed output, stale data, ignored input, or policy hold as PASS.

Born from the 2026-09-16 incident where a wrapper could record
PASS despite an upstream HTTP 500 — the audit graded wrapper
completion rather than factual success.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TransportState(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    RESPONDED = "RESPONDED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"


class ExecutionState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CRASHED = "CRASHED"
    CANCELLED = "CANCELLED"


class SemanticState(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    VALID = "VALID"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"
    INPUT_FIDELITY_FAIL = "INPUT_FIDELITY_FAIL"
    CONTRACT_INVALID = "CONTRACT_INVALID"
    CONFLICTED = "CONFLICTED"
    UNMEASURED = "UNMEASURED"


class PolicyState(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    OBSERVATION_ONLY = "OBSERVATION_ONLY"
    PERMITTED = "PERMITTED"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


class Verdict(str, Enum):
    PASS = "PASS"
    DEGRADED = "DEGRADED"
    HOLD = "HOLD"
    FAIL = "FAIL"


DECISION_ELIGIBILITY = {
    # semantic state -> decision eligibility
    SemanticState.NOT_EVALUATED: "INELIGIBLE",
    SemanticState.VALID: "ELIGIBLE",
    SemanticState.STALE: "INELIGIBLE",
    SemanticState.INCOMPLETE: "INELIGIBLE",
    SemanticState.INPUT_FIDELITY_FAIL: "INELIGIBLE",
    SemanticState.CONTRACT_INVALID: "INELIGIBLE",
    SemanticState.CONFLICTED: "INELIGIBLE",
    SemanticState.UNMEASURED: "INELIGIBLE",
}


def compute_verdict(
    transport: TransportState,
    execution: ExecutionState,
    semantic: SemanticState,
    policy: PolicyState,
) -> Verdict:
    """The decisive four-truth invariant.

    PASS iff all four truths hold.
    """
    transport_ok = transport == TransportState.RESPONDED
    execution_ok = execution == ExecutionState.SUCCESS
    semantic_ok = semantic == SemanticState.VALID
    policy_ok = policy in (PolicyState.OBSERVATION_ONLY, PolicyState.PERMITTED)

    if (
        execution in (ExecutionState.FAILED, ExecutionState.CRASHED)
        or transport in (TransportState.TIMEOUT, TransportState.NETWORK_ERROR)
    ):
        return Verdict.FAIL

    if semantic in (
        SemanticState.INPUT_FIDELITY_FAIL,
        SemanticState.CONTRACT_INVALID,
        SemanticState.CONFLICTED,
    ):
        if policy == PolicyState.HOLD:
            return Verdict.HOLD
        return Verdict.FAIL

    if transport_ok and execution_ok and semantic_ok and policy_ok:
        return Verdict.PASS

    if policy == PolicyState.HOLD or semantic == SemanticState.STALE:
        return Verdict.HOLD

    return Verdict.DEGRADED


def decision_eligibility(semantic: SemanticState, policy: PolicyState) -> str:
    """Resolve decision eligibility from semantic + policy.

    Stale, missing, or held outputs are INELIGIBLE — never actionable.
    """
    if policy in (PolicyState.HOLD, PolicyState.BLOCKED):
        return "INELIGIBLE"
    return DECISION_ELIGIBILITY.get(semantic, "INELIGIBLE")


@dataclass
class ReceiptV2:
    """Machine-checkable receipt of one tool invocation."""

    receipt_id: str
    tool_name: str
    tool_version: str
    trace_id: str = ""
    request_id: str = ""
    idempotency_key: str = ""

    # Source/build attestation
    source_revision: str = ""
    build_digest: str = ""

    # Four truths
    transport: TransportState = TransportState.NOT_ATTEMPTED
    execution: ExecutionState = ExecutionState.NOT_STARTED
    semantic: SemanticState = SemanticState.NOT_EVALUATED
    policy: PolicyState = PolicyState.NOT_EVALUATED

    # Derived
    verdict: Verdict = Verdict.FAIL
    decision_eligibility: str = "INELIGIBLE"

    # Hashes
    input_hash: str = ""
    output_hash: str = ""
    parent_receipt_hash: str = ""

    # Provenance
    evidence_refs: list[str] = field(default_factory=list)
    runtime_attestation: dict = field(default_factory=dict)
    sanitized_error: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        # Re-derive verdict + eligibility from the four truths.
        # A receipt is invalid if these disagree with stored fields.
        derived_verdict = compute_verdict(
            self.transport, self.execution, self.semantic, self.policy
        )
        if derived_verdict != self.verdict:
            # Force the invariant. Never silently promote.
            self.verdict = derived_verdict
        self.decision_eligibility = decision_eligibility(self.semantic, self.policy)

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "idempotency_key": self.idempotency_key,
            "source_revision": self.source_revision,
            "build_digest": self.build_digest,
            "transport": self.transport.value,
            "execution": self.execution.value,
            "semantic": self.semantic.value,
            "policy": self.policy.value,
            "verdict": self.verdict.value,
            "decision_eligibility": self.decision_eligibility,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "parent_receipt_hash": self.parent_receipt_hash,
            "evidence_refs": list(self.evidence_refs),
            "runtime_attestation": dict(self.runtime_attestation),
            "sanitized_error": self.sanitized_error,
            "created_at": self.created_at,
            # Four-truth invariant explicit in payload
            "_invariant": (
                "PASS iff transport=RESPONDED AND execution=SUCCESS "
                "AND semantic=VALID AND policy in {OBSERVATION_ONLY, PERMITTED}"
            ),
        }


__all__ = [
    "TransportState",
    "ExecutionState",
    "SemanticState",
    "PolicyState",
    "Verdict",
    "ReceiptV2",
    "compute_verdict",
    "decision_eligibility",
]