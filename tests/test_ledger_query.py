"""P1 capital_ledger query reconciliation tests (WEALTH-RECONCILIATION-20260916).

Invariant: the ledger queries the file the writer writes. Absence is only
reportable after a scan of that file — never from a store mismatch. Sealed
IDs inside `arguments` must be findable (the AMEND-2026-08-03-001 defect).
"""

from __future__ import annotations

import json

import pytest

from wealth_mcp.server import create_mcp_server


def _tool_fn(name: str):
    mcp = create_mcp_server()
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


@pytest.fixture
def receipts_file(tmp_path, monkeypatch):
    records = [
        {
            "receipt_id": "r1",
            "timestamp_utc": "2026-09-16T01:00:00+00:00",
            "actor_id": "tester",
            "tool_name": "capital_diagnose",
            "arguments": {"mode": "petronas_vitals", "org": "PETRONAS"},
            "call_status": "PASS",
        },
        {
            "receipt_id": "r2",
            "timestamp_utc": "2026-09-16T02:00:00+00:00",
            "actor_id": "FI-003",
            "tool_name": "capital_entropy",
            "arguments": {"note": "AMEND-2026-08-03-001 dividend cap 60%"},
            "call_status": "ERROR",
        },
        {
            "receipt_id": "r3",
            "timestamp_utc": "2026-09-16T03:00:00+00:00",
            "actor_id": "geox-bridge",
            "tool_name": "capital_primitive",
            "arguments": {"mode": "npv"},
            "call_status": "PASS",
        },
    ]
    p = tmp_path / "receipts.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    monkeypatch.setenv("WEALTH_RECEIPTS_PATH", str(p))
    return p


@pytest.mark.asyncio
async def test_query_finds_sealed_id_inside_arguments(receipts_file):
    fn = _tool_fn("capital_ledger")
    env = await fn(mode="query", query="AMEND-2026-08-03-001", session_id="t")
    r = env["result"]
    assert r["status"] == "OK"
    assert r["matched"] == 1
    assert r["records"][0]["receipt_id"] == "r2"
    assert r["scanned"] == 3
    assert "receipts.jsonl" in r["source_path"]


@pytest.mark.asyncio
async def test_query_case_insensitive_full_text(receipts_file):
    fn = _tool_fn("capital_ledger")
    env = await fn(mode="query", query="petronas", session_id="t")
    r = env["result"]
    assert r["matched"] == 1
    assert r["records"][0]["receipt_id"] == "r1"


@pytest.mark.asyncio
async def test_query_empty_browses_newest_first(receipts_file):
    fn = _tool_fn("capital_ledger")
    env = await fn(mode="query", session_id="t")
    r = env["result"]
    assert r["matched"] == 3
    assert r["records"][0]["receipt_id"] == "r3"  # newest first


@pytest.mark.asyncio
async def test_query_absence_is_witnessed_not_assumed(receipts_file):
    fn = _tool_fn("capital_ledger")
    env = await fn(mode="query", query="definitely-not-present", session_id="t")
    r = env["result"]
    assert r["status"] == "OK"
    assert r["matched"] == 0
    assert "witnessed absence" in r["absence_note"]
    assert r["scanned"] == 3


@pytest.mark.asyncio
async def test_query_missing_file_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "WEALTH_RECEIPTS_PATH", str(tmp_path / "does-not-exist.jsonl")
    )
    fn = _tool_fn("capital_ledger")
    env = await fn(mode="query", query="anything", session_id="t")
    r = env["result"]
    assert r["status"] == "UNAVAILABLE"
    assert r["error_code"] == "RECEIPTS_FILE_ABSENT"
