# WEALTH — Capital Intelligence & Resource Stewardship

[![SafeSkill Security](https://img.shields.io/badge/SafeSkill-85%2F100%20Pass%20with%20Notes-yellow)](https://safeskill.dev/scan/ariffazil-wealth)
[![MCP](https://img.shields.io/badge/MCP-FastMCP_3.2.4-7C3AED?style=flat-square)](https://github.com/ariffazil/wealth)
[![arifOS](https://img.shields.io/badge/arifOS-F1%E2%80%93F13_Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)
[![License](https://img.shields.io/badge/License-AGPL_V3-4EAF0C?style=flat-square)](./LICENSE)

> **Status:** OPERATIONAL | **Organ:** CAPITAL (Ω-WEALTH) | **Authority:** arifOS
> **Domain:** `wealth.arif-fazil.com`

## 🏛️ What this repo is

The capital intelligence and economic logic organ within the arifOS federation. WEALTH owns the financial thermodynamics layer — NPV, IRR, DSCR, EMV calculations, capital flow modeling, and resource stewardship. It operates across both Python (FastMCP kernel) and Node.js (legacy JS kernel) runtimes.

**WEALTH owns the CAPITAL — the thermodynamic layer that governs how resources flow through the federation.**

> **MCP Surface (live test 2026-05-17):** 17 tools — 12 Ω-WEALTH primitives × modes + synthesize + IEQ tools + `mcp_health_check`. Health reports `hidden_alias_count: 34`. Source has 69 `@mcp.tool` decorators; only 17 exposed on public surface.

## 📦 Ownership

- **Owns**: Financial calculations (NPV, IRR, DSCR, EMV), capital flow modeling, Supabase integration, civilizational boundary monitors.
- **Does NOT own**: Constitutional judgment (arifOS), geoscience (GEOX).

## 🏗️ Current Structure

```
WEALTH/
├── internal/
│   └── monolith.py          # Canonical FastMCP kernel (17 live MCP tools; 69 @mcp.tool decorators total — 52 hidden)
├── server.py               # Thin backward-compat wrapper (~15 lines)
├── mcp/
│   └── server.py           # Cross-domain demo surface (6 tools)
├── host/                  # Modular Python libraries
│   ├── coordination/      # Coordination protocols
│   ├── epistemic/         # Epistemic state
│   ├── governance/        # Constitutional floor hooks
│   ├── ingest/           # Data ingestion
│   ├── kernel/           # Core kernel logic
│   └── wealth/           # Wealth-specific logic
├── src/                   # Legacy Node.js kernel (JS)
├── civilizational/        # JS boundary monitors and prosperity index
├── canon/                 # Constitutional specs
├── archive/              # Archived files
│   └── monolith.py.v66.backup
├── api/                  # API definitions
├── apps/                 # Application surfaces
├── docs/                 # Documentation
├── tests/                # pytest (Python) + node --test (JS)
└── package.json          # Node.js scripts
```

## 🚀 Verified Commands

```bash
# Python side
pip install -e .
python internal/monolith.py   # Start canonical FastMCP server

# Node.js side
npm install
npm test                      # node --test tests/*.test.js
npm run boot                  # node cli.js boot
npm run check                 # node cli.js check
npm run seal                  # node cli.js seal

# Docker
docker build -t wealth .
```

## 🔗 Federation Loop

- [arifOS](https://github.com/ariffazil/arifOS) — Kernel (constitutional judgment)
- [GEOX](https://github.com/ariffazil/geox) — Field (economic constraints on field development)
- [WELL](https://github.com/ariffazil/well) — Substrate (human flourishing metrics)

---

*Last Verified: 2026.05.16 | 999 SEAL ALIVE*
