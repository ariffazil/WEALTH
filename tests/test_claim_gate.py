"""P1 named-entity claim gate tests (WEALTH-RECONCILIATION-20260916).

Founding case: the false "zero independent NEDs" claim had no external
source and was computed from discarded input — this gate blocks that class
before publication. Engine output is never a source; persons are scored
as structures, not personalities.
"""

from __future__ import annotations

import pytest

from wealth_core.evidence.claim_gate import validate_claims
from wealth_mcp.server import create_mcp_server


def _tool_fn(name: str):
    mcp = create_mcp_server()
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


NOW = "2026-09-16T12:00:00+00:00"


def test_false_ned_claim_holds_without_external_source():
    """The exact claim class that reached the public page."""
    out = validate_claims(
        [
            {
                "claim_text": "PETRONAS board contains zero independent non-executive directors",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
                "truth_class_claimed": "OBSERVED",
            }
        ]
    )
    assert out["publication_gate"] == "BLOCKED"
    assert out["claims"][0]["verdict"] == "HOLD"
    assert "missing_citation" in out["claims"][0]["reasons"][0]


def test_corrected_ned_claim_passes_with_external_witness():
    out = validate_claims(
        [
            {
                "claim_text": "PETRONAS leaders page lists four Independent Non-Executive Directors",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
                "source_uri": "https://www.petronas.com/about-us/our-leaders",
                "retrieved_at": NOW,
                "contradiction_check": {
                    "status": "CHECKED",
                    "second_source_uri": "https://www.petronas.com/integrated-report-2023/",
                },
            }
        ]
    )
    assert out["publication_gate"] == "PASS"
    assert out["claims"][0]["verdict"] == "OBS_ELIGIBLE"


def test_engine_output_is_never_a_source():
    out = validate_claims(
        [
            {
                "claim_text": "Governance score 1.00/3",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
                "source_uri": "wealth://commodity/oil/snapshot",
                "retrieved_at": NOW,
                "contradiction_check": {"status": "CHECKED", "second_source_uri": "https://x.example/a"},
            }
        ]
    )
    assert out["claims"][0]["verdict"] == "HOLD"
    assert "self_sourced" in out["claims"][0]["reasons"][0]


def test_own_domain_page_is_not_external():
    out = validate_claims(
        [
            {
                "claim_text": "Extraction 70.5%",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
                "source_uri": "https://arif-fazil.com/vitals/",
                "retrieved_at": NOW,
                "contradiction_check": {"status": "CHECKED", "second_source_uri": "https://x.example/a"},
            }
        ]
    )
    assert out["claims"][0]["verdict"] == "HOLD"


def test_person_trait_claim_rejected_structures_not_people():
    out = validate_claims(
        [
            {
                "claim_text": "CEO X is reckless and incompetent",
                "about_entities": [{"name": "X", "type": "person"}],
                "category": "competence",
                "source_uri": "https://news.example/article",
                "retrieved_at": NOW,
                "contradiction_check": {"status": "CHECKED", "second_source_uri": "https://y.example/b"},
            }
        ]
    )
    assert out["claims"][0]["verdict"] == "REJECT"
    assert "structures" in out["claims"][0]["reasons"][0]


def test_stale_claim_holds_under_freshness_policy():
    out = validate_claims(
        [
            {
                "claim_text": "Brent at $100.60",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
                "source_uri": "https://tradingeconomics.com/commodity/brent-crude-oil",
                "retrieved_at": "2026-08-01T00:00:00+00:00",
                "freshness_days": 7,
                "contradiction_check": {"status": "CHECKED", "second_source_uri": "https://y.example/b"},
            }
        ]
    )
    assert out["claims"][0]["verdict"] == "HOLD"
    assert "stale" in out["claims"][0]["reasons"][0]


def test_unchecked_contradiction_holds():
    out = validate_claims(
        [
            {
                "claim_text": "Single-sourced claim",
                "about_entities": [{"name": "ORGA", "type": "organization"}],
                "source_uri": "https://a.example/x",
                "retrieved_at": NOW,
                "contradiction_check": {"status": "UNCHECKED"},
            }
        ]
    )
    assert out["claims"][0]["verdict"] == "HOLD"
    assert "contradiction_unchecked" in out["claims"][0]["reasons"][0]


def test_non_entity_claim_recorded_without_citation_requirement():
    out = validate_claims(
        [{"claim_text": "FCF = CFFO − capex − dividend", "about_entities": []}]
    )
    assert out["claims"][0]["verdict"] == "NON_ENTITY"
    assert out["publication_gate"] == "PASS"


@pytest.mark.asyncio
async def test_capital_claims_tool_live_registration():
    fn = _tool_fn("capital_claims")
    env = await fn(
        claims=[
            {
                "claim_text": "zero independent NEDs",
                "about_entities": [{"name": "PETRONAS", "type": "organization"}],
            }
        ],
        session_id="t",
    )
    r = env["result"]
    assert r["publication_gate"] == "BLOCKED"
    assert env["errors"]  # blocking reasons surfaced at envelope level


@pytest.mark.asyncio
async def test_capital_claims_tool_missing_claims_fails_closed():
    fn = _tool_fn("capital_claims")
    env = await fn(session_id="t")
    assert env["result"]["error_code"] == "MISSING_DATA"
