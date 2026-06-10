# WEALTH MONOLITH SPLIT — Forge Plan
> **Status:** IN PROGRESS — Domain structure created, POC pending
> **Owner:** Ω · **Date:** 2026-06-10 · **Estimate:** 3-4h remaining

## PHASE 1: Domain Structure (DONE ✅)
```
/root/WEALTH/internal/domains/
├── capital/         ← conservation, flow, gradient, entropy (Ω-01 through Ω-04)
├── time/            ← NPV, IRR, payback, compounding, discount (Ω-06)
├── signal/          ← EVOI, information value, coupling (Ω-09)
├── field/           ← macro, FX, commodities (Ω-08, D3)
├── personal/        ← personal finance, EPF, zakat (D1)
├── stock/           ← D4 stock analysis (already modular)
├── registry/        ← system registry, health, contracts
└── shared/          ← config, database, base models, exceptions
```

## PHASE 2: Move Tool Implementations (3h)

### Step 1: Extract personal_finance domain (30min)
- Move: `wealth_personal_finance`, `wealth_cashflow_track`, `wealth_cashflow_summary`, 
  `wealth_net_worth_snapshot`, `wealth_epf_project`, `wealth_zakat_calculate`
  → `domains/personal/personal_finance.py`
- In monolith.py: `from internal.domains.personal import personal_finance_handler`

### Step 2: Extract capital domain (45min)
- Move: `wealth_conservation_capital`, `wealth_flow_liquidity`, `wealth_gradient_price`,
  `wealth_entropy_risk`, `wealth_energy_productivity`
  → `domains/capital/` (one file per sub-domain or one service.py)
- These are the Ω-WEALTH-01 through Ω-WEALTH-05 tools

### Step 3: Extract time domain (30min)
- Move: `wealth_time_discount`, `wealth_inertia_leverage`, NPV, IRR, MIRR
  → `domains/time/`

### Step 4: Extract signal domain (30min)
- Move: `wealth_signal_information`, `wealth_signal_evoi`, `wealth_signal_evoi_mc`,
  `wealth_evoi_compute`, `wealth_evoi_monte_carlo`, `wealth_correlation_guard_check`
  → `domains/signal/`

### Step 5: Extract field domain (20min)
- Move: `wealth_field_macro`, `wealth_market_data`, `wealth_fx_rate`,
  `wealth_commodity_price`, `wealth_macro_indicator`
  → `domains/field/`

### Step 6: Extract registry domain (20min)
- Move: `wealth_system_registry_status`, `wealth_health_check`, `mcp_server_card`
  → `domains/registry/`

### Step 7: monolith.py becomes thin entry point (15min)
- Keep: imports, FastMCP server init, tool registration glue
- All tool handlers import from domain modules
- Target: monolith.py < 2000 lines (down from 16022)

## PHASE 3: OrganBaseModel Migration (30min)
- Replace `from pydantic import BaseModel` with `from internal.shared.base import OrganBaseModel`
- In all domain modules and monolith.py
- Run test suite: `pytest tests/ -q` (153 tests, must stay green)

## PHASE 4: Test & Deploy (30min)
```bash
cd /root/WEALTH
pytest tests/ -q --tb=short          # all 153 must pass
python internal/monolith.py &        # start server
sleep 2
curl http://localhost:18082/health   # must return healthy
curl -X POST http://localhost:18082/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']['tools']))"
  # must return 20
kill %1
```

## PHASE 5: Git & Push (15min)
```bash
git add -A
git commit -m "refactor(wealth): split monolith into domain modules

- Domain modules: capital, time, signal, field, personal, stock, registry
- Shared OrganBaseModel for Pydantic v2 consistency
- monolith.py reduced from 16K to ~2K lines (entry point only)
- All 153 tests passing, 20-tool surface unchanged"
git tag v2026.06.11 -m "WEALTH monolith domain split"
git push origin main --tags
```

## RISK MITIGATION
- **Rollback:** `git revert HEAD` restores monolith.py as single file
- **Test first:** Run `pytest tests/ -q` before AND after each step
- **Atomic commits:** One commit per domain. Easy to revert individual domains.
- **Keep aliases:** All 34 hidden aliases must still route correctly

## CURRENT STATE (Before Split)
```
monolith.py:          16,022 lines
Public tools:         20 (+ 34 aliases)
Tests:                153 passing
Test coverage:        44%
```

## TARGET STATE (After Split)
```
monolith.py:          ~2,000 lines (entry point)
domains/capital/:     ~2,500 lines
domains/time/:        ~1,500 lines
domains/signal/:      ~2,000 lines
domains/field/:       ~1,500 lines
domains/personal/:    ~2,000 lines
domains/stock/:       ~2,800 lines (unchanged)
domains/registry/:    ~800 lines
domains/shared/:      ~150 lines
Total:                ~16,000 lines (same logic, better organized)
Tests:                153 passing (same)
```

---

*DITEMPA BUKAN DIBERI — Forged, Not Given.*
