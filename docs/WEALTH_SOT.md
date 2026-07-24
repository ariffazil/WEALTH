# WEALTH Organ — Source of Truth
**Status:** `source-aligned` — runtime restart/deploy was not part of this change

## Configuration
- **Canonical Git Source:** `/root/WEALTH`
- **Canonical Branch:** `main`
- **Runtime Entrypoint:** `server_federated.py`
- **FastMCP Registration:** `wealth_mcp/server.py`
- **Legacy Implementation Library:** `internal/monolith.py` (not the public entrypoint)
- **Supplemental Surface:** `mcp/server.py` (demo / non-canonical)

## Public Surface
- `/health` — JSON federation health and identity metadata
- `/tools` — live public tool names
- `/mcp` — MCP streamable-http endpoint

## MCP Runtime Truth
| Field | Value |
|---|---|
| Public URL | `https://wealth.arif-fazil.com/mcp` |
| Transport | streamable-http |
| Health | `https://wealth.arif-fazil.com/health` |
| Canonical capital tools | `8` |
| Institutional compatibility tools | `4` |
| Public surface count | `12` |
| Hidden aliases | `0` advertised |
| Final authority | `ARIF` |
| Caddy upstream | `127.0.0.1:18082` |

## Canonical Capital Family (8)
1. `capital_primitive`
2. `capital_health`
3. `capital_diagnose`
4. `capital_wisdom`
5. `capital_market`
6. `capital_ledger`
7. `capital_registry`
8. `capital_entropy`

## Institutional Compatibility Family (4)
9. `wealth_institutional_stress_index`
10. `wealth_cascade_model`
11. `wealth_governance_capacity`
12. `wealth_external_exploitation_detect`

## Governance
- `capital_ledger` defaults to C2/IRREVERSIBLE; `mode="query"` is resolved read-only.
- Ledger writes require both arifOS `SEAL` and `ack_irreversible=true`.
- Receipt and ledger persistence failures are returned as observable metadata; missing targets are never created implicitly.
- `capital_entropy` reports a structured `UNAVAILABLE` envelope if its optional dependency is absent from this repository.

## Operational Doctrine
- Authenticated `tools/list` and `/health` beat every static count.
- `/health` reports a Git SHA only when it can read the source repository; `.git_commit` is exposed solely as an unverified fallback.
- WEALTH computes. arifOS judges. Arif decides.

