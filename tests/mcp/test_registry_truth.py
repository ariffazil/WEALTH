"""
Tests for WEALTH MCP — Registry Truth.

Every tool in the MCP surface must be callable.
No phantom tools. No ghost aliases.

ZEN migration 2026-07-11: 7 capital_* canonical tools only.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from wealth_mcp.server import create_mcp_server


EXPECTED_TOOLS = [
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
        """Must have exactly the 7 canonical tools."""
        mcp = create_mcp_server()
        tool_names = _tool_names(mcp)
        for expected in EXPECTED_TOOLS:
            assert expected in tool_names, f"Missing tool: {expected}"
        assert len([t for t in tool_names if t in EXPECTED_TOOLS]) == 8

    def test_no_phantom_tools(self):
        """Registered public tools must be subset of the 7-canonical set."""
        mcp = create_mcp_server()
        tool_names = _tool_names(mcp)
        for name in tool_names:
            assert name in EXPECTED_TOOLS, f"Phantom tool: {name}"
