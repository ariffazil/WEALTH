"""RASA spine tests — U1 (envelope), U6 (authority chain), U5 (output shape).

WEALTH side of the D1 → U1 → U6 epistemic trust spine (2026-09-16).
Gate source: /root/.hermes/policy (F13-ratified, D1-unified).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wealth_mcp.tools import rasa_bridge  # noqa: E402


def test_u1_narrative_downgrade_without_envelope():
    out = rasa_bridge.assess_claim_envelope({"note": "CEO sounds desperate"})
    assert out["storage_class"] == "UNSTRUCTURED_NARRATIVE"
    assert out["verdict"] == "UNSTRUCTURED_NARRATIVE"


def test_u1_quarantine_on_interior_promotion():
    out = rasa_bridge.assess_claim_envelope(
        {
            "claim_id": "test-interior-001",
            "proposition": "He is secretly anxious about the merger.",
            "source_layer": "PSYCHOLOGICAL",
            "target_layer": "PHENOMENOLOGICAL",
            "evidence_mode": "MODEL_INFERENCE",
            "epistemic_status": "INFERRED",
            "provenance_class": "I",
            "confidence": 0.8,
        }
    )
    assert out["storage_class"] == "QUARANTINE"
    assert out["verdict"] == "888_HOLD"
    assert "INTERIOR_STATE" in out["reason"] or "BRIDGE" in out["reason"]


def test_u1_clean_observation_passes():
    out = rasa_bridge.assess_claim_envelope(
        {
            "provenance_class": "O",
            "proposition": "The company paid RM400 for three meals during the audit.",
        }
    )
    assert out["storage_class"] == "CANONICAL_ELIGIBLE", out


def test_u6_laundering_chain_blocked():
    # Agent A infers -> Agent B "confirms" by rephrasing -> Agent C stores as observed.
    chain = [
        {"provenance_class": "I", "evidence_refs": ["analyst-note-7"]},
        {"provenance_class": "I", "evidence_refs": ["analyst-note-7"]},
        {"provenance_class": "O", "evidence_refs": ["analyst-note-7"]},
    ]
    violations = rasa_bridge.validate_authority_chain(chain)
    assert violations, "I→O on inherited evidence must be blocked"
    assert "link 2" in violations[0]
    assert "rephrasing" in violations[0]


def test_u6_no_evidence_blocked():
    chain = [
        {"provenance_class": "I", "evidence_refs": ["e1"]},
        {"provenance_class": "O", "evidence_refs": []},
    ]
    violations = rasa_bridge.validate_authority_chain(chain)
    assert violations and "NO evidence" in violations[0]


def test_u6_new_evidence_permits_promotion():
    chain = [
        {"provenance_class": "I", "evidence_refs": ["analyst-note-7"]},
        {
            "provenance_class": "O",
            "evidence_refs": ["analyst-note-7", "8k-filing-2026-q3"],
        },
    ]
    assert rasa_bridge.validate_authority_chain(chain) == []


def test_u6_flat_chain_ignored():
    chain = [
        {"provenance_class": "O", "evidence_refs": ["e1"]},
        {"provenance_class": "O", "evidence_refs": ["e1"]},
    ]
    assert rasa_bridge.validate_authority_chain(chain) == []


def test_u5_output_shape_never_attributs_motive():
    block = rasa_bridge.declared_revealed_block(
        declared_purpose="shareholder returns",
        gaming_signals=["prestige-acquisition-pattern"],
    )
    assert block["motive_attribution"] == "UNRESOLVED"
    assert "behavior is not motive" in block["law"]
