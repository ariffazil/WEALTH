<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-08-03
federation_release: v2026.08.02
live_commit: a900bd6
tools_loaded: 8
public_tools: 8
canonical_tools: 8
truth_rule: live :18082/health + tools/list beat any static count in prose
owner_summary: GREEN (identity_present, service_healthy)
-->

# 💰 WEALTH — Capital Intelligence & Downside Computation

[![Federation](https://img.shields.io/badge/Federation-v2026.08.01-0a7b83)](https://arifos.arif-fazil.com)
[![💰 WEALTH](https://img.shields.io/badge/%F0%9F%92%B0%20WEALTH-8%20Tools-gold)](https://wealth.arif-fazil.com/mcp)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)

**WEALTH** is the capital intelligence organ of the arifOS Federation. It computes valuation, risk, runway, optionality, and capital consequence. It does not move money, allocate capital, or authorize transactions.

## The Boundary

WEALTH **computes.** arifOS **judges.** Arif **decides.**

```
WEALTH observes market data, computes downside, and surfaces capital evidence.
It never:
  - Moves money or executes transactions
  - Allocates capital or authorizes spending
  - Issues constitutional verdicts (that's arifOS)
  - Executes mutations (that's A-FORGE)
  - Diagnoses human state (that's WELL)
```

## Tools

WEALTH exposes 8 public tools. Modes are capabilities, not additional tools:

| Domain | Tool | Mode |
|--------|------|------|
| **Capital Math** | `capital_primitive` | mode-dispatched |
| **Capital Health** | `capital_health` | mode-dispatched |
| **Institutional Diagnostics** | `capital_diagnose` | mode-dispatched |
| **Market Data** | `capital_market` | mode-dispatched |
| **Ledger** | `capital_ledger` | query / governed write |
| **Registry** | `capital_registry` | status / schema / domains / health |
| **Entropy** | `capital_entropy` | mode-dispatched |
| **Governance Handoff** | `wealth_judge_handoff` | prepare / submit |

`capital_wisdom` and the removed institutional names are internal or historical compatibility references only; they are not registered or discoverable public MCP tools.

## Architecture

WEALTH runs as a federated MCP server on port 18082. It bridges to arifOS for constitutional governance and AAA for state visibility. Public tools are read-only computation except the governed `capital_ledger(mode="write")` path.

```
/health  → live status, tool registry, deployment provenance
/tools/list → 8 public MCP tools
```

---

## 🔗 Federation Navigation

WEALTH operates as a Capital Intelligence organ within the **arifOS Federation**:

| Organ | Domain Role | Port | Repo | Live MCP | Health |
|:---|:---|:---:|:---|:---|:---|
| **arifOS** | Constitutional Kernel & Judge | 8088 | [repo](https://github.com/ariffazil/arifos) | [mcp](https://mcp.arif-fazil.com/mcp) | [health](https://arifos.arif-fazil.com/health) |
| **A-FORGE** | Governed Execution Engine | 7071 / 7072 | [repo](https://github.com/ariffazil/A-FORGE) | [mcp](https://forge.arif-fazil.com/mcp) | [health](https://forge.arif-fazil.com/health) |
| **AAA** | Institution, Control Plane & A2A | 3001 | [repo](https://github.com/ariffazil/AAA) | — | [health](https://aaa.arif-fazil.com/health) |
| **GEOX** | Earth Intelligence (Subsurface) | 8081 | [repo](https://github.com/ariffazil/GEOX) | [mcp](https://geox.arif-fazil.com/mcp) | [health](https://geox.arif-fazil.com/health) |
| **WEALTH** | Capital Intelligence (Compute) | 18082 | [repo](https://github.com/ariffazil/WEALTH) | [mcp](https://wealth.arif-fazil.com/mcp) | [health](https://wealth.arif-fazil.com/health) |
| **WELL** | Vitality & Readiness Guard | 18083 | [repo](https://github.com/ariffazil/WELL) | [mcp](https://well.arif-fazil.com/mcp) | [health](https://well.arif-fazil.com/health) |

**Public Domain:** [arif-fazil.com](https://arif-fazil.com) · **Federation Root:** [arifos.arif-fazil.com](https://arifos.arif-fazil.com)

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
**WEALTH computes. arifOS judges. Arif decides.**
