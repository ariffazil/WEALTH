"""
Tests for WEALTH MCP registry truth.

The declarations, internal FastMCP components, and discoverable tools/list
surface must describe the same callable tools. No phantom tools or ghost aliases.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_mcp import CAPITAL_TOOL_NAMES, PUBLIC_TOOL_NAMES, WEALTH_VERSION
from wealth_mcp.server import (
    _append_existing_jsonl,
    _tool_result_status,
    create_mcp_server,
)


EXPECTED_TOOLS = tuple(PUBLIC_TOOL_NAMES)


def _component_tool_names(mcp) -> tuple[str, ...]:
    """Return the internal FastMCP tool components in registration order."""
    return tuple(
        key.removeprefix("tool:").split("@", 1)[0]
        for key in mcp._local_provider._components
        if key.startswith("tool:")
    )


async def _live_tool_names(mcp) -> tuple[str, ...]:
    """Use tools/list as the public runtime contract."""
    return tuple(tool.name for tool in await mcp.list_tools())


class TestRegistryTruth:
    """All declared tools must be registered and publicly discoverable."""

    def test_server_creates(self):
        """Server must create without error."""
        mcp = create_mcp_server()
        assert mcp is not None

    @pytest.mark.asyncio
    async def test_expected_tool_count(self):
        """Counts come from declarations, never a stale numeric constant."""
        mcp = create_mcp_server()
        internal_names = _component_tool_names(mcp)
        live_names = await _live_tool_names(mcp)

        assert internal_names == EXPECTED_TOOLS
        assert live_names == EXPECTED_TOOLS
        assert tuple(CAPITAL_TOOL_NAMES) == EXPECTED_TOOLS
        assert len(live_names) == len(PUBLIC_TOOL_NAMES)

    @pytest.mark.asyncio
    async def test_no_phantom_tools(self):
        """Internal registration cannot hide tools behind list middleware."""
        mcp = create_mcp_server()
        internal_names = set(_component_tool_names(mcp))
        live_names = set(await _live_tool_names(mcp))
        declared_names = set(PUBLIC_TOOL_NAMES)

        assert internal_names == live_names == declared_names

    @pytest.mark.asyncio
    async def test_every_public_schema_can_carry_session_envelope(self):
        """Runtime auth must never require fields absent from discovery."""
        mcp = create_mcp_server()
        tools = await mcp.list_tools()
        for tool in tools:
            properties = tool.parameters.get("properties", {})
            assert "session_id" in properties, f"{tool.name} cannot carry session_id"
            assert "actor_id" in properties, f"{tool.name} cannot carry actor_id"


def _component_fn(mcp, name: str):
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


@pytest.mark.asyncio
async def test_capital_registry_reports_canonical_and_public_counts():
    registry = _component_fn(create_mcp_server(), "capital_registry")

    status = (await registry(mode="status"))["result"]
    schema = (await registry(mode="schema"))["result"]
    domains = (await registry(mode="domains"))["result"]
    health = (await registry(mode="health"))["result"]

    canonical_count = len(CAPITAL_TOOL_NAMES)
    public_count = len(PUBLIC_TOOL_NAMES)
    declared_names = set(PUBLIC_TOOL_NAMES)
    schema_names = set(schema["tools"])
    domain_names = {
        tool_name
        for domain in domains["domains"]
        for tool_name in domain["tools"]
    }

    assert status["canonical_tools"] == list(CAPITAL_TOOL_NAMES)
    assert status["canonical_tool_count"] == canonical_count
    assert status["public_tools"] == list(PUBLIC_TOOL_NAMES)
    assert status["public_tool_count"] == public_count
    assert schema["canonical_tool_count"] == canonical_count
    assert schema["public_tool_count"] == public_count
    assert schema_names == declared_names
    assert domains["canonical_tool_count"] == canonical_count
    assert domains["public_tool_count"] == public_count
    assert domain_names == declared_names
    assert health["canonical_tools"] == canonical_count
    assert health["public_tools"] == public_count
    assert {status["version"], schema["version"], domains["version"], health["version"]} == {
        WEALTH_VERSION
    }


@pytest.mark.asyncio
async def test_capital_ledger_hold_is_explicitly_blocked():
    ledger = _component_fn(create_mcp_server(), "capital_ledger")
    envelope = await ledger(mode="write", ack_irreversible=False)

    assert envelope["result"]["status"] == "HOLD"
    assert envelope["execution_authority"] == "BLOCKED"
    assert envelope["requires_888_hold"] is True


@pytest.mark.asyncio
async def test_capital_ledger_write_reports_only_observed_persistence(monkeypatch):
    from host.governance import vault_supabase

    def fake_append(record):
        return {
            **record,
            "integrity": "observed-integrity",
            "persistence": {"status": "APPENDED", "path": "/provisioned/ledger"},
        }

    monkeypatch.setattr(vault_supabase, "append_vault999", fake_append)
    ledger = _component_fn(create_mcp_server(), "capital_ledger")
    envelope = await ledger(
        mode="write",
        tx_type="test",
        amount=10,
        ack_irreversible=True,
        session_id="SEAL-ledger-test",
        actor_id="tester",
    )

    result = envelope["result"]
    assert result["status"] == "APPENDED"
    assert result["integrity"] == "observed-integrity"
    assert "vault_id" not in result
    assert "chain_hash" not in result
    assert envelope["evidence_quality"] == "OBSERVED"


@pytest.mark.asyncio
async def test_capital_entropy_missing_dependency_is_structured():
    entropy = _component_fn(create_mcp_server(), "capital_entropy")
    envelope = await entropy(mode="invalid_test_mode")

    assert envelope["tool_name"] == "capital_entropy"
    assert envelope["result"]["status"] == "ERROR"
    assert envelope["result"]["error_code"] == "UNKNOWN_MODE"


def test_receipt_append_never_creates_missing_target(tmp_path):
    target = tmp_path / "receipts.jsonl"
    state = _append_existing_jsonl(str(target), {"receipt_id": "r-1"})

    assert state["persisted"] is False
    assert not target.exists()

    target.write_text("", encoding="utf-8")
    state = _append_existing_jsonl(str(target), {"receipt_id": "r-2"})
    assert state["persisted"] is True
    assert '"receipt_id": "r-2"' in target.read_text(encoding="utf-8")


def test_vault_append_reports_missing_and_existing_targets(tmp_path, monkeypatch):
    from host.governance import vault_supabase

    monkeypatch.setattr(vault_supabase, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(vault_supabase, "snapshot_portfolio", lambda **kwargs: {})
    target = tmp_path / "vault.jsonl"

    missing = vault_supabase.append_vault999({"tool": "test"}, str(target))
    assert missing["persistence"]["status"] == "ERROR"
    assert not target.exists()

    target.write_text("", encoding="utf-8")
    appended = vault_supabase.append_vault999({"tool": "test"}, str(target))
    assert appended["persistence"]["status"] == "APPENDED"
    assert target.read_text(encoding="utf-8").strip()


def test_receipt_status_uses_structured_tool_result():
    class Result:
        is_error = False
        structured_content = {"result": {"status": "HOLD"}}

    assert _tool_result_status(Result()) == "HOLD"
