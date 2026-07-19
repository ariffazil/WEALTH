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

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
**Part of the arifOS Federation. See `/root/AAA/docs/FEDERATION_MAP.md` for canonical topology.**
