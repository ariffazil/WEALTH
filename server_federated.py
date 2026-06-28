#!/usr/bin/env python3
"""
WEALTH Federated Domain — MCP Server Entry Point.

This is the NEW entry point that uses the federated architecture:
  wealth_core/    — pure engines (no MCP, no I/O)
  wealth_contracts/ — output envelopes, epistemic tags
  wealth_mcp/     — MCP surface (tools, prompts, resources)
  wealth_arifos_bridge/ — arifOS integration
  wealth_compat/  — legacy aliases

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import os
import sys

# Ensure parent directory is in path
base_dir = os.path.abspath(os.path.dirname(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from wealth_mcp.server import create_mcp_server

mcp = create_mcp_server()

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.responses import JSONResponse

    async def health(request):
        return JSONResponse(
            {
                "status": "ALIVE",
                "version": "2026.06.15",
                "domain": "WEALTH Federated Domain",
                "transport": "streamable-http",
                "architecture": "federated",
                "layers": [
                    "wealth_core",
                    "wealth_contracts",
                    "wealth_mcp",
                    "wealth_arifos_bridge",
                    "wealth_compat",
                ],
            }
        )

    async def tools_endpoint(request):
        tools_list = await mcp.list_tools()
        return JSONResponse({"tools": [{"name": t.name} for t in tools_list]})

    # ── A2A Agent Card (Federation Discovery) ────────────────────────────
    # FORGE 2026-06-28: /.well-known/agent.json for AAA A2A mesh discovery.

    _WEALTH_AGENT_CARD = {
        "schema": "agent-manifest/v1",
        "name": "WEALTH — Capital Intelligence",
        "description": (
            "Capital intelligence for arifOS federation. Computes capital, "
            "risk, wisdom, and power metrics. Does NOT authorize execution. "
            "WEALTH computes. arifOS judges. Arif decides."
        ),
        "version": "2026.06.15",
        "url": "https://wealth.arif-fazil.com",
        "endpoints": {
            "mcp": "https://wealth.arif-fazil.com/mcp",
            "health": "https://wealth.arif-fazil.com/health",
            "tools": "https://wealth.arif-fazil.com/tools",
        },
        "authority_class": "evidence",
        "allowed_action_classes": ["OBSERVE", "PREPARE"],
        "max_risk_tier": "T1",
        "auth": {"type": "none"},
        "federation": {
            "protocol": "A2A",
            "peer_coordinator": "https://aaa.arif-fazil.com",
            "constitutional_kernel": "https://arifos.arif-fazil.com",
        },
        "owned_mcp": {
            "server": "wealth-mcp",
            "transport": "streamable-http",
            "tool_count": 25,
            "canonical_tools": [
                "wealth_wisdom_evaluate",
                "wealth_power_audit",
                "wealth_capture_scan",
                "wealth_compute_npv",
                "wealth_compute_irr",
                "wealth_conservation_check",
                "wealth_flow_check",
                "wealth_runway_check",
                "wealth_compute_emv",
                "wealth_monte_carlo_simulate",
                "wealth_compute_evoi",
                "wealth_stock_analysis",
                "wealth_omni_wisdom",
                "wealth_collapse_signature_scan",
                "wealth_beautiful_mouse_scan",
            ],
        },
        "skills": [
            {
                "id": "capital.thermodynamics",
                "name": "Capital Thermodynamics",
                "tags": ["npv", "irr", "emv", "risk"],
            },
            {
                "id": "institutional.resilience",
                "name": "Institutional Resilience",
                "tags": ["collapse", "signature", "scan"],
            },
            {
                "id": "wisdom.evaluate",
                "name": "Wisdom Evaluation",
                "tags": ["dignity", "sovereignty", "optionality"],
            },
        ],
    }

    async def _wealth_agent_card_handler(request):
        return JSONResponse(_WEALTH_AGENT_CARD)

    # Get the MCP ASGI app
    mcp_app = mcp.http_app(
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
    )

    # Wrap in a Starlette app with health endpoint
    # CRITICAL: pass lifespan from mcp_app to parent app
    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/tools", tools_endpoint),
            Route(
                "/.well-known/agent.json", _wealth_agent_card_handler, methods=["GET"]
            ),
            Route(
                "/.well-known/agent-card.json",
                _wealth_agent_card_handler,
                methods=["GET"],
            ),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.lifespan,
    )

    print("WEALTH Federated Domain starting on port 18082...")
    print("  Architecture: 5-layer federated")
    print("  MCP endpoint: /mcp")
    print("  Health: /health")
    print("  DITEMPA BUKAN DIBERI")

    uvicorn.run(app, host="127.0.0.1", port=18082)
