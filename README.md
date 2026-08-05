<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-08-04T20:23:33Z
federation_release: v2026.08.04
live_commit: 34e5b3f (IndentationError fix in monolith.py — 11 tests unblocked)
tools_loaded: 8
public_tools: 8
canonical_tools: 8
truth_rule: live :18082/health + tools/list beat any static count in prose
owner_summary: GREEN (identity_present, service_healthy)
-->

# 💰 WEALTH — Capital Intelligence Organ

[![Federation](https://img.shields.io/badge/Federation-v2026.08.04-0a7b83)](https://arifos.arif-fazil.com)
[![💰 WEALTH](https://img.shields.io/badge/%F0%9F%92%B0%20WEALTH-8%20Tools-gold)](https://wealth.arif-fazil.com/mcp)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)

> **WEALTH computes. arifOS judges. Arif decides.**
> **DITEMPA BUKAN DIBERI — Forged, Not Given.**

**WEALTH** is the capital intelligence organ of the arifOS Federation. It computes valuation, risk, runway, optionality, and capital consequence. It does not move money, allocate capital, or authorize transactions.

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

| Domain | Tool | Capabilities |
|--------|------|-------------|
| **Capital Math** | `capital_primitive` | NPV · IRR · EMV · Monte Carlo · Kelly criterion · Markowitz |
| **Capital Health** | `capital_health` | Runway · Burn rate · Survival analysis · Fiscal health |
| **Market Data** | `capital_market` | FX rates · Commodities (Brent, gold, gas) · Stock fundamentals |
| **Institutional** | `capital_diagnose` | Stress index · Governance capacity · Cascade modeling · Exploitation detection |
| **Entropy** | `capital_entropy` | Capital entropy · Consequence displacement · Metric drift |
| **Ledger** | `capital_ledger` | VAULT999 query · Governed write |
| **Registry** | `capital_registry` | Status · Schema · Domain index · Health |
| **Handoff** | `wealth_judge_handoff` | Structured envelope for arifOS governance review |

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

## 🏛️ Federation Navigation

| Organ | Role | Port | Repo | MCP | Health | LLMs |
|:---|:---|:---:|:---|:---|:---|:---|
| **⚖️ arifOS** | Constitutional Kernel — judges, seals | 8088 | [repo](https://github.com/ariffazil/arifos) | [mcp](https://mcp.arif-fazil.com/mcp) | [health](https://arifos.arif-fazil.com/health) | [llms.txt](https://arifos.arif-fazil.com/llms.txt) |
| **⚒️ A-FORGE** | Execution Engine — builds, deploys | 7071/72 | [repo](https://github.com/ariffazil/A-FORGE) | [mcp](https://forge.arif-fazil.com/mcp) | [health](https://forge.arif-fazil.com/health) | [llms.txt](https://forge.arif-fazil.com/llms.txt) |
| **🏛️ AAA** | Control Plane — A2A gateway, cockpit | 3001 | [repo](https://github.com/ariffazil/AAA) | — | [health](https://aaa.arif-fazil.com/health) | [llms.txt](https://aaa.arif-fazil.com/llms.txt) |
| **🌍 GEOX** | Earth Intelligence — seismic, wells | 8081 | [repo](https://github.com/ariffazil/GEOX) | [mcp](https://geox.arif-fazil.com/mcp) | [health](https://geox.arif-fazil.com/health) | [llms.txt](https://geox.arif-fazil.com/llms.txt) |
| **💰 WEALTH** | Capital Intelligence — NPV, risk | 18082 | [repo](https://github.com/ariffazil/WEALTH) | [mcp](https://wealth.arif-fazil.com/mcp) | [health](https://wealth.arif-fazil.com/health) | [llms.txt](https://wealth.arif-fazil.com/llms.txt) |
| **🫀 WELL** | Vitality Guard — human readiness | 18083 | [repo](https://github.com/ariffazil/WELL) | [mcp](https://well.arif-fazil.com/mcp) | [health](https://well.arif-fazil.com/health) | [llms.txt](https://well.arif-fazil.com/llms.txt) |
| **🔮 HERMES** | Multi-Modal Bridge — Telegram relay | 8644 | [repo](https://github.com/ariffazil/HERMES) | — | — | — |
| **🌐 arif-fazil.com** | Public Web Surface — one domain | 443 | [repo](https://github.com/ariffazil/arif-fazil.com) | — | [verify](https://arif-fazil.com/999/verify) | — |

---

## 📡 MCP Registries

WEALTH is registered as an MCP server on the federation registries. Discovery metadata is exposed at each endpoint.

| Registry | Server | Manifest |
|----------|--------|----------|
| **Glama** | [glama.ai/mcp/servers/ariffazil/wealth](https://glama.ai/mcp/servers/ariffazil/wealth) | `https://wealth.arif-fazil.com/.well-known/glama.json` |
| **Smithery** | [smithery.ai/server/wealth](https://smithery.ai/server/wealth) | `https://wealth.arif-fazil.com/.well-known/smithery.yaml` |
| **mcp.so** | [mcp.so/server/ariffazil/wealth](https://mcp.so/server/ariffazil/wealth) | `https://wealth.arif-fazil.com/.well-known/mcp-so.json` |

Discovery endpoint: `GET https://wealth.arif-fazil.com/.well-known/mcp/server.json`

---

## � Sovereignty & License

- **License:** GNU Affero General Public License v3.0 (**AGPL-3.0**)
- **Sovereign:** **Muhammad Arif bin Fazil** (F13 SOVEREIGN)

> *DITEMPA BUKAN DIBERI — Forged, Not Given.*  
> *WEALTH computes. arifOS judges. Arif decides. 999 SEAL ALIVE.*
