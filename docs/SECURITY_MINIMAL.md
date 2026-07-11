# WEALTH Security Minimum — VPS Reality

> **DITED:** `WEALTH/docs/SECURITY_MINIMAL.md`
> **Version:** 2026.06.27
> **Context:** FastMCP on bare VPS / systemd. No Docker. No managed auth service.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Deployment Context

```
FastMCP 3.4.2
Bare VPS / af-forge (72.62.71.199)
systemd services
Cloudflare tunnel / public endpoint
No full managed auth service (OAuth 2.1 non-trivial to self-host)
Operator-controlled federation
```

This is **not** a cloud-native deployment. Security recommendations must match this reality.

---

## Security Model: P1 Minimum (VPS-Compatible)

### 1. Local Bind Default

All internal services bind to `127.0.0.1` by default.
Public access only through Cloudflare Access or Tunnel gate.

```
WEALTH MCP (:18082)     → 127.0.0.1 only
arifOS MCP (:8088)       → 127.0.0.1 only
A-FORGE MCP (:7072)      → 127.0.0.1 only
Public-facing: Cloudflare tunnel → internal 127.0.0.1
```

### 2. Signed SOT Manifest at Startup

On every WEALTH server startup:

```bash
# Generate manifest hash at startup
python3 -c "
import hashlib, json, os
files = [
  '/root/WEALTH/wealth_mcp/server.py',
  '/root/WEALTH/contracts/*.schema.json',
  '/root/WEALTH/wealth_mcp/prompts/*.md',
]
manifest = {'version': '2026.06.27', 'files': {}, 'signed_at': ''}
for pattern in files:
    for path in glob.glob(pattern):
        with open(path) as f:
            manifest['files'][path] = hashlib.sha256(f.read().encode()).hexdigest()
print(json.dumps(manifest, indent=2))
"
```

Compare hash against last known good. If mismatch → log alert, continue with degraded flag.

### 3. Short-Lived HMAC Invocation Tokens

For non-local calls (cross-service within VPS):

```python
import hmac, hashlib, time

HMAC_SECRET = os.environ.get("WEALTH_INVOKE_SECRET")  # Set in systemd env
TOKEN_TTL_SECONDS = 300  # 5 minutes

def sign_invoke(payload: dict) -> str:
    """Sign a WEALTH tool invocation payload with HMAC-SHA256."""
    nonce = str(int(time.time() // TOKEN_TTL_SECONDS))
    msg = json.dumps(payload, sort_keys=True) + nonce
    sig = hmac.new(HMAC_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{nonce}.{sig}"

def verify_invoke(token: str, payload: dict) -> bool:
    """Verify HMAC token is unexpired and authentic."""
    nonce, sig = token.split(".")
    if int(time.time() // TOKEN_TTL_SECONDS) - int(nonce) > 2:
        return False  # Expired or replayed
    msg = json.dumps(payload, sort_keys=True) + nonce
    expected = hmac.new(HMAC_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)
```

**Not full OAuth 2.1.** HMAC tokens are P1 for a bare-VPS reality.
OAuth 2.1 remains P2 when/if a managed auth service is added.

### 4. Schema Hash Verification

Before processing any federation envelope, verify:

```python
def verify_envelope(envelope: dict) -> bool:
    # 1. Schema is known
    assert envelope["artifact_kind"] in ARTIFACT_KINDS
    # 2. trace_id is present and non-empty
    assert envelope["trace_id"]
    # 3. manifest_hash is present
    assert envelope["manifest_hash"]
    # 4. created_at is recent (not replay)
    age_seconds = time.time() - parse_iso(envelope["created_at"]).timestamp()
    assert age_seconds < 3600, "Envelope older than 1 hour"
    return True
```

### 5. Allowlist for MCP Clients

Only registered MCP clients can call WEALTH tools:

```python
ALLOWED_CLIENTS = {
    "arifos-kernel": {"organs": ["arifOS"], "tiers": ["TIER_1", "TIER_2", "TIER_3"]},
    "a-forge": {"organs": ["A-FORGE"], "tiers": ["TIER_1", "TIER_2"]},
    "hermes": {"organs": ["AAA"], "tiers": ["TIER_1"]},
    "opencode": {"organs": ["AAA"], "tiers": ["TIER_1"]},
}
```

No organ can call WEALTH at a higher TIER than its allowlist entry.

### 6. 888_HOLD Before Mutation

All TIER_3 actions (vault write, arifOS submit, capital authorization) require:

```python
def require_888_hold(intent: str, blast_radius: str) -> bool:
    if blast_radius in ["HIGH", "CRITICAL"]:
        return True
    if intent in ["vault_write", "capital_authorize", "public_claim"]:
        return True
    return False
```

WEALTH prepares the envelope. WEALTH never self-authorizes.

### 7. Append-Only Replay Receipts

Every cross-organ workflow emits a receipt:

```
/root/VAULT999/wealth/receipts.jsonl
```

Format: one JSON object per line, one line per workflow completion.

```json
{"trace_id": "trace-001", "step": "WEALTH::emv_compute", "actor": "WEALTH", "outcome": "PASS", "inputs": [...], "outputs": [...], "epistemic_grade": "DER", "timestamp": "2026-06-27T12:00:00Z"}
```

Immutability: VAULT999 is append-only. No delete, no update.

---

## Security Not Done (P2)

These are architecturally sound but deferred to P2:

| Item | Why Deferred |
|------|-------------|
| OAuth 2.1 (PKCE, dynamic client registration) | Requires managed auth service not present on bare VPS |
| Full DID / Verifiable Credentials | Overkill for 7-organ operator-controlled federation |
| Hardware HSM for signing keys | Not yet justified by threat model |
| Mutual TLS | Cloudflare handles TLS termination at edge |

---

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Unauthorized external call | Cloudflare gate + local bind |
| Replay attack (old envelope) | Timestamp check + nonce |
| Tampering with envelope | HMAC signature |
| WEALTH self-authorizing T3 | 888_HOLD enforced server-side |
| Stale tool surface used | Startup manifest hash comparison |
| Open MCP port scanned | 127.0.0.1 bind only |
| Secret in environment variable | Use systemd `LoadCredentialEncrypted=` or Vault |

---

## Audit Trail

Every consequential action leaves a trace:

1. **Reception:** Federation envelope received, schema verified
2. **Processing:** Tool called, inputs logged (not values), epistemic grade assigned
3. **Output:** Artifact emitted with grade, receipts written
4. **Handoff:** arifOS envelope built, hold status declared

VAULT999 receives `replay_receipt` on every terminal decision.

arifOS kernel (`arifOS:8088`) is the constitutional auditor. WEALTH is a governed instrument, not its own auditor.
