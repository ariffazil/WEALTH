# WEALTH Organ — Source of Truth
**Status:** Temporary Runtime Allocation

## Configuration
- **Current Runtime SOT:** `/opt/arifos/src/wealth`
- **Deployment Source:** This path is the active build source for Docker.
- **Divergence:** `/root/WEALTH` is currently a secondary development path and is NOT the active deployment source.

## Exposure Status
- **Public Status:** Static Site + SSE only.
- **MCP Endpoint:** `/mcp` is routed at Caddy but returns 404 upstream. It remains **UNSEALED**.
- **Protocols:** Do not claim full MCP health until upstream serves a valid handshake.

## Next Steps
- Arif to decide on final canonical GitHub SOT reconciliation.
