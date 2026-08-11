<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-08-11T05:58:51Z
federation_release: v2026.08.09
live_commit: 50a4047 (pydantic-ai 2.25.0→2.26.0 dependabot bump)
tools_loaded: 8
public_tools: 8
canonical_tools: 8
resources: 18
prompts: 7
receipt_chain: PERSISTING (/root/VAULT999/wealth/receipts.jsonl)
truth_rule: live :18082/health + tools/list beat any static count in prose
owner_summary: GREEN (identity_present, service_healthy, receipts_persisting, 0_ghosts)
infra_organs: arifFlow:7073 METABOLISM, FED:7074 ADVISORY, FLAME:18901 ADVISORY, FRAME:frame-organ.service OBSERVE
audit_basis: 333-AGI Δ MIND session (2026-08-11)
-->

# 💰 WEALTH — Capital Intelligence Organ

[![Federation](https://img.shields.io/badge/Federation-v2026.08.06-0a7b83)](https://arifos.arif-fazil.com)
[![💰 WEALTH](https://img.shields.io/badge/%F0%9F%92%B0%20WEALTH-8%20Tools-gold)](https://wealth.arif-fazil.com/mcp)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)

> **WEALTH computes. arifOS judges. Arif decides.**
> **DITEMPA BUKAN DIBERI — Forged, Not Given.**

**WEALTH** is the capital intelligence organ of the arifOS Federation. It is not a finance tool, a trading bot, a personal finance app, or a Bloomberg terminal. It is a **capital-intelligence nervous system** — it computes valuation, risk, institutional decay, capital entropy, and investment-consequence chains across months-to-years timeframes, not minutes-to-hours.

---

## What WEALTH Is

| Capability | Examples |
|------------|----------|
| **Capital Allocation Intelligence** | "Was Petronas Brazil a good investment?" · "Which basin destroys value?" |
| **Institutional Failure Detection** | Enron · 1MDB · Wirecard · FTX · LTCM collapse signatures |
| **IOC Portfolio Analysis** | Exxon · Shell · Petronas · Petrobras — asset quality, risk concentration |
| **Sovereign Investment Analysis** | PIF · Khazanah · Temasek · EPF — where capital flows, what incentives move it |
| **Economic Policy Analysis** | Fuel subsidy · Carbon tax · Resource nationalism — who pays, who benefits |

## What WEALTH Is NOT

❌ Trading bot · Day-trading assistant · Technical analysis (RSI/MACD/Bollinger) · HFT · Personal budget app · Tax filing · Fiqh authority · Bloomberg terminal replacement

---

## The Boundary

```
WEALTH observes market data, computes downside, and surfaces capital evidence.

IT NEVER:
  - Moves money or executes transactions
  - Allocates capital or authorizes spending
  - Issues constitutional verdicts (→ arifOS)
  - Executes mutations (→ A-FORGE)
  - Diagnoses human state (→ WELL)
```

---

## Tools (8 Public)

| Domain | Tool | Modes | Coverage |
|--------|------|-------|----------|
| **Capital Math** | `capital_primitive` | npv · irr · emv · evoi · mc · kelly · markowitz · robust · chance_constrained · two_stage | Valuation, optimization, simulation |
| **Capital Health** | `capital_health` | conservation · flow · runway · survival · fiscal_breakeven · confluence · asymmetry | Balance sheet, cashflow, sovereign fiscal |
| **Market Data** | `capital_market` | fx · commodity · indicator · stock · gold · oil · gas | Live Brent, DXY, MYR, Bursa |
| **Institutional** | `capital_diagnose` | stress_index · governance_capacity · cascade_model · exploitation_detect · collapse_signature · beautiful_mouse · capture_scan · power_audit · bid_surface · optimize_mwc · cadence_monitor · crisis_reflex · petronas_vitals | Collapse detection, governance erosion, capture |
| **Entropy** | `capital_entropy` | power_consequence_map · metric_purpose_audit · responsibility_ledger · trust_capital_decay · coercive_order_cost · entropy_externality | Who pays, who benefits, metric drift |
| **Ledger** | `capital_ledger` | query · write (ack_irreversible required) | VAULT999 append-only audit |
| **Registry** | `capital_registry` | status · schema · domains · health | Self-introspection, 8/8 PASS |
| **Handoff** | `wealth_judge_handoff` | prepare · submit | arifOS 888_HOLD governance envelope |

---

## 🗺️ Where WEALTH Sits in the Federation

```mermaid
flowchart LR
  subgraph Witness["🔬 Witness Plane (compute-only)"]
    WEALTH[("💰 WEALTH :18082<br/>Capital evidence<br/>14 public tools")]
  end

  subgraph Governance["⚖️ Governance"]
    ARIFOS["arifOS :8088<br/>F1-F13 · 888 JUDGE"]
  end

  subgraph Execution["⚒️ Execution"]
    AFORGE["A-FORGE :7071/72"]
  end

  subgraph Truth["💀 Truth"]
    VAULT["VAULT999<br/>WEALTH receipts"]
  end

  subgraph Sibling["Sibling witness"]
    GEOX["🌍 GEOX"]
    WELL["� WELL"]
  end

  WEALTH ==>|capital_primitive<br/>capital_health<br/>+ epistemic label| ARIFOS
  WEALTH ==>"capital_ledger.write (ack_irreversible)"| VAULT
  GEOX <-->|"capital bridge<br/>(EMV, NPV)"| WEALTH
  WELL -.->|"no cross-talk"| WEALTH

  ARIFOS ==>|"SEAL verdict"| AFORGE
  AFORGE ==>|"execute · verify"| VAULT
  VAULT ==>|"audit receipt<br/>with WEALTH computation hash"| WEALTH

  classDef witness fill:#4285F4,stroke:#000,color:#fff
  classDef governance fill:#A42E2E,stroke:#000,color:#fff
  classDef execution fill:#2E7D32,stroke:#000,color:#fff
  classDef truth fill:#000,stroke:#000,color:#fff
  class WEALTH witness
  class ARIFOS governance
  class AFORGE execution
  class VAULT truth
```

**WEALTH internal loop (capital reasoning):**

```
intent ───▶ capital_primitive (npv/irr/emv/mc) ───▶ capital_health (conservation/runway)
                                                              │
                                                              ▼
                                              capital_diagnose (collapse_signature · cascade)
                                                              │
                                                              ▼
                                              capital_entropy (power · who-pays · metric-drift)
                                                              │
                                                              ▼
                                              capital_ledger.write ──▶ VAULT999 (irreversible)
                                                              │
                                                              ▼
                                              wealth_judge_handoff ──▶ arifOS 888 JUDGE
```

**Hard rules:**
- WEALTH never allocates capital. Returns numbers + epistemic labels. Allocation is sovereign decision.
- `capital_ledger.write` requires `ack_irreversible=true` — no silent ledger writes.
- WEALTH never self-cites between witness organs except the GEOX capital bridge.

## Resources (18)

`wealth://schema` · `wealth://tools/registry` · `wealth://prompts/index` · `wealth://domains/index` · `wealth://runtime/policy` · `wealth://canon/002-human-law` · `wealth://glossary` · `wealth://federation/contract` · `wealth://health` · `wealth://reality/context` · `wealth://market/sources` · `wealth://risk/thresholds` · `wealth://affordance/contracts` · `wealth://handoff/arifos-schema` · `wealth://replay/receipt-schema` · `wealth://schema/field-dictionary` · `wealth://epistemic/tag-definitions` · `wealth://provenance/feeds`

## Prompts (7)

`wealth_reality_intake_loop` · `wealth_capital_diagnosis_loop` · `wealth_risk_downside_loop` · `wealth_market_reality_loop` · `wealth_allocation_judgment_loop` · `wealth_institutional_power_loop` · `wealth_arifos_handoff_loop`

---

## Architecture

```
/health     → live status, tool registry, deployment provenance
/tools/list → 8 public MCP tools
Port: 18082
```

```bash
curl -s http://127.0.0.1:18082/health | jq .
```

---

## 🔧 Stabilization (2026-08-06)

WEALTH underwent a constitutional stabilization audit. Changes across 6 files (−76 net lines, 0 new tools):

| ID | Fix | Verdict |
|----|-----|---------|
| **M0** | Receipt chain provisioned: `/root/VAULT999/wealth/receipts.jsonl` now persists. F11 AUDITABILITY reachable from every tool call. | ✅ |
| **C2** | `capital_wisdom` ghost tool **DELETED** (120 lines). Violated "WEALTH computes, arifOS frames" separation. F13 directive. | ✅ |
| **C4** | `capital_health` survival mode attribution bug fixed (was labeling as `capital_market`). | ✅ |
| **C6** | Dead import `register_institutional_tools` removed. | ✅ |
| **C7** | Preload ghost metadata removed from `capital_registry` (health/domains). | ✅ |
| **C8** | Unresolved `omni_wisdom` alias chain cleaned across 3 files. | ✅ |
| **C3** | Schema/runtime session_id gap documented in governance wrapper. | 📋 |
| **C10** | Judge trust boundary (`actor_cryptographically_verified`) documented as caller-declared. | 📋 |
| **C11** | Witness activation path (`is_complete`) documented — requires orchestrator. | 📋 |

**Result:** 8 tools, 18 resources, 7 prompts, 0 ghosts, receipts persisting, registry 8/8 PASS.

---

## 🧪 Backtest Acceptance Criteria (WEALTH v2)

When the orchestrator (`wealth_artifact_assemble`) ships, these three historical cases become the constitutional regression suite:

| Case | Cutoff | What It Tests | Pass If |
|------|--------|---------------|---------|
| **Enron** | 2000-12-31 | Reality ↔ Narrative divergence | `collapse_signature` + `beautiful_mouse` + `governance_capacity` all elevated BEFORE bankruptcy |
| **1MDB** | 2014-12-31 | Power ↔ Incentive capture | `capture_scan` + `power_audit` elevated BEFORE public unraveling |
| **LTCM** | 1998-06-01 | Risk ↔ Fragility detection | `tail_risk` + `cascade_model` + `fragility` elevated BEFORE failure |

All three test the ability to detect failure gradients using only pre-collapse public information. No hindsight permitted.

---

## 🏛️ Federation Navigation

| Organ | Role | Port | Repo | MCP | Health | LLMs |
|:---|:---|:---:|:---|:---|:---|:---|
| **⚖️ arifOS** | Constitutional Kernel — judges, seals | 8088 | [repo](https://github.com/ariffazil/arifos) | [mcp](https://mcp.arif-fazil.com/mcp) | [health](https://arifos.arif-fazil.com/health) | [llms.txt](https://arifos.arif-fazil.com/llms.txt) |
| **⚒️ A-FORGE** | Execution Engine — builds, deploys | 7071/72 | [repo](https://github.com/ariffazil/A-FORGE) | [mcp](https://forge.arif-fazil.com/mcp) | [health](https://forge.arif-fazil.com/health) | [llms.txt](https://forge.arif-fazil.com/llms.txt) |
| **🏛️ AAA** | Control Plane — A2A gateway, cockpit | 3001 | [repo](https://github.com/ariffazil/AAA) | — | [health](https://aaa.arif-fazil.com/health) | [llms.txt](https://aaa.arif-fazil.com/llms.txt) |
| **🌍 GEOX** | Earth Intelligence — seismic, wells | 8081 | [repo](https://github.com/ariffazil/GEOX) | [mcp](https://geox.arif-fazil.com/mcp) | [health](https://geox.arif-fazil.com/health) | [llms.txt](https://geox.arif-fazil.com/llms.txt) |
| **💰 WEALTH** | Capital Intelligence — NPV, risk | 18082 | [repo](https://github.com/ariffazil/WEALTH) | [mcp](https://wealth.arif-fazil.com/mcp) | [health](https://wealth.arif-fazil.com/health) | (llms.txt pending) |
| **🫀 WELL** | Vitality Guard — human readiness | 18083 | [repo](https://github.com/ariffazil/WELL) | [mcp](https://well.arif-fazil.com/mcp) | [health](https://well.arif-fazil.com/health) | [llms.txt](https://well.arif-fazil.com/llms.txt) |
| **🫀 arifFlow** | Metabolism — FQ pulse, receipts | 7073 | [repo](https://github.com/ariffazil/arifFlow) | — | [health](https://arifflow.arif-fazil.com/health) | — |
| **� FED** | Route Advisor — model/provider ranking | 7074 | private (internal) | — | [health](https://fed.arif-fazil.com/health) | — |
| **🔥 FLAME** | RM0 Inference — free-loop model mesh | 18901 | private (internal) | — | [health](https://flame.arif-fazil.com/health) | — |
| **🧱 FRAME** | Substrate — federation scaffolding | frame-organ.service | private (internal) | — | — | — |
| **🔮 HERMES** | Multi-Modal Bridge — Telegram relay | 8644 | [repo](https://github.com/ariffazil/HERMES) | — | — | — |
| **🌐 arif-fazil.com** | Public Web Surface — one domain | 443 | [repo](https://github.com/ariffazil/arif-fazil.com) | — | [verify](https://arif-fazil.com/999/verify) | — |

---

## 📡 MCP Registries

WEALTH is registered as an MCP server on the federation registries. Discovery metadata is exposed at each endpoint.

| Registry | Server | Manifest |
|----------|--------|----------|
| **Glama** | ⚠️ 301 → [glama.ai/mcp/servers/ariffazil/arifos](https://glama.ai/mcp/servers/ariffazil/arifos) | WEALTH uses arifOS umbrella |
| **TurboMCP** | ❌ 404 (2026-08-11) | Federation-wide entry — was `turbomcp.ai/server/ariffazil/arifos`, now dead |

Discovery endpoint: `GET https://arif-fazil.com/.well-known/mcp/server.json`

---

## � Sovereignty & License

- **License:** GNU Affero General Public License v3.0 (**AGPL-3.0**)
- **Sovereign:** **Muhammad Arif bin Fazil** (F13 SOVEREIGN)

> *DITEMPA BUKAN DIBERI — Forged, Not Given.*  
> *WEALTH computes. arifOS judges. Arif decides. 999 SEAL ALIVE.*

---

## 🛡️ CI Governance (F13 verdict 2026-08-10)

This repo follows the federation's CI governance pattern (replicated from `ariffazil/arifOS` PR #683). The pattern ensures Dependabot PRs receive a real, reproducible unprivileged verdict — no more all-red check rolls from structurally-incompatible gates.

**Per-repo adapter** (see `.github/workflows/` for the actual files):

- `.github/dependabot.yml` — `uv` (Python) / `cargo` (Rust) / `npm` (TypeScript) ecosystem; cooldown 3d; open-PRs 5; constitutional packages un-grouped (no `ignore:` — visibility preserved)
- `.github/workflows/dependabot-ci.yml` — unprivileged gate; runs ONLY on Dependabot PRs; SHA-bound probes
- `.github/workflows/{ci-uv-lock-invariant|cargo-lock-invariant|npm-lock-invariant}.yml` — universal `{uv lock --check && uv sync --frozen | cargo check --locked && cargo build --locked | npm ci}` invariant on every PR + push to main
- `.github/workflows/auto-merge-dependabot.yml` — constitutional package denylist (per-language); F13 review the only merge path
- Privileged workflows gated with `if: github.actor != 'dependabot[bot]' && github.actor != 'app/dependabot'` — so they SKIP for Dependabot PRs where their inputs cannot be satisfied

**Constitutional packages** (denied auto-merge, require F13 review):

| Language | Denylist |
|---|---|
| Python | `protobuf`, `cryptography`, `fastmcp-slim`, `fastmcp`, `caio`, `sentence-transformers`, `pynacl`, `blake3` |
| Rust    | `serde`, `tokio`, `hyper`, `axum`, `reqwest`, `rustls`, `async-trait`, `clap`, `tracing` |
| TypeScript | `zod`, `@modelcontextprotocol/sdk`, `fastmcp`, `mcp-sdk`, `tsx`, `vitest`, `@types/node`, `typescript`, `ts-node` |
| Static site | `vite`, `react`, `react-dom`, `react-router`, `@tanstack/react-query`, `tailwindcss` |

**Reference:** [`/root/AGENTS.md`](/root/AGENTS.md) — canonical federation doctrine. `AAA/docs/ORGAN.md` — topology.

DITEMPA BUKAN DIBERI — governance is forged, not given.
