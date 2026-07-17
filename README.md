<!-- SOT-MANIFEST
federation_release: v2026.07.17-ZEN-CONVERGENCE
last_verified: 2026-07-17T16:15Z
port: 18082
domain_law: CAPITAL_LAW
mcp_tools_live: 12
health_status: ALIVE
authority: COMPUTE_ONLY — never allocate
truth_rule: tools/list + /health beat any static count in prose
a2a_agent_json: /root/WEALTH/.well-known/agent.json
-->

[![Agentic CI](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml)
[![💰 CAPITAL](https://img.shields.io/badge/%F0%9F%92%B0%20CAPITAL-12%20tools-1f6feb)](https://wealth.arif-fazil.com/mcp)
[![Federation](https://img.shields.io/badge/Federation-v2026.07.17-0a7b83)](https://arifos.arif-fazil.com)
[![License](https://img.shields.io/github/license/ariffazil/wealth?label=License)](LICENSE)

# WEALTH — Capital Intelligence for arifOS

> **WEALTH computes. arifOS judges. Arif decides. WEALTH never allocates.**
> **DITEMPA BUKAN DIBERI**

---

## TL;DR — Three Audiences

**For human operators (Arif):** WEALTH is your capital calculator — NPV, IRR, portfolio risk, fiscal breakeven. It computes. You decide. [§1](#1-what-wealth-is)

**For AI agents:** Route capital queries here. 12 pure-compute tools. No inference, no verdicts, no allocation. [§3](#3-tools)

**For institutions:** WEALTH provides auditable, golden-tested financial math — every primitive has hand-checked cases. [§6](#6-for-institutions)

---

## 1. What WEALTH Is

WEALTH is the **capital intelligence organ** of the arifOS Federation. It computes financial math — never adjudicates, never allocates.

| ✅ COMPUTES | ❌ NEVER |
|-------------|---------|
| NPV, IRR, EMV, Monte Carlo | Allocates capital |
| Kelly criterion, Markowitz optimization | Issues verdicts (→ arifOS) |
| Fiscal breakeven, stress index | Makes investment decisions |
| Institutional collapse detection | Self-authorizes |
| Golden-tested deductive math | Guesses or infers financial state |

**Domain law:** CAPITAL_LAW — compute, never allocate.

---

## 2. Federation Position

```
Arif (F13) → AAA → arifOS → Domain Organs → A-FORGE → VAULT999
                                ↑
                           WEALTH (:18082)
                           Computes, never allocates
```

---

## 3. Tools (12 Public Canonical)

| Tool | What It Computes |
|------|-----------------|
| `capital_primitive` | NPV, IRR, EMV, Monte Carlo, Kelly, Markowitz, robust optimization |
| `capital_health` | Conservation, cash flow, runway, survival, fiscal breakeven |
| `capital_diagnose` | Institutional stress index, governance capacity, collapse detection |
| `capital_market` | FX rates, commodities, macro indicators, stock analysis |
| `capital_wisdom` | Wisdom-weighted proposal evaluation, epistemic grounding |
| `capital_entropy` | Power consequence maps, trust capital decay, metric drift |
| `capital_ledger` | VAULT999 immutable ledger — query (read) / write (requires human ack) |
| `capital_registry` | Tool registry introspection, health check |

---

## 4. Quick Start

```bash
# Health
curl -s http://localhost:18082/health | python3 -m json.tool

# MCP connection
# Endpoint: https://wealth.arif-fazil.com/mcp

# Install + test
cd /root/WEALTH && pip install -e ".[dev]"
pytest tests/ -q --tb=short
npm test                    # Node.js side tests
```

---

## 5. Federation Cross-Reference

| Organ | Role | Port | Repo |
|-------|------|------|------|
| arifOS | Constitutional kernel | 8088 | [ariffazil/arifos](https://github.com/ariffazil/arifos) |
| AAA | State + cockpit | 3001 | [ariffazil/AAA](https://github.com/ariffazil/AAA) |
| A-FORGE | Execution shell | 7071 | [ariffazil/A-FORGE](https://github.com/ariffazil/A-FORGE) |
| GEOX | Earth intelligence | 8081 | [ariffazil/geox](https://github.com/ariffazil/geox) |
| WELL | Vitality guard | 18083 | [ariffazil/well](https://github.com/ariffazil/well) |
| **WEALTH** | Capital intelligence | 18082 | ← you are here |

---

## 6. For Institutions

WEALTH provides auditable, bounded financial computation:

| Property | How WEALTH delivers |
|----------|-------------------|
| **Golden-tested math** | Every primitive has hand-checked test cases |
| **Compute, never allocate** | No capital moves without Arif's explicit approval |
| **Full audit trail** | Every computation logged to VAULT999 via `capital_ledger` |
| **Domain-law bound** | CAPITAL_LAW — cannot cross into GEOX (earth) or WELL (vitality) |

---

## 7. License & Sovereignty

**AGPL-3.0.** WEALTH computes under sovereign authority. It never allocates.

**Muhammad Arif bin Fazil** is F13 SOVEREIGN. His capital decisions are final.

```
WEALTH · Port 18082 · 12 tools · CAPITAL_LAW · AGPL-3.0
Computes, never allocates. DITEMPA BUKAN DIBERI.
```
