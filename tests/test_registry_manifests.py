"""P1 five-manifest registry tests (WEALTH-RECONCILIATION-20260916).

Constitutional invariant: declared ≠ runtime. The registry must name each
view's scope, honor tool_name, and disclose — never blend — count drift.
"""

from __future__ import annotations

import pytest

from wealth_mcp.server import create_mcp_server


def _tool_fn(name: str):
    mcp = create_mcp_server()
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


@pytest.mark.asyncio
async def test_manifests_exposes_five_named_views():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="manifests", session_id="t-manifests")
    r = env["result"]
    assert r["status"] == "OK"
    views = r["manifests"]
    assert set(views.keys()) == {"source", "build", "runtime", "public", "probe"}
    assert views["source"]["scope"] and views["public"]["scope"]
    assert views["runtime"]["witness_state"] == "WITNESSED"
    assert views["runtime"]["tools"]  # server mounts its own tools
    assert r["count_reconciliation"]["source"] >= 1
    assert r["count_reconciliation"]["runtime"] >= 1


@pytest.mark.asyncio
async def test_manifests_per_tool_states_and_registry_self():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="manifests", session_id="t-manifests")
    per_tool = {e["tool"]: e for e in env["result"]["per_tool"]}
    assert "capital_registry" in per_tool
    assert per_tool["capital_registry"]["state"] == "LIVE"
    assert per_tool["capital_registry"]["mounted"] is True
    for entry in per_tool.values():
        assert entry["state"] in {
            "LIVE",
            "IMPORT_FAILED",
            "NOT_REGISTERED",
            "MOUNTED_UNDECLARED",
            "RUNTIME_ONLY",
        }


@pytest.mark.asyncio
async def test_manifests_honors_tool_name_filter():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="manifests", tool_name="capital_backtest", session_id="t")
    r = env["result"]
    assert r["tool"] == "capital_backtest"
    assert "views" in r and "state" in r


@pytest.mark.asyncio
async def test_manifests_unknown_tool_fails_closed():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="manifests", tool_name="capital_wisdom", session_id="t")
    r = env["result"]
    assert r["status"] == "ERROR"
    assert r["error_code"] == "UNKNOWN_TOOL"
    # ghost check: deleted capital_wisdom must not be known in any manifest
    assert "capital_wisdom" not in r["known_tools"]


@pytest.mark.asyncio
async def test_schema_mode_discloses_partial_scope():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="schema", session_id="t")
    r = env["result"]
    assert "partial mode-map" in r["scope"]
    assert r["schema_map_count"] == len(r["tools"])
    assert r["schema_map_count"] < r["public_tool_count"] or r[
        "schema_map_count"
    ] == r["public_tool_count"]


@pytest.mark.asyncio
async def test_schema_mode_honors_tool_name():
    fn = _tool_fn("capital_registry")
    env = await fn(mode="schema", tool_name="capital_market", session_id="t")
    r = env["result"]
    assert set(r["tools"].keys()) == {"capital_market"}
