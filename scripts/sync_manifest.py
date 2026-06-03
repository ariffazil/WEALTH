#!/usr/bin/env python3
"""
sync_manifest.py — auto-generate WEALTH MCP manifest counts from runtime.

Source of truth: FastMCP runtime introspection via internal/monolith.py
(via async mcp.list_tools()). NOT decorator count — that includes
54 unnamed auto-exposed tools that the runtime can see but a code
grep cannot reconcile with intent.

Outputs:
  - fastmcp.json            (always)
  - .well-known/mcp.json    (with --full)
  - wealth-mcp-tools.json   (with --full)

Discipline: every commit touching internal/monolith.py @mcp.tool must
run this script with --full, or CI fails. See scripts/README.md.

State: scripts/.manifest_state.json stores the previous tool list for diffing.

DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
SEAL: 888_HOLD on 2026-06-03 by Arif Fazil (feat/wealth-manifest-sync-2026-06-03)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

# Suppress known deprecation noise from monolith import
warnings.filterwarnings("ignore", category=DeprecationWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = Path(__file__).resolve().parent / ".manifest_state.json"
ZERO_TOOLS_ABORT = (
    "SYNC_ABORT: runtime returned 0 tools — possible import failure, "
    "monolith.py not updated, or FastMCP registration broken"
)
IMPORT_FAIL_ABORT = (
    "SYNC_ABORT: failed to import internal.monolith — check sys.path and "
    "WEALTH pyproject.toml; this is a CI infrastructure error, not a manifest error"
)


def get_live_tools() -> list[str]:
    """Import the WEALTH FastMCP app and return the live tool name list.

    Uses the async mcp.list_tools() — the only introspection API exposed
    by FastMCP 3.3.1. Returns sorted name list.
    """
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from internal.monolith import mcp
    except Exception as e:
        print(
            f"{IMPORT_FAIL_ABORT}\n  root cause: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        sys.exit(2)

    async def _list():
        tools = await mcp.list_tools()
        return sorted([t.name for t in tools])

    return asyncio.run(_list())


def load_snapshot() -> set[str]:
    if SNAPSHOT_PATH.exists():
        try:
            data = json.loads(SNAPSHOT_PATH.read_text())
            if isinstance(data, list):
                return set(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return set()


def save_snapshot(tools: list[str]) -> None:
    SNAPSHOT_PATH.write_text(json.dumps(tools, indent=2, sort_keys=True))


def compute_diff(old: set[str], new: set[str]) -> tuple[list[str], list[str]]:
    """Returns (added, removed) — name lists."""
    return sorted(new - old), sorted(old - new)


def atomic_write_json(path: Path, data: dict) -> None:
    """Atomic JSON write: write to temp, fsync, replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, indent=2, sort_keys=True)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def update_fastmcp_json(tools: list[str]) -> None:
    """fastmcp.json: capabilities.tools.count + description string."""
    path = REPO_ROOT / "fastmcp.json"
    data = json.loads(path.read_text())
    data["capabilities"]["tools"]["count"] = len(tools)
    data["capabilities"]["tools"]["source"] = (
        "scripts/sync_manifest.py (auto-generated from FastMCP runtime; do not hand-edit)"
    )
    desc = data.get("description", "")
    # Replace any "(N tools live; ...)" parenthetical with current count
    new_paren = f"({len(tools)} tools live; run scripts/sync_manifest.py to update)"
    data["description"] = re.sub(r"\(\d+ tools live[^)]*\)", new_paren, desc)
    atomic_write_json(path, data)


def update_wellknown_json(tools: list[str]) -> None:
    """.well-known/mcp.json: primitives stays at 13 (canonical family), tools reflects live count."""
    path = REPO_ROOT / ".well-known" / "mcp.json"
    data = json.loads(path.read_text())
    meta = data.setdefault("metadata", {})
    surfaces = meta.setdefault("runtime_surfaces", {})
    canonical = surfaces.setdefault("canonical_kernel", {})
    canonical["tools"] = len(tools)
    # primitives stays — that's the 13 canonical family count, not the live count
    meta["live_runtime_count"] = len(tools)
    meta["live_runtime_as_of"] = "2026-06-03"
    meta["last_updated"] = "2026-06-03"
    atomic_write_json(path, data)


def update_tools_json(tools: list[str]) -> None:
    """wealth-mcp-tools.json: add live count note, keep schema body intact."""
    path = REPO_ROOT / "wealth-mcp-tools.json"
    data = json.loads(path.read_text())
    data["_live_runtime_count"] = len(tools)
    data["_deprecation_notice"] = (
        f"DEPRECATED. Live runtime as of 2026-06-03 serves {len(tools)} tools. "
        "For canonical surface, see .well-known/mcp.json. "
        "To regenerate this file from runtime, run: python scripts/sync_manifest.py --full"
    )
    atomic_write_json(path, data)


def print_diff(added: list[str], removed: list[str], live_count: int) -> None:
    print(f"Live: {live_count} tools")
    if added:
        print(f"  + added ({len(added)}):")
        for name in added:
            print(f"      {name}")
    if removed:
        print(f"  - removed ({len(removed)}):")
        for name in removed:
            print(f"      {name}")
    if not added and not removed:
        print("  (no changes since last snapshot)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync WEALTH MCP manifest counts from FastMCP runtime introspection."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also rewrite .well-known/mcp.json and wealth-mcp-tools.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute diff and print, but do not write any files",
    )
    args = parser.parse_args()

    tools = get_live_tools()

    if not tools:
        print(ZERO_TOOLS_ABORT, file=sys.stderr)
        return 1

    old = load_snapshot()
    new = set(tools)
    added, removed = compute_diff(old, new)

    print_diff(added, removed, len(tools))

    if args.dry_run:
        print("DRY RUN — no files written")
        return 0

    update_fastmcp_json(tools)
    print(f"  → fastmcp.json: count → {len(tools)}")

    if args.full:
        update_wellknown_json(tools)
        print(f"  → .well-known/mcp.json: live_runtime_count → {len(tools)}")
        update_tools_json(tools)
        print(f"  → wealth-mcp-tools.json: live count note added ({len(tools)} tools)")

    save_snapshot(tools)
    print(f"  → snapshot: {SNAPSHOT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
