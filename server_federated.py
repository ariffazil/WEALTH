#!/usr/bin/env python3
"""
WEALTH Federated Domain — MCP Server Entry Point.

This is the NEW entry point that uses the federated architecture:
  wealth_core/    — pure engines (no MCP, no I/O)
  wealth_contracts/ — output envelopes, epistemic tags
  wealth_mcp/     — MCP surface (tools, prompts, resources)
  wealth_arifos_bridge/ — arifOS integration
  wealth_compat/  — legacy aliases

To activate: symlink or rename to server.py after migration is verified.
To test: python server_federated.py

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
    from starlette.routing import Mount
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.http_app(
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
    )

    # Health endpoint
    @app.route("/health")
    async def health(request):
        from starlette.responses import JSONResponse
        return JSONResponse({
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
        })

    print("WEALTH Federated Domain starting on port 18082...")
    print("  Architecture: 5-layer federated")
    print("  MCP endpoint: /mcp")
    print("  Health: /health")
    print("  DITEMPA BUKAN DIBERI")

    uvicorn.run(app, host="127.0.0.1", port=18082)
