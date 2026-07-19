# PROTOCOL_CONFORMANCE.md — WEALTH (L3 DOMAIN)

```yaml
organ: WEALTH
layer: L3 DOMAIN
mcp_port: 18082
last_verified: 2026-07-19T17:30Z
```

## Protocol Status

| Protocol | Status | Notes |
|----------|--------|-------|
| **MCP** | ✅ CONFORMANT | 20+ capital_* tools via FastMCP |
| **FastMCP** | ✅ CONFORMANT | `wealth_mcp/server.py` uses FastMCP |
| **JSON-RPC 2.0** | ✅ CONFORMANT | Enforced by FastMCP |
| **SSE** | ✅ CONFORMANT | `/sse` endpoint |
| **Streamable HTTP** | ✅ CONFORMANT | `/mcp` POST endpoint |
| **SEP-2127** | ⚠️ GAP | Missing `llms.txt` for AI discovery |
| **XMCP** | ⚠️ GAP | No XMCP app manifests |
| **A2A** | ⚠️ GAP | No A2A agent card |
| **CloudEvents** | ⚠️ GAP | No CloudEvents emission |

## MCP Tool Surface

```
capital_primitive (npv, irr, emv, evoi, mc, kelly, markowitz, robust)
capital_health (conservation, flow, runway, survival, fiscal_breakeven)
capital_diagnose (stress_index, governance_capacity, cascade_model)
capital_market (fx, commodity, indicator, stock, gold, oil, gas)
capital_wisdom (wisdom, omni, epistemic)
capital_entropy, capital_ledger, capital_registry
wealth_institutional_stress_index, wealth_governance_capacity
wealth_cascade_model, wealth_external_exploitation_detect
```

## Gaps to Close

1. **SEP-2127**: Create `llms.txt` at repo root for AI discovery
2. **XMCP**: Add `xmcp.json` app manifest for MCP Apps compatibility
3. **CloudEvents**: Emit CloudEvents on capital computation
4. **A2A**: Register A2A agent card for inter-organ discovery
