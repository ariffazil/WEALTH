# CLAUDE.md — WEALTH Agent Instructions

> **Canonical federation instruction file:** `/root/AAA/CLAUDE.md`
> **WEALTH organ** of the arifOS federation.
> **Port:** 18082 | **Identity version:** 2026.07.19 | **Transport:** streamable-http

## What WEALTH Is

The **capital intelligence organ** of the arifOS federation. It computes financial math, market observations, risk, wisdom, and institutional diagnostics. It never allocates capital or issues the final governance verdict.

The public MCP surface has **12 tools**: 8 mode-dispatched `capital_*` tools and 4 institutional compatibility tools. Authenticated `tools/list` is final truth.

Canonical entrypoint: `server_federated.py` → `wealth_mcp/server.py`.
`internal/monolith.py` remains a legacy implementation library and must not be deleted.

## Authority & Autonomy

### Autonomous
- Modify Python/JS logic, tools, and schemas within task scope
- Run tests and fix bugs

### Requires 888_HOLD
- Cross-repo API contract changes
- Capital execution or allocation authority
- Production deploy without verified build + test pass

## Build & Test

```bash
cd /root/WEALTH
uv sync --frozen
python server_federated.py             # Start canonical server on :18082
pytest tests/ -q --tb=short
npm test                               # Legacy Node.js tests
```

## Health Check

```bash
systemctl status wealth-organ
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
curl -s http://127.0.0.1:18082/tools | python3 -m json.tool
```

## Federation Position

```
Arif (F13) → AAA → arifOS (:8088) → WEALTH (:18082) → A-FORGE → VAULT999
```

WEALTH provides evidence and computation. arifOS judges. Arif decides.

## Key Paths

| Path | Purpose |
|------|---------|
| `server_federated.py` | Canonical HTTP entrypoint and health identity |
| `wealth_mcp/server.py` | FastMCP registration, governance wrapper, receipts, resources |
| `wealth_mcp/tools/canonical.py` | 8 canonical `capital_*` tools |
| `wealth_mcp/tools/institutional.py` | 4 institutional compatibility tools |
| `internal/monolith.py` | Legacy implementation library; preserve |
| `internal/engines/` | Advisory, five seals, canonical tools; preserve |
| `mcp/server.py` | Supplemental demo surface; preserve |
| `host/` | Modular Python libraries |
| `tests/` | Python verification |

## Safety Truths

- `capital_ledger(mode="write")` is C2/IRREVERSIBLE; query is read-only.
- Receipt and ledger targets must be pre-provisioned; code must not silently create or claim persistence.
- `capital_entropy` returns structured `UNAVAILABLE` when its local optional dependency is absent.
- `/health` must not present `.git_commit` fallback data as a live source SHA.

---

**DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.**
