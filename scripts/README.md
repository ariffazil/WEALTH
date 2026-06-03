# WEALTH Manifest Sync Discipline

**SEAL: 888_HOLD on 2026-06-03 by Arif Fazil** (`feat/wealth-manifest-sync-2026-06-03`)

## Why this exists

`fastmcp.json` previously hardcoded `"count": 87` and a `"87 tools live"` description string. Runtime introspection via FastMCP showed **44 live tools**. The 87 figure was a manually authored static write that was never updated as tools were pruned from `internal/monolith.py`.

This script is the structural fix. The 87 → 44 correction in `fastmcp.json` is the surface fix. Without this script, the drift will return in 2–3 months.

## What it does

`scripts/sync_manifest.py` imports `internal/monolith.py`, calls `await mcp.list_tools()` against the live FastMCP app, and atomically rewrites:

- **`fastmcp.json`** (always) — `capabilities.tools.count` and the `(N tools live; …)` substring in `description`
- **`.well-known/mcp.json`** (with `--full`) — `metadata.runtime_surfaces.canonical_kernel.tools` and `metadata.live_runtime_count`
- **`wealth-mcp-tools.json`** (with `--full`) — adds `_live_runtime_count` field and refreshes `_deprecation_notice`

It also:
- Emits a diff: tools added, removed, or renamed since the last snapshot
- **Zero-tools guard**: exits with `SYNC_ABORT` if FastMCP returns 0 tools (catches broken imports)
- Stores the previous tool list at `scripts/.manifest_state.json` for diffing

## Usage

```bash
# First run after this branch lands (creates initial snapshot, writes all 3 manifests)
python scripts/sync_manifest.py --full

# Subsequent runs (compares against snapshot, rewrites only if changed)
python scripts/sync_manifest.py --full

# Dry-run: see what would change without writing files
python scripts/sync_manifest.py --dry-run

# Minimum (writes only fastmcp.json)
python scripts/sync_manifest.py
```

## Discipline

**Every commit that touches `internal/monolith.py` `@mcp.tool` decorators MUST:**

1. Run `python scripts/sync_manifest.py --full` locally before committing
2. Commit the regenerated manifest files in the same commit as the code change
3. Push

**The CI hook** (separate commit, see `pyproject.toml` discussion below) will fail any commit that:
- Touches `internal/monolith.py`
- Does NOT also touch `fastmcp.json` (i.e., the manifest count is stale)

## Why runtime introspection, not decorator grep

`@mcp.tool` decorators in `internal/monolith.py` total **84** (verified 2026-06-03). Only **30** have explicit `name="..."`. The remaining **54** are auto-named by FastMCP from the function name. A `grep @mcp.tool | wc -l` would report 84, but FastMCP exposes only 44 distinct live tools. The runtime count is the only authoritative number.

This is also why a hand-edited manifest count is structurally fragile: even a correct total today becomes wrong the next time someone adds an unnamed decorator. Runtime introspection is the only path that doesn't decay.

## What stays out of scope

- **Path C** (decorator audit): reading all 84 decorators and classifying the 54 unnamed ones as `intentional_expose` / `hide` / `rename` / `remove`. That's a separate branch (`feat/wealth-decorator-audit-2026-06-03`) and a separate work session — it touches 84 sites in a 500KB file.
- **WEALTH module federation** (decomposing `monolith.py` into `engines/` modules): locked until Path C completes, per the agreement that blind decomposition is what generated the 87-vs-44 mess in the first place.

## Files in this branch

```
feat/wealth-manifest-sync-2026-06-03
├── fastmcp.json                  count: 87 → 44, description corrected
├── .well-known/mcp.json          primitives: 13, tools: 44, live_runtime_count added
├── wealth-mcp-tools.json         _deprecation_notice + _live_runtime_count added
├── scripts/sync_manifest.py      NEW — auto-generation script
├── scripts/README.md             NEW — this file
├── scripts/.manifest_state.json  NEW (created on first run)
└── pyproject.toml                (separate commit) CI hook
```

---

DITEMPA BUKAN DIBERI — Forged, Not Given.
