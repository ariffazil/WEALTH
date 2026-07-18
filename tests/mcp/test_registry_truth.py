"""
Tests for WEALTH MCP — Registry Truth.

Every tool in the MCP surface must be callable.
No phantom tools. No ghost aliases.

ZEN migration 2026-07-11: 7 capital_* canonical tools only.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_mcp.server import create_mcp_server


EXPECTED_TOOLS = [
    "wealth_institutional_stress_index",
    "wealth_cascade_model",
    "wealth_governance_capacity",
    "wealth_external_exploitation_detect",
    "capital_primitive",
    "capital_health",
    "capital_diagnose",
    "capital_wisdom",
    "capital_market",
    "capital_ledger",
    "capital_registry",
    "capital_entropy",
]


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
