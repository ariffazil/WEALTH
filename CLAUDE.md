# CLAUDE.md — WEALTH Agent Instructions

> **Canonical agent instruction file:** `/root/AAA/CLAUDE.md`
> **WEALTH organ** of the arifOS federation.
> **Port:** 18082 | **Version:** 2026.06.15 | **Transport:** streamable-http

## What WEALTH Is

The **capital intelligence organ** of the arifOS federation. It computes:

- **D1 Personal Finance** — cashflow, net worth, EPF, zakat, runway
- **D3 Market Data** — FX rates, commodities, macro indicators (delegates to `internal/market_data.py`)
- **D4 Stock Analysis** — 12-mode capital-risk governance (verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence)
- **Ω-domain physics** — conservation, flow, gradient, entropy, energy, time, inertia, field, signal, game, boundary, hysteresis
- **Collapse Signature** — enron corpus + institutional failure forensics

**20 public MCP tools** + **34 hidden alias tools** (internal routing only).
Canonical FastMCP server at `internal/monolith.py` (657KB, ~16K lines, 83 tool decorators).

## Authority & Autonomy

### Autonomous
- Modify Python/JS logic, add tools, refactor
- Run tests, fix bugs, update schemas
- Restart service (systemctl restart wealth-organ)

### Requires 888_HOLD
- Cross-repo API contract changes
- Adding buy/sell oracle tools (WEALTH computes, Arif decides)
- Production deploy without verified build + test pass

## Build & Test

```bash
cd /root/WEALTH
uv sync --frozen
python internal/monolith.py          # Start canonical server (port 18082)
pytest tests/ -q --tb=short          # Python tests (153 pass)
npm test                              # Node.js legacy tests
npm run boot                          # node cli.js boot
```

## Health Check

```bash
systemctl status wealth-organ
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
```

## Federation Position

```
arifOS (Ω Law :8088) → WEALTH (Capital :18082) → A-FORGE (Ψ Execution :7071) → VAULT999 (:8100)
```

WEALTH provides **evidence-only**. It computes. It never allocates, never executes, never judges.

## Key Directories

| Path | Purpose |
|------|---------|
| `internal/monolith.py` | Canonical kernel — 83 tool-like functions, 20 public MCP surface |
| `internal/stock/` | D4 Stock Analysis — 12 modes |
| `internal/market_data.py` | D3 FX/commodities/macro |
| `internal/personal_finance.py` | D1 cashflow/EPF/zakat |
| `internal/engines/` | Advisory, five seals, canonical tools |
| `wealth_core/collapse_signature/` | Enron corpus + institutional failure forensics |
| `src/` | Legacy JS/Node kernel |
| `capitalx/` | Constitutional capital pricing engine |
| `host/` | Modular Python libraries |

## Stale SOT Files

- ~~CLAUDE.md~~ — ✅ Updated 2026-06-21
- ~~RUNBOOK.md~~ — ✅ Updated 2026-06-21

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**
