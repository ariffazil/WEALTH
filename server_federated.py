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
        "schema_version": "0.2",
        "organ_id": "wealth",
        "name": "WEALTH — Capital Intelligence",
        "role": "capital",
        "description": (
            "Capital intelligence for arifOS federation. Computes capital, "
            "risk, wisdom, and power metrics. Does NOT authorize execution. "
            "WEALTH computes. arifOS judges. Arif decides."
        ),
        "version": "2026.06.15",
        "url": "https://wealth.arif-fazil.com",
        "a2a_endpoint": "http://127.0.0.1:18082/a2a",
        "agent_card_url": "http://127.0.0.1:18082/.well-known/agent-card.json",
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
        "owned_mcp": [
            "wealth_wisdom_evaluate",
            "wealth_power_audit",
            "wealth_capture_scan",
            "wealth_compute_npv",
            "wealth_compute_irr",
            "wealth_conservation_check",
            "wealth_flow_check",
            "wealth_runway_check",
            "wealth_compute_emv",
            "wealth_compute_evoi",
            "wealth_monte_carlo_simulate",
            "wealth_confluence_check",
            "wealth_asymmetry_check",
            "wealth_stock_analysis",
            "wealth_personal_finance",
            "wealth_market_data",
            "wealth_omni_wisdom",
            "wealth_agent_path",
            "wealth_vault_write",
            "wealth_vault_query",
            "wealth_collapse_signature_scan",
            "wealth_beautiful_mouse_scan",
            "wealth_judge_handoff",
        ],
        "judge_skills": [],
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

    # 2026-06-29 — Federation-wide OAuth discovery (Hermes-flow fix).
    # Spec-compliant MCP clients (Cursor, Claude Code, MiniMax) fetch
    # /.well-known/oauth-protected-resource first per RFC 8707. Without
    # this, OAuth clients fail with "failed to get oauth authorization url".
    # arifOS (port 8088) is the canonical authorization server for the
    # whole federation; these endpoints mirror its metadata.
    async def _wealth_oauth_protected_resource(request):
        return JSONResponse(
            {
                "resource": "https://mcp.arif-fazil.com/mcp",
                "authorization_servers": ["https://mcp.arif-fazil.com"],
                "bearer_methods_supported": ["header"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

    async def _wealth_oauth_authorization_server(request):
        return JSONResponse(
            {
                "issuer": "https://mcp.arif-fazil.com",
                "authorization_endpoint": "https://mcp.arif-fazil.com/api/auth/authorize",
                "token_endpoint": "https://mcp.arif-fazil.com/api/auth/token",
                "jwks_uri": "https://mcp.arif-fazil.com/.well-known/jwks.json",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

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
            Route(
                "/.well-known/oauth-protected-resource",
                _wealth_oauth_protected_resource,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-protected-resource/mcp",
                _wealth_oauth_protected_resource,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-authorization-server",
                _wealth_oauth_authorization_server,
                methods=["GET"],
            ),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.lifespan,
    )

    # ── DNS Rebinding Protection (2026-07-08) ──────────────────────
    # MCPJam conformance: localhost servers must reject requests with
    # non-localhost Host/Origin headers to prevent DNS rebinding attacks.
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    _LOCALHOST_PATTERNS = ("localhost", "127.0.0.1", "[::1]", "::1")

    class DNSRebindingProtection(BaseHTTPMiddleware):
        async def dispatch(self, request: StarletteRequest, call_next):
            # Only check POST /mcp with initialize method
            if request.url.path == "/mcp" and request.method == "POST":
                try:
                    body = await request.body()
                    import json as _json

                    parsed = _json.loads(body)
                    if parsed.get("method") == "initialize":
                        host = (request.headers.get("host") or "").lower()
                        origin = (request.headers.get("origin") or "").lower()
                        if host and not any(p in host for p in _LOCALHOST_PATTERNS):
                            return StarletteResponse(
                                content=_json.dumps(
                                    {
                                        "error": "Invalid Origin",
                                        "detail": "DNS rebinding protection",
                                    }
                                ),
                                status_code=403,
                                media_type="application/json",
                            )
                        if origin and not any(p in origin for p in _LOCALHOST_PATTERNS):
                            return StarletteResponse(
                                content=_json.dumps(
                                    {
                                        "error": "Invalid Origin",
                                        "detail": "DNS rebinding protection",
                                    }
                                ),
                                status_code=403,
                                media_type="application/json",
                            )
                except Exception:
                    pass
            return await call_next(request)

    app.add_middleware(DNSRebindingProtection)

    print("WEALTH Federated Domain starting on port 18082...")
    print("  Architecture: 5-layer federated")
    print("  MCP endpoint: /mcp")
    print("  Health: /health")
    print("  DITEMPA BUKAN DIBERI")

    uvicorn.run(app, host="127.0.0.1", port=18082)
