"""GOLD_GRAVITY_FIELD — gravity-driven regime + volatility model for XAUUSD.

A challenger that treats gold price as a **wave being pulled by a gravity
field**. The gravity sources (with strict release-timestamp guards) are:

* **DFII10** — 10Y real yield (daily, FRED primary / yfinance ^TNX fallback)
* **USD basket** — DXY + EURUSD + USDCNY, derived from `/api/gold/macro`
* **Silver residual** — XAG-USD vs gold (computed)
* **ETF flows** — WGC weekly SPDR GLD tonnage change
* **COT positioning** — CFTC weekly (Friday release for Tuesday data)
* **CB demand** — quarterly (slow structural prior; static constant 800t/q)

Pipeline (all receipted):

    000-INGEST     build the gravity feature series with timestamp guards
    111-REGIME     posterior over {RANGE, TREND_UP, TREND_DOWN,
                                  COMPRESSION, TRANSITION, EVENT_RISK}
    444-DISTRIBUTION  emit P10/P25/P50/P75/P90 for 24/48/72h,
                       expected range, vol expansion probability
    555-ABLATION   M0 / M1 / M2 / M3 / M4 walk-forward on the same history
    888-JUDGE      USE / HOLD / QUARANTINE — admission rule:
                     M4 must beat M0, M1, M2, M3
    999-WITNESS    write receipt (and admission_rule_failed on failure)

Laws binding this module
------------------------
* NO FAKE GRAVITY — every feature point carries an ingestion timestamp
  (``release_ts``); the joiner refuses to use a value before that
  timestamp even if the underlying series goes further back.
* NO FAKE OHLC — the price path is real (or honest synthetic with
  ``SYNTHETIC`` label, never silently substituted).
* Default status = ``SHADOW_CHALLENGER``. Promotion out of SHADOW
  requires passing the admission tournament.
* The 444 distribution is a **distribution** — not a direction call.
* The 111 regime is a **posterior** — never a Boolean.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from .ingest import (
    IngestPoint,
    GravityFeatureSeries,
    DEFAULT_CB_DEMAND_TONNES_QUARTERLY,
    fetch_real_yield_dfii10,
    fetch_usd_basket,
    fetch_silver_residual,
    fetch_etf_flows_wgc,
    fetch_cot_positioning,
    fetch_cb_demand_prior,
    build_gravity_feature_series,
)

from .regime import (
    REGIME_STATES,
    RegimePosterior111,
    compute_regime_posterior_111,
    DEFAULT_VOL_RATIO_COMPRESSION,
    DEFAULT_VOL_RATIO_EXPANSION,
)

from .distribution import (
    Distribution444,
    HorizonDistribution,
    compute_distribution_444,
    quantile_cone_from_regime,
    expected_range_p10_p90,
    volatility_expansion_probability,
)

from .ablation import (
    ModelSkillRow,
    AblationTable,
    run_ablation_tournament,
    PROMOTION_SKILL_FLOOR,
)

from .gravity_pipeline import (
    SCHEMA,
    STATUS,
    GravityResult,
    run_gravity_field,
    write_gravity_receipt,
    write_admission_rule_failed_receipt,
)

__all__ = [
    # ingest
    "IngestPoint",
    "GravityFeatureSeries",
    "DEFAULT_CB_DEMAND_TONNES_QUARTERLY",
    "fetch_real_yield_dfii10",
    "fetch_usd_basket",
    "fetch_silver_residual",
    "fetch_etf_flows_wgc",
    "fetch_cot_positioning",
    "fetch_cb_demand_prior",
    "build_gravity_feature_series",
    # regime
    "REGIME_STATES",
    "RegimePosterior111",
    "compute_regime_posterior_111",
    "DEFAULT_VOL_RATIO_COMPRESSION",
    "DEFAULT_VOL_RATIO_EXPANSION",
    # distribution
    "Distribution444",
    "HorizonDistribution",
    "compute_distribution_444",
    "quantile_cone_from_regime",
    "expected_range_p10_p90",
    "volatility_expansion_probability",
    # ablation
    "ModelSkillRow",
    "AblationTable",
    "run_ablation_tournament",
    "PROMOTION_SKILL_FLOOR",
    # pipeline
    "SCHEMA",
    "STATUS",
    "GravityResult",
    "run_gravity_field",
    "write_gravity_receipt",
    "write_admission_rule_failed_receipt",
]
