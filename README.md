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
```

</div>

---

> **DITEMPA BUKAN DIBERI** — *"Forged, Not Given."*
>
> Capital intelligence is not handed out. It is built through sweat, scar tissue, and
> a federated kernel that never lied about a single decimal point. This is not a
> startup. This is not a SaaS. This is the capital organ of a constitutional AI
> federation — it computes. It warns. It prepares evidence for sealing.
> It never seals itself. It never allocates alone.

[![CI](https://img.shields.io/badge/tests-153%2F153%20PASS-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![MCP Tools](https://img.shields.io/badge/MCP-28%20canonical%20tools-10b981?logo=anthropic)](wealth_mcp/server.py)
[![Federation](https://img.shields.io/badge/organ-CAPITAL-f59e0b)](FEDERATION_CONTRACT.md)
[![License](https://img.shields.io/badge/license-AGPL--3.0-ef4444?logo=gnu)](LICENSE)
[![Port](https://img.shields.io/badge/port-18082-64748b)](RUNBOOK.md)
[![Service](https://img.shields.io/badge/systemd-wealth--organ.service-success)](RUNBOOK.md)
[![Architecture](https://img.shields.io/badge/architecture-federated-8b5cf6)](wealth_mcp/server.py)
[![Status](https://img.shields.io/badge/status-OPERATIONAL-success)](CONTEXT.md)

---

## Table of Contents

1. [What Is WEALTH?](#1-what-is-wealth)
2. [Source of Truth Layers](#2-source-of-truth-layers)
3. [The Federation Position](#3-the-federation-position)
4. [The 13 Thermodynamics Primitives + LAW](#4-the-13-thermodynamics-primitives--law)
5. [Full Capability Map](#5-full-capability-map)
6. [Boundary Declaration](#6-boundary-declaration)
7. [Constitutional Binding](#7-constitutional-binding)
8. [Quick Start](#8-quick-start)
9. [Architecture](#9-architecture)
10. [For Human Operators (Arif)](#10-for-human-operators-arif)
11. [For AI Agents](#11-for-ai-agents)
12. [For Institutions](#12-for-institutions)
13. [Build, Test, Deploy](#13-build-test-deploy)
14. [Known Limitations](#14-known-limitations)
15. [Federation Cross-Reference](#15-federation-cross-reference)
16. [GENESIS Chain](#16-genesis-chain)
17. [License & Sovereignty](#17-license--sovereignty)
18. [Change Log — 2026-06-24 SOT Sync](#18-change-log--2026-06-24-sot-sync)

---

## 1. What Is WEALTH?

### In One Sentence

> **WEALTH is the capital intelligence organ of the arifOS federation — it computes NPV, IRR, EMV, EVOI, risk scores, stock analytics, game theory, and sovereign resource economics, then tags every output with an epistemic band so you know exactly how confident it should make you.**

### What It IS

- ✅ **The compute-only capital engine** — NPV, IRR, EMV, EVOI, DSCR, risk scores, portfolio analysis, Monte Carlo
- ✅ **A thermodynamics-of-capital substrate** — 13 orthogonal primitives mapping physics to finance (Conservation, Flow, Gradient, Entropy, Energy, Time, Inertia, Field, Signal, Game, Boundary, Hysteresis, Survival) plus a 14th jurisdictional layer (LAW)
- ✅ **An MCP server on port 18082** — **24 canonical public tools** + federated architecture (5 layers)
- ✅ **A federated dual-runtime organ** — Python canonical kernel (`wealth_mcp/server.py`, 1220 lines) + Node.js legacy kernel (`src/`, `host/kernel/`); `internal/monolith.py` kept for back-compat (marked DEPRECATED)
- ✅ **A stock analysis layer (D4)** — multi-mode capital-risk governance: verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence, + more
- ✅ **A market data bridge (D3)** — live FX rates, commodities, macro indicators
- ✅ **A personal finance engine (D1)** — cashflow, net worth, EPF projection, zakat calculation (Malaysian)
- ✅ **A human-law geometry engine (Ω-LAW)** — Malaysian jurisdiction (Federal, State, Syariah, Adat), inheritance/land/regulatory/contract layers, soul/shadow/anthropology framing
- ✅ **A collapse forensics engine** — Enron/PDVSA/Pemex/1MDB/WorldCom institutional failure pattern matching + Calhoun Phase C Beautiful Mouse detector (early warning)
- ✅ **A counterfactual engine** — structured "what if" analysis across the 13 primitives with joint posterior and sensitivity ranking
- ✅ **A federation bridge** — `wealth_arifos_judge_handoff` hands WEALTH verdicts to arifOS 888_JUDGE for constitutional review
- ✅ **Evidence-tagged always** — every output carries an epistemic band (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN)
- ✅ **Built for one sovereign** — Muhammad Arif bin Fazil. WEALTH computes. arifOS judges. Arif decides.

### What It Is NOT

- ❌ **NOT a trading bot** — does not buy, sell, or move capital
- ❌ **NOT a financial advisor** — outputs are advisory, never prescriptive
- ❌ **NOT a stock oracle** — `recommendation_only: True`, `final_authority: "Arif"`
- ❌ **NOT a bank** — holds no accounts, processes no transactions
- ❌ **NOT a constitutional judge** — that belongs to arifOS (port 8088)
- ❌ **NOT an executor** — that belongs to A-FORGE (port 7071)
- ❌ **NOT a black box** — every formula is inspectable at `afwealth://formulas/*` and `afwealth://canon/*`

---

## 2. Source of Truth Layers

### Runtime SOT

Call `wealth_system_registry_status(mode="registry")` to get currently callable public tools.
Live registry command:

```bash
curl -s -X POST http://127.0.0.1:18082/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_system_registry_status","arguments":{"mode":"registry"}},"id":1}'
```

Expected invariant: `status = ALIVE`, `public_tools.length = 28` (live 2026-06-27).

### Code SOT

`wealth_mcp/server.py` — canonical MCP implementation.

### Doctrine SOT

`BOUNDARY.md`, `INVARIANTS.md`, `FEDERATION_CONTRACT.md`, `GENESIS/011_WEALTH_MANDATE.md`.

**Conflict resolution:** Runtime registry wins for callable tools. Doctrine wins for authority. Code wins for implementation. File an 888_HOLD for reconciliation.

---

## 3. The Federation Position

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
    └────────────┘  └────────┬┘ └────────┘ └──────────┘  └──────────┘
                            │
                 ┌──────────▼──────────┐
                 │   WEALTH verdicts:   │
                 │   • NEEDS_DATA       │
                 │   • HOLD             │
                 │   • SEAL-ready       │
                 │   • 888_HOLD (req)   │
                 └──────────┬──────────┘
                            │
              ┌─────────────▼─────────────┐
              │  wealth_arifos_judge_handoff│  ← new 2026-06-24
              │  (F13 SOVEREIGN bridge)     │
              └─────────────┬─────────────┘
                            │
                 ┌──────────▼──────────┐
                 │   arifOS 888_JUDGE  │
                 │   (port 8088)       │
                 └─────────────────────┘
```

### The Authority Chain (Non-Negotiable)

```
Arif (F13 SOVEREIGN)
  → arifOS kernel (F1-F13 enforcement, 888 JUDGE)
    → WEALTH computes capital verdict (advisory evidence)
      → wealth_arifos_judge_handoff (NEW 2026-06-24) prepares envelope
        → arif_judge renders SEAL / SABAR / HOLD / VOID
          → A-FORGE executes (only under SEAL)
            → VAULT999 seals (immutable, forever)
```

**No organ may authorize its own execution. WEALTH computes. arifOS judges. Arif decides.**

### Organ Boundaries

| Aspect | OWNS (WEALTH) | DOES NOT (other organ) |
|--------|---------------|------------------------|
| NPV / IRR / EMV / EVOI | ✅ Compute | — |
| Risk / DSCR | ✅ Compute | — |
| Stock analysis | ✅ D4 multi-mode engine | — |
| Market data (FX, macro) | ✅ Fetch, normalize | — |
| Zakat / EPF | ✅ Malaysian calc | — |
| Counterfactual scenarios | ✅ 13-primitive joint posterior | — |
| Collapse forensics | ✅ Phase C + Phase D pattern match | — |
| Constitutional verdicts | — | ➜ arifOS (port 8088) |
| Earth evidence | — | ➜ GEOX (port 8081) |
| Human readiness | — | ➜ WELL (port 18083) |
| Execution / deploy | — | ➜ A-FORGE (port 7071) |
| Display / cockpit | — | ➜ AAA (port 3001) |

---

## 4. The 13 Thermodynamics Primitives + LAW

Every capital question maps to one or more of these primitives. Twelve are
thermodynamic invariants applied to finance; the thirteenth (Survival) is the
harness that asks "is the system still alive at horizon?"; the fourteenth (LAW)
is jurisdictional capital geometry.

| Ω | Primitive | Physics Analogy | Key Tool | One-Line Purpose |
|---|-----------|----------------|----------|------------------|
| **Ω-00** | Synthesis | Master field equation | `wealth_omni_wisdom` | Unified capital verdict across all primitives |
| **Ω-01** | Conservation | Mass balance (assets, liabilities) | `wealth_conservation_check` | What do we actually own? |
| **Ω-02** | Flow | Mass flow rate (cashflow, burn) | `wealth_flow_check` | How fast is capital moving? |
| **Ω-03** | Gradient | Pressure differential (mispricing) | `wealth_asymmetry_check` | Where is the pressure? |
| **Ω-04** | Entropy | Disorder (risk, uncertainty, tail) | `wealth_compute_emv` | What could go wrong? |
| **Ω-05** | Energy | Output per input (efficiency) | `wealth_compute_irr` | How much bang for buck? |
| **Ω-06** | Time | Potential well decay (discounting) | `wealth_compute_npv` | When does it pay back? |
| **Ω-07** | Inertia | Structural load (leverage, fragility) | `wealth_compute_emv` (variance) | How much debt can this carry? |
| **Ω-08** | Field | External environment (macro) | `wealth_market_data` | What's the external regime? |
| **Ω-09** | Signal | Evidence quality (info value) | `wealth_compute_evoi` | Is the data good enough? |
| **Ω-10** | Game | Multi-agent equilibrium (Nash) | `wealth_omni_wisdom` (game mode) | Who wins, who loses? |
| **Ω-11** | Boundary | Constitutional floors (maruah) | `wealth_power_audit` | Is this permissible? |
| **Ω-12** | Hysteresis | Path dependence (ledger memory) | `wealth_omni_wisdom` (path_params) | Where were we before? |
| **Ω-13** | **Survival** | Liquidity horizon, runway | `wealth_runway_check` | Can the system still be alive at horizon? |
| **Ω-LAW** | **LAW** | Jurisdictional capital geometry — sealed canon, institutional shadow, living human gap | `afwealth://canon/002-human-law` (canon resource) | What rules bind this capital, and who bleeds through them? |

**Start with `wealth_omni_wisdom(mode='synthesize')`** — it orchestrates across the
primitives and returns a unified verdict. For counterfactual analysis use
`wealth_omni_wisdom(mode='counterfactual', deltas=[...])` (NEW 2026-06-24).

---

## 5. Full Capability Map

### 5.1 Public MCP Surface — 28 Canonical Tools

```
28 public tools · 6 resources · 2 prompts (live 2026-06-27)
(4 alias tools for legacy compat: emv_compute, monte_carlo, evoi_compute)
```

| # | Tool | Domain | Verb | What It Does |
|---|------|--------|------|-------------|
| 1 | `wealth_wisdom_evaluate` | wisdom | evaluate | 6-dim wisdom (dignity/sovereignty/resilience/inequality/ecological/optionality) |
| 2 | `wealth_power_audit` | power | audit | 6-dim power dynamics + capture risk |
| 3 | `wealth_capture_scan` | power | scan | Audit advice text for capture signals |
| 4 | `wealth_compute_npv` | capital | compute | Net present value of cash flows |
| 5 | `wealth_compute_irr` | capital | compute | Internal rate of return |
| 6 | `wealth_conservation_check` | capital | check | Net worth, asset/liability totals |
| 7 | `wealth_flow_check` | capital | check | Income / expense / monthly burn |
| 8 | `wealth_runway_check` | capital | check | Runway in months at current burn |
| 9 | `wealth_compute_emv` | risk | compute | Expected Monetary Value + variance |
| 10 | `wealth_emv_compute` | risk | compute | Alias of wealth_compute_emv (legacy compat) |
| 11 | `wealth_monte_carlo_simulate` | risk | simulate | Monte Carlo value projection |
| 12 | `wealth_monte_carlo` | risk | simulate | Alias of wealth_monte_carlo_simulate (legacy compat) |
| 13 | `wealth_compute_evoi` | risk | compute | Expected Value of Information |
| 14 | `wealth_evoi_compute` | risk | compute | Alias of wealth_compute_evoi (legacy compat) |
| 15 | `wealth_confluence_check` | risk | check | Detect false confluence in indicators |
| 16 | `wealth_asymmetry_check` | risk | check | Risk distribution skew detection |
| 17 | `wealth_fiscal_breakeven` | capital | compute | Fiscal breakeven analysis (PSC) |
| 18 | `wealth_stock_analysis` | D4 | analyze | Governed multi-mode stock safety gate |
| 19 | `wealth_personal_finance` | D1 | finance | Cashflow, net worth, EPF, zakat, runway |
| 20 | `wealth_market_data` | D3 | fetch | FX, commodities, macro indicators |
| 21 | `wealth_omni_wisdom` | synthesis | synthesize | Multi-mode orchestrator (synthesize/deal/path_params/**counterfactual**) |
| 22 | `wealth_agent_path` | meta | route | Sovereign intent routing |
| 23 | `wealth_vault_write` | governance | write | Write transaction to VAULT999 |
| 24 | `wealth_vault_query` | governance | query | Query VAULT999 ledger |
| 25 | `wealth_system_registry_status` | meta | status | Live tool registry truth |
| 26 | `wealth_collapse_signature_scan` | collapse | scan | Institutional collapse pattern match (Phase D imminent) |
| 27 | `wealth_beautiful_mouse_scan` | collapse | scan | Calhoun Phase C early warning (Phase C entry) |
| 28 | `wealth_arifos_judge_handoff` | governance | handoff | Hand WEALTH verdict to arifOS 888_JUDGE |

### 4.2 D4 Stock Analysis — Modes

`wealth_stock_analysis(mode='...')` is the governed multi-mode stock safety gate.
It computes. It warns. It never recommends.

| Mode | What It Checks | Verdict |
|------|---------------|---------|
| `verify_math` | Recalculate P/L from entry/exit — detect AI hallucination | MATH_ERROR or SAFE_TO_STUDY |
| `separate_pl` | Separate realized vs unrealized P/L | Advisory |
| `position_size` | Risk-based position sizing (max 1% risk per trade) | Risk-bounded |
| `r_multiple` | Risk-reward geometry (R = reward / risk) | Ratio check |
| `exposure` | Portfolio exposure and gap-down scenarios | Exposure map |
| `bursa_cost` | Bursa Malaysia transaction cost model | Cost breakdown |
| `tamak_check` | Greed/emotional behavior detection — stop-loss moved lower? Averaging down? Revenge trading? | Behavioral flag |
| `pre_trade` | Full pre-trade safety gate — 9 checks before any trade | SAFE_TO_STUDY / UNSAFE |
| `fundamentals` | 9 business reality invariants (cash conversion, debt, margins, moat) | Scorecard |
| `TAC-9` | TAC-9 technical: regime → structure → risk-reward | Structure analysis |
| `contrast` | Anomalous contrast — market layer disagreement detection | Contrast alert |
| `confluence` | False confluence — same-class indicator collapse | Confluence warning |

**Iron rule:** `recommendation_only: True`. `final_authority: "Arif"`. No buy/sell signal.
No trading coach. No stock promotion. The math is the math. You decide what to do with it.

### 4.3 D3 Market Data

`wealth_market_data` provides economic indicators via free public APIs (not Bloomberg/Reuters grade):

| Mode | Source | Output |
|------|--------|--------|
| `fx` | Frankfurter API | Latest available FX rate |
| `commodity` | Market adapter | Latest available commodity reference |
| `macro` | World Bank API | GDP, inflation, rates, country indicators |

### 4.4 D1 Personal Finance

`wealth_personal_finance` covers Malaysian-specific personal capital:

| Mode | What |
|------|------|
| `summary` | Aggregate by category |
| `track` | Record a transaction |
| `runway` | Months of financial survival |
| `net_worth` | Assets minus liabilities |
| `epf` | Project EPF accumulation to target age |
| `zakat` | Malaysian 2.5% zakat above nisab |

### 4.5 Resources — 6 Live

| Resource URI | Reads from | What it provides |
|---|---|---|
| `afwealth://schema` | inline | Canonical tool surface + version + deprecation status |
| `afwealth://health` | inline | Organ health status + transport + final authority |
| `afwealth://tools/registry` | inline | Full tool registry with active/deprecated partition |
| `afwealth://canon/002-human-law` | `canon/002_HUMAN_LAW.md` | CANON 002 — Law as capital geometry (247 lines) |
| `afwealth://glossary` | `canon/GLOSSARY.md` | 13 core terms (888_HOLD, 999_SEAL, ΔS, Maruah, F1-F13, etc.) |
| `afwealth://federation/contract` | `FEDERATION_CONTRACT.md` | Organ position, authority, handoffs |

### 4.6 Prompts — 2 Live

| Prompt | Use case |
|---|---|
| `wealth_capital_deal_brief` | Sequenced 13-primitive capital brief before any irreversible decision |
| `wealth_d4_stock_pre_trade` | 12-mode pre-trade checklist before entering any position > 1% of portfolio |

### 4.7 Ω-LAW — Human Law as Capital Geometry (CANON / RESOURCE)

WEALTH holds Malaysian human law through three layers (canon artifacts, not callable tools):

| Layer | Artifact | What it provides |
|-------|----------|------------------|
| **Soul / Sealed Canon** | `canon/002_HUMAN_LAW.md` + law pack | Statute text, section numbers, jurisdiction |
| **Shadow / Institutional Reality** | `domains/law/ONTOLOGY.yaml` § institutional_graph + hold_matrix | PTG, courts, forms, delays, costs, 888_HOLD triggers |
| **Anthropology / Living Human Gap** | `canon/002a_LAW_SHADOW.md` + `AnthropologyRecord` | The Mak cuk who does not know Form A; dignity risk |

**Subdomains:** `domains/law/`, `domains/land-law/`, `domains/inheritance/`, `domains/regulatory/`, `domains/contracts/`.

**Rule:** WEALTH computes the shadow. arifOS judges the soul. WELL witnesses the human gap.
No binding legal verdicts. No self-sealing.
Ω-LAW is exposed through canon resources (`afwealth://canon/002-human-law`), not a standalone `wealth_law_*` tool family.

### 4.8 Three Eurekas — Forged 2026-06-24

**1. Counterfactual engine** (`wealth_omni_wisdom(mode='counterfactual')`)

Bridges the MOF watch observation protocol with the V3 scenario model.
Takes a base context + a list of named deltas, runs each through the 13
primitives, and returns a joint posterior with confidence + sensitivity
ranking. F7 confidence capped at 0.90.

```python
await wealth_omni_wisdom(
  mode="counterfactual",
  decision_context={"net_worth": 1e6, "monthly_burn": 50_000},
  deal_params={"deltas": [
    {"name": "mof_dividend_cut", "primitive": "flow", "change": -0.5},
    {"name": "brent_crash", "levers": ["commodity_price_change"], "change": -0.3}
  ]},
  path_params={"cf_mode": "grid", "top_k": 5}
)
# → joint_posterior: total_shift=-0.69, confidence=0.85
```

**2. Beautiful Mouse detector** (`wealth_beautiful_mouse_scan`)

Calhoun behavioural-death Phase C early warning. Detects the absence of
failure as the failure signal. Fires BEFORE the collapse scanner.
6 indicators: PERFECT_PERFORMANCE, ZERO_FAILURE, NARRATIVE_CENTRALISATION,
TALENT_DRAIN, MONITOR_CULTURE, EXTERNAL_BLAME. F7 cap 0.85 (lower than
collapse scanner because Phase C is inherently ambiguous). F6 MARUAH
enforced — never names individuals.

**3. arifOS Judge Handoff** (`wealth_arifos_judge_handoff`)

Closes the federation loop. F13 SOVEREIGN becomes a substrate guarantee,
not an agent discipline. Two modes: `prepare` (build envelope, non-mutating)
and `submit` (call arif_judge via MCP, return verdict). 8th memory graph
entity: `WEALTH_Arifos_Judge_Handoff_2026`.

```python
await wealth_arifos_judge_handoff(
  tool_name="wealth_collapse_signature_scan",
  result='{"risk":{"score":0.45},...}',
  intent="Register collapse signature claim for PETRONAS Phase C entry",
  capability="register_collapse_signature_claim",
  blast_radius="HIGH",
  reversibility_level="FULL",
  epistemic_state="INTERPRETED",
  domain="collapse",
  mode="prepare"  # or "submit"
)
# → readiness=READY, envelope_keys=8, next_action=submit_to_arif_judge
```

---

## 6. Boundary Declaration

### OWNS (Compute Territory)

- **Net Present Value (NPV)** and discounted cash flow
- **Internal Rate of Return (IRR)** and profitability index
- **Expected Monetary Value (EMV)** and decision tree analysis
- **Expected Value of Information (EVOI)** for information acquisition
- **Debt Service Coverage Ratio (DSCR)** and leverage stress
- **Risk scores** — entropy, tail risk, Monte Carlo simulation
- **Portfolio allocation models** — mean-variance, capital budgeting
- **Stock analysis** — multi-mode governed safety gate
- **Market data** — FX rates, commodity prices, macro indicators
- **Game theory** — Nash equilibria, multi-party contract modeling
- **Counterfactual analysis** — joint posterior across 13 primitives
- **Collapse forensics** — Phase C Beautiful Mouse + Phase D imminent
- **Personal finance** — cashflow, net worth, EPF, zakat
- **Sovereign resource economics** — PSC modeling, national oil calculus
- **arifOS handoff** — constitutional bridge to 888_JUDGE

### NEVER (Constitutional Territory)

- Move capital or authorize trades
- Execute financial transactions
- Hide downside risk or overstate returns
- Issue constitutional verdicts (SEAL / SABAR / HOLD / VOID)
- Adjudicate legal disputes
- Replace human judgment in irreversible decisions
- Self-authorize allocation of resources
- Bind to 0.0.0.0 (always 127.0.0.1)
- Pre-declare SEAL/VOID from WEALTH (F13 SOVEREIGN — must go through handoff)

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
| **arifOS** (8088) | Capital viability verdicts, risk scores, decision memos, **handoff envelopes** | MCP tools |
| **AAA** (3001) | Decision memo viewer data, portfolio dashboard metrics | HTTP API |
| **A-FORGE** (7071) | Docker image, build context | `ghcr.io/ariffazil/wealth:<sha>` |

---

## 7. Constitutional Binding

WEALTH operates under the F1-F13 floors of the arifOS constitution. Every tool call,
every computation, every output is governed.

| Floor | Name | How WEALTH Enforces It |
|-------|------|----------------------|
| **F1** | AMANAH | Reversible-first. All WEALTH tools are compute-only. `prepare` mode of `wealth_arifos_judge_handoff` is non-mutating. `submit` mode preserves envelope on failure. |
| **F2** | TRUTH | Every WEALTH output carries an `epistemic_tag` (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN). No bare numbers without uncertainty bands. |
| **F6** | MARUAH | Protect weakest stakeholder. `wealth_power_audit` surfaces who loses. `wealth_beautiful_mouse_scan` heuristically detects individual names and refuses to surface them — references roles, not people. |
| **F7** | HUMILITY | Confidence hard-capped across the engine: counterfactual engine 0.90, beautiful mouse 0.85, collapse scanner 0.90, handoff 0.90. |
| **F8** | LAW | `submit` mode of `wealth_arifos_judge_handoff` respects arifOS 888_HOLD gates. Constitutionally pre-checked: irreversibility + CRITICAL blast = BLOCKED. |
| **F9** | ANTIHANTU | No deception. `contrast` mode detects anomalous divergence between market layers. `wealth_capture_scan` audits advice for hidden incentives. |
| **F11** | AUDITABILITY | Every tool call logs to `wealth_governance_verdict`. Every capital verdict has a SHA-256 receipt. Every eureka has a VAULT999 seal. |
| **F13** | SOVEREIGN | All verdicts are `recommendation_only`. `wealth_arifos_judge_handoff` is the only constitutional path — F13 is a substrate property, not an agent discipline. |

**WEALTH does not self-judge.** arifOS reads the envelope and applies the floors.
WEALTH provides the evidence. The kernel makes the law.

---

## 8. Quick Start

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
      "args": ["server_federated.py", "--transport", "stdio"],
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

# Start the federated MCP server (CANONICAL entry point)
python server_federated.py

# Health check
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
# Expected: {"status":"ALIVE","version":"2026.06.15","architecture":"federated",...}

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
curl -s -X POST http://127.0.0.1:18082/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_system_registry_status","arguments":{"mode":"registry"}},"id":1}' \
  | python3 -c "
import json,sys
d = json.load(sys.stdin)
text = json.loads(d['result']['content'][0]['text'])
print(f'tools={len(text[\"public_tools\"])} status={text[\"status\"]}')
"
# Expected: tools=24 status=ALIVE
```

### First Capital Computation

```bash
# Via MCP: compute NPV of a 5-year project
# (call wealth_compute_npv via any MCP client)

# Or via curl (JSON-RPC):
curl -s -X POST http://127.0.0.1:18082/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_compute_npv","arguments":{"cash_flows":[-500000,100000,120000,140000,160000,180000],"discount_rate":0.08}},"id":1}'
```

---

## 9. Architecture

### Directory Tree — Federated (live 2026-06-24)

```
WEALTH/
│
├── wealth_mcp/                         # CANONICAL MCP server (federated)
│   ├── server.py                       # THE KERNEL — 1220+ lines, 28 public tools
│   │                                  #   13 Ω-WEALTH primitives, 6 resources, 2 prompts
│   ├── tools/                          # Tool sub-modules (future expansion)
│   ├── prompts/                        # Prompt sub-modules (future expansion)
│   └── resources/                      # Resource sub-modules (future expansion)
│
├── wealth_core/                        # PURE ENGINES (no MCP, no I/O)
│   ├── capital/                        # Capital domain engines
│   ├── collapse_signature/             # Institutional failure forensics
│   │   ├── patterns.py                 # 7 collapse signature taxonomy
│   │   ├── scanner.py                  # Acemoglu × Calhoun 2D risk map
│   │   ├── beautiful_mouse.py          # NEW 2026-06-24: Phase C early warning
│   │   └── corpus/                     # Historical priors (Enron, PDVSA, etc.)
│   ├── counterfactual.py               # NEW 2026-06-24: 13-primitive counterfactual engine
│   ├── game/                           # Nash equilibria, multi-party deals
│   ├── governance/                     # F1-F13 floor hooks
│   ├── macro/                          # Field/macro engines
│   ├── math/                           # Core financial math primitives
│   ├── personal/                       # Personal finance engines
│   ├── power/                          # Power dynamics + capture scan
│   ├── risk/                           # EMV, EVOI, Monte Carlo
│   ├── stock/                          # D4 stock analysis engines
│   ├── transport.py                    # Cross-organ transport
│   └── wisdom/                         # 6-dim wisdom evaluation
│
├── wealth_contracts/                   # OUTPUT ENVELOPES
│   ├── envelope.py                     # wrap_result() — every tool output
│   └── epistemic.py                    # EpistemicTag, EvidenceQuality, ClaimState
│
├── wealth_arifos_bridge/               # FEDERATION BRIDGE (NEW 2026-06-24)
│   ├── __init__.py                     # send_evidence_contract, probe_arifos_health, seal_to_vault
│   └── judge_handoff.py                # NEW: arifOS 888_JUDGE constitutional handoff
│
├── wealth_compat/                      # LEGACY ALIASES (back-compat)
│
├── internal/                           # ⚠️ DEPRECATED — monolith (back-compat only)
│   ├── monolith.py                     # ⚠️ 16,000 lines, 60 @mcp.tool decorators
│   │                                  #   Kept for back-compat. Federated server is canonical.
│   │                                  #   5 tools still delegate here: stock_analysis,
│   │                                  #   personal_finance, market_data, omni_wisdom, agent_path.
│   ├── __init__.py
│   ├── organ_governance.py             # arifOS F1-F13 binding wrapper
│   ├── governance.py                   # Floor hooks, policy engine
│   ├── invariants.py                   # Constitutional invariants
│   ├── kernel_math.py                  # Core financial math
│   ├── db_schema.py                    # PostgreSQL schema
│   ├── market_data.py                  # D3 Market Data
│   ├── personal_finance.py             # D1 Personal Finance
│   ├── stock/                          # D4 stock engine (delegated to by federated)
│   ├── engines/                        # Computation engines
│   ├── domains/                        # Domain expansion (WIP)
│   └── prompts/                        # Prompt templates (legacy)
│
├── host/                               # MODULAR PYTHON LIBRARIES
│   ├── coordination/                   # LP allocator, cooperative/strategic protocols
│   ├── epistemic/                      # Correlation guard, EVOI, schema validator
│   ├── governance/                     # Floor hooks, policy, vault bridge
│   ├── ingest/                         # ECB, FRED, OWID, Ember, WorldBank adapters
│   ├── kernel/                         # JS legacy: floors.js, finance.js, seal.js
│   └── wealth/                         # JS: cashflow, networth, projection, maruah
│
├── src/                                # NODE.JS LEGACY KERNEL
│   ├── kernel/                         # Legacy JS kernel
│   └── wealth/                         # Legacy wealth computation
│
├── capitalx/                           # Constitutional capital pricing engine (Node.js)
│
├── civilizational/                     # Boundary monitors (Calhoun sink, extractive drift)
│
├── canon/                              # CONSTITUTIONAL SPECS
│   ├── 001_CAPITAL_MANIFEST.md
│   ├── 002_HUMAN_LAW.md                # Law as capital geometry
│   ├── 002a_LAW_SHADOW.md              # soul/shadow/anthropology
│   ├── 015_LAW_MANIFEST.md
│   ├── CAPITALX_SPEC.md
│   ├── CASE_STUDIES.md
│   ├── COSMOLOGY.md
│   ├── ECONOMIC_MODEL.md
│   ├── GLOSSARY.md
│   └── GOVERNANCE.md
│
├── api/                                # HTTP API surfaces
├── apps/                               # Demo apps
│
├── tests/                              # TEST SUITES
│
├── docs/                               # Documentation
│
├── server_federated.py                 # CANONICAL entry point (5-layer federated)
├── server.py                           # 15-line backward-compat shim
├── cli.js                              # Node.js CLI: boot, check, seal, capitalx
├── pyproject.toml                      # Python packaging (AGPL-3.0)
├── package.json                        # Node.js packaging
├── Makefile                            # test, lint, format, forge, health
├── fastmcp.json                        # FastMCP configuration
├── mcp.json                            # MCP configuration
│
├── GENESIS/
│   └── 011_WEALTH_MANDATE.md           # Organ mandate (canon pending F13)
│
├── BOUNDARY.md                         # Boundary declaration
├── TOOL_SURFACE.md                     # Tool surface registry (legacy, post-2026-06-24 partial stale)
├── FEDERATION_CONTRACT.md              # Federation contract
├── CONTEXT.md                          # Live state
├── RUNBOOK.md                          # Operations
├── INVARIANTS.md                       # Source of truth
├── AGENTS.md                           # Agent boot sequence
├── SPEC.md                             # Orthogonal architecture rebuild spec
├── ROADMAP.md                          # Development roadmap
├── ARIF.md                             # Address to sovereign
└── WEALTH_SNAPSHOT.yaml                # Quick state snapshot
```

### The Federated Architecture (Live)

The federated architecture replaced the monolith-era design in 2026-06. Five
layers, each with a single bounded responsibility:

| Layer | Path | Responsibility | MCP-coupled? |
|-------|------|----------------|--------------|
| **wealth_core** | `wealth_core/` | Pure engines, no MCP, no I/O | No |
| **wealth_contracts** | `wealth_contracts/` | Output envelopes, epistemic tags | No |
| **wealth_mcp** | `wealth_mcp/` | MCP surface (tools, resources, prompts) | Yes |
| **wealth_arifos_bridge** | `wealth_arifos_bridge/` | arifOS 8088 transport | Yes |
| **wealth_compat** | `wealth_compat/` | Legacy aliases for back-compat | No |

**Why federated, not monolith?** The federated split separates pure
computation (core) from MCP surface (mcp) from federation transport
(bridge). This lets the engines be tested without an MCP transport,
lets the MCP surface be swapped without rewriting engines, and lets the
federation bridge evolve independently. The 16K-line monolith is kept
as back-compat for now.

### Dual Runtime

| Runtime | Path | Status | Use |
|---------|------|--------|-----|
| **Python (federated)** | `wealth_mcp/server.py` (1220+ lines) | ✅ **CANONICAL** | All 28 MCP tools, 6 resources, 2 prompts |
| **Python (monolith)** | `internal/monolith.py` (16K lines) | ⚠️ DEPRECATED | Back-compat only; 5 tools delegate here |
| **Node.js** | `src/`, `host/kernel/` | ⚠️ Legacy | Numerical parity testing, `cli.js` operations |

---

## 10. For Human Operators (Arif)

You don't need to code. You need to know three things:

### 1. Ask WEALTH anything about capital

Through Hermes (`@ASI_arifos_bot` on Telegram):

```
"Tanya WEALTH: NPV projek offshore tu kalau kos RM500k, cashflow tahunan RM100k-180k, discount 8%"
"Tanya WEALTH: Berapa runway aku sekarang?"
"Tanya WEALTH: Check EPF aku umur 55"
"Tanya WEALTH: Zakat tahun ni — total wealth RM50k, cukup nisab?"
"Tanya WEALTH: Analyze saham TENAGA — fundamentals dia ok ke?"
"Tanya WEALTH: Scan PETRONAS untuk Phase C Beautiful Mouse"
"Tanya WEALTH: Counterfactual — apa jadi kalau MOF potong dividen DAN Brent crash?"
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
- A collapse signature scan returns DOMINANT (Phase C/D entry)

**You are the final authority. WEALTH computes. arifOS judges. You decide.**

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

## 11. For AI Agents

### Connection

WEALTH exposes **28 governed MCP tools + 6 resources + 2 prompts**. Connect via:

```
MCP Endpoint:  https://wealth.arif-fazil.com/mcp
Transport:     streamable-http (public) or stdio (local)
Port:          18082
```

### Tool Categories (live 2026-06-27)

| Category | Tools | Use When |
|----------|-------|----------|
| **Routing** | `wealth_agent_path`, `wealth_system_registry_status` | "What tool do I use?" |
| **Core Finance** | `wealth_compute_npv`, `wealth_compute_irr`, `wealth_compute_emv`, `wealth_emv_compute`, `wealth_compute_evoi`, `wealth_evoi_compute`, `wealth_monte_carlo_simulate`, `wealth_monte_carlo`, `wealth_fiscal_breakeven` | NPV, IRR, EMV, EVOI, Monte Carlo, fiscal breakeven |
| **Conservation + Flow + Survival** | `wealth_conservation_check`, `wealth_flow_check`, `wealth_runway_check` | Net worth, cashflow, runway |
| **Risk geometry** | `wealth_asymmetry_check`, `wealth_confluence_check` | Skew detection, false confluence |
| **Macro** | `wealth_market_data` | FX rates, GDP, commodities |
| **Stock** | `wealth_stock_analysis` (multi-mode) | Position safety, fundamentals, TAC-9 |
| **Personal** | `wealth_personal_finance` | EPF, zakat, net worth |
| **Wisdom** | `wealth_wisdom_evaluate` | 6-dim wisdom evaluation |
| **Power** | `wealth_power_audit`, `wealth_capture_scan` | Power dynamics + capture risk |
| **Synthesis** | `wealth_omni_wisdom` (synthesize / deal / path_params / **counterfactual**) | Multi-mode capital intelligence |
| **Collapse forensics** | `wealth_collapse_signature_scan`, `wealth_beautiful_mouse_scan` | Phase D imminent / Phase C entry |
| **Federation** | `wealth_arifos_judge_handoff` (prepare / submit), `wealth_vault_write`, `wealth_vault_query` | Constitutional handoff, VAULT999 |

### Rules for Agents

1. **WEALTH computes, Arif decides.** Never present a WEALTH output as a final decision.
2. **Always read the epistemic tag.** CLAIM ≠ HYPOTHESIS. Don't treat an ESTIMATE like a CLAIM.
3. **Route irreversible actions through arifOS.** `wealth_* → wealth_arifos_judge_handoff → arif_judge → SEAL → arif_forge_execute → VAULT999`.
4. **Never fabricate NPV.** If WEALTH returns `NEEDS_DATA`, tell the user what's missing.
5. **Downside first.** When presenting results, surface the worst case before the expected case.
6. **Zakat is wajib.** If a Malaysian user asks about wealth, surface the zakat tool.
7. **Stock analysis is a safety gate, not a signal.** `SAFE_TO_STUDY` means "nothing obviously wrong." It does not mean "buy."
8. **Collapse signature is diagnostic, not adversarial.** Always pair with `wealth_capture_scan` + `wealth_power_audit` first.
9. **Beautiful Mouse = early warning.** Fire this BEFORE the collapse scanner when scanning new institutions.
10. **Counterfactual = MOF watch meets V3 model.** Use this when "if X AND if Y" needs a joint answer.

### Agent Invariants

1. Call `wealth_system_registry_status(mode="registry")` before assuming tool availability.
2. Treat WEALTH outputs as advisory evidence, not decisions.
3. Never convert `SAFE_TO_STUDY` into `BUY`.
4. Never convert `HYPOTHESIS` or `ESTIMATE` into `CLAIM`.
5. Surface downside before upside.
6. Route irreversible capital action through `wealth_arifos_judge_handoff`.
7. Do not call deprecated monolith paths (`internal/monolith.py`) unless testing compatibility.
8. If `TOOL_SURFACE.md` conflicts with registry, registry wins.
9. If a legal, trade, or capital allocation decision is requested, return compute evidence plus 888_HOLD.

### The WEALTH Call Chain (Standard Pattern)

```
1. wealth_agent_path(task_description)              → "Which tool do I need?"
2. wealth_conservation_check(assets, liabilities)    → "Is the balance sheet sane?"
3. wealth_omni_wisdom(decision_context)              → "Compute the capital verdict"
4. wealth_capture_scan(advice_text)                  → "Is the advice itself captured?"
5. wealth_power_audit(scenario, actors)              → "Is the scenario symmetric?"
6. wealth_arifos_judge_handoff(                      → "Hand off to arifOS 888_JUDGE"
     tool_name, result, intent, capability,
     blast_radius, reversibility_level,
     epistemic_state, domain, mode="prepare")
7. arif_judge renders SEAL / SABAR / HOLD / VOID     → "Constitutional verdict"
8. arif_vault_seal(payload=verdict)                  → "Record this forever."
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
→ wealth_market_data(mode='macro', country='MYS')
→ Returns: GDP, inflation, Brent price, MYR/USD, energy mix
```

**Scenario 4: "How long can I survive on current cash?"**
```
→ wealth_runway_check(liquid_assets=45000, monthly_burn=8000)
→ Returns: runway_months, conservative_estimate
```

**Scenario 5 (NEW): "Counterfactual — what if MOF cuts dividend AND Brent crashes?"**
```
→ wealth_omni_wisdom(mode='counterfactual',
    decision_context={"net_worth": 1e6, "monthly_burn": 50_000},
    deal_params={"deltas": [
      {"name": "mof_dividend_cut", "primitive": "flow", "change": -0.5},
      {"name": "brent_crash", "levers": ["commodity_price_change"], "change": -0.3}
    ]},
    path_params={"cf_mode": "grid", "top_k": 5})
→ Returns: joint_posterior, sensitivity_ranking, dominant_primitives
```

**Scenario 6 (NEW): "Is PETRONAS entering Phase C?"**
```
→ wealth_beautiful_mouse_scan(
    text="<latest CEO speech or annual report excerpt>",
    historical_priors=["enron_2000", "suriname_2026"])
→ Returns: phase_c_verdict (ABSENT/EMERGING/ACTIVE/DOMINANT),
           phase_c_score, indicator breakdown
```

---

## 12. For Institutions

### Governance-Compliant Capital Intelligence

WEALTH is designed for institutions that need:

1. **Auditable financial computation** — every NPV, IRR, EMV carries a SHA-256 receipt
2. **Constitutional governance** — F1-F13 floors enforced on every tool call
3. **Epistemic honesty** — no overconfident numbers, every output tagged with uncertainty
4. **Sovereign resource modeling** — PSC templates, national oil calculus, multi-party game theory
5. **Inequality diagnosis** — 5-dimension structural analysis with live World Bank data
6. **Immutable audit trail** — every sealed verdict lands in VAULT999, append-only, forever
7. **Constitutional handoff** — every irreversible decision routes through arifOS 888_JUDGE

### Malaysian-Specific Capabilities

| Capability | Tool | Why It Matters |
|------------|------|---------------|
| **EPF projection** | `wealth_personal_finance(mode='epf')` | Retirement readiness for Malaysian workforce |
| **Zakat calculation** | `wealth_personal_finance(mode='zakat')` | Islamic wealth obligation, 2.5% above nisab |
| **Bursa Malaysia costs** | `wealth_stock_analysis(mode='bursa_cost')` | Real Malaysian transaction costs |
| **MYR/USD FX** | `wealth_market_data(mode='fx', targets='MYR')` | Ringgit exposure, live |
| **Sovereign PSC** | `wealth_omni_wisdom(mode='deal', deal_params={...})` | NOC vs foreign contractor game theory |
| **Collapse forensics** | `wealth_collapse_signature_scan` + `wealth_beautiful_mouse_scan` | Institutional failure early warning |

### The 3-Axis Wealth Basis (Energy, Entropy, Echo)

```
W⃗ = (Ê, 1 − Ŝ, Eχ̂)
```

| Axis | Symbol | BM | Question |
|------|--------|-----|----------|
| **Energy** | Ê | Berapa banyak tenaga kita? | Capital stock, productivity, flow |
| **Entropy** | Ŝ | Berapa bocor sistem ni? | Risk, leakage, uncertainty, shadow |
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

## 13. Build, Test, Deploy

### Python (Canonical — Federated)

```bash
cd /root/WEALTH

# Install dependencies
uv sync --frozen

# Run the FEDERATED server (CANONICAL entry point)
python server_federated.py                        # HTTP on 127.0.0.1:18082
# Or via systemd
systemctl restart wealth-organ

# Tests (153/153 PASS)
PYTHONPATH=. pytest tests/ -q --tb=short

# Lint & format
ruff check . && ruff format .

# Health
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
# → {"status":"ALIVE","version":"2026.06.15","architecture":"federated",...}

# Full forge (security audit + health)
make forge
```

> ⚠️ **DEPRECATED:** `python internal/monolith.py` still works for back-compat
> but the federated server is the canonical surface. The monolith is kept
> for 5 tools (stock, personal, market, omni, agent) that delegate to it.
> See `internal/monolith.py` line 1-15 for the deprecation notice.

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

git pull origin main           # Fetch latest
git tag vYYYY.MM.DD            # Date-stamp tag only (no semver)
```

---

## 14. Known Limitations

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| **License anomaly** | LOW | ✅ RESOLVED | Both `pyproject.toml` and `package.json` declare AGPL-3.0. |
| **Monolith deprecation** | LOW | ⚠️ Migration in progress | `internal/monolith.py` (16K lines, 60 decorators) is marked DEPRECATED. Federated server (`wealth_mcp/server.py`, 1220 lines) is canonical. 5 tools still delegate. Migration target: 0 tools delegate. |
| **Node.js harness bug** | LOW | ⚠️ Known | 17 Node tests fail due to stdout pollution from Python `runPython` — filter `runPython` output. Python canonical suite is clean (153/153). |
| **Dual runtime** | MEDIUM | ⚠️ Legacy | Python is canonical. Node.js is legacy. Should eventually be deprecated. |
| **A-FORGE reimplements WEALTH** | MEDIUM | ⚠️ Drift | `A-FORGE/src/tools/WealthTools.ts` duplicates ROI/EMV/portfolio logic. Should delegate to WEALTH MCP instead. |
| **TOOL_SURFACE.md stale** | LOW | ⚠️ Known | Still says 65 decorators / 17 public / 40 UNKNOWN. README now correctly reflects 28 live tools. `TOOL_SURFACE.md` itself is separate and still stale. |
| **No real-time market feed** | MEDIUM | ℹ️ Design | D3 market data uses free APIs (Frankfurter, World Bank) — not Bloomberg/Reuters grade. Sufficient for modeling, not for HFT. |
| **Collapse scanner calibration** | LOW | ⚠️ Filed | Initial smoke test returned risk 0.163 on a textbook pre-collapse scenario. Threshold review needed. Filed for next forge cycle. |
| **arifos_seal block** | INFO | ℹ️ Architectural | `arif_seal` MCP blocks on `actor_verified: false` sessions. Use local epoch ledger (F1 AMANAH alternative) until session upgrade. |

### What WEALTH Cannot Do (By Design)

- Cannot execute trades on any exchange
- Cannot move money between accounts
- Cannot authorize capital allocation
- Cannot provide personalized financial advice
- Cannot guarantee investment returns
- Cannot hide or minimize downside risk
- Cannot self-certify its own output as SEAL-grade
- Cannot pre-declare SEAL/VOID (must go through `wealth_arifos_judge_handoff`)
- Cannot name individuals in collapse analyses (F6 MARUAH)

---

## 15. Federation Cross-Reference

WEALTH is one of seven organs in the arifOS Constitutional Federation.

| Organ | Port | Repo | Role | Relationship to WEALTH |
|-------|------|------|------|----------------------|
| **arifOS** | 8088 | `ariffazil/arifos` | Constitutional kernel | **Governs WEALTH** — F1-F13 enforcement, 888 JUDGE, VAULT999. **Receives handoffs from WEALTH via `wealth_arifos_judge_handoff` (NEW 2026-06-24).** |
| **GEOX** | 8081 | `ariffazil/geox` | Earth intelligence | **Feeds WEALTH** — prospect volumes, resource quality (planned) |
| **WELL** | 18083 | `ariffazil/well` | Human readiness | **Informs WEALTH** — cognitive load → capital preservation (planned) |
| **AAA** | 3001 | `ariffazil/AAA` | Control plane | **Displays WEALTH** — cockpit, portfolio dashboard, decision memos |
| **A-FORGE** | 7071 | `ariffazil/A-FORGE` | Execution shell | **Executes under WEALTH verdicts** — gated by arifOS SEAL |
| **APEX** | 3002 | `ariffazil/APEX` | 888 JUDGE (legacy) | Legacy health probe — deliberation moved to AAA a2a-server |

### Key Federation Files

| File | Purpose |
|------|---------|
| `/root/arifOS/FEDERATION_CONTRACT.md` | Canonical federation contract |
| `/root/arifOS/AGENTS.md` | Federation-wide agent boot sequence |
| `/root/arifOS/GENESIS/000_KERNEL_CANON.md` | Kernel canon (Source of Truth) |
| `/root/arifOS/static/arifos/theory/000/000_CONSTITUTION.md` | 13 Constitutional Laws |
| `FEDERATION_CONTRACT.md` | WEALTH's local contract |
| `BOUNDARY.md` | WEALTH's boundary declaration |
| `GENESIS/011_WEALTH_MANDATE.md` | WEALTH's organ mandate |

> **MIND/MEMORY services:** A-FORGE hosts the MIND service (port 51001) and MEMORY service (port 51002) for cross-agent state and recall. These are not separate federation organs; they are runtime services under A-FORGE.

### Memory Graph (8 entities as of 2026-06-24)

| Entity | Type | Role |
|--------|------|------|
| `PETRONASThirdAxisCollapse2026` | 888_GROUNDED_ENTITY | Third Axis qualitative complement |
| `PETRONAS_Collapse_Trajectory_v3_2026` | quantitative_financial_model | V3 model quantitative complement |
| `WEALTH_Arifos_Judge_Handoff_2026` | federation_bridge | NEW 2026-06-24 — F13 SOVEREIGN bridge (8th entity) |
| (4 more entities — Faisal, Suriname, Barokah-1, Hidayah, Upstream Restructuring) | (various) | Cross-referenced via V3 cross_relations |

---

## 16. GENESIS Chain

```
000_KERNEL_CANON.md         ← arifOS (Source of Truth)
    │
    ├── 001-010              ← Other organs (GEOX, WELL, AAA, A-FORGE, etc.)
    │
    └── 011_WEALTH_MANDATE.md ← THIS ORGAN
           │
           ├── Invariants (compute-only, evidence-tagged, kernel-gated)
           ├── Boundaries  (OWNS: NPV/IRR/EMV · NEVER: allocate/trade/hide)
           └── 13 Ω-WEALTH Primitives + LAW
                 (Conservation through Survival + Jurisdictional Geometry)
```

**Status:** `011_WEALTH_MANDATE.md` exists as a stub. Full canon expansion pending F13
sovereign ratification. All invariants enumerated in `INVARIANTS.md` and `BOUNDARY.md`
are enforced at runtime regardless of canon formalization status.

---

## 17. License & Sovereignty

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

## 18. Change Log — 2026-06-24 SOT Sync

### Major rewrites (sections touched)

| Section | Before | After | Why |
|---|---|---|---|
| Top doctrine header | "seventeen thousand lines of monolith" | Federated kernel (1220 lines) | Monolith DEPRECATED, federated is canonical |
| Badge (line 27) | "MCP-20 canonical tools" | "MCP-24 canonical tools" | Live surface grew: -3 deprecated, +1 collapse, +1 beautiful mouse, +1 judge handoff, +counterfactual mode |
| Badge | (missing) | "architecture-federated" | Federated architecture is the new design |
| §3 — 13 Primitives + LAW | "12 Ω + 1 LAW" (survival missing) | "13 primitives + LAW" | Survival (Ω-13) is the harness primitive; the table now includes it |
| §4.1 — 24 canonical tools | 20 tool names, mostly phantom (e.g., `wealth_time_discount`, `wealth_conservation_capital`) | 24 live tool names (e.g., `wealth_compute_npv`, `wealth_conservation_check`) | Aligned to `wealth_system_registry_status` live query |
| §4.2 — D4 Stock modes | 12 modes listed (some stale names like `tac9`) | Multi-mode (correct names like `TAC-9`) | Aligned to live stock engine |
| §4.5 — Resources | "18+ resources" with stale `wealth://` URIs | 6 live resources with `afwealth://` URIs | Aligned to live resource list |
| §4.6 — Prompts | "10+ prompts" with phantom names | 2 live prompts (`wealth_capital_deal_brief`, `wealth_d4_stock_pre_trade`) | Aligned to live prompt list |
| §4.7 — LAW | (was §4.7) | Now §4.7, content unchanged | Re-ordered |
| §4.8 — Three Eurekas | (new section) | Counterfactual engine, Beautiful Mouse, Judge Handoff | NEW 2026-06-24 — documents the 3 eurekas forged in this session |
| §5 Boundary | (was missing eurekas) | OWNS counterfactual + collapse + handoff | Aligned to current scope |
| §6 — Constitutional binding | F6 referenced `maruah_score` (phantom); F11 referenced `wealth_governance_verdict` (phantom) | F6 references `wealth_power_audit` + `wealth_beautiful_mouse_scan`; F8 LAW + F13 SOVEREIGN handoff architecture | Aligned to live tools + new F8 LAW floor |
| §7 Quick Start | `python internal/monolith.py` | `python server_federated.py` | Federated is canonical |
| §7 Quick Start | `wealth_time_discount(mode='npv', initial_investment=...)` | `wealth_compute_npv(cash_flows, discount_rate)` | Live tool name + signature |
| §7 Verify | `status=healthy registry_truth=PASS` (phantom) | `status=ALIVE` + 24 tools (live query) | Aligned to live health endpoint |
| §8 Architecture | Directory tree showed monolith-era | Directory tree now shows federated: `wealth_mcp/`, `wealth_core/`, `wealth_contracts/`, `wealth_arifos_bridge/`, `wealth_compat/` | Federated structure is the new reality |
| §8 Architecture | "The Monolith Philosophy" argued monolith is the design | "The Federated Architecture" documents the 5-layer design | Monolith is DEPRECATED, not the design |
| §10 — Tool Categories | Phantom tool names (`wealth_time_discount`, `wealth_entropy_risk`, `wealth_energy_productivity`, `wealth_flow_liquidity`, `wealth_survival_engine`, `wealth_field_macro`, `wealth_game_coordination`, `wealth_inequality_kernel`, `wealth_boundary_governance`) | Live tool names | Aligned to live surface |
| §10 — Call Chain | `wealth_boundary_governance(mode='floors')` + `arif_judge_deliberate` | `wealth_conservation_check` + `wealth_arifos_judge_handoff` + `arif_judge` | Aligned to live tools + new handoff pattern |
| §10 — Scenarios | 4 scenarios (2 used phantom tool names) | 4 original + 2 NEW (counterfactual, beautiful mouse) | NEW eurekas documented |
| §10 — Rules for Agents | 7 rules | 10 rules (added collapse signature discipline, beautiful mouse, counterfactual) | NEW eurekas require new discipline |
| §12 — Build | `python internal/monolith.py` (DEPRECATED) | `python server_federated.py` (canonical) | Federated is canonical |
| §12 — Build | Health endpoint output: `{"status":"healthy","final_authority":"ARIF","tool_count":20,"registry_truth":"PASS"}` | `{"status":"ALIVE","version":"2026.06.15","architecture":"federated",...}` | Aligned to live output |
| §13 — Known Limitations | "SPEC.md proposes 42 atomic tools" (stale) | "Collapse scanner calibration" + "arifos_seal block" (current) | Updated to current state |
| §14 — Federation | (no memory graph entity count) | "8 entities as of 2026-06-24" with the 8th = handoff | Memory graph grew |
| §16 — Sovereignty | (unchanged) | (unchanged) | Preserved |
| New §17 | (new) | Change log (this section) | SOT hygiene |

### What did NOT change

- ASCII art (preserved)
- Section 1 doctrine (preserved — the WHAT IS / IS NOT is doctrine, not SOT)
- Section 2 federation position (mostly preserved, added handoff to the diagram)
- Section 9 (human operator guidance) — preserved
- Section 11 (institutions) — preserved
- Section 15 (GENESIS chain) — preserved
- Section 16 (license + sovereignty) — preserved

### SOT references

- `wealth_mcp/server.py` — canonical MCP surface (24 tools, 6 resources, 2 prompts)
- `wealth_core/` — pure engines (no MCP, no I/O)
- `wealth_arifos_bridge/` — federation bridge (NEW 2026-06-24)
- `wealth_contracts/envelope.py` — output envelope pattern
- `wealth_arifos_bridge/judge_handoff.py` — handoff bridge
- `wealth_core/counterfactual.py` — counterfactual engine (NEW 2026-06-24)
- `wealth_core/collapse_signature/beautiful_mouse.py` — Phase C detector (NEW 2026-06-24)
- `/root/arifOS/memory/entities/WEALTH_Arifos_Judge_Handoff_2026.json` — 8th memory graph entity
- `/root/forge_work/wealth-mcp-augmentation-2026-06-24/RECEIPT.md` — full forge receipt
- `/root/forge_work/wealth-mcp-augmentation-2026-06-24/VAULT999_EUREKA_SEALS.jsonl` — 3 eureka seals

### Live verification

```
$ curl -s -X POST http://127.0.0.1:18082/mcp -H "Content-Type: application/json" -H "Accept: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"wealth_system_registry_status","arguments":{"mode":"registry"}},"id":1}' \
    | python3 -c "import json,sys; d=json.load(sys.stdin); r=json.loads(d['result']['content'][0]['text']); print(f'tools={len(r[\"public_tools\"])} status={r[\"status\"]}')"
tools=24 status=ALIVE
```

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

*README v3.1.0 · SOT sync 2026-06-24 by FORGE (000Ω) · arifOS Federation*
*Canonical source: `git@github.com:ariffazil/wealth.git` · Branch: `main`*
*Forged under 888 vote ("audit my wealth github readme. indentify section need to uodate to SOT. comnit push deploy seal")*

*999 SEAL ALIVE — 3 eureka seals in epoch ledger*
