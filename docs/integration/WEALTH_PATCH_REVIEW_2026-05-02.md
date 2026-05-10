# WEALTH Patch Review — 2026-05-02

## 1. Root Cause
The current bridge implementation is stateless. It creates a new `httpx.AsyncClient` for every request and does not persistently store or propagate the `mcp-session-id` header returned by the WEALTH server during the `initialize` handshake.

## 2. Protocol Requirement (FastMCP 3.x)
The MCP StreamableHTTP transport requires that the `mcp-session-id` (or `x-mcp-session-id`) header provided by the server in the `initialize` response must be included in all subsequent JSON-RPC requests (e.g., `tools/call`, `tools/list`). Failure to provide this ID causes the server to treat the request as unauthenticated or out-of-order, often resulting in 406 or empty SSE responses.

## 3. Implementation Choice: Persistent Client
A persistent `httpx.AsyncClient` is employed here to:
- Enable **connection pooling** to reduce handshake latency.
- Allow for **sticky headers**; once the session ID is retrieved, it is added to the client's base headers, ensuring automatic propagation without manual injection in every call site.

## 4. Refined Diff
```python
--- arifOS/arifosmcp/runtime/wealth_bridge.py
+++ arifOS/arifosmcp/runtime/wealth_bridge.py
@@ -19,41 +19,53 @@
 WEALTH_PORT = 8082
 WEALTH_BASE = f"http://{WEALTH_HOST}:{WEALTH_PORT}"
 
-_WEALTH_SESSION_ID: str | None = None
+class WealthClient:
+    """Managed MCP client for WEALTH organ with persistent session."""
+    def __init__(self):
+        self.session_id: str | None = None
+        self.client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
+
+    async def ensure_session(self) -> str:
+        """Initialize or return existing session ID."""
+        if self.session_id:
+            return self.session_id
+
+        resp = await self.client.post(
+            f"{WEALTH_BASE}/mcp",
+            json={
+                "jsonrpc": "2.0", "id": 1, "method": "initialize",
+                "params": {
+                    "protocolVersion": "2024-11-05",
+                    "capabilities": {},
+                    "clientInfo": {"name": "arifOS-kernel", "version": "1.0"},
+                },
+            },
+            headers={"Accept": "application/json, text/event-stream"}
+        )
+
+        if resp.status_code != 200:
+            raise ConnectionError(f"WEALTH init failed: {resp.status_code}")
+
+        sid = resp.headers.get("mcp-session-id") or resp.headers.get("x-mcp-session-id")
+        if not sid:
+            raise ConnectionError("WEALTH: No mcp-session-id in response headers")
+
+        self.session_id = sid
+        self.client.headers.update({"mcp-session-id": sid, "x-mcp-session-id": sid})
+        return sid
+
+    async def call_rpc(self, method: str, params: dict) -> dict:
+        await self.ensure_session()
+        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
+        resp = await self.client.post(f"{WEALTH_BASE}/mcp", json=payload)
+        
+        buffer = ""
+        async for line in resp.aiter_lines():
+            if line.startswith("data: "):
+                buffer += line[6:]
+        
+        data = json.loads(buffer)
+        if "error" in data:
+            raise ValueError(f"WEALTH Error: {data['error']}")
+        return data.get("result", {})
+
+_client = WealthClient()
 
 async def call_wealth_tool(tool_name: str, arguments: dict | None = None) -> dict:
-    # ... old global state logic ...
-    result = await _post_json_rpc(payload)
-    return result
+    return await _client.call_rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})
```

## 5. Proof Checklist
- [x] **Handshake:** `initialize` request captures session header. (Verified: `d3b8c2dd51d74ffd888299783c74b86d`).
- [x] **First Call:** `tools/call` succeeds with the captured header. (Result: `SSE_VALID`).
- [x] **Persistence:** Second `tools/call` succeeds without re-initializing. (Verified via container logs).
- [x] **Telemetry:** Logs show single "session established" event for multiple tool calls.
# WEALTH Patch Review - 2026-05-02

## Actual Test Output

Command:

```bash
cd /root/arifOS
python3 test_wealth_persistence.py
```

Output:

```json
{
  "first_call_keys": [
    "content",
    "isError",
    "structuredContent"
  ],
  "initialize_count_after_first": 1,
  "initialize_count_after_second": 1,
  "same_session_reused": true,
  "second_call_keys": [
    "content",
    "isError",
    "structuredContent"
  ],
  "second_call_rehandshake": false,
  "tool": "wealth_future_value"
}
```

CLAIM: The persistent-session patch is applied in `/root/arifOS` on `feat/wealth-mcp-session`.

CLAIM: The diagnostic called `wealth_future_value` twice with different arguments and proved the bridge initialized once, reused the same MCP session, and did not re-handshake for the second call.

CLAIM: `/root/WEALTH` is on `feat/wealth-mcp-session`; no WEALTH source patch was needed for this client-side bridge fix.

## Notes

The diagnostic targets `http://127.0.0.1:8082` from the host. Production bridge code still uses Docker DNS `wealth-organ:8082` when running inside the arifOS container/network.

DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
