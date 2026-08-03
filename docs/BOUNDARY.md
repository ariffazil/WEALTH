<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-24
valid_from: 2026-07-24
valid_until: 2026-08-17
confidence: high
scope: /root/WEALTH/BOUNDARY.md
-->

# BOUNDARY.md — WEALTH Capital Intelligence

> **DITEMPA BUKAN DIBERI** — WEALTH computes. arifOS judges. Arif decides.

## Owns

- Capital math: NPV, IRR, EMV, EVOI, Monte Carlo, Kelly, Markowitz
- Capital health: conservation, flow, runway, survival, fiscal breakeven
- Market observation: FX, commodities, macro indicators, equities
- Institutional diagnostics: stress, governance capacity, cascades, exploitation patterns
- Entropy analysis when evidence/dependencies are available
- Ledger query and a governed C2/IRREVERSIBLE write path

## Does Not Own

- Constitutional judgment or SEAL authority — arifOS
- Final capital allocation or investment authority — Arif
- Earth-truth modeling — GEOX
- Human readiness — WELL
- Deployment execution — A-FORGE
- Operator cockpit — AAA

## Public MCP Surface

The canonical runtime is `server_federated.py` → `wealth_mcp/server.py`.
Authenticated `tools/list` is final truth.

**8 canonical public tools:**

`capital_primitive`, `capital_health`, `capital_diagnose`, `capital_market`,
`capital_ledger`, `capital_registry`, `capital_entropy`,
`wealth_judge_handoff`

There are **0 public institutional compatibility tools**. `capital_wisdom` and
former institutional names remain only in internal or historical compatibility
contexts; they are not registered or discoverable public MCP tools.

Total public surface: **8**. No hidden aliases are advertised.

## Mutation Boundary

- All public tools compute or observe except `capital_ledger(mode="write")`.
- `capital_ledger` is mapped to C2/IRREVERSIBLE by default.
- `capital_ledger(mode="query")` is explicitly resolved READONLY.
- Write requires arifOS `SEAL` plus `ack_irreversible=true`.
- Persistence must be observed; WEALTH does not invent vault IDs, chain hashes, or receipt success.

## Preserved Compatibility Files

- `internal/monolith.py`
- `internal/engines/canonical_tools.py`
- `internal/engines/five_seals.py`
- `mcp/server.py`

These files are not the canonical public entrypoint but remain required compatibility or supplemental surfaces.
