# 🔀 Agentic Routing Doctrine — WEALTH Federation

> **DITEMPA BUKAN DIBERI** — Forged, not given.
> Every agent reasons from **semantic capabilities**, not ports, IPs, or provider APIs.

---

## 1. Four Action Classes

Every intent falls into one class:

| Class | Examples | Route | Governance |
|-------|----------|-------|------------|
| **A — Read** | ticker, health, documentation, registry | Agent → domain organ | None |
| **B — Compute** | NPV, EMV, RSI, volumetrics, transmission | Agent → domain organ | Label DERIVED |
| **C — Interpret** | macro diagnosis, scenario, risk assessment | Agent → domain → synthesis | Advisory only |
| **D — Act** | deploy, publish consequential claim, mutate | Evidence → arifOS → Human → A-FORGE | Full chain |

---

## 2. Semantic Owner Map

| Intent | Correct Organ | MCP Tool | Risk |
|--------|--------------|----------|------|
| Market data, capital, macro | **WEALTH**:18082 | `capital_market` | Read/Compute |
| Geology, seismic, basins | **GEOX**:8081 | `geox_basin`, `geox_prospect` | Read/Compute |
| Human readiness, fatigue | **WELL**:18083 | `well_validate_vitality` | Interpret |
| Authority, judgment, seal | **arifOS**:8088 | `arif_judge`, `arif_seal` | Governed |
| Deployment, mutation | **A-FORGE**:7071 | `forge_*` | Mutate |
| State, routing, display | **AAA**:3001 | A2A gateway | Display |
| Immutable receipt | **VAULT999** | via arifOS | Record |

---

## 3. Agent Protocol

```
1. INIT — arif_init (bind identity)
2. DISCOVER — tools/list on relevant organ (never assume)
3. CLASSIFY — A/B/C/D action class
4. CALL — organ tool with stable semantic params
5. VERIFY — check status, freshness, epistemic class
6. HOLD if — stale, conflicted, authority missing, irreversible
7. JUDGE if — Class D or consequential Class C
8. SEAL if — irreversible or published
```

---

## 4. WEALTH Output Envelope

Every WEALTH tool returns this standard envelope:

```json
{
  "status": "OK",
  "tool": "capital_market",
  "domain": "wealth",
  "operation": "gold.snapshot",
  "result": {},
  "epistemic": {
    "class": "OBSERVED|DERIVED|INTERPRETED",
    "confidence": 0.0
  },
  "evidence": {
    "sources": [],
    "fetched_at": null,
    "freshness": "CURRENT|STALE|UNKNOWN",
    "conflicts": []
  },
  "authority": {
    "scope": "ADVISORY",
    "execution_authorized": false
  },
  "runtime": {
    "schema_version": "1.0.0",
    "source_commit": null
  },
  "errors": []
}
```

---

## 5. Engine Health Model

```
GET /health → {
  "status": "HEALTHY|DEGRADED|DOWN",
  "process": "HEALTHY",
  "transport": "HEALTHY",
  "dependencies": {
    "upstream": "HEALTHY|DEGRADED"
  },
  "data_freshness": "CURRENT|STALE|UNKNOWN",
  "source_commit": "e55b260",
  "uptime": 3600
}

GET /identity → {
  "service": "gold",
  "repo": "github.com/ariffazil/WEALTH",
  "commit": "e55b260",
  "engine_version": "1.0.0"
}
```

---

## 6. Error Doctrine

| Condition | Response | Behaviour |
|-----------|----------|-----------|
| Unknown asset | `UNKNOWN_ASSET` | Fail-closed |
| Unknown operation | `UNKNOWN_OPERATION` | List allowed ops |
| Engine timeout | `ENGINE_FAILURE` | Return degraded |
| Invalid input | `INVALID_ARGUMENT` | Schema error |
| Never silently substitute | — | Always explicit |

---

## 7. Cross-Organ Workflows

### Malaysia Macro Intelligence
```
AAA/intent → WEALTH/macro → GEOX(energy) → WELL(consequence) → arifOS(publish?) → ARIF
```

### Prospect Economics
```
GEOX/uncertainty → WEALTH/NPV+EMV → arifOS/admissibility → ARIF/decision
```

### Infrastructure Change
```
A-FORGE/plan → arifOS/judge → ARIF/approve → A-FORGE/execute → VAULT999/receipt
```

---

## 8. Anti-Patterns

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Call port 3456 directly | Use `capital_market(mode="gold")` |
| Hardcode API paths | Discover via `tools/list` |
| Assume tool exists | Verify runtime surface |
| Treat INTERPRETED as fact | Distinguish epistemic class |
| Skip arif_judge for Class D | Always route through governance |
| Use LLM description as security | Enforce in server code |
