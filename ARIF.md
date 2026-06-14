# ARIF.md | METABOLIC KERNEL v1.0

> ⚰️ **TOMBSTONE — STALE AS OF 2026-06-14**
> This file is a historical metabolic snapshot from 2026-06-03. It has **not** been the live source of truth since the 2026-06-12 federation topology alignment.
> Do not rely on counts, commit hashes, or test numbers here. See `README.md`, `CONTEXT.md`, `BOUNDARY.md`, and `FEDERATION_STATUS.md` for current state.
> Preserved for audit trail only.
>
> **Live facts (2026-06-14):**
> - Public MCP surface: **20 tools**
> - Hidden aliases: **34**
> - Verified `@mcp.tool` decorators: **65** in `internal/monolith.py`
> - Port: **18082**
> - arifOS kernel port: **8088**
> - APEX: legacy health probe on **3002**
> - License: **AGPL-3.0**
> - Python tests: **153/153 PASS**

---

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
- VERSION: v2026.06.03-PR5-SEALED


## 1. CURRENT FOCUS (INSTRUCTION POINTER)

- Branch: `main` (HEAD = `304ae54`, 2026-06-03 forge receipt). Public surface: 42 tools.
- **PR 5 sealed (2026-06-03):** WEALTH advisory boundary — `domain_seal_validity` ≠ `judge_seal_authorization`; `INSUFFICIENT_INPUT` honored by `wealth_synthesize`; 81/81 pass.
- Sovereign Malaysia context: maruah, scale_mode='sovereign', E&P presets, emergence scan hardening.
- Container image lags HEAD — rebuild pending.


## 2. OPERATIONAL MANDATE

- WEALTH = capital allocation intelligence organ. Internal kernel: `internal/monolith.py` (6000+ LOC).
- Constitutional floor enforcement: F1-F13 on all tools. Emergence scan detects sovereignty/extraction context.
- Upstream: GEOX (prospect economics), arifOS kernel. Downstream: arifOS 888_JUDGE, allocation workflows.
- PR 5 doctrine: WEALTH advises (`domain_seal_validity`); arifOS authorizes (`judge_seal_authorization`). The two never conflate.


## 3. THE 999 SEAL (SESSION LOG)

- 2026-06-03 | Claude Code (AGI OPENCLAW) | **PR 5: WEALTH advisory boundary ⚖️ SEALED.** Commit `304ae54` pushed to origin/main. `internal/engines/advisory.py` (NEW, 206 LOC). `wajib_envelope` injects 5 advisory fields. `wealth_synthesize` honors `INSUFFICIENT_INPUT`. 8 new tests; 81/81 pass; F13 honored (zero new MCP tools).
- 2026-05-15 | Claude + Omega | WL-1/2/3: EVOI priors, emergence aliases, WorldBank staleness. Sovereign Malaysia context.
- 2026-05-07 | big-pickle | Next Horizon refactor: 36 atomic tools. Merged to main.


## 4. ACTIVE TOPOLOGY (MEMORY MAP)

- CRITICAL_FILES:
  - `internal/monolith.py` → WEALTH MCP kernel (6000+ LOC): 15 public tools, emergence scan, maruah, EVOI, synthesize
  - `internal/engines/canonical_tools.py` → 16 canonical wrappers with WAJIB envelope + Five Seals
  - `internal/engines/five_seals.py` → WAJIB envelope; emits 5 advisory fields (PR 5)
  - `internal/engines/advisory.py` → PR 5 advisory boundary (NEW 2026-06-03)
  - `mcp/server.py` → Cross-domain demo (6 tools)
  - `host/governance/` → Floor enforcement, vault, policy engine
  - `tests/test_advisory_boundary.py` → PR 5 tests (8 NEW)
  - `tests/test_smoke.py` → Public surface verification

- ENTRYPOINTS:
  - `python3 -m internal.monolith` → systemd `wealth-organ` on :18082
  - `python3 -m pytest tests/ -q` → 81/81 pass (post-PR 5)

- DATA_FLOWS: WorldBank/Ember → wealth_field_macro → EVOI → synthesize → `[INSUFFICIENT_INPUT guard]` → arifOS JUDGE. Every output carries `domain_seal_validity` + `seal_authority_disclaimer` (PR 5).


## 5. INTERRUPTS & FAULTS (BLOCKERS)

- SOFT_FRICTION: Container image lags HEAD (PR 5 not in GHCR yet). Rebuild pending.
- SOFT_FRICTION: 25 legacy V2 aliases in `__main__`. Phase 3 retirement pending.
- SOFT_FRICTION: arifOS manifest claims `tool_count: 44`; runtime is `42` (post-Path D). PR #489 sync pending.
- HARD_BLOCK: None. 81/81 pass. F1-F13 governance wrapper active.


## 6. RECENT SCARS (W_scar)

- [2026-06-03] → [PR 5: domain_seal_validity vs judge_seal_authorization] → [8/8 new tests. 73/73 existing. Zero new MCP tools. Service restarted, head=304ae54.]
- [2026-05-15] → [WL-1/2/3: EVOI priors, emergence aliases, WorldBank staleness] → [Sovereign context hardened.]


## 7. EXECUTION BUFFER (COMMANDS)

| Command | Status | Context |
|---------|--------|---------|
| `python3 -m internal.monolith` | ✅ | systemd `wealth-organ` on :18082, head=304ae54 |
| `python3 -m pytest tests/ -q` | ✅ | 81/81 pass (post-PR 5) |
| `git push origin main` | ✅ | Pre-push guard: `REPO=ariffazil/wealth` trailer required |


## 8. PRIVILEGE ESCALATION (888 HOLD)

- [Q]: Phase 3 — retire 25 legacy V2 aliases? Ω₀ = 0.3 (low uncertainty).
- [Q]: Git history rewrite for Supabase key? Key was hardcoded in tracked file; now uses env var; history still contains it. Ω₀ = 0.0 (certain — key is in history).


## 9. PIPELINE PREFETCH (NEXT MOVES)

- [x] **PR 5: WEALTH advisory boundary** — SEALED 2026-06-03, commit 304ae54
- [ ] **PR 6: WELL reflect-only boundary** 🪞 — next in chain (Claude Code)
- [ ] **PR 7: GEOX declared-vs-callable registry** 🔧 — next in chain (Claude Code)
- [ ] **HF AAA card expansion (Path B)** — 12 gates, GATES.md staging
- [ ] **PR 4: A-FORGE hard gate** 🔒 — F13 architecture, sovereign ratification
- [ ] Rebuild WEALTH container → GHCR
- [ ] Phase 3: retire 25 legacy V2 aliases
- [ ] Resolve arifOS manifest `tool_count: 44` vs runtime `42` (PR #489)


---

*🪙 GOLD SEAL | METABOLIC KERNEL v1.0 | arifOS AAA | 888 JUDGE VETO | DITEMPA BUKAN DIBERI*
*Readable by: single human · couple · company · institution · AI agent · machine · team · civilisation intelligence*
