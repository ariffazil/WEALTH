# WEALTH MCP — Advisory Boundary Module
# PR 5: Enforce no-default-rich-synthesis, synthetic-input labeling, and
# DOMAIN_SEAL_VALIDITY vs JUDGE_SEAL_AUTHORIZATION clarity across all 44
# WEALTH tools.
#
# Doctrine (F2 Truth, F7 Stewardship, F13 SOVEREIGN):
#   - WEALTH advises. arifOS authorizes. Never the reverse.
#   - Every WEALTH output carries the domain-seal-validity label so the
#     agent that consumes it can never mistake a WEALTH advisory verdict
#     for an execution-grade seal.
#   - When inputs are missing or synthetic, the tool MUST say so. The
#     "rich default narrative" is the forbidden path. INSUFFICIENT_INPUT
#     or SYNTHETIC is the honest path.
#
# Floor map:
#   F1 AMANAH     — every detection is observable from metrics; no inference.
#   F2 TRUTH      — disclaimers are facts, not vibes.
#   F7 STEWARDSHIP — never let a missing input become a confident synthesis.
#   F13 SOVEREIGN  — this module labels authority; it does not grant it.
#
# SPEAR: DITEMPA BUKAN DIBERI — Forged, Not Given.

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

# ─── AUTHORITY CONSTANTS ─────────────────────────────────────────────────
# These are the only two seal authorities a WEALTH tool may emit. arifOS
# alone holds JUDGE_SEAL_AUTHORIZATION for execution-grade work.

DOMAIN_SEAL_VALIDITY: str = "WEALTH|advisory_only"
"""A WEALTH tool's verdict is domain-valid (i.e., the math is sound) but
advisory only. It does NOT authorize execution. arifOS 888_JUDGE holds the
only JUDGE_SEAL_AUTHORIZATION that an action can be executed against."""

JUDGE_SEAL_AUTHORIZATION: str = "arifOS|execution_authorized"
"""The execution-grade seal. Only arifOS 888_JUDGE may emit this. WEALTH
never emits it. WEALTH tools that need execution-grade verdicts must
hand off to arifOS."""

# ─── DETECTION SIGNALS ───────────────────────────────────────────────────
# Field names that, when missing/None/empty, signal INSUFFICIENT_INPUT.
# These are the cash-flow-shaped fields that a synthesis cannot fabricate
# without violating F7.

INSUFFICIENT_INPUT_FIELDS: tuple = (
    "cash_flows",
    "cashflows",
    "cashflow",
    "cash_flow",
    "p50_value_musd",
    "well_cost_musd",
    "prior_pos",
    "assets",
    "liabilities",
    "income",
    "expenses",
    "holdings",
    "scenarios",
)

# Markers that signal SYNTHETIC input — values produced by a default or
# placeholder path, not by user-supplied data.

SYNTHETIC_MARKERS: tuple = (
    "SYNTHETIC_DEFAULT",
    "SYNTHETIC",
    "synthetic",
    "_default",
    "_placeholder",
    "PLACEHOLDER",
)


# ─── DETECTION HELPERS ───────────────────────────────────────────────────


def detect_synthetic_inputs(metrics: Dict[str, Any]) -> bool:
    """Return True if `metrics` contains any synthetic/placeholder signal.

    F2-honest: walks the dict and looks for SYNTHETIC_MARKERS in string
    values. Does not infer beyond what is observable.
    """
    if not isinstance(metrics, dict):
        return False

    def _walk(node: Any) -> bool:
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and any(m in v for m in SYNTHETIC_MARKERS):
                    return True
                if _walk(v):
                    return True
        elif isinstance(node, list):
            for item in node:
                if _walk(item):
                    return True
        return False

    return _walk(metrics)


def detect_insufficient_input(
    metrics: Dict[str, Any],
    required_fields: Optional[Iterable[str]] = None,
) -> bool:
    """Return True if the metrics dict is missing data the tool needs.

    `required_fields` defaults to INSUFFICIENT_INPUT_FIELDS. A field is
    "missing" if it is absent, None, an empty list, or 0.0.

    F2-honest: this is a presence check, not a quality check. Quality is
    the responsibility of the calling tool.
    """
    if not isinstance(metrics, dict):
        return True  # a non-dict metrics payload is, definitionally, insufficient

    fields = tuple(required_fields) if required_fields is not None else INSUFFICIENT_INPUT_FIELDS
    present_count = 0
    for f in fields:
        if f in metrics:
            v = metrics[f]
            if v is None:
                continue
            if isinstance(v, (list, tuple, str, dict)) and len(v) == 0:
                continue
            if isinstance(v, (int, float)) and v == 0:
                continue
            present_count += 1
    # If NONE of the canonical fields are present with substantive value,
    # the tool has insufficient input.
    return present_count == 0


# ─── ADVISORY BOUNDARY COMPUTATION ───────────────────────────────────────

# The one-line disclaimer that every WEALTH output carries. F2-honest.
# It is short so it cannot be confused with the body of the result, and
# explicit so an agent cannot read past it.

SEAL_AUTHORITY_DISCLAIMER: str = (
    "WEALTH verdict is domain-valid advisory only. "
    "Execution requires arifOS JUDGE_SEAL_AUTHORIZATION."
)


def compute_advisory_boundary(
    metrics: Dict[str, Any],
    decision_class: str = "W2",
    evidence_level: str = "E3",
    required_fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Compute the 5 advisory-boundary fields that must accompany every
    WEALTH tool output.

    Returns a dict with:
      - domain_seal_validity: literal "WEALTH|advisory_only"
      - judge_seal_authorization_required: True for W4/W5; False otherwise
      - synthetic_inputs_detected: True if metrics contain SYNTHETIC markers
      - insufficient_input_detected: True if required fields are absent
      - seal_authority_disclaimer: 1-line F2-honest disclaimer

    F1 AMANAH: every field is computed from the inputs above; no hidden state.
    F13 SOVEREIGN: this function labels authority, it does not grant it.
    """
    return {
        "domain_seal_validity": DOMAIN_SEAL_VALIDITY,
        "judge_seal_authorization_required": decision_class in ("W4", "W5"),
        "synthetic_inputs_detected": detect_synthetic_inputs(metrics),
        "insufficient_input_detected": detect_insufficient_input(
            metrics, required_fields=required_fields
        ),
        "seal_authority_disclaimer": SEAL_AUTHORITY_DISCLAIMER,
    }


# ─── STATUS CONSTANTS ────────────────────────────────────────────────────
# Verdict vocabulary for the INSUFFICIENT_INPUT path. These are advisory
# outputs, not seals.

INSUFFICIENT_INPUT_STATUS: str = "INSUFFICIENT_INPUT"
INSUFFICIENT_INPUT_SUMMARY: str = (
    "Insufficient input — provide cash_flows, p50_value_musd, "
    "well_cost_musd, or prior_pos. No synthesis possible without data."
)
INSUFFICIENT_INPUT_VERDICT: str = "HOLD"

SYNTHETIC_INPUT_STATUS: str = "SYNTHETIC"
SYNTHETIC_INPUT_VERDICT: str = "HOLD"


__all__ = [
    "DOMAIN_SEAL_VALIDITY",
    "JUDGE_SEAL_AUTHORIZATION",
    "INSUFFICIENT_INPUT_FIELDS",
    "SYNTHETIC_MARKERS",
    "INSUFFICIENT_INPUT_STATUS",
    "INSUFFICIENT_INPUT_SUMMARY",
    "INSUFFICIENT_INPUT_VERDICT",
    "SYNTHETIC_INPUT_STATUS",
    "SYNTHETIC_INPUT_VERDICT",
    "SEAL_AUTHORITY_DISCLAIMER",
    "detect_synthetic_inputs",
    "detect_insufficient_input",
    "compute_advisory_boundary",
]
