<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-15
valid_from: 2026-07-15
valid_until: 2026-08-15
confidence: high
scope: /root/WEALTH entrypoints
domain_law: CAPITAL_LAW
-->

# WEALTH MCP entry points — single canonical path

> **Zen rule:** one public MCP entry per organ.  
> **Live unit:** `wealth-organ.service` → `server_federated.py` → `wealth_mcp.server`  
> **Port:** `18082` · tools live **12** (`tools/list`)  
> **DITEMPA BUKAN DIBERI**

---

## Canonical (production)

| Path | Role |
|------|------|
| **`server_federated.py`** | **ONLY production entry** — systemd `ExecStart` |
| **`wealth_mcp/server.py`** | FastMCP create_mcp_server — tools / resources / prompts |
| **`wealth_core/`** | Pure capital math (no HTTP) |
| **`wealth_contracts/`** | Envelopes · epistemic tags |
| **`wealth_arifos_bridge/`** | Kernel handoff |
| **`wealth_compat/`** | Legacy aliases only |

```bash
# Production (matches systemd)
cd /root/WEALTH && .venv/bin/python3 server_federated.py
# or
systemctl status wealth-organ
curl -s :18082/health
```

Architecture layers (federated):

```
wealth_core → wealth_contracts → wealth_mcp → wealth_arifos_bridge
                                              ↑
                                    server_federated.py
```

---

## Deprecated (do not start for prod)

| Path | Status | Removal target | Notes |
|------|--------|----------------|-------|
| **`server.py`** | **DEPRECATED** — re-exports `internal.monolith` | 2026-08-15 | Tests/scripts only until migrated |
| **`internal/monolith.py`** | **LEGACY gravity well** | progressive extract → `wealth_core` | Not systemd entry |
| **`mcp/server.py`** | **DEPRECATED demo** (small tool surface) | 2026-08-15 | Banner already warns |
| **package.json `mcp` / `fastmcp` scripts** | Pointed at monolith historically | **fixed → federated** | Use python server_federated |

### Deprecation banner (agents)

```
If you import internal.monolith or run server.py as production:
  STOP → use server_federated.py / wealth_mcp.
  Monolith is not the federation SOT.
```

---

## npm / package scripts

```json
{
  "mcp": "python server_federated.py",
  "fastmcp": "python server_federated.py"
}
```

---

## Verification

```bash
systemctl cat wealth-organ | grep ExecStart
# expect: server_federated.py

curl -s http://127.0.0.1:18082/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('status'),d.get('architecture'),d.get('layers'))"
# expect: ALIVE · federated · wealth_core…wealth_mcp…
```

*One membrane. One law. CAPITAL_LAW.*
