# Trading Stack → WEALTH Migration

**Migrated:** 2026-07-19
**Source:** `/root/trading/` (deleted)
**Sovereign:** 888_AUTHORIZED

## What was preserved

| Module | Files | Why |
|--------|-------|-----|
| **APEX predictor** | `apex/apex_predictor.py`, `apex/regime.py`, `apex/scanner.py` | Novel APEX theory applied to markets. G·C_dark·W³ framework. Multi-TF witness. |
| **Risk engine** | `risk/manager.py`, `risk/position_sizer.py` | Kelly criterion, drawdown tracking, position caps |
| **Governance** | `governance/gate.py`, `governance/GoldConstitutionalInvariants.md` | F1-F13 floors mapped to trading rules. Constitutional gate via arifOS |
| **Core** | `core/config.py`, `core/models.py`, `core/journal.py` | Frozen config + epistemic models (OBS/DER/INT/SPEC) |
| **Config** | `config/trading_spec.json` | Canonical XAUUSD trading spec |
| **Backtest** | `backtest/engine_v2.py`, `backtest/engine.py` | Event-driven backtest framework |
| **Cron** | `cron/hourly_scan.py`, `cron/weekly_report.py` | Live WEALTH MCP integration pattern |
| **Docs** | `ARCHITECTURE.md`, `FEDERATION_REGISTRATION.md`, `README.md` | Design reference |
| **Reference** | `reference/red-news-impact.md` | Trading knowledge base |

## What was NOT preserved (redundant/outdated)

- `signals/engine.py` (v1, superseded)
- `signals/technical.py` (duplicates scanner)
- `data/*` (sample data, logs)
- `cron/*.json` (historical scan output)
- `lib/`, `lib64/` (embedded Python venv, 1GB)
- `test_*.py` (scaffold tests)

## Integration path

These modules are WEALTH primitives — market intelligence IS capital intelligence.
To activate, wire the governance gate to `wealth_capital_wisdom` and restore the
WEALTH MCP bridge in `cron/hourly_scan.py`.
