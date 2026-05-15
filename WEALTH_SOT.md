# WEALTH Organ — Source of Truth
**Status:** `ready` — public and local MCP ingress confirmed on 2026-05-11

## Configuration
- **Canonical Git Source:** `/root/wealth`
- **Canonical Branch:** `main`
- **Repo HEAD at audit:** `cad82c5`
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
| Substrate invariant tools | `12` |
| Diagnostic tools | `2` |
| Runtime surface count | `14` |
| Hidden legacy aliases | `68` |
| Final authority | `ARIF` |
| Caddy upstream | `127.0.0.1:8082` |

## Canonical Public Tool Surface
**Diagnostics (2)**
1. `mcp_health_check` — Universal federation health check
2. `wealth_system_registry_status` — Registry truth diagnostic

**Substrate Invariants (12)**
3. `wealth_conservation_capital` — Ω-WEALTH-01: Conservation (capital stock reality)
4. `wealth_flow_liquidity` — Ω-WEALTH-02: Flow (liquidity movement)
5. `wealth_gradient_price` — Ω-WEALTH-03: Gradient (price pressure, mispricing)
6. `wealth_entropy_risk` — Ω-WEALTH-04: Entropy (uncertainty, tail risk)
7. `wealth_energy_productivity` — Ω-WEALTH-05: Energy (output per input)
8. `wealth_time_discount` — Ω-WEALTH-06: Time (NPV, IRR, payback)
9. `wealth_inertia_leverage` — Ω-WEALTH-07: Inertia (leverage stress, fragility)
10. `wealth_field_macro` — Ω-WEALTH-08: Field (macro environment)
11. `wealth_signal_information` — Ω-WEALTH-09: Signal (info value, evidence quality)
12. `wealth_game_coordination` — Ω-WEALTH-10: Game (multi-agent incentives)
13. `wealth_boundary_governance` — Ω-WEALTH-11: Boundary (floors, stewardship)
14. `wealth_hysteresis_ledger` — Ω-WEALTH-12: Hysteresis (ledger, path dependence)

## Hidden Alias Surface
68 legacy canonical tool names remain callable for backward compatibility but are not advertised in the public MCP surface. They route through the 12 invariant dispatchers internally.

## Operational Doctrine
- Commit long-term source changes to `/root/wealth`.
- The live runtime currently comes from the mounted canonical monolith, not only the image tag.
- Default transport is `streamable-http`; legacy aliases remain callable but are no longer the public truth surface.
- **Doctrine count:** 12 substrate invariants + 2 diagnostics = 14 public tools.
