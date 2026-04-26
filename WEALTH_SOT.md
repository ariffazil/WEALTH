# WEALTH Organ — Source of Truth
**Status:** Canonical Realignment Complete

## Configuration
- **Canonical Git Source:** `/root/WEALTH`
- **Deployment Mirror:** `/opt/arifos/src/wealth`
- **Runtime Entrypoint:** `server.py`
- **Supplemental Surface:** `mcp/server.py`

## Exposure Status
- **Public Status:** Static Site + SSE only.
- **MCP Endpoint:** `/mcp` is routed at Caddy but upstream returns 404. It remains **UNSEALED**.

## Operational Doctrine
- All long-term source changes MUST be committed to `/root/WEALTH`.
- `/opt/arifos/src/wealth` serves as the active build context and deployment target.
