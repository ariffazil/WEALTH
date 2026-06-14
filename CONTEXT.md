# CONTEXT.md — WEALTH (Capital Intelligence)

> **Organ:** WEALTH | **Port:** 18082 | **Repo:** `ariffazil/wealth`
> **Kernel SoT:** `ariffazil/arifOS` (FEDERATION_CONTRACT.md + GENESIS/000)
> **Last Updated:** 2026-06-14

## Live State
- **Service:** `wealth-organ.service` (systemd, enabled)
- **Health:** `http://127.0.0.1:18082/health`
- **Tools:** 20 public MCP tools + 34 hidden aliases (65 `@mcp.tool` decorators)
- **License:** AGPL-3.0
- **Dual Runtime:** Python (canonical, `internal/monolith.py`) + Node.js (legacy)

## Dependencies
- arifOS MCP kernel (port 8088) — constitutional judgment
- PostgreSQL (port 5432) — trades, positions, watchlist tables
- Caddy reverse proxy for public endpoint

## Current Focus
- Operational. D4 Stock Analysis live (12 modes). Python tests 153/153 PASS.
- GENESIS/ still missing (pending 011+ allocation)

## Known Issues
- `raw/CONSTITUTION.md` is a stale "AGI-bot v63" duplicate with wrong floor numbering — tombstone header added; removal requires explicit F13 approval.
- APEX (port 3002) is legacy health probe only; deliberation moved to AAA a2a-server.
- No GENESIS/ — kernel canon unlinked.

## Federation Services Note
- **A-FORGE** hosts MIND (port 51001) and MEMORY (port 51002) runtime services for cross-agent state and recall. These are not independent organs.
