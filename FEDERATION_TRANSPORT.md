# WEALTH Federation Transport Layer

> **DITED:** `WEALTH/docs/FEDERATION_TRANSPORT.md`
> **Version:** 2026.06.27
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## What This Is

The WEALTH Federation Transport Layer governs how intelligence objects move between arifOS organs — GEOX → WEALTH → arifOS.

It is **not** a new protocol. It is a discipline layer above MCP that enforces:
1. Every cross-organ handoff uses typed artifacts, not prose
2. Every artifact carries epistemic grades and provenance
3. Every terminal decision emits a replay receipt
4. Every handoff is governed by arifOS, not WEALTH

---

## Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│ MCP NATIVE LAYER (wealth_mcp/server.py)                     │
│                                                             │
│  tools    = computation                                     │
│  resources = reality context                                │
│  prompts  = disciplined workflow                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ Every output above TIER_1
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ WEALTH FEDERATION TRANSPORT LAYER                           │
│                                                             │
│  federation envelope  = transport wrapper                    │
│  context capsule     = portable working state               │
│  domain translation card = typed cross-domain transform     │
│  affordance contract  = tool/prompt safe-use policy         │
│  replay receipt      = immutable decision audit             │
└──────────────────────┬──────────────────────────────────────┘
                       │ WEALTH → arifOS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ arifOS CONSTITUTIONAL KERNEL (:8088)                        │
│                                                             │
│  arif_judge  = verdict on capability request                 │
│  arif_seal   = immutable record                             │
│  VAULT999    = append-only ledger                           │
└─────────────────────────────────────────────────────────────┘
```

**Do not confuse the two layers.**
- MCP transports primitives.
- WEALTH Federation Transport Layer moves governed intelligence objects.

---

## Five Contract Schemas

| Schema | URI | Purpose |
|--------|-----|---------|
| Federation Envelope | `wealth://contracts/federation-envelope.schema.json` | Transport wrapper for all cross-organ handoffs |
| Context Capsule | `wealth://contracts/context-capsule.schema.json` | Portable working state |
| Affordance Contract | `wealth://contracts/affordance-contract.schema.json` | Tool/prompt safe-use policy |
| Replay Receipt | `wealth://contracts/replay-receipt.schema.json` | Immutable decision audit |
| Domain Translation Card | `wealth://contracts/domain-translation-card.schema.json` | Typed cross-domain transform |

---

## Cross-Organ Handoff Flows

### GEOX → WEALTH

```
GEOX emits:
  - context_capsule (geological evidence)
  - domain_translation_card (geox-to-wealth)

WEALTH receives:
  - Typed capsule with facts, assumptions, unknowns, constraints
  - Translation card maps seismic confidence → discount rate adjustment
  - Translation card maps POS → p_technical_success for EMV

WEALTH never receives prose geological narratives as capital inputs.
```

### WEALTH → arifOS

```
WEALTH emits:
  - allocation_memo (advisory synthesis)
  - replay_receipt (audit trail)
  - federation_envelope (transport wrapper)

arifOS receives:
  - Governed decision package (not a directive)
  - Verdict is arifOS's job, not WEALTH's

WEALTH never tells Arif what to decide.
WEALTH tells Arif what the capital looks like.
```

### WELL → WEALTH

```
WELL emits:
  - readiness signals (cognitive_clarity, stress_load, fatigue)

WEALTH receives:
  - WELL readiness affects decision quality ceiling
  - Allocation memo complexity is capped by WELL signal
  - 888_HOLD triggered by chronic_fatigue flag

WELL never authorizes WEALTH computation.
WELL reflects substrate. WEALTH computes. arifOS adjudicates. Arif decides.
```

---

## Transport Rules

1. **No free-form text between organs.** Only typed artifacts.
2. **Every envelope carries `trace_id`.** The trace links every step.
3. **Every terminal decision emits a `replay_receipt`.** Appended to `VAULT999/wealth/receipts.jsonl`.
4. **Every domain boundary uses a `domain_translation_card`.** The translation is explicit, versioned, auditable.
5. **WEALTH never bypasses arifOS judgment for TIER_3 actions.** Irreversible = 888_HOLD.
6. **Every artifact carries epistemic grade (OBS/DER/INT/SPEC).** No unmarked conclusions.

---

## Evidence Adapters (Read-Only)

All external data enters WEALTH through typed evidence adapters:

| Source Class | Examples | Freshness TTL |
|---|---|---|
| P1 Malaysia/ASEAN | BNM OpenAPI, Bursa, DOSM, ST/MEIH, PETRONAS | 300s (market) / 3600s (macro) |
| P2 Global | IMF, World Bank, FRED, EIA | 3600s |
| P3 US/EU-specific | SEC EDGAR | 86400s |

**Rule:** No mutation, no trading, no write-capable actions in any adapter.

---

## Typed Handoff: GEOX Prospect → WEALTH Capital

```
Input to WEALTH:
  capsule_id: caps-geox-prospect-north-sabah-001
  facts:
    - claim: "POS = 35%"
      grade: INT
      support: geox://prospect/POS_summary
    - claim: "2C resource 180 MMbbl"
      grade: DER
      support: geox://petrophysics/2c_resource
  assumptions:
    - Porosity 18%, Sw 35% from analog
    - Recovery factor 30% from Sabah clastic analog
  constraints:
    - Sabah PSC: 38% royalty, 38% PTP
    - DOE EIA: 18-month approval timeline
    - Water depth 80m: jack-up required

Translation card applied: dtc-geox-wealth-prospect-v1

WEALTH output:
  evoi: +USD 8.4M (DER, ceiling 0.85)
  emv: +USD 12.3M base case (DER)
  monte_carlo_p95: +USD 68.4M
  monte_carlo_p5: -USD 22.1M
  fiscal_breakeven: USD 72/bbl (DER)
  888_hold_required: TRUE (drilling irreversible)

arifOS envelope:
  intent: Authorize North Sabah appraisal well
  blast_radius: ORGAN
  reversibility: NONE
  epistemic_state: DER
```

---

## Repository Structure

```
WEALTH/
├── contracts/
│   ├── federation-envelope.schema.json
│   ├── affordance-contract.schema.json
│   ├── context-capsule.schema.json
│   ├── replay-receipt.schema.json
│   └── domain-translation-card.schema.json
├── wealth_mcp/
│   ├── prompts/
│   │   ├── wealth_intake.md
│   │   ├── wealth_capital_diagnosis.md
│   │   ├── wealth_risk_downside.md
│   │   ├── wealth_market_reality.md
│   │   ├── wealth_allocation_judgment.md
│   │   ├── wealth_institutional_power.md
│   │   └── wealth_arifos_handoff.md
│   └── resources/
│       ├── sot/manifest.schema.json
│       ├── registry/tools.schema.json
│       ├── registry/prompts.schema.json
│       ├── sources/catalog.json
│       ├── policy/epistemic-ladder.md
│       ├── policy/action-boundaries.md
│       ├── translation/geox-to-wealth/prospect.json
│       ├── translation/well-to-wealth/readiness.json
│       ├── translation/wealth-to-arifos/allocation.json
│       ├── translation/geox-to-well/field-risk.json
│       └── examples/
│           ├── geox-to-wealth.json
│           └── wealth-to-arifos.json
├── FEDERATION_TRANSPORT.md
└── SECURITY_MINIMAL.md
```
