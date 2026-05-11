# TODO — WEALTH Capital Engine

> **Roadmap:** ARIFOS_NEXT_HORIZON_2026  
> **Execution Status:** HOLD until contracts frozen  
> **Last Updated:** 2026-05-10  
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ Embodiment Attestation (Completed Earlier Today)

- [x] arifOS embodiment contracts deployed
- [x] Model registry fix

---

## 🔴 P0 — Horizon 0: Canon Lock (Days 0–14)

**Gate: No new features until contracts are frozen.**

### Authority Freeze
- [ ] **Create `REPO_AUTHORITY_MATRIX.md`** — what WEALTH may own / must not own
- [ ] **Tool inventory** — 48 tools, verify no overlap with other repos
- [ ] **Schema inventory** — map all valuation schemas
- [ ] **Dual runtime decision** — Python vs Node.js canonical kernel

### C4 Security Debt
- [ ] **Rotate Supabase key** — current key exposed in git history
- [ ] **Purge from git history** — `git filter-repo` or BFG
- [ ] **Audit with detect-secrets + truffleHog**

---

## 🟠 P1 — Horizon 1: Security + Session Spine (Days 15–45)

**Gate: Every model output has assumptions. Every recommendation is advisory.**

### Evidence Schemas
- [ ] **Create `/schemas/capital_evidence.schema.json`** — structured capital evidence object
- [ ] **Create `/schemas/emv.schema.json`** — expected monetary value schema
- [ ] **Create `/schemas/risk_exposure.schema.json`** — risk exposure schema
- [ ] **Assumption inventory** — every model output declares assumptions explicitly
- [ ] **Advisory labeling** — every capital recommendation labeled "advisory — requires arifOS SEAL"

---

## 🟡 P2 — Horizon 2: Deterministic Judge (Days 46–90)

**Gate: High-impact financial actions return HOLD unless arifOS SEAL + F13 approval exist.**

### Models + Ontology
- [ ] **Create `/ontology/fibo_map.yaml`** — FIBO-compatible concept map
- [ ] **`/models/npv.py`** — with explicit assumptions
- [ ] **`/models/irr.py`** — with explicit assumptions
- [ ] **`/models/emv.py`** — with explicit assumptions
- [ ] **`/models/downside.py`** — with explicit assumptions
- [ ] **Valuation golden cases** — `/tests/valuation_golden_cases.py`

### Constitutional Enforcement
- [ ] **High-impact HOLD gate** — >MYR 10k or >1 stakeholder requires arifOS SEAL
- [ ] **F13 approval gate** — irreversible capital actions require human ack

---

## 🟢 P3 — Horizon 3: Semantic Federation (Days 91–135)

**Gate: GEOX uncertainty produces WEALTH risk witness without manual prompt glue.**

### GEOX → WEALTH Bridge
- [ ] **Define bridge contract** — GEOX evidence maps to WEALTH evidence
- [ ] **`capital_evidence.schema.json`** — export format for cross-domain use
- [ ] **FIBO mapping v1** — semantic concept alignment
- [ ] **First cross-domain demo** — real subsurface uncertainty → capital risk witness

### Cross-Domain Pipeline
- [ ] GEOX detects subsurface uncertainty
- [ ] arifOS requests evidence
- [ ] WEALTH calculates EMV / downside / option value
- [ ] arifOS judges
- [ ] A-FORGE executes report generation only
- [ ] VAULT999 seals trace

---

## 🔵 P4 — Horizon 4: Self-Healing + Release (Days 136–180)

**Gate: Capital risk affects execution permission.**

- [ ] **Causal template integration** — WEALTH → A-FORGE capital risk affects execution permission
- [ ] **Thermodynamic capital accounting** — exergy + negentropy capital types
- [ ] **Cross-scale stress testing** — personal → agentic → institutional cascade
- [ ] **Public docs cleanup**
- [ ] **Release tag `vNext-Horizon-0`**

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**
