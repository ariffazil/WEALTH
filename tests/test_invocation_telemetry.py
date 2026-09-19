"""Tuas 2 — WEALTH MCP dispatch invocation telemetry.

Proves the single dispatch chokepoint (`mcp.call_tool` inside
`wealth_mcp.server.create_mcp_server`) receipts every dispatched tool call to
the shared federation telemetry contract (`/root/AAA/lib/invocation_log.py`),
and proves the three properties that matter:

  1. the real instrumented path writes a receipt (organ=WEALTH, tool=<name>);
  2. a forced telemetry failure does NOT break the tool call;
  3. the receipt carries the tool NAME and the caller id and nothing of the
     arguments — no financial payload ever reaches a metrics log.

Both sinks are redirected to `tmp_path`. The VAULT999 receipt sink is pointed
at a non-existent file on purpose: WEALTH's `_append_existing_jsonl` refuses to
create an unprovisioned target, so this test is structurally incapable of
writing into the ledger.

Run:
    PYTHONPATH=/root/WEALTH /usr/bin/python3 -m pytest \
        /root/WEALTH/tests/test_invocation_telemetry.py -q
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

ORGAN = "WEALTH"
OBSERVE_TOOL = "capital_registry"
# A tool that is NOT in WEALTH's OBSERVE-class set, so an unbound session is
# refused by the session gate — the receipt for it must read ok=False.
GATED_TOOL = "wealth_judge_handoff"
SESSION = "S-TUAS2-proof-0001"

# Exhaustive allow-list of keys the shared contract writes. Anything else in a
# receipt means something smuggled content into the metrics log.
CONTRACT_KEYS = {
    "ts",
    "organ",
    "tool",
    "actor_id",
    "ok",
    "duration_ms",
    "session_id",
    "epoch",
    "host",
    "extra",
    "error",
}


def _receipts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


@pytest.fixture()
def dispatch(tmp_path, monkeypatch):
    """Build the REAL WEALTH MCP server with every sink redirected to tmp_path."""
    inv_log = tmp_path / "tool_invocations.jsonl"
    monkeypatch.setenv("WEALTH_INVOCATION_LOG_PATH", str(inv_log))
    monkeypatch.setenv("WEALTH_RECEIPT_PATH", str(tmp_path / "receipts.jsonl"))

    import wealth_mcp.server as server

    mcp = server.create_mcp_server()
    assert mcp is not None
    return mcp, inv_log


# ── 1. the real path writes a real receipt ──────────────────────────────────


def test_mcp_dispatch_writes_invocation_receipt(dispatch):
    """A dispatched call through mcp.call_tool lands in the shared log."""
    mcp, inv_log = dispatch
    asyncio.run(mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION}))

    rows = _receipts(inv_log)
    assert rows, "mcp.call_tool is not instrumented: no invocation receipt written"
    assert {r["organ"] for r in rows} == {ORGAN}
    assert {r["tool"] for r in rows} == {OBSERVE_TOOL}
    for row in rows:
        assert isinstance(row["ts"], str) and row["ts"].endswith("Z")
        assert isinstance(row["epoch"], (int, float))
        assert isinstance(row["ok"], bool)
        assert isinstance(row["duration_ms"], (int, float))


def test_dispatch_chokepoint_is_the_instrumented_call_site(dispatch, monkeypatch):
    """The telemetry call site is on the dispatch path, not merely importable."""
    mcp, _inv_log = dispatch

    import wealth_mcp.server as server

    seen: list[tuple] = []
    monkeypatch.setattr(
        server,
        "_log_tool_invocation",
        lambda *a, **k: (seen.append((a, k)), True)[1],
    )
    asyncio.run(mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION}))

    assert seen, "mcp.call_tool is not wrapped by the Tuas-2 telemetry call site"
    assert seen[0][0][0] == OBSERVE_TOOL
    assert seen[0][1]["ok"] is True


def test_exercise_count_readback_sees_the_receipt(dispatch):
    """The readback that replaces the proxy denominator counts this call."""
    mcp, inv_log = dispatch
    asyncio.run(mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION}))

    from invocation_log import exercise_count

    got = exercise_count(ORGAN, window_days=30, path=inv_log)
    assert got["distinct_tools"] == 1
    assert got["total"] >= 1
    assert got["organs_seen"] == [ORGAN]
    assert got["unparsable"] == 0


def test_both_dispatch_passes_are_receipted_and_marked(dispatch):
    """Pin the 2x: FastMCP re-enters the patched attribute for its middleware.

    Both entries are written and the re-entry is flagged, so a reader summing
    `total` can discount it and a reader counting distinct tools is unaffected.
    """
    mcp, inv_log = dispatch
    asyncio.run(mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION}))

    rows = _receipts(inv_log)
    assert {r["tool"] for r in rows} == {OBSERVE_TOOL}
    assert {bool(r["extra"]["inner_pass"]) for r in rows} == {True, False}
    assert sum(1 for r in rows if not r["extra"]["inner_pass"]) == 1, (
        "expected exactly one client-visible (outer) receipt per dispatched call"
    )

    from invocation_log import exercise_count

    got = exercise_count(ORGAN, window_days=30, path=inv_log)
    assert got["distinct_tools"] == 1, "the 2x must not inflate distinct_tools"


# ── 2. caller identity ──────────────────────────────────────────────────────


def test_receipt_carries_self_reported_actor_id(dispatch):
    mcp, inv_log = dispatch
    asyncio.run(
        mcp.call_tool(
            OBSERVE_TOOL,
            {"mode": "status", "session_id": SESSION, "actor_id": "arif"},
        )
    )
    rows = _receipts(inv_log)
    assert rows
    assert {r["actor_id"] for r in rows} == {"arif"}


def test_absent_actor_id_is_logged_as_null_not_invented(dispatch):
    """No caller identity available => None, never a fabricated principal."""
    mcp, inv_log = dispatch
    asyncio.run(mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION}))
    rows = _receipts(inv_log)
    assert rows
    assert {r["actor_id"] for r in rows} == {None}


# ── 3. privacy boundary: name and id only ───────────────────────────────────


def test_receipt_never_carries_arguments_or_financial_payload(dispatch):
    """Financial arguments must not land in a metrics log."""
    mcp, inv_log = dispatch
    payload = {
        "mode": "status",
        "session_id": SESSION,
        "fee": 9876543.21,
        "tx_type": "pledged",
        "counterparty": "MARGIN_CALL_ACME",
    }
    try:
        asyncio.run(mcp.call_tool(OBSERVE_TOOL, payload))
    except BaseException:
        # A validation refusal is fine — the receipt is written either way.
        pass

    rows = _receipts(inv_log)
    assert rows, "no receipt written for the payload-bearing call"
    blob = inv_log.read_text(encoding="utf-8")
    for leaked in ("9876543.21", "fee", "tx_type", "pledged", "counterparty", "MARGIN_CALL_ACME"):
        assert leaked not in blob, f"payload token {leaked!r} leaked into the metrics log"
    for row in rows:
        assert set(row) <= CONTRACT_KEYS, f"unexpected receipt keys: {set(row) - CONTRACT_KEYS}"
        assert row["extra"] == {"inner_pass": False} or row["extra"] == {"inner_pass": True}


def test_blocked_call_receipts_as_not_ok(dispatch):
    """A gate-blocked call is a real invocation attempt, receipted ok=False."""
    mcp, inv_log = dispatch
    result = asyncio.run(mcp.call_tool(GATED_TOOL, {"mode": "prepare"}))
    assert getattr(result, "is_error", False) is True

    rows = [r for r in _receipts(inv_log) if r["tool"] == GATED_TOOL]
    assert rows, "blocked call was not receipted"
    assert all(r["ok"] is False for r in rows)


# ── 4. the instrument can never break the thing it measures ─────────────────


class _RaisingLogger:
    """Every call raises — the worst possible telemetry sink."""

    @staticmethod
    def log_invocation(*_args, **_kwargs):
        raise RuntimeError("telemetry sink exploded")


@pytest.mark.parametrize(
    "broken",
    [
        pytest.param("raises", id="logger-raises"),
        pytest.param("unavailable", id="logger-module-missing"),
        pytest.param("unwritable", id="logger-sink-unwritable"),
    ],
)
def test_forced_telemetry_failure_does_not_break_tool_call(
    dispatch, monkeypatch, tmp_path, broken
):
    mcp, inv_log = dispatch

    import wealth_mcp.server as server

    if broken == "raises":
        monkeypatch.setattr(server, "_load_invocation_log", lambda: _RaisingLogger())
    elif broken == "unavailable":
        monkeypatch.setattr(server, "_load_invocation_log", lambda: None)
    else:
        # A directory that cannot be created: the real logger swallows it and
        # returns False, so the call must still succeed.
        monkeypatch.setenv(
            "WEALTH_INVOCATION_LOG_PATH", str(tmp_path / "nope" / "x" / "inv.jsonl")
        )
        Path(tmp_path / "nope").write_text("not a directory", encoding="utf-8")

    result = asyncio.run(
        mcp.call_tool(OBSERVE_TOOL, {"mode": "status", "session_id": SESSION})
    )

    assert result is not None, "telemetry failure broke the tool call"
    assert getattr(result, "is_error", True) is False
    structured = getattr(result, "structured_content", None)
    assert isinstance(structured, dict) and structured.get("tool_name") == OBSERVE_TOOL


def test_raising_tool_still_returns_its_exception_and_receipts(monkeypatch, tmp_path):
    """The wrapper must not swallow or alter an exception from the tool path."""
    import wealth_mcp.server as server

    inv_log = tmp_path / "inv.jsonl"
    monkeypatch.setenv("WEALTH_INVOCATION_LOG_PATH", str(inv_log))

    async def exploding(_name, _arguments=None, **_kwargs):
        raise ValueError("tool blew up")

    wrapped = server._telemetry_wrapped(exploding)
    with pytest.raises(ValueError, match="tool blew up"):
        asyncio.run(wrapped(OBSERVE_TOOL, {"session_id": SESSION}))

    rows = _receipts(inv_log)
    assert rows and rows[0]["ok"] is False
    assert rows[0]["error"] == "ValueError"
    assert "tool blew up" not in inv_log.read_text(encoding="utf-8")


def test_log_helper_returns_false_and_never_raises(monkeypatch):
    """The helper's contract is a bool, never an exception."""
    import wealth_mcp.server as server

    monkeypatch.setattr(server, "_load_invocation_log", lambda: _RaisingLogger())
    assert server._log_tool_invocation(OBSERVE_TOOL, None, ok=True) is False
