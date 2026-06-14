<div align="center">

```
██╗    ██╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
██║    ██║██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
██║ █╗ ██║█████╗  ███████║██║     ██║   ███████║
██║███╗██║██╔══╝  ██╔══██║██║     ██║   ██╔══██║
╚███╔███╔╝███████╗██║  ██║███████╗██║   ██║  ██║
 ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝

    Capital Intelligence & Resource Thermodynamics
    ─────────────────────────────────────────────────
    Not a trading bot. Not a financial advisor. The MATH.
</div>

---

> **DITEMPA BUKAN DIBERI** — *"Forged, Not Given."*
>
> Capital intelligence is not handed out. It is built through sweat, scar tissue, and
> seventeen thousand lines of monolith that never lied about a single decimal point.
> This is not a startup. This is not a SaaS. This is the capital organ of a constitutional
> AI federation — it computes, it warns, it seals. It never allocates alone.

[![CI](https://img.shields.io/badge/tests-153%2F153%20PASS-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![MCP Tools](https://img.shields.io/badge/MCP-20%20canonical%20tools-10b981?logo=anthropic)](internal/monolith.py)
[![Federation](https://img.shields.io/badge/organ-CAPITAL-f59e0b)](FEDERATION_CONTRACT.md)
[![License](https://img.shields.io/badge/license-AGPL--3.0-ef4444?logo=gnu)](LICENSE)
[![Port](https://img.shields.io/badge/port-18082-64748b)](INVARIANTS.md)
[![Service](https://img.shields.io/badge/systemd-wealth--organ.service-success)](RUNBOOK.md)
[![Status](https://img.shields.io/badge/status-OPERATIONAL-success)](CONTEXT.md)

---

## Table of Contents

1. [What Is WEALTH?](#1-what-is-wealth)
2. [The Federation Position](#2-the-federation-position)
3. [The 12 Ω-WEALTH Domains](#3-the-12-ω-wealth-domains)
4. [Full Capability Map](#4-full-capability-map)
5. [Boundary Declaration](#5-boundary-declaration)
6. [Constitutional Binding](#6-constitutional-binding)
7. [Quick Start](#7-quick-start)
8. [Architecture](#8-architecture)
9. [For Human Operators (Arif)](#9-for-human-operators-arif)
10. [For AI Agents](#10-for-ai-agents)
11. [For Institutions](#11-for-institutions)
12. [Build, Test, Deploy](#12-build-test-deploy)
13. [Known Limitations](#13-known-limitations)
14. [Federation Cross-Reference](#14-federation-cross-reference)
15. [GENESIS Chain](#15-genesis-chain)
16. [License & Sovereignty](#16-license--sovereignty)

---

## 1. What Is WEALTH?

### In One Sentence

> **WEALTH is the capital intelligence organ of the arifOS federation — it computes NPV, IRR, EMV, risk scores, stock analytics, game theory, and sovereign resource economics, then tags every output with an epistemic band so you know exactly how confident it should make you.**

### What It IS

- ✅ **The compute-only capital engine** — NPV, IRR, EMV, DSCR, risk scores, portfolio analysis, Monte Carlo
- ✅ **A thermodynamics-of-capital substrate** — 12 orthogonal dimensions mapping physics to finance (Conservation, Flow, Gradient, Entropy, Energy, Time, Inertia, Field, Signal, Game, Boundary, Hysteresis)
- ✅ **An MCP server on port 18082** — 20 canonical public tools + 34 hidden aliases for backward compat
- ✅ **A dual-runtime organ** — Python canonical kernel (`internal/monolith.py`) + Node.js legacy kernel (`src/`, `host/kernel/`)
- ✅ **A stock analysis layer (D4)** — 12-mode capital-risk governance: verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence
- ✅ **A market data bridge (D3)** — live FX rates (Frankfurter), commodities, macro indicators (World Bank)
- ✅ **A personal finance engine (D1)** — cashflow, net worth, EPF projection, zakat calculation (Malaysian)
- ✅ **An inequality diagnosis kernel** — 5 dimensions of structural inequality with live World Bank presets
- ✅ **Evidence-tagged always** — every output carries an epistemic band (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN)
- ✅ **Built for one sovereign** — Muhammad Arif bin Fazil. WEALTH computes. arifOS judges. Arif decides.

### What It Is NOT

- ❌ **NOT a trading bot** — does not buy, sell, or move capital
- ❌ **NOT a financial advisor** — outputs are advisory, never prescriptive
- ❌ **NOT a stock oracle** — `recommendation_only: True`, `final_authority: "Arif"`
- ❌ **NOT a bank** — holds no accounts, processes no transactions
- ❌ **NOT a constitutional judge** — that belongs to arifOS (port 8088)
- ❌ **NOT an executor** — that belongs to A-FORGE (port 7071)
- ❌ **NOT a black box** — every formula is inspectable at `wealth://formulas/*`

---

## 2. The Federation Position

WEALTH sits in the middle of the arifOS constitutional chain. It receives intent,
computes value, and passes verdicts upward to the kernel. It never executes.

```
                         ┌─────────────────────────┐
                         │   Arif bin Fazil         │
                         │   F13 SOVEREIGN          │
                         │   "Arif decides"         │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │       arifOS (Ω)        │
                         │   Constitutional Kernel │
                         │   Port: 8088            │
                         │   F1-F13 · 888 JUDGE    │
                         │   999 VAULT             │
                         └───┬───┬───┬───┬───┬────┘
                             │   │   │   │   │
              ┌──────────────┼───┼───┼───┼───┼──────────────┐
              │              │   │   │   │   │              │
    ┌─────────▼──┐  ┌───────▼─┐ ┌▼───────┐ ┌▼─────────┐  ┌▼─────────┐
    │   GEOX     │  │ WEALTH  │ │  WELL  │ │   AAA    │  │ A-FORGE  │
    │   Earth    │  │ CAPITAL │ │  Human │ │ Cockpit  │  │ Execute  │
    │   :8081    │  │ :18082  │ │ :18083 │ │  :3001   │  │  :7071   │
    │  Evidence  │  │ Compute │ │ Reflect│ │ Display  │  │ Execute  │
    └────────────┘  └────┬────┘ └────────┘ └──────────┘  └──────────┘
                         │
              ┌──────────▼──────────┐
              │   WEALTH verdicts:   │
              │   • SAFE_TO_STUDY    │
              │   • NEEDS_DATA       │
              │   • UNSAFE           │
              │   • 888_HOLD         │
              │   • MATH_ERROR       │
              └─────────────────────┘
```

### The Authority Chain (Non-Negotiable)

```
Arif (F13 SOVEREIGN)
  → arifOS kernel (F1-F13 enforcement, 888 JUDGE)
    → WEALTH computes capital verdict (advisory evidence)
      → arifOS judges the verdict (SEAL / SABAR / HOLD / VOID)
        → A-FORGE executes (only under SEAL)
          → VAULT999 seals (immutable, forever)
```

**No organ may authorize its own execution. WEALTH computes. arifOS judges. Arif decides.**

### Organ Boundaries

| Aspect | OWNS (WEALTH) | DOES NOT (other organ) |
|--------|---------------|------------------------|
| NPV / IRR / EMV | ✅ Compute | — |
| Risk / DSCR | ✅ Compute | — |
| Stock analysis | ✅ 12-mode D4 engine | — |
| Market data (FX, macro) | ✅ Fetch, normalize | — |
| Zakat / EPF | ✅ Malaysian calc | — |
| Constitutional verdicts | — | ➜ arifOS (port 8088) |
| Earth evidence | — | ➜ GEOX (port 8081) |
| Human readiness | — | ➜ WELL (port 18083) |
| Execution / deploy | — | ➜ A-FORGE (port 7071) |
| Display / cockpit | — | ➜ AAA (port 3001) |

---

## 3. The 12 Ω-WEALTH Domains

Every capital question maps to one or more of these 12 thermodynamic dimensions. Each
dimension is a physics invariant applied to finance — Conservation is mass balance,
Entropy is disorder, Gradient is pressure differential.

| Ω | Domain | Physics Analogy | Key Tool | One-Line Purpose |
|---|--------|----------------|----------|------------------|
| **Ω-00** | Synthesis | Master field equation | `wealth_omni_wisdom` | Unified capital verdict across all dimensions |
| **Ω-01** | Conservation | Mass balance (assets, liabilities) | `wealth_conservation_capital` | What do we actually own? |
| **Ω-02** | Flow | Mass flow rate (cashflow, burn) | `wealth_flow_liquidity` | How fast is capital moving? |
| **Ω-03** | Gradient | Pressure differential (mispricing) | `wealth_gradient_price` | Where is the pressure? |
| **Ω-04** | Entropy | Disorder (risk, uncertainty, tail) | `wealth_entropy_risk` | What could go wrong? |
| **Ω-05** | Energy | Output per input (efficiency) | `wealth_energy_productivity` | How much bang for buck? |
| **Ω-06** | Time | Potential well decay (discounting) | `wealth_time_discount` | When does it pay back? |
| **Ω-07** | Inertia | Structural load (leverage, fragility) | `wealth_inertia_leverage` | How much debt can this carry? |
| **Ω-08** | Field | External environment (macro) | `wealth_field_macro` | What's the external regime? |
| **Ω-09** | Signal | Evidence quality (info value) | `wealth_signal_information` | Is the data good enough? |
| **Ω-10** | Game | Multi-agent equilibrium (Nash) | `wealth_game_coordination` | Who wins, who loses? |
| **Ω-11** | Boundary | Constitutional floors (maruah) | `wealth_boundary_governance` | Is this permissible? |
| **Ω-12** | Hysteresis | Path dependence (ledger memory) | `wealth_hysteresis_ledger` | Where were we before? |

**Start with `wealth_omni_wisdom(mode='omni')`** — it fan-outs to all 12 dimensions in parallel
and fuses the results. For specific analysis, call the dimension tool directly.

---

## 4. Full Capability Map

### 4.1 Public MCP Surface — 20 Canonical Tools

```
20 public tools + 34 hidden aliases (65 @mcp.tool decorators)
```

| # | Tool | Domain | What It Does |
|---|------|--------|-------------|
| 1 | `wealth_omni_wisdom` | Ω-00 | Unified synthesis + deal frame + hysteresis in one call |
| 2 | `wealth_conservation_capital` | Ω-01 | Asset/liability accounting, net worth, capital stock |
| 3 | `wealth_flow_liquidity` | Ω-02 | Cashflow modeling, burn rate, runway, survival |
| 4 | `wealth_gradient_price` | Ω-03 | Spread detection, mispricing, price pressure |
| 5 | `wealth_entropy_risk` | Ω-04 | EMV, tail risk, Monte Carlo, return classification |
| 6 | `wealth_energy_productivity` | Ω-05 | IRR, PI, productivity index, capital efficiency |
| 7 | `wealth_time_discount` | Ω-06 | NPV, payback period, time-value-of-money |
| 8 | `wealth_inertia_leverage` | Ω-07 | DSCR, leverage stress, structural fragility |
| 9 | `wealth_field_macro` | Ω-08 | Live macro data — Brent, MYR/USD, GDP, inflation |
| 10 | `wealth_signal_information` | Ω-09 | EVOI, evidence quality, PoS for E&P wells |
| 11 | `wealth_game_coordination` | Ω-10 | Nash equilibria, multi-party deals, PSC templates |
| 12 | `wealth_boundary_governance` | Ω-11 | Floor compliance, maruah dignity scoring, legitimacy |
| 13 | `wealth_hysteresis_ledger` | Ω-12 | Path-dependent state, sealed financial memory |
| 14 | `wealth_inequality_kernel` | IEQ | 5-dimension inequality diagnosis (`preset='malaysia'`) |
| 15 | `wealth_agent_path` | Agent | Sovereign intent routing — find the right tool path |
| 16 | `wealth_stock_analysis` | D4 | 12-mode stock safety gate (see §4.2) |
| 17 | `wealth_market_data` | D3 | FX rates, commodities, macro indicators |
| 18 | `wealth_personal_finance` | D1 | Cashflow, net worth, EPF, zakat, runway |
| 19 | `wealth_survival_engine` | Survival | Unified liquidity + burn + runway dashboard |
| 20 | `wealth_system_registry_status` | System | Tool surface audit, health probe, registry truth |

### 4.2 D4 Stock Analysis — 12 Modes

`wealth_stock_analysis(mode='...')` is the governed stock safety gate. It computes.
It warns. It never recommends.

| Mode | What It Checks | Verdict |
|------|---------------|---------|
| `verify_math` | Recalculate P/L from entry/exit — detect AI number hallucination | MATH_ERROR or SAFE_TO_STUDY |
| `separate_pl` | Separate realized vs unrealized P/L | Advisory |
| `position_size` | Risk-based position sizing (max 1% risk per trade) | Risk-bounded |
| `r_multiple` | Risk-reward geometry (R = reward / risk) | Ratio check |
| `exposure` | Portfolio exposure and gap-down scenarios | Exposure map |
| `bursa_cost` | Bursa Malaysia transaction cost model | Cost breakdown |
| `tamak_check` | Greed/emotional behavior detection — stop-loss moved lower? Averaging down? Revenge trading? | Behavioral flag |
| `pre_trade` | Full pre-trade safety gate — 9 checks before any trade | SAFE_TO_STUDY / UNSAFE |
| `fundamentals` | 9 business reality invariants (cash conversion, debt, margins, moat) | Scorecard |
| `tac9` | TAC-9 technical: regime → structure → risk-reward | Structure analysis |
| `contrast` | Anomalous contrast — market layer disagreement detection | Contrast alert |
| `confluence` | False confluence — same-class indicator collapse | Confluence warning |

**Iron rule:** `recommendation_only: True`. `final_authority: "Arif"`. No buy/sell signal.
No trading coach. No stock promotion. The math is the math. You decide what to do with it.

### 4.3 D3 Market Data

`wealth_market_data` provides live economic indicators:

| Mode | Source | Example |
|------|--------|---------|
| `fx` | Frankfurter API | USD/MYR = 4.68 (live) |
| `commodity` | Approximate markets | Brent crude ~$72/bbl |
| `macro` | World Bank API | Malaysia GDP, inflation, rates |

### 4.4 D1 Personal Finance

`wealth_personal_finance` covers Malaysian-specific personal capital:

| Mode | What |
|------|------|
| `track` | Record a transaction |
| `summary` | Aggregate by category |
| `runway` | Months of financial survival |
| `net_worth` | Assets minus liabilities |
| `epf` | Project EPF accumulation to target age |
| `zakat` | Malaysian 2.5% zakat above nisab |

### 4.5 Inequality Kernel

`wealth_inequality_kernel(preset='malaysia')` diagnoses structural inequality across
5 dimensions with live World Bank data. Analyzes:

- Institutions quality · Ownership concentration · Mobility channels
- Risk distribution · Information symmetry · Voice access
- Time horizon · Historical damage · Power/dignity/network asymmetry
- Youth unemployment · Housing unaffordability · Future orientation collapse

**Verdict:** Bounded inequality + high mobility + universal dignity is achievable.
Extractive lock-in is the enemy, not inequality itself.

### 4.6 Resources & Prompts

| Type | Count | Examples |
|------|-------|----------|
| **Resources** | 18+ | `wealth://doctrine/valuation`, `wealth://formulas/npv`, `wealth://governance/floors`, `stock://{ticker}/fundamentals`, `stock://{ticker}/TAC9` |
| **Prompts** | 10+ | `wealth_diagnose_portfolio`, `wealth_crisis_triage`, `wealth_opportunity_ranking`, `wealth_allocation_rebalance`, `wealth_governance_audit`, `stock_screen`, `stock_pre_trade` |

---

## 5. Boundary Declaration

### OWNS (Compute Territory)

- **Net Present Value (NPV)** and discounted cash flow
- **Internal Rate of Return (IRR)** and profitability index
- **Expected Monetary Value (EMV)** and decision tree analysis
- **Debt Service Coverage Ratio (DSCR)** and leverage stress
- **Risk scores** — entropy, tail risk, Monte Carlo simulation
- **Portfolio allocation models** — mean-variance, capital budgeting
- **Stock analysis** — 12-mode governed safety gate
- **Market data** — FX rates, commodity prices, macro indicators
- **Game theory** — Nash equilibria, multi-party contract modeling
- **Inequality diagnosis** — structural economic fairness metrics
- **Personal finance** — cashflow, net worth, EPF, zakat
- **Sovereign resource economics** — PSC modeling, national oil calculus

### NEVER (Constitutional Territory)

- Move capital or authorize trades
- Execute financial transactions
- Hide downside risk or overstate returns
- Issue constitutional verdicts (SEAL / SABAR / VOID)
- Adjudicate legal disputes
- Replace human judgment in irreversible decisions
- Self-authorize allocation of resources
- Bind to 0.0.0.0 (always 127.0.0.1)

### Imports From

| Source | What | Interface |
|--------|------|-----------|
| **arifOS** (8088) | Constitutional constraints, session tokens, floor enforcement, federation geometry | MCP mesh |
| **A-FORGE** (7071) | Deploy metadata, build pipeline, container registry | GHCR image |
| **GEOX** (8081) — *planned* | Prospect volume estimates, resource quality data | MCP mesh (future) |
| **AAA** (3001) | Operator capital allocation intent, portfolio review requests | A2A mesh |

### Exports To

| Consumer | What | Interface |
|----------|------|-----------|
| **arifOS** (8088) | Capital viability verdicts, risk scores, decision memos | MCP tools |
| **AAA** (3001) | Decision memo viewer data, portfolio dashboard metrics | HTTP API |
| **A-FORGE** (7071) | Docker image, build context | `ghcr.io/ariffazil/wealth:<sha>` |

---

## 6. Constitutional Binding

WEALTH operates under three specific floors of the arifOS constitution. Every tool call,
every computation, every output is governed.

| Floor | Name | How WEALTH Enforces It |
|-------|------|----------------------|
| **F1** | AMANAH | Reversible-first. All WEALTH tools are compute-only. Irreversible financial actions require `ack_irreversible=True` + `arif_judge_deliberate → SEAL`. |
| **F2** | TRUTH | P(truth) ≥ 0.99. Every WEALTH output carries an `epistemic_tag` (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN). No bare numbers without uncertainty bands. |
| **F6** | EMPATHY | Protect weakest stakeholder. `wealth_boundary_governance(mode='legitimacy_audit')` surfaces who loses. `maruah_score` tracks dignity preservation. |
| **F7** | HUMILITY | ω₀ ∈ [0.03, 0.05]. The `verify_math` mode of D4 Stock Analysis exists specifically to catch AI number hallucination. Every `r_multiple` reports confidence. |
| **F9** | ANTIHANTU | No deception. `contrast` mode detects anomalous divergence between market layers that might indicate manipulated inputs. |
| **F11** | AUDITABILITY | Every tool call logs to `wealth_governance_verdict`. Every capital verdict has a SHA-256 receipt. |
| **F13** | SOVEREIGN | All verdicts are `recommendation_only`. The final decision belongs to Muhammad Arif bin Fazil. Always. |

**WEALTH does not self-judge.** arifOS reads the envelope and applies the floors.
WEALTH provides the evidence. The kernel makes the law.

---

## 7. Quick Start

### For Human Operators (Non-Coders)

You interact with WEALTH through the **AAA Cockpit** or through **Hermes ASI** on Telegram:

```
AAA Cockpit:   https://aaa.arif-fazil.com
Hermes:        @ASI_arifos_bot (Telegram)
Health check:  https://wealth.arif-fazil.com/health
```

To ask a capital question, tell Hermes:
> "Tanya WEALTH: NPV projek ni kalau 5 tahun cashflow RM100k setahun, discount rate 8%"

### For AI Agents (MCP Clients)

Connect to the MCP endpoint:

```json
{
  "mcpServers": {
    "wealth": {
      "url": "https://wealth.arif-fazil.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

Or via **stdio** for local agents (Claude Code, OpenCode, Continue CLI):

```json
{
  "mcpServers": {
    "wealth": {
      "command": "python3",
      "args": ["internal/monolith.py", "--transport", "stdio"],
      "cwd": "/root/WEALTH"
    }
  }
}
```

### For Developers

```bash
# Clone
git clone git@github.com:ariffazil/wealth.git
cd wealth

# Install (uv — Python 3.12+)
uv sync --frozen

# Start the canonical MCP server
python internal/monolith.py

# Health check
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
# Expected: {"status":"healthy","final_authority":"ARIF"}

# Run tests (Python — 153/153 PASS)
PYTHONPATH=. pytest tests/ -q --tb=short

# Run tests (Node.js legacy)
npm install && npm test

# Lint
ruff check . && ruff format .

# Full forge (security audit + health)
make forge
```

### Verify Everything Works

```bash
# Registry truth — does the surface match the manifest?
curl -s http://127.0.0.1:18082/health | python3 -c "
import json,sys
d = json.load(sys.stdin)
print(f'status={d[\"status\"]} registry_truth={d.get(\"registry_truth\",\"?\")}')
"
# Expected: status=healthy registry_truth=PASS
```

### First Capital Computation

```bash
# Via MCP: compute NPV of a 5-year project
# (call wealth_omni_wisdom or wealth_time_discount via any MCP client)

# Or via curl (JSON-RPC):
curl -s -X POST http://127.0.0.1:18082/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_time_discount","arguments":{"mode":"npv","initial_investment":500000,"cash_flows":[100000,120000,140000,160000,180000],"discount_rate":0.08}},"id":1}'
```

---

## 8. Architecture

### Directory Tree — What Lives Where

```
WEALTH/
│
├── internal/                          # CANONICAL KERNEL (Python 3.12+)
│   ├── monolith.py                    # THE KERNEL — ~16,000 lines, 20 public tools,
│   │                                  #   12 Ω-WEALTH domains, all MCP registration
│   ├── __init__.py                    # Makes internal/ a Python package
│   ├── organ_governance.py            # Governance wrapper — arifOS F1-F13 binding
│   ├── governance.py                  # Floor hooks, policy engine
│   ├── invariants.py                  # Constitutional invariants and boundary checks
│   ├── kernel_math.py                 # Core financial math primitives
│   ├── db_schema.py                   # PostgreSQL schema — trades, positions, watchlist
│   ├── market_data.py                 # D3 Market Data — FX, commodities, macro
│   ├── personal_finance.py            # D1 Personal Finance — EPF, zakat, cashflow
│   ├── federation_memory.py           # Federation cross-organ memory bridge
│   ├── pai_receipt.py                 # PAI (Perplexity AI Interface) receipt format
│   │
│   ├── stock/                         # D4 STOCK ANALYSIS ENGINE
│   │   ├── __init__.py                # Module init + registration
│   │   ├── math_tools.py              # verify_math, separate_pl, position_size, r_multiple
│   │   ├── risk_tools.py              # exposure, bursa_cost
│   │   ├── behavior_tools.py          # tamak_check (greed detection)
│   │   ├── fundamentals.py            # 9 business reality invariants
│   │   ├── technical.py               # TAC-9 technical analysis
│   │   └── contrast.py                # Anomalous contrast + false confluence detection
│   │
│   ├── engines/                       # Computation engines
│   │   ├── canonical_tools.py         # Tool registry and dispatch
│   │   ├── five_seals.py              # Five-seal advisory boundary
│   │   └── advisory.py                # Advisory output formatting
│   │
│   ├── domains/                       # Domain expansion (WIP)
│   │   ├── capital/                   # Capital domain modules
│   │   ├── field/                     # Field/macro domain
│   │   ├── personal/                  # Personal finance domain
│   │   ├── signal/                    # Signal/information domain
│   │   ├── stock/                     # Stock analysis domain
│   │   ├── time/                      # Time value domain
│   │   ├── registry/                  # Domain registry
│   │   └── shared/                    # Shared domain primitives
│   │
│   ├── shared/                        # Cross-domain shared primitives
│   │   ├── __init__.py
│   │   └── base.py                    # Base classes and utilities
│   │
│   └── prompts/                       # MCP prompt templates
│
├── host/                              # MODULAR PYTHON LIBRARIES
│   ├── coordination/                  # LP allocator, cooperative/strategic protocols
│   ├── epistemic/                     # Correlation guard, EVOI, schema validator
│   ├── governance/                    # Floor hooks, policy, vault bridge
│   ├── ingest/                        # ECB, FRED, OWID, Ember, WorldBank adapters
│   ├── kernel/                        # JS legacy: floors.js, finance.js, seal.js
│   └── wealth/                        # JS: cashflow, networth, projection, maruah
│
├── src/                               # NODE.JS LEGACY KERNEL
│   ├── kernel/                        # Legacy JS kernel
│   └── wealth/                        # Legacy wealth computation
│
├── capitalx/                          # Constitutional capital pricing engine (Node.js)
│   └── DESIGN.md                      # Full engine specification
│
├── civilizational/                    # Boundary monitors (Calhoun sink, extractive drift)
│
├── canon/                             # CONSTITUTIONAL SPECS (13 Markdown files)
│   ├── ECONOMIC_MODEL.md              # Economic model specification
│   ├── THREAT_MODEL.md                # Threat model
│   ├── STRESS_TESTS.md                # Stress test scenarios
│   ├── GOVERNANCE.md                  # Governance specification
│   ├── CAPITALX_SPEC.md               # capitalx engine specification
│   ├── WEALTH_HARNESS.md              # Harness architecture
│   ├── TELEMETRY_SCHEMA.md            # Telemetry schema
│   ├── NODE_SPEC.md                   # Node specification
│   ├── COSMOLOGY.md                   # Cosmology / worldview
│   ├── CASE_STUDIES.md                # Case studies
│   ├── GLOSSARY.md                    # Terminology glossary
│   ├── ROADMAP.md                     # Development roadmap
│   └── README.md                      # Canon overview
│
├── mcp/                               # Cross-domain demo MCP surface (6 tools)
│   └── server.py                      # Not production — development demo only
│
├── tests/                             # TEST SUITES
│   ├── *.py                           # Python pytest — 153/153 PASS
│   └── *.test.js                      # Node.js node:test — parity validation
│
├── docs/                              # Documentation
│   ├── wealth-basis-spec.md           # 3-axis Wealth Basis (Energy, Entropy, Echo)
│   ├── repo-role-boundary.md          # Repository role boundaries
│   ├── waw-envelope-spec.md           # WAW envelope specification
│   ├── mcp-tool-families-spec.md      # MCP tool families
│   ├── 00-niat-dan-amanah.md          # Niat dan Amanah (Malay)
│   ├── 03-ujian-keselamatan.md        # Safety tests (Malay)
│   ├── integration/                   # Integration docs
│   └── REPO_HYGIENE_AUDIT_*.md        # Repo hygiene audits
│
├── raw/                               # Historical design docs
├── wiki/                              # Knowledge base (cosmology, concepts, entities)
├── memory/                            # Session logs
├── datasources/                       # Data source adapters
├── assets/                            # Static assets
├── scripts/                           # Utility scripts
│
├── server.py                          # 15-line backward-compat shim → monolith
├── cli.js                             # Node.js CLI: boot, check, seal, capitalx
├── pyproject.toml                     # Python packaging (AGPL-3.0)
├── package.json                       # Node.js packaging
├── Makefile                           # test, lint, format, forge, health
├── fastmcp.json                       # FastMCP configuration
├── mcp.json                           # MCP configuration
│
├── GENESIS/
│   └── 011_WEALTH_MANDATE.md          # Organ mandate (canon pending F13)
│
├── BOUNDARY.md                        # Boundary declaration
├── TOOL_SURFACE.md                    # Tool surface registry
├── FEDERATION_CONTRACT.md             # Federation contract
├── CONTEXT.md                         # Live state
├── RUNBOOK.md                         # Operations
├── INVARIANTS.md                      # Source of truth
├── AGENTS.md                          # Agent boot sequence
├── SPEC.md                            # Orthogonal architecture rebuild spec
├── ROADMAP.md                         # Development roadmap
└── ARIF.md                            # Address to sovereign
```

### The Monolith Philosophy

`internal/monolith.py` is ~16,000 lines. This is not technical debt — it is intentional
architecture. The 12 Ω-WEALTH domains are deeply mathematically coupled. NPV feeds IRR
feeds risk entropy feeds DSCR. Splitting them creates circular imports and breaks the
physics invariants. **The monolith is the design.**

The file is structured internally by domain, each section clearly delimited. The
public surface (`PUBLIC_SURFACE_WHITELIST`) controls which 20 tools are exposed to
MCP clients. The other 34 decorated functions are internal aliases, deprecated
wrappers, or test helpers — registered but not listed.

### Dual Runtime

| Runtime | Path | Status | Use |
|---------|------|--------|-----|
| **Python** | `internal/monolith.py` | ✅ **CANONICAL** | All MCP tools, all computation |
| **Node.js** | `src/`, `host/kernel/` | ⚠️ Legacy | Numerical parity testing, `cli.js` operations |

---

## 9. For Human Operators (Arif)

You don't need to code. You need to know three things:

### 1. Ask WEALTH anything about capital

Through Hermes (`@ASI_arifos_bot` on Telegram):

```
"Tanya WEALTH: NPV projek offshore tu kalau kos RM500k, cashflow tahunan RM100k-180k, discount 8%"
"Tanya WEALTH: Berapa runway aku sekarang?"
"Tanya WEALTH: Check EPF aku umur 55"
"Tanya WEALTH: Zakat tahun ni — total wealth RM50k, cukup nisab?"
"Tanya WEALTH: Analyze saham TENAGA — fundamentals dia ok ke?"
```

### 2. WEALTH never decides for you

Every output is tagged:

| Tag | Meaning |
|-----|---------|
| **CLAIM** | Verified. P(truth) ≥ 0.99. Evidence-backed. |
| **PLAUSIBLE** | Reasonable. P(truth) ≥ 0.85. Acceptable but verify. |
| **HYPOTHESIS** | Speculative. P(truth) ≥ 0.60. Needs more data. |
| **ESTIMATE** | Rough. Directional only. Do not commit capital. |
| **UNKNOWN** | Cannot compute. Missing data. Ask for more inputs. |

If WEALTH says `HYPOTHESIS`, it means "jangan commit duit lagi — data tak cukup."

### 3. Irreversible decisions need your 888

Any output labeled `888_HOLD` means the computation says "STOP — human review required."
This fires when:

- A stock trade exceeds position size limits
- An NPV calculation has uncertainty > 30%
- A leverage ratio crosses the danger threshold
- A pre-trade safety gate finds a TAMAK pattern (stop-loss moved lower, revenge trading, etc.)

**You are the final authority. WEALTH computes. You decide.**

### The Stock Safety Gate (what it watches for you)

When you ask WEALTH to check a stock position, the `pre_trade` mode silently checks:

1. ✅ Position size ≤ 1% of account
2. ✅ Stop-loss is SET (not moved lower since entry — TAMAK flag)
3. ✅ R-multiple ≥ 2:1 (reward proportional to risk)
4. ✅ No revenge trading pattern (selling loser, immediately buying another)
5. ✅ No averaging down (adding to a losing position)
6. ✅ Sector exposure balanced (not all-in on one sector)
7. ✅ Liquidity adequate (can exit without moving the market)
8. ✅ Market regime compatible (don't fight the trend)
9. ✅ Fundamental check passed (business reality, not just chart pattern)

Any one flag = `UNSAFE`. All nine green = `SAFE_TO_STUDY`.

---

## 10. For AI Agents

### Connection

WEALTH exposes 20 governed MCP tools. Connect via:

```
MCP Endpoint:  https://wealth.arif-fazil.com/mcp
Transport:     streamable-http (public) or stdio (local)
Port:          18082
```

### Tool Categories

| Category | Tools | Use When |
|----------|-------|----------|
| **Routing** | `wealth_agent_path`, `wealth_system_registry_status` | "What tool should I use?" |
| **Core Finance** | `wealth_time_discount`, `wealth_entropy_risk`, `wealth_energy_productivity` | NPV, IRR, EMV, risk |
| **Cashflow** | `wealth_flow_liquidity`, `wealth_survival_engine` | Runway, burn, liquidity |
| **Macro** | `wealth_field_macro`, `wealth_market_data` | FX rates, GDP, commodities |
| **Stock** | `wealth_stock_analysis` (12 modes) | Position safety, fundamentals, TAC-9 |
| **Strategy** | `wealth_game_coordination`, `wealth_inequality_kernel` | Multi-party deals, inequality |
| **Governance** | `wealth_boundary_governance`, `wealth_omni_wisdom` | Floor checks, synthesis |
| **Personal** | `wealth_personal_finance` | EPF, zakat, net worth |

### Rules for Agents

1. **WEALTH computes, Arif decides.** Never present a WEALTH output as a final decision.
2. **Always read the epistemic tag.** CLAIM ≠ HYPOTHESIS. Don't treat an ESTIMATE like a CLAIM.
3. **Route irreversible actions through arifOS.** `wealth_* → arif_judge_deliberate → SEAL → arif_forge_execute → VAULT999`.
4. **Never fabricate NPV.** If WEALTH returns `NEEDS_DATA`, tell the user what's missing.
5. **Downside first.** When presenting results, surface the worst case before the expected case.
6. **Zakat is wajib.** If a Malaysian user asks about wealth, surface the zakat tool.
7. **Stock analysis is a safety gate, not a signal.** `SAFE_TO_STUDY` means "nothing obviously wrong." It does not mean "buy."

### The WEALTH Call Chain (Standard Pattern)

```
1. wealth_agent_path(task_description)         → "Which tool do I need?"
2. wealth_boundary_governance(mode='floors')   → "Is this action bounded?"
3. wealth_omni_wisdom(decision_context)         → "Compute the capital verdict"
4. arif_judge_deliberate(candidate=verdict)     → "Is this constitutionally valid?"
5. arif_vault_seal(payload=verdict)             → "Record this forever."
```

### Common Scenarios

**Scenario 1: "Should I invest in Project X?"**
```
→ wealth_omni_wisdom(mode='deal',
    deal_params={initial_investment: 500000,
                 cash_flows: [100000, 120000, 140000, 160000, 180000],
                 discount_rate: 0.08})
→ Returns: NPV, IRR, PI, payback, risk score, maruah impact, epistemic tag
```

**Scenario 2: "Is my stock position safe?"**
```
→ wealth_stock_analysis(mode='pre_trade',
    entry_price=4.65, current_price=5.20, stop_loss=4.30,
    position_size=1000, account_balance=50000)
→ Returns: 9-check safety gate verdict + per-check pass/fail
```

**Scenario 3: "What's Malaysia's macro snapshot?"**
```
→ wealth_field_macro(mode='snapshot', entity_code='MYS')
→ Returns: GDP, inflation, Brent price, MYR/USD, energy mix
```

**Scenario 4: "How long can I survive on current cash?"**
```
→ wealth_personal_finance(mode='runway',
    monthly_burn=8000, liquid_assets=45000)
→ Returns: runway_months, burn_rate, conservative_estimate
```

---

## 11. For Institutions

### Governance-Compliant Capital Intelligence

WEALTH is designed for institutions that need:

1. **Auditable financial computation** — every NPV, IRR, EMV carries a SHA-256 receipt
2. **Constitutional governance** — F1-F13 floors enforced on every tool call
3. **Epistemic honesty** — no overconfident numbers, every output tagged with uncertainty
4. **Sovereign resource modeling** — PSC templates, national oil calculus, multi-party game theory
5. **Inequality diagnosis** — 5-dimension structural analysis with live World Bank data
6. **Immutable audit trail** — every sealed verdict lands in VAULT999, append-only, forever

### Malaysian-Specific Capabilities

| Capability | Tool | Why It Matters |
|------------|------|---------------|
| **EPF projection** | `wealth_personal_finance(mode='epf')` | Retirement readiness for Malaysian workforce |
| **Zakat calculation** | `wealth_personal_finance(mode='zakat')` | Islamic wealth obligation, 2.5% above nisab |
| **Bursa Malaysia costs** | `wealth_stock_analysis(mode='bursa_cost')` | Real Malaysian transaction costs |
| **MYR/USD FX** | `wealth_market_data(mode='fx', targets='MYR')` | Ringgit exposure, live |
| **Malaysia macro** | `wealth_field_macro(preset='malaysia_gdp')` | GDP, inflation, oil price, energy mix |
| **Sovereign PSC** | `wealth_game_coordination(template='sovereign_resource')` | NOC vs foreign contractor game theory |
| **Inequality diagnosis** | `wealth_inequality_kernel(preset='malaysia')` | Structural economic fairness |

### The 3-Axis Wealth Basis (Energy, Entropy, Echo)

```
W⃗ = (Ê, 1 − Ŝ, Eχ̂)
```

| Axis | Symbol | BM | Question |
|------|--------|-----|----------|
| **Energy** | Ê | Berapa banyak tenaga kita? | Capital stock, productivity, flow |
| **Entropy** | Ŝ | Berapa bocor sistem ni? | Risk, leakage, uncertainty, shadow |
| **Echo** | Eχ̂ | Gaung dia sampai generasi berapa? | Intergenerational impact, sustainability |

This basis feeds into the **capitalx** constitutional pricing engine, which adjusts
discount rates for paradox, scar, and shadow — ensuring the math accounts for what
the market refuses to price.

### Compliance Frameworks

WEALTH outputs are compatible with:

- **SG MAIGF** (Singapore Model AI Governance Framework for Agentic AI)
- **ASEAN Guide on AI Governance and Ethics** (GenAI expansion)
- **EU AI Act Article 14** (human oversight)
- **OWASP LLM Top 10** (LLM09: Overreliance)

---

## 12. Build, Test, Deploy

### Python (Canonical)

```bash
cd /root/WEALTH

# Install dependencies
uv sync --frozen

# Run the server
python internal/monolith.py                         # HTTP on 127.0.0.1:18082
python internal/monolith.py --transport stdio       # Stdio for local agents

# Tests (153/153 PASS)
PYTHONPATH=. pytest tests/ -q --tb=short

# Lint & format
ruff check . && ruff format .

# Health
make health
# → {"status":"healthy","final_authority":"ARIF","tool_count":20,"registry_truth":"PASS"}

# Full forge (security audit + health)
make forge
```

### Node.js (Legacy)

```bash
cd /root/WEALTH

# Install
npm install

# Run tests (numerical parity validation)
npm test

# CLI operations
npm run boot       # Initialize capital state
npm run check      # Run health checks
npm run seal       # Seal session to VAULT999
```

### Docker

```bash
docker build -t wealth .
docker run -p 18082:18082 wealth
```

### Systemd

```bash
# Start / Stop / Restart
systemctl start wealth-organ
systemctl stop wealth-organ
systemctl restart wealth-organ
systemctl status wealth-organ

# Logs
journalctl -u wealth-organ -n 50 --no-pager
```

### Git

```bash
# Repo: git@github.com:ariffazil/wealth.git
# Branch: main
# Current HEAD: b06f8b8

git pull origin main           # Fetch latest
git tag vYYYY.MM.DD            # Date-stamp tag only (no semver)
```

---

## 13. Known Limitations

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| **License anomaly** | LOW | ✅ RESOLVED | Both `pyproject.toml` and `package.json` declare AGPL-3.0. Historical `PROPRIETARY` references are stale. |
| **Node.js harness bug** | LOW | ⚠️ Known | 17 Node tests fail due to stdout pollution from Python `runPython` — filter `runPython` output. Python canonical suite is clean (153/153). |
| **Dual runtime** | MEDIUM | ⚠️ Legacy | Python is canonical. Node.js is legacy. Should eventually be deprecated. |
| **A-FORGE reimplements WEALTH** | MEDIUM | ⚠️ Drift | `A-FORGE/src/tools/WealthTools.ts` duplicates ROI/EMV/portfolio logic. Should delegate to WEALTH MCP instead. |
| **GENESIS/ missing** | LOW | ⚠️ Stub | Only `011_WEALTH_MANDATE.md` exists. Full canon pending F13 ratification. |
| **Tool surface in flux** | LOW | ℹ️ Evolution | SPEC.md proposes 42 atomic tools to replace the 20 canonical composite tools. This is planned, not yet executed. |
| **Docker bypasses UFW** | INFO | ℹ️ Architecture | Docker containers (Postgres, Redis) on `0.0.0.0`. Mitigation: all bind to `127.0.0.1`. |
| **No real-time market feed** | MEDIUM | ℹ️ Design | D3 market data uses free APIs (Frankfurter, World Bank) — not Bloomberg/Reuters grade. Sufficient for modeling, not for HFT. |

### What WEALTH Cannot Do (By Design)

- Cannot execute trades on any exchange
- Cannot move money between accounts
- Cannot authorize capital allocation
- Cannot provide personalized financial advice
- Cannot guarantee investment returns
- Cannot hide or minimize downside risk
- Cannot self-certify its own output as SEAL-grade

---

## 14. Federation Cross-Reference

WEALTH is one of seven organs in the arifOS Constitutional Federation.

| Organ | Port | Repo | Role | Relationship to WEALTH |
|-------|------|------|------|----------------------|
| **arifOS** | 8088 | `ariffazil/arifos` | Constitutional kernel | **Governs WEALTH** — F1-F13 enforcement, 888 JUDGE, VAULT999 |
| **GEOX** | 8081 | `ariffazil/geox` | Earth intelligence | **Feeds WEALTH** — prospect volumes, resource quality (planned) |
| **WELL** | 18083 | `ariffazil/well` | Human readiness | **Informs WEALTH** — cognitive load → capital preservation (planned) |
| **AAA** | 3001 | `ariffazil/AAA` | Control plane | **Displays WEALTH** — cockpit, portfolio dashboard, decision memos |
| **A-FORGE** | 7071 | `ariffazil/A-FORGE` | Execution shell | **Executes under WEALTH verdicts** — gated by arifOS SEAL |
| **APEX** | 3002 | `ariffazil/APEX` | 888 JUDGE (legacy) | Legacy health probe — deliberation moved to AAA a2a-server |

### Key Federation Files

| File | Purpose |
|------|---------|
| `/root/arifOS/FEDERATION_CONTRACT.md` | Canonical federation contract |
| `/root/arifOS/FEDERATION_STATUS.md` | Live health of all 7 organs + MIND/MEMORY services |
| `/root/arifOS/GENESIS/000_KERNEL_CANON.md` | Kernel canon (Source of Truth) |
| `/root/arifOS/static/arifos/theory/000/000_CONSTITUTION.md` | 13 Constitutional Laws |
| `FEDERATION_CONTRACT.md` | WEALTH's local contract |
| `BOUNDARY.md` | WEALTH's boundary declaration |
| `GENESIS/011_WEALTH_MANDATE.md` | WEALTH's organ mandate |

> **MIND/MEMORY services:** A-FORGE hosts the MIND service (port 51001) and MEMORY service (port 51002) for cross-agent state and recall. These are not separate federation organs; they are runtime services under A-FORGE.

---

## 15. GENESIS Chain

```
000_KERNEL_CANON.md         ← arifOS (Source of Truth)
    │
    ├── 001-010              ← Other organs (GEOX, WELL, AAA, A-FORGE, etc.)
    │
    └── 011_WEALTH_MANDATE.md ← THIS ORGAN
           │
           ├── Invariants (compute-only, evidence-tagged, kernel-gated)
           ├── Boundaries  (OWNS: NPV/IRR/EMV · NEVER: allocate/trade/hide)
           └── 12 Ω-WEALTH Domains (Conservation through Hysteresis)
```

**Status:** `011_WEALTH_MANDATE.md` exists as a stub. Full canon expansion pending F13
sovereign ratification. All invariants enumerated in `INVARIANTS.md` and `BOUNDARY.md`
are enforced at runtime regardless of canon formalization status.

---

## 16. License & Sovereignty

### License

**AGPL-3.0** — GNU Affero General Public License v3.0.

See [LICENSE](LICENSE) for the full text.

This means:
- ✅ You can use WEALTH for any purpose
- ✅ You can study and modify the source code
- ✅ You can distribute copies
- ⚠️ If you run a modified WEALTH as a network service, you MUST release your changes under AGPL-3.0
- ⚠️ This is a **strong copyleft** license — it protects the freedom of the code even when used over a network

> **Note:** A stale line in an older README referenced `PROPRIETARY` license. This was a known
> documentation anomaly that has been resolved. The canonical license is AGPL-3.0 as declared in `pyproject.toml`,
> `package.json`, and this README.

### Sovereignty

```
███████╗ ██████╗ ██╗   ██╗███████╗██████╗ ███████╗██╗ ██████╗ ███╗   ██╗
██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔════╝██║██╔════╝ ████╗  ██║
███████╗██║   ██║██║   ██║█████╗  ██████╔╝█████╗  ██║██║  ███╗██╔██╗ ██║
╚════██║██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██╔══╝  ██║██║   ██║██║╚██╗██║
███████║╚██████╔╝ ╚████╔╝ ███████╗██║  ██║███████╗██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

**WEALTH serves one sovereign:** Muhammad Arif bin Fazil.

- **Arif is F13.** His veto is absolute. No algorithm overrides his judgment.
- **WEALTH computes. arifOS judges. Arif decides.** This chain is not negotiable.
- **The VAULT999 seal is final.** Every irreversible capital verdict is recorded in the append-only, hash-chained immutable ledger.
- **The Adat Agentik layer applies.** Malu (shame) score, Maruah (dignity) index, and Tebus Salah (restitution) are operative runtime concepts in WEALTH's governance boundary.

The constitutional floors are not optional. The epistemic tags are not decorative.
The human veto is not a formality. This is not SaaS. This is not a startup.

**This is the perlembagaan for capital in the age of agentic AI.**

---

<div align="center">

```
     WEALTH computes the value.
     arifOS judges the verdict.
     Arif makes the decision.
     VAULT999 seals the record.

     No organ may authorize its own execution.
     No tool may self-certify its own output.
     No algorithm may override the sovereign.

     DITEMPA BUKAN DIBERI — Forged, Not Given.
```

</div>

---

*README v3.0.0 · Forged 2026-06-12 by Omega (Ω) · arifOS Federation*
*Canonical source: `git@github.com:ariffazil/wealth.git` · Branch: `main` · HEAD: `b06f8b8`*
*999 SEAL ALIVE*
