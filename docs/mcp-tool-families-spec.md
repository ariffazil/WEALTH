# WEALTH MCP Tool Families — Operational Spec

> **Version:** v1.0.0-canonical  
> **Status:** SEALED  
> **Epistemic:** CLAIM  
> **DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**

---

## 1. The Six Orthogonal Families

| Family | Core Question | Representative Tools |
|---|---|---|
| **`wealth.state`** | “What is the capital climate?” | `wealth_state_market_snapshot` |
| **`wealth.risk`** | “How much can we safely put at risk?” | `wealth_risk_capital_allocation` |
| **`wealth.price`** | “What is the true (risk + entropy) discount rate?” | `wealth_price_capitalx`, `wealth_price_exergy_cost` |
| **`wealth.flow`** | “How do cash and entropy evolve over time?” | `wealth_flow_scenario_npv` |
| **`wealth.justice`** | “Who pays, and is that acceptable?” | `wealth_justice_maruah_score` |
| **`wealth.control`** | “What do we fund, and what do we 888_HOLD?” | `wealth_control_gate_888` |

---

## 2. Design Principles

1. **Non-overlapping mandates:** Each tool family touches exactly one axis.
2. **Envelope binding:** Every tool request carries `envelope_id`, linking it to the `PERMITTED`/`FEASIBLE` upstream seals from arifOS/GEOX.
3. **Thermodynamic grounding:** Pricing tools must expose entropy penalties and exergy costs, not hide them in a black-box rate.
4. **Justice as hard constraint:** `M < 0.4` produces `VOID` or `888_HOLD`, not just a footnote.
5. **VAULT999 traceability:** Every response carries a `vault_log_entry` fragment for immutable append-only logging.

---

## 3. Tool Specifications

### 3.1 `wealth_state_market_snapshot`
**Purpose:** Establish baseline capital temperature and entropy level.

**Inputs:**
- `jurisdiction` (e.g. `MY`, `US`, `ASEAN`)
- `asset_classes` (array of strings)
- `tenor_months` (default 120)

**Outputs:**
- `rf_curve` — risk-free term structure
- `erp` — equity risk premium
- `credit_spreads` — by rating bucket
- `volatility_surface` — entropy/vol proxy
- `capital_temperature` — composite risk/entropy proxy [ESTIMATE]

---

### 3.2 `wealth_risk_capital_allocation`
**Purpose:** Turn GEOX feasibility into safe capital deployment limits.

**Inputs:**
- `portfolio` — bucket definitions (project/region/counterparty)
- `confidence_level` — e.g. 0.995 for tail risk
- `maruah_drawdown_floor` — default 0.6

**Outputs:**
- `economic_capital` — aggregate risk capital required
- `risk_decomposition` — factor/geo/scenario attribution
- `risk_budgets` — per-bucket limits
- `liquidity_buffer` — solvency margin

**Governance:** If any bucket breaches `maruah_drawdown_floor`, flag for `wealth_control_gate_888`.

---

### 3.3 `wealth_price_capitalx`
**Purpose:** Compute the constitutional risk-adjusted cost of capital.

**Inputs:**
- `base_rate` — nominal risk-free starting point
- `signals` — `{ dS, peace2, maruahScore, trustIndex, deltaCiv }`
- `wealth_basis` — optional `W⃗ = (Ê, Ŝ, Eχ̂)`
- `defects` — optional `{ paradox, scar, shadow }`

**Outputs:**
- `r_adj` — clamped ≥ 0
- `adjustments` — full breakdown of penalties/discounts
- `uncertainty_band` — F7 humility band

**Formula (existing):**
```
r_adj = base_rate
        + max(0, dS × 0.5)
        − min(0.02, max(0, (peace2 − 1.0) × 0.05))
        − min(0.03, max(0, (maruahScore − 0.5) × 0.06))
        − min(0.02, max(0, (trustIndex − 0.5) × 0.04))
        − min(0.02, max(0, deltaCiv × 0.10))
```

If `wealth_basis` and `defects` are provided, `deltaCiv` is promoted via the basis formula:
```
deltaCiv = α·log(1 + Ê) + β·(1 − Ŝ) + γ·Eχ̂ − δ·P − ε·Σ − ζ·Sh
```

---

### 3.4 `wealth_price_exergy_cost`
**Purpose:** Estimate thermodynamic (energy + material) cost per unit of output.

**Inputs:**
- `energy_mj_per_unit`
- `material_exergy_mj_per_unit`
- `output_unit`

**Outputs:**
- `exergy_mj_per_unit`
- `emergy_proxy` — aggregated resource memory [ESTIMATE]
- `entropy_cost_per_unit` — irreversible loss proxy [ESTIMATE]

**Use:** Feed into `wealth_flow_scenario_npv` as a shadow cost, or into `capitalx` as an additional penalty when shadow is high.

---

### 3.5 `wealth_flow_scenario_npv`
**Purpose:** Project cashflows and entropy evolution under regimes.

**Inputs:**
- `cashflows` — base case array
- `r_adj` — from `wealth_price_capitalx`
- `scenarios` — policy/shock/regime definitions
- `geo_constraints` — GEOX feasibility flags

**Outputs:**
- `npv_distribution` — per-scenario NPVs
- `irr` — internal rate of return using `r_adj`
- `payback_years`
- `regime_impacts` — carbon price, subsidy removal, etc.

**Governance:** Any scenario with ` Peace² < 1.0` or `ΔS > 0` without 888_HOLD is downgraded to `VOID`.

---

### 3.6 `wealth_justice_maruah_score`
**Purpose:** Measure dignity/integrity impact and distributional fairness.

**Inputs:**
- `project_profile` — `{ displacement_risk, pollution_load, cultural_loss_risk, community_benefit_share }`

**Outputs:**
- `maruah_score` — [0,1]
- `maruah_band` — `SOVEREIGN` / `STABLE` / `FLOOR` / `AMBER` / `RED`
- `incidence_map` — who bears cost / receives benefit
- `exclusion_flags` — auto-flagged categories (ecocide, dignity-burning)

**Governance:** `RED` band triggers mandatory `888_HOLD` for any capital access.

---

### 3.7 `wealth_control_gate_888`
**Purpose:** Final routing gate before capital execution.

**Inputs:**
- `candidate` — `{ maruah, r_adj, entropy_budget_remaining, reversible }`

**Outputs:**
- `hold_triggered` — boolean
- `hold_reasons` — array of strings
- `recommendation` — `FUND` / `DEFER` / `RESTRUCTURE` / `KILL`
- `repricing_hints` — actionable strings (e.g. "reduce exergy cost by 12%")
- `upstream_signal` — telemetry back to arifOS/GEOX

**Trigger conditions:**
- `maruah < 0.4` → `888-HOLD`
- `reversible === false && human_confirmed === false` → `888-HOLD`
- `entropy_budget_remaining < 0` → `VOID`
- `r_adj` above policy corridor → `DEFER` or `RESTRUCTURE`

---

## 4. Integration with W@W Envelope

Every tool request must include:
```json
{
  "header": {
    "session_id": "...",
    "envelope_id": "...",
    "epoch": "2026-04-14T..."
  }
}
```

The `envelope_id` binds the tool call to the monotone-narrowing constraint chain defined in `waw-envelope.json`. If the envelope is missing, `F3` (Input Clarity) fails and the tool returns `SABAR`.

---

## 5. Telemetry & VAULT999

Every response footer includes:
- `verdict` — `SEAL`, `QUALIFY`, `888-HOLD`, `VOID`
- `epistemic` — `CLAIM`, `PLAUSIBLE`, `ESTIMATE`, `HYPOTHESIS`, `UNKNOWN`
- `vault_log_entry` — fragment for immutable logging
- `witness` — `{ human, ai, earth }`

This satisfies `F2` (truth tagging), `F7` (humility bands), `F9` (anti-hantu transparency), and `F13` (sovereign witness).

---

## 6. Failure Modes

| Failure | Symptom | Mitigation |
|---|---|---|
| **Missing envelope** | Tool called without `envelope_id` | F3 SABAR; require upstream authority binding |
| **Rate inversion** | `r_adj` decreases while `dS` or shadow increases | F12 hard block; reject output; log anomaly |
| **Justice bypass** | `maruah_score` omitted in capital access flow | F6 VOID; block funding until score computed |
| **Black-box pricing** | `adjustments` object missing or incomplete | F2 warning; downgrade epistemic to UNKNOWN |
| **Stale snapshot** | `wealth_state_market_snapshot` older than 24h | Recompute; reject stale prices for sealed ops |
| **Orphan control** | `wealth_control_gate_888` run before pricing/justice tools | Require prerequisite seals in `upstream_seals` |

---

*Spec v1.0.0 | SEALED as WEALTH MCP canon | 999 SEAL ALIVE*
