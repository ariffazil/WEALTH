# WEALTH Monolith Split Plan

> **Version:** 2026.06.14  
> **Status:** PLANNED — not executed  
> **Target:** Split `internal/monolith.py` (17,302 lines, 25+ tools) into modular `internal/engines/`  
> **Doctrine:** DITEMPA BUKAN DIBERI

---

## Rationale

The monolith has grown to 17,302 lines across 25+ public MCP tools plus ~50 internal helper functions. This is structurally sound for a kernel but creates:

1. **Merge conflicts** — every PR touches the same file
2. **Cognitive load** — even the author can't hold 17K lines in working memory
3. **Import coupling** — a change to one engine can break others via shared globals
4. **Test isolation** — can't test `wealth_gradient_price` without loading the entire kernel

The split addresses all four without changing the public API.

---

## Phase Plan (7 Phases, Ordered by Risk)

### Phase 1: Survival Engine (LOWEST RISK)

**Files:** `engines/survival.py` ← `wealth_survival_engine` (lines 4907–5268)

Has few external dependencies. Extracts cleanly.

**Dependencies pulled:** `wealth_flow_cashflow`, `wealth_velocity_runway`, `wealth_gravity_dscr`, `wealth_mass_networth` (these are already REMOVED from public surface).

**Success check:** All existing tests pass. `wealth_survival_engine` callable on port 18082.

### Phase 2: Gradient + Conservation (LOW RISK)

**Files:**
- `engines/gradient.py` ← `wealth_gradient_price` (lines 11642–11654)
- `engines/conservation.py` ← `wealth_conservation_capital` (lines 11581–11610)

Pure math: spread calculation, net worth summation. No external API calls. These are the safest to move because they don't import `host.governance.vault_supabase` or similar heavy deps.

**Internal engine functions to extract alongside:**
- `_gradient_spread`, `_gradient_pressure`, `_gradient_mispricing`
- `networth_state`, `snapshot_portfolio_tool`

### Phase 3: Time + Energy + Entropy (MEDIUM RISK)

**Files:**
- `engines/time.py` ← `wealth_time_discount` (lines 11971–11997)
- `engines/energy.py` ← `wealth_energy_productivity` (lines 11800–11970)
- `engines/entropy.py` ← `wealth_entropy_risk` (lines 11657–11970)

Medium risk because these depend on:
- `npv_reward`, `irr_yield`, `payback_time`, `emv_risk`, `pi_efficiency`
- `build_cashflow_series`, `measurement_npv`, `measurement_irr`, `measurement_emv`
- `measurement_validate_invariants`, `weakest_epistemic`
- `create_envelope` (THE critical shared function)

**Critical dependency:** `create_envelope` (line ~3652) — used by EVERY tool. Must remain in monolith.py or be extracted to its own `_envelope.py` module.

**Recommendation:** Move `npv_reward`, `irr_yield`, `payback_time`, `emv_risk`, `pi_efficiency` into the new engine files alongside their callers. Keep `create_envelope` in `monolith.py` or extract to `engines/_envelope.py`.

### Phase 4: Field + Signal + Game + Boundary (HIGHER RISK)

**Files:**
- `engines/field.py` ← `wealth_field_macro` (lines 12096–12298)
- `engines/signal.py` ← `wealth_signal_information` (lines 12299–12467)
- `engines/game.py` ← `wealth_game_coordination` (lines 12468–12547)
- `engines/boundary.py` ← `wealth_boundary_governance` (lines 12548–12993)

Higher risk because:
- `wealth_field_macro` makes HTTP calls to World Bank / Frankfurter APIs
- `wealth_signal_information` calls EVol computation with Monte Carlo
- `wealth_boundary_governance` has 888_HOLD logic that touches constitutional floors

### Phase 5: Omni Wisdom + Inequality (HIGHEST RISK)

**Files:**
- `engines/omni_wisdom.py` ← `wealth_omni_wisdom` (lines 13250–14786)
- `engines/inequality.py` ← `wealth_inequality_kernel` (lines 15402–15645)

`wealth_omni_wisdom` is the largest single tool (~1,500 lines), with three sub-engines (synthesize, deal_frame, hysteresis_ledger). It must be last because it depends on every other engine.

### Phase 6: Convert monolith.py to Import Facade

After all tools are extracted, `monolith.py` becomes:

```python
"""WEALTH MCP Kernel — Import Facade.
All tools live in internal/engines/. This file re-exports them
for backward compatibility and FastMCP assembly.
"""
from __future__ import annotations
from .engines.conservation import wealth_conservation_capital
from .engines.flow import wealth_flow_liquidity
from .engines.gradient import wealth_gradient_price
from .engines.entropy import wealth_entropy_risk
# ... etc.
```

**Critical design:**
- `mcp` (FastMCP app instance) stays in `monolith.py`
- Tool registration stays in `monolith.py`
- Each engine module imports `mcp` via `from ..monolith import mcp` or via a shared `_app.py`

### Phase 7: Full Test Suite + Seal

**Exit criteria:**
```bash
pytest tests/ -q --tb=short              # All 25+ tests pass
python -c 'from internal.monolith import mcp; print(mcp.list_tools())'  # All tools present
curl -s http://localhost:18082/health | python3 -m json.tool  # Service healthy
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Circular imports between engines | Tools stop loading | Extract `create_envelope` first; keep `_envelope.py` import-free |
| `host.governance.vault_supabase` import fails | Ledger tools break | Keep vault tools in monolith until last phase |
| Monolith's `_PUBLIC_TOOLS` set out of sync | Registry drift | Auto-generate from engine `__init__.py` exports |
| `mcp` object not shared between modules | Tools not registered | Use shared `_app.py` module or import from monolith |
| Tests pass on branch but fail on main after merge | Blocked deploy | Run full test suite on merge commit before deploy |

---

## Shared Dependencies (Must Stay or Move First)

| Function | Lines | Used By | Recommendation |
|----------|-------|---------|----------------|
| `create_envelope` | 3652–3800 | ALL tools | Extract to `engines/_envelope.py` FIRST |
| `_normalize_primitive_envelope` | 7250–7300 | Several tools | Extract with create_envelope |
| `_clean_payload` | ~11400 | Several tools | Extract with create_envelope |
| `_dispatch_invariant_tool` | 11550–11578 | gradient, time, hysteresis | Extract in Phase 2 |
| `_dispatch_emergence` | 11204–11549 | conservation, flow | Extract in Phase 2 |
| `_invariant_dispatch_registry` | 11524–11543 | dispatch tools | Extract with dispatch |
| `mcp` (FastMCP instance) | ~50 | ALL tools | Stays in monolith.py |
| `WEALTH_PUBLIC_TOOL_ORDER` | 15887–15928 | Registry | Stays in monolith.py |
| `_PUBLIC_TOOLS` | 15929 | Registry | Stays in monolith.py |

---

## Timeline Estimate

| Phase | Effort | Lines Changed | Risk |
|-------|--------|---------------|------|
| 0: Extract `_envelope.py` | 1 session | ~200 | Critical (pre-requisite) |
| 1: Survival | 1 session | ~400 | Low |
| 2: Gradient + Conservation | 1 session | ~300 | Low |
| 3: Time + Energy + Entropy | 2 sessions | ~1,200 | Medium |
| 4: Field + Signal + Game + Boundary | 2 sessions | ~2,000 | Medium-High |
| 5: Omni Wisdom + Inequality | 2 sessions | ~3,000 | High |
| 6: Convert to facade | 1 session | ~100 | Medium |
| 7: Test + Seal | 1 session | ~50 | Low |

**Total:** ~11 sessions, ~7,250 lines changed, ~7,000 lines removed from monolith.py.

---

## Executable Reference

The file `scripts/split_monolith.sh` contains the exact extraction map with line ranges and target filenames.

```bash
bash scripts/split_monolith.sh  # Shows plan (does NOT extract)
```

**Do not execute the split without 888_HOLD approval.** This is a production service.
