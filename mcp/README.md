# WEALTH MCP Surfaces

This repo ships **two** MCP servers. They are not interchangeable.

## 1. Canonical packaged kernel

- **File:** `server.py`
- **Role:** Primary WEALTH valuation kernel
- **Used by:** `package.json`, `fastmcp.json`, `mcp.json`, `Dockerfile`
- **Scope:** 29 tools + 2 resources

Run it with:

```bash
cd /root/WEALTH
python server.py
```

This is the source of truth for the packaged WEALTH MCP runtime.

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

If you are wiring WEALTH into another system and need the **real packaged kernel**, use **`server.py`**.

If you are experimenting with domain-specific civilizational demos, use **`mcp/server.py`**.
