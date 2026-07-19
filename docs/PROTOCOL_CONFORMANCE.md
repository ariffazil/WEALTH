# 💰 WEALTH — Protocol Conformance

> **Layer:** L3 DOMAIN · **Role:** Capital Intelligence Organ
> **Protocols:** MCP Server, JSON-RPC 2.0, Well-Known

## Supported Protocols

| Protocol | Status | Detail |
|----------|--------|--------|
| MCP Server | ✅ CONFORMANT | 8 public tools (capital_*), session-gated |
| JSON-RPC 2.0 | ✅ CONFORMANT | MCP transport layer |
| Well-Known | ⚠️ PARTIAL | /health exists, no /.well-known/mcp/server.json |
| SEP-2127 | ❌ GAP | No MCP server card |
| XMCP Apps | ❌ GAP | No MCP Apps registered |

## MCP Tool Surface
- **Public tools:** 8 (capital_primitive, capital_market, capital_health, capital_entropy, capital_wisdom, capital_diagnose, capital_ledger, capital_registry)
- **Session requirement:** SESSION_REQUIRED for all tools (L11 AUTH)

## Gaps
1. **SEP-2127:** No MCP server card endpoint
2. **Well-Known:** No /.well-known/mcp/server.json
3. **XMCP Apps:** No interactive apps registered

*DITEMPA BUKAN DIBERI*
