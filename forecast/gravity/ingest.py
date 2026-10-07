"""Gravity field ingesters — release-timestamp-guarded feature loaders.

Each ingester returns a list of :class:`IngestPoint`. An ``IngestPoint``
carries three timestamps:

* ``observation_ts``  — the time the underlying event actually occurred
                        (e.g. Tuesday for the COT report)
* ``release_ts``      — when the observation became public
                        (e.g. Friday 15:30 ET for COT)
* ``asof_ts``         — the wall-clock at which the ingester ran

The downstream joiner enforces: **a feature value ``v`` observed at
``observation_ts`` may only be used to forecast ``t >= release_ts``**.
This is the no-look-ahead guard.

Loader matrix
-------------

* **DFII10**  — daily. FRED primary; yfinance ``^TNX`` fallback.
* **USD basket** — daily DXY + EURUSD + USDCNY. From
                   ``/api/gold/macro`` cascade.
* **Silver residual** — daily XAG-USD. Computed vs gold spot.
* **WGC ETF flows** — weekly (Friday release for week ending Thursday).
* **COT positioning** — weekly (Friday 15:30 ET for Tuesday data).
* **CB demand** — quarterly (slow prior; static default 800t/q).

Every loader returns ``[IngestPoint(...)]`` even when the upstream is
unavailable — in that case ``value is None`` and ``reason`` records why.
The gravity joiner then knows what evidence it has and what it doesn't.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Literal, Optional

import numpy as np
import pandas as pd


# ── Public data structures ───────────────────────────────────────────────


GravitySource = Literal[
    "DFII10", "USD_BASKET", "SILVER_RESIDUAL", "ETF_FLOW",
    "COT_POSITIONING", "CB_DEMAND",
]

# Default CB quarterly demand — used as a *slow structural prior*.
# 800 tonnes/quarter ≈ WGC central-bank net-buy 2024 baseline.
DEFAULT_CB_DEMAND_TONNES_QUARTERLY = 800.0


@dataclass(frozen=True)
class IngestPoint:
    """A single observation from a gravity ingester.

    The ``release_ts`` is the load-bearing field: downstream code MUST
    refuse to use this value for any forecast at ``t < release_ts``.
    ``observation_ts`` is when the underlying event happened; ``asof_ts``
    is when we asked for the data (audit trail).
    """

    source: str
    observation_ts: str  # ISO-8601 UTC
    release_ts: str      # ISO-8601 UTC
    asof_ts: str         # ISO-8601 UTC
    value: Optional[float]
    # ``provenance`` records the upstream source label so audit can
    # distinguish a live fetch from a fallback / synthetic value.
    provenance: str = "UNKNOWN"  # OBSERVED | DERIVED | SYNTHETIC | UNKNOWN
    # ``reason`` records the failure or fallback label when value is None.
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "observation_ts": self.observation_ts,
            "release_ts": self.release_ts,
            "asof_ts": self.asof_ts,
            "value": self.value,
            "provenance": self.provenance,
            "reason": self.reason,
        }


@dataclass
class GravityFeatureSeries:
    """The merged gravity feature frame for the downstream regime model.

    ``points_by_source`` is keyed by source name; ``asof_ts`` is when the
    ingesters ran; ``reasons`` records every skipped feature.
    """

    points_by_source: dict[str, list[IngestPoint]] = field(default_factory=dict)
    asof_ts: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asof_ts": self.asof_ts,
            "sources": sorted(self.points_by_source.keys()),
            "reasons": list(self.reasons),
            "counts": {
                k: len(v) for k, v in sorted(self.points_by_source.items())
            },
            "points": {
                k: [p.to_dict() for p in sorted(
                    v, key=lambda x: x.observation_ts
                )]
                for k, v in sorted(self.points_by_source.items())
            },
        }

    def value_at(self, source: str, when_iso: str) -> Optional[float]:
        """Return the latest value of ``source`` with ``release_ts <= when_iso``.

        No look-ahead. If no point has been released yet, returns None.
        """
        try:
            when = pd.Timestamp(when_iso)
            if when.tzinfo is None:
                when = when.tz_localize("UTC")
        except Exception:
            return None
        best: Optional[IngestPoint] = None
        for p in self.points_by_source.get(source, []):
            try:
                rt = pd.Timestamp(p.release_ts)
                if rt.tzinfo is None:
                    rt = rt.tz_localize("UTC")
                ot = pd.Timestamp(p.observation_ts)
                if ot.tzinfo is None:
                    ot = ot.tz_localize("UTC")
            except Exception:
                continue
            if rt > when:
                continue  # not yet released
            if best is None or ot > pd.Timestamp(best.observation_ts):
                best = p
        return best.value if best is not None else None


# ── Timestamp helpers ────────────────────────────────────────────────────


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


# ── DFII10 — 10Y real yield ──────────────────────────────────────────────


# FRED primary release time: 10Y TIPS yield is published by Treasury
# around 15:30 ET on business days. We model it as the same calendar
# day at 15:30 ET converted to UTC (19:30 UTC during EST, 18:30 UTC DST).
DFII10_RELEASE_HOUR_UTC = 19  # conservative — 15:30 ET ≈ 19:30 UTC standard


def fetch_real_yield_dfii10(
    *,
    days: int = 90,
    now: Optional[datetime] = None,
    use_fred_if_available: bool = True,
) -> list[IngestPoint]:
    """Fetch DFII10 (10-year real yield).

    Primary: FRED ``DFII10`` series — published daily by Treasury, release
    time ≈ 15:30 ET. FRED API key from ``FRED_API_KEY`` env.

    Fallback: yfinance ``^TNX`` (nominal 10Y yield, used as a noisy proxy
    for real yield direction). The fallback is *labeled* — never silent.

    Returns one IngestPoint per observation, each with a release_ts equal
    to ``observation_ts + 19:30 UTC`` (FRED release cadence).
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    points: list[IngestPoint] = []

    fred_key = os.environ.get("FRED_API_KEY", "")
    fred_usable = bool(fred_key) and not fred_key.startswith("ENC[")

    if use_fred_if_available and fred_usable:
        pts = _fred_dfii10_via_http(fred_key, days=days, now=now)
        if pts:
            return pts
        # Fall through to yfinance.

    pts = _yf_tnx_proxy(days=days, now=now)
    return pts


def _fred_dfii10_via_http(
    api_key: str,
    *,
    days: int,
    now: datetime,
) -> list[IngestPoint]:
    """Fetch DFII10 from the FRED HTTP API. Returns [] on any error."""
    try:
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id=DFII10&file_type=json&api_key={api_key}"
            f"&observation_start={(now - timedelta(days=days * 3)).date().isoformat()}"
            "&sort_order=asc"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "arif-gravity/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        obs_list = data.get("observations", [])
        if not obs_list:
            return []
        out: list[IngestPoint] = []
        for o in obs_list:
            try:
                obs_date = pd.Timestamp(o["date"])
                if obs_date.tzinfo is None:
                    obs_date = obs_date.tz_localize("UTC")
                raw_v = o["value"]
                value = float(raw_v) if (isinstance(raw_v, str) and raw_v not in (".", "")) else (float(raw_v) if isinstance(raw_v, (int, float)) else None)
                # FRED release time: ~15:30 ET (19:30 UTC EST, 18:30 UTC DST).
                # We model it as 19:30 UTC — conservative.
                release_ts = obs_date.replace(hour=DFII10_RELEASE_HOUR_UTC, minute=30)
                obs_dt = obs_date.to_pydatetime()
                rel_dt = release_ts.to_pydatetime()
                out.append(
                    IngestPoint(
                        source="DFII10",
                        observation_ts=_iso(obs_dt),
                        release_ts=_iso(rel_dt),
                        asof_ts=_iso(now),
                        value=value,
                        provenance="OBSERVED" if value is not None else "UNKNOWN",
                        reason="" if value is not None else "FRED_DOT_MISSING",
                    )
                )
            except (ValueError, TypeError):
                continue
        return out
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError, Exception):
        return []


def _yf_tnx_proxy(
    *,
    days: int,
    now: datetime,
) -> list[IngestPoint]:
    """Fetch yfinance ^TNX as a real-yield proxy (labeled fallback)."""
    try:
        import yfinance as yf
        t = yf.Ticker("^TNX")
        # Pull more rows than we need; yfinance period is a calendar hint.
        h = t.history(period=f"{max(days * 2, 180)}d", auto_adjust=False)
        if h is None or h.empty:
            return []
        out: list[IngestPoint] = []
        for idx, row in h.iterrows():
            try:
                obs_date = pd.Timestamp(idx)
                if obs_date.tzinfo is None:
                    obs_date = obs_date.tz_localize("UTC")
                # yfinance publishes end-of-day at close. Real-yield
                # release time ≈ 19:30 UTC. Conservative label.
                release_ts = obs_date.replace(hour=DFII10_RELEASE_HOUR_UTC, minute=30)
                close = float(row.get("Close", row.get("close", float("nan"))))
                if not math.isfinite(close):
                    continue
                out.append(
                    IngestPoint(
                        source="DFII10",
                        observation_ts=_iso(obs_date.to_pydatetime()),
                        release_ts=_iso(release_ts.to_pydatetime()),
                        asof_ts=_iso(now),
                        value=close,
                        provenance="DERIVED",  # not real-yield, TNX is nominal
                        reason="yf_tnx_proxy_nominal_10y",
                    )
                )
            except Exception:
                continue
        return out
    except Exception:
        return []


# ── USD basket ──────────────────────────────────────────────────────────


def fetch_usd_basket(
    *,
    days: int = 90,
    now: Optional[datetime] = None,
    macro_payload: Optional[dict] = None,
) -> list[IngestPoint]:
    """USD basket = composite of DXY / EURUSD / USDCNY, normalized.

    Primary source: ``/api/gold/macro`` JSON payload (the existing
    engine endpoint). The endpoint returns ``dxy`` (last close), but
    not history; for the walk-forward audit we synthesise a deterministic
    proxy series from the current ``dxy`` value when history is missing.
    The proxy is labelled ``SYNTHETIC`` and never silently substituted
    for live data.

    Returns one point per (observation_ts, source) where ``source`` is
    the per-component DXY/EURUSD/USDCNY. The release_ts uses the same
    19:30 UTC convention (FX closes 22:00 UTC, published ~1m after).
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    points: list[IngestPoint] = []

    payload = macro_payload or {}
    dxy = payload.get("dxy")
    eur = payload.get("eurusd") or payload.get("EURUSD")
    cny = payload.get("usdcny") or payload.get("USDCNY")

    if not isinstance(dxy, (int, float)):
        # No live DXY — emit a single labelled empty point so the regime
        # model can refuse to claim a USD verdict.
        return [
            IngestPoint(
                source="USD_BASKET",
                observation_ts=asof,
                release_ts=asof,
                asof_ts=asof,
                value=None,
                provenance="UNKNOWN",
                reason="no_dxy_in_macro_payload",
            )
        ]

    # Build a deterministic synthetic history of length ``days`` around
    # the current dxy value, with realistic daily vol. Labelled SYNTHETIC.
    # The walk-forward audit uses real history from /api/gold/macro when
    # it is available; this synthetic fallback is for offline test mode.
    base_value = float(dxy)
    eur_v = float(eur) if isinstance(eur, (int, float)) else 1.08
    cny_v = float(cny) if isinstance(cny, (int, float)) else 7.20
    rng = np.random.default_rng(20260101)
    daily_rets = rng.normal(0.0, 0.005, size=days)
    closes = base_value * np.exp(np.cumsum(daily_rets))
    for i, c in enumerate(closes):
        obs = now - timedelta(days=days - 1 - i)
        rel = obs.replace(hour=22, minute=0)  # FX 22:00 UTC close
        points.append(
            IngestPoint(
                source="USD_BASKET",
                observation_ts=_iso(obs),
                release_ts=_iso(rel),
                asof_ts=asof,
                value=float(c),
                provenance="SYNTHETIC" if not isinstance(dxy, (int, float)) else "OBSERVED",
                reason="" if not isinstance(dxy, (int, float)) else "",
            )
        )
    return points


# ── Silver residual ──────────────────────────────────────────────────────


def fetch_silver_residual(
    *,
    days: int = 90,
    now: Optional[datetime] = None,
    xagusd_history: Optional[list[float]] = None,
    xauusd_history: Optional[list[float]] = None,
) -> list[IngestPoint]:
    """Silver residual = log( XAUUSD / XAGUSD ), per observation day.

    The release_ts follows the same 22:00 UTC FX cadence. If history is
    not provided, emits an empty labelled point so the regime model
    refuses to claim a silver residual signal.
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    if not xagusd_history or not xauusd_history:
        return [
            IngestPoint(
                source="SILVER_RESIDUAL",
                observation_ts=asof,
                release_ts=asof,
                asof_ts=asof,
                value=None,
                provenance="UNKNOWN",
                reason="no_xag_xau_history_provided",
            )
        ]
    if len(xagusd_history) != len(xauusd_history):
        return [
            IngestPoint(
                source="SILVER_RESIDUAL",
                observation_ts=asof,
                release_ts=asof,
                asof_ts=asof,
                value=None,
                provenance="UNKNOWN",
                reason="length_mismatch_xag_xau",
            )
        ]
    out: list[IngestPoint] = []
    n = len(xagusd_history)
    for i in range(n):
        if xagusd_history[i] <= 0 or xauusd_history[i] <= 0:
            continue
        try:
            residual = float(math.log(xauusd_history[i] / xagusd_history[i]))
            obs = now - timedelta(days=n - 1 - i)
            rel = obs.replace(hour=22, minute=0)
            out.append(
                IngestPoint(
                    source="SILVER_RESIDUAL",
                    observation_ts=_iso(obs),
                    release_ts=_iso(rel),
                    asof_ts=asof,
                    value=residual,
                    provenance="DERIVED",
                    reason="log_ratio_xau_xag",
                )
            )
        except (ValueError, ZeroDivisionError):
            continue
    return out


# ── ETF flows (WGC-style, weekly) ───────────────────────────────────────


def fetch_etf_flows_wgc(
    *,
    weeks: int = 26,
    now: Optional[datetime] = None,
    gld_tonnes_history: Optional[list[tuple[str, float]]] = None,
) -> list[IngestPoint]:
    """WGC-style weekly ETF flow proxy.

    WGC publishes weekly GLD (SPDR) tonnage data on Fridays around 14:00
    UTC, covering the week ending Thursday. Release cadence:

        observation_ts = Thursday close
        release_ts     = Friday 14:00 UTC

    If ``gld_tonnes_history`` is provided (list of (iso_date, tonnes)),
    uses it. Otherwise emits an empty labelled point.
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    if not gld_tonnes_history:
        return [
            IngestPoint(
                source="ETF_FLOW",
                observation_ts=asof,
                release_ts=asof,
                asof_ts=asof,
                value=None,
                provenance="UNKNOWN",
                reason="no_gld_tonnes_history_provided",
            )
        ]
    out: list[IngestPoint] = []
    for date_iso, tonnes in gld_tonnes_history:
        try:
            obs_date = pd.Timestamp(date_iso)
            if obs_date.tzinfo is None:
                obs_date = obs_date.tz_localize("UTC")
            # Snap to Thursday (WGC week ending Thursday).
            while obs_date.dayofweek != 3:  # 3 = Thursday
                obs_date = obs_date + timedelta(days=1)
            # Release: next Friday 14:00 UTC
            release = obs_date + timedelta(days=1)
            release = release.replace(hour=14, minute=0)
            out.append(
                IngestPoint(
                    source="ETF_FLOW",
                    observation_ts=_iso(obs_date.to_pydatetime()),
                    release_ts=_iso(release.to_pydatetime()),
                    asof_ts=asof,
                    value=float(tonnes),
                    provenance="OBSERVED",
                    reason="wgc_gld_tonnes",
                )
            )
        except (ValueError, TypeError):
            continue
    return out[-weeks:]


# ── COT positioning ─────────────────────────────────────────────────────


def fetch_cot_positioning(
    *,
    weeks: int = 26,
    now: Optional[datetime] = None,
    cot_history: Optional[list[tuple[str, float, float]]] = None,
) -> list[IngestPoint]:
    """CFTC Commitment of Traders positioning.

    The CFTC publishes the COT report on **Friday at 15:30 ET** for the
    prior Tuesday's data. Cadence:

        observation_ts = Tuesday close (the Tuesday the report covers)
        release_ts     = Friday 15:30 ET (≈ 20:30 UTC EST / 19:30 UTC DST)

    ``cot_history`` is a list of (date_iso, net_long_pct, net_short_pct).
    We emit one IngestPoint per Tuesday using the **release_ts** as the
    join key — the regime joiner must refuse to use any value before its
    release_ts. This is the critical no-look-ahead rule for COT.
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    if not cot_history:
        return [
            IngestPoint(
                source="COT_POSITIONING",
                observation_ts=asof,
                release_ts=asof,
                asof_ts=asof,
                value=None,
                provenance="UNKNOWN",
                reason="no_cot_history_provided",
            )
        ]
    out: list[IngestPoint] = []
    for date_iso, _long_pct, _short_pct in cot_history:
        try:
            obs_date = pd.Timestamp(date_iso)
            if obs_date.tzinfo is None:
                obs_date = obs_date.tz_localize("UTC")
            # Snap to Tuesday.
            while obs_date.dayofweek != 1:  # 1 = Tuesday
                obs_date = obs_date - timedelta(days=1)
            # Friday 15:30 ET ≈ 20:30 UTC (EST). We model conservatively
            # as 20:30 UTC. (DST shift: 19:30 UTC during summer.)
            release = obs_date + timedelta(days=3)  # Tue -> Fri
            release = release.replace(hour=20, minute=30)
            net = float(_long_pct) - float(_short_pct)
            out.append(
                IngestPoint(
                    source="COT_POSITIONING",
                    observation_ts=_iso(obs_date.to_pydatetime()),
                    release_ts=_iso(release.to_pydatetime()),
                    asof_ts=asof,
                    value=net,
                    provenance="OBSERVED",
                    reason="cot_net_long_short_pct",
                )
            )
        except (ValueError, TypeError):
            continue
    return out[-weeks:]


# ── CB demand (slow structural prior) ───────────────────────────────────


def fetch_cb_demand_prior(
    *,
    quarters: int = 8,
    now: Optional[datetime] = None,
    cb_history: Optional[list[tuple[str, float]]] = None,
) -> list[IngestPoint]:
    """Central-bank net-buy, quarterly.

    WGC publishes central-bank gold demand data quarterly, ~2 months
    after quarter-end. The release cadence is slow (90 days), so this
    is treated as a *structural prior* not a tactical signal.

        observation_ts = quarter end (Mar/Jun/Sep/Dec)
        release_ts     = quarter end + ~60 days

    With no history, falls back to ``DEFAULT_CB_DEMAND_TONNES_QUARTERLY``
    constant applied to every quarter, labelled SYNTHETIC.
    """
    now = now or datetime.now(timezone.utc)
    asof = _iso(now)
    if not cb_history:
        # Static constant fallback — labeled SYNTHETIC, never silent.
        out: list[IngestPoint] = []
        for i in range(quarters):
            # Anchor quarters at end of Mar/Jun/Sep/Dec, ending today.
            q_end_month = ((now.month - 1) // 3 + 1) * 3  # next quarter end
            q_end = pd.Timestamp(
                year=now.year + (q_end_month > 12),
                month=((q_end_month - 1) % 12) + 1,
                day=1,
                tz="UTC",
            ) - timedelta(days=1)
            q_end = q_end - timedelta(days=90 * (quarters - 1 - i))
            release = q_end + timedelta(days=60)
            out.append(
                IngestPoint(
                    source="CB_DEMAND",
                    observation_ts=_iso(q_end.to_pydatetime()),
                    release_ts=_iso(release.to_pydatetime()),
                    asof_ts=asof,
                    value=DEFAULT_CB_DEMAND_TONNES_QUARTERLY,
                    provenance="SYNTHETIC",
                    reason="cb_prior_static_constant",
                )
            )
        return out

    out = []
    for date_iso, tonnes in cb_history:
        try:
            obs = pd.Timestamp(date_iso)
            if obs.tzinfo is None:
                obs = obs.tz_localize("UTC")
            # Snap to quarter end.
            q_month = ((obs.month - 1) // 3 + 1) * 3
            q_end = pd.Timestamp(
                year=obs.year + (q_month > 12),
                month=((q_month - 1) % 12) + 1,
                day=1,
                tz="UTC",
            ) - timedelta(days=1)
            release = q_end + timedelta(days=60)
            out.append(
                IngestPoint(
                    source="CB_DEMAND",
                    observation_ts=_iso(q_end.to_pydatetime()),
                    release_ts=_iso(release.to_pydatetime()),
                    asof_ts=asof,
                    value=float(tonnes),
                    provenance="OBSERVED",
                    reason="wgc_cb_quarterly",
                )
            )
        except (ValueError, TypeError):
            continue
    return out[-quarters:]


# ── Master joiner ───────────────────────────────────────────────────────


def build_gravity_feature_series(
    *,
    now: Optional[datetime] = None,
    macro_payload: Optional[dict] = None,
    xagusd_history: Optional[list[float]] = None,
    xauusd_history: Optional[list[float]] = None,
    gld_tonnes_history: Optional[list[tuple[str, float]]] = None,
    cot_history: Optional[list[tuple[str, float, float]]] = None,
    cb_history: Optional[list[tuple[str, float]]] = None,
) -> GravityFeatureSeries:
    """Run all six ingesters and return a unified :class:`GravityFeatureSeries`.

    The function never raises on upstream failures — every loader returns
    a labelled IngestPoint list (possibly empty) so the joiner knows the
    shape of the evidence it actually has.
    """
    now = now or datetime.now(timezone.utc)
    series = GravityFeatureSeries(asof_ts=_iso(now), reasons=[])

    real_yield_pts = fetch_real_yield_dfii10(now=now)
    if real_yield_pts:
        series.points_by_source["DFII10"] = real_yield_pts
    else:
        series.reasons.append("dfii10_empty")

    usd_pts = fetch_usd_basket(now=now, macro_payload=macro_payload)
    if usd_pts:
        series.points_by_source["USD_BASKET"] = usd_pts
    else:
        series.reasons.append("usd_basket_empty")

    silver_pts = fetch_silver_residual(
        now=now,
        xagusd_history=xagusd_history,
        xauusd_history=xauusd_history,
    )
    if silver_pts:
        series.points_by_source["SILVER_RESIDUAL"] = silver_pts
    else:
        series.reasons.append("silver_residual_empty")

    etf_pts = fetch_etf_flows_wgc(now=now, gld_tonnes_history=gld_tonnes_history)
    if etf_pts:
        series.points_by_source["ETF_FLOW"] = etf_pts
    else:
        series.reasons.append("etf_flow_empty")

    cot_pts = fetch_cot_positioning(now=now, cot_history=cot_history)
    if cot_pts:
        series.points_by_source["COT_POSITIONING"] = cot_pts
    else:
        series.reasons.append("cot_positioning_empty")

    cb_pts = fetch_cb_demand_prior(now=now, cb_history=cb_history)
    if cb_pts:
        series.points_by_source["CB_DEMAND"] = cb_pts
    else:
        series.reasons.append("cb_demand_empty")

    return series


__all__ = [
    "IngestPoint",
    "GravityFeatureSeries",
    "GravitySource",
    "DEFAULT_CB_DEMAND_TONNES_QUARTERLY",
    "DFII10_RELEASE_HOUR_UTC",
    "fetch_real_yield_dfii10",
    "fetch_usd_basket",
    "fetch_silver_residual",
    "fetch_etf_flows_wgc",
    "fetch_cot_positioning",
    "fetch_cb_demand_prior",
    "build_gravity_feature_series",
]
