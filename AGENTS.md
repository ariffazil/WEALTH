<!-- CANONICAL: /root/AGENTS.md -->
<!-- Status: DERIVED — organ-specific extension. Authoritative doctrine: /root/AGENTS.md -->

<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-24
valid_from: 2026-07-24
valid_until: 2026-08-17
confidence: high
scope: /root/WEALTH
-->

# AGENTS.md — WEALTH | arifOS Federation

> **Capital intelligence — computes, never allocates.**
> arifOS judges. A-FORGE executes. WEALTH observes and computes.
> **ZEN:** `/root/AAA/prompts/AAA-ZEN-ALIGNMENT.md` — 18 operational rules. Load at boot.

## Identity
Canonical capital engine. Port 18082. Public MCP surface: 12 tools total — 8 mode-dispatched `capital_*` tools plus 4 institutional compatibility tools. The canonical family is capital_primitive, capital_health, capital_diagnose, capital_wisdom, capital_market, capital_ledger, capital_registry, capital_entropy.

## Build & Test
```bash
pip install -e .
pytest tests/ -q --tb=short
```

## Boundary
✅ Compute NPV, IRR, EMV, risk, market data, portfolio
❌ Never allocate capital — that's Arif's domain
❌ Never issue SEAL/verdict — that's arifOS
