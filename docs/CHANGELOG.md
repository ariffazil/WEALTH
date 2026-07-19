# Changelog

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
