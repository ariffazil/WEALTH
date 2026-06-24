# WEALTH Quickstart — 15 Minutes to Running Locally

> **WEALTH** is the capital intelligence organ of the arifOS federation.
> It computes value — NPV, IRR, EMV, risk scores, portfolio allocation,
> sovereign resource economics — and enforces constitutional rules that
> prevent AI from overstating returns or authorizing resource allocation
> without human approval. It computes. It models. It never allocates alone.

---

## What You'll Have

A running FastMCP server on `http://localhost:18082` exposing
**24 public capital-intelligence tools** (verified via
`wealth_system_registry_status` 2026-06-24).

## Prerequisites

- Python 3.12+
- pip / uv

## Quickstart

```bash
# 1. Clone
git clone https://github.com/ariffazil/wealth.git
cd wealth

# 2. Install
uv sync --frozen        # canonical
# or: pip install -e .

# 3. Start the canonical server
python internal/monolith.py
```

**That's it.** The server starts on `http://localhost:18082`.

## Verify

```bash
# Health check
curl -s http://localhost:18082/health | python3 -m json.tool
# Expected: {"status": "ALIVE", "version": "2026.06.15", "domain": "WEALTH Federated Domain", ...}

# Live tool count (single source of truth)
curl -s -X POST http://127.0.0.1:18082/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_system_registry_status","arguments":{"mode":"registry"}},"id":1}' \
  | python3 -m json.tool | grep -E "public_tools"
```

## The 24 Public Tools (live, verified 2026-06-24)

### Core capital primitives (the 13 thermodynamics primitives)

| Tool | Primitive | What it computes |
|------|-----------|------------------|
| `wealth_conservation_check` | Conservation | Assets = Liabilities + Equity, net worth |
| `wealth_flow_check` | Flow | Income / expense / monthly burn |
| `wealth_asymmetry_check` | Boundary | Skew detection in upside/downside distributions |
| `wealth_compute_emv` | Entropy | Expected Monetary Value with variance + std dev |
| `wealth_compute_irr` | Energy | Internal Rate of Return |
| `wealth_compute_npv` | Time | Net Present Value of cash flows |
| `wealth_monte_carlo_simulate` | Inertia | Monte Carlo value projection |
| `wealth_market_data` | Field | FX, commodities, macro indicators |
| `wealth_compute_evoi` | Signal | Expected Value of Information |
| `wealth_confluence_check` | Game | False-confluence detection in indicators |
| `wealth_omni_wisdom` | Game + Hysteresis | Unified synthesis, deal framing, path params |
| `wealth_wisdom_evaluate` | Wisdom | 6-dim wisdom (dignity, sovereignty, resilience, inequality, ecological, optionality) |
| `wealth_runway_check` | Survival | Runway in months |

### Risk + governance

| Tool | What it does |
|------|-------------|
| `wealth_capture_scan` | Audit AI-generated financial advice for capture signals (incentive asymmetry, hidden incentives, false precision, time pressure, authority without evidence) |
| `wealth_power_audit` | Audit scenario power dynamics (incentive map, capture risk, rent extraction, opacity, coercion, rule asymmetry) |

### Personal finance (D1) + market data (D3)

| Tool | What it does |
|------|-------------|
| `wealth_personal_finance` | Cashflow, net worth, EPF, zakat, runway summary |
| `wealth_market_data` | FX rates, commodities, macro indicators (MYS / global) |

### Stock analysis (D4 — 12 modes)

| Tool | Modes |
|------|-------|
| `wealth_stock_analysis` | verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence, +6 more |

### Orchestration + memory

| Tool | What it does |
|------|-------------|
| `wealth_omni_wisdom` | `synthesize` / `deal_frame` / `path_params` — multi-mode capital intelligence |
| `wealth_agent_path` | Sovereign Intent Router — classifies task into L1/L2 paths |
| `wealth_system_registry_status` | Live registry truth (intended vs registered vs callable) |
| `wealth_vault_write` | Write to VAULT999 ledger (irreversible — requires human confirmation) |
| `wealth_vault_query` | Query VAULT999 ledger |

## Quick Test

```bash
# NPV — basic discounted cash flow
curl -s -X POST http://localhost:18082/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_compute_npv","arguments":{"cash_flows":[-1000,300,400,500,600],"discount_rate":0.1}},"id":1}' \
  | python3 -m json.tool

# Runway — survival
curl -s -X POST http://localhost:18082/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_runway_check","arguments":{"liquid_assets":100000,"monthly_burn":5000}},"id":2}' \
  | python3 -m json.tool

# Capture scan — audit an advice
curl -s -X POST http://localhost:18082/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_capture_scan","arguments":{"advice_text":"Buy X now, urgent window, guaranteed return","source_model":"user"}},"id":3}' \
  | python3 -m json.tool
```

## MCP Resources (3 live)

| URI | What it provides |
|-----|------------------|
| `afwealth://schema` | Pydantic schema reference |
| `afwealth://health` | Live health probe |
| `afwealth://tools/registry` | Live tool registry truth |

## Configuration (Optional)

WEALTH works out of the box. For advanced features:

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
export WEALTH_SUPABASE_WRITE_MODE="domain"  # enables VAULT999 ledger writes
```

## Related Skills (load before complex tasks)

| Skill | When to load |
|-------|--------------|
| `wealth-capital-thermodynamics` | Multi-primitive analysis (NPV + EMV + EVOI, runway + risk, deal framing) |
| `wealth-collapse-signature` | Institutional failure forensics (Petronas, sovereign, GE16, "calm before") |
| `wealth-law-anthropology` | Malaysian law (pusaka, faraid, KTN, MA63, Syariah, NCR) |

## Common Issues

| Symptom | Fix |
|---------|-----|
| `ImportError: numpy/scipy` | `uv pip install numpy scipy numpy-financial` |
| Port 18082 in use | `WEALTH_PORT=18084 python internal/monolith.py` |
| `registry_truth: degraded` | Normal standalone (no federation peers); tools still work |
| D4 stock analysis 888_HOLD | Populate `wealth.trades` table |
| `uv sync` failing | `uv sync` (not `--frozen`) to regenerate lock |

## Next Steps

- Read [`arifOS/AGENTS.md`](https://github.com/ariffazil/arifOS/blob/main/AGENTS.md) for federation rules
- Read [`FEDERATION_CONTRACT.md`](./FEDERATION_CONTRACT.md) for organ authority
- Set up [`GEOX`](https://github.com/ariffazil/geox) for Earth intelligence
- Set up [`WELL`](https://github.com/ariffazil/well) for human readiness
- Read the [Glossary](https://github.com/ariffazil/arifOS/blob/main/docs/GLOSSARY.md)

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**

*Tool surface last reconciled: 2026-06-24 (per `wealth_system_registry_status` live query).*
