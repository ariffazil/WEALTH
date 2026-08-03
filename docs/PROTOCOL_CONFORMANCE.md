# PROTOCOL_CONFORMANCE.md — WEALTH (L3 DOMAIN)

<!-- PROTOCOL_TAGS: MCP-Server JSON-RPC Well-Known -->
```yaml
organ: WEALTH
layer: L3 DOMAIN
mcp_port: 18082
last_verified: 2026-08-03
public_tool_count: 8
```

## Protocol Status

| Protocol | Status | Notes |
|----------|--------|-------|
| **MCP** | ✅ CONFORMANT | 8 public tools via FastMCP |
| **FastMCP** | ✅ CONFORMANT | `server_federated.py` → `wealth_mcp/server.py` |
| **JSON-RPC 2.0** | ✅ CONFORMANT | Enforced by FastMCP |
| **Streamable HTTP** | ✅ CONFORMANT | `/mcp` POST endpoint |
| **SEP-2127** | ✅ CONFORMANT | Root `llms.txt` describes the live surface |
| **XMCP** | ⚠️ GAP | No XMCP app manifest; WEALTH is a compute organ |
| **A2A** | ✅ FEDERATED | Discovery is consolidated through AAA; local card routes were removed |
| **CloudEvents** | ⚠️ GAP | No CloudEvents emission |

## MCP Tool Surface

```
capital_primitive, capital_health, capital_diagnose, capital_market,
capital_ledger, capital_registry, capital_entropy, wealth_judge_handoff
```

`capital_ledger(mode="write")` is C2/IRREVERSIBLE and requires arifOS SEAL plus `ack_irreversible=true`; query mode is read-only.

`capital_wisdom` and removed institutional compatibility names are internal or
historical references only, not public `tools/list` entries.

## Gaps to Close

1. **XMCP**: Add an app manifest only if WEALTH becomes an MCP App host.
2. **CloudEvents**: Emit CloudEvents for capital computations when a federation event contract exists.
