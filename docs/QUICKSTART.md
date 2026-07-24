# WEALTH Quickstart — 15 Minutes to Running Locally

> WEALTH is the compute-only capital intelligence organ. It computes; arifOS judges; Arif decides.

## What You'll Have

A FastMCP server on `http://localhost:18082` advertising 12 tools: 8 mode-dispatched `capital_*` tools plus 4 institutional compatibility tools.

## Prerequisites

- Python 3.12+
- `uv` or `pip`

## Start

```bash
git clone https://github.com/ariffazil/wealth.git
cd wealth
uv sync --frozen
python server_federated.py
```

## Verify

```bash
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
curl -s http://127.0.0.1:18082/tools | python3 -m json.tool
```

`/tools` is the runtime source of truth and should list 12 names.

## Public Tools

### Canonical capital family

- `capital_primitive` — NPV, IRR, EMV, EVOI, Monte Carlo, portfolio optimization
- `capital_health` — conservation, flow, runway, survival, fiscal breakeven
- `capital_diagnose` — institutional stress, governance, cascade, collapse, power
- `capital_wisdom` — advisory wisdom and epistemic synthesis
- `capital_market` — FX, commodities, indicators, stocks
- `capital_ledger` — query; C2/IRREVERSIBLE write requires arifOS SEAL and acknowledgment
- `capital_registry` — status, schema, domains, health
- `capital_entropy` — optional entropy-integrity analysis; structured UNAVAILABLE if dependency is absent

### Institutional compatibility family

- `wealth_institutional_stress_index`
- `wealth_cascade_model`
- `wealth_governance_capacity`
- `wealth_external_exploitation_detect`

## Local Test

```bash
pytest tests/ -q --tb=short
```

## Common Issues

| Symptom | Fix |
|---|---|
| Port 18082 in use | Stop the conflicting process or set the configured WEALTH port before startup |
| `capital_entropy` reports `ENTROPY_MODULE_MISSING` | The optional dependency is absent from this repo; do not treat the result as computed |
| Ledger write returns HOLD | Provide a valid arifOS session/SEAL and `ack_irreversible=true` |
| Receipt target unavailable | Provision the configured JSONL target; WEALTH will not create it silently |

## Next Steps

- Read `README.md` for the human overview.
- Read `docs/TOOL_MODE_MAP.md` for modes.
- Read `contracts/tools.yaml` for the machine-readable surface.
- Read `docs/WEALTH_SOT.md` for runtime identity and authority.

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
