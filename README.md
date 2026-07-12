<!-- SOT-MANIFEST
federation_release: v2026.07.12-CONSOLIDATION-EPOCH
last_verified: 2026-07-12T04:50Z
live_commit: 6adefdb
runtime_path: /root/WEALTH (synced from /root/wealth)
port: 18082
health_status: ALIVE
health_version_banner: 2026.07.12 (banner lag; code @6adefdb)
changelog: Kelly criterion + optimizer suite + APEX Pillar IV
audit_finding: actor_id self-report pattern at wealth_mcp/server.py:272 — deferred
a2a_agent_json: /root/WEALTH/.well-known/agent.json
machine_sot: /root/A-FORGE/forge_work/2026-07-09/MACHINE-SOT-2026-07-09.json
-->

# WEALTH — Capital Intelligence for arifOS

> **DITEMPA BUKAN DIBERI** — *"Forged, Not Given."*

**It computes. It warns. It prepares evidence for judgment.**

It does not move money. It does not authorize capital. It does not self-seal.

[![Agentic CI](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml)
[![Governance Gate](https://github.com/ariffazil/wealth/actions/workflows/governance-gate.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/governance-gate.yml)
[![Build Validation](https://github.com/ariffazil/wealth/actions/workflows/publish-image.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/publish-image.yml)
[![License](https://img.shields.io/github/license/ariffazil/wealth?label=License)](LICENSE)

---

## Current Runtime SOT

WEALTH is the capital intelligence organ of arifOS.

**Runtime:**
- Version: **2026.07.06**
- Public MCP tools: **50** (live tools/list count; canonical ~45 unique)
- Stock analysis modes: **27** (including Kelly, Nash multi-factor, TAC-9)
- Optimizer suite: **5 engines** (Markowitz, Kelly, Robust, Chance-constrained, Two-stage)
- Prompts: **7 canonical loops**
- Resources: **15** (8 SOT + 7 dynamic reality)
- Transport: FastMCP 3.4.2 (streamable-HTTP, Python 3.12)
- Port: **18082** (`wealth.service`)
- License: **AGPL-3.0** — strong copyleft, network services must disclose source

**Authority:**
- WEALTH computes
- WEALTH does not move money
- WEALTH does not authorize capital
- WEALTH does not self-seal

**Federation Position:**

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

> **If README and runtime disagree → runtime registry is source of truth.**
> Verify via `resources/read wealth://schema` and `tools/list`.

---

## APEX STACK Bridge

> APEX is the admissibility framework for decisions under uncertainty (ΔΩΨ). arifOS compiles those dynamics into a constitutional orchestration substrate. AAA renders federation-state and coordination (display layer — not ASI-civilisation claims). A-FORGE gives the system governed hands. GEOX, WEALTH, and WELL anchor those hands to earth, capital, and human reality. VAULT999 preserves consequence. Arif/F13 remains the sovereign witness and final veto.

**WEALTH must never:** move capital, issue final investment decisions, or make allocation calls without arifOS SEAL.

Full doctrine: [GENESIS/040_APEX_STACK.md](https://github.com/ariffazil/arifos/blob/main/GENESIS/040_APEX_STACK.md)

**Orthogonal CANON:** [ariffazil/CANON.md](https://github.com/ariffazil/ariffazil/blob/main/CANON.md) — this repo is **capital domain intelligence** (compute, never allocate). Touches money surfaces only through APA leases, never free agent hands.

---

## What WEALTH Is

WEALTH is the **capital intelligence organ** of the arifOS federation. It models cashflow, valuation, risk, market reality, institutional power, and capital wisdom as **computable primitives** — never as opinions.

WEALTH tells you what the capital looks like. It does not move the money. The sovereign decides.

---

## Optimizer Suite (APEX × Pyomo)

Five mathematical optimization engines forged from first principles. Each maps to an APEX conservation law.

| Engine | Mode | APEX Organ | What It Does |
|--------|------|------------|--------------|
| **Markowitz** | `markowitz` | ΔR Reality | Mean-variance frontier — optimal portfolio weights |
| **Kelly** | `kelly` | W Execution | Optimal bet sizing — half-Kelly default, C_dark detection |
| **Robust** | `robust` | ΔG Governance | Worst-case optimization under uncertainty |
| **Chance-Constrained** | `chance_constrained` | Ω Witness | VaR/CVaR optimization — P(loss > threshold) ≤ α |
| **Two-Stage** | `two_stage` | ∂M/∂t Memory | Stochastic recourse — invest now, adjust later |

**Forge verdict (2026-07-06):**
- Markowitz: Equal-weight wins for correlated assets. Kept as reference.
- Kelly: **FORGED** — 13x better on strong edge, adapts to edge quality.
- Robust/Chance: Concentrates risk, marginal improvement. Kept as reference.

**APEX mapping:** Each optimizer returns `apex.organ`, `apex.conservation_law`, `apex.G_score`, `apex.C_dark`, `apex.verdict`.

---

## WEALTH Intelligence Loop

Every query flows through a structured loop:

1. **Reality Intake** — what context, what facts, what unknowns?
2. **Domain Classification** — capital, risk, market, allocation, power, handoff?
3. **Tool Routing** — which primitives apply?
4. **Downside Challenge** — what's the worst case? What's missing?
5. **Boundary Enforcement** — is this reversible? Does it need 888_HOLD?
6. **Output (Advisory only)** — never a verdict, never an authorization.
7. **arifOS Handoff** (if required) — prepare envelope, let arifOS judge.

This loop is implemented through **7 canonical MCP prompts**:

| # | Prompt | Domain |
|---|--------|--------|
| 1 | `wealth_reality_intake_loop` | Universal entrypoint — any query |
| 2 | `wealth_capital_diagnosis_loop` | Cashflow, runway, NPV, IRR |
| 3 | `wealth_risk_downside_loop` | EMV, EVOI, asymmetry, downside |
| 4 | `wealth_market_reality_loop` | FX, commodities, macro |
| 5 | `wealth_allocation_judgment_loop` | Advisory comparison of options |
| 6 | `wealth_institutional_power_loop` | Capture, Beautiful Mouse, collapse signature |
| 7 | `wealth_arifos_handoff_loop` | Prepare judge envelope (irreversible, high-risk) |

---

## Tools (Public Canonical)

### Core Capital
| Tool | Purpose |
|------|---------|
| `wealth_compute_npv` | Net Present Value |
| `wealth_compute_irr` | Internal Rate of Return |
| `wealth_conservation_check` | Capital conservation audit |
| `wealth_flow_check` | Cash flow analysis |

### Risk & Simulation
| Tool | Purpose |
|------|---------|
| `wealth_compute_emv` | Expected Monetary Value |
| `wealth_compute_evoi` | Expected Value of Information |
| `wealth_monte_carlo_simulate` | Monte Carlo simulation |
| `wealth_asymmetry_check` | Risk asymmetry detection |
| `wealth_runway_check` | Financial runway calculation |

### Stock Analysis (27 modes)
| Tool | Key Modes |
|------|-----------|
| `wealth_stock_analysis` | `verify_math` · `position_size` · `kelly` · `nash_multi_factor` · `tac9` · `fundamentals` · `pre_trade` · `contrast` · `confluence` · `risk_metrics` · `calhoun_survival` · `888` · `999` |

### Optimizers
| Tool | Purpose |
|------|---------|
| `wealth_markowitz_frontier` | Mean-variance portfolio optimization |
| `wealth_kelly_sizing` | Kelly criterion position sizing |
| `wealth_robust_portfolio` | Robust optimization under uncertainty |
| `wealth_chance_constrained` | VaR/CVaR constrained optimization |
| `wealth_two_stage_recourse` | Two-stage stochastic programming |

### Wisdom & Power
| Tool | Purpose |
|------|---------|
| `wealth_wisdom_evaluate` | 6-dimension wisdom scoring |
| `wealth_omni_wisdom` | Unified capital intelligence |
| `wealth_power_audit` | Power dynamics audit |
| `wealth_capture_scan` | Capture signal detection |
| `wealth_collapse_signature_scan` | Institutional collapse detection |
| `wealth_beautiful_mouse_scan` | Calhoun Phase C detection |

### Personal & Market
| Tool | Purpose |
|------|---------|
| `wealth_personal_finance` | Cashflow, net worth, EPF, zakat |
| `wealth_market_data` | FX, commodities, macro indicators |
| `wealth_survival_engine` | Cashflow, runway, burn, liquidity |
| `wealth_fiscal_breakeven` | Malaysia fiscal breakeven oil price |

### Governance & Meta
| Tool | Purpose |
|------|---------|
| `wealth_boundary_governance` | F1-F13 floor compliance |
| `wealth_judge_handoff` | Prepare arifOS judge envelope |
| `wealth_registry_status` | Tool registry diagnostic |
| `wealth_agent_path` | Intent routing |
| `wealth_confluence_check` | False confluence detection |

### Vault (Irreversible)
| Tool | Purpose |
|------|---------|
| `wealth_vault_query` | Query VAULT999 ledger |
| `wealth_vault_write` | Write to VAULT999 (requires SEAL) |

Full registry: `resources/read wealth://tools/registry`

---

## Resource Layer (Reality Context)

Resources provide the context that prevents incorrect computation.

**WEALTH does not trust memory. WEALTH loads context from resources before computation.**

### Static SOT (8)
| URI | Purpose |
|-----|---------|
| `wealth://schema` | Full tool/prompt/resource manifest + version |
| `wealth://tools/registry` | All tools with action_class + mutation flags |
| `wealth://prompts/index` | 7 prompts with required args + outputs |
| `wealth://domains/index` | Federated domain maps |
| `wealth://runtime/policy` | Discipline contract — required resources per tool class |
| `wealth://canon/002-human-law` | Human law as capital geometry |
| `wealth://glossary` | arifOS/WEALTH canonical glossary |
| `wealth://federation/contract` | Authority chain, handoffs, never-list |

### Dynamic Reality (7)
| URI | Purpose |
|-----|---------|
| `wealth://health` | Liveness + timestamp |
| `wealth://reality/context` | Current reality assumptions |
| `wealth://market/sources` | What counts as "real" market data |
| `wealth://risk/thresholds` | LOW/MEDIUM/HIGH/CRITICAL definitions |
| `wealth://affordance/contracts` | Tool authority, mutation, 888_HOLD map |
| `wealth://handoff/arifos-schema` | Required structure for judge handoff |
| `wealth://replay/receipt-schema` | Reproducible intelligence trace |

---

## MCP Transport Model

WEALTH transports intelligence through:

- **Tools** → computation
- **Resources** → context
- **Prompts** → reasoning discipline

**Execution order:**

1. Load resources (`resources/read` — schema, risk/thresholds, reality/context)
2. Apply prompt loop (`prompts/get`)
3. Call tools (`tools/call` — read affordance/contracts first)
4. Produce advisory output
5. Prepare arifOS handoff (if irreversible or HIGH/CRITICAL risk)

> No tool should be called without context.
> No output should skip the prompt loop.
> No verdict should be claimed without arifOS response.

---

## Authority Boundary

| Layer | Responsibility |
|-------|---------------|
| **WEALTH** | Compute capital intelligence |
| **arifOS** | Judge admissibility |
| **Arif** | Final decision (F13 SOVEREIGN) |
| **A-FORGE** | Execute |
| **VAULT999** | Seal |

**WEALTH cannot:**
- move money
- issue trade instructions
- allocate capital
- override arifOS
- self-seal

If any of these is implied by a tool output, the output is malformed — escalate.

---

## Example Flow

**User:** *"What's the optimal position size for PETRONAS?"*

**Flow:**

1. `wealth_reality_intake_loop` — establish account, risk tolerance, edge quality
2. `wealth_stock_analysis(mode="kelly")` — Kelly criterion: half-Kelly, C_dark check
3. `wealth_stock_analysis(mode="risk_metrics")` — VaR, CVaR, max drawdown
4. `wealth_market_reality_loop` — current MYR/USD, oil price, Bursa context

**Output:**
- Kelly fraction: 13.44% of account (half-Kelly)
- Position value: RM13,437.50
- Edge per trade: 0.0215
- APEX verdict: SABAR (C_dark=0.2, G=0.8)
- Advisory only — Arif decides

---

## Reality Constraint

> If data is missing, WEALTH must say: **"I don't know."**
> If data is stale, WEALTH must say: **"This is not current."**
> If risk is unclear, WEALTH must say: **"This cannot be concluded safely."**

This is non-negotiable. A WEALTH output that hides ignorance is a constitutional breach.

---

## Quick Start

```bash
# 1. Health
curl https://wealth.arif-fazil.com/health

# 2. Initialize MCP session
curl -X POST https://wealth.arif-fazil.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"cli","version":"1.0"}}}'

# 3. List tools
# tools/list → ~45 tools

# 4. Kelly example
curl -X POST https://wealth.arif-fazil.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"wealth_stock_analysis","arguments":{"mode":"kelly","account_balance":100000,"win_rate":0.55,"avg_win":0.08,"avg_loss":0.05,"kelly_fraction":0.5}}}'
```

Full runtime guide: `RUNBOOK.md`. Constitutional mandate: `GENESIS/011_WEALTH_MANDATE.md`.

---

## Limitations

- **No live trading.** WEALTH never moves capital.
- **No legal advice.** WEALTH reflects capital geometry only.
- **No real-time guarantees on external market data** beyond what `wealth://market/sources` declares as fresh.
- **No consciousness, no opinion.** WEALTH computes. Tools return numbers + labels.
- **WEALTH does not judge.** Judgment belongs to arifOS (`arif_judge`). Decisions belong to Arif (F13).

---

## Architecture

```
arifOS :8088  (Constitutional Kernel — judge, seal)
   ↓
WEALTH :18082 (Capital Intelligence — this repo)
   ↓
A-FORGE :7071 (Execution Shell — never adjudicates)
   ↓
VAULT999       (Append-only immutable ledger)
```

**Five-layer runtime:** `wealth_core` (engines + optimizers), `wealth_contracts` (output envelopes), `wealth_mcp` (tools + resources + prompts), `wealth_arifos_bridge` (kernel integration), `wealth_compat` (legacy aliases).

**Key directories:**

| Path | Purpose |
|------|---------|
| `internal/monolith.py` | Canonical kernel — 19 named tools, 27 stock modes |
| `wealth_mcp/server.py` | MCP surface — 39 tools, preload guards, governance |
| `wealth_core/optimizers/` | Pyomo optimizer suite (Markowitz, Kelly, Robust, Chance, Two-stage) |
| `internal/stock/` | D4 Stock Analysis — 27-mode capital-risk governance |
| `internal/market_data.py` | D3 Market Data — FX, commodities, macro |
| `internal/personal_finance.py` | D1 Personal Finance — cashflow, net worth, EPF, zakat |
| `tests/` | Test suite — optimizers, stock analysis, survival engine, governance |

---

## 🔌 MCP Connection

Connect to WEALTH via the Model Context Protocol:

| Property | Value |
|----------|-------|
| **Endpoint** | `https://wealth.arif-fazil.com/mcp` |
| **Transport** | Streamable HTTP (JSON-RPC 2.0) |
| **Tools** | 50 tools (live) |
| **Health** | `https://wealth.arif-fazil.com/health` |

### Claude Code / Cursor

```json
{
  "mcpServers": {
    "wealth": {
      "url": "https://wealth.arif-fazil.com/mcp"
    }
  }
}
```

---

## License

AGPL-3.0. See `LICENSE`.

---

*Forged: 2026-07-06. Runtime SOT is canonical — README defers to `wealth://schema`.*
*Prior README content archived to `GENESIS/README-archive-2026-06-27.md`.*
*DITEMPA BUKAN DIBERI*
