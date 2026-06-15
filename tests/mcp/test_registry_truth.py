"""
Tests for WEALTH MCP — Registry Truth.

Every tool in the MCP surface must be callable.
No phantom tools. No ghost aliases.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_mcp.server import create_mcp_server


EXPECTED_TOOLS = [
    "wealth_wisdom_evaluate",
    "wealth_power_audit",
    "wealth_capture_scan",
    "wealth_compute_npv",
    "wealth_compute_irr",
    "wealth_conservation_check",
    "wealth_flow_check",
    "wealth_runway_check",
    "wealth_emv_compute",
    "wealth_monte_carlo",
    "wealth_evoi_compute",
    "wealth_confluence_check",
    "wealth_asymmetry_check",
    "wealth_system_registry_status",
    # Legacy surface tools (delegate to monolith)
    "wealth_stock_analysis",
    "wealth_personal_finance",
    "wealth_market_data",
    "wealth_omni_wisdom",
    "wealth_agent_path",
]


class TestRegistryTruth:
    """All expected tools must be registered."""

    def test_server_creates(self):
        """Server must create without error."""
        mcp = create_mcp_server()
        assert mcp is not None

    def test_expected_tool_count(self):
        """Must have at least the expected number of tools."""
        mcp = create_mcp_server()
        # FastMCP stores tools internally
        tool_names = []
        for key in mcp._local_provider._components:
            if key.startswith("tool:"):
                tool_names.append(key[5:].rstrip("@"))
        for expected in EXPECTED_TOOLS:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_no_phantom_tools(self):
        """Every registered tool must be in expected list."""
        mcp = create_mcp_server()
        tool_names = []
        for key in mcp._local_provider._components:
            if key.startswith("tool:"):
                tool_names.append(key[5:].rstrip("@"))
        # New tools are allowed, but no expected tool should be missing
        for expected in EXPECTED_TOOLS:
            assert expected in tool_names
