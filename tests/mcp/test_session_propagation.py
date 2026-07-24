from __future__ import annotations

import pytest

from wealth_mcp.server import create_mcp_server


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["status", "schema", "domains", "health"])
async def test_capital_registry_echoes_session(mode: str) -> None:
    mcp = create_mcp_server()
    component = next(
        value
        for key, value in mcp._local_provider._components.items()
        if key.startswith("tool:capital_registry@")
    )
    result = await component.fn(
        mode=mode,
        session_id="SEAL-session-echo",
        actor_id="arif",
    )
    assert result["session_id"] == "SEAL-session-echo"
    assert result["actor_id"] == "arif"
