# WEALTH Tool × Mode Map

> **Public MCP tools = 8** (SOT: live `tools/list`).
> **Modes ≠ tools.** Counting modes or internal aliases as tools produces false counts.
> **Entry:** `server_federated.py` → `wealth_mcp/` · **License:** AGPL-3.0
> **Epoch:** 2026-08-03

## The 8 registered tools

| # | Tool | Kind | Modes (capability surface) |
|---|------|------|----------------------------|
| 1 | `capital_primitive` | Deductive math | `npv` · `irr` · `emv` · `evoi` · `mc` · `kelly` · `markowitz` · `robust` · `chance_constrained` · `two_stage` |
| 2 | `capital_health` | Deductive health | `conservation` · `flow` · `runway` · `survival` · `fiscal_breakeven` · `confluence` · `asymmetry` |
| 3 | `capital_diagnose` | Abductive institutional | `stress_index` · `governance_capacity` · `cascade_model` · `exploitation_detect` · `collapse_signature` · `beautiful_mouse` · `capture_scan` · `power_audit` · `bid_surface` · `optimize_mwc` · `cadence_monitor` · `crisis_reflex` |
| 4 | `capital_market` | Observational market | `fx` · `commodity` · `indicator` · `stock` · `gold` · `oil` · `gas` · **`crypto`*** |
| 5 | `capital_ledger` | Ledger | `query` · `write` (write is C2/IRREVERSIBLE and gated) |
| 6 | `capital_registry` | Meta | `status` · `schema` · `domains` · `health` |
| 7 | `capital_entropy` | Entropy mesh | `power_consequence_map` · `metric_purpose_audit` · `responsibility_ledger` · `trust_capital_decay` · `coercive_order_cost` · `entropy_externality` |
| 8 | `wealth_judge_handoff` | Governance handoff | `prepare` · `submit` |

`capital_wisdom` and the former `wealth_institutional_*` names are not public
MCP tools. Internal direct-import compatibility paths are not counted here.

## Surface extensions since 2026-08-03

| Date | Surface delta | Notes |
|------|---------------|-------|
| 2026-08-18 | `capital_market(asset_class="crypto"*, stock_payload={"asset":"BTC","kind":"spot_price"})` | Step 9 of `/root/WEALTH/docs/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md`. Wires the existing `crypto_router` substrate (CoinGecko, Binance public REST, DefiLlama) to the canonical `capital_market` tool. NO new tool created — `asset_class` parameter is additive, defaults to `"fx_commodity"` so existing callers are unaffected. F2/F11 envelopes carry `crypto_router:<provider>` source attribution and the substrate's `response_hash`. |

\* `crypto` is reachable through two discriminators on `capital_market`:
- (a) legacy `mode` discriminator — `mode="crypto"` triggers the crypto branch directly (back-compat for any caller that already passed `mode="crypto"` in payloads).
- (b) new `asset_class: str` parameter — `asset_class="crypto"` triggers the crypto branch regardless of `mode`, with `mode` then interpreted as the data kind (`spot_price`/`24h_change`/`depth_top20`/`tvl`).
Default `asset_class="fx_commodity"` preserves all existing call signatures; the canonical surface stays at 8 tools (no federation expansion).

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
| `contracts/archive/tools.yaml.monolith-legacy-2026-05-19` | Historical catalog only |
| Monolith `wealth_*` names | Compatibility / legacy — not public federated SOT |
| `capital_wisdom` and institutional shadow names | Internal or historical only; absent from `tools/list` |

## Registry files

| File | Role |
|------|------|
| `contracts/tools.yaml` | **Live** 8-tool SOT |
| `contracts/archive/tools.yaml.monolith-legacy-2026-05-19` | LEGACY |
| `docs/TOOL_MODE_MAP.md` | This map |

**DITEMPA BUKAN DIBERI** — capability preserved; surface entropy reduced.
