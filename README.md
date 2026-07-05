<!-- SOT-MANIFEST
federation_release: v2026.07.04-MCP-A2A
last_verified: 2026-07-05
changelog: /root/CHANGELOG-2026-07-04.md
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
- Version: **2026.06.15**
- Public MCP tools: **26** (32 total decorated tools including 6 backward-compat aliases)
- Prompts: **7 canonical loops**
- Resources: **15** (8 SOT + 7 dynamic reality)
- Transport: FastMCP (streamable-HTTP, Python 3.12)
- Port: **18082** (`wealth-organ.service`)
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
| `wealth://tools/registry` | 26 public tools + 6 aliases (32 total) with action_class + mutation flags |
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
curl http://localhost:18082/health

# 2. Schema
echo '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"wealth://schema"}}' \
  | curl -X POST -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    --data-binary @- http://localhost:18082/mcp

# 3. Initialize MCP session, then:
#    prompts/list         → discover 7 prompts
#    prompts/get wealth_reality_intake_loop
#    tools/list           → 32 tools (26 canonical + 6 aliases)
#    resources/list       → 15 resources

# 4. Handoff to arifOS
wealth_judge_handoff(
    tool_name="wealth_compute_npv",
    result=...,
    intent="...",
    capability="issue_capital_recommendation",
    blast_radius="HIGH",
    reversibility_level="PARTIAL",
    epistemic_state="DERIVED",
    domain="capital",
    mode="prepare"
)
```

Full runtime guide: `RUNBOOK.md`. Constitutional mandate: `GENESIS/011_WEALTH_MANDATE.md`.

---

## Tools (Public Canonical, 26)

Categories:

| Category | Count | Examples |
|----------|-------|----------|
| Capital | 4 | `wealth_compute_npv`, `wealth_compute_irr`, `wealth_conservation_check`, `wealth_flow_check` |
| Risk | 5 | `wealth_compute_emv`, `wealth_compute_evoi`, `wealth_monte_carlo_simulate`, `wealth_asymmetry_check`, `wealth_runway_check` |
| Survival | 1 | `wealth_survival_engine` |
| Personal Finance | 1 | `wealth_personal_finance` |
| Market Data | 1 | `wealth_market_data` |
| Stock | 1 | `wealth_stock_analysis` |
| Wisdom | 2 | `wealth_wisdom_evaluate`, `wealth_omni_wisdom` |
| Power | 2 | `wealth_power_audit`, `wealth_capture_scan` |
| Collapse | 2 | `wealth_collapse_signature_scan`, `wealth_beautiful_mouse_scan` |
| Governance | 1 | `wealth_boundary_governance` |
| Meta | 4 | `wealth_agent_path`, `wealth_registry_status`, `wealth_judge_handoff`, `wealth_confluence_check` |
| Vault | 2 | `wealth_vault_query`, `wealth_vault_write` (irreversible) |

**Aliases** (legacy surface, deprecated but live for backward compat): `wealth_emv_compute`, `wealth_evoi_compute`, `wealth_monte_carlo`, `wealth_reason_agent`, `wealth_system_registry_status`.

**Additional callable tools** (exposed via `tools/list` but not in the 26-public canonical surface): `wealth_fiscal_breakeven`.

Full registry: `resources/read wealth://tools/registry`.

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

## License

AGPL-3.0. See `LICENSE`.

---

## 🔌 MCP Connection

Connect to WEALTH via the Model Context Protocol:

| Property | Value |
|----------|-------|
| **Endpoint** | `https://wealth.arif-fazil.com/mcp` |
| **Transport** | Streamable HTTP (JSON-RPC 2.0) |
| **Tools** | 32 tools |
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

*Forged: 2026-07-01. Runtime SOT is canonical — README defers to `wealth://schema`.*
*Prior README content archived to `GENESIS/README-archive-2026-06-27.md`.*
*DITEMPA BUKAN DIBEI*
