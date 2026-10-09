"""Calibrated collapse-signature layer v2 (LAW-WEALTH-01 first release, 2026-09-16).

The v1 detector matched fixed narrative phrases and returned a confident
MINIMAL on the exact case it existed to catch (an adversarial paraphrase of
PETRONAS extraction facts — "sovereign extraction" is not in the phrase
lists). This layer adds what the witness verdict demanded: mechanism, not
vocabulary.

Three additions, all additive to the existing profile:

1. QUANTITATIVE TRIGGERS — hard, paraphrase-immune numeric/structural
   evidence (payout percentages, cadence changes, offshore transfers,
   impairments, guarantee structures, board zeros, capex collapse).
2. SEMANTIC MECHANISMS — paraphrase-tolerant concept regexes (extraction,
   stripping, visibility compression, loyalty appointments, kickback
   inflation, off-balance concealment).
3. COVERAGE DISCIPLINE — MINIMAL risk is forbidden unless evidence coverage
   is adequate; thin evidence yields INSUFFICIENT_DATA with named missing
   fields. Hard triggers floor the risk at MODERATE (ELEVATED across >=2
   axes) regardless of narrative phrasing.
"""

from __future__ import annotations

import re
from typing import Optional

# (id, axis, evidence_field, compiled regex)
_QUANT_SPECS = [
    ("QT_PAYOUT_PCT", "fiscal_extraction", "payout_ratio_or_pct",
     re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent|per\s?cent|sen)\b[^.\n]{0,60}(?:of\s+)?(?:every\s+)?(?:ringgit|dollar|profit|pat|earnings|net\s+income|revenue)", re.I)),
    ("QT_RATIO_SLASH", "fiscal_extraction", "payout_ratio_or_pct",
     re.compile(r"(?:dividend|payout)[^.\n]{0,40}\d+(?:\.\d+)?\s*/\s*(?:PAT|profit|earnings)", re.I)),
    ("QT_TAX_OVER_INCOME", "fiscal_extraction", "payout_ratio_or_pct",
     re.compile(r"(?:tax(?:es)?|duty|lev(?:y|ies))[^.\n]{0,60}(?:exceed\w*|greater\s+than|more\s+than|above|>)", re.I)),
    ("QT_CADENCE_EROSION", "disclosure_erosion", "cadence_statement",
     re.compile(r"(?:quarterly|quarter(?:ly)?\s+report\w*)[^.\n]{0,80}(?:semi-?annual|half-?yearly|half-?year|bi-?annual)", re.I)),
    ("QT_OFFSHORE_TRANSFER", "asset_ringfencing", "transfer_structure",
     re.compile(r"(?:transfer\w*|relocat\w*|mov(?:e|ed|ing)|ring[- ]?fenc\w*)[^.\n]{0,120}(?:UK|United Kingdom|offshore|SPV|special[- ]purpose|Cayman|British Virgin|English law)", re.I)),
    ("QT_IMPAIRMENT", "loss_concealment", "loss_figure",
     re.compile(r"(?:RM|US\$|USD|\$)\s?\d+(?:\.\d+)?\s*[Bb](?:n|il(?:lion)?)?[^.\n]{0,100}(?:loss|impairment|write[- ]?down|non-?cash)", re.I)),
    ("QT_GUARANTEE_DEBT", "loss_concealment", "debt_structure",
     re.compile(r"guarantee\w*[^.\n]{0,100}(?:notes?|debt|bonds?|facility|program)", re.I)),
    ("QT_CAPFLOOR_COLLISION", "fiscal_extraction", "debt_structure",
     re.compile(r"(?:dividend\s*)?(?:cap|ceiling)[^.\n]{0,100}\bfloor\b", re.I)),
    ("QT_BOARD_INDEP_ZERO", "governance_concentration", "governance_composition",
     re.compile(r"independent[^.\n]{0,60}(?:NED|non-?executive\s+director)[^.\n]{0,60}(?:zero|\b0\b|none|no\s+independent)", re.I)),
    ("QT_CAPEX_COLLAPSE", "reinvestment_suppression", "reinvestment",
     re.compile(r"cap\w*[^.\n]{0,80}(?:cut|collapse|halv\w*|slash\w*|down\s+\d{1,3}\s*%)", re.I)),
    ("QT_PRODUCTION_DECLINE", "operational_erosion", "operations",
     re.compile(r"production[^.\n]{0,80}(?:declin\w*|fall\w*|down\s+(?:by\s+)?\d{1,3}\s*%|collapse\w*)", re.I)),
]

_SEMANTIC_SPECS = [
    ("SM_SOVEREIGN_EXTRACTION", "fiscal_extraction", "payout_ratio_or_pct",
     re.compile(r"(?:sovereign|state|government(?:al)?)\s+(?:extraction|take|taking|raid|harvest\w*|bleed\w*)", re.I)),
    ("SM_HARVEST_OVER_RENEW", "fiscal_extraction", "reinvestment",
     re.compile(r"harvest\w*\s+(?:faster|more\s+than)[^.\n]{0,60}renew\w*", re.I)),
    ("SM_ASSET_STRIPPING", "asset_ringfencing", "transfer_structure",
     re.compile(r"(?:asset\s*)?stripp\w+|value\s+transfer|capital\s+repatriation", re.I)),
    ("SM_VISIBILITY_COMPRESS", "disclosure_erosion", "cadence_statement",
     re.compile(r"(?:compress\w*|reduc\w*|narrow\w*|shift\w*)[^.\n]{0,60}(?:visibility|disclosure|transparency|reporting)", re.I)),
    ("SM_LOYALTY_APPOINT", "governance_concentration", "governance_composition",
     re.compile(r"(?:appoint\w*|promotion\w*)[^.\n]{0,80}(?:loyal\w*|political|party|cadre)", re.I)),
    ("SM_KICKBACK_INFLATE", "loss_concealment", "loss_figure",
     re.compile(r"(?:kickback|bribe\w*|markup|inflate\w*)[^.\n]{0,80}(?:contract|capex|project|cost)", re.I)),
    ("SM_OFFBALANCE_HIDE", "loss_concealment", "debt_structure",
     re.compile(r"off[- ](?:the\s+)?balance[^.\n]{0,80}(?:sheet|vehicle|SPE|entit)|special[- ]purpose\s+(?:entity|vehicle|entities)", re.I)),
    ("SM_MISSION_DRIFT", "reinvestment_suppression", "reinvestment",
     re.compile(r"(?:mission|purpose)\s+(?:drift|shift|abandon\w*)|(?:cash\s+)?cow\s+(?:mentality|mode)", re.I)),
]

_PROBE_FIELDS = [
    "payout_ratio_or_pct",
    "cadence_statement",
    "transfer_structure",
    "loss_figure",
    "debt_structure",
    "governance_composition",
    "reinvestment",
    "operations",
]

_RISK_RANK = {"MINIMAL": 0, "LOW": 0, "MODERATE": 1, "ELEVATED": 2, "HIGH": 2, "CRITICAL": 3}


def analyze(text: str) -> dict:
    hard, semantic = [], []
    present_fields = set()
    for spec_id, axis, field, rx in _QUANT_SPECS:
        m = rx.search(text or "")
        if not m:
            continue
        if spec_id == "QT_PAYOUT_PCT":
            # Only extraction-scale payouts are hard evidence; a healthy
            # 30% payout must not floor the risk (calibration lesson).
            try:
                if float(m.group(1)) < 50.0:
                    continue
            except (ValueError, IndexError):
                continue
        hard.append({"id": spec_id, "axis": axis, "field": field, "match": m.group(0)[:120]})
        present_fields.add(field)
    for spec_id, axis, field, rx in _SEMANTIC_SPECS:
        m = rx.search(text or "")
        if m:
            semantic.append({"id": spec_id, "axis": axis, "field": field, "match": m.group(0)[:120]})
            present_fields.add(field)
    missing = [f for f in _PROBE_FIELDS if f not in present_fields]
    coverage = round(len(_PROBE_FIELDS) - len(missing)) / max(1, len(_PROBE_FIELDS))
    return {
        "hard_triggers": hard,
        "semantic_mechanisms": semantic,
        "coverage": {
            "ratio": round(coverage, 2),
            "present": sorted(present_fields),
            "missing": missing,
            "adequate": coverage >= 0.5,
        },
    }


def calibrated_overlay(result: dict, analysis: dict) -> dict:
    """Merge calibrated discipline into the v1 result. Additive; never
    lowers risk; forbids confident negatives on thin evidence."""
    result = dict(result)
    result["quantitative_triggers"] = analysis["hard_triggers"]
    result["semantic_mechanism_hits"] = analysis["semantic_mechanisms"]
    result["evidence_coverage"] = analysis["coverage"]
    result["detector_version"] = "calibrated_v2_2026-09-16"

    risk = result.get("risk", {})
    level = str(risk.get("risk_level", "") or "").upper()
    hard_axes = {t["axis"] for t in analysis["hard_triggers"]}
    sem_axes = {t["axis"] for t in analysis["semantic_mechanisms"]}
    cov = analysis["coverage"]

    verdict = None
    floor = None
    if analysis["hard_triggers"]:
        floor = "ELEVATED" if len(hard_axes) >= 2 else "MODERATE"
        verdict = "COLLAPSE_SIGNATURE_QUANTITATIVE_TRIGGER"
    elif analysis["semantic_mechanisms"]:
        floor = "MODERATE"
        verdict = "SIGNATURE_SEMANTIC_ONLY"

    if floor is not None and _RISK_RANK.get(floor, 0) > _RISK_RANK.get(level, 0):
        risk = dict(risk)
        risk["risk_level"] = floor
        risk["risk_level_floored_by"] = "calibrated_v2"
        result["risk"] = risk

    if level in ("", "MINIMAL", "LOW") and (not cov["adequate"]) and not analysis["hard_triggers"]:
        # Thin evidence can never support a confident negative.
        result["verdict_discipline"] = "INSUFFICIENT_DATA"
        result["missing_evidence_fields"] = cov["missing"]
        result["recommendation"] = None
        if verdict is None:
            verdict = "INSUFFICIENT_DATA"
    if verdict:
        result["calibrated_verdict"] = verdict
    return result
