# WEALTH Organ — Source of Truth
**Status:** `ready` — public and local MCP ingress confirmed on 2026-05-11

## Configuration
- **Canonical Git Source:** `/root/wealth`
- **Canonical Branch:** `main`
- **Repo HEAD at audit:** `f040a3b`
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
| Canonical public tools | `50` |
| Runtime surface count | `50` |
| Hidden legacy aliases | `68` |
| Final authority | `ARIF` |
| Caddy upstream | `127.0.0.1:8082` |

## Canonical Public Tool Surface
**Sense (7)**
1. `mcp_health_check`
2. `wealth_sense_fetch`
3. `wealth_sense_health`
4. `wealth_sense_ingest`
5. `wealth_sense_reconcile`
6. `wealth_sense_snapshot`
7. `wealth_sense_sources`
8. `wealth_sense_vintage`

**Mind (6)**
9. `wealth_mind_correlation`
10. `wealth_mind_emv`
11. `wealth_mind_evoi`
12. `wealth_mind_evoi_mc`
13. `wealth_mind_monte_carlo`
14. `wealth_mind_schema`

**Survival (8)**
15. `wealth_survival_cashflow`
16. `wealth_survival_civilization`
17. `wealth_survival_dscr`
18. `wealth_survival_leverage`
19. `wealth_survival_liquidity`
20. `wealth_survival_networth`
21. `wealth_survival_triage`
22. `wealth_survival_velocity`

**Reason (9)**
23. `wealth_npv_reward`
24. `wealth_reason_agent`
25. `wealth_reason_equilibrium`
26. `wealth_reason_game`
27. `wealth_reason_irr`
28. `wealth_reason_npv`
29. `wealth_reason_payback`
30. `wealth_reason_personal`
31. `wealth_reason_pi`

**Judge (4)**
32. `wealth_judge_entropy`
33. `wealth_judge_floors`
34. `wealth_judge_kernel`
35. `wealth_judge_policy`

**Vault (3)**
36. `wealth_vault_init`
37. `wealth_vault_record`
38. `wealth_vault_snapshot`

**Future (3)**
39. `wealth_future_simulate`
40. `wealth_future_steward`
41. `wealth_future_value`

**Allocate / Game / Info / Truth / Rule / Past / Present**
42. `wealth_allocate_optimize`
43. `wealth_game_coordinate`
44. `wealth_info_value`
45. `wealth_past_record`
46. `wealth_present_expect`
47. `wealth_rule_enforce`
48. `wealth_truth_validate`

**Cross-organ Vault**
49. `vault_query`
50. `vault_write`

## Operational Doctrine
- Commit long-term source changes to `/root/wealth`.
- The live runtime currently comes from the mounted canonical monolith, not only the image tag.
- Default transport is `streamable-http`; legacy aliases remain callable but are no longer the public truth surface.
