# WEALTH — Architecture Document

> Version: 1.0.0 | Epoch: 2026-04-14 | Sealed by: ariffazil

---

## 000 INIT — System Declaration

WEALTH is a **sovereign financial intelligence OS** built on arifOS. It is not a CRUD app. It is a governance machine with physics-first epistemics.

**Core constraint:** Every operation passes through F1–F13 floors before execution. No exception.

---

## System Layers

### Layer 0 — arifOS Kernel

The lowest layer. Enforces civilization-level rules before any financial logic runs.

```
kernel/
├── floors.js          — F1–F13 enforcement engine
├── pipeline.js        — 000–999 pipeline state machine
├── telemetry.js       — JSON telemetry at every SEAL
└── seal.js            — 999 SEAL: finalize, emit, archive
```

**Pipeline states:**

| Stage | Code | Purpose |
|---|---|---|
| INIT | 000 | System boot, safety scan, epoch stamp |
| THINK | 111 | Clean reasoning, no narrative bias |
| EXPLORE | 333 | ≥3 options generated before decision |
| HEART | 555 | Peace ≥ 1.0 check + Maruah check |
| REASON | 777 | Trade-off comparison, F7 uncertainty band |
| AUDIT | 888 | Holds flagged, uncertainty declared |
| SEAL | 999 | Telemetry emitted, epoch stamped |

**888 HOLD triggers:**
- Net worth delta > -20% in a single session
- Debt-to-asset ratio crosses red band
- Maruah Score drops below floor
- Any marked-irreversible action
- Human override of F13 requested

---

### Layer 1 — Data (Local-First)

```
data/
├── schema.json          — Master schema (versioned)
├── sample-state.json    — Demo / onboarding state
└── migrations/          — Schema evolution log
```

**Design principles:**
- Local-first: data stays on device by default (F8 — law & safety)
- No cloud sync in Phase 1
- All records carry epistemic tag: CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE | UNKNOWN
- Soft delete only (F1 — reversible)
- UUID-keyed, append-only ledger for financial events

**Schema (canonical):**

```json
{
  "_schema_version": "1.0.0",
  "_epoch": "ISO8601",
  "identity": {
    "id": "uuid",
    "name": "string",
    "currency_base": "MYR",
    "maruah_floor": 0.6
  },
  "assets": [
    {
      "id": "uuid",
      "name": "string",
      "category": "liquid|fixed|digital|equity|property|other",
      "value": 0.0,
      "tag": "CLAIM|ESTIMATE",
      "last_updated": "ISO8601",
      "deleted": false
    }
  ],
  "liabilities": [
    {
      "id": "uuid",
      "name": "string",
      "category": "mortgage|personal|business|other",
      "principal": 0.0,
      "interest_rate": 0.0,
      "monthly_payment": 0.0,
      "tag": "CLAIM",
      "deleted": false
    }
  ],
  "cashflow": {
    "income": [],
    "expenses": [],
    "runway_months": null
  },
  "goals": [],
  "maruah_score": {
    "current": 0.0,
    "history": [],
    "floor": 0.6
  },
  "telemetry_log": []
}
```

---

### Layer 2 — Wealth Domain Modules

```
wealth/
├── networth.js        — Core: Assets − Liabilities
├── cashflow.js        — Income, Expense, Runway
├── goals.js           — Goal lifecycle management
├── risk.js            — Risk band classification
├── maruah-score.js    — Dignity integrity engine
└── projection.js      — ESTIMATE-tagged projections
```

#### `networth.js`
- Computes: `Σ(assets) − Σ(liabilities)`
- Tags output: CLAIM if all inputs are CLAIM; degrades to ESTIMATE if any input is ESTIMATE
- Emits delta alerts if drop > threshold
- 888 HOLD if delta > -20% session change

#### `cashflow.js`
- Monthly income streams (tagged per source reliability)
- Expense categorisation: fixed | variable | discretionary | emergency
- Runway = liquid_assets / monthly_burn
- F9 Anti-Hantu: flags unresolved / phantom transactions

#### `goals.js`
- Goal states: DRAFT → ACTIVE → PAUSED → 888-HELD → COMPLETED | ABANDONED
- Milestone tracking with epistemic tags on projections
- ABANDONED requires 888 HOLD + human confirmation

#### `risk.js`
- Risk bands: GREEN (0–0.3) | AMBER (0.3–0.6) | RED (0.6+)
- F7: All projections carry uncertainty band 0.03–0.15 minimum
- Debt-to-asset ratio, concentration risk, liquidity ratio

#### `maruah-score.js`
- Composite score: financial_integrity + sovereignty + community_contribution
- Range: 0.0 – 1.0
- Floor: 0.6 (configurable, never below 0.0)
- Feeds into risk assessment and goal prioritisation
- F6: ASEAN/MY context — includes zakat-alignment, amanah index

#### `projection.js`
- Compound growth: `FV = PV × (1 + r)^n`
- Always emits ESTIMATE tag
- Always shows uncertainty band: `[low_estimate, mid, high_estimate]`
- Never presents single-point futures as CLAIM

---

### Layer 3 — UI Dashboard

```
ui/
├── dashboard.html     — Single-page WEALTH OS
├── style.css          — Nexus Design System tokens
└── app.js             — Reactive UI logic
```

**Design system:** Nexus (warm beige surfaces, Hydra Teal accent, dark/light mode)

**KPI Panel (primary viewport):**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Net Worth   │  Monthly     │  Runway      │  Maruah      │
│  [CLAIM]     │  Delta       │  X months    │  Score       │
│  RM XXX,XXX  │  [ESTIMATE]  │  [PLAUSIBLE] │  0.XX / 1.0  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Charts:**
- Net worth trend (12-month)
- Cashflow waterfall
- Asset allocation donut
- Goal progress bars
- Maruah score history

**888 HOLD Banner:** Full-width, non-dismissable, warm amber. Requires explicit human action.

---

## Branch Strategy

| Branch | Purpose | Merge Gate |
|---|---|---|
| `main` | Stable sealed builds | 999 SEAL required |
| `dev` | Active development | PR + floor checks |
| `feat/*` | Feature development | PR to `dev` |
| `audit/*` | F13 human veto review | Human sign-off required |
| `888-hold/*` | Irreversible change review | 888 cleared + human confirm |

---

## GitHub Labels

| Label | Purpose |
|---|---|
| `F1-reversible` | Reversibility check required |
| `F13-veto` | Human veto triggered |
| `888-hold` | Irreversible action flagged |
| `domain:networth` | Net worth module |
| `domain:cashflow` | Cashflow module |
| `domain:goals` | Goals module |
| `domain:risk` | Risk module |
| `domain:maruah` | Maruah score module |
| `epistemic:claim` | High-confidence data |
| `epistemic:estimate` | Projection / rough data |
| `epistemic:unknown` | Data gap |
| `pipeline:888` | Audit hold |
| `pipeline:999` | Seal ready |

---

## Security & Privacy

- F8 active: financial data is device-local by default
- No telemetry to external servers without explicit consent
- No third-party financial data aggregation in Phase 1
- All API keys (if any) managed via `ENV_POLICY.md`
- 888 HOLD on any action that touches external systems

---

## Telemetry Schema

```json
{
  "epoch": "2026-04-14T02:30:00+08:00",
  "dS": 0.0,
  "peace2": 1.0,
  "kappa_r": 0.05,
  "shadow": false,
  "confidence": 0.92,
  "psi_le": 0.0,
  "verdict": "SEALED",
  "witness": {
    "human": true,
    "ai": true,
    "earth": true
  },
  "qdf": "WEALTH:v1.0.0"
}
```

---

*WEALTH Architecture v1.0.0 — Forged 2026-04-14*

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
