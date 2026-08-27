---
name: wealth-mcp-architecture
version: 1.0.0
description: "WEALTH MCP architecture — split monolith, test, harden."
owner: HERMES
risk_tier: T1
floor_scope: [F1, F2, F4]
autonomy_tier: T1
ecology_state: WARM
---

# WEALTH MCP Architecture Patterns

> Lessons from WEALTH MCP P0 hardening (2026-08-28).

## Monolithic to Per-Tool Split

**Trigger:** Single tool file >500 lines or holds 3+ tools.

**Target:**
```
wealth_mcp/tools/
├── __init__.py          # imports all register_* functions
├── types.py             # shared CoercedList, CoercedDict, validators
├── primitive.py         # register_primitive(mcp) → capital_primitive
├── health.py            # register_health(mcp) → capital_health
├── market.py            # register_market(mcp) → capital_market
├── diagnose.py          # register_diagnose(mcp) → capital_diagnose
├── ledger.py            # register_ledger(mcp) → capital_ledger
├── registry.py          # register_registry(mcp) → capital_registry
├── entropy.py           # register_entropy(mcp) → capital_entropy
├── judge_handoff.py     # register_judge_handoff(mcp)
├── indicator.py         # register_indicator(mcp)
├── backtest.py          # register_backtest(mcp)
└── entry_plan.py        # register_entry_plan(mcp)
```

**Recipe:**
1. Extract shared types to `types.py` (CoercedList, _coerce_json_string, etc.)
2. One file per tool: `def register_<name>(mcp)` with `@mcp.tool(name=...)` inside
3. `canonical.py` becomes thin orchestrator importing and calling all register functions
4. Verify: `python3 -c 'from wealth_mcp.server import create_mcp_server; s = create_mcp_server(); print(len(s._tool_manager._tools), "tools")'`

**Pitfalls:**
- `_call_legacy_tool` defined in canonical.py — move to shared utils or inline direct imports
- Lazy imports (inside function body) stay lazy — only shared types centralize
- Receipt emission logic — extract to `receipt.py` if shared across tools
- Test imports from `wealth_mcp.tools.canonical` break — update or keep re-export

## Resilience Hardening

**http_retry.py pattern** — shared retry wrapper for all external API calls:
```python
async def fetch_with_retry(url, max_retries=3, timeout=10.0, **kwargs):
    # exponential backoff: 1s, 2s, 4s
    # returns dict with status/error on failure
    # logs retries to stderr
```

Apply to: `engines/commodity/*/fetch_*.py`, `engines/crypto/*/fetch_*.py`, `wealth_core/commodity_engines.py`, `wealth_core/ingest/crypto/router.py`

## Test Coverage Map

| Tool | Test File | Status |
|------|-----------|--------|
| capital_primitive | test_smoke.py | EXISTING |
| capital_health | test_conservation.py, test_flow.py | EXISTING |
| capital_diagnose | test_capital_entropy_bugfixes.py | PARTIAL |
| capital_market | test_market_data.py, test_step9_canonical_e2e.py | EXISTING |
| capital_ledger | test_vault_supabase_sync.py | EXISTING |
| capital_registry | test_organ_governance.py | EXISTING |
| capital_entropy | test_entropy.py, test_capital_entropy_bugfixes.py | EXISTING |
| wealth_judge_handoff | test_session_contract.py | EXISTING |
| capital_indicator | test_capital_indicator.py | NEW |
| capital_backtest | test_capital_backtest.py | NEW |
| capital_entry_plan | test_capital_entry_plan.py | NEW |

## Tool Families (current)

- **Deductive math:** capital_primitive (11 modes: npv, irr, emv, evoi, mc, kelly, markowitz, robust, chance_constrained, two_stage, reward_design)
- **Financial health:** capital_health (6 modes: conservation, flow, runway, survival, indicators, cross_validate)
- **Institutional diagnostics:** capital_diagnose (15 modes: stress_index, cascade, governance, exploitation, power_*, collapse, cadence)
- **Market data:** capital_market (8 modes: fx, commodity, indicator, stock, gold, oil, gas + crypto via asset_class)
- **Ledger:** capital_ledger (query, write — write requires F13 ack_irreversible)
- **Meta:** capital_registry (status, schema, domains, health)
- **Entropy:** capital_entropy (optional, returns UNAVAILABLE when dependency absent)
- **Handoff:** wealth_judge_handoff (arifOS governance bridge)
- **Indicators:** capital_indicator (rsi, macd, bollinger, sma, ema, atr, stochastic, ichimoku, vwap, obv, adx)
- **Backtest:** capital_backtest (strategy validation)
- **Entry plan:** capital_entry_plan (support/resistance, position sizing, risk:reward)
