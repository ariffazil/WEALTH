"""
WEALTH Stock Analysis — Fundamental Invariants Engine
══════════════════════════════════════════════════════

9 business-reality invariants that must pass before technicals.
Checks: cash flow, balance sheet, profitability, ROIC, growth quality,
dilution, valuation, business quality, governance.

DITEMPA BUKAN DIBERI — Fundamentals are forged, not assumed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def check_fundamental_invariants(
    ticker: str = "",
    # F1: Cash Flow
    operating_cash_flow: Optional[float] = None,
    free_cash_flow: Optional[float] = None,
    cash_conversion: Optional[float] = None,
    # F2: Balance Sheet
    cash: Optional[float] = None,
    total_debt: Optional[float] = None,
    current_ratio: Optional[float] = None,
    interest_coverage: Optional[float] = None,
    debt_maturity_years: Optional[float] = None,
    # F3: Profitability
    gross_margin: Optional[float] = None,
    operating_margin: Optional[float] = None,
    net_margin: Optional[float] = None,
    margin_trend: str = "stable",  # "improving", "stable", "declining"
    # F4: Return on Capital
    roic: Optional[float] = None,
    roe: Optional[float] = None,
    # F5: Growth Quality
    revenue_growth: Optional[float] = None,
    fcf_growth: Optional[float] = None,
    organic_growth: bool = True,
    debt_funded_growth: bool = False,
    # F6: Dilution
    shares_outstanding_m: Optional[float] = None,
    dilution_rate: Optional[float] = None,
    has_warrants: bool = False,
    has_convertibles: bool = False,
    has_esos: bool = False,
    # F7: Valuation
    pe_ratio: Optional[float] = None,
    pb_ratio: Optional[float] = None,
    ev_ebitda: Optional[float] = None,
    fcf_yield: Optional[float] = None,
    # F8: Business Quality
    has_moat: bool = False,
    pricing_power: bool = False,
    recurring_revenue: bool = False,
    # F9: Governance
    related_party_txns: bool = False,
    insider_selling: bool = False,
    audit_issues: bool = False,
    pledged_shares_pct: Optional[float] = None,
) -> dict:
    """Check 9 fundamental business invariants.

    Returns per-invariant verdict + overall seal recommendation.
    Verdicts: PASS | FLAG | WARNING | FAIL | INSUFFICIENT_DATA
    """
    invariants: List[Dict[str, Any]] = []
    flags: List[str] = []
    passed = 0
    total_evaluated = 0
    total_defined = 9  # we always count all 9 even if some have no data

    # ── F1: Cash Flow ──
    f1_data = (operating_cash_flow is not None) or (free_cash_flow is not None)
    if f1_data:
        total_evaluated += 1
        f1_issues: List[str] = []
        if free_cash_flow is not None and free_cash_flow < 0:
            f1_issues.append(f"Negative FCF: {free_cash_flow}")
        if operating_cash_flow is not None and free_cash_flow is not None:
            if free_cash_flow < operating_cash_flow * 0.3:
                f1_issues.append("FCF < 30% of OCF — high capex or weak conversion")
        if cash_conversion is not None and cash_conversion < 0.8:
            f1_issues.append(f"Low cash conversion: {cash_conversion}")

        f1_verdict = (
            "PASS" if not f1_issues else "WARNING" if len(f1_issues) == 1 else "FLAG"
        )
        if f1_verdict == "PASS":
            passed += 1
        elif f1_verdict in ("FLAG", "WARNING"):
            flags.extend(f1_issues)
        invariants.append(
            {
                "invariant": "F1_CASH_FLOW",
                "tagline": "Cash flow = oxygen",
                "verdict": f1_verdict,
                "issues": f1_issues,
                "data": {
                    "operating_cf": operating_cash_flow,
                    "free_cf": free_cash_flow,
                    "cash_conversion": cash_conversion,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F1_CASH_FLOW",
                "tagline": "Cash flow = oxygen",
                "verdict": "INSUFFICIENT_DATA",
                "issues": ["No cash flow data provided"],
                "data": {},
            }
        )

    # ── F2: Balance Sheet ──
    f2_data = any(
        v is not None for v in [cash, total_debt, current_ratio, interest_coverage]
    )
    if f2_data:
        total_evaluated += 1
        f2_issues: List[str] = []
        if cash is not None and total_debt is not None and total_debt > 0:
            net_debt_ratio = (total_debt - cash) / total_debt if total_debt else 0
            if net_debt_ratio > 0.8:
                f2_issues.append(
                    f"Net debt = {net_debt_ratio:.0%} of gross debt — low cash buffer"
                )
        if current_ratio is not None and current_ratio < 1.0:
            f2_issues.append(f"Current ratio < 1.0: {current_ratio}")
        if interest_coverage is not None and interest_coverage < 3.0:
            f2_issues.append(f"Interest coverage < 3x: {interest_coverage}")
        if debt_maturity_years is not None and debt_maturity_years < 2.0:
            f2_issues.append(f"Near-term debt maturity: {debt_maturity_years} years")

        f2_verdict = (
            "PASS" if not f2_issues else "FLAG" if len(f2_issues) >= 2 else "WARNING"
        )
        if f2_verdict == "PASS":
            passed += 1
        elif f2_verdict in ("FLAG", "WARNING"):
            flags.extend(f2_issues)
        invariants.append(
            {
                "invariant": "F2_BALANCE_SHEET",
                "tagline": "Debt = pressure. Too much cracks structure.",
                "verdict": f2_verdict,
                "issues": f2_issues,
                "data": {
                    "cash": cash,
                    "total_debt": total_debt,
                    "current_ratio": current_ratio,
                    "interest_coverage": interest_coverage,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F2_BALANCE_SHEET",
                "tagline": "Debt = pressure.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F3: Profitability ──
    f3_data = any(v is not None for v in [gross_margin, operating_margin, net_margin])
    if f3_data:
        total_evaluated += 1
        f3_issues: List[str] = []
        if net_margin is not None and net_margin <= 0:
            f3_issues.append(f"Negative net margin: {net_margin}")
        elif net_margin is not None and net_margin < 5:
            f3_issues.append(f"Thin net margin: {net_margin}%")
        if operating_margin is not None and operating_margin < 10:
            f3_issues.append(f"Low operating margin: {operating_margin}%")
        if margin_trend == "declining":
            f3_issues.append("Margins declining")

        f3_verdict = (
            "PASS" if not f3_issues else "FLAG" if len(f3_issues) >= 2 else "WARNING"
        )
        if f3_verdict == "PASS":
            passed += 1
        elif f3_verdict in ("FLAG", "WARNING"):
            flags.extend(f3_issues)
        invariants.append(
            {
                "invariant": "F3_PROFITABILITY",
                "tagline": "Profit = usable energy.",
                "verdict": f3_verdict,
                "issues": f3_issues,
                "data": {
                    "gross_margin": gross_margin,
                    "op_margin": operating_margin,
                    "net_margin": net_margin,
                    "trend": margin_trend,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F3_PROFITABILITY",
                "tagline": "Profit = usable energy.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F4: Return on Capital ──
    f4_data = any(v is not None for v in [roic, roe])
    if f4_data:
        total_evaluated += 1
        f4_issues: List[str] = []
        if roic is not None and roic < 10:
            f4_issues.append(f"ROIC below 10%: {roic}%")
        if roe is not None and roe < 12:
            f4_issues.append(f"ROE below 12%: {roe}%")

        f4_verdict = (
            "PASS" if not f4_issues else "FLAG" if len(f4_issues) >= 2 else "WARNING"
        )
        if f4_verdict == "PASS":
            passed += 1
        elif f4_verdict in ("FLAG", "WARNING"):
            flags.extend(f4_issues)
        invariants.append(
            {
                "invariant": "F4_RETURN_ON_CAPITAL",
                "tagline": "Capital must reproduce.",
                "verdict": f4_verdict,
                "issues": f4_issues,
                "data": {"roic": roic, "roe": roe},
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F4_RETURN_ON_CAPITAL",
                "tagline": "Capital must reproduce.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F5: Growth Quality ──
    f5_data = revenue_growth is not None or fcf_growth is not None
    if f5_data:
        total_evaluated += 1
        f5_issues: List[str] = []
        if revenue_growth is not None and revenue_growth < 0:
            f5_issues.append(f"Revenue declining: {revenue_growth}%")
        if not organic_growth:
            f5_issues.append("Growth driven by acquisitions, not organic")
        if debt_funded_growth:
            f5_issues.append("Growth funded by debt — leverage risk")

        f5_verdict = (
            "PASS" if not f5_issues else "FLAG" if len(f5_issues) >= 2 else "WARNING"
        )
        if f5_verdict == "PASS":
            passed += 1
        elif f5_verdict in ("FLAG", "WARNING"):
            flags.extend(f5_issues)
        invariants.append(
            {
                "invariant": "F5_GROWTH_QUALITY",
                "tagline": "Growth without structure = cancer.",
                "verdict": f5_verdict,
                "issues": f5_issues,
                "data": {
                    "revenue_growth": revenue_growth,
                    "fcf_growth": fcf_growth,
                    "organic": organic_growth,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F5_GROWTH_QUALITY",
                "tagline": "Growth without structure = cancer.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F6: Dilution ──
    f6_data = dilution_rate is not None or shares_outstanding_m is not None
    if f6_data:
        total_evaluated += 1
        f6_issues: List[str] = []
        if dilution_rate is not None and dilution_rate > 3.0:
            f6_issues.append(f"Dilution rate {dilution_rate}% — ownership entropy high")
        if has_warrants:
            f6_issues.append("Outstanding warrants — potential dilution")
        if has_convertibles:
            f6_issues.append("Convertible instruments — potential dilution")
        if has_esos:
            f6_issues.append("ESOS — modest dilution expected, but monitor")

        f6_verdict = (
            "PASS"
            if not f6_issues
            or f6_issues == ["ESOS — modest dilution expected, but monitor"]
            else "FLAG"
            if len(f6_issues) >= 2
            else "WARNING"
        )
        # ESOS only = still PASS (normal for Malaysian listed companies)
        if f6_issues == ["ESOS — modest dilution expected, but monitor"]:
            f6_verdict = "PASS"
        if f6_verdict == "PASS":
            passed += 1
        elif f6_verdict in ("FLAG", "WARNING"):
            flags.extend(f6_issues)
        invariants.append(
            {
                "invariant": "F6_DILUTION",
                "tagline": "Dilution = entropy of ownership.",
                "verdict": f6_verdict,
                "issues": f6_issues,
                "data": {
                    "dilution_rate": dilution_rate,
                    "warrants": has_warrants,
                    "convertibles": has_convertibles,
                    "esos": has_esos,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F6_DILUTION",
                "tagline": "Dilution = entropy of ownership.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F7: Valuation ──
    f7_data = any(v is not None for v in [pe_ratio, pb_ratio, ev_ebitda, fcf_yield])
    if f7_data:
        total_evaluated += 1
        f7_issues: List[str] = []
        if pe_ratio is not None and pe_ratio > 30:
            f7_issues.append(
                f"P/E {pe_ratio} — expensive. Future return gets pulled down."
            )
        elif pe_ratio is not None and pe_ratio < 0:
            f7_issues.append("Negative P/E — company is losing money")
        if pb_ratio is not None and pb_ratio > 5:
            f7_issues.append(f"P/B {pb_ratio} — well above book value")
        if ev_ebitda is not None and ev_ebitda > 20:
            f7_issues.append(f"EV/EBITDA {ev_ebitda} — rich valuation")
        if fcf_yield is not None and fcf_yield < 3:
            f7_issues.append(f"FCF yield {fcf_yield}% — below EPF rate")

        f7_verdict = (
            "PASS" if not f7_issues else "WARNING" if len(f7_issues) == 1 else "FLAG"
        )
        if f7_verdict == "PASS":
            passed += 1
        elif f7_verdict in ("FLAG", "WARNING"):
            flags.extend(f7_issues)
        invariants.append(
            {
                "invariant": "F7_VALUATION",
                "tagline": "Price is gravity.",
                "verdict": f7_verdict,
                "issues": f7_issues,
                "data": {
                    "pe": pe_ratio,
                    "pb": pb_ratio,
                    "ev_ebitda": ev_ebitda,
                    "fcf_yield": fcf_yield,
                },
            }
        )
    else:
        invariants.append(
            {
                "invariant": "F7_VALUATION",
                "tagline": "Price is gravity.",
                "verdict": "INSUFFICIENT_DATA",
                "issues": [],
                "data": {},
            }
        )

    # ── F8: Business Quality ──
    total_evaluated += 1  # always evaluated — qualitative flags
    f8_issues: List[str] = []
    if not has_moat:
        f8_issues.append("No identifiable moat")
    if not pricing_power:
        f8_issues.append("Limited pricing power")
    if not recurring_revenue:
        f8_issues.append("Revenue not recurring — higher cyclicality risk")

    f8_verdict = "PASS" if not f8_issues else "FLAG"
    if f8_verdict == "PASS":
        passed += 1
    else:
        flags.extend(f8_issues)
    invariants.append(
        {
            "invariant": "F8_BUSINESS_QUALITY",
            "tagline": "Moat prevents value leakage.",
            "verdict": f8_verdict,
            "issues": f8_issues,
            "data": {
                "moat": has_moat,
                "pricing_power": pricing_power,
                "recurring_revenue": recurring_revenue,
            },
        }
    )

    # ── F9: Governance ──
    total_evaluated += 1  # always evaluated
    f9_issues: List[str] = []
    if related_party_txns:
        f9_issues.append("Related party transactions detected")
    if insider_selling:
        f9_issues.append("Insider selling — those who know are reducing")
    if audit_issues:
        f9_issues.append("Audit issues flagged")
    if pledged_shares_pct is not None and pledged_shares_pct > 30:
        f9_issues.append(f"Pledged shares {pledged_shares_pct}% — margin call risk")

    f9_verdict = (
        "PASS" if not f9_issues else "FLAG" if len(f9_issues) >= 2 else "WARNING"
    )
    if f9_verdict == "PASS":
        passed += 1
    else:
        flags.extend(f9_issues)
    invariants.append(
        {
            "invariant": "F9_GOVERNANCE",
            "tagline": "Management is the steering system.",
            "verdict": f9_verdict,
            "issues": f9_issues,
            "data": {
                "related_party": related_party_txns,
                "insider_selling": insider_selling,
                "audit_issues": audit_issues,
                "pledged_pct": pledged_shares_pct,
            },
        }
    )

    # ── Overall ──
    flag_count = sum(1 for inv in invariants if inv["verdict"] == "FLAG")
    warn_count = sum(1 for inv in invariants if inv["verdict"] == "WARNING")
    missing_count = sum(
        1 for inv in invariants if inv["verdict"] == "INSUFFICIENT_DATA"
    )

    if flag_count >= 3:
        overall = "UNSAFE"
    elif flag_count >= 1:
        overall = "NEEDS_DATA"
    elif warn_count >= 2:
        overall = "NEEDS_DATA"
    elif missing_count >= 5:
        overall = "NEEDS_DATA"
    elif missing_count >= 7:
        overall = "UNSAFE"
    else:
        overall = "SAFE_TO_STUDY"

    return {
        "status": "OK",
        "verdict": overall,
        "result": {
            "ticker": ticker.upper() if ticker else "?",
            "invariants_passed": passed,
            "invariants_evaluated": total_evaluated,
            "invariants_flagged": flag_count,
            "invariants_warned": warn_count,
            "invariants_missing_data": missing_count,
            "overall_fundamental_verdict": overall,
            "invariants": invariants,
            "flags": flags,
            "rule": "Fundamentals before technicals. No fundamental seal = no trade.",
        },
        "warnings": flags,
        "recommendation_only": True,
        "final_authority": "Arif",
    }
