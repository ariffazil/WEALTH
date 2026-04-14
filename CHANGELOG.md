# Changelog

## v1.3.1 - 2026-04-14

- Hardened the WEALTH finance kernel with deterministic measurement code for NPV, EAA, IRR, MIRR, PI, EMV, payback, discounted payback, and DSCR.
- Added parity coverage so canonical NPV, DSCR, and growth vectors match across `host/kernel/finance.js` and `server.py`.
- Locked the shared `t=0` cashflow convention across NPV, PI, and payback tests.
- Escalated ambiguous IRR (`MULTIPLE_IRR_POSSIBLE`) and DSCR default stress (`DSCR < 1.0`) to `888-HOLD`.
- Added confidence-band telemetry for estimated or hypothesis-level NPV and DSCR inputs.
- Removed the Python MCP surface's hard dependency on a `node` subprocess for core WEALTH tool execution.
- Restored a stable `src/` import surface over the live `host/` runtime code and expanded the WEALTH test suite to 23 passing tests.
