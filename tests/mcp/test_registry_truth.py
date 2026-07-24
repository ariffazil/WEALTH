"""
Tests for WEALTH MCP — Registry Truth.

Every tool in the MCP surface must be callable.
No phantom tools. No ghost aliases.

ZEN migration 2026-07-24: 8 canonical capital tools + 4 institutional tools.
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


EXPECTED_TOOLS = list(PUBLIC_TOOL_NAMES)


def _tool_names(mcp) -> list[str]:
    tool_names: list[str] = []
    for key in mcp._local_provider._components:
        if key.startswith("tool:"):
            tool_names.append(key[5:].rstrip("@"))
    return tool_names


class TestRegistryTruth:
    """All expected tools must be registered."""

    def test_server_creates(self):
        """Server must create without error."""
        mcp = create_mcp_server()
        assert mcp is not None

    def test_expected_tool_count(self):
        """Must expose the current registered surface without omissions."""
        mcp = create_mcp_server()
        tool_names = _tool_names(mcp)
        for expected in EXPECTED_TOOLS:
            assert expected in tool_names, f"Missing tool: {expected}"
        assert len(tool_names) == len(EXPECTED_TOOLS)

    def test_no_phantom_tools(self):
        """Registered public tools must match the declared runtime set."""
        mcp = create_mcp_server()
        tool_names = _tool_names(mcp)
        for name in tool_names:
            assert name in EXPECTED_TOOLS, f"Phantom tool: {name}"

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

    assert status["canonical_tools"] == list(CAPITAL_TOOL_NAMES)
    assert status["canonical_tool_count"] == len(CAPITAL_TOOL_NAMES) == 8
    assert status["public_tools"] == list(PUBLIC_TOOL_NAMES)
    assert status["public_tool_count"] == len(PUBLIC_TOOL_NAMES) == 12
    assert schema["canonical_tool_count"] == 8
    assert schema["public_tool_count"] == 12
    assert domains["canonical_tool_count"] == 8
    assert domains["public_tool_count"] == 12
    assert health["canonical_tools"] == 8
    assert health["public_tools"] == 12
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
    envelope = await entropy(mode="power_consequence_map")

    assert envelope["tool_name"] == "capital_entropy"
    assert envelope["result"]["status"] == "UNAVAILABLE"
    assert envelope["result"]["error_code"] == "ENTROPY_MODULE_MISSING"
    assert envelope["execution_authority"] == "BLOCKED"
    assert envelope["shadow"] is True


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
