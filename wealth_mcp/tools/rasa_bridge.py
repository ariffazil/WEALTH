"""
WEALTH ↔ RASA epistemic bridge — U1/U5/U6 spine (2026-09-16).

U1  Claims entering WEALTH carry provenance (O/S/R/I/F/P/C). Unenveloped
    narrative downgrades to UNSTRUCTURED_NARRATIVE — never canonical.
U5  Declared ≠ Revealed divergence is mechanical; motive attribution stays
    UNRESOLVED. Behavior is not motive.
U6  Authority(C_{t+1}) > Authority(C_t) ⇒ ∃E_new ∧ E_new ≢ rephrasing(C_t).
    Inference-laundering chains (I→I→O, R→O) are blocked at the handoff.

Gate source: /root/.hermes/policy — F13-ratified RASA boundary + layer
registry (D1-unified). Fail-closed for canonical: when the gate cannot be
loaded, storage_class falls back to UNSTRUCTURED_NARRATIVE — narrative,
never silently canonical.

Four-law compression this enforces:
    Evidence has provenance · Claims have principals ·
    Inference does not create evidence · Observation does not confer authority.
"""

from __future__ import annotations

import os
import sys
from typing import Any

# Overridable for sandboxed services (wealth-organ binds the gate read-only
# at /opt/rasa-gate via systemd BindReadOnlyPaths — see rasa-gate.conf).
_RASA_POLICY_DIR = os.environ.get("RASA_POLICY_DIR", "/root/.hermes/policy")

_GATE: dict[str, Any] | None = None
_GATE_ERROR = ""


def _load_gate() -> dict[str, Any] | None:
    global _GATE, _GATE_ERROR
    if _GATE is not None or _GATE_ERROR:
        return _GATE
    try:
        if _RASA_POLICY_DIR not in sys.path:
            sys.path.insert(0, _RASA_POLICY_DIR)
        from rasa_boundary import AUTHORITY_RANK, PROVENANCE_CLASSES  # type: ignore
        from rasa_write_hook import guarded_human_claim, guarded_layer_claim  # type: ignore

        _GATE = {
            "AUTHORITY_RANK": AUTHORITY_RANK,
            "PROVENANCE_CLASSES": PROVENANCE_CLASSES,
            "guarded_human_claim": guarded_human_claim,
            "guarded_layer_claim": guarded_layer_claim,
        }
    except Exception as exc:  # pragma: no cover — fail-closed path
        _GATE_ERROR = repr(exc)
    return _GATE


def assess_claim_envelope(claim: Any, writer: str = "wealth") -> dict[str, Any]:
    """U1: provenance-gate a single claim dict. Never raises.

    Returns {verdict, storage_class, reason}.
    storage_class ∈ {CANONICAL_ELIGIBLE, UNSTRUCTURED_NARRATIVE, QUARANTINE}.
    """
    gate = _load_gate()
    if gate is None:
        return {
            "verdict": "UNKNOWN_GATE_DOWN",
            "storage_class": "UNSTRUCTURED_NARRATIVE",
            "reason": (
                f"RASA gate unavailable ({_GATE_ERROR}); fail-closed for "
                "canonical: treat as narrative."
            ),
        }
    if not isinstance(claim, dict) or not claim.get("provenance_class"):
        return {
            "verdict": "UNSTRUCTURED_NARRATIVE",
            "storage_class": "UNSTRUCTURED_NARRATIVE",
            "reason": "U1: no provenance_class envelope — narrative only.",
        }
    try:
        env = gate["guarded_human_claim"](dict(claim), writer=writer)
        # Claims carrying layer fields also face the Cross-Layer Promotion Law.
        if any(
            k in env
            for k in ("source_layer", "target_layer", "evidence_mode", "epistemic_status")
        ):
            env = gate["guarded_layer_claim"](env, writer=writer)
    except Exception as exc:
        msg = str(exc)
        hold_shaped = any(
            marker in msg
            for marker in (
                "888_HOLD",
                "CROSS_LAYER",
                "BRIDGE",
                "INTERIOR",
                "COAUTHORED",
                "SENSITIVE",
            )
        )
        return {
            "verdict": "888_HOLD" if hold_shaped else "REJECTED",
            "storage_class": "QUARANTINE",
            "reason": f"RASAViolation: {msg}",
        }
    return {"verdict": "PASS", "storage_class": "CANONICAL_ELIGIBLE"}


def validate_authority_chain(chain: Any) -> list[str]:
    """U6: block authority increases that are rephrasings, not new evidence.

    Each link: {provenance_class, evidence_refs?: [...]}.
    Law: Authority(C_{t+1}) > Authority(C_t) ⇒ ∃E_new ∧ E_new ⊄ E(C_t).
    Ten agents repeating one analyst's speculation must not produce ten
    units of evidence.
    """
    gate = _load_gate()
    if not isinstance(chain, list) or len(chain) < 2:
        return []
    if gate is None:
        return [
            "U6_UNVERIFIABLE: RASA gate unavailable "
            f"({_GATE_ERROR}) — chain cannot be certified; treat as unproven."
        ]
    rank = gate["AUTHORITY_RANK"]
    violations: list[str] = []
    prev = chain[0]
    for i, link in enumerate(chain[1:], start=1):
        if isinstance(prev, dict) and isinstance(link, dict):
            p_cls = str(prev.get("provenance_class", "")).strip()
            c_cls = str(link.get("provenance_class", "")).strip()
            if p_cls in rank and c_cls in rank and rank[c_cls] > rank[p_cls]:
                prev_refs = {str(r) for r in (prev.get("evidence_refs") or [])}
                curr_refs = {str(r) for r in (link.get("evidence_refs") or [])}
                if not curr_refs:
                    violations.append(
                        f"U6 VIOLATION (link {i}): authority {p_cls}->{c_cls} with "
                        "NO evidence — inference does not create evidence."
                    )
                elif not (curr_refs - prev_refs):
                    violations.append(
                        f"U6 VIOLATION (link {i}): authority {p_cls}->{c_cls} carries "
                        "only inherited evidence (rephrasing) — E_new ≢ rephrasing(C_t)."
                    )
        prev = link
    return violations


def declared_revealed_block(
    declared_purpose: str | None, gaming_signals: list | None = None
) -> dict[str, Any]:
    """U5: output-shape law for declared-vs-revealed divergence.

    The machine may flag divergence. It may not attribute motive.
    """
    return {
        "declared_purpose": declared_purpose or "",
        "divergence_signals": gaming_signals or [],
        "motive_attribution": "UNRESOLVED",
        "law": "Declared ≠ Revealed ⇏ HiddenMotive=X — behavior is not motive",
    }
