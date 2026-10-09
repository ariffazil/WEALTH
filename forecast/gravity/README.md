# GOLD_GRAVITY_FIELD — Regime + Volatility Model (SHADOW_CHALLENGER)

Wave + gravity challenger for XAUUSD. Treats the gold price as a **wave
being pulled by a gravity field** of cross-asset, cross-frequency signals.

## Status

**SHADOW_CHALLENGER** — the admission rule has not been satisfied on the
current evidence. Status remains unchanged until M4 (wave + gravity)
demonstrates measurable incremental skill over M0, M1, M2, AND M3 on a
walk-forward pinball tournament.

## Pipeline

```
000-INGEST       build the gravity feature series with release-timestamp guards
111-REGIME       posterior over {RANGE, TREND_UP, TREND_DOWN,
                                COMPRESSION, TRANSITION, EVENT_RISK}
444-DISTRIBUTION per-horizon cone (P10/P25/P50/P75/P90) + expected range +
                  vol-expansion probability — NOT a direction call
555-ABLATION     M0/M1/M2/M3/M4 walk-forward tournament
888-JUDGE        USE / HOLD / QUARANTINE based on admission
999-WITNESS      write receipt to VAULT999; admission_rule_failed on loss
```

## Ingesters (release-timestamp-guarded)

| Source            | Cadence | Release rule                                     |
|-------------------|---------|--------------------------------------------------|
| **DFII10**        | daily   | observation_ts + 19:30 UTC (FRED ~15:30 ET)      |
| **USD basket**    | daily   | observation_ts + 22:00 UTC (FX close)            |
| **Silver resid**  | daily   | observation_ts + 22:00 UTC                       |
| **ETF flows**     | weekly  | Thursday close → Friday 14:00 UTC (WGC cadence)  |
| **COT position**  | weekly  | Tuesday close → Friday 20:30 UTC (CFTC cadence)  |
| **CB demand**     | quarterly | quarter end + ~60 days (WGC cadence)            |

The joiner (`GravityFeatureSeries.value_at`) refuses to use any value
whose `release_ts` is in the future — no look-ahead.

DFII10 source priority: FRED `DFII10` if `FRED_API_KEY` is plaintext in
env; otherwise yfinance `^TNX` (nominal 10Y, labelled fallback).

CB demand fallback: 800 t/quarter static constant (WGC 2024 baseline),
labelled `SYNTHETIC` when used.

## Regime states (six)

* **RANGE** — gravity balanced
* **TREND_UP** — USD weak / real yields falling / ETF inflows
* **TREND_DOWN** — USD strong / real yields rising / COT crowded long
* **COMPRESSION** — realised vol < 75% of trailing median
* **TRANSITION** — features disagree directionally
* **EVENT_RISK** — exogenous event window (FOMC/NFP/CPI) within N hours

## Admission rule

M4 (wave + gravity) must beat M0, M1, M2, AND M3 on walk-forward pinball
to be promoted. Failure → `SHADOW_CHALLENGER` remains, write
`admission_rule_failed` receipt to VAULT999.

## Files

```
/root/WEALTH/forecast/gravity/
├── __init__.py             # public surface
├── ingest.py               # release-timestamp-guarded ingesters
├── regime.py               # 111_REGIME posterior
├── distribution.py         # 444_DISTRIBUTION cone builder
├── ablation.py             # 555-ABLATION tournament
├── gravity_pipeline.py     # 000→999 orchestrator + receipts
└── tests/
    └── test_gravity_field.py   # 27 tests covering all four lanes
```

## Usage

```python
from forecast.gravity import run_gravity_field

result = run_gravity_field(
    closes=closes_array,         # optional; falls back to wave_forge synthetic
    macro_payload=macro_dict,    # from /api/gold/macro
    event_window_hours=4,        # optional
    m4_wave_predictor=predictor, # optional wave_forge predictor
    write_receipt=True,
)

print(result.verdict)               # USE / HOLD / QUARANTINE
print(result.regime.state)          # RANGE / TREND_UP / ...
print(result.distribution.horizons) # 24/48/72h quantile cones
print(result.ablation.rows)         # M0/M1/M2/M3/M4 skill table
print(result.honest_verdict)        # human-readable admission verdict
```

## Honest verdict — what is known

* The pipeline runs end-to-end on synthetic XAUUSD history.
* The M4 ablation row shows negative skill on every baseline (skill
  vs M0 = -3.72, vs M1 = -3.61, vs M2 = -3.72, vs M3 = -3.61). This is
  because M4 in the synthetic fallback path delegates to M1 (no wave
  predictor provided) and amplifies M1's bias via the gravity term.
* The admission rule failed; the challenger stays SHADOW_CHALLENGER.
* An honest admission_rule_failed receipt has been written to
  `/root/AAA/VAULT999/receipts/`.

To prove M4 is genuinely better, the challenger needs:

1. A real wave-forge `m4_wave_predictor` from `wave_forge.run_wave_forge`.
2. Live FRED `DFII10` (currently encrypted env — would need KUNCI).
3. Live `/api/gold/macro` USD basket.

Until then: SHADOW. F13 authorization required for promotion.

DITEMPA BUKAN DIBERI — Forged, not given.
