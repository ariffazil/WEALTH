# ARIF.md | METABOLIC KERNEL v1.0

> SYSTEM TYPE: LORE INTERFACE
> GOVERNANCE: arifOS AAA
> VETO: 888 JUDGE
>
> INVARIANT: Descriptive memory of repo state.
> This file NEVER modifies Law. It only reports and compresses observed reality.
> Law lives in: arifOS `000/000_CONSTITUTION.md`. Template: https://gist.github.com/ariffazil/81314f6cda1ea898f9feb88ce8f8959b


## 0. IDENTITY & MOUNT POINT

- REPO_NAME: WEALTH
- CONTAINER_ID: 2026-05-15
- DOMAIN_ROLE: Capital Intelligence Engine — constitutional capital allocation, valuation, and economic reasoning organ for arifOS federation
- STABILITY_CLASS: RAPID-ITERATE
- VERSION: v2026.05.15-WL123-SEALED


## 1. CURRENT FOCUS (INSTRUCTION POINTER)

- Branch: `main` (merged from `wealth/next-horizon-refactor`).
- 17 public MCP tools: wealth_conservation_capital through wealth_synthesize + mcp_health_check.
- WL-1 sealed: EVOI well_type priors (wildcat 0.25, near_field 0.50, appraisal 0.55, development 0.75). prior_pos/posterior_pos optional with Bayesian fallback.
- WL-2 sealed: Emergence scan aliases (foreign_actor_involved, irreversible=True, irreversibility=HIGH).
- WL-3 sealed: WorldBank staleness detection (≥2y → STALE_WARN + MEDIUM ceiling, ≥3y → STALE_CRITICAL + LOW ceiling).
- Sovereign Malaysia context: compute_maruah_from_context(), SCALE_DEFAULTS["sovereign"] (50yr horizon, F13 required, maruah_floor=0.70), WEALTH_SERIES_PRESETS (8 Malaysian E&P series).
- 8-gap forge: synthesize engine + live intelligence nervous system committed.
- Container running `ghcr.io/ariffazil/wealth:93ddd72` — 4 commits behind HEAD. Rebuild pending.
- Tests: 33/33 pass (Python). Dual runtime: Python FastMCP + Node.js legacy.


## 2. OPERATIONAL MANDATE

- WEALTH is the capital allocation intelligence organ — 15 public tools across 12 physics dimensions.
- Internal kernel: `internal/monolith.py` (6000+ lines). FastMCP server.
- Physics-first naming: wealth_conservation_capital, wealth_flow_liquidity, wealth_gradient_price, etc.
- Constitutional floor enforcement: F1-F13 gates on all tools. Emergence scan detects sovereignty/extraction context.
- Sovereign Malaysia presets: brent, malaysia_gdp, malaysia_oil, lng_asia, usd_myr, inflation_my, coal_price, energy_mix_my.
- Upstream: GEOX (prospect economics), arifOS kernel (constitutional governance).
- Downstream: arifOS 888_JUDGE, capital allocation workflows.


## 3. THE 999 SEAL (SESSION LOG)

- 2026-05-15 | Claude (WL-1/2/3 audit) + Omega (SOT) | WL-1: EVOI well_type priors. WL-2: emergence scan aliases. WL-3: WorldBank staleness. All 33 tests pass. CONTAINER_ID updated.
- 2026-05-15 | Omega | Sovereign Malaysia context (maruah scoring, scale_mode='sovereign', E&P presets, emergence scan hardening). Data staleness flags + well type baselines. Test assertions bumped 14→15.
- 2026-05-07 | big-pickle (opencode) | Next Horizon refactor: 36 atomic tools, 12 prompts, 28 resources. branch `wealth/next-horizon-refactor` created (now merged to main). Old canonical tools retained as deprecated shims.


## 4. ACTIVE TOPOLOGY (MEMORY MAP)

- CRITICAL_FILES:
  - `internal/monolith.py` → WEALTH MCP kernel (6000+ lines): 15 public tools, emergence scan, maruah scoring, EVOI compute, field macro presets, synthesize engine
  - `mcp/server.py` → Cross-domain demo surface (6 tools)
  - `host/governance/` → Floor enforcement, vault, policy engine
  - `canon/WEALTH_HARNESS.md` → Harness architecture spec
  - `tests/test_smoke.py` → Public surface verification (33 tests)

- ENTRYPOINTS:
  - `python internal/monolith.py` → WEALTH MCP server (port 8082)
  - `python -m pytest tests/ -q` → 33/33 pass

- DATA_FLOWS:
  - WorldBank/Ember → wealth_field_macro → ingest_fetch (staleness check) → EVOI → synthesize → arifOS JUDGE


## 5. INTERRUPTS & FAULTS (BLOCKERS)

- SOFT_FRICTION: Container image 4 commits behind HEAD. Rebuild needed.
- SOFT_FRICTION: 25 legacy V2 aliases still in `__main__` block. Phase 3 retirement pending.
- HARD_BLOCK: None. 33/33 tests pass. All MCP tools operational.


## 6. RECENT SCARS (W_scar)

- [2026-05-15] → [WL-1/2/3 sealed: EVOI priors, emergence aliases, WorldBank staleness] → [All tests pass. Sovereign context hardened.]
- [2026-05-07] → [36 umbrella tools decomposed into atomic physics-first tools] → [Zero breaking changes. Deprecated shims retained.]


## 7. EXECUTION BUFFER (COMMANDS)

| Command | Status | Context |
|---------|--------|---------|
| `python internal/monolith.py` | ✅ | WEALTH MCP on port 8082 |
| `python -m pytest tests/ -q` | ✅ | 33/33 pass |
| `npm test` | ✅ | JS: 52 passed |


## 8. PRIVILEGE ESCALATION (888 HOLD)

- [Q]: Phase 3 — retire 25 legacy V2 aliases from `__main__` block?
- [CONTEXT]: Migration path documented. Zero breaking changes expected. Ω₀ = 0.3 (low uncertainty).
- [Q]: Git history rewrite for Supabase key in git history?
- [CONTEXT]: Key was hardcoded in tracked file. Now uses env var. History still contains it. Ω₀ = 0.0 (certain — key is in history).


## 9. PIPELINE PREFETCH (NEXT MOVES)

- [ ] Rebuild WEALTH container → push to GHCR → `docker compose up -d`
- [ ] Phase 3: Retire 25 legacy V2 aliases
- [ ] Phase 4: Clean up mcp/server.py domain tools
- [ ] Git history rewrite for Supabase key


---

*🪙 GOLD SEAL | METABOLIC KERNEL v1.0 | arifOS AAA | 888 JUDGE VETO | DITEMPA BUKAN DIBERI*
*Readable by: single human · couple · company · institution · AI agent · machine · team · civilisation intelligence*
