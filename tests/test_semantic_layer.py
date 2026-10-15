"""
WEALTH Semantic Concept Layer — golden + resolution + gate tests
================================================================

Mission wealth-mcp-semantic (2026-10-15). Covers:
1. Golden arithmetic for capital_breakeven both anchors (hand-checked).
2. Resolution + verification-flag logic for capital_read (fixture sources,
   monkeypatched paths — hermetic, no live feeds, no real vault writes).
3. Evidence-gate withholding (broken locator / UNVERIFIED source → WITHHELD
   with input_requests, NO numbers — MRTR spirit).
4. Scoped-token enforcement on the 3 NEW tools only.
5. Receipt-truth: _meta.arifOS.ledger_pointer references a REAL receipt line.

Run: PYTHONPATH=. .venv/bin/pytest tests/test_semantic_layer.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastmcp import Client, FastMCP

from wealth_mcp import semantic


# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture()
def semantic_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Hermetic semantic env: fixture ontology + sources + isolated stores."""
    src = tmp_path / "src.json"
    src.write_text(
        json.dumps(
            {
                "schema": "test.src.v1",
                "value_field": 42.5,
                "verification": "VERIFIED_SINGLE",
                "as_of": "2026-10-15",
            }
        )
    )
    old_src = tmp_path / "old.json"
    old_src.write_text(
        json.dumps(
            {
                "schema": "test.old.v1",
                "value_field": 1.0,
                "as_of": "2020-01-01",
                "last_updated": "2020-01-01",
            }
        )
    )
    unver = tmp_path / "unver.json"
    unver.write_text(
        json.dumps({"schema": "test.unver.v1", "value_field": 7.0, "verification": "UNVERIFIED"})
    )
    missing = tmp_path / "missing.json"  # deliberately absent → broken locator

    onto = {
        "schema": "test.onto.v1",
        "concepts": [
            {
                "id": "test.live",
                "title": "fixture live",
                "unit": "u",
                "entity_default": "E",
                "description": "fixture",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(src),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.9,
                        "freshness": "daily",
                        "verification_policy": "inherit source verification field",
                    }
                ],
            },
            {
                "id": "test.stale",
                "title": "fixture stale",
                "unit": "u",
                "entity_default": "E",
                "description": "fixture",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(old_src),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.9,
                        "freshness": "daily",
                        "verification_policy": "inherit + stale_30d",
                    }
                ],
            },
            {
                "id": "test.unverified",
                "title": "fixture unverified",
                "unit": "u",
                "entity_default": "E",
                "description": "fixture",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(unver),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.9,
                        "freshness": "daily",
                        "verification_policy": "inherit source verification field",
                    }
                ],
            },
            {
                "id": "test.broken",
                "title": "fixture broken locator",
                "unit": "u",
                "entity_default": "E",
                "description": "fixture",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(missing),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.9,
                        "freshness": "daily",
                        "verification_policy": "inherit source verification field",
                    }
                ],
            },
            {
                "id": "test.fallthrough",
                "title": "fixture fallthrough",
                "unit": "u",
                "entity_default": "E",
                "description": "best binding broken, second healthy",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(missing),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.95,
                        "freshness": "daily",
                        "verification_policy": "inherit",
                    },
                    {
                        "source_kind": "static_json",
                        "locator": str(src),
                        "jsonpath_or_field": "value_field",
                        "quality": 0.8,
                        "freshness": "daily",
                        "verification_policy": "inherit",
                    },
                ],
            },
            {
                "id": "test.scaled",
                "title": "fixture scaled (RM m → RM b)",
                "unit": "RM b",
                "entity_default": "E",
                "description": "fixture",
                "refresh": "daily",
                "bindings": [
                    {
                        "source_kind": "static_json",
                        "locator": str(src),
                        "jsonpath_or_field": "value_field",
                        "scale": 0.001,
                        "quality": 0.9,
                        "freshness": "daily",
                        "verification_policy": "inherit",
                    }
                ],
            },
        ],
    }
    onto_path = tmp_path / "concepts_ontology.json"
    onto_path.write_text(json.dumps(onto))

    tokens = {
        "tokens": {
            "tok_read": {"label": "t-read", "scopes": ["wealth:read"]},
            "tok_compute": {"label": "t-compute", "scopes": ["wealth:compute"]},
            "tok_admin": {"label": "t-admin", "scopes": ["wealth:admin"]},
        }
    }
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(json.dumps(tokens))

    monkeypatch.setattr(semantic, "ONTOLOGY_PATH", onto_path)
    monkeypatch.setattr(semantic, "_ontology_cache", {"mtime": None, "data": None})
    monkeypatch.setattr(semantic, "TOKENS_PATH", tokens_path)
    monkeypatch.setattr(semantic, "_TOKEN_CACHE", {"mtime": None, "data": {}})
    monkeypatch.setattr(semantic, "INVOCATION_LOG_PATH", tmp_path / "invocations.jsonl")
    monkeypatch.setattr(semantic, "_receipts_path", lambda: tmp_path / "receipts.jsonl")
    return tmp_path


def _server() -> FastMCP:
    mcp = FastMCP("semantic-test")
    semantic.register_semantic_tools(mcp)
    return mcp


async def _call(tool: str, args: dict) -> dict:
    async with Client(_server()) as client:
        res = await client.call_tool(tool, args)
    data = getattr(res, "data", None)
    if isinstance(data, dict):
        return data
    return json.loads(res.content[0].text)


# ── 1. Golden arithmetic (hand-checked) ────────────────────────────────────
class TestGoldenBreakevenMath:
    def test_budget_balance_midpoint(self):
        # spot=100, deficit=3.8, GDP=RM1900B, sens=3.5
        # headroom = (5 − 3.8)/100 × 1900 = 22.8 RM B
        # allowance = 22.8/3.5 × 10 = 65.142857…
        # breakeven = 100 − 65.142857 = 34.8571 (range: sens 3.0 → 24.0; 4.0 → 43.0)
        m = semantic.compute_budget_balance_breakeven(100.0, 3.8, 1900.0)
        assert m["deficit_headroom_rm_b"] == pytest.approx(22.8)
        assert m["breakeven_brent"] == pytest.approx(34.8571, abs=1e-3)
        assert m["breakeven_brent_range_low"] == pytest.approx(24.0)
        assert m["breakeven_brent_range_high"] == pytest.approx(43.0)
        assert m["sensitivity_rm_b_per_10usd"] == 3.5
        assert m["sensitivity_range"] == [3.0, 4.0]

    def test_budget_balance_alt_anchor_inputs(self):
        # spot=85, deficit=4.0, GDP=RM2000B → headroom 20; allowance 57.142857;
        # breakeven 27.8571; range 18.3333–35.0
        m = semantic.compute_budget_balance_breakeven(85.0, 4.0, 2000.0)
        assert m["deficit_headroom_rm_b"] == pytest.approx(20.0)
        assert m["breakeven_brent"] == pytest.approx(27.8571, abs=1e-3)
        assert m["breakeven_brent_range_low"] == pytest.approx(18.3333, abs=1e-3)
        assert m["breakeven_brent_range_high"] == pytest.approx(35.0)

    def test_budget_balance_at_trip_is_flat(self):
        # deficit at the 5% trip → zero headroom → breakeven == spot
        m = semantic.compute_budget_balance_breakeven(90.0, 5.0, 1900.0)
        assert m["deficit_headroom_rm_b"] == 0.0
        assert m["breakeven_brent"] == pytest.approx(90.0)

    def test_dividend_floor_anchor_is_sealed_6734(self):
        # The live sealed SOT (stable, owner-editable only) must carry 67.34.
        import importlib

        importlib.reload(semantic)
        res = semantic.resolve_concept("commodity.brent.dividend_floor")
        assert res["status"] == "resolved"
        obs = res["observation"]
        assert obs["value"] == pytest.approx(67.34)
        assert obs["verification"] in ("VERIFIED_SINGLE", "VERIFIED_LIVE")


# ── 2. Resolution + verification flags ────────────────────────────────────
class TestResolution:
    async def test_resolved_verifies_inline(self, semantic_env):
        obs = semantic.resolve_concept("test.live")["observation"]
        assert obs["value"] == 42.5
        assert obs["verification"] == "VERIFIED_SINGLE"
        assert obs["source"].endswith("src.json")

    async def test_stale_drift_over_30d(self, semantic_env):
        obs = semantic.resolve_concept("test.stale")["observation"]
        assert obs["verification"] == "STALE"
        assert obs["value"] == 1.0  # STALE still observes; gate keeps it passed

    async def test_scale_transform(self, semantic_env):
        obs = semantic.resolve_concept("test.scaled")["observation"]
        assert obs["value"] == pytest.approx(0.0425)
        assert "formula_note" in obs

    async def test_fallthrough_to_next_binding(self, semantic_env):
        res = semantic.resolve_concept("test.fallthrough")
        assert res["status"] == "resolved"
        assert res["observation"]["source"].endswith("src.json")

    async def test_rank_bindings_order(self, semantic_env):
        concept = semantic.get_concept("test.fallthrough")
        ranked = semantic.rank_bindings(concept)
        assert ranked[0]["rank"] == 1
        assert ranked[0]["quality"] == 0.95  # best first despite broken locator
        scores = [b["_rank_score"] for b in ranked]
        assert scores == sorted(scores, reverse=True)


# ── 3. Evidence gate: withheld + input_requests, NO numbers ───────────────
class TestEvidenceGate:
    async def test_broken_locator_withholds(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "test.broken", "token": "tok_read"})
        assert d["result"]["status"] == "WITHHELD"
        assert d["result"]["numbers"] is None
        assert d["result"]["input_requests"], "must ask for the missing input"
        assert "value" not in d["result"]
        assert d["_meta"]["arifOS"]["evidence_gate"] == "failed"
        assert d["_meta"]["arifOS"]["ledger_pointer"].startswith("/")

    async def test_unverified_source_withholds(self, semantic_env):
        d = await _call(
            "capital_read", {"concept_id": "test.unverified", "token": "tok_read"}
        )
        assert d["result"]["status"] == "WITHHELD"
        assert "UNVERIFIED" in " ".join(d["result"]["errors"])
        assert "value" not in d["result"]

    async def test_unknown_concept_withholds_with_known_ids(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "nope.nope", "token": "tok_read"})
        assert d["result"]["status"] == "WITHHELD"
        assert any("test.live" in r["why"] for r in d["result"]["input_requests"])

    async def test_resolved_passes_gate_and_carries_flag(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "test.live", "token": "tok_read"})
        obs = d["result"]
        assert obs["concept_id"] == "test.live"
        assert obs["value"] == 42.5
        assert obs["verification"] == "VERIFIED_SINGLE"
        assert d["_meta"]["arifOS"]["evidence_gate"] == "passed"
        assert d["_meta"]["arifOS"]["arifOS_fidelity"] == "F1-F13"
        assert d["_meta"]["arifOS"]["reversibility"] == "reversible"


# ── 4. Scoped tokens ──────────────────────────────────────────────────────
class TestTokenGate:
    async def test_missing_token_refused(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "test.live"})
        assert d["result"]["status"] == "REFUSED"
        assert "value" not in d["result"]

    async def test_invalid_token_refused(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "test.live", "token": "wrong"})
        assert d["result"]["status"] == "REFUSED"

    async def test_read_token_cannot_compute(self, semantic_env):
        d = await _call(
            "capital_breakeven",
            {"market": "MY", "fiscal_anchor": "budget_balance", "token": "tok_read"},
        )
        assert d["result"]["status"] == "REFUSED"

    async def test_rank_sources_requires_token(self, semantic_env):
        d = await _call("capital_rank_sources", {"concept_id": "test.live", "token": "tok_read"})
        assert d["result"]["concept_id"] == "test.live"
        assert d["result"]["bindings"][0]["rank"] == 1
        assert "verification_policy" in d["result"]["bindings"][0]


# ── 5. capital_breakeven (tool-level, hermetic via resolve_concept stub) ──
def _stub_resolve(canned: dict):
    def _fake(concept_id: str):
        if concept_id in canned:
            return {"status": "resolved", "observation": canned[concept_id]}
        return {"status": "unresolved", "errors": [f"{concept_id}: unresolvable"], "attempts": []}

    return _fake


class TestBreakevenTool:
    async def test_budget_balance_golden_through_tool(self, semantic_env, monkeypatch):
        canned = {
            "commodity.brent.spot": {
                "value": 100.0, "verification": "VERIFIED_LIVE",
                "source": "engine", "observed_at": "2026-10-15T00:00:00Z",
            },
            "sovereign.fiscal_deficit_pct": {
                "value": 3.8, "verification": "VERIFIED_SINGLE",
                "source": "sovereign.json", "observed_at": "2026-10-15",
            },
            "sovereign.gdp_rm_t": {
                "value": 1.90, "verification": "VERIFIED_SINGLE",
                "source": "sovereign.json", "observed_at": "2026-10-15",
                "formula_note": "DERIVED: 1.2/0.631",
            },
        }
        monkeypatch.setattr(semantic, "resolve_concept", _stub_resolve(canned))
        d = await _call(
            "capital_breakeven",
            {"market": "MY", "fiscal_anchor": "budget_balance", "token": "tok_compute"},
        )
        r = d["result"]
        assert r["status"] == "OK"
        assert r["breakeven_brent"] == pytest.approx(34.8571, abs=1e-3)
        assert "deficit_headroom_rm_b" in r["formula"]
        assert r["breakeven_brent_range"] == [24.0, 43.0]
        assert r["components"]["spot_usd"]["verification"] == "VERIFIED_LIVE"
        assert r["components"]["sensitivity_rm_b_per_10usd"]["range"] == [3.0, 4.0]
        assert d["_meta"]["arifOS"]["evidence_gate"] == "passed"

    async def test_dividend_floor_returns_sealed_anchor(self, semantic_env, monkeypatch):
        canned = {
            "commodity.brent.spot": {
                "value": 106.45, "verification": "VERIFIED_LIVE",
                "source": "engine", "observed_at": "2026-10-15T00:00:00Z",
            },
            "sovereign.fiscal_deficit_pct": {
                "value": 3.8, "verification": "VERIFIED_SINGLE",
                "source": "sovereign.json", "observed_at": "2026-10-15",
            },
            "commodity.brent.dividend_floor": {
                "value": 67.34, "verification": "VERIFIED_SINGLE",
                "source": "floor.json", "observed_at": "2026-10-15",
            },
        }
        monkeypatch.setattr(semantic, "resolve_concept", _stub_resolve(canned))
        d = await _call(
            "capital_breakeven",
            {"market": "MY", "fiscal_anchor": "dividend_floor", "token": "tok_admin"},
        )
        r = d["result"]
        assert r["status"] == "OK"
        assert r["breakeven_brent"] == pytest.approx(67.34)
        assert "Overlay T-A" in r["formula"]
        assert r["anchor_provenance"]["verification"] == "VERIFIED_SINGLE"
        assert r["context"]["above_floor"] is True

    async def test_unverified_input_withholds_no_numbers(self, semantic_env, monkeypatch):
        canned = {
            "commodity.brent.spot": {
                "value": 100.0, "verification": "VERIFIED_LIVE",
                "source": "engine", "observed_at": "2026-10-15T00:00:00Z",
            },
            "sovereign.fiscal_deficit_pct": {
                "value": 3.8, "verification": "UNVERIFIED",
                "source": "nowhere", "observed_at": None,
            },
            "sovereign.gdp_rm_t": {
                "value": 1.90, "verification": "VERIFIED_SINGLE",
                "source": "sovereign.json", "observed_at": "2026-10-15",
            },
        }
        monkeypatch.setattr(semantic, "resolve_concept", _stub_resolve(canned))
        d = await _call(
            "capital_breakeven",
            {"market": "MY", "fiscal_anchor": "budget_balance", "token": "tok_compute"},
        )
        r = d["result"]
        assert r["status"] == "WITHHELD"
        assert "breakeven" not in r
        assert r["input_requests"]

    async def test_unknown_market_refused_without_numbers(self, semantic_env, monkeypatch):
        d = await _call(
            "capital_breakeven",
            {"market": "SG", "fiscal_anchor": "budget_balance", "token": "tok_compute"},
        )
        assert d["result"]["status"] == "WITHHELD"
        assert "breakeven" not in d["result"]


# ── 6. Receipt truth + invocation log ─────────────────────────────────────
class TestLedgerTruth:
    async def test_ledger_pointer_references_real_receipt(self, semantic_env):
        d = await _call("capital_read", {"concept_id": "test.live", "token": "tok_read"})
        pointer = d["_meta"]["arifOS"]["ledger_pointer"]
        assert "#" in pointer
        receipt_id = pointer.split("#", 1)[1]
        receipts_file = semantic_env / "receipts.jsonl"
        lines = [json.loads(x) for x in receipts_file.read_text().splitlines() if x.strip()]
        assert any(r["receipt_id"] == receipt_id for r in lines), pointer

    async def test_invocation_logged_without_token_value(self, semantic_env):
        await _call("capital_read", {"concept_id": "test.live", "token": "tok_read"})
        log_file = semantic_env / "invocations.jsonl"
        entry = json.loads(log_file.read_text().splitlines()[-1])
        assert entry["tool"] == "capital_read"
        assert entry["token_label"] == "t-read"
        assert "tok_read" not in json.dumps(entry)
