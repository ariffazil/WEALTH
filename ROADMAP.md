# WEALTH — Roadmap H1–H4

**Version:** v2026.05.10  
**Organ:** WEALTH (Capital · Ω Node)  
**Maturity:** PRODUCTION (155 commits, 48 tools)  
**Role:** Capital intelligence coprocessor — NPV, EMV, crisis triage, Makcik² relational credit  
**Status:** SEALED — pending APEX ratification — **EMBODIMENT-AWARE CAPITAL**

---

## Executive Summary

WEALTH is the capital intelligence coprocessor of the arifOS federation — the Ω node for economic and financial evidence. As of 2026-05-10, WEALTH benefits from kernel-level tool embodiment contracts and model registry fixes. The highest-priority risks are **C4 security debt** (Supabase key in git history, unrotated secrets) and **dual runtime consolidation** (Python + Node.js kernels).

**WEALTH responsibilities by horizon:**

| Horizon | Theme | WEALTH Milestones |
|---------|-------|------------------|
| **H1** (Q2–Q3 2026) | Substrate Hardening | Exergy/negentropy capital, stress testing, **security debt** |
| **H2** (Q4 2026–Q1 2027) | Recursive Governance | WEALTH ↔ GEOX coupling, Makcik² GA |
| **H3** (Q2–Q3 2027) | AGI-Scale Runtime | Real-time planetary boundary monitoring |
| **H4** (Q4 2027+) | Foundational Substrate | Cross-federation capital standard |

---

## What Changed (2026-05-10)

### ✅ Deployed
- **arifOS embodiment contracts** — WEALTH tools now respect lane/tier gating at kernel + REST levels
- **Model registry fix** — `gpt-5.5-thinking` resolves correctly for governance attestation

### 🔄 Active Frontier
- C4 security debt (Supabase key rotation, history purge)
- Dual runtime consolidation (Python vs Node.js canonical kernel)
- Thermodynamic capital accounting schema

---

## H1: Substrate Hardening (Q2–Q3 2026)

### H1.0 — C4 Security Debt (P0)

**WEALTH Supabase key in git history** — must be rotated and purged before any other H1 work.

**Action items:**
- Rotate Supabase key in Supabase dashboard
- Purge from git history (`git filter-repo` or BFG)
- Run `detect-secrets` + `truffleHog` across full history
- Update `.env.example` with rotated placeholder

**Blocked by:** Sovereign approval for history rewrite (F01 AMANAH).

### H1.1 — Dual Runtime Consolidation

WEALTH currently maintains **both Python and Node.js kernels**. Divergence risk is high.

**Decision needed:** Python (FastMCP 3.2) should be the canonical kernel.

**Action items:**
- Audit feature parity — which tools exist only in Python vs only in Node
- Migration plan with deprecation timeline
- Freeze Node kernel with clear "legacy" labels
- Unified test suite (single pytest runner)

### H1.2 — Thermodynamic Capital Accounting

Extend the 7 capital types to include **exergy** and **negentropy**.

```python
class CapitalType(Enum):
  FINANCIAL = "financial"
  MANUFACTURED = "manufactured"
  HUMAN = "human"
  SOCIAL = "social"
  NATURAL = "natural"
  INTELLECTUAL = "intellectual"
  CULTURAL = "cultural"
  EXERGY = "exergy"          # NEW: Useful work potential (kWh equivalent)
  NEGENTROPY = "negentropy"  # NEW: Organizational/order capital (bits equivalent)
```

**Why this matters for AGI substrate:**
A pure financial optimization will destroy natural capital and human wellbeing. Exergy and negentropy give arifOS a thermodynamic language for trade-offs that financial models cannot express.

**Owner:** WEALTH science team  
**Target:** September 2026

### H1.3 — Cross-Scale Stress Testing

Build automated catastrophe scenarios that cascade from `personal` → `agentic` scale in <60 seconds.

**Required test scenarios (H1):**
1. **Flash crash** — Capital markets drop 40% in 60 seconds
2. **Opportunity cost cascade** — Wrong personal decision → agentic failure → institutional stress
3. **Constitutional stress** — Does F5 PEACE hold when financial survival is at stake?
4. **Makcik² default** — Relational credit network collapse simulation

**Target:** All constitutional floors hold at all scales by September 2026.

**Owner:** WEALTH risk team  
**Target:** September 2026

### H1.4 — WEALTH ↔ GEOX Coupling

Price ecological damage in real time: GEOX outputs feed directly into WEALTH `wealth_future_steward`.

```python
class PlanetaryBoundaryInput:
  # From GEOX real-time sensor bridge
  seismic_risk_index: float           # 0–1
  groundwater_depletion_rate: float   # m³/year
  soil_erosion_flux: float            # tonnes/year
  carbon_storage_delta: float         # tonnes CO2/year
  
  # WEALTH processing
  ecological_damage_price: float      # MYR/year
  planetary_boundary_indicator: float # 0–1 (1 = boundary exceeded)
  
  # Alert thresholds
  boundary_warning: bool              # True if > 0.8
  boundary_exceeded: bool             # True if > 1.0
```

---

## H2: Recursive Governance (Q4 2026 – Q1 2027)

### H2.1 — Makcik² Relational Credit GA

Makcik² relational credit scoring reaches General Availability.

**Current state:** Prototype  
**Target:** GA with full VAULT999 audit trail

### H2.2 — Cross-Institutional Capital Flow

WEALTH tracks capital flows across institutional boundaries with constitutional compliance verification at each handoff.

---

## H3: AGI-Scale Runtime (Q2–Q3 2027)

### H3.1 — Real-Time Planetary Boundary Monitoring

Continuous WEALTH ↔ GEOX loop with automatic alerting when planetary boundaries are approached or exceeded.

### H3.2 — Emotional/Social Capital Quantification

Extend capital types to include emotional capital (wellbeing, trust) as quantified dimensions.

---

## H4: Foundational Substrate (Q4 2027+)

### H4.1 — Cross-Federation Capital Standard

WEALTH capital schemas adopted as the federation standard for economic evidence exchange.

---

## Dependency Chain

```
[C4 Security Debt] ──► [Dual Runtime Consolidation]
         │
         └──────► [Exergy/Negentropy Capital] ──► [Stress Testing]
                          │
                          └──────► [WEALTH↔GEOX Coupling]
                                           │
                                           ▼
                          [H3 Real-time Planetary Monitoring]
```

---

## Tool Count Note

WEALTH claims 48 tools (13 sovereign primitives × modes). This must be reconciled in the unified `MCP_ENDPOINT_REGISTRY` v2.0 (AAA ownership, June 2026).

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**

*SEALED: 2026-05-10 | WEALTH Capital Domain — Embodiment-Aware*
