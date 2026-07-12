# CLAUDE.md — WEALTH Agent Instructions

> **Canonical agent instruction file:** `/root/AAA/CLAUDE.md`
> **WEALTH organ** of the arifOS federation.
> **Port:** 18082 | **Version:** 2026.07.12 | **Transport:** streamable-http

## What WEALTH Is

The **capital intelligence organ** of the arifOS federation. It computes:

- **D1 Personal Finance** — cashflow, net worth, EPF, zakat, runway
- **D3 Market Data** — FX rates, commodities, macro indicators (delegates to `internal/market_data.py`)
- **D4 Stock Analysis** — 12-mode capital-risk governance (verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence)
- **Ω-domain physics** — conservation, flow, gradient, entropy, energy, time, inertia, field, signal, game, boundary, hysteresis
- **Collapse Signature** — enron corpus + institutional failure forensics

**Canonical MCP tools** (verify with `tools/list` at runtime). Internal alias tools for routing only.
Canonical FastMCP server at `internal/monolith.py`.

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
pytest tests/ -q --tb=short          # Python tests
npm test                              # Node.js legacy tests
npm run boot                          # node cli.js boot
```

## Health Check

```bash
systemctl status wealth-organ
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
```

## Federation Position (canonical organ map)

```
Arif (F13 SOVEREIGN)
    ↓
AAA / Hermes / OpenClaw (A2A)
    ↓
arifOS KERNEL (F1-F13, :8088)
    ↓
WEALTH (CAPITAL, :18082)  ← computes, never allocates
    ↓
A-FORGE (:7071)  ← executes after SEAL
    ↓
VAULT999  ← immutable record
```

WEALTH provides **evidence-only**. It computes. It never allocates, never executes, never judges.

## Key Directories

| Path | Purpose |
|------|---------|
| `internal/monolith.py` | Canonical kernel — public MCP surface |
| `internal/stock/` | D4 Stock Analysis — 12 modes |
| `internal/market_data.py` | D3 FX/commodities/macro |
| `internal/personal_finance.py` | D1 cashflow/EPF/zakat |
| `internal/engines/` | Advisory, five seals, canonical tools |
| `wealth_core/collapse_signature/` | Enron corpus + institutional failure forensics |
| `src/` | Legacy JS/Node kernel |
| `capitalx/` | Constitutional capital pricing engine |
| `host/` | Modular Python libraries |

## Stale SOT Files

- ~~CLAUDE.md~~ — ✅ Updated 2026-07-01
- ~~RUNBOOK.md~~ — ✅ Updated 2026-07-01

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**
