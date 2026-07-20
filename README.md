<!-- SOT-MANIFEST
federation_release: v2026.07.20-ZEN-CONVERGENCE
last_verified: 2026-07-20T16:25Z
live_commit: ad2d5a1
port: 18082
domain_law: CAPITAL_LAW
mcp_tools_live: 20
health_status: ALIVE
authority: COMPUTE_ONLY — never allocate
truth_rule: tools/list + /health beat any static count in prose
a2a_agent_json: /root/WEALTH/.well-known/agent.json
-->

[![Agentic CI](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml)
[![💰 CAPITAL](https://img.shields.io/badge/%F0%9F%92%B0%20CAPITAL-12%20tools-1f6feb)](https://wealth.arif-fazil.com/mcp)
[![Federation](https://img.shields.io/badge/Federation-v2026.07.19-0a7b83)](https://arifos.arif-fazil.com)
[![License](https://img.shields.io/github/license/ariffazil/wealth?label=License)](LICENSE)

# WEALTH — Capital Intelligence for arifOS

> **WEALTH computes. arifOS judges. Arif decides. WEALTH never allocates.**
> **DITEMPA BUKAN DIBERI**

---

## TL;DR — Three Audiences

**For human operators (Arif):** WEALTH is your capital calculator — NPV, IRR, portfolio risk, fiscal breakeven. It computes. You decide. [§1](#1-what-wealth-is)

**For AI agents:** Route capital queries here. 20 pure-compute tools. No inference, no verdicts, no allocation. [§3](#3-tools)

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

---

## 🛡️ Federation Governance

This organ operates under the [arifOS Federation Contract](FEDERATION_CONTRACT.md). All 13 constitutional floors (F1-F13) apply. Compute only — never allocate capital. All outputs labeled OBS/DER/INT/SPEC per F2 TRUTH.

### Constitutional Compliance
- **F1 AMANAH:** All mutations reversible or backed up
- **F2 TRUTH:** Epistemic labels on all substantive claims
- **F3 WITNESS:** Tri-witness required for SEAL-grade outputs
- **F4 CLARITY:** ΔS ≤ 0 — every output reduces entropy
- **F11 AUDIT:** Every tool call logged to VAULT999

### Quick Links
- [Federation Landing](/root/AGENTS.md)
- [Organ Map](/root/AAA/docs/ORGAN.md)
- [VAULT999](/root/VAULT999/)
- [Secrets Vault](/root/.secrets/INDEX.md)

---

## 🔧 Tool Registry

This organ exposes MCP tools discoverable via `tools/list` on port 18082. For the canonical tool manifest, query the live registry.

### Epistemic Standards (F2 TRUTH)
All tool outputs follow the epistemic labeling convention:
- **OBS** — Direct observation from market data or measurement
- **DER** — Derived from OBS via deterministic computation
- **INT** — Interpretation requiring capital/financial expertise
- **SPEC** — Speculative, forward-looking, or hypothetical

### Audit Trail (F11)
Every tool invocation that produces evidence is logged to VAULT999 with actor signature. Immutable. Append-only. Hash-chained.

### Connection
```bash
curl -s http://localhost:18082/health | python3 -m json.tool
```

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
*DITEMPA BUKAN DIBERI — Forged, Not Given.*

### Capital Primitives

| Mode | Description |
|------|-------------|
| `npv` | Net Present Value |
| `irr` | Internal Rate of Return |
| `emv` | Expected Monetary Value |
| `evoi` | Expected Value of Information |
| `mc` | Monte Carlo simulation |
| `kelly` | Kelly criterion position sizing |
| `markowitz` | Modern portfolio optimization |
| `robust` | Robust optimization under uncertainty |
| `chance_constrained` | Chance-constrained stochastic programming |
| `two_stage` | Two-stage stochastic programming with recourse |

All primitives are pure deductive math — golden-tested against hand-checked cases.

### Market Intelligence
FX rates, commodity prices, stock analysis, gold/oil/gas signals — observational with derived and interpreted fields. Never a trading recommendation. WEALTH computes; arifOS judges; Arif decides.

### Capital Wisdom
Multi-dimensional proposal evaluation across dignity, sovereignty, resilience, inequality, ecological cost, and optionality. Advisory only. Does NOT emit GO/HOLD/SEAL verdicts — those are arifOS's domain.

*Compute only. Never allocate. VAULT999-audited. F13 sovereign.*
