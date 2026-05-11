# WEALTH Organ — Source of Truth
**Status:** `ready` — public and local MCP ingress confirmed on 2026-05-11

## Configuration
- **Canonical Git Source:** `/root/wealth`
- **Canonical Branch:** `main`
- **Repo HEAD at audit:** `d6c4e44`
- **Runtime Entrypoint:** `internal/monolith.py` (mounted into `wealth-organ`)
- **Backward-Compat Wrapper:** `server.py`
- **Supplemental Surface:** `mcp/server.py` (demo / non-canonical)

## Public Surface
- `/` — Static human landing page
- `/health` — JSON health endpoint
- `/ready` — JSON readiness endpoint
- `/tools` — tool discovery and registry truth view
- `/mcp` — live MCP streamable-http endpoint

## MCP Runtime Truth
| Field | Value |
|---|---|
| Public URL | `https://wealth.arif-fazil.com/mcp` |
| Transport | streamable-http |
| Health | `https://wealth.arif-fazil.com/health` |
| Ready | `https://wealth.arif-fazil.com/ready` |
| Schema version | `wealth.physics_economics.v1` |
| Canonical public tools | `14` |
| Runtime surface count | `14` |
| Hidden legacy aliases | `68` |
| Final authority | `ARIF` |
| Caddy upstream | `127.0.0.1:8082` |

## Canonical Public Tool Surface
1. `mcp_health_check`
2. `wealth_conservation_capital`
3. `wealth_flow_liquidity`
4. `wealth_gradient_price`
5. `wealth_entropy_risk`
6. `wealth_energy_productivity`
7. `wealth_time_discount`
8. `wealth_inertia_leverage`
9. `wealth_field_macro`
10. `wealth_signal_information`
11. `wealth_game_coordination`
12. `wealth_boundary_governance`
13. `wealth_hysteresis_ledger`
14. `wealth_system_registry_status`

## Operational Doctrine
- Commit long-term source changes to `/root/wealth`.
- The live runtime currently comes from the mounted canonical monolith, not only the image tag.
- Default transport is `streamable-http`; legacy aliases remain callable but are no longer the public truth surface.
