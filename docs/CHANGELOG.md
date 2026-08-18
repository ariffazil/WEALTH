# Changelog

## v2026.08.18-crypto-extension - 2026-08-18

WEALTH capital intelligence extended to multi-asset surface with full F1-F13 constitutional envelope preserved on crypto data ingestion. NO new federated tool was created.

### Substrate (Steps 3–8.5)
- `wealth_core/ingest/crypto/router.py` — `CryptoRouter` with priority-based fallback chain (Option B lock: Binance → CoinGecko → DefiLlama). F12 fail-closed via `WEALTH_BINANCE_ENABLED` env-guard. F4 CLARITY via 60s cache; F7 HUMILITY via `SPEC` label on stale cache hits.
- `wealth_core/ingest/crypto/provider_config.py` — per-kind priority chain + GeoSkip.
- `wealth_core/ingest/crypto/adapters/registry.py` — lazy `importlib`-based dispatch; `ImportError → ProviderError` so the live tree stays bootable while providers land one-at-a-time.
- `engines/crypto/coingecko/fetch_coingecko.py` — adapter (forge_evaluate G=0.8144).
- `engines/crypto/binance/fetch_binance.py` — adapter with 429 + 403/451 geo-block detection (forge_evaluate G=0.8144 after description-tighten retry).
- `engines/crypto/defillama/fetch_defillama.py` — adapter for `spot_price` and `tvl`; silent-redundancy aggregator (forge_evaluate G=0.8144 first try).
- `tests/test_crypto_router_smoke.py` — 7-scenario mock-based router E2E (all PASS).
- Step 8.5: `Literal` import fix to `router.py` (Pydantic forward-ref bug caught by mandatory smoke test; LSP gate had been blind to runtime schema).

### Canonical surface (Step 9)
- `wealth_mcp/tools/canonical.py` — added `asset_class: str = "fx_commodity"` parameter to `capital_market` (1 dispatcher branch routing to `CryptoRouter.fetch` when `asset_class == "crypto"`). Zero new tool. Federated surface remains 8 tools.
- `tests/test_step9_canonical_e2e.py` — 3-scenario stub-MCP canonical-surface E2E (all PASS): happy-path crypto routing, backward-compat (default `asset_class` does NOT touch `crypto_router`), and F12 RESILIENCE (router exception → ERROR envelope, not crash).

### Documentation
- `docs/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md` — promoted from `forge_work/` for audit-chain persistence.
- `docs/TOOL_MODE_MAP.md` — capital_market mode row extended with `crypto*`; new surface-extension table entry; `*` footnote documents the `asset_class` discriminator and back-compat guarantee.

### Deferred (per F13 directive 2026-08-18)
- Step 11 (Arkham) — `arkham` adapter code path is registered in the dispatch table but the underlying `engines/crypto/arkham/fetch_arkham.py` module is intentionally absent. `get_adapter("arkham")` raises `ProviderError("module not yet implemented")` which the router's existing fallback chain catches cleanly. No provisional adapter code, no fake API keys, no discharge without `ARKHAM_API_KEY` provision via the 5-R protocol.

### Cumulative receipt

```
3a155d2  Step 9 canonical surface wiring        +271
a18569c  Step 8.5 router Pydantic schema fix   +3  -4
9adf79c  Steps 7+8 DefiLlama + smoke test      +413
6808b2e  Step 5  Binance adapter                +206
5717b4e  Step 3  scaffold + CoinGecko           +476
─────────────────────────────────────────────────
NET:     12 files added, 1 modified
         0 new canonical tools
         0 F-floor breach
         4 F8 GENIUS G-receipts (each adapter ≥ 0.80)
         10/10 scenarios PASS across both E2E suites
```

## v2026.06.02-truth-bound - 2026-06-02

- Fixed eureka forge runtime in `wealth_synthesize` so `stat_assumptions` actually fires.
- Bug 1: `_Path` was referenced before being defined in the function scope, raising `NameError`. Added `from pathlib import Path as _Path` and replaced the typo `_os.environ.setdefault` with `os.environ.setdefault` (the `_os` prefix was an undefined name; the module-level import is `os`).
- Bug 2: `_tag_dimension` overwrites the entire `results["entropy"]` dict, silently dropping the `_saf_assumptions` / `_saf_embed_skipped` keys the forge had just set. Refactored to capture them in locals, then re-attach them after `_tag_dimension` runs.
- Verified the eureka forge now produces live normality checks: bimodal cashflow `[5,8,80,12,10,...]` returns `shapiro_p=6e-06, non_normal=True, advisory triggered`; normal cashflow `[25,30,35,30,25,...]` returns `shapiro_p=0.815, non_normal=False`.
- Honors the prior seal `EUREKA-FORGE-SAF-20260602-OMEGA` (commit `664964f`), which had overclaimed the runtime behavior. The seal's intent is now honored at runtime.
- Wired `SAF_DATA_ROOT=/root/.local/share/arifos/saf-data` via systemd override on `wealth-organ.service` (the SAF-organ was archived to `/root/_archive/SAF-2026-06-02-eureka-forged`, leaving the sandbox's hardcoded path stale).
- Bumped version in `pyproject.toml` and `package.json` from `2026.05.01` to `2026.06.02`.
- Verified `pytest tests/ -q`: 66/66 passing.
- Companion seal: VAULT999 `TRUTH-BOUND-UPGRADE-20260602` (merkle leaf `edea707d3d3742db...`) records the recursive alignment pass at the federation level.

## v2026.05.22-pre - 2026-05-22

- Added birthday pre-release notes for the 2026-05-22 repo-hygiene branch.
- Repaired the shared federation layout contract.
- Added a 2026-05-21 repo hygiene audit ledger.
- Made `server.py` import-safe so tests can import WEALTH functions without binding port `8082`.
- Updated stale registry assertions to the current public tool surface.
- Verified `npm test`: 52/52 passing.
- Verified `pytest tests/ -q`: 50/50 passing.
- No license fields changed.

## v1.5.0 - 2026-04-17

- Aligned the active documentation set to the current repo source of truth.
- Clarified that the canonical packaged MCP kernel is `server.py`, while `mcp/server.py` is a secondary civilizational FastMCP surface.
- Documented the live kernel families, current tool counts, and the split between the canonical 11-band map and the larger runtime superset.
- Added `wealth_evaluate_prospect` to the civilizational demo MCP surface and documented it alongside the existing markets / energy / food tools.
- Replaced stale active-doc references to the retired `mcp/server.js` packaging story.

## v1.3.1 - 2026-04-14

- Hardened the WEALTH finance kernel with deterministic measurement code for NPV, EAA, IRR, MIRR, PI, EMV, payback, discounted payback, and DSCR.
- Added parity coverage so canonical NPV, DSCR, and growth vectors match across `host/kernel/finance.js` and `server.py`.
- Locked the shared `t=0` cashflow convention across NPV, PI, and payback tests.
- Escalated ambiguous IRR (`MULTIPLE_IRR_POSSIBLE`) and DSCR default stress (`DSCR < 1.0`) to `888-HOLD`.
- Added confidence-band telemetry for estimated or hypothesis-level NPV and DSCR inputs.
- Removed the Python MCP surface's hard dependency on a `node` subprocess for core WEALTH tool execution.
- Restored a stable `src/` import surface over the live `host/` runtime code and expanded the WEALTH test suite to 23 passing tests.
