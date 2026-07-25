# Contributing to WEALTH

> **SOT:** 2026-07-25 | **DITEMPA BUKAN DIBERI**

WEALTH is the capital intelligence organ of the arifOS Federation. It computes financial math — never allocates capital, never issues verdicts.

## Before You Start

1. Read the [README](README.md) — understand CAPITAL_LAW: compute, never allocate
2. Run `curl :18082/health` — ensure WEALTH is running

## Setup

```bash
git clone git@github.com:ariffazil/WEALTH.git && cd WEALTH
pip install -e ".[dev]"
python server_federated.py   # starts on :18082
curl http://localhost:18082/health
```

## Making Changes

1. **Fork → Branch → Edit → Test → PR**
2. Run `pytest tests/ -q --tb=short` before pushing
3. Run `npm test` for Node.js side tests
4. All primitives must be golden-tested against hand-checked cases

## Boundaries

- WEALTH computes — never allocates capital
- WEALTH models — never issues investment verdicts
- `capital_ledger(mode="write")` is C2/IRREVERSIBLE
- Every output tagged OBS/DER/INT/SPEC

## Federation

WEALTH is one of 7 organs. See [ariffazil/ariffazil](https://github.com/ariffazil/ariffazil) for the federation map.

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
