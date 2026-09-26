# M7 — Survival and Path-Risk

> **M7 does not predict gold. It decides whether a forecast can SAFELY
> become a position.**

## Mission

`SURVIVE_THE_PATH`. The single constraint:

```
P(margin breach before thesis resolution) < alpha
```

Given an M5 distribution + a candidate position, M7 emits one of:

| Verdict | Meaning                                                              |
|---------|----------------------------------------------------------------------|
| ACT     | Proceed at the proposed size (or Kelly-scaled size).                  |
| REDUCE  | Proceed only at reduced size (`size_multiplier < 1`).                  |
| HOLD    | Do not act now (insufficient evidence / data missing).                |
| BLOCK   | Refuse — survival probability is below alpha.                         |

## Authority

```python
M7_AUTHORITY = {
    "may_reduce_size": True,
    "may_block_trade": True,
    "may_increase_size": False,    # sovereign's call only
    "may_override_human": False,   # sovereign decides
}
```

M7 may shrink a position or refuse a trade. It may never grow a
position and may never override a human.

## Inputs

| Input | Source | Notes |
|---|---|---|
| `m5_forecast` | `m5/latest_forecast.json` or `run_m5()` output | required |
| `side`, `entry`, `stop`, `target` | proposed position | absolute prices |
| `leverage`, `margin_buffer` | proposed risk | leverage multiple / fraction distance to margin call |
| `notional_usd`, `equity_usd` | account | required for liquidation cost + Kelly sizing |
| `spread_bps`, `slippage_bps`, `adv_usd` | market state | defaults are explicit synthetic XAUUSD values |
| `max_acceptable_loss_usd` | user-defined ceiling | hard BLOCK if CVaR exceeds it |
| `f_signal`, `t_signal`, `d_signal` | F/T/D organ signals | in `[-1, +1]` |
| `disagreement_series` | historical magnitudes | for M7.6 half-life |
| `edge_log`, `sigma_log` | per-period log-return | for Kelly sizing |
| `horizon_h` | 1 / 6 / 24 / 72 | M5 horizon label |
| `alpha` | default 0.10 | constraint threshold |

## Outputs

```
probability_of_margin_breach     # in [0, 1]
probability_of_stop_before_target # in [0, 1]
expected_shortfall                # CVaR in price units (positive)
liquidation_cost_bps              # round-trip
liquidation_cost_usd              # round-trip
maximum_survivable_size_usd       # Kelly × survival
thesis_half_life_bars             # autocorrelation decay (NaN if insufficient)
size_multiplier                   # final, in [0, 1]
verdict                           # ACT | REDUCE | HOLD | BLOCK
```

## The 7 sub-modules

| Module | File | What it computes |
|---|---|---|
| **7.1** | `leverage_stress.py` | `P(margin breach)` from M5 quantiles + effective buffer |
| **7.2** | `stop_risk.py` | `P(stop hit before target)` (Brownian bridge, reflection principle) |
| **7.3** | `expected_shortfall.py` | CVaR at α = 0.05 (analytic log-normal) |
| **7.4** | `liquidation_cost.py` | spread + slippage + Almgren-Chriss linear-sqrt impact |
| **7.5** | `max_survivable_size.py` | Kelly × survival × disagreement × half-life × cost drag |
| **7.6** | `thesis_half_life.py` | autocorrelation decay of disagreement magnitude |
| **7.7** | `abstention_gate.py` | regime-action table + hard-block rules → ACT/REDUCE/HOLD/BLOCK |

Plus `disagreement.py` — preserves F/T/D individually and applies
the spec protocol:

> if organs_disagree → confidence DOWN, interval_width UP,
>                      position_size DOWN, review_frequency UP

## Regime-action table

| Regime        | survival_p ≥ 0.9  | survival_p 0.7–0.9 | survival_p < 0.7 |
|---------------|-------------------|--------------------|------------------|
| RANGE         | ACT  (size=1.0)   | REDUCE (size×0.5)  | HOLD             |
| COMPRESSION   | REDUCE (size×0.5) | REDUCE (size×0.25) | HOLD             |
| TRENDING      | ACT  (size=1.0)   | REDUCE (size×0.5)  | BLOCK            |
| EVENT_RISK    | REDUCE (size×0.5) | HOLD               | BLOCK            |

The constraint equation `P(breach) < alpha` is enforced as a hard block:
`p_margin_breach > alpha` always ⇒ BLOCK regardless of regime.

Hard blocks also fire when:

* CVaR > `max_acceptable_loss_usd`
* Order > 50% of ADV (cannot liquidate cleanly)
* `survival_p < 0.5` (mission failed)
* `data_insufficient` ⇒ HOLD (refuse on missing data, never BLOCK)

## Constitutional rule

```
Fundamentals propose value.
Price reveals acceptance.
Flow reveals pressure.
The distribution measures uncertainty.
M7 determines survivability.
The judge may permit or refuse—but only the sovereign decides.
```

## Honest verdict

**What M7 has demonstrated:**

* All 7 sub-modules produce sensible outputs against the real M5 cascade
  and synthetic stress scenarios.
* All four verdicts (ACT, REDUCE, HOLD, BLOCK) are reachable and
  correctly triggered by the regime-action table + hard-block rules.
* Disagreement between F/T/D organs is preserved (individual signals
  exposed) and widens the safety envelope per spec.
* Honest receipts are written to `/root/AAA/VAULT999/receipts/`.

**What M7 has NOT demonstrated:**

* The default `spread_bps=5`, `slippage_bps=2`, and `adv_usd=$30B`
  are explicit synthetic XAUUSD defaults. There is no first-party
  live venue data source for these in this sandbox. The honest-caveat
  receipt marks them as synthetic.
* M7 does NOT predict gold. It only decides whether someone else's
  forecast can SAFELY become a position.
* M5 admission is the gate to live data; until M5 is promoted out of
  SHADOW_CHALLENGER, M7 runs on the same sandbox yfinance cascade
  (levels shifted to ~$4300 vs real-world ~$3300).

## Tests

`forecast/m7/tests/test_m7.py` — **45 tests** covering each module,
disagreement preservation, safety gate rules, end-to-end `run_m7`,
receipt writing, honest fallback, and the no-forecast invariant.

```
$ cd /root/WEALTH && python -m pytest forecast/m7/tests/ -v
45 passed in 0.88s
```

## Files

```
forecast/m7/
├── __init__.py
├── abstention_gate.py     # 7.7
├── disagreement.py        # F/T/D preservation
├── engine.py              # M7.0 orchestrator
├── expected_shortfall.py  # 7.3
├── leverage_stress.py     # 7.1
├── liquidation_cost.py    # 7.4
├── max_survivable_size.py # 7.5
├── receipts.py            # survival + honest-caveat receipts
├── stop_risk.py           # 7.2
├── thesis_half_life.py    # 7.6
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_m7.py
```

DITEMPA BUKAN DIBERI — Forged, not given.
