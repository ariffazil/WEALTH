# TODO — WEALTH Capital Engine

> **Last Updated:** 2026-05-10  
> **Session:** Governance Attestation + Cross-Organ Coupling  
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ Completed This Session

- [x] **arifOS embodiment contracts** deployed — WEALTH tools now respect lane/tier gating at kernel level
- [x] **Model registry** fixed — `gpt-5.5-thinking` resolves correctly for governance attestation

---

## 🔴 P0 — Critical (Before Next Session)

### C4 Security Debt — Supabase Key Exposure
- [ ] **Rotate WEALTH Supabase key** — current key is in git history
- [ ] **Purge from git history** — `git filter-repo` or BFG on `internal/monolith.py` history
- [ ] **Verify no other secrets** — run `truffleHog` + `detect-secrets` across full history
- [ ] **Update `.env.example`** with rotated key placeholder

**Blocked by:** Sovereign approval for history rewrite (F01 AMANAH).

### Dual Runtime Consolidation
WEALTH currently maintains **both Python and Node.js kernels**. This creates divergence risk.

- [ ] **Audit feature parity** — which tools exist only in Python vs only in Node
- [ ] **Migration plan** — canonical kernel should be Python (FastMCP 3.2)
- [ ] **Deprecate Node kernel** — or freeze it with clear "legacy" labels
- [ ] **Unified test suite** — single pytest runner covering all 48 tools

---

## 🟠 P1 — High (Next 7 Days)

### Thermodynamic Capital Accounting (H1.1)
Extend the 7 capital types to include **exergy** and **negentropy**.

- [ ] **ExergyValuation schema** — `exergy_kwh`, `exergy_efficiency`, `carbon_intensity`, `depletion_rate`
- [ ] **NegentropyValuation schema** — `negentropy_bits`, `institutional_resilience`, `knowledge_preservation`
- [ ] **Integrate into `wealth_future_steward`** — every asset gets thermodynamic footprint
- [ ] **arifOS floor coupling** — reject outputs where exergy cost exceeds constitutional bounds

### Cross-Scale Stress Testing (H1.2)
Automated catastrophe scenarios cascading `personal → agentic → institutional` in <60s.

- [ ] **Flash crash scenario** — markets drop 40% in 60s
- [ ] **Opportunity cost cascade** — wrong personal decision → agentic failure → institutional stress
- [ ] **Constitutional stress** — does F5 PEACE hold when financial survival at stake?
- [ ] **Makcik² default** — relational credit network collapse simulation

---

## 🟡 P2 — Medium (Next 30 Days)

### WEALTH ↔ GEOX Coupling (H1.3)
Price ecological damage in real time.

- [ ] **PlanetaryBoundaryInput schema** — seismic_risk_index, groundwater_depletion, soil_erosion, carbon_storage_delta
- [ ] **Ecological damage pricing** — MYR/year per boundary exceeded
- [ ] **Alert thresholds** — warning at 0.8, critical at 1.0
- [ ] **Hourly MCP loop** — GEOX feeds → WEALTH prices → arifOS alerts

### Makcik² Relational Credit GA
- [ ] **VAULT999 audit trail** — every credit decision logged immutably
- [ ] **Full test coverage** — adversarial tests for gaming/collusion
- [ ] **Documentation** — operator guide for Makcik² scoring

---

## 🟢 P3 — Backlog (H2 2026)

### Emotional/Social Capital Quantification
- [ ] **Emotional capital metric** — wellbeing, trust as quantified dimensions
- [ ] **Social capital decay** — model how trust networks degrade over time

### Cross-Institutional Capital Flow
- [ ] **Track flows across institutional boundaries** with constitutional compliance at each handoff
- [ ] **Compliance verification** — arifOS 888_JUDGE stamps each transfer

---

## Dependency Chain

```
[C4 Security Debt] ──► [Dual Runtime Consolidation]
         │
         └──────► [Thermodynamic Capital] ──► [Stress Testing]
                          │
                          └──────► [WEALTH↔GEOX Coupling]
```

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**
