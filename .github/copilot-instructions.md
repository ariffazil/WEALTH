# WEALTH — Capital Intelligence Organ

WEALTH is the **evidence-only** capital computation organ. It models, quantifies, and governs capital flows. It **never** allocates, invests, or authorizes expenditure alone. Constitutional judgment stays in arifOS.

## Repo identity

- **Path:** `/root/WEALTH`
- **Port:** 18082 | **Domain:** `wealth.arif-fazil.com/mcp`
- **Systemd:** `wealth-organ.service`
- **Language:** Python 3.12 + Node.js 22 (dual runtime)

## Build, test, run

```bash
# Python side (canonical — 44 tools)
pip install -e ".[dev]"
pytest tests/ -q --tb=short          # 153 pass, 10 skip
python internal/monolith.py          # FastMCP server on :18082

# Node.js side (legacy)
npm install && npm test               # node --test tests/*.test.js
npm run boot                          # node cli.js boot

# Redeploy
make forge && systemctl restart wealth-organ
```

## Key directories

| Path | Role |
|------|------|
| `internal/monolith.py` | Canonical 44-tool MCP kernel (~16K lines) |
| `internal/stock/` | D4 Stock Analysis — 12-mode capital-risk |
| `internal/engines/` | canonical_tools.py, five_seals.py, advisory.py |
| `internal/personal_finance.py` | Personal cashflow, EPF, zakat |
| `internal/market_data.py` | Live FX, Brent, World Bank macro |
| `internal/domains/` | Capital and Time domain modules |
| `internal/shared/` | Base classes, shared utilities |
| `capitalx/` | Constitutional capital pricing (Node.js) |
| `tests/` | Python pytest (153 pass) + Node test suite |

## The 12 Ω-WEALTH dimensions

01 Conservation, 02 Flow, 03 Gradient, 04 Entropy, 05 Energy, 06 Time, 07 Inertia, 08 Field, 09 Signal, 10 Game, 11 Boundary, 12 Hysteresis

## Conventions

- `internal/monolith.py` is the canonical kernel. Do NOT add tools to server.py.
- All 44 tools export `mode` parameter for routing. Hidden aliases (34) are internal.
- AGPL-3.0 license (code). README §dir-tree has a stale "PROPRIETARY" comment — ignore it.
- REPO= commit trailer required: `REPO=wealth`
- Tags: `vYYYY.MM.DD` only — never semver counters.

## F1-F13 binding

WEALTH is EVIDENCE_ONLY. It computes → arifOS adjudicates → 888_JUDGE seals.
