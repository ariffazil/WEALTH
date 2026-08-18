# WEALTH Crypto Sensor Extension — Architecture Proposal v1

> **Status:** DRAFT (Phase 2 of 3) — awaiting arif_seal
> **Author:** A-FORGE via arifOS
> **Date:** 2026-08-18
> **License:** AGPL-3.0 (matches WEALTH)
> **Authority:** WEALTH is advisory only. Arif Fazil is final authority.

---

## 0. Scope Decision (load-bearing)

**Do not expand the 11-tool canonical surface.**

WEALTH currently exposes 11 federated canonical tools (`federated-11-canonical v2026.07.24`). Six of them live in the `sensor` dimension — already generic over asset class. Adding 4 crypto providers means **4 new sources behind existing sensors**, not 4 new tools.

| Layer | Surface | New artifacts | Cardinality |
|---|---|---|---|
| L0 Substrate | `engines/crypto/<provider>/` | adapter modules | 4 (1 per provider) |
| L1 Router | `wealth_core/ingest/crypto/router.py` | dispatch + fallback | 1 |
| L2 Sensor dimension | existing `wealth_sensor_*` tools | wiring only | 0 new tools |
| L3 Audit | VAULT999 + arif_seal pipeline | auto via existing chain | 0 |

**Net effect on canonical surface:** `+0` tools, `+4` registered sources.

---

## 1. Provider Coverage Matrix

| Provider | Asset coverage | Auth required | Free tier | Rate limit | F12 surface | F2 label |
|---|---|---|---|---|---|---|
| **CoinGecko** | Spot prices, market cap, 24h change | Optional Pro key | Yes (public endpoints work without key) | 10–30 calls/min | Hard cap + mandatory fallback | `OBS` |
| **Binance public ticker** | Price, order book depth (top 20) | None (public endpoint) | Yes | 1200 req/min | Geo-block US IPs — enforce | `OBS` |
| **DefiLlama** | DeFi TVL, token prices (oracle) | None | Yes | Lenient (~no hard cap) | None expected | `OBS` (TVL + price oracle) |
| **Arkham** | On-chain address attribution, flow | API key required | Limited trial; paid beyond | Tier-dependent (500–50k/mo) | Per-key budget, bearer rotation, **conditional on Arif provisioning key** | `OBS` w/ source-provenance badge |

Excluded for v1 (each has distinct risk profile, deferred):
- **CryptoCompare** — paid, redundant given DefiLlama oracle
- **Kaiko** — institutional tier, no free path
- **CoinMarketCap** — paid API, conflicts with F2 free-tier preference

---

## 2. Existing Patterns Reused

Pattern reuse — not new architecture:

- `engines/commodity/gold-api/fetch_gold.py + server.js` — vertical asset-class adapter template. We mirror this with `engines/crypto/<provider>/fetch_<provider>.py`.
- `wealth_core/market_data_fallback.py` — fallback chain dispatcher. The crypto router imports this pattern.
- `wealth_contracts/epistemic.py` — epistemic ladder. Crypto extension appends: spot price → `OBS`; 24h vol → `DER`; momentum signal → `SPEC`.
- `wealth_contracts/source_registry.yaml` — adapter registration. Add 4 entries with `asset_class: crypto` discriminator.
- `wealth_sensor_*` tools (6 of them) — observation dispatch surface. Wire via `asset_class="crypto"` parameter on the existing mode dispatcher.

---

## 3. New Artifacts (precise contracts)

### 3.1 L0 Substrate — `engines/crypto/<provider>/`

One directory per provider. Each adapter is a single Python module that:
- Fetches from the provider's REST endpoint
- Coerces the response into a typed `SourceBundle` (Pydantic)
- Emits an `epistemic_label` per field
- Returns a `response_hash` (sha256) for audit chain

**Canonical response contract (all 4 adapters):**

```python
class SourceBundle(BaseModel):
    provider: Literal["coingecko", "binance_public", "defillama", "arkham"]
    asset: str                    # "BTC", "ETH", "wBTC", or chain address (Arkham)
    value: float
    currency: str                 # "USD" default
    timestamp: datetime           # ISO8601, UTC
    source_uri: str               # exact endpoint hit
    epistemic_label: Literal["OBS", "DER", "INT", "SPEC", "UNKNOWN"]
    response_hash: str            # sha256(raw_response_bytes)
    extras: dict[str, Any] | None # provider-specific (24h_change, tvl_usd, etc.)
```

**Per-provider shapes:**

```
engines/crypto/
├── coingecko/fetch_coingecko.py      # GET /simple/price, /coins/markets
├── binance/fetch_binance.py          # GET /api/v3/ticker/price, /api/v3/ticker/24hr
├── defillama/fetch_defillama.py      # GET /prices/current, /tvls
└── arkham/fetch_arkham.py            # GET /addresses/{addr}/flows, /transfers
```

### 3.2 L1 Router — `wealth_core/ingest/crypto/router.py`

```python
class CryptoRouter:
    def fetch(
        self,
        asset: str,
        kind: Literal["spot_price", "24h_change", "depth_top20", "tvl", "flow"],
        priority: list[str] = ["coingecko", "defillama", "binance_public", "arkham"],
    ) -> SourceBundle:
        # priority-based dispatch
        # rate-limit budget enforcement (per-provider)
        # on 429/503/network: auto-fallback to next priority
        # on all-priority fail: emit CacheHit (last known bundle) + HOLD signal
        # emit W3 failure witness per fallback
```

Fallback chain by **kind** (not global):
- `spot_price` → CoinGecko → DefiLlama oracle → Binance public ticker
- `24h_change` → CoinGecko → Binance 24hr ticker
- `tvl` → DefiLlama only (DefiLlama is the canonical TVL source)
- `flow` → Arkham only (no fallback — explicitly HOLD if key missing/expired)

### 3.3 L2 Sensor wiring — zero new tools

Existing tools accept `asset_class` and `asset` discriminator. The mode dispatcher in `wealth_sensor_fetch` (already implemented) routes based on these. We add a branch:

```python
# In wealth_sensor_fetch mode dispatcher
if asset_class == "crypto":
    return crypto_router.fetch(asset=asset, kind=mode, priority=priority_default)
```

No tool rename, no new decorator, no canonical surface change.

### 3.4 L3 Audit — auto via existing pipeline

Every `SourceBundle` is sealed to VAULT999 via the existing `vault_write` chain (with provider, source_uri, response_hash, timestamp). No new audit code path.

---

## 4. Governance Gates Per Floor

| Floor | Mechanism | Owner / Artifact |
|---|---|---|
| **F1 AMANAH** | Read-only fetches. No wallet operations. No order placement. | Adapter contract; documented in `wealth_boundary_floors` resource |
| **F2 TRUTH** | `epistemic_label` mandatory per `SourceBundle` field. `source_uri` mandatory. | Adapter contract |
| **F3 TRI-WITNESS** | Provider agreement: 2+ providers agree on `spot_price` → WITNESS.PASS. Divergence > 0.5% → WITNESS.WEAK (flagged, not blocked). | Router emits witness; existing `wealth_measurement_schema` consumes |
| **F4 CLARITY** | 60-second price cache reduces entropy. Cache hit → `OBS w/ vintage`. | Router cache layer |
| **F5 PEACE²** | n/a (data ingestion only). | n/a |
| **F7 HUMILITY** | Confidence cap 0.95 (no crypto price is "certain"). | `wealth_measurement_schema` enforces |
| **F8 GENIUS** | `forge_evaluate` G≥0.80 gate per adapter before activation. | A-FORGE on each forge_skill. |
| **F9 ANTIHANTU** | Precise `source_uri` + `provider` fields. No "coingecko says BTC = $X" without timestamp. | Adapter contract |
| **F10 ONTOLOGY** | AI-only ontology (no AI sentience). n/a here. | n/a |
| **F11 AUDITABILITY** | Every fetch → VAULT999 with `response_hash` chain. | Auto via existing `vault_write` |
| **F12 RESILIENCE** | Rate-limit caps per provider, bearer rotation (Arkham), geo enforcement (Binance), all-priority fallback → cache → HOLD. | Router config + env vars |
| **F13 SOVEREIGN** | WEALTH is advisory only — `wealth_sensor_*` returns data, never triggers trading. Tool docstring carries: "WEALTH is advisory only. Arif Fazil is final authority." | Tool docstring |

---

## 5. Implementation Sequence (Phase 3, post-seal)

Strict order — each step gated on previous step passing `forge_evaluate` G≥0.80:

1. **CoinGecko adapter** — lowest auth friction, free tier, public API. Build → forge_evaluate.
2. **DefiLlama adapter** — free, no auth, lenient rate limit. Build → forge_evaluate.
3. **Binance public ticker** — no key required, but geo-block US IPs via env check. Build → forge_evaluate.
4. **Crypto router** — priority-based dispatch + fallback chain. Build → forge_evaluate.
5. **`wealth_sensor_fetch` mode wiring** — single-branch addition, gated by `asset_class == "crypto"`. Build → forge_evaluate.
6. **End-to-end smoke** — BTC spot price via CoinGecko → fall back to DefiLlama on simulated rate limit → sealed to VAULT999 → probe response with `capital_registry`.
7. **Arkham adapter** — **conditional, deferred**. Only after Arif provisions `ARKHAM_API_KEY` in `secrets/kunci-root.env`. Built last because it's the only paid, key-gated provider.

Per-step commit message convention: `WEALTH crypto: <step> — <forged|cancelled>` with receipt body citing this proposal as evidence.

---

## 6. Failure Modes (honest)

| Failure | Recovery | Blast radius |
|---|---|---|
| All 4 providers fail simultaneously | Serve last `SourceBundle` from cache + emit HOLD signal | **Low** (no synthesis, no action) |
| CoinGecko rate limit (10/min ceiling hit) | Auto-fallback to DefiLlama oracle | Low |
| DefiLlama schema change | Pin version, emit warning | **Medium** |
| Binance geo-block (US IP) | DefiLlama handles price oracle | Low |
| Arkham key expiration | Auto-pause provider, HOLD signal for operator | Low |
| Source price divergence > 0.5% | `wealth_sensor_reconcile` flags delta, no synthesis | **Medium** |
| Stale cache (offline > 5 min) | `epistemic_label` flips from `OBS` to `SPEC` (uncertainty surfaced) | Low |

---

## 7. Out of Scope (explicit)

- **Trading execution.** Data only. No order placement, no signal-to-trade conversion.
- **Wallet integration.** F12 surface too high (irreversible commitment, key custody).
- **DEX routing.** Binance public ticker only. No UniSwap, PancakeSwap, Curve.
- **Sub-federation of crypto exchanges.** Out of scope this round.
- **Real-time sub-second streaming.** Polling only. WebSocket = future work, separate proposal.
- **On-chain MEV / mempool scraping.** Different substrate entirely (requires archive node).
- **NFT floor prices.** Different vertical; defer to v2.

---

## 8. Approval Path (F13)

- [ ] **arif_seal Phase 2** — this document. 888 verdict on architecture.
- [ ] **forge_evaluate Phase 3** — each adapter G≥0.80 before activation.
- [ ] **Arif provisions keys** (if Arkham): add `ARKHAM_API_KEY` to `secrets/kunci-root.env` via the 5-R protocol.
- [ ] **End-to-end smoke** — live BTC price via crypto path, sealed to VAULT999.
- [ ] **F13 retention** — `wealth_sensor_*` docstring carries advisory-only sentence.

---

## 9. Open Questions for Phase 2 Gate

| # | Question | Default if no answer |
|---|---|---|
| Q1 | Provider priority order for `spot_price` fallback? | CoinGecko → DefiLlama → Binance (Arkham out of spot path) |
| Q2 | Cache TTL for spot price (60s default)? | 60s (sub-minute freshness not a v1 goal) |
| Q3 | Allow `priority` override per call, or lock to provider config? | Override per call (flexibility), default in router config |
| Q4 | Arkham deferred vs simultaneous with the other 3? | **Deferred** until Arif provisions key |

---

## 10. References

- `WEALTH/docs/WEALTH_MCP_ARCHITECTURE.md` (historical, sealed 2026-07-15)
- `WEALTH/wealth_mcp/tools/canonical.py` (11 canonical tools live)
- `WEALTH/engines/commodity/gold-api/fetch_gold.py` (vertical-asset adapter template)
- `WEALTH/wealth_core/market_data_fallback.py` (fallback pattern)
- `WEALTH/wealth_contracts/epistemic.py` (epistemic ladder)
- `WEALTH/wealth_contracts/source_registry.yaml` (adapter registry)
- `/root/AGENTS.md` (constitution pointer)
- arifOS F1-F13 floor table (`arifOS/GENESIS/FLOOR_TABLE.json`)

---

**DITEMPA BUKAN DIBERI**

Forged not given. Physics is sovereign; WEALTH routes economics through it.
Crypto data joins the sensor dimension, doesn't expand the canonical surface.
