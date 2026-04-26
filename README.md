# 📊 WEALTH — Capital Intelligence Engine

> **Constitutional Capital Allocation Layer for arifOS**
> DITEMPA BUKAN DIBERI — Forged, Not Given

[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](./LICENSE)
[![WEALTH](https://img.shields.io/badge/WEALTH-v1.6-FFFFFF?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZh0PSIyMCIgdmlld0JveD0iMCAwIDIwIDIwIj48Y2lyY2xlIGN4PSIxMCIgY3k9IjEwIiByPSI4IiBmaWxsPSIjMzMzIi8+PHBhdGggZD0iTTEzLjUsNy41aC0zbC0yLjUsMi41TDkuNSwxMyIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiLz48L3N2Zz4=)](https://github.com/ariffazil/wealth)
[![arifOS](https://img.shields.io/badge/arifOS-Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)

---

## What WEALTH Is

WEALTH is the **capital allocation intelligence engine** in the arifOS organism. It prices reward, survival, entropy, leverage, dignity, coordination, and policy constraints — so that capital decisions can be evaluated before arifOS applies the final constitutional judgment.

WEALTH does not make decisions. It produces **capital intelligence** — NPV, IRR, EMV, crisis triage, civilization stewardship — that arifOS's 888_JUDGE ratifies or voids.

```
Capital Signal → WEALTH Engine → Intelligence Output → arifOS 888_JUDGE → SEAL/HOLD/VOID
```

**This is not a calculator. This is epistemic capital sovereignty.**

---

## Architecture

WEALTH operates across **11 capital scales** and **7 capital types**:

**Scales:** personal · household · sme · enterprise · national · crisis · civilization · agentic

**Capital Types:** financial · temporal · cognitive · social · ecological · strategic · thermodynamic

### MCP Server Surfaces

| Surface | File | Tools | Purpose |
|---|---|---|---|
| **Canonical kernel** | `server.py` | 33 async tools + 57 sync functions | Core valuation, risk, crisis, coordination |
| **Civilizational demo** | `mcp/server.py` | 6 tools | Markets, energy, food security domains |

### Core Tool Families (from `api/schemas/wealth-mcp-tools.json`)

| Family | Tools | Purpose |
|---|---|---|
| `wealth.state` | networth_state, cashflow_flow | Personal/enterprise balance sheet |
| `wealth.risk` | npv_reward, irr_yield, pi_efficiency, emv_risk, audit_entropy | Capital risk evaluation |
| `wealth.price` | capitalx, dscr_leverage, growth_velocity | Price signals across scales |
| `wealth.flow` | monte_carlo_forecast, ingest_* | Cashflow projection and ingestion |
| `wealth.crisis` | crisis_triage, civilization_stewardship | Crisis-mode capital response |
| `wealth.coordination` | coordination_equilibrium, game_theory_solve | Multi-agent coordination |
| `wealth.control` | check_floors_tool, policy_audit | Constitutional floor enforcement |
| `wealth.personal` | personal_decision, agent_budget | Personal capital decisions |
| `wealth.agentic` | wealth_score_kernel, wealth_evoi_compute | Agent-level capital intelligence |

### MCP Server Tool Inventory (11 Exposed Tools)

**From `server.py`:**
- `wealth_evoi_compute` — Expected Value of Information
- `wealth_evoi_monte_carlo` — Monte Carlo EVOI simulation
- `wealth_correlation_guard_check` — Portfolio correlation risk guard
- `wealth_schema_validate` — Schema validation for capital envelopes
- `wealth_init_tool` — Session initialization

**From `mcp/server.py` (Civilizational Demo):**
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
|---|---|---|
| `verdict` | allocation_signal | ACCEPT / REJECT / MARGINAL / INSUFFICIENT_DATA |
| `governance_verdict` | constitutional_seal | SEAL / QUALIFY / 888-HOLD / VOID |

**A negative-NPV project returns `verdict=REJECT`, `governance_verdict=SEAL`.**
SEAL means the computation was constitutionally valid — NOT that you should fund it.

### Epistemic States

| State | Meaning | Action |
|---|---|---|
| `CLAIM` | Unverified — awaiting validation | Do not allocate |
| `PLAUSIBLE` | Has evidence, needs corroboration | Allocate with warning |
| `ESTIMATE` | Model-based with uncertainty bounds | P10/P50/P90 range |
| `HYPOTHESIS` | Theory, needs Tri-Witness | HOLD |
| `UNKNOWN` | Insufficient data | 888-HOLD |

### Integrity Score Gating

| Score | Classification | Action |
|---|---|---|
| < 0.3 | **AUTO_HOLD** | Do NOT pass to capital allocation |
| 0.3 – 0.6 | **PLAUSIBLE** | Pass with warning |
| > 0.6 | **CLAIM** | Pass to capital allocation |

### Portfolio Correlation Guard

Tracks `model_lineage_hash` across all prospects. If ≥3 prospects share the same lineage hash:

```
{"systemic_risk": true, "action": "HOLD — correlated model bias detected"}
```

---

## Quick Start

```bash
# Local MCP server
python server.py

# Civilizational demo server
python mcp/server.py

# Health check
curl http://localhost:8000/health

# Run tests
npm test
```

---

## Federation Index Map — All Systems

| Layer | System | URL | License | Purpose |
|---|---|---|---|---|
| **Ω APPS/MCP** | arifOS Kernel | [mcp.arif-fazil.com](https://mcp.arif-fazil.com) | AGPL-3.0 | Governance runtime |
| **Ω FORGE** | A-FORGE | [forge.arif-fazil.com](https://forge.arif-fazil.com) | AGPL-3.0 | Intelligence forge |
| **Δ THEORY** | APEX | [apex.arif-fazil.com](https://apex.arif-fazil.com) | AGPL-3.0 | Constitutional theory |
| **Δ AAA** | AAA Workspace | [aaa.arif-fazil.com](https://aaa.arif-fazil.com) | — | arifOS workspace |
| **Ψ HUMAN** | Arif Hub | [arif-fazil.com](https://arif-fazil.com) | — | Personal hub |
| **⚡ GEOX** | Physics9 Earth | [geox.arif-fazil.com](https://geox.arif-fazil.com) | Apache 2.0 | Earth intelligence |
| **📊 WEALTH** | This System | [waw.arif-fazil.com](https://waw.arif-fazil.com) | Apache 2.0 | Capital allocation |

| arifOS Floor Doc | Path |
|---|---|
| 888_JUDGE | [docs/wiki/arifos/888_JUDGE.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/888_JUDGE.md) |
| 999_VAULT | [docs/wiki/arifos/999_VAULT.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/999_VAULT.md) |
| FLOORS | [docs/wiki/arifos/FLOORS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/FLOORS.md) |
| VERDICTS | [docs/wiki/arifos/VERDICTS.md](https://github.com/ariffazil/AAA/blob/main/docs/wiki/arifos/VERDICTS.md) |
| WEALTH HARNESS | [canon/WEALTH_HARNESS.md](https://github.com/ariffazil/wealth/blob/main/canon/WEALTH_HARNESS.md) |

---

## Project Structure

```
WEALTH/
├── server.py              ← Canonical MCP kernel (33 exposed tools)
├── mcp/server.py         ← Civilizational demo surface (6 tools)
├── host/
│   └── governance/        ← Floor enforcement, vault, policy engine
├── api/
│   └── schemas/
│       └── wealth-mcp-tools.json   ← Tool manifest + envelope schema
├── canon/
│   └── WEALTH_HARNESS.md  ← Harness architecture spec
├── capitalx/             ← CapitalX pricing engine design
├── domains/              ← Market, energy, food domain adapters
├── wiki/                 ← Architecture documentation
└── tests/                ← Node test suite
```

---

## License

**Apache 2.0** — Commercial embedding allowed. Attribution required.
See [LICENSE](./LICENSE)

WEALTH is the commercial capital layer — Apache 2.0 allows companies to embed WEALTH in proprietary systems without exposing their full stack.

---

## GitHub Repos

| Repo | URL |
|---|---|
| WEALTH | https://github.com/ariffazil/wealth |
| arifOS | https://github.com/ariffazil/arifOS |
| GEOX | https://github.com/ariffazil/geox |
| A-FORGE | https://github.com/ariffazil/A-FORGE |
| AAA | https://github.com/ariffazil/AAA |

---

> *"Ruang untuk rasa, batas untuk selamat."*

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
`VAULT999 | Capital Intelligence | Alignment: ΔΩΨ | 11 Tools Exposed`