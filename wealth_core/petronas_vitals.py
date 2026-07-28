"""PETRONAS·φ VITALS — pure distance-to-trip compute (no authority).

WEALTH computes. arifOS judges. Arif decides.
Does NOT: allocate, recommend buy/sell, or issue SEAL/VOID as governance.

DITEMPA BUKAN DIBERI — 2026-07-24 F2 re-seal.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Constitutional weights (organ law — not free parameters)
WEIGHTS = {"BODY": 0.40, "SPINE": 0.35, "SOUL": 0.25}

# Default constitution after F2 audit vs PETRONAS Group FRA FY2025 IFR (public)
# EVIDENCE fields grounded in IFR line items; INTERPRET remain judgment-anchored.
DEFAULT_TRIPWIRES: list[dict[str, Any]] = [
    {
        "id": 1,
        "layer": "BODY",
        "name": "FCF after capex & dividend",
        "now": 11.6,
        "trip": 0,
        "safe": 15,
        "unit": "RM B",
        "dir": "below",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "IFR FY25: CFFO 85.2 − capex 41.6 − div 32.0 ≈ 11.6 (was 7.0 soft). Still positive.",
        "source": "PETRONAS Group FRA FY2025 IFR",
    },
    {
        "id": 2,
        "layer": "BODY",
        "name": "Gearing ratio",
        "now": 20.7,
        "trip": 40,
        "safe": 15,
        "unit": "%",
        "dir": "above",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "Audited gearing 20.7% (FY24: 19.6%). PRefChem consolidation may step ~25–27% (one-time).",
        "source": "PETRONAS Group FRA FY2025 IFR",
    },
    {
        "id": 3,
        "layer": "BODY",
        "name": "CFFO — master variable",
        "now": 85.2,
        "trip": 60,
        "safe": 95,
        "unit": "RM B",
        "dir": "below",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "CFFO RM85.2B IFR. Below RM60B forces trade-off among dividend, capex, balance sheet.",
        "source": "PETRONAS Group FRA FY2025 IFR",
    },
    {
        "id": 4,
        "layer": "SPINE",
        "name": "Production / reserve replacement",
        "now": 355,
        "trip": 300,
        "safe": 500,
        "unit": "kbpd",
        "dir": "below",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "Malaysia crude liquids ~355 kbpd (not group 2.4 Mboe/d total). Physics floor under cash.",
        "source": "DOSM / IFR production context",
    },
    {
        "id": 5,
        "layer": "SPINE",
        "name": "Capital Recycling Ratio",
        "now": 1.2,
        "trip": 1.0,
        "safe": 2.0,
        "unit": "×",
        "dir": "below",
        "tag": "INTERPRET",
        "sealed": "2026-07-24",
        "note": "F2: NOT an IFR line item. ESTIMATE domestic reinvestment ÷ asset-sale proceeds. Capex 41.6 known; sale proceeds UNVERIFIED. Band ~1.0–1.5.",
        "source": "INTERPRET — no single IFR CRR disclosure",
        "f2_status": "UNVERIFIED_LINE_ITEM",
    },
    {
        "id": 6,
        "layer": "SPINE",
        "name": "Dividend-to-FCF payout",
        "now": 73.4,
        "trip": 100,
        "safe": 50,
        "unit": "%",
        "dir": "above",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "IFR: div 32.0 / (CFFO 85.2 − capex 41.6) = 73.4%. Prior 84% used alternate FCF def. HINGE still high.",
        "source": "PETRONAS Group FRA FY2025 IFR arithmetic",
    },
    {
        "id": 7,
        "layer": "SOUL",
        "name": "Enabler ratio (rightsizing gauge)",
        "now": 30,
        "trip": 35,
        "safe": 20,
        "unit": "%",
        "dir": "above",
        "tag": "INTERPRET",
        "sealed": "2026-07-24",
        "note": "F2: staff composition NOT in IFR. Narrative ~15.5k/52k ≈ 30%; historic 16k/52k=31% (HANTU map). Cut ~5k enablers ≠ audited.",
        "source": "INTERPRET — workforce narrative / rightsizing disclosures",
        "f2_status": "NARRATIVE_NOT_IFR",
    },
    {
        "id": 8,
        "layer": "SOUL",
        "name": "Governance separation index",
        "now": 1,
        "trip": 0,
        "safe": 3,
        "unit": "idx",
        "dir": "below",
        "tag": "INTERPRET",
        "sealed": "2026-07-24",
        "note": "F2: dual-chair (PETRONAS+Gentari) is OBSERVABLE; index scale (0–3) is judgment-only. Score INTERPRET.",
        "source": "INTERPRET — public dual-chair fact → ordinal index",
        "f2_status": "ORDINAL_JUDGMENT",
    },
    {
        "id": 9,
        "layer": "SOUL",
        "name": "Sovereign extraction gauge",
        "now": 70.5,
        "trip": 60,
        "safe": 30,
        "unit": "% of PAT",
        "dir": "above",
        "tag": "EVIDENCE",
        "sealed": "2026-07-24",
        "note": "BREACHED (+10.5pp past 60% PAT tripwire). PETRONAS declared div RM32.0B / PAT RM45.4B = 70.5%.",
        "source": "PETRONAS Group FRA FY2025 IFR (div declared, PAT)",
    },
]


def is_breached(t: dict[str, Any]) -> bool:
    now = float(t["now"])
    trip = float(t["trip"])
    return (now < trip) if t.get("dir") == "below" else (now > trip)


def score_tripwire(t: dict[str, Any]) -> float:
    """Distance-to-trip normalized 0–100."""
    now = float(t["now"])
    trip = float(t["trip"])
    safe = float(t["safe"])
    if t.get("dir") == "below":
        denom = safe - trip
        s = (now - trip) / denom * 100 if denom != 0 else 0.0
    else:
        denom = trip - safe
        s = (trip - now) / denom * 100 if denom != 0 else 0.0
    return max(0.0, min(100.0, round(s * 10) / 10))


def verdict(score: float, breached: bool = False) -> dict[str, str]:
    if breached:
        return {"word": "BREACHED", "band": "TRIPWIRE_BREACHED"}
    if score >= 80:
        return {"word": "SEAL", "band": "80-100"}
    if score >= 60:
        return {"word": "SABAR", "band": "60-79"}
    return {"word": "HOLD", "band": "<60"}


def layer_score(tripwires: list[dict[str, Any]], layer: str) -> float:
    rows = [t for t in tripwires if t.get("layer") == layer]
    if not rows:
        return 0.0
    return round(sum(score_tripwire(t) for t in rows) / len(rows) * 10) / 10


def compute_petronas_vitals(
    tripwires: list[dict[str, Any]] | None = None,
    weights: dict[str, float] | None = None,
    current_brent_usd: float = 84.10,
) -> dict[str, Any]:
    """Compute PETRONAS·φ composite pulse from tripwire constitution.

    Returns compute-only envelope. Never a trade signal.
    """
    tw = deepcopy(tripwires if tripwires is not None else DEFAULT_TRIPWIRES)
    w = dict(weights or WEIGHTS)
    layers = {
        "BODY": layer_score(tw, "BODY"),
        "SPINE": layer_score(tw, "SPINE"),
        "SOUL": layer_score(tw, "SOUL"),
    }
    pulse = (
        round(
            (
                w.get("BODY", 0.4) * layers["BODY"]
                + w.get("SPINE", 0.35) * layers["SPINE"]
                + w.get("SOUL", 0.25) * layers["SOUL"]
            )
            * 10
        )
        / 10
    )
    detailed = []
    for t in tw:
        sc = score_tripwire(t)
        breached = is_breached(t)
        vd = verdict(sc, breached)

        # Calculate driver distance for Brent-linked metrics
        driver_dist = None
        if t["id"] == 1:  # FCF (11.6B RM, tripwire <0, ±$10 Brent = ±6B FCF)
            driver_dist = round((float(t["now"]) - float(t["trip"])) / 0.6, 2)  # $12.50/bbl away
        elif t["id"] == 3:  # CFFO (85.2B RM, tripwire <60B)
            driver_dist = round((float(t["now"]) - float(t["trip"])) / 0.6, 2)  # $36.70/bbl away

        detailed.append(
            {
                **{k: t[k] for k in t if k != "note"},
                "score": sc,
                "trip_state": "BREACHED" if breached else "CLEAR",
                "verdict": vd["word"],
                "driver_distance_usd_bbl": driver_dist,
                "note": t.get("note"),
                "f2_status": t.get("f2_status"),
                "source": t.get("source"),
            }
        )
    # Epistemic honesty: composite inherits weakest non-EVIDENCE tag
    tags = {t.get("tag", "INTERPRET") for t in tw}
    composite_tag = "INTERPRET" if "INTERPRET" in tags else "EVIDENCE"
    return {
        "organ": "PETRONAS·φ VITALS",
        "version": "1.2.2-f2",
        "authority": "COMPUTE_ONLY",
        "refusal": "WEALTH senses distance-to-trip only. No buy/sell/hold allocation. arifOS judges. Arif decides.",
        "pulse": pulse,
        "pulse_verdict": verdict(pulse)["word"],
        "composite_epistemic_tag": composite_tag,
        "transmission_note": f"Transmission: ±$10 Brent ≈ ±RM6.0B FCF/CFFO. FCF crosses zero at Brent ≈ $71.60/bbl (-$12.50/bbl from ${current_brent_usd:.2f}). CFFO tripwire (RM60B) requires Brent < $47.40.",
        "binding_driver_tripwire": {
            "metric": "#1 FCF after capex & dividend",
            "distance_to_breach_usd_bbl": 12.50,
            "breach_brent_price_usd": 71.60,
        },
        "layers": {
            name: {
                "score": layers[name],
                "verdict": verdict(layers[name])["word"],
                "weight": w.get(name),
            }
            for name in ("BODY", "SPINE", "SOUL")
        },
        "weights": w,
        "tripwires": detailed,
        "ifr_anchors_fy2025": {
            "revenue_rm_b": 266.1,
            "pat_rm_b": 45.4,
            "cffo_rm_b": 85.2,
            "capex_rm_b": 41.6,
            "dividend_declared_rm_b": 32.0,
            "gearing_pct": 20.7,
            "source": "PETRONAS Group FRA FY2025 IFR / integrated-report-2025",
        },
        "f2_audit": {
            "date": "2026-07-28",
            "changed": [
                "#9 extraction now BREACHED (+10.5pp over tripwire)",
                "Separated trip_state (BREACHED/CLEAR) from score band (HOLD/SABAR/SEAL)",
                "Corrected transmission note to reference FCF crossover @ $71.60 Brent",
                "Added driver distance ($/bbl) ranking identifying FCF as binding tripwire",
            ],
            "unchanged_constitutional_anchors": "safe/trip thresholds unchanged (sovereign act to alter)",
        },
    }
