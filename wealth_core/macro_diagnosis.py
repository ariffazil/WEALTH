"""
WEALTH Macro Diagnosis Engine — Global→Malaysia Transmission.
Produces OBSERVED/DERIVED/INTERPRETED macro diagnosis.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone


# ── Types ──────────────────────────────────────────────────────────


@dataclass
class MacroObservation:
    """Single macro observation with provenance."""

    value: float | str | None
    observation_period: str  # e.g. "2026-06"
    published_at: str | None  # e.g. "2026-07-15T04:00:00Z"
    fetched_at: str  # when WEALTH retrieved it
    source: str  # provider name
    freshness: str = "UNKNOWN"  # CURRENT | STALE | UNKNOWN | UNAVAILABLE
    revision_status: str = "final"  # preliminary | revised | final

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "observation_period": self.observation_period,
            "published_at": self.published_at,
            "fetched_at": self.fetched_at,
            "source": self.source,
            "freshness": self.freshness,
            "revision_status": self.revision_status,
            "_class": "OBSERVED",
        }


@dataclass
class DerivedMetric:
    """Computed metric from observations."""

    value: float | str
    method: str  # e.g. "rate_differential", "real_rate"
    inputs: list[str]  # source observation names
    fetched_at: str
    freshness: str = "CURRENT"

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "method": self.method,
            "inputs": self.inputs,
            "fetched_at": self.fetched_at,
            "freshness": self.freshness,
            "_class": "DERIVED",
        }


@dataclass
class DiagnosisStatement:
    """WEALTH interpretation — never authorization."""

    statement: str
    horizon: str  # "near-term" | "medium-term" | "long-term"
    channel: str  # transmission channel
    confidence: float  # 0.0-1.0
    contrary_evidence: list[str] = field(default_factory=list)
    freshness: str = "CURRENT"

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "horizon": self.horizon,
            "channel": self.channel,
            "confidence": round(self.confidence, 2),
            "contrary_evidence": self.contrary_evidence,
            "freshness": self.freshness,
            "_class": "INTERPRETED",
            "_note": "WEALTH diagnosis. Not investment advice. Not authorization.",
        }


# ── Transmission Channels ──────────────────────────────────────────

TRANSMISSION_CHANNELS = {
    "currency": {
        "name": "Currency Channel",
        "description": "Global rates → DXY → MYR → imported costs",
        "global_drivers": ["fed_rate", "us2y", "us10y", "dxy"],
        "malaysia_variables": ["opr", "myr_usd", "myr_twi"],
    },
    "inflation": {
        "name": "Inflation Channel",
        "description": "Global CPI → imported inflation → domestic CPI → subsidy pressure",
        "global_drivers": ["us_cpi", "us_core_cpi", "brent", "lng_asia"],
        "malaysia_variables": ["my_cpi", "my_core_cpi", "my_ppi", "fuel_subsidy"],
    },
    "growth": {
        "name": "Growth/Trade Channel",
        "description": "China/US demand → exports → industrial production → employment",
        "global_drivers": ["china_pmi", "us_pmi", "global_trade"],
        "malaysia_variables": ["my_exports", "my_ipi", "my_pmi", "my_employment"],
    },
    "fiscal_energy": {
        "name": "Fiscal-Energy Channel",
        "description": "Brent/LNG → PETRONAS revenue → government fiscal → subsidy cost",
        "global_drivers": ["brent", "lng_asia"],
        "malaysia_variables": [
            "petronas_dividend",
            "govt_revenue",
            "fuel_subsidy",
            "fiscal_deficit",
        ],
    },
}


# ── Diagnosis Engine ───────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def diagnose_gold_snapshot(engine_data: dict[str, Any]) -> dict[str, Any]:
    """
    Produce macro diagnosis from gold engine snapshot data.
    engine_data is raw output from commodity_engines.get_snapshot('gold')
    """
    snapshot = engine_data.get("snapshot", {})
    ticker = snapshot.get("ticker", {})
    macro = snapshot.get("macro", {})

    now = _now()

    # OBSERVED
    observations = {
        "gold_price": MacroObservation(
            value=ticker.get("price"),
            observation_period="realtime",
            published_at=ticker.get("timestamp"),
            fetched_at=now,
            source="engine:gold",
            freshness="CURRENT",
        ).to_dict(),
        "dxy": MacroObservation(
            value=macro.get("dxy"),
            observation_period="realtime",
            published_at=macro.get("timestamp"),
            fetched_at=now,
            source="engine:gold",
            freshness="CURRENT",
        ).to_dict(),
    }

    # DERIVED
    derivatives = {}
    price = ticker.get("price")
    dxy = macro.get("dxy")
    if price and dxy:
        myr_usd = 4.65  # placeholder — should come from live FX feed
        xau_myr = round(price * myr_usd, 2)
        derivatives["xau_myr"] = DerivedMetric(
            value=xau_myr,
            method="XAU/USD × USD/MYR",
            inputs=["gold_price", "myr_usd"],
            fetched_at=now,
        ).to_dict()

    # INTERPRETED
    diagnoses = []
    rsi = ticker.get("rsi")
    if rsi is not None:
        if rsi > 70:
            diagnoses.append(
                DiagnosisStatement(
                    statement=f"Gold RSI at {rsi} — technically overbought. Caution on chasing upside.",
                    horizon="near-term",
                    channel="price",
                    confidence=0.6,
                    contrary_evidence=["Overbought can persist in strong trends"],
                )
            )
        elif rsi < 30:
            diagnoses.append(
                DiagnosisStatement(
                    statement=f"Gold RSI at {rsi} — technically oversold. Potential bounce opportunity.",
                    horizon="near-term",
                    channel="price",
                    confidence=0.6,
                )
            )
        else:
            diagnoses.append(
                DiagnosisStatement(
                    statement=f"Gold RSI at {rsi} — neutral territory. No extreme signal.",
                    horizon="near-term",
                    channel="price",
                    confidence=0.7,
                )
            )

    if dxy and dxy < 104:
        diagnoses.append(
            DiagnosisStatement(
                statement="DXY below 104 supports gold. Weaker USD reduces headwind for XAU/USD.",
                horizon="near-term",
                channel="currency",
                confidence=0.65,
                contrary_evidence=["DXY can reverse on hawkish Fed surprise"],
            )
        )

    return {
        "asset": "gold",
        "diagnosed_at": now,
        "summary": {
            "price": ticker.get("price"),
            "rsi": ticker.get("rsi"),
            "signal": ticker.get("signal"),
            "xau_myr": derivatives.get("xau_myr", {}).get("value"),
            "dxy": macro.get("dxy"),
        },
        "observations": observations,
        "derivatives": derivatives,
        "interpretations": [d.to_dict() for d in diagnoses],
        "freshness": {
            "gold_price": "CURRENT",
            "dxy": "CURRENT",
            "xau_myr": "DERIVED",
        },
        "_compact": True,
    }


def diagnose_macro_briefing(
    global_obs: dict[str, MacroObservation],
    malaysia_obs: dict[str, MacroObservation],
) -> dict[str, Any]:
    """
    Produce a full Global→Malaysia macro diagnosis.
    Both inputs are dicts of {name: MacroObservation}.
    """
    now = _now()
    interpretations = []

    # Currency channel diagnosis
    dxy = global_obs.get("dxy")
    myr = malaysia_obs.get("myr_usd")
    if dxy and dxy.value and myr and myr.value:
        if float(dxy.value) < 104 and float(myr.value) < 4.70:
            interpretations.append(
                DiagnosisStatement(
                    statement="MYR may strengthen further if DXY continues to fall "
                    "and BNM holds OPR. Favourable for import costs.",
                    horizon="near-term",
                    channel="currency",
                    confidence=0.55,
                    contrary_evidence=["Capital flow reversal", "BNM surprise cut"],
                ).to_dict()
            )

    # Energy channel diagnosis
    brent = global_obs.get("brent")
    if brent and brent.value and float(brent.value) > 75:
        interpretations.append(
            DiagnosisStatement(
                statement=f"Brent at {brent.value} supports PETRONAS upstream revenue "
                f"but increases subsidy expenditure. Net fiscal effect is "
                f"positive at current levels.",
                horizon="medium-term",
                channel="fiscal_energy",
                confidence=0.6,
                contrary_evidence=["Subsidy cost may offset revenue gain"],
            ).to_dict()
        )

    return {
        "diagnosed_at": now,
        "transmission_channels": list(TRANSMISSION_CHANNELS.keys()),
        "interpretations": interpretations,
        "observation_count": len(global_obs) + len(malaysia_obs),
        "note": "WEALTH macro diagnosis. Not investment advice. Not authorization.",
    }
