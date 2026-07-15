# WEALTH Tool × Mode Map

> **Public MCP tools = 12** (SOT: live `tools/list`).  
> **Modes ≠ tools.** Counting modes as tools produced the false “50” figure.  
> **Entry:** `server_federated.py` → `wealth_mcp/` · **License:** AGPL-3.0  
> **Epoch:** 2026-07-15 · F13 sealed HOLD-02

## The 12 registered tools

| # | Tool | Kind | Modes (capability surface) |
|---|------|------|----------------------------|
| 1 | `capital_primitive` | Deductive math | `npv` · `irr` · `emv` · `evoi` · `mc` · `kelly` · `markowitz` · `robust` · `chance_constrained` · `two_stage` |
| 2 | `capital_health` | Deductive health | `conservation` · `flow` · `runway` · `survival` · `fiscal_breakeven` · `confluence` · `asymmetry` |
| 3 | `capital_diagnose` | Abductive institutional | `stress_index` · `governance_capacity` · `cascade_model` · `exploitation_detect` · `collapse_signature` · `beautiful_mouse` · `capture_scan` · `power_audit` · `bid_surface` · `optimize_mwc` · `cadence_monitor` · `crisis_reflex` |
| 4 | `capital_wisdom` | Abductive wisdom | `wisdom` · `omni` · `epistemic` |
| 5 | `capital_market` | Observational market | `fx` · `commodity` · `indicator` · `stock` |
| 6 | `capital_ledger` | Ledger | `query` · `write` (write still advisory / gated) |
| 7 | `capital_registry` | Meta | `status` · `schema` · `domains` · `health` |
| 8 | `capital_entropy` | Entropy mesh | `power_consequence_map` · `metric_purpose_audit` · `responsibility_ledger` · `trust_capital_decay` · `coercive_order_cost` · `entropy_externality` |
| 9 | `wealth_institutional_stress_index` | Institutional | — (single purpose) |
| 10 | `wealth_cascade_model` | Institutional | — |
| 11 | `wealth_governance_capacity` | Institutional | — |
| 12 | `wealth_external_exploitation_detect` | Institutional | — |

## How to call (agents)

```text
# EMV (old world: wealth_compute_emv)
capital_primitive(mode="emv", outcomes=[...], probabilities=[...])

# Kelly (old world: wealth_stock_analysis mode kelly)
capital_primitive(mode="kelly", win_prob=..., odds=...)

# Runway
capital_health(mode="runway", liquid_assets=..., monthly_burn=...)
```

## What is NOT a tool count

| Legacy claim | Reality |
|--------------|---------|
| “50 public tools” | Modes + aliases + monolith names miscounted |
| `contracts/archive/tools.yaml.monolith-legacy-*` | Historical catalog only |
| Monolith `wealth_*` names | Compatibility / legacy — not public federated SOT |

## Registry files

| File | Role |
|------|------|
| `contracts/tools.yaml` | **Live** 12-tool SOT |
| `contracts/archive/tools.yaml.monolith-legacy-2026-05-19` | LEGACY |
| `docs/TOOL_MODE_MAP.md` | This map |

**DITEMPA BUKAN DIBERI** — capability preserved; surface entropy reduced.
