# WEALTH MCP Server

> Model Context Protocol server for WEALTH constitutional governance and financial engines.

## Usage

### Run directly

```bash
node mcp/server.js
```

### Via npm script

```bash
npm run mcp
```

## Tools

| Tool | Purpose |
|------|---------|
| `wealth_check_floors` | Run F1-F13 floor checks on a proposed operation |
| `wealth_seal_999` | Attempt 999 SEAL on a decision state |
| `wealth_capitalx_score` | Calculate risk-adjusted cost of capital |
| `wealth_capitalx_compare` | Compare virtuous vs extractive capital rates (bps advantage) |
| `wealth_compute_networth` | Compute net worth with epistemic tags |
| `wealth_compute_cashflow` | Compute monthly cashflow, burn, and runway |
| `wealth_compute_maruah` | Compute Maruah dignity/integrity score |
| `wealth_project_growth` | Compound growth with F7 humility bands |
| `wealth_project_runway` | Runway depletion estimate |

## Resources

| Resource | Purpose |
|----------|---------|
| `wealth://governance/floors` | F1-F13 floor definitions and hold types |
| `wealth://governance/epistemic` | Epistemic tag enum (CLAIM, PLAUSIBLE, etc.) |
| `wealth://sample/state` | Demo financial state (MYR) |

## Safety

All tools enforce WEALTH governance natively:
- Irreversible actions trigger 888 HOLD
- Projections without uncertainty bands fail F7
- AI-deciding operations fail F10
- Floor overrides fail F12

## Integration Example (Claude Desktop)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wealth": {
      "command": "node",
      "args": ["/absolute/path/to/WEALTH/mcp/server.js"]
    }
  }
}
```

## Dependencies

- `@modelcontextprotocol/sdk`
- `zod`

---
*999 SEAL ALIVE*
