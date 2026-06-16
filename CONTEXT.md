# CONTEXT.md — WEALTH (Capital Intelligence)

> **Organ:** WEALTH | **Port:** 18082 | **Repo:** `ariffazil/wealth`
> **Kernel SoT:** `ariffazil/arifos` (FEDERATION_CONTRACT.md + GENESIS/000)
> **Last Updated:** 2026-06-16

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
- T0 canon cleanup complete: stale constitution duplicates removed.
- T4 A-FORGE lease gate in progress.

## Known Issues
- APEX (port 3002) is legacy health probe only; deliberation moved to AAA a2a-server.
- GENESIS/ linked via `011_WEALTH_MANDATE.md`; canonical constitution is `/root/arifOS/static/arifos/theory/000/000_CONSTITUTION.md`.

## Federation Services Note
- **A-FORGE** hosts MIND (port 51001) and MEMORY (port 51002) runtime services for cross-agent state and recall. These are not independent organs.
