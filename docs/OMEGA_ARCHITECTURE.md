# The Ω Architecture — full reference
> **Moved verbatim from README.md** (the full table + L11 AUTH gate detail) during the
> AGENTIC-README-DOCTRINE v1 restructure, 2026-10-16. Source archive:
> `docs/archive/README-2026-10-16-pre-doctrine.md`.

## Twelve invariants, one synthesis primitive

| Ω    | Invariant | Question | Canonical name | Implementation |
|------|-----------|----------|----------------|----------------|
| Ω00  | Synthesis | Cross-dimensional roll-up → domain_assessment | `wealth_synthesize` | 12→1 roll-up; ADVISORY_ONLY |
| Ω01  | Mass      | What exists? | `wealth_conservation_capital` | assets / liabilities / reserves |
| Ω02  | Flow      | Where is money moving? | `wealth_flow_liquidity` | cash flow / burn / runway |
| Ω03  | Gradient  | What differential drives movement? | `wealth_gradient_price` | price pressure / spreads |
| Ω04  | Entropy   | How uncertain / disordered is it? | `wealth_entropy_risk` | tail risk / disorder |
| Ω05  | Energy    | What output does capital produce? | `wealth_energy_productivity` | output per capital input |
| Ω06  | Time      | What is future value worth now? | `wealth_time_discount` | NPV / IRR / decay |
| Ω07  | Inertia   | What makes the system hard to change? | `wealth_inertia_leverage` | leverage / fragility |
| Ω08  | Field     | What macro regime surrounds it? | `wealth_field_macro` | rates / FX / energy |
| Ω09  | Signal    | What information deserves belief? | `wealth_signal_information` | evidence quality / information value |
| Ω10  | Game      | What incentives shape behaviour? | `wealth_game_coordination` | incentives / bargaining |
| Ω11  | Boundary  | What constraints cannot be crossed? | `wealth_boundary_governance` | governance / stewardship |
| Ω12  | Hysteresis | How does history constrain the future? | `wealth_hysteresis_ledger` | path dependence / capital memory |

**Ω00 is a synthesis primitive, not a thirteenth domain invariant** — it rolls the twelve
up into one `domain_assessment`. The Ω invariants are the *fundamentals*. NPV, RSI, MACD,
Bollinger, PSAR, ATR, ADX, backtest, and entry planning are market-microstructure
implementations underneath Ω08 (Field) and Ω09 (Signal).

## Capability surface (arithmetic, restated)

- 13 canonical primitives (Ω00 + Ω01–Ω12)
- 2 societal extensions (inequality, role scarcity)
- 2 infrastructure capabilities (health, registry)
- 14 legacy aliases (`capital_*` names) — **excluded from the canonical count**

**Canonical visible surface: 17** (declared). Live `tools/list` reports **18** (probe
2026-10-16) — declared-vs-live difference is an open gap row in the README.

## L11 AUTH gate (P1 fix)

Direct `:18082` connector previously required `session_id` for every tool, including
diagnostic reads. P1 restores OBSERVE-class exemptions:

- `capital_market`, `capital_registry`, `capital_primitive`, `capital_entropy`,
  `capital_indicator`, `capital_backtest`, `capital_entry_plan`, `capital_claims`,
  `capital_diagnose`, `capital_health`, `capital_polix`, `capital_civx`,
  `wealth_synthesize` — and their legacy aliases — pass without a session.
- MUTATE tools (`capital_ledger`, `wealth_judge_handoff`) still require a verified session.
