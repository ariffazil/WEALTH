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

import json
import os
import re
import subprocess
import uuid
from pathlib import Path

from wealth_mcp import CAPITAL_TOOL_NAMES, PUBLIC_TOOL_NAMES, WEALTH_VERSION
from wealth_mcp.server import create_mcp_server


def _resolve_source_commit(repo_path: str | Path | None = None) -> dict[str, object]:
    """Resolve the source SHA while keeping static fallback data unverified.

    Priority:
      1. git rev-parse HEAD (live git repo)
      2. .git_commit file (deployment artifact)
      3. UNAVAILABLE
    """
    repo = Path(repo_path) if repo_path is not None else Path(__file__).resolve().parent

    # Try live git first
    try:
        result = subprocess.run(
            ["/usr/bin/git", "-C", str(repo), "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        sha = result.stdout.strip()
        if result.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{7,40}", sha):
            return {
                "git_commit": sha,
                "git_commit_source": "git",
                "source_sha_available": True,
                "git_commit_fallback": None,
                "git_commit_fallback_trusted": False,
            }
    except (OSError, subprocess.SubprocessError):
        pass

    # Fallback: read .git_commit file
    try:
        fallback_sha = (repo / ".git_commit").read_text(encoding="utf-8").strip()
    except OSError:
        fallback_sha = ""
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", fallback_sha):
        fallback_sha = ""

    if fallback_sha:
        return {
            "git_commit": "UNAVAILABLE",
            "git_commit_source": "fallback_file",
            "source_sha_available": False,
            "git_commit_fallback": fallback_sha,
            "git_commit_fallback_trusted": False,
        }

    return {
        "git_commit": "UNAVAILABLE",
        "git_commit_source": "unavailable",
        "source_sha_available": False,
        "git_commit_fallback": None,
        "git_commit_fallback_trusted": False,
    }


base_dir = os.path.abspath(os.path.dirname(__file__))
mcp = create_mcp_server()

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.responses import JSONResponse

    async def health(request):
        # FEDERATION HANDSHAKE (canonical: arifOS/arifosmcp/schemas/federation_enums.py)
        # See: /root/AAA/governance/FEDERATION_HANDSHAKE.md
        # T5 2026-07-17 — canonical 5-field federation header + organ payload
        identity_hash = "UNAVAILABLE"
        try:
            import hashlib

            id_path = Path(base_dir) / "identity.toml"
            if id_path.exists():
                try:
                    import blake3  # type: ignore

                    identity_hash = blake3.blake3(id_path.read_bytes()).hexdigest()
                except Exception:
                    identity_hash = hashlib.sha256(id_path.read_bytes()).hexdigest()
        except Exception:
            identity_hash = "UNAVAILABLE"

        # Tool surface visibility: distinguish a live count from declared metadata.
        public_tools_live = None
        tool_count_source = "unavailable"
        tool_count_error = None
        try:
            tools = await mcp.list_tools()
            public_tools_live = len(tools)
            tool_count_source = "mcp.list_tools"
        except Exception as exc:
            tool_count_error = f"{type(exc).__name__}: {exc}"

        commit_identity = _resolve_source_commit(base_dir)

        return JSONResponse(
            {
                "status": "healthy",
                "identity": identity_hash,
                "identity_hash": identity_hash,
                **commit_identity,
                "tools_loaded": public_tools_live,
                "public_tools": public_tools_live,
                "public_tools_declared": len(PUBLIC_TOOL_NAMES),
                "canonical_tools": len(CAPITAL_TOOL_NAMES),
                "tool_count_source": tool_count_source,
                "tool_count_error": tool_count_error,
                "apex_scalars": {
                    "G": {"value": None, "status": "UNMEASURED"},
                    "C_dark": {"value": None, "status": "UNMEASURED"},
                    "W3": {"value": None, "status": "UNMEASURED"},
                    "h": {"value": None, "status": "UNMEASURED"},
                    "QDF": {"value": None, "status": "UNMEASURED"},
                },
                "federation_geometry": {
                    "status": "enabled",
                    "subjects": 0,
                    "ledger_events": 0,
                    "witness_oracle": "active",
                    "note": "geometry owned by arifOS; WEALTH reports local presence only",
                },
                "final_authority": "ARIF",
                # F2-fidelity fix (MCP-PROBE-2026-08-08): declare authority_ceiling.
                # Per ORGAN.md, WEALTH = COMPUTE_ONLY (555).
                "authority_ceiling": "555_COMPUTE_ONLY",
                "version": (
                    f"v{WEALTH_VERSION}"
                    if WEALTH_VERSION != "UNAVAILABLE"
                    else WEALTH_VERSION
                ),
                "federation_schema_version": "2.0.0",
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

    # ── A2A Agent Card: REMOVED 2026-07-15 (WEALTH portion of federation-wide
    # A2A card consolidation). Local agent-card serving is now disabled;
    # federation-level A2A discovery flows through the central coordinator
    # (AAA / a2aproject mesh). MCP manifests, OAuth discovery, /health,
    # /tools, and the canonical capital surface are preserved below.

    # Get the MCP ASGI app
    # Pass host_origin_protection=False because our outer DNSRebindingProtection
    # middleware already handles Host and Origin verification without throwing 421.
    mcp_app = mcp.http_app(
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
        host_origin_protection=False,
    )

    # Wrap in a Starlette app with health endpoint
    # CRITICAL: pass lifespan from mcp_app to parent app

    # 2026-06-29 — Federation-wide OAuth discovery (Hermes-flow fix).
    # Spec-compliant MCP clients (Cursor, Claude Code, MiniMax) fetch
    # /.well-known/oauth-protected-resource first per RFC 9728. Without
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

    # ── DNS Rebinding Protection (restored 2026-07-09 P0-8) ────────
    # Header-only check (no body consume). Allow production + localhost.
    # Empty Origin is allowed (server-to-server MCP clients).
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    _ALLOWED_HOST_MARKERS = (
        "localhost",
        "127.0.0.1",
        "[::1]",
        "::1",
        "wealth.arif-fazil.com",
        "mcp.arif-fazil.com",
        "arif-fazil.com",
        # 2026-09-04 FI-008: mesh ingress — OpenClaw edge (kvm4-forge) reaches organs via the
        # tailscaled front on 100.64.0.2, so Host header is the mesh IP/name. Edge migration fix.
        "100.64.0.2",
        "af-forge",
    )
    _ALLOWED_ORIGIN_PREFIXES = (
        "https://wealth.arif-fazil.com",
        "https://mcp.arif-fazil.com",
        "https://arif-fazil.com",
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )

    # ── Session Store ──────────────────────────────────────────────────────
    # In-memory set of valid MCP session IDs for transport-level enforcement.
    _valid_mcp_sessions: set[str] = set()

    class McpSessionEnforcementMiddleware(BaseHTTPMiddleware):
        """Enforce Mcp-Session-Id header on all MCP tool calls.

        Strict-organ doctrine: domain operations require a session. Always.
        Three-way taxonomy: 400 missing / 401 invalid / 403 insufficient.
        Initialize requests are exempt (they bootstrap the session).
        """

        _EXEMPT_METHODS = frozenset({"initialize", "notifications/initialized"})

        async def dispatch(self, request: StarletteRequest, call_next):
            if request.method == "POST" and request.url.path.startswith("/mcp"):
                body = await request.body()
                method = None
                if body:
                    try:
                        payload = json.loads(body)
                        method = payload.get("method", "")
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

                # Initialize bootstraps the session — allow through
                if method in self._EXEMPT_METHODS:
                    # Generate and store session ID for initialize
                    if method == "initialize":
                        new_sid = uuid.uuid4().hex
                        _valid_mcp_sessions.add(new_sid)
                        # Rebuild request with new scope including session_key
                        scope = dict(request.scope)
                        scope["mcp_session_id"] = new_sid
                        # Restore body for downstream
                        request._body = body
                        response = await call_next(request)
                        # Inject Mcp-Session-Id header into the response
                        response.headers["Mcp-Session-Id"] = new_sid
                        return response
                    request._body = body
                    return await call_next(request)

                # Non-initialize requests must have Mcp-Session-Id
                session_id = request.headers.get(
                    "Mcp-Session-Id"
                ) or request.headers.get("mcp-session-id")

                if not session_id:
                    return StarletteResponse(
                        content=json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32000,
                                    "message": "SESSION_MISSING: Mcp-Session-Id header required",
                                },
                            }
                        ),
                        status_code=400,
                        media_type="application/json",
                    )

                # Validate session exists
                if session_id not in _valid_mcp_sessions:
                    return StarletteResponse(
                        content=json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32000,
                                    "message": "SESSION_INVALID: Unknown or expired session ID",
                                },
                            }
                        ),
                        status_code=404,
                        media_type="application/json",
                    )
                request._body = body

            return await call_next(request)

    class DNSRebindingProtection(BaseHTTPMiddleware):
        async def dispatch(self, request: StarletteRequest, call_next):
            if request.url.path.startswith("/mcp"):
                host = (request.headers.get("host") or "").lower()
                origin = (request.headers.get("origin") or "").strip()
                if host and not any(m in host for m in _ALLOWED_HOST_MARKERS):
                    return StarletteResponse(
                        content='{"error":"Invalid Host","detail":"DNS rebinding protection"}',
                        status_code=403,
                        media_type="application/json",
                    )
                if origin and not any(
                    origin.startswith(p) for p in _ALLOWED_ORIGIN_PREFIXES
                ):
                    return StarletteResponse(
                        content='{"error":"Invalid Origin","detail":"DNS rebinding protection"}',
                        status_code=403,
                        media_type="application/json",
                    )
            return await call_next(request)

    # Order matters: session enforcement OUTERMOST (runs first in Starlette)
    # DNS protection runs last (inner) so session check happens before host check.
    app.add_middleware(DNSRebindingProtection)
    app.add_middleware(McpSessionEnforcementMiddleware)

    print("WEALTH Federated Domain starting on port 18082...")
    print("  Architecture: 5-layer federated")
    print("  MCP endpoint: /mcp")
    print("  Health: /health")
    print("  DITEMPA BUKAN DIBERI")

    uvicorn.run(app, host="127.0.0.1", port=18082)
