<!-- SOT-MANIFEST
federation_release: v2026.07.15-DOMAIN-CONTRAST
last_verified: 2026-07-17T04:45Z
mcp_tools_live: 12
domain_law: CAPITAL_LAW
truth_rule: tools/list + /health beat any static count in prose
runtime_path: /root/WEALTH
port: 18082
health_status: ALIVE
health_version_banner: 2026.07.12
domain_contrast: /root/AAA/docs/DOMAIN_ORGAN_CONTRAST.md
a2a_agent_json: /root/WEALTH/.well-known/agent.json
-->

# WEALTH — Capital Intelligence for arifOS

> **DITEMPA BUKAN DIBERI.** It **computes**. It does **not** move money.

## Identity

| Field | Value |
|-------|-------|
| **Domain** | Capital — cashflow, risk, optimizers, institutional power |
| **Port** | `:18082` · `https://wealth.arif-fazil.com` |
| **MCP Tools (public)** | **12** — SOT: live `tools/list` |
| **Primary Physics** | Capital thermodynamics · Kelly · conservation · VaR/CVaR |
| **Epistemic Labels** | DERIVED / CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE |
| **License** | AGPL-3.0 |
| **Final Authority** | ARIF (F13 SOVEREIGN) |
| **Production entry** | **`server_federated.py`** → `wealth_mcp/` — [`ENTRYPOINTS.md`](./ENTRYPOINTS.md) |
| **Soul** | [`SOUL.md`](./SOUL.md) · Docs: [`docs/index.md`](./docs/index.md) |

## Federation Position

```
ARIF (F13) → arifOS KERNEL :8088 → WEALTH :18082 (this organ)
                                      ↑ GEOX feeds (volumes/POS artifacts)
                                      ↑ WELL livelihood frames (S13)
                                      └→ arifOS 888 judge → A-FORGE after SEAL
```

## What WEALTH Owns

- NPV · IRR · EMV · EVOI · Monte Carlo · Kelly · portfolio optimizers  
- Runway / conservation / market / institutional diagnostics  
- Advisory envelopes + judge handoff prep  

## What WEALTH Refuses (Hard)

| Refusal | Who owns it instead |
|---------|---------------------|
| Move money / trade exec | Human + external broker · never this organ |
| Earth truth / geology | GEOX |
| Medical / readiness law | WELL |
| Constitutional SEAL | arifOS / VAULT999 |
| Self-seal | forbidden |

## Connect

```json
{ "mcpServers": { "wealth": { "url": "https://wealth.arif-fazil.com/mcp" } } }
```

SOT RULE: `tools/list` wins. **Deprecated:** root `server.py` monolith path.

[![License](https://img.shields.io/github/license/ariffazil/wealth?label=License)](LICENSE)

---

## Current Runtime SOT

WEALTH is the capital intelligence organ of arifOS.

**Runtime (probe 2026-07-15 — runtime wins over prose):**
- Version banner: **2026.07.12** · health `status=ALIVE`
- **`domain_law`:** `CAPITAL_LAW`
- Public MCP tools: **12** live (`tools/list` / mcporter) — not the historical decorator backlog
- Stock analysis / optimizer modes: multi-mode tools (Kelly, Markowitz, VaR/CVaR family — see tool schemas)
- Prompts: **7** canonical capital loops
- Resources: static SOT + dynamic reality URIs under `wealth://`
- Transport: FastMCP streamable-HTTP, Python 3.12
- Port: **18082** (`wealth-organ` · entry **`server_federated.py`** — see [`ENTRYPOINTS.md`](./ENTRYPOINTS.md))
- License: **AGPL-3.0**
- **Deprecated:** `server.py` / `internal/monolith.py` as production MCP (removal target 2026-08-15)

**Authority:**
- WEALTH computes
- WEALTH does not move money
- WEALTH does not authorize capital
- WEALTH does not self-seal

> **If README and runtime disagree → runtime registry is source of truth.**  
> Verify via `resources/read wealth://schema` and `tools/list`.

---

## Domain contrast — GEOX · WEALTH · WELL (federation MCP)

> Full architecture seal: [ARIFOS_MCP_ARCHITECTURE_v2026.07.15](https://github.com/ariffazil/AAA/blob/main/docs/ARIFOS_MCP_ARCHITECTURE_v2026.07.15.md) · Contrast: [DOMAIN_ORGAN_CONTRAST](https://github.com/ariffazil/AAA/blob/main/docs/DOMAIN_ORGAN_CONTRAST.md) · Organ map: [FEDERATION_ORGAN](https://github.com/ariffazil/AAA/blob/main/docs/ORGAN.md)  
> **This organ answers to `CAPITAL_LAW`.** Not natural law. Not substrate law. Not constitutional law.

Three domain MCP servers share one governance spine (arifOS) and three **orthogonal laws of truth**. Collapsing them is a constitutional error.

| Axis | GEOX | **WEALTH (this repo)** | WELL |
|------|------|------------------------|------|
| Port / MCP | `:8081` · geox.arif-fazil.com/mcp | **`:18082`** · [wealth.arif-fazil.com/mcp](https://wealth.arif-fazil.com/mcp) | `:18083` · well.arif-fazil.com/mcp |
| GitHub | [ariffazil/GEOX](https://github.com/ariffazil/GEOX) | [ariffazil/WEALTH](https://github.com/ariffazil/WEALTH) | [ariffazil/WELL](https://github.com/ariffazil/WELL) |
| `domain_law` | `NATURAL_LAW` | **`CAPITAL_LAW`** | `SUBSTRATE_LAW` |
| Primary axis | Earth / material substrate | **Capital / scarcity / allocation geometry** | Vitality / readiness / dignity |
| Live tools (2026-07-15) | **15** | **12** | **27** |
| Authority | Evidence only | **Compute only (advisory)** | `REFLECT_ONLY` |
| May claim | OBS / DER / INT earth facts | **Numbers, risk envelopes, advisory size** | Readiness signals, dignity flags |
| Must never | Drill · allocate · seal law | **Move money · claim earth truth · self-seal** | Diagnose · decide fitness · override human |

### Knowledge grammars (Math · Physics · Code)

| Grammar | GEOX | **WEALTH** | WELL |
|---------|------|------------|------|
| **Physics** | Primary — Physics9 rock bounds | **Mapped** — capital as conserved flow (runway, burn, risk entropy, conservation check) | Homeostatic flux (not diagnosis) |
| **Math** | Transforms, P10/P50/P90 | **Primary** — NPV, IRR, EMV, EVOI, Kelly, Markowitz, VaR/CVaR, Monte Carlo | Scores, thresholds, entropy |
| **Code / MCP** | FastMCP `geox_*` | **FastMCP `wealth_*` + `wealth://` resources + 7 prompts** | FastMCP `well_*` |

### MCP architecture (this server)

WEALTH is a **standalone MCP server**, not a plugin inside arifOS.

| Primitive | Role on WEALTH |
|-----------|----------------|
| **Tools** | Capital compute (`wealth_*`) — public contract = live `tools/list` |
| **Resources** | Context that prevents wrong math (`wealth://schema`, risk, market, handoff) |
| **Prompts** | 7 capital intelligence loops (intake → risk → market → handoff) |
| **Transport** | Streamable HTTP (`:18082/mcp`) + stdio |
| **Public door** | Caddy → `https://wealth.arif-fazil.com/mcp` |
| **Does not own** | F1–F13 judgment, SEAL, earth evidence, medical diagnosis |

**Execution order (discipline):** load resources → apply prompt loop → call tools → advisory only → `wealth_judge_handoff` if irreversible / HIGH-CRITICAL.

**Agentic flow:** intent → arifOS classify/route → **WEALTH tools** (capital evidence) → optional GEOX (earth) / WELL (readiness) → `arif_judge` → SEAL/HOLD/VOID → A-FORGE execute → VAULT999.

```
Arif (F13) → AAA/Hermes/OpenClaw → arifOS :8088
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                 GEOX :8081      WEALTH :18082     WELL :18083
                 NATURAL_LAW     CAPITAL_LAW       SUBSTRATE_LAW
                 earth evidence  capital compute   vitality reflect
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                              arifOS 888 JUDGE → A-FORGE → VAULT999
```

| Peer | WEALTH relationship |
|------|---------------------|
| **arifOS** | Governor — WEALTH prepares judge envelopes; never seals |
| **GEOX** | Earth volumes / POS-class inputs for capital geometry; WEALTH does not invent geology |
| **WELL** | Livelihood / human-risk coupling (`well_handoff_livelihood_to_wealth`); WEALTH does not assess biology |
| **A-FORGE** | Hands after SEAL — never allocate from WEALTH alone |
| **VAULT999** | Immutable capital consequence after SEAL |

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
# tools/list → live count (probe; README is not the registry)

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
| **Tools** | 12 tools (live `tools/list`; runtime wins) |
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
