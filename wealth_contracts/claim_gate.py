"""Named-entity claim gate (P1#1, WEALTH-RECONCILIATION-20260916).

Public-surface rule: a claim about a real, named institution may be labelled
externally verified ONLY if it is bound to an external source URI. The
engine's own output is not a source for claims about real entities.

Born from the 2026-09-16 incident: an engine-internal "0 independent NEDs"
claim about PETRONAS reached a public page as observed fact because nothing
between computation and publication checked evidence binding.

Scope note (COMPUTE_ONLY respected): the gate does NOT refuse computation.
It labels publication eligibility. Fail-closed: on gate error the verdict is
GATE_ERROR with treat-as-unbound semantics.

GENERALISED (2026-09-19)
------------------------
The source-class rule invented here is not WEALTH-specific, so it now lives in
`source_class_ok()` — importable by any organ publishing claims about real
named entities. Two axes are enforced together:

  axis 1  source class  a named-entity claim needs an EXTERNAL source URI;
                        the engine's own output is never such a source.
  axis 2  claim class   a named-entity claim bound for publication must ALSO
                        declare an action-eligible explanatory class
                        (MEASURED / MECHANISM / PATTERN, per claim_kernel).

The legacy keys (`state`, `publication_eligibility`) keep exactly their
pre-2026-09-19 values for existing callers. The second axis lands in additive
keys: `explanation_*` / `publication_decision` / `publishable`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

__all__ = [
    "extract_external_uris",
    "detect_named_entities",
    "is_engine_self_reference",
    "source_class_ok",
    "evaluate_claim_class",
    "evaluate",
    "evaluate_dict_result",
    "SOURCE_CLASS_SCHEMA",
    "SOURCE_CLASS_VERDICTS",
    "EXPLANATORY_SCHEMA",
    "EXPLANATORY_VERDICTS",
    "CLAIM_CLASSES",
    "ACTION_ELIGIBLE_CLASSES",
]

_HERE = Path(__file__).resolve().parent
_REGISTRY_PATH = _HERE / "named_entities.json"

_URI_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def _load_entities() -> list:
    try:
        reg = json.loads(_REGISTRY_PATH.read_text())
        names = list(reg.get("institutions", [])) + list(reg.get("persons", []))
        # longest first so "Saudi Aramco" wins over "Aramco" in reporting
        return sorted({e for e in names if e}, key=len, reverse=True)
    except Exception:
        return []


def extract_external_uris(source_attribution: Optional[Iterable]) -> list:
    """Pull external URIs from source attributions. Names of reports,
    engines, or internal modules are NOT external evidence."""
    uris: list = []
    for s in source_attribution or []:
        for m in _URI_RE.findall(str(s)):
            if m not in uris:
                uris.append(m)
    return uris


def detect_named_entities(text: str, entities: Optional[list] = None) -> list:
    entities = entities if entities is not None else _load_entities()
    found: list = []
    for e in entities:
        # case-sensitive, both-side alpha boundary: "Eni" must not match
        # inside "benign"/"Ending"; "PETROS" not inside "PETROLEUM"
        if re.search(rf"(?<![A-Za-z]){re.escape(e)}(?![A-Za-z])", text):
            found.append(e)
    return found


# ---------------------------------------------------------------------------
# GENERALISED SOURCE-CLASS RULE (2026-09-19)
#
# This is the invention that was never WEALTH-specific: any organ that
# publishes output about a real named entity needs it. Import it, do not copy
# it. Verdict strings are stable API:
#   NO_NAMED_ENTITIES              rule not applicable
#   EXTERNAL_URI_BOUND             rule satisfied
#   ENGINE_SELF_REFERENCE_REJECTED only the engine's own output was named
#   UNBOUND_EXTERNAL_EVIDENCE      no external source URI at all
# ---------------------------------------------------------------------------
SOURCE_CLASS_SCHEMA = "claim_gate/source_class/v1"
SOURCE_CLASS_VERDICTS = (
    "NO_NAMED_ENTITIES",
    "EXTERNAL_URI_BOUND",
    "ENGINE_SELF_REFERENCE_REJECTED",
    "UNBOUND_EXTERNAL_EVIDENCE",
)

# Attribution strings naming the engine's own machinery instead of an outside
# source. Two shapes: prose ("wealth engine", "internal model") and code
# ("governance_analysis", "wealth_core.evidence.claim_gate").
_ENGINE_WORD_RE = re.compile(
    r"\b(engines?|internal|in[- ]house|proprietary|self|module|kernel|"
    r"pipeline|scorer|analys(?:is|es|tics?)|model|simulat\w*)\b",
    re.IGNORECASE,
)
_MODULE_PATH_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$|^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$"
)


def is_engine_self_reference(source: object) -> bool:
    """True when an attribution names the engine itself, not an outside source."""
    text = str(source).strip()
    if not text:
        return False
    if _URI_RE.search(text):
        return False
    if _MODULE_PATH_RE.match(text):
        return True
    return bool(_ENGINE_WORD_RE.search(text))


def source_class_ok(
    source_attribution: Optional[Iterable] = None,
    text: Optional[str] = None,
    entities: Optional[list] = None,
) -> dict:
    """The generalised rule: may this output carry an 'externally verified' label?

    A claim about a real, named entity may be labelled externally verified ONLY
    if it is bound to an external source URI. The engine's own output — module
    names, model names, report titles, self-schemes — is not a source about a
    real entity, however often it is cited.

    Args:
        source_attribution: iterable of attribution strings.
        text: claim text; enables the NO_NAMED_ENTITIES verdict.
        entities: pre-detected entity list (skips detection).

    Returns:
        {verdict, ok, entities_detected, external_source_uris,
         engine_self_sources, entity_check_applied, reason, rule, schema}

    Fail-closed: `ok` is True only for NO_NAMED_ENTITIES (rule not applicable)
    and EXTERNAL_URI_BOUND (rule satisfied). Everything else is not ok.
    """
    sources = [] if source_attribution is None else [str(s) for s in source_attribution]
    uris = extract_external_uris(source_attribution)

    if entities is not None:
        ents, applied = [str(e) for e in entities], True
    elif text is not None:
        ents, applied = detect_named_entities(text), True
    else:
        ents, applied = [], False

    engine_self = [s for s in sources if is_engine_self_reference(s)]
    named = [s for s in sources if s.strip()]

    if applied and not ents:
        verdict, ok = "NO_NAMED_ENTITIES", True
        reason = "No named entities detected; the rule does not apply."
    elif uris:
        verdict, ok = "EXTERNAL_URI_BOUND", True
        reason = f"{len(uris)} external source URI(s) bind this output."
    elif engine_self and len(engine_self) == len(named):
        verdict, ok = "ENGINE_SELF_REFERENCE_REJECTED", False
        reason = (
            "The only sources named are the engine's own output ("
            + ", ".join(engine_self[:3])
            + "). Engine output is not a source about a real entity."
        )
    else:
        verdict, ok = "UNBOUND_EXTERNAL_EVIDENCE", False
        reason = (
            "Named entity with no external source URI. The engine's own "
            "output cannot bind this claim."
        )

    return {
        "verdict": verdict,
        "ok": ok,
        "entities_detected": ents,
        "external_source_uris": uris,
        "engine_self_sources": engine_self,
        "entity_check_applied": applied,
        "reason": reason,
        "rule": (
            "Claims about real named entities may be labelled externally "
            "verified only with an external source URI. Engine output is not "
            "a source for named-entity claims."
        ),
        "schema": SOURCE_CLASS_SCHEMA,
    }


# ---------------------------------------------------------------------------
# AXIS 2 — EXPLANATORY CLASS (claim_kernel, 2026-09-19)
#
# A named-entity claim bound for publication must also declare an
# action-eligible claim_class: MEASURED / MECHANISM / PATTERN. A NARRATIVE
# claim may be true, valuable and worth reading and still carry zero
# explanatory power; an UNDECLARED class fails closed.
# ---------------------------------------------------------------------------
EXPLANATORY_SCHEMA = "claim_gate/explanatory_class/v1"
EXPLANATORY_VERDICTS = (
    "CLAIM_CLASS_NOT_DECLARED",
    "EXPLANATORY_CLASS_ACTION_ELIGIBLE",
    "EXPLANATORY_CLASS_NOT_ACTION_ELIGIBLE",
    "EXPLANATORY_CLASS_MISMATCH",
    "EXPLANATORY_CLASS_GATE_ERROR",
)
CLAIM_CLASSES = ("MEASURED", "MECHANISM", "PATTERN", "NARRATIVE", "UNCLASSIFIED")
ACTION_ELIGIBLE_CLASSES = ("MEASURED", "MECHANISM", "PATTERN")

# claim_kernel is the authority for axis 2. It is reached by import; if it is
# not already on sys.path its parent directory is appended once (the module's
# own documented install instruction). Unreachable kernel does NOT open the
# gate: the membership rule is still enforced locally, and `degraded` says so.
CLAIM_KERNEL_PATH = os.environ.get("CLAIM_KERNEL_PATH", "/root/AAA/lib")
_CLAIM_KERNEL_CACHE: dict = {"loaded": False, "module": None}


def _claim_kernel():
    """Import claim_kernel if reachable; None if not. Never raises."""
    if _CLAIM_KERNEL_CACHE["loaded"]:
        return _CLAIM_KERNEL_CACHE["module"]
    module = None
    try:
        import claim_kernel as module  # type: ignore  # noqa: F401
    except Exception:  # noqa: BLE001
        module = None
        try:
            if CLAIM_KERNEL_PATH not in sys.path:
                sys.path.append(CLAIM_KERNEL_PATH)
            import claim_kernel as module  # type: ignore  # noqa: F401,F811
        except Exception:  # noqa: BLE001
            module = None
    _CLAIM_KERNEL_CACHE["loaded"] = True
    _CLAIM_KERNEL_CACHE["module"] = module
    return module


def evaluate_claim_class(claim_text: str, claim_class: Optional[str] = None) -> dict:
    """Axis 2: may this claim be published on explanatory-class grounds?

    Delegates to claim_kernel.action_eligible(), then reports one of
    EXPLANATORY_VERDICTS. Fail-closed in every branch that is not a declared,
    action-eligible, self-consistent class.
    """
    declared = str(claim_class or "").strip().upper()
    result = {
        "schema": EXPLANATORY_SCHEMA,
        "declared": declared if declared else "UNCLASSIFIED",
        "kernel": "not_consulted",
        "kernel_schema": "",
        "inferred": "",
        "agree": False,
        "action_eligible": False,
        "verdict": "CLAIM_CLASS_NOT_DECLARED",
        "reasons": [],
        "note": "",
        "degraded": False,
    }

    if not declared or declared not in CLAIM_CLASSES:
        result["reasons"] = ["class=UNCLASSIFIED is not action-eligible"]
        result["note"] = (
            "No action-eligible claim_class declared"
            + (f" ({declared!r} is not a known class)" if declared else "")
            + ". Undeclared fails closed: not publishable on the explanatory axis."
        )
        return result

    kernel = _claim_kernel()
    if kernel is None:
        eligible = declared in ACTION_ELIGIBLE_CLASSES
        result.update(
            {
                "kernel": "local-fallback",
                "action_eligible": eligible,
                "degraded": True,
                "verdict": (
                    "EXPLANATORY_CLASS_ACTION_ELIGIBLE"
                    if eligible
                    else "EXPLANATORY_CLASS_NOT_ACTION_ELIGIBLE"
                ),
                "reasons": (
                    [] if eligible else [f"class={declared} is not action-eligible"]
                ),
                "note": (
                    f"claim_kernel unreachable at {CLAIM_KERNEL_PATH}; membership "
                    "rule enforced locally, mismatch lint skipped."
                ),
            }
        )
        return result

    try:
        verdict_dict = kernel.action_eligible(claim_text, declared)
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "kernel": "claim_kernel",
                "kernel_schema": str(getattr(kernel, "SCHEMA", "")),
                "verdict": "EXPLANATORY_CLASS_GATE_ERROR",
                "reasons": [f"claim_kernel raised: {str(exc)[:120]}"],
                "note": "Explanatory-class check errored; fail-closed.",
            }
        )
        return result

    class_verdict = verdict_dict.get("class_verdict") or {}
    eligible = bool(verdict_dict.get("eligible"))
    if eligible:
        verdict = "EXPLANATORY_CLASS_ACTION_ELIGIBLE"
    elif declared == "NARRATIVE":
        verdict = "EXPLANATORY_CLASS_NOT_ACTION_ELIGIBLE"
    elif class_verdict.get("agree") is False:
        verdict = "EXPLANATORY_CLASS_MISMATCH"
    else:
        verdict = "EXPLANATORY_CLASS_NOT_ACTION_ELIGIBLE"

    result.update(
        {
            "kernel": "claim_kernel",
            "kernel_schema": str(verdict_dict.get("schema", "")),
            "inferred": str(class_verdict.get("inferred", "")),
            "agree": bool(class_verdict.get("agree", False)),
            "action_eligible": eligible,
            "verdict": verdict,
            "reasons": [str(r) for r in (verdict_dict.get("reasons") or [])],
            "note": str(class_verdict.get("note", "")),
        }
    )
    return result


def evaluate(
    text: str,
    source_attribution: Optional[Iterable] = None,
    tool_name: str = "",
    claim_class: Optional[str] = None,
) -> dict:
    """Evaluate named-entity claim binding for a block of output text.

    Axis 1 (source class) keeps the legacy keys `state` and
    `publication_eligibility` with exactly their previous values.
    Axis 2 (explanatory class) is reported additively in
    `explanatory_class_gate`, `publication_decision` and `publishable`.
    """
    src = source_class_ok(source_attribution, entities=detect_named_entities(text))
    entities = src["entities_detected"]
    uris = src["external_source_uris"]

    if src["verdict"] == "NO_NAMED_ENTITIES":
        state = "NO_NAMED_ENTITIES"
        eligibility = "NOT_APPLICABLE"
    elif src["ok"]:
        state = "EVIDENCE_BOUND"
        eligibility = "ELIGIBLE_PENDING_CONTRADICTION_CHECK"
    else:
        state = "UNBOUND_EXTERNAL_EVIDENCE"
        eligibility = "BLOCKED_AS_EXTERNALLY_VERIFIED"

    explanatory = evaluate_claim_class(text, claim_class)

    if state == "NO_NAMED_ENTITIES":
        decision = "NOT_APPLICABLE"
    elif state != "EVIDENCE_BOUND":
        decision = "BLOCKED_AS_EXTERNALLY_VERIFIED"
    elif explanatory["action_eligible"]:
        decision = "PUBLISHABLE"
    elif explanatory["verdict"] == "CLAIM_CLASS_NOT_DECLARED":
        decision = "BLOCKED_CLAIM_CLASS_UNDECLARED"
    else:
        decision = "BLOCKED_CLAIM_CLASS"

    return {
        "gate": "named_entity_claim_gate",
        "tool": tool_name,
        "entities_detected": entities,
        "external_source_uris": uris,
        "state": state,
        "publication_eligibility": eligibility,
        "rule": (
            "Claims about real named institutions may be published as "
            "externally verified only with an external source URI. Engine "
            "output is not a source for named-entity claims."
        ),
        "origin": "0-independent-NEDs public-page incident, 2026-09-16",
        # --- additive, 2026-09-19 -------------------------------------------
        "source_class": {
            "verdict": src["verdict"],
            "ok": src["ok"],
            "engine_self_sources": src["engine_self_sources"],
            "reason": src["reason"],
            "schema": src["schema"],
        },
        "explanatory_class_gate": explanatory,
        "publication_decision": decision,
        "publishable": decision in ("PUBLISHABLE", "NOT_APPLICABLE"),
        "publication_rule": (
            "A named-entity claim may be published only with BOTH an external "
            "source URI and a declared action-eligible claim_class (MEASURED / "
            "MECHANISM / PATTERN). NARRATIVE and undeclared classes are not "
            "publishable here."
        ),
    }


def evaluate_dict_result(
    result,
    source_attribution: Optional[Iterable] = None,
    tool_name: str = "",
    claim_class: Optional[str] = None,
) -> dict:
    """Convenience: evaluate a result dict; gate errors fail closed
    (treat-as-unbound), computation itself is never blocked."""
    try:
        return evaluate(
            json.dumps(result, default=str), source_attribution, tool_name, claim_class
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "gate": "named_entity_claim_gate",
            "tool": tool_name,
            "state": "GATE_ERROR",
            "error": str(exc)[:160],
            "publication_eligibility": "UNKNOWN_TREAT_AS_UNBOUND",
            "origin": "0-independent-NEDs public-page incident, 2026-09-16",
            "publication_decision": "BLOCKED_GATE_ERROR",
            "publishable": False,
            "explanatory_class_gate": {
                "schema": EXPLANATORY_SCHEMA,
                "declared": str(claim_class or "UNCLASSIFIED").strip().upper(),
                "action_eligible": False,
                "verdict": "EXPLANATORY_CLASS_GATE_ERROR",
                "note": "Gate failed before the explanatory axis could be read.",
            },
            "reasons": ["gate error; treat-as-unbound (fail-closed)"],
        }
