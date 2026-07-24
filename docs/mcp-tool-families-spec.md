# WEALTH MCP Tool Families — Current Repo SOT

> **Version:** 2026.07.24
> **Status:** ACTIVE REPO STATE
> **Epistemic:** CLAIM
> Runtime `tools/list` remains final truth.

## 1. Runtime split

| Surface | File | Purpose |
|---|---|---|
| Canonical federated runtime | `server_federated.py` → `wealth_mcp/server.py` | Public 12-tool WEALTH surface |
| Civilizational demo surface | `mcp/server.py` | Secondary six-tool market/energy/food/prospect demo |
| Legacy implementation library | `internal/monolith.py` | Compatibility implementations; not the public entrypoint |

## 2. Public 12-tool surface

### Canonical capital family (8)

| Tool | Family |
|---|---|
| `capital_primitive` | deductive capital math |
| `capital_health` | conservation, flow, runway, survival |
| `capital_diagnose` | institutional diagnostics |
| `capital_wisdom` | advisory wisdom synthesis |
| `capital_market` | market observation |
| `capital_ledger` | read/write ledger; write is C2/IRREVERSIBLE |
| `capital_registry` | introspection and health |
| `capital_entropy` | optional entropy-integrity analysis |

### Institutional compatibility family (4)

- `wealth_institutional_stress_index`
- `wealth_cascade_model`
- `wealth_governance_capacity`
- `wealth_external_exploitation_detect`

These four tools remain public compatibility entrypoints for direct institutional analysis. They do not increase WEALTH's authority.

## 3. Civilizational demo family

`mcp/server.py` remains real but supplemental:

- `wealth_evaluate_prospect`
- `markets_analyze_ticker`
- `markets_portfolio_stress_test`
- `energy_crisis_assess`
- `energy_shortage_predict`
- `food_security_index`

## 4. Truth and governance

- `tools/list` beats static registry counts.
- `capital_registry` reports both 8 canonical capital tools and 12 total public tools.
- `capital_ledger(mode="query")` is read-only.
- `capital_ledger(mode="write")` requires C2 arifOS `SEAL` and `ack_irreversible=true`.
- `capital_entropy` must return structured `UNAVAILABLE`, never fabricated output, when its local optional dependency is absent.

## 5. Failure modes

| Failure | Mitigation |
|---|---|
| Wrong entrypoint assumption | Use `server_federated.py` for production integrations |
| Stale count in prose | Probe `tools/list`; declared count is 12 |
| Demo promoted as kernel | Keep `mcp/server.py` explicitly supplemental |
| Unconfirmed persistence reported as success | Surface receipt/ledger persistence state and omit invented IDs or hashes |
