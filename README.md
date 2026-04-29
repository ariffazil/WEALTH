# 📊 WEALTH — Capital Intelligence Engine

> **Constitutional Capital Allocation Layer for arifOS**
> **DITEMPA BUKAN DIBERI — Forged, Not Given**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](./LICENSE)
[![WEALTH](https://img.shields.io/badge/WEALTH-v2026.04.29-FFFFFF?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDIwIDIwIj48Y2lyY2xlIGN4PSIxMCIgY3k9IjEwIiByPSI4IiBmaWxsPSIjMzMzIi8+PHBhdGggZD0iTTEzLjUsNy41aC0zbC0yLjUsMi41TDkuNSwxMyIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiLz48L3N2Zz4=)](https://github.com/ariffazil/wealth)
[![arifOS](https://img.shields.io/badge/arifOS-Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)

---

## What WEALTH Is

**WEALTH** is the capital allocation intelligence engine in the arifOS organism. It prices reward, survival, entropy, leverage, dignity, coordination, and policy constraints — so that capital decisions can be evaluated before arifOS applies the final constitutional judgment.

WEALTH does not make decisions. It produces **capital intelligence** — NPV, IRR, EMV, crisis triage, civilization stewardship — that arifOS's 888_JUDGE ratifies or voids.

```text
Capital Signal → WEALTH Engine → Intelligence Output → arifOS 888_JUDGE → SEAL/HOLD/VOID
```

**This is not a calculator. This is epistemic capital sovereignty.**

---

## Architecture

WEALTH operates across **11 capital scales** and **7 capital types**:

- **Scales:** personal · household · sme · enterprise · national · crisis · civilization · agentic
- **Capital Types:** financial · temporal · cognitive · social · ecological · strategic · thermodynamic

### MCP Server Surfaces

| Surface | File | Tools | Purpose |
| :--- | :--- | :--- | :--- |
| **Canonical kernel** | `internal/monolith.py` | 33 async tools + 57 sync functions | Core valuation, risk, crisis, coordination |
| **Boot wrapper** | `server.py` | Thin compat wrapper | Points to canonical kernel |
| **Civilizational demo** | `mcp/server.py` | 6 tools | Markets, energy, food security domains |

### Sovereign Pipeline Families (v2 Canonical)

| Family | Stage | Purpose | Primary Tools |
| :--- | :--- | :--- | :--- |
| **SENSE** | 100 | Reality ingestion & observation | `wealth_sense_fetch`, `wealth_sense_snapshot` |
| **MIND** | 200 | Epistemic modeling & Monte Carlo | `wealth_mind_forecast`, `wealth_mind_evoi` |
| **SURVIVAL** | 300 | Solvency & metabolic triage | `wealth_survival_dscr`, `wealth_survival_flow` |
| **REASON** | 400 | Capital discipline & optimization | `wealth_reason_npv`, `wealth_reason_irr` |
| **JUDGE** | 888 | Constitutional gating & audit | `wealth_judge_floors`, `wealth_judge_policy` |
| **VAULT** | 999 | Immutable anchoring & ledger | `wealth_vault_init`, `wealth_vault_seal` |

### MCP Server Tool Inventory (13 Sovereign Primitives + 66 Legacy Aliases)

**V3 Canonical Primitives (`wealth_<verb>_<noun>`):**

These 13 tools subsume all 66 legacy endpoints. Each accepts a `mode` parameter to dispatch to the specific sub-operation.

| Primitive | Modes | Dimension | Temporal Axis |
| :--- | :--- | :--- | :--- |
| `wealth_future_value` | `npv`, `irr`, `pi`, `payback` | Time-Discounted Projection | **Future** |
| `wealth_present_expect` | — | Probability-Weighted Expectation (EMV) | **Present** |
| `wealth_future_simulate` | — | Stochastic Projection (Monte Carlo) | **Future** |
| `wealth_info_value` | `evoi`, `evoi_mc` | Expected Value of Information | **Future** |
| `wealth_truth_validate` | `schema`, `correlation`, `entropy` | Epistemic Integrity | **Present** |
| `wealth_survival_liquidity` | `cashflow`, `velocity`, `triage` | Survival Liquidity | **Present** |
| `wealth_survival_leverage` | `dscr`, `networth` | Structural Load + Balance Sheet | **Present** |
| `wealth_rule_enforce` | `floors`, `policy` | Governance Constraint (F1–F13) | **Present** |
| `wealth_allocate_optimize` | `kernel`, `personal`, `agent` | Capital Allocation Brain | **Future** |
| `wealth_game_coordinate` | `equilibrium`, `game` | Multi-Agent Dynamics | **Future** |
| `wealth_sense_ingest` | `fetch`, `snapshot`, `sources`, `health`, `vintage`, `reconcile` | Reality Intake | **Cross-temporal** |
| `wealth_past_record` | `init`, `transaction`, `portfolio` | Memory & Audit Trail | **Past** |
| `wealth_future_steward` | — | Long-Horizon Planetary Boundaries | **Future** |

**Legacy v1/v2 aliases (66 names)** are preserved for backward compatibility and map to the same underlying functions.

**From `mcp/server.py` (6 cross-domain tools):**

- `wealth_evaluate_prospect` — GEOX prospect economics → WEALTH valuation
- `markets_analyze_ticker` — Market fundamentals analysis
- `markets_portfolio_stress_test` — Portfolio stress testing
- `energy_crisis_assess` — Energy crisis assessment
- `energy_shortage_predict` — Energy shortage prediction
- `food_security_index` — Food security index by country

---

## Capital Intelligence Design

### Dual-Verdict Architecture

WEALTH emits two verdict layers:

| Layer | Field | Purpose |
| :--- | :--- | :--- |
| `verdict` | `allocation_signal` | ACCEPT / REJECT / MARGINAL / INSUFFICIENT_DATA |
| `governance_verdict` | `constitutional_seal` | SEAL / QUALIFY / 888-HOLD / VOID |

**A negative-NPV project returns `verdict=REJECT`, `governance_verdict=SEAL`.**
SEAL means the computation was constitutionally valid — NOT that you should fund it.

### Epistemic States

| State | Meaning | Action |
| :--- | :--- | :--- |
| `CLAIM` | Unverified — awaiting validation | Do not allocate |
| `PLAUSIBLE` | Has evidence, needs corroboration | Allocate with warning |
| `ESTIMATE` | Model-based with uncertainty bounds | P10/P50/P90 range |
| `HYPOTHESIS` | Theory, needs Tri-Witness | HOLD |
| `UNKNOWN` | Insufficient data | 888-HOLD |

### Integrity Score Gating

| Score | Classification | Action |
| :--- | :--- | :--- |
| < 0.3 | **AUTO_HOLD** | Do NOT pass to capital allocation |
| 0.3 – 0.6 | **PLAUSIBLE** | Pass with warning |
| > 0.6 | **CLAIM** | Pass to capital allocation |

### Portfolio Correlation Guard

Tracks `model_lineage_hash` across all prospects. If ≥3 prospects share the same lineage hash:

```json
{"systemic_risk": true, "action": "HOLD — correlated model bias detected"}
```

---

## Quick Start

### Public Surface

| Endpoint | Transport | Purpose |
| :--- | :--- | :--- |
| `/` | HTTP | Static human landing page |
| `/health` | HTTP | JSON health & status |
| `/mcp` | streamable-http | Public MCP endpoint (default) |
| `/sse` | SSE | Optional — set `MCP_TRANSPORT=sse` to enable |

```bash
# Local MCP server (streamable-http default)
python internal/monolith.py
# Or use the backward-compat wrapper:
# python server.py

# Civilizational demo server
python mcp/server.py

# Health check
curl http://localhost:8000/health

# MCP initialize (streamable-http)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}'

# Run tests
npm test
```

---

## Federation Index Map — All Systems

| Layer | System | URL | License | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Ω APPS/MCP** | arifOS Kernel | [mcp.arif-fazil.com](https://mcp.arif-fazil.com) | AGPL-3.0 | Governance runtime |
| **Ω FORGE** | A-FORGE | [forge.arif-fazil.com](https://forge.arif-fazil.com) | AGPL-3.0 | Intelligence forge |
| **Δ THEORY** | APEX | [apex.arif-fazil.com](https://apex.arif-fazil.com) | AGPL-3.0 | Constitutional theory |
| **Δ AAA** | AAA Workspace | [aaa.arif-fazil.com](https://aaa.arif-fazil.com) | — | arifOS workspace |
| **Ψ HUMAN** | Arif Hub | [arif-fazil.com](https://arif-fazil.com) | — | Personal hub |
| **⚡ GEOX** | Physics9 Earth | [geox.arif-fazil.com](https://geox.arif-fazil.com) | Apache 2.0 | Earth intelligence |
| **📊 WEALTH** | This System | [waw.arif-fazil.com](https://waw.arif-fazil.com) | Apache 2.0 | Capital allocation |

| arifOS Floor Doc | Path |
| :--- | :--- |
| 888_JUDGE | [docs/wiki/arifos/888_JUDGE.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/888_JUDGE.md) |
| 999_VAULT | [docs/wiki/arifos/999_VAULT.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/999_VAULT.md) |
| FLOORS | [docs/wiki/arifos/FLOORS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/FLOORS.md) |
| VERDICTS | [docs/wiki/arifos/VERDICTS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/VERDICTS.md) |
| WEALTH HARNESS | [canon/WEALTH_HARNESS.md](https://github.com/ariffazil/wealth/blob/main/canon/WEALTH_HARNESS.md) |

---

## Project Structure

```text
WEALTH/
├── internal/monolith.py   ← Canonical MCP kernel (13 primitives + 66 legacy aliases)
├── server.py              ← Backward-compat wrapper (points to canonical)
├── mcp/server.py          ← Civilizational demo surface (6 tools)
├── host/
│   └── governance/        ← Floor enforcement, vault, policy engine
├── api/
│   └── schemas/
│       └── wealth-mcp-tools.json   ← Tool manifest + envelope schema
├── canon/
│   └── WEALTH_HARNESS.md  ← Harness architecture spec
├── capitalx/              ← CapitalX pricing engine design
├── domains/               ← Market, energy, food domain adapters
├── wiki/                  ← Architecture documentation
└── tests/                 ← Node test suite
```

---

## License

**Apache 2.0** — Commercial embedding allowed. Attribution required.
See [LICENSE](./LICENSE)

WEALTH is the commercial capital layer — Apache 2.0 allows companies to embed WEALTH in proprietary systems without exposing their full stack.

---

## GitHub Repos

| Repo | URL |
| :--- | :--- |
| WEALTH | https://github.com/ariffazil/wealth |
| arifOS | https://github.com/ariffazil/arifOS |
| GEOX | https://github.com/ariffazil/geox |
| A-FORGE | https://github.com/ariffazil/A-FORGE |
| AAA | https://github.com/ariffazil/AAA |

---

> *"Ruang untuk rasa, batas untuk selamat."*

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
`VAULT999 | Capital Intelligence | Alignment: ΔΩΨ | 11 Tools Exposed`