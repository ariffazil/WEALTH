<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.08.25
last_verified: 2026-08-25T04:30:00Z
live_commit: f714140
tools_live: 11 (canonical, live-witnessed via :18082/health)
resources: 18
prompts: 7
authority_ceiling: 555_COMPUTE_ONLY
truth_rule: live :18082/health + tools/list beat any static count in prose
-->

# WEALTH — Capital Intelligence Engine

## AI-driven capital health, market intelligence, and financial decision engine.

WEALTH transforms capital flows, markets, incentives, and risk into auditable evidence. It answers the questions that matter before money moves: *Where is institutional failure beginning? What is the downside nobody is pricing? Who benefits? Who pays?*

**WEALTH computes. arifOS judges. Humans decide.**

Licensed under **AGPL-3.0**.

---

## The Problem

Organizations rarely fail because they lack spreadsheets. They fail because:
- Risk accumulates unseen until it's too late
- Incentive structures drift away from stated goals
- Governance erodes silently over quarters and years
- Reporting diverges from reality without anyone noticing

Traditional financial tools show you prices and charts. They don't show you the structural rot underneath.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    WEALTH Capital Engine                      │
│  Port :18082  ·  MCP Interface  ·  11 Tools  ·  18 Resources│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  Capital     │  │   Market     │  │   Entropy          │ │
│  │ Diagnostics  │  │   Pulse      │  │   Modeling         │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘ │
│         │                 │                     │           │
│  ┌──────▼─────────────────▼─────────────────────▼──────────┐│
│  │              WEALTH Compute Core                         ││
│  │  NPV · IRR · EMV · Scenario Stress · Monte Carlo        ││
│  └──────────────────────────┬──────────────────────────────┘│
│                             │                               │
│  ┌──────────────┐  ┌───────▼───────┐  ┌──────────────────┐ │
│  │  Entry Plan  │  │   Backtest    │  │  Ledger & Runway │ │
│  │  (S/R aware) │  │   Engine      │  │  Tracking        │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │ MCP
                    ┌──────▼──────┐
                    │  arifOS FED  │
                    │  :7080 MCP   │
                    └─────────────┘
```

---

## Quick Start

### Docker

```bash
git clone https://github.com/arif-fazil/WEALTH.git
cd WEALTH
docker compose up -d

# Verify
curl http://localhost:18082/health
curl http://localhost:18082/tools/list
```

### Local Development

```bash
cd WEALTH
pip install -e .
python -m wealth.server --port 18082
```

---

## Capabilities

### Capital Diagnostics
- NPV, IRR, EMV computation with scenario stress
- Capital health monitoring across portfolios
- Concentration risk identification
- Downside exposure analysis

### Market Intelligence
- Real-time FX, commodity, and stock indicators
- Technical analysis: EMA, SMA, RSI, MACD, Bollinger Bands, PSAR, ATR, ADX
- XAUUSD (gold) market analysis
- Commodity price monitoring and alerts

### Entropy Modeling
- Institutional decay detection
- Narrative vs. reality divergence scoring
- Incentive structure mapping
- Governance capacity assessment

### Entry Planning
- Support/resistance-aware entry, stop, and target computation
- Strategy backtesting with enhanced metrics
- Risk/reward ratio analysis
- Monte Carlo simulation

### Ledger & Runway
- Immutable capital ledger tracking
- Financial runway analysis
- Receipt chain persistence (VAULT999)
- Historical collapse replay (Enron, 1MDB, Wirecard, FTX, LTCM)

---

## Historical Collapse Replay

WEALTH can replay historical financial collapses using **only information available before the collapse**:

| Case | Pre-collapse Signal Detected |
|------|------------------------------|
| **Enron** (2000) | Reality ↔ Narrative divergence |
| **1MDB** (2014) | Power ↔ Incentive capture |
| **Wirecard** | Reporting ↔ Reality divergence |
| **FTX** | Custody ↔ Governance coupling |
| **LTCM** | Leverage ↔ Liquidity concentration |

The objective is not hindsight. It is measuring **whether risk signals existed before reality arrived**.

---

## Use Cases

| Industry | Application | Value |
|----------|-------------|-------|
| Sovereign Wealth Funds | Investment evaluation | Long-term consequence visibility |
| Oil & Gas | Capital project assessment | NPV/IRR with scenario stress |
| Asset Management | Portfolio health | Real-time diagnostics + entropy |
| Trading | Algorithmic strategy | Backtesting + entry planning (XAUUSD) |
| Policy Analysis | Institutional health | Decay detection + governance scoring |

---

## MCP Interface

WEALTH exposes 11 canonical tools via MCP (Model Context Protocol):

`capital_backtest` · `capital_diagnose` · `capital_entropy` · `capital_entry_plan` · `capital_health` · `capital_indicator` · `capital_ledger` · `capital_market` · `capital_primitive` · `capital_registry` · `wealth_judge_handoff`

Full tool list: `curl http://localhost:18082/tools/list`

---

## Federation Role

WEALTH is the capital intelligence organ in the arifOS federation. It computes financial evidence — it never allocates, trades, or decides.

**GEOX** = truth about reality · **WEALTH** = truth about consequences · **WELL** = truth about readiness

**ARIF vetoes. arifOS judges. AAA routes. A-FORGE executes.**

**Sister Repos:**
- [arifOS](https://github.com/arif-fazil/arifOS) — Constitutional kernel
- [AAA](https://github.com/arif-fazil/AAA) — Intelligence routing
- [A-FORGE](https://github.com/arif-fazil/A-FORGE) — Execution engine
- [GEOX](https://github.com/arif-fazil/GEOX) — Earth sciences
- [WELL](https://github.com/arif-fazil/WELL) — Biometric monitoring
- [arifFlow](https://github.com/arif-fazil/arifFlow) — Workflow orchestration

---

## Documentation

- [Full Technical README](docs/README-FULL.md)
- [Unified Architecture](docs/WEALTH_UNIFIED_ARCHITECTURE.md)
- [Sovereign Wealth Spec](docs/SOVEREIGN_WEALTH_SPEC.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

---

## License

**GNU Affero General Public License v3.0 (AGPL-3.0)**

This program is free software: you can redistribute it and/or modify it under the terms of the GNU AGPL v3.0. See [LICENSE](LICENSE) for the full text.

---

**DITEMPA BUKAN DIBERI** — Forged, Not Given.

Built by Muhammad Arif bin Fazil.
