# WEALTH — Capital Intelligence Organ

WEALTH is the **compute-only** capital intelligence organ. It models and quantifies capital flows. It **never** allocates, invests, or authorizes expenditure alone. Constitutional judgment stays in arifOS.

## Repo identity

- **Path:** `/root/WEALTH`
- **Port:** 18082 | **Domain:** `wealth.arif-fazil.com/mcp`
- **Systemd:** `wealth-organ.service`
- **Language:** Python 3.12 + Node.js 22 (legacy side)
- **Tool surface:** 8 canonical public MCP tools

## Build, test, run

```bash
pip install -e ".[dev]"
pytest tests/ -q --tb=short
python server_federated.py             # FastMCP server on :18082

# Node.js side (legacy)
npm install && npm test
npm run boot
```

Do not restart or deploy without a verified test pass.

## Key directories

| Path | Role |
|------|------|
| `server_federated.py` | Canonical HTTP entrypoint |
| `wealth_mcp/server.py` | FastMCP registration, governance, receipts, resources |
| `wealth_mcp/tools/canonical.py` | 8 canonical public tools plus internal engines |
| `wealth_mcp/tools/institutional.py` | Internal institutional engines; no public registrations |
| `internal/monolith.py` | Legacy implementation library; keep for compatibility |
| `internal/stock/` | D4 Stock Analysis |
| `internal/engines/` | canonical_tools.py, five_seals.py, advisory.py |
| `tests/` | Python pytest + Node test suite |

## Conventions

- `tools/list` and `/health` beat static prose.
- `capital_ledger(mode="write")` is C2/IRREVERSIBLE; query is read-only.
- `capital_entropy` must report UNAVAILABLE when its in-repo optional dependency is absent.
- `capital_wisdom` and former institutional names are internal/historical only,
  not public `tools/list` entries.
- AGPL-3.0 license (code and packaging).
- Tags: `vYYYY.MM.DD` only — never semver counters.
- WEALTH computes → arifOS adjudicates → Arif decides.
