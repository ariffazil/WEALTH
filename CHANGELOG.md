# Changelog

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
