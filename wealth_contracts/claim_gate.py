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
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Optional

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


def evaluate(
    text: str,
    source_attribution: Optional[Iterable] = None,
    tool_name: str = "",
) -> dict:
    """Evaluate named-entity claim binding for a block of output text."""
    entities = detect_named_entities(text)
    uris = extract_external_uris(source_attribution)
    if not entities:
        state = "NO_NAMED_ENTITIES"
        eligibility = "NOT_APPLICABLE"
    elif uris:
        state = "EVIDENCE_BOUND"
        eligibility = "ELIGIBLE_PENDING_CONTRADICTION_CHECK"
    else:
        state = "UNBOUND_EXTERNAL_EVIDENCE"
        eligibility = "BLOCKED_AS_EXTERNALLY_VERIFIED"
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
    }


def evaluate_dict_result(
    result,
    source_attribution: Optional[Iterable] = None,
    tool_name: str = "",
) -> dict:
    """Convenience: evaluate a result dict; gate errors fail closed
    (treat-as-unbound), computation itself is never blocked."""
    try:
        return evaluate(json.dumps(result, default=str), source_attribution, tool_name)
    except Exception as exc:  # noqa: BLE001
        return {
            "gate": "named_entity_claim_gate",
            "tool": tool_name,
            "state": "GATE_ERROR",
            "error": str(exc)[:160],
            "publication_eligibility": "UNKNOWN_TREAT_AS_UNBOUND",
            "origin": "0-independent-NEDs public-page incident, 2026-09-16",
        }
