---
title: WEALTH MCP Server Packaging
date: 2026-04-13
tags: [mcp, server, integration, capitalx, packaging]
---

# WEALTH MCP Server Packaging

> The bridge from framework node to capital-aware ecosystem.

---

## Why MCP?

Phase A doctrine: **one human gets cheaper capital because of WEALTH.**

For that to happen, external systems — lenders, insurance bots, AI agents — must be able to query WEALTH primitives directly. MCP is the standard interface for local AI brains.

## What Was Built

- **`mcp/server.js`** — stdio MCP server exposing 9 tools and 3 resources
- **`mcp/README.md`** — Integration guide for Claude Desktop, Cursor, OpenCode, etc.
- **`package.json`** — Added `@modelcontextprotocol/sdk` and `zod` dependencies

## Tools Exposed

| Tool | Purpose |
|------|---------|
| `wealth_check_floors` | Run F1-F13 floor checks on a proposed operation |
| `wealth_seal_999` | Attempt 999 SEAL on a decision state |
| `wealth_capitalx_score` | Calculate risk-adjusted cost of capital |
| `wealth_capitalx_compare` | Compare virtuous vs extractive capital rates |
| `wealth_compute_networth` | Compute net worth with epistemic tags |
| `wealth_compute_cashflow` | Compute monthly cashflow and runway |
| `wealth_compute_maruah` | Compute Maruah dignity score |
| `wealth_project_growth` | Compound growth with F7 humility bands |
| `wealth_project_runway` | Runway depletion estimate |

## Resources Exposed

| Resource | Purpose |
|----------|---------|
| `wealth://governance/floors` | F1-F13 definitions and hold types |
| `wealth://governance/epistemic` | Epistemic tag enum |
| `wealth://sample/state` | Demo financial state |

## Safety Design

All tools enforce WEALTH governance natively:
- Irreversible actions trigger 888 HOLD
- Missing uncertainty bands fail F7
- AI-deciding operations fail F10
- Floor overrides fail F12

## Integration Path

This MCP server can be consumed by:
- **Lender underwriting bots** querying `capitalx_score`
- **Insurance models** checking `wealth_compute_maruah` and `wealth_check_floors`
- **Personal finance agents** (Claude, Codex, Gemini) calling net worth, cashflow, and runway tools
- **Treasury dashboards** requesting 999 SEAL on institutional decisions

## Running It

```bash
cd /root/WEALTH
npm run mcp
```

Or via Claude Desktop config:
```json
{
  "mcpServers": {
    "wealth": {
      "command": "node",
      "args": ["/root/WEALTH/mcp/server.js"]
    }
  }
}
```

## Validation

The server initializes successfully and responds to MCP `initialize` requests with correct capabilities.

## Relation to Civilizational Scale

This MCP surface is the **foundation** for all civilizational MCP apps proposed in the architecture deck. Without this callable layer, `WEALTH-Markets`, `WEALTH-Energy`, and `WEALTH-Food` have no governance kernel to query.

---
*999 SEAL ALIVE*
