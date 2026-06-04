# WEALTH Quickstart — 15 Minutes to Running Locally

> **WEALTH** is the capital intelligence organ of the arifOS federation. It computes value — NPV, IRR, risk scores, portfolio allocation, sovereign resource economics — and enforces constitutional rules that prevent AI from overstating returns or authorizing resource allocation without human approval. It computes. It models. It never allocates alone.

---

## What You'll Have

A running FastMCP server on `http://localhost:18082` exposing 48 capital-intelligence tools.

## Prerequisites

- Python 3.12+
- pip

## Quickstart

```bash
# 1. Clone
git clone https://github.com/ariffazil/wealth.git
cd wealth

# 2. Install
pip install -e .

# 3. Start the canonical server
python internal/monolith.py
```

**That's it.** The server starts on `http://localhost:18082`.

## Verify

```bash
# Health check
curl http://localhost:18082/health | python3 -m json.tool

# Expected: {"status": "healthy", "service": "wealth-mcp", "registry_truth": "PASS"}

# List tools (44+ canonical tools)
curl -s http://localhost:18082/tools | python3 -m json.tool | head -30
```

## Quick Test

```bash
# Compute NPV of a simple cash flow
curl -s -X POST http://localhost:18082/call \
  -H "Content-Type: application/json" \
  -d '{"tool":"wealth_time_discount","args":{"mode":"npv","initial_investment":1000,"cash_flows":[300,400,500,600],"discount_rate":0.1}}' \
  | python3 -m json.tool
```

## Key Tools

| Tool | What It Does |
|------|-------------|
| `wealth_time_discount` | NPV, IRR, payback period |
| `wealth_entropy_risk` | EMV, scenario analysis, tail risk |
| `wealth_omni_wisdom` | Unified synthesis + deal framing + path dependence |
| `wealth_field_macro` | FX rates, commodity prices, macro indicators |
| `wealth_inequality_kernel` | Diagnose structural inequality across 5 dimensions |
| `wealth_game_coordination` | Multi-agent bargaining and game theory |
| `wealth_zakat_calculate` | Malaysian 2.5% zakat calculation |
| `wealth_survival_engine` | Cashflow, runway, burn rate, liquidity |

## Configuration (Optional)

WEALTH works out of the box with no configuration. For advanced features like Supabase ledger integration or live market data, set these environment variables:

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
export WEALTH_SUPABASE_WRITE_MODE="domain"  # enables audit ledger writes
```

## Common Issues

- **ImportError: numpy/scipy** → Run `pip install numpy scipy numpy-financial`
- **Port 18082 in use** → Set `WEALTH_PORT=18084` before starting
- **registry_truth shows degraded** → Normal when running standalone (no federation peers). The tools still work.

## Next Steps

- Read the [arifOS Constitution](https://github.com/ariffazil/arifOS/blob/main/docs/CONSTITUTION.md)
- Set up [GEOX](https://github.com/ariffazil/geox) for Earth intelligence
- Set up [WELL](https://github.com/ariffazil/well) for human readiness
- Read the [Glossary](https://github.com/ariffazil/arifOS/blob/main/docs/GLOSSARY.md)

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
