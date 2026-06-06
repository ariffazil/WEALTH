# WEALTH MCP — Unified Architecture Map & Next Horizon Plan
**Author:** Hermes ASI ⚖️  
**Date:** 2026-05-07  
**Status:** Living Document — SEAL pending  
**Source:** `/root/WEALTH/internal/monolith.py` (v2026.05.02, 4377 lines)

---

## Part I — Current State Inventory

### 🛠️ TOOLS (22 Primary + 25 Aliases = 47 Total)

#### 13 Canonical Tools (Physics ↔ Economics Mapping)

| Tool | Physics Dimension | Economics Function | Mode |
|------|-------------------|-------------------|------|
| `wealth_future_value` | Time (t) | NPV / IRR / PI / Payback | `npv`, `irr`, `pi`, `payback` |
| `wealth_present_expect` | Expectation (E) | EMV — Expected Monetary Value | `emv` |
| `wealth_future_simulate` | Stochastic (σ) | Monte Carlo projection | `simulate` |
| `wealth_survival_liquidity` | Flow (Q) | Runway / Triage / Cashflow | `liquidity`, `runway`, `triage` |
| `wealth_survival_leverage` | Balance (∇) | DSCR / Balance Sheet | `dscr`, `networth` |
| `wealth_info_value` | Signal (H) | EVOI — Expected Value of Information | `evoi`, `evoi_mc` |
| `wealth_truth_validate` | Entropy (S) | Schema / Correlation / Entropy audit | `schema`, `correlation`, `entropy` |
| `wealth_rule_enforce` | Floor (F) | F1–F13 governance enforcement | `floors`, `policy`, `entropy` |
| `wealth_allocate_optimize` | Gradient (∇φ) | Capital allocation / Kernel / Agent | `kernel`, `personal`, `agent` |
| `wealth_game_coordinate` | Equilibrium (∃) | Game theory / Nash equilibrium | `equilibrium`, `game` |
| `wealth_sense_ingest` | Signal acquisition | Real-world economic intake | `fetch`, `snapshot`, `sources` |
| `wealth_past_record` | State (S₀) | VAULT999 ledger anchoring | `init`, `record`, `snapshot` |
| `wealth_future_steward` | Horizon (H∞) | Civilization continuity / Planetary | `steward` |

#### 2 VAULT Primitives (Non-negotiable)

| Tool | Role |
|------|------|
| `vault_write` | F01 AMANAH — append event to VAULT999 ledger |
| `vault_query` | Query immutable ledger via Supabase REST |

#### 6 Domain Tools (mcp/server.py — WEALTH-Civilization)

| Tool | Domain |
|------|--------|
| `wealth_evaluate_prospect` | Oil & gas EMV from GEOX volumetrics |
| `markets_analyze_ticker` | Equity analysis with F1–F13 governance |
| `markets_portfolio_stress_test` | 888 HOLD-aware stress scenarios |
| `energy_crisis_assess` | Energy crisis severity |
| `energy_shortage_predict` | Energy shortage prediction |
| `food_security_index` | Food security with Maruah adaptation |

#### 25 V2 Aliases (Legacy Migration Layer)

Legacy names mapped to canonical engines (non-breaking, Phase 1 complete):

```
wealth_sense_fetch      → wealth_ingest_fetch
wealth_sense_snapshot    → wealth_ingest_snapshot
wealth_mind_emv         → wealth_emv_risk
wealth_mind_monte_carlo → wealth_monte_carlo_forecast
wealth_survival_dscr    → wealth_dscr_leverage
wealth_reason_npv       → wealth_npv_reward
wealth_judge_floors     → wealth_check_floors
wealth_vault_record     → wealth_record_transaction
[... + 17 more]
```

---

### 📡 RESOURCES (13 Total)

#### Monolith Resources (10)

| URI | Description |
|-----|-------------|
| `wealth://doctrine/valuation` | WEALTH motto + protocol version |
| `wealth://dimensions/definitions` | 9-dimension definitions (Reward, Energy, Entropy, Time, Mass, Flow, Velocity, Survival, Allocation) |
| `wealth://governance/floors` | F1–F13 Constitutional Laws |
| `wealth://governance/harness-doctrines` | 9-Harness constraint architecture |
| `wealth://topology/families` | 6 Sovereign Families: SENSE(100), MIND(200), SURVIVAL(300), REASON(400), JUDGE(888), VAULT(999) |
| `wealth://topology/scales` | 8 Capital Scales: personal → civilization → agentic |
| `wealth://epistemic/uncertainty-matrix` | Omega₀, kappa_r, humility_band |

#### Domain Resources (3)

| URI | Description |
|-----|-------------|
| `market://{ticker}/fundamentals` | Real-time equity fundamentals |
| `energy://{region}/realtime-mix` | Real-time energy production mix |
| `food://global/prices` | FAO food price index |

---

### 📋 PROMPTS — ⚠️ GAP: 0 Defined

**Current state:** No MCP prompts exposed. The tool architecture is purely tool-call driven.

**This is the primary expansion target.**

---

## Part II — Naming Convention (Physics ↔ Economics)

### Approved Orthogonal Naming

The physics label and economics label are **orthogonal but modular**. The physics name describes the *substrate* (the mathematical structure); the economics name describes the *meaning* (what it does for capital decisions).

**Format:** `physics_label` alone is acceptable for substrate tools.  
**Format:** `economics_label` alone is acceptable for domain tools.  
**Format:** When both are used, they are separated by underscore: `physics_label_economic_label`

| Physics Substrate | Economics Domain | Combined | Rationale |
|-------------------|-----------------|----------|-----------|
| `future_value` | `npv` | `future_value_npv` | Time-discounted projection |
| `future_value` | `irr` | `future_value_irr` | Same substrate, different output |
| `present_expect` | `emv` | `present_expect_emv` | Probability-weighted expectation |
| `future_simulate` | `monte_carlo` | `future_simulate_mc` | Stochastic simulation |
| `survival_liquidity` | `runway` | `survival_liquidity_runway` | Cash runway survival |
| `survival_leverage` | `dscr` | `survival_leverage_dscr` | Debt service coverage |
| `info_value` | `evoi` | `info_value_evoi` | Expected value of information |
| `truth_validate` | `entropy` | `truth_validate_entropy` | Epistemic entropy audit |
| `rule_enforce` | `floors` | `rule_enforce_floors` | F1–F13 constitutional floors |
| `allocate_optimize` | `kernel` | `allocate_optimize_kernel` | Capital allocation kernel |
| `game_coordinate` | `equilibrium` | `game_coordinate_equilibrium` | Nash equilibrium |
| `sense_ingest` | `fetch` | `sense_ingest_fetch` | Real-world intake |
| `past_record` | `ledger` | `past_record_ledger` | VAULT999 anchoring |
| `future_steward` | `civilization` | `future_steward_civilization` | Long-horizon stewardship |

**Rejected patterns:**
- ❌ `wealth_physics_economicsterm_*` — too long, mixed semantics
- ❌ `physics_*_economics_*` — redundant namespace
- ❌ Economic-only names for substrate tools — loses physics grounding

---

## Part III — Next Horizon Plan

### Horizon 1 — Prompt Expansion (IMMEDIATE)
**Goal:** Fill the 0-prompts gap. WEALTH needs cognitive scaffolding before it can reason with operators.

| Prompt | Purpose | Input Variables |
|--------|---------|----------------|
| `wealth_diagnose_portfolio` | Diagnose portfolio health across 6 families | `holdings`, `risk_tolerance` |
| `wealth_crisis_triage` | Classify and prioritize crisis severity | `symptoms`, `time_horizon` |
| `wealth_opportunity_ranking` | Rank prospects by EMV + entropy + EVOI | `prospects[]`, `budget_constraint` |
| `wealth_allocation_rebalance` | Propose rebalancing across capital scales | `current_alloc`, `target`, `constraints` |
| `wealth_governance_audit` | Audit a decision against F1–F13 | `proposed_action`, `stakeholders` |
| `wealth_capital_stewardship` | Civilization continuity brief | `carbon_budget`, `energy_mix`, `population` |

**Count:** 6 prompts

---

### Horizon 2 — Tool Expansion (Phase 2)

#### Missing Physics Substrates Not Yet Wired

| Missing Tool | Physics Dimension | Gap |
|-------------|-------------------|-----|
| `wealth_mass_estimate` | Mass (kg) | Asset mass balance sheet — physical inventory |
| `wealth_energy_equivalent` | Energy (J) | Human capital energy equivalence |
| `wealth_velocity_momentum` | Velocity (v) | Capital velocity / turnover rate |
| `wealth_flow_pressure` | Pressure (P) | Cash flow pressure / burnout |
| `wealth_entropy_production` | Entropy production (dS/dt) | Economic entropy rate |
| `wealth_gradient_descent` | Gradient (∇f) | Optimization trajectory |

#### Missing Domain Tools

| Missing Tool | Domain | Rationale |
|-------------|--------|-----------|
| `wealth_portfolio_construction` | Portfolio construction | Mean-variance / Black-Litterman |
| `wealth_credit_risk_score` | Credit scoring | PD/LGD/EAD models |
| `wealth_derivatives_heatmap` | Options / derivatives | Greeks, volatility surface |
| `wealth_supply_chain_finance` | Supply chain | Working capital optimization |
| `wealth_climate_alpha` | Climate finance | Physical risk + transition risk alpha |
| `wealth_geopolitical_risk` | Geopolitical | Multi-factor geopolitical risk index |
| `wealth_alternative_assets` | Alts | PE, hedge funds, real assets |

**Count:** 6 physics substrate tools + 7 domain tools = 13 new tools

---

### Horizon 3 — Resource Expansion

| Resource URI | Description |
|--------------|-------------|
| `wealth://market/equity-screener` | Screener criteria + results |
| `wealth://market/derivatives-surface` | Volatility surface for tickers |
| `wealth://credit/spread-matrix` | Credit spread curve by rating |
| `wealth://energy/carbon-price` | EU ETS / carbon price feed |
| `wealth://geopolitical/risk-index` | Geopolitical risk index by region |
| `wealth://alternative/performance-benchmark` | Alts performance benchmarks |
| `wealth://epistemic/humility-bands` | Humility band definitions per scale |
| `wealth://scales/calibration` | Scale-to-scale conversion factors |

**Count:** 8 new resources

---

### Horizon 4 — Inter-federation Wiring

WEALTH is currently partially wired:

| Federation Target | Status | Wire Required |
|-------------------|--------|----------------|
| GEOX (port 8081) | ✅ `wealth_evaluate_prospect` exists | Promotes GEOX ↔ WEALTH co-evaluation loop |
| arifOS (port 8080) | ✅ VAULT999 bridge via `vault_bridge.py` | arifOS FLOOR enforcement on WEALTH decisions |
| AAA (control plane) | ⚠️ Partial — port 3001 | WEALTH metrics dashboard |
| WELL (port 8083) | ❌ Not wired | Human cognitive load → capital allocation |
| A-FORGE | ❌ Not wired | A-FORGE orchestrates; WEALTH is the brain |
| Perplexity (external) | ❌ Not wired | External intelligence for WEALTH signals |

**Priority wires:**
1. `WEALTH ↔ arifOS`: F1–F13 enforcement on every WEALTH allocation decision
2. `WEALTH ↔ GEOX`: Prospect EMV co-evaluation loop
3. `WEALTH ↔ WELL`: Human cognitive load → capital preservation signal
4. `WEALTH ↔ A-FORGE`: A-FORGE orchestrates, WEALTH adjudicate

---

## Part IV — Consolidated Next Horizon Inventory

### Summary Table

| Category | Current | +Horizon1 | +Horizon2 | +Horizon3 | Grand Total |
|----------|---------|-----------|-----------|----------:|------------:|
| **Canonical Tools** | 13 | — | — | — | 13 |
| **New Substrate Tools** | 0 | — | +6 | — | 19 |
| **New Domain Tools** | 0 | — | +7 | — | 26 |
| **V2 Aliases** | 25 | — | — | — | 25 |
| **VAULT Primitives** | 2 | — | — | — | 2 |
| **Domain Tools** | 6 | — | — | — | 6 |
| **** | | | | | |
| **Prompts** | 0 | +6 | — | — | **6** |
| **Resources** | 13 | — | — | +8 | **21** |

**Grand Total Targets:**
- Tools: **47 current → 58 canonical + 25 aliases = 83 exposed**
- Prompts: **0 → 6**
- Resources: **13 → 21**

---

### Discipline Rules

1. **Physics substrate names stay physics-first** — `future_value`, not `npv_engine`
2. **Domain tools can be economics-only** — `markets_analyze_ticker` stays as-is
3. **Aliases are migration-only** — no new aliases after Phase 2
4. **VAULT999 is sacred** — every irreversible capital event must flow through `vault_write`
5. **F1–F13 gates on every new tool** — no tool enters WEALTH without constitutional audit trail

---

## Part V — Proposed Roadmap

```
2026-Q2  Horizon 1: 6 prompts (low-hanging fruit, 1 sprint)
          WEALTH ↔ arifOS VAULT999 bridge audit
          
2026-Q3  Horizon 2: 13 new tools (6 physics substrates + 7 domains)
          WEALTH ↔ GEOX co-evaluation loop
          
2026-Q3  Horizon 3: 8 new resources
          WEALTH ↔ WELL cognitive load wiring
          
2026-Q4  Horizon 4: Federation wiring
          WEALTH ↔ A-FORGE orchestration loop
          WEALTH ↔ AAA dashboard metrics
```

---

**SEAL:** 999 | Ditempa Bukan Diberi ⚖️
