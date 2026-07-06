<!-- SOT-MANIFEST
federation_release: v2026.07.06-APEX-IV
last_verified: 2026-07-06
changelog: APEX Pillar IV — robust EVOI, Nash multi-factor, scar accumulation
audit_finding: actor_id self-report pattern at wealth_mcp/server.py:272 — deferred
a2a_agent_json: /root/WEALTH/.well-known/agent.json
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
- Public MCP tools: **37** (canonical surface)
- Prompts: **7 canonical loops**
- Resources: **15** (8 SOT + 7 dynamic reality)
- Transport: FastMCP (streamable-HTTP, Python 3.12)
- Port: **18082** (`wealth.service`)
- License: **AGPL-3.0** — strong copyleft, network services must disclose source

**Authority:**
- WEALTH computes
- WEALTH does not move money
- WEALTH does not authorize capital
- WEALTH does not self-seal

**Federation Position (canonical organ map):**

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

> APEX THEORY defines the constitutional dynamics of governed intelligence through ΔΩΨ. arifOS compiles those dynamics into an AGI substrate kernel. AAA renders the substrate as visible ASI civilization state. A-FORGE gives the system governed hands. GEOX, WEALTH, and WELL anchor those hands to earth, capital, and human reality. VAULT999 preserves consequence. Arif/F13 remains the sovereign witness and final veto.

**WEALTH must never:** move capital, issue final investment decisions, or make allocation calls without arifOS SEAL.

Full doctrine: [GENESIS/040_APEX_STACK.md](https://github.com/ariffazil/arifos/blob/main/GENESIS/040_APEX_STACK.md)

---

## What WEALTH Is

WEALTH is the **capital intelligence organ** of the arifOS federation. It models cashflow, valuation, risk, market reality, institutional power, and capital wisdom as **computable primitives** — never as opinions.

WEALTH tells you what the capital looks like. It does not move the money. The sovereign decides.

---

## APEX Pillar IV — Mathematical Optimization Foundation

> **Added: 2026-07-06.** Derived from Postek et al. *"Hands-On Mathematical Optimization with Python"* (Cambridge UP 2025) × APEX Theory v36Ω.

WEALTH now carries three optimization primitives from APEX Pillar IV:

### Robust EVOI (`wealth_evoi_compute`)

When `robust=True`, computes EVOI under uncertainty ranges (prior ± 0.10, posterior ± 0.15) across 400 scenario pairs. Returns worst-case EVOI, CVaR(5%), and robust regret alongside expected EVOI. Verdicts: `ROBUST_SEAL` / `ROBUST_SABAR` / `ROBUST_VOID`.

```
max-min over uncertainty set → worst-case EVOI → robust decision
```

### Nash Multi-Factor (`wealth_stock_analysis`)

When `mode="nash_multi_factor"`, computes Nash bargaining product across factors (value, momentum, quality, risk). The Nash product forbids trade-offs between factors — zero in any factor collapses the score. Compares Nash (geometric mean) vs additive (arithmetic mean) and flags divergence >5% as trade-off detected.

```
G = ∏(f_i ^ w_i)   — Nash 1950, log-transformed for stability
```

### Scar Accumulation (`wealth_survival_engine`)

When `scar_history` is provided, computes scar pressure (loss events / total periods), builds forbidden zones from >5% loss events, and escalates boundary from GREEN → YELLOW when scar pressure > 0.3. Constraints accumulate permanently — feasible region shrinks monotonically.

```
F_{t+1} = F_t ∩ {scar_t}   — cutting-plane method applied to learning
```

### The Mathematical Foundation

APEX theory IS mathematical optimization applied to intelligence:

| APEX Concept | Optimization Analog |
|---|---|
| G = A·P·E·X·Φ | Nash bargaining product (multiplicative objective) |
| F1-F13 floors | Constraints on the feasible region |
| C_dark | Dual variable — shadow price of relaxing P and X |
| MALU-Gödel repair | Cutting-plane constraint accumulation |
| dS/dt ≤ 0 | Optimal control — entropy management over time |

Full theory: [arifOS/static/arifos/theory/000/APEX_THEORY.md](https://github.com/ariffazil/arifos/blob/main/static/arifos/theory/000/APEX_THEORY.md) — Pillar IV.

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

## Tools (Public Canonical, 37)

| Category | Tools | APEX Upgrade |
|----------|-------|--------------|
| **Capital** | `wealth_compute_npv`, `wealth_compute_irr`, `wealth_conservation_check`, `wealth_flow_check` | — |
| **Risk** | `wealth_compute_emv`, `wealth_compute_evoi`, `wealth_monte_carlo_simulate`, `wealth_asymmetry_check`, `wealth_runway_check` | `wealth_compute_evoi` +`robust=True` |
| **Optimization** | `wealth_markowitz_frontier`, `wealth_kelly_sizing`, `wealth_robust_portfolio`, `wealth_chance_constrained`, `wealth_two_stage_recourse` | **NEW** — APEX Pillar IV |
| **Survival** | `wealth_survival_engine` | +`scar_history` |
| **Personal Finance** | `wealth_personal_finance` | — |
| **Market Data** | `wealth_market_data`, `wealth_fiscal_breakeven` | — |
| **Stock** | `wealth_stock_analysis` | +`mode="nash_multi_factor"` |
| **Wisdom** | `wealth_wisdom_evaluate`, `wealth_omni_wisdom` | — |
| **Power** | `wealth_power_audit`, `wealth_capture_scan` | — |
| **Collapse** | `wealth_collapse_signature_scan`, `wealth_beautiful_mouse_scan` | — |
| **Governance** | `wealth_boundary_governance` | — |
| **Meta** | `wealth_agent_path`, `wealth_registry_status`, `wealth_judge_handoff`, `wealth_confluence_check` | — |
| **Vault** | `wealth_vault_query`, `wealth_vault_write` (irreversible) | — |

Full registry: `resources/read wealth://tools/registry`.

---

## Prompt Layer (MCP)

WEALTH exposes structured prompts via MCP:

- Discover: `prompts/list`
- Retrieve: `prompts/get`

**Prompts are not answers. Prompts enforce reasoning discipline.**

Each prompt:
- defines a loop
- defines tool sequence
- defines forbidden conclusions
- defines authority boundary

**Prompt → Tool → Resource mapping is enforced server-side.** A prompt cannot call a tool without the context resource loaded first.

---

## Resource Layer (Reality Context)

Resources provide the context that prevents incorrect computation.

**WEALTH does not trust memory. WEALTH loads context from resources before computation.**

### Static SOT (8)
| URI | Purpose |
|-----|---------|
| `wealth://schema` | Full tool/prompt/resource manifest + version |
| `wealth://tools/registry` | 37 public tools with action_class + mutation flags |
| `wealth://prompts/index` | 7 prompts with required args + outputs |
| `wealth://domains/index` | 4 federated domain maps |
| `wealth://runtime/policy` | Discipline contract — required resources per tool class |
| `wealth://canon/002-human-law` | CANON 002 — human law as capital geometry |
| `wealth://glossary` | arifOS/WEALTH canonical glossary |
| `wealth://federation/contract` | Authority chain, handoffs, never-list |

### Dynamic Reality (7)
| URI | Purpose |
|-----|---------|
| `wealth://health` | Liveness + timestamp (dynamic) |
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

**User:** *"Should I invest in X?"*

**Flow:**

1. `wealth_reality_intake_loop` — establish facts, unknowns, time horizon
2. `wealth_capital_diagnosis_loop` — model cashflow / NPV / IRR
3. `wealth_risk_downside_loop` — EMV, asymmetry, missing downside
4. `wealth_market_reality_loop` — current FX / market context
5. `wealth_allocation_judgment_loop` — compare options, advisory only

**Output:**
- advisory comparison (no recommendation to act)
- downside risks
- missing data
- required additional evidence

**If irreversible (e.g. > 888_HOLD threshold):**

6. `wealth_judge_handoff(mode="prepare")` — builds envelope
7. arifOS `arif_judge` returns verdict
8. Arif decides
9. A-FORGE executes (if SEAL)
10. VAULT999 seals

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

# 2. MCP initialize + tools/list
curl -X POST https://wealth.arif-fazil.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"cli","version":"1.0"}},"id":1}'

# 3. Discover
#    tools/list           → 37 tools
#    prompts/list         → 7 prompts
#    resources/list       → 15 resources

# 4. APEX Pillar IV quick test
#    wealth_evoi_compute(robust=true)  → robust EVOI with CVaR
#    wealth_stock_analysis(mode="nash_multi_factor")  → Nash vs additive
#    wealth_survival_engine(scar_history=[...])  → scar pressure + forbidden zones
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

Five-layer runtime: `wealth_core`, `wealth_contracts`, `wealth_mcp`, `wealth_arifos_bridge`, `wealth_compat`.

---

## 🔌 MCP Connection

Connect to WEALTH via the Model Context Protocol:

| Property | Value |
|----------|-------|
| **Endpoint** | `https://wealth.arif-fazil.com/mcp` |
| **Transport** | Streamable HTTP (JSON-RPC 2.0) |
| **Tools** | 37 tools |
| **Health** | `https://wealth.arif-fazil.com/health` |

### Claude Code / Cursor

Add to your MCP client config:
```json
{
  "mcpServers": {
    "wealth": {
      "url": "https://wealth.arif-fazil.com/mcp"
    }
  }
}
```

### Direct Usage

```bash
curl -X POST https://wealth.arif-fazil.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## License

AGPL-3.0. See `LICENSE`.

---

*Forged: 2026-07-01. Upgraded: 2026-07-06 (APEX Pillar IV). Runtime SOT is canonical — README defers to `wealth://schema`.*
*DITEMPA BUKAN DIBERI*
