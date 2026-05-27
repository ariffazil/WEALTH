<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-05-26
valid_from: 2026-05-26
valid_until: 2026-06-26
confidence: high
scope: /root/WEALTH
-->

# AGENTS.md — WEALTH | arifOS Federation

> **MANDATORY BOOT SEQUENCE**
> 1. Read `/root/AGENTS.md` (Global Federation Rules & Identity)
> 2. Read `/root/CONTEXT.md` (Live Machine State & Ports)
> 3. Read this file (Repo-Specific Build/Test/Run rules)

> **DITEMPA BUKAN DIBERI** — Capital intelligence is forged, not given.

## Who You Serve

Arif. This is the **WEALTH** organ of the arifOS federation — Resource Intelligence / Capital Thermodynamics.

## What This Repo Is

The canonical capital engine. It models conservation, flow, gradient, entropy, energy, time, inertia, field, signal, game, boundary, and hysteresis as thermodynamic invariants over financial and resource systems.

**48 MCP tools** across 13 primitives × modes. Dual runtime: Python (canonical) + Node.js (legacy).

## Authority & Autonomy

### Autonomous
- Modify Python/JS logic, add tools, refactor
- Run tests, fix bugs
- Update schemas and contracts

### Requires 888_HOLD
- Changes to `pyproject.toml` license field (currently PROPRIETARY — anomaly noted)
- Cross-repo API contract changes
- Production deployment without verified build + test pass

## Build & Test

```bash
cd /root/WEALTH

# Python side
pip install -e .
python internal/monolith.py   # Start canonical FastMCP server (default port 8082; live VPS: 18082)
pytest tests/ -q              # Python tests

# Node.js side (legacy JS kernel)
npm install
npm test                      # node --test tests/*.test.js
npm run boot                  # node cli.js boot

# Docker
docker build -t wealth .
```

## Key Directories

| Path | Purpose |
|------|---------|
| `internal/monolith.py` | Canonical kernel — 48 MCP tools (~10,152 lines) |
| `mcp/server.py` | Cross-domain demo surface (6 tools) |
| `host/` | Modular Python libraries (coordination, epistemic, governance, ingest, kernel, wealth) |
| `src/` | Legacy JS/Node kernel |
| `civilizational/` | JS boundary monitors |
| `canon/` | Constitutional specs |

## Known Anomalies

- `pyproject.toml` declares `license = {text = "PROPRIETARY"}` while `package.json` declares `"license": "AGPL-3.0"`. **Do not change without 888_HOLD.**

## Federation Position

```
arifOS (Ω Law) → WEALTH (Capital) → A-FORGE (Ψ Execution) → VAULT999 (Seal)
```

WEALTH provides **evidence** — never execution. It computes NPV, IRR, EMV, DSCR, risk scores, and macro snapshots. It does not move capital.

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
