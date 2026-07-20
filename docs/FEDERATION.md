# FEDERATION.md — WEALTH

```yaml
role: DOMAIN
organ: wealth
layer: L3
citizenship: warga-aaa
canon: ariffazil/ariffazil

depends_on:
  - repo: ariffazil/arifOS
    reason: Evidence routing, governance gates, constitutional compliance

mcp:
  port: 18082
  endpoint: https://wealth.arif-fazil.com/mcp
  tools_count: 20+
  tool_prefix: capital_
  public_tools:
    - capital_primitive (npv, irr, emv, evoi, mc, kelly, markowitz, robust)
    - capital_health (conservation, flow, runway, survival, fiscal_breakeven)
    - capital_diagnose (stress_index, governance_capacity, cascade_model)
    - capital_market (fx, commodity, indicator, stock, gold, oil, gas)
    - capital_wisdom (wisdom, omni, epistemic)
    - capital_entropy
    - capital_ledger
    - capital_registry

governance:
  judge: arifOS
  seal: VAULT999
  floors: F1-F13
  mutation_rule: NEVER mutate. Compute only. arifOS judges; A-FORGE executes.

stack_role: |
  WEALTH is the capital intelligence organ — L3 DOMAIN.
  It computes financial evidence: NPV, IRR, EMV, Monte Carlo, portfolio
  optimization, market data, institutional stress analysis.
  It computes, never allocates. It advises, never decides.
  All evidence flows through arifOS governance gates before any action.

entrypoints:
  - MCP: https://wealth.arif-fazil.com/mcp
  - Health: http://localhost:18082/health
  - Code: https://github.com/ariffazil/wealth
```

---

## Cross-Organ Federation Links

| Organ | Role | Connection |
|-------|------|------------|
| **arifOS** (:8088) | Constitutional Kernel | Routes WEALTH evidence via `wealth_arifos_bridge/judge_handoff.py`. All irreversible decisions gated by `arif_judge`. |
| **AAA** (:3001) | Control Plane / A2A Gateway | Federation topology, agent routing, cockpit visibility. WEALTH registers tools via `tools/list` for AAA discovery. |
| **A-FORGE** (:7071) | Execution Shell | Receives SEAL'd judge envelopes for capital execution. WEALTH never self-executes — only computes evidence. |
| **GEOX** (:8081) | Earth Intelligence | Receives prospect economics via `geox_to_wealth_bridge` — POS, NPV, risk inputs. |
| **WELL** (:18083) | Human Readiness | Livelihood handoff — capital readiness requires human readiness. |
| **VAULT999** | Immutable Ledger | All SEAL'd capital decisions anchored to VAULT999 hash chain. |

### Data Flow

```
WEALTH (compute) → arif_judge (verdict) → A-FORGE (execute) → VAULT999 (seal)
     ↑                                                    ↑
  GEOX (prospect)                                    WELL (readiness)
```

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
**Part of the arifOS Federation. See [`/root/AAA/docs/FEDERATION_MAP.md`](../../AAA/docs/FEDERATION_MAP.md) for canonical topology.**
