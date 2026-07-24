# WEALTH MCP Surfaces

This repo ships two MCP surfaces. They are not interchangeable.

## 1. Canonical federated runtime

- **Entrypoint:** `server_federated.py`
- **FastMCP registration:** `wealth_mcp/server.py`
- **Role:** Public WEALTH capital intelligence runtime
- **Scope:** 12 public tools — 8 `capital_*` tools plus 4 institutional compatibility tools
- **Truth:** authenticated `tools/list`

Run it with:

```bash
cd /root/WEALTH
python server_federated.py
```

`internal/monolith.py` remains a legacy implementation library used by compatibility paths and tests. It is not the public entrypoint and must not be deleted.

## 2. Civilizational demo surface

- **File:** `mcp/server.py`
- **Role:** Secondary FastMCP demo for markets, energy, food, and prospect economics
- **Scope:** 6 tools + 3 resources

Run it with:

```bash
cd /root/WEALTH
python mcp/server.py
```

Current demo tools:

- `wealth_evaluate_prospect`
- `markets_analyze_ticker`
- `markets_portfolio_stress_test`
- `energy_crisis_assess`
- `energy_shortage_predict`
- `food_security_index`

## Practical rule

Use `server_federated.py` for production WEALTH integrations. Use `mcp/server.py` only for the supplemental demo surface. Never infer the live tool count from `internal/monolith.py`; probe `tools/list`.
