"""
LAW-WEALTH-01 — Reality-Bound Capability Promotion (F13 ratified 2026-09-16).

WEALTH computes. arifOS judges. Human decides.
No WEALTH capability may be promoted above SPECULATED unless it passes
all 10 clauses below. This module makes the law testable in CI.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class PromotionState(str, Enum):
    """Where a capability sits on the truth ladder.

    Promotion is monotonic: a capability cannot move DOWN unless a
    regression is detected and LAW-WEALTH-01 §6 (four-truth receipt)
    forces it back to a lower state.
    """

    DECLARED = "DECLARED"            # Schema exists, never executed
    IMPORTABLE = "IMPORTABLE"        # Cold-import succeeds
    INVOKABLE = "INVOKABLE"          # Safe invocation returns envelope
    VALIDATED = "VALIDATED"          # All 10 LAW clauses pass
    LIVE = "LIVE"                    # Probe confirms in serving build
    DEGRADED = "DEGRADED"            # Some clause now fails
    HELD = "HELD"                    # Policy HOLD; arifOS review pending
    UNAVAILABLE = "UNAVAILABLE"      # Upstream or runtime dead
    DEAD = "DEAD"                    # Import or cold-start failed


@dataclass
class ClauseResult:
    """Outcome of one LAW-WEALTH-01 clause evaluation."""

    clause_id: int
    title: str
    passed: bool
    detail: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class LawEvaluation:
    """Aggregate of all 10 clauses against one capability."""

    capability: str
    state: PromotionState
    clauses: list[ClauseResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.clauses if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.clauses if not c.passed)

    @property
    def is_validated(self) -> bool:
        return self.failed_count == 0 and self.passed_count == 10

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "state": self.state.value,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "validated": self.is_validated,
            "clauses": [
                {
                    "id": c.clause_id,
                    "title": c.title,
                    "passed": c.passed,
                    "detail": c.detail,
                    "evidence": dict(c.evidence),
                }
                for c in self.clauses
            ],
        }


# ── 10 LAW clauses (canonical, machine-readable) ──────────────────────

LAW_W01_CLAUSES: tuple[tuple[int, str, str], ...] = (
    (1, "schema_validity", "Inputs/outputs validate against declared contracts"),
    (2, "input_fidelity", "Every material input consumed and reflected in output"),
    (3, "evidence_binding", "Claims carry source refs or epistemic labels"),
    (4, "temporal_validity", "Current-state outputs carry time/source/freshness/eligibility"),
    (5, "runtime_proof", "Promotion requires independent runtime probe, not schema only"),
    (6, "four_truth_receipt", "PASS iff transport/execution/semantic/policy all pass"),
    (7, "failure_injection", "Controlled failure tests exist before promotion"),
    (8, "calibration", "Interpretive capabilities stay ≤ SPECULATED until calibrated"),
    (9, "authority_boundary", "WEALTH cannot self-authorize execution/allocation/judgment"),
    (10, "named_entity_discipline", "Public claims about named entities require external sources"),
)


class LawWealth01:
    """Callable enforcement of LAW-WEALTH-01.

    Use:
        law = LawWealth01()
        result = law.evaluate(
            capability="capital_diagnose",
            checks={...},
        )
        if not result.is_validated:
            downgrade_to(result.state)
    """

    def evaluate(
        self,
        capability: str,
        checks: Mapping[int, Callable[[], tuple[bool, str, Mapping[str, Any]]]],
    ) -> LawEvaluation:
        clauses: list[ClauseResult] = []
        for cid, title, desc in LAW_W01_CLAUSES:
            check = checks.get(cid)
            if check is None:
                clauses.append(
                    ClauseResult(
                        clause_id=cid,
                        title=title,
                        passed=False,
                        detail=f"clause '{title}' not provided ({desc})",
                    )
                )
                continue
            try:
                passed, detail, evidence = check()
            except Exception as exc:  # noqa: BLE001 — fail-closed
                passed, detail, evidence = False, f"check raised: {exc}", {}
            clauses.append(
                ClauseResult(
                    clause_id=cid,
                    title=title,
                    passed=passed,
                    detail=detail if detail else desc,
                    evidence=evidence,
                )
            )

        if all(c.passed for c in clauses):
            state = PromotionState.VALIDATED
        elif any(not c.passed for c in clauses[:5]):
            # First five are minimum-viable (import/schema/runtime)
            state = PromotionState.DEGRADED
        else:
            state = PromotionState.HELD

        return LawEvaluation(
            capability=capability,
            state=state,
            clauses=clauses,
        )


def enforcement_required(state: PromotionState, capability: str = "") -> bool:
    """Promote-or-hold gate used by CI.

    Returns True when a capability at this state may NOT execute live.
    """
    return state in {
        PromotionState.DECLARED,
        PromotionState.UNAVAILABLE,
        PromotionState.DEAD,
    }


__all__ = [
    "PromotionState",
    "ClauseResult",
    "LawEvaluation",
    "LAW_W01_CLAUSES",
    "LawWealth01",
    "enforcement_required",
]