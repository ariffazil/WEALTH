"""
A2A Card Consolidation (WEALTH portion) — Federation-wide.

Date: 2026-07-15.
Scope: WEALTH local A2A agent-card surfaces removed during federation-wide
A2A card consolidation. MCP manifests, OAuth discovery, /health, /tools,
and the canonical capital surface are preserved.

These tests prove:
  1. The local static agent-card file (.well-known/agent-card.json) is gone.
  2. The local in-memory _WEALTH_AGENT_CARD constant is gone.
  3. The _wealth_agent_card_handler function is gone.
  4. Both /.well-known/agent.json and /.well-known/agent-card.json routes
     are gone from server_federated.py.
  5. The federation's preserved discovery surfaces remain intact:
       - /health (federation handshake)
       - /tools (capital surface discovery)
       - /.well-known/oauth-protected-resource (RFC 8707)
       - /.well-known/oauth-protected-resource/mcp (RFC 8707)
       - /.well-known/oauth-authorization-server
       - Mount("/", app=mcp_app) — the MCP ASGI surface
     at the source level (server_federated.py).
  6. Preserved MCP manifests remain on disk:
       - .well-known/mcp.json (canonical discovery manifest)
       - .well-known/mcp/server.json (sub-route manifest)

The tests are self-contained: only `pathlib`, `ast`, and stdlib.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WELL_KNOWN = ROOT / ".well-known"
SERVER_FEDERATED = ROOT / "server_federated.py"


# ── Helpers ─────────────────────────────────────────────────────────────


def _module_ast(path: Path) -> ast.Module:
    """Parse a Python source file into an AST module."""
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_names(tree: ast.AST) -> set[str]:
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _assigned_top_level_names(tree: ast.Module) -> set[str]:
    """Names that appear on the LHS of a top-level assignment (Name target)."""
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            names.add(stmt.target.id)
        elif isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name):
                    names.add(tgt.id)
    return names


def _annotated_top_level_names(tree: ast.Module) -> set[str]:
    """Names that appear on the LHS of a top-level AnnAssign with a value."""
    names: set[str] = set()
    for stmt in tree.body:
        if (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.value is not None
        ):
            names.add(stmt.target.id)
    return names


def _route_paths(tree: ast.AST) -> set[str]:
    """Collect first positional string-argument of every Route(...) call."""
    paths: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Route":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                paths.add(node.args[0].value)
        elif isinstance(func, ast.Attribute) and func.attr == "Route":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                paths.add(node.args[0].value)
    return paths


def _mount_paths(tree: ast.AST) -> set[str]:
    """Collect first positional string-argument of every Mount(...) call."""
    paths: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Mount":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                paths.add(node.args[0].value)
        elif isinstance(func, ast.Attribute) and func.attr == "Mount":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                paths.add(node.args[0].value)
    return paths


# ── Section 1: Local agent-card file must be gone ───────────────────────


def test_local_agent_card_file_removed():
    """The static .well-known/agent-card.json must NOT exist locally."""
    assert not (WELL_KNOWN / "agent-card.json").exists(), (
        "Local static agent-card.json still on disk; "
        "federation A2A card consolidation requires its removal."
    )


def test_well_known_directory_has_no_agent_card_json():
    """No spurious agent-card.json anywhere in .well-known/."""
    matches = list(WELL_KNOWN.rglob("agent-card*.json"))
    assert matches == [], f"Found unexpected agent-card*.json files: {matches}"


# ── Section 2: MCP manifests must be preserved ──────────────────────────


def test_mcp_manifest_well_known_json_preserved():
    """MCP canonical discovery manifest (.well-known/mcp.json) is preserved."""
    path = WELL_KNOWN / "mcp.json"
    assert path.exists(), "MCP manifest .well-known/mcp.json must be preserved"
    assert path.stat().st_size > 0, "MCP manifest must not be empty"


def test_mcp_server_card_preserved():
    """MCP sub-route manifest (.well-known/mcp/server.json) is preserved."""
    path = WELL_KNOWN / "mcp" / "server.json"
    assert path.exists(), "MCP sub-route manifest .well-known/mcp/server.json must be preserved"
    assert path.stat().st_size > 0, "MCP sub-route manifest must not be empty"


# ── Section 3: Local A2A agent-card surfaces gone from server_federated ─


def test_server_federated_module_parses_clean():
    """server_federated.py must remain a valid Python module."""
    ast.parse(SERVER_FEDERATED.read_text(encoding="utf-8"))


def test_local_agent_card_constant_removed_from_source():
    """_WEALTH_AGENT_CARD constant must be fully removed from server_federated.py."""
    tree = _module_ast(SERVER_FEDERATED)
    top_level_names = _assigned_top_level_names(tree) | _annotated_top_level_names(tree)
    # _WEALTH_AGENT_CARD was an assignment at module top-level. Even if our
    # refactor nests it elsewhere, this name is reserved for the consolidated
    # agent card surface and must not appear at all.
    assert "_WEALTH_AGENT_CARD" not in top_level_names, (
        "_WEALTH_AGENT_CARD constant still defined at module top-level."
    )
    # Also check function-scope declarations (e.g. inside if __name__ == "__main__").
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "_WEALTH_AGENT_CARD":
                    raise AssertionError(
                        "_WEALTH_AGENT_CARD assignment still present in server_federated.py."
                    )
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_WEALTH_AGENT_CARD":
                raise AssertionError(
                    "_WEALTH_AGENT_CARD annotated assignment still present."
                )


def test_local_agent_card_handler_removed_from_source():
    """_wealth_agent_card_handler must not be defined anywhere in server_federated.py."""
    tree = _module_ast(SERVER_FEDERATED)
    fn_names = _function_names(tree)
    assert "_wealth_agent_card_handler" not in fn_names, (
        "_wealth_agent_card_handler still defined in server_federated.py."
    )


def test_local_agent_json_route_removed():
    """Route /.well-known/agent.json must not be registered in server_federated.py."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/.well-known/agent.json" not in routes, (
        f"Route '/.well-known/agent.json' still registered in server_federated.py. "
        f"Present routes: {sorted(routes)}"
    )


def test_local_agent_card_json_route_removed():
    """Route /.well-known/agent-card.json must not be registered in server_federated.py."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/.well-known/agent-card.json" not in routes, (
        f"Route '/.well-known/agent-card.json' still registered in server_federated.py. "
        f"Present routes: {sorted(routes)}"
    )


# ── Section 4: Core federation discovery surfaces remain on WEALTH ──────


def test_health_route_preserved():
    """/health federation handshake route must remain."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/health" in routes, (
        f"/health route missing from server_federated.py. Present: {sorted(routes)}"
    )


def test_tools_route_preserved():
    """/tools capital-surface discovery route must remain."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/tools" in routes, (
        f"/tools route missing from server_federated.py. Present: {sorted(routes)}"
    )


def test_oauth_protected_resource_route_preserved():
    """RFC 8707 — /.well-known/oauth-protected-resource must remain."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/.well-known/oauth-protected-resource" in routes, (
        "OAuth discovery route /oauth-protected-resource missing."
    )


def test_oauth_protected_resource_mcp_route_preserved():
    """RFC 8707 — /.well-known/oauth-protected-resource/mcp alias must remain."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/.well-known/oauth-protected-resource/mcp" in routes, (
        "OAuth discovery alias /oauth-protected-resource/mcp missing."
    )


def test_oauth_authorization_server_route_preserved():
    """OAuth /.well-known/oauth-authorization-server must remain."""
    tree = _module_ast(SERVER_FEDERATED)
    routes = _route_paths(tree)
    assert "/.well-known/oauth-authorization-server" in routes, (
        "OAuth authorization server discovery route missing."
    )


def test_mcp_mount_preserved():
    """The MCP ASGI surface must still be mounted at the root."""
    tree = _module_ast(SERVER_FEDERATED)
    mounts = _mount_paths(tree)
    assert "/" in mounts, (
        f"Root Mount('/') missing from server_federated.py. Present Mounts: {sorted(mounts)}"
    )


def test_server_federated_module_imports_clean():
    """server_federated.py must still import without error after the consolidation."""
    # Re-import with a fresh sys.modules cache so a previous test's import
    # doesn't mask a new error.
    saved = sys.modules.pop("server_federated", None)
    try:
        import server_federated  # noqa: F401
    finally:
        if saved is not None:
            sys.modules["server_federated"] = saved
    # Module-level must still expose the canonical entry points.
    import server_federated as sf  # noqa: F401
    assert hasattr(sf, "create_mcp_server"), "create_mcp_server must remain exported."
    assert hasattr(sf, "mcp"), "mcp FastMCP server instance must remain exported."


# ── Section 5: No agent-card strings leaked into server_federated ───────


def test_no_agent_card_url_leaked_in_source():
    """server_federated.py must not contain a /agent-card.json reference."""
    text = SERVER_FEDERATED.read_text(encoding="utf-8")
    assert "agent-card.json" not in text, (
        "server_federated.py still references 'agent-card.json'. "
        "This is the WEALTH A2A consolidation surface; all references must be gone."
    )


def test_no_agent_card_url_path_leaked_in_source():
    """No /agent-card.json URL fragment must survive in server_federated.py."""
    text = SERVER_FEDERATED.read_text(encoding="utf-8")
    assert "/agent-card.json" not in text, (
        "server_federated.py still references '/agent-card.json'."
    )


def test_no_agent_card_constant_name_leaked_in_source():
    """The literal identifier `_WEALTH_AGENT_CARD` must not appear in source."""
    text = SERVER_FEDERATED.read_text(encoding="utf-8")
    assert "_WEALTH_AGENT_CARD" not in text, (
        "Source string '_WEALTH_AGENT_CARD' still appears in server_federated.py."
    )


# ── Section 6: No agent-card handler lambda/call survives ───────────────


def test_no_agent_card_handler_function_call_remaining():
    """No call site of _wealth_agent_card_handler must remain."""
    text = SERVER_FEDERATED.read_text(encoding="utf-8")
    assert "_wealth_agent_card_handler" not in text, (
        "Source string '_wealth_agent_card_handler' still appears in server_federated.py."
    )
