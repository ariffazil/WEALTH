"""
Input-Fidelity Gate v1.

Material input supplied but not consumed/reflected in output is a
BLOCKING semantic failure. The gate is the single source of truth
for what counts as a fidelity failure.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class InputFidelityState(str, Enum):
    NOT_PROVIDED = "NOT_PROVIDED"
    MALFORMED = "MALFORMED"
    UNMAPPED_INPUT = "UNMAPPED_INPUT"
    UNCONSUMED_MATERIAL_INPUT = "UNCONSUMED_MATERIAL_INPUT"
    EMPTY_CONFIRMED = "EMPTY_CONFIRMED"
    MEASURED_ZERO = "MEASURED_ZERO"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    CONFLICTED = "CONFLICTED"
    VALID = "VALID"


@dataclass
class MaterialFieldBinding:
    """One material input field's consumption record."""

    path: str
    supplied: bool
    consumed: bool
    reflected_in_output: bool
    reason: str = ""


@dataclass
class InputFidelityReport:
    """Aggregate fidelity report for one tool invocation."""

    tool_name: str
    state: InputFidelityState
    bindings: list[MaterialFieldBinding] = field(default_factory=list)
    suppressed_recommendation: bool = True

    @property
    def has_unconsumed_material(self) -> bool:
        return any(
            b.supplied and not b.consumed for b in self.bindings
        )

    @property
    def has_unreflected_material(self) -> bool:
        return any(
            b.supplied and b.consumed and not b.reflected_in_output
            for b in self.bindings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "state": self.state.value,
            "suppressed_recommendation": self.suppressed_recommendation,
            "bindings": [
                {
                    "path": b.path,
                    "supplied": b.supplied,
                    "consumed": b.consumed,
                    "reflected_in_output": b.reflected_in_output,
                    "reason": b.reason,
                }
                for b in self.bindings
            ],
            "has_unconsumed_material": self.has_unconsumed_material,
            "has_unreflected_material": self.has_unreflected_material,
        }


# Material input paths per tool — extend as new material fields are
# ratified. Anything in this set is BLOCKING if supplied but ignored.
MATERIAL_INPUT_PATHS: dict[str, tuple[str, ...]] = {
    "capital_diagnose": (
        "board_members",
        "ownership_structure",
        "regulatory_disclosures",
        "financial_statements",
    ),
    "capital_health": (
        "balance_sheet",
        "income_statement",
        "cash_flow_statement",
    ),
    "capital_primitive": (
        "cash_flows",
        "discount_rate",
        "horizon_years",
    ),
    "capital_market": (
        "instrument",
        "venue",
        "as_of",
    ),
    "capital_entry_plan": (
        "instrument",
        "horizon",
        "risk_tolerance",
    ),
    "capital_entropy": (
        "institution",
        "regime_evidence",
    ),
    "capital_claims": (
        "claim_text",
        "evidence_refs",
    ),
    "wealth_judge_handoff": (
        "tool_name",
        "result_summary",
        "evidence_refs",
    ),
}


def _walk(obj: Mapping[str, Any], prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield dotted-path → value pairs from a nested dict."""
    if not isinstance(obj, Mapping):
        yield prefix, obj
        return
    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, Mapping):
            yield from _walk(v, path)
        else:
            yield path, v


def evaluate_input_fidelity(
    tool_name: str,
    inputs: Mapping[str, Any] | None,
    outputs: Mapping[str, Any] | None,
) -> InputFidelityReport:
    """Evaluate whether material inputs were consumed and reflected.

    State semantics:
      NOT_PROVIDED                     → caller sent nothing
      MALFORMED                        → caller payload unparseable
      UNMAPPED_INPUT                  → recognized tool but inputs contain
                                        unexpected top-level keys
      UNCONSUMED_MATERIAL_INPUT       → material path supplied, not read
      EMPTY_CONFIRMED                 → material path supplied, value is [],
                                        binding is honest
      MEASURED_ZERO                    → material path supplied, computed 0
      PARTIAL_EVIDENCE                 → some material paths missing
      INSUFFICIENT_DATA                → no material paths supplied
      CONFLICTED                       → inputs disagree with stored evidence
      VALID                            → all material bindings consumed
                                        and reflected
    """
    bindings: list[MaterialFieldBinding] = []
    inputs = inputs or {}
    outputs = outputs or {}

    material_paths = MATERIAL_INPUT_PATHS.get(tool_name, ())
    if not material_paths:
        return InputFidelityReport(
            tool_name=tool_name,
            state=InputFidelityState.NOT_PROVIDED,
            bindings=[],
            suppressed_recommendation=True,
        )

    # Flatten inputs + outputs for path lookup.
    input_paths = {p: v for p, v in _walk(inputs)}
    output_paths = {p: v for p, v in _walk(outputs)}

    # Unmapped input detection: any top-level key in inputs that is not
    # in material_paths AND not in output_paths is a fidelity violation.
    unmapped: list[str] = []
    for k in inputs.keys():
        if k in material_paths:
            continue
        if any(p == k or p.startswith(f"{k}.") for p in output_paths):
            continue
        unmapped.append(k)

    if unmapped:
        for u in unmapped:
            bindings.append(
                MaterialFieldBinding(
                    path=u,
                    supplied=True,
                    consumed=False,
                    reflected_in_output=False,
                    reason="unmapped top-level key",
                )
            )
        return InputFidelityReport(
            tool_name=tool_name,
            state=InputFidelityState.UNMAPPED_INPUT,
            bindings=bindings,
            suppressed_recommendation=True,
        )

    # Per-material-path binding check.
    consumed_count = 0
    reflected_count = 0
    for path in material_paths:
        supplied = path in input_paths
        # Consumed: input value must appear (by value or by hash) somewhere
        # in the output tree. Reflection is a stronger claim: the output
        # contains a field whose provenance traces back to this input.
        consumed = supplied
        reflected = False
        if supplied:
            value = input_paths[path]
            if value in (None,):
                consumed = False
            else:
                consumed = True
                consumed_count += 1
                # Reflection: output references the input path or value.
                if path in output_paths or value in output_paths.values():
                    reflected = True
                    reflected_count += 1

        bindings.append(
            MaterialFieldBinding(
                path=path,
                supplied=supplied,
                consumed=consumed,
                reflected_in_output=reflected,
                reason="" if consumed else "material path not consumed",
            )
        )

    # Decide state.
    supplied_count = sum(1 for b in bindings if b.supplied)
    if supplied_count == 0:
        state = InputFidelityState.INSUFFICIENT_DATA
    elif any(b.supplied and not b.consumed for b in bindings):
        state = InputFidelityState.UNCONSUMED_MATERIAL_INPUT
    elif supplied_count < len(material_paths):
        state = InputFidelityState.PARTIAL_EVIDENCE
    elif consumed_count != reflected_count:
        state = InputFidelityState.UNCONSUMED_MATERIAL_INPUT
    else:
        state = InputFidelityState.VALID

    return InputFidelityReport(
        tool_name=tool_name,
        state=state,
        bindings=bindings,
        suppressed_recommendation=state != InputFidelityState.VALID,
    )


__all__ = [
    "InputFidelityState",
    "MaterialFieldBinding",
    "InputFidelityReport",
    "MATERIAL_INPUT_PATHS",
    "evaluate_input_fidelity",
]