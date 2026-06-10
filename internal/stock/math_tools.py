"""
WEALTH Stock Analysis — Deterministic Math Tools
════════════════════════════════════════════════

Four pure-math tools. No API calls. No AI. Just arithmetic.
Purpose: Stop AI number hallucination in trading contexts.

DITEMPA BUKAN DIBERI — Numbers are forged, not hallucinated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import math


# ─── Tool 1: verify_trade_math ──────────────────────────────────────────


def verify_trade_math(
    ticker: str = "",
    entry_price: float = 0.0,
    exit_price: Optional[float] = None,
    current_price: Optional[float] = None,
    position_size: int = 0,
    fees: float = 0.0,
    direction: str = "long",
    status: str = "unrealized",
    journal_pnl: Optional[float] = None,
    journal_pnl_pct: Optional[float] = None,
) -> dict:
    """Stop AI number hallucination. Recalculate everything deterministically.

    Returns gross P/L, net P/L, and flags any discrepancy with a
    journal-reported P/L value.

    Verdicts: OK | MATH_ERROR | NEEDS_DATA
    """
    warnings: List[str] = []
    missing: List[str] = []

    if not ticker:
        missing.append("ticker")
    if entry_price <= 0:
        missing.append("entry_price")
    if position_size <= 0:
        missing.append("position_size")

    price = exit_price if status == "realized" and exit_price else current_price
    if price is None or price <= 0:
        missing.append("exit_price" if status == "realized" else "current_price")

    if missing:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": missing,
            "warnings": ["Cannot compute P/L without complete inputs."],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    # ── Gross P/L ──
    if direction == "short":
        gross_pl_rm = (entry_price - price) * position_size
    else:
        gross_pl_rm = (price - entry_price) * position_size

    gross_invested = entry_price * position_size
    gross_pl_pct = (gross_pl_rm / gross_invested) * 100.0 if gross_invested else 0.0

    # ── Net P/L (after fees) ──
    net_pl_rm = gross_pl_rm - fees
    net_pl_pct = (net_pl_rm / gross_invested) * 100.0 if gross_invested else 0.0

    # ── Journal comparison ──
    journal_error = False
    diff_vs_journal = None
    if journal_pnl is not None:
        diff_vs_journal = round(gross_pl_rm - journal_pnl, 4)
        if abs(diff_vs_journal) > 0.01:
            journal_error = True
            warnings.append(
                f"JOURNAL_DISCREPANCY: calculated gross P/L = RM{gross_pl_rm:.2f}, "
                f"journal claims RM{journal_pnl:.2f}. Difference: RM{diff_vs_journal:.2f}."
            )
    if journal_pnl_pct is not None:
        calc_pct = round(gross_pl_pct, 2)
        if abs(calc_pct - journal_pnl_pct) > 0.01:
            journal_error = True
            warnings.append(
                f"JOURNAL_PCT_DISCREPANCY: calculated = {calc_pct}%, "
                f"journal claims {journal_pnl_pct}%."
            )

    result = {
        "ticker": ticker.upper(),
        "entry_price": entry_price,
        "exit_or_current_price": price,
        "position_size": position_size,
        "direction": direction,
        "status": status,
        "gross_invested_rm": round(gross_invested, 2),
        "gross_pl_rm": round(gross_pl_rm, 2),
        "gross_pl_pct": round(gross_pl_pct, 2),
        "fees_rm": round(fees, 2),
        "net_pl_rm": round(net_pl_rm, 2),
        "net_pl_pct": round(net_pl_pct, 2),
        "formula_used": f"({'P_exit' if status == 'realized' else 'P_current'} - P_entry) × size {'/' if direction == 'long' else '× (-1)'}",
    }
    if diff_vs_journal is not None:
        result["difference_vs_journal_rm"] = diff_vs_journal

    return {
        "status": "OK",
        "verdict": "MATH_ERROR" if journal_error else "SAFE_TO_STUDY",
        "result": result,
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 2: separate_realized_unrealized ───────────────────────────────


def separate_realized_unrealized(
    trades: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """Stop paper profits from pretending to be real profits.

    Separates realized and unrealized P/L from a list of trades.
    Each trade dict must have: ticker, status (realized/unrealized),
    gross_pl_rm, gross_pl_pct, position_value_rm.
    """
    warnings: List[str] = []
    if not trades:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": ["trades"],
            "warnings": ["No trade data provided."],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    realized_pl = 0.0
    realized_count = 0
    unrealized_pl = 0.0
    unrealized_count = 0
    open_exposure = 0.0

    for i, t in enumerate(trades):
        status = str(t.get("status", "")).lower()
        pl = float(t.get("gross_pl_rm", 0) or 0)
        pos_val = float(t.get("position_value_rm", 0) or 0)

        if status == "realized":
            realized_pl += pl
            realized_count += 1
        elif status == "unrealized":
            unrealized_pl += pl
            unrealized_count += 1
            open_exposure += pos_val
        else:
            warnings.append(f"Trade {i}: unknown status '{status}' — skipped.")

    total_pl = realized_pl + unrealized_pl

    # ── The critical warning ──
    if realized_pl < 0 and unrealized_pl > 0 and total_pl > 0:
        warnings.append(
            "PAPER_PROFIT_WARNING: Realized P/L is negative (RM%.2f). "
            "Total looks positive only because of unrealized gains (RM%.2f). "
            "Do NOT call this period profitable. Open positions are currently "
            "marked positive, not closed positive." % (realized_pl, unrealized_pl)
        )

    return {
        "status": "OK",
        "verdict": "SAFE_TO_STUDY",
        "result": {
            "realized_pl_rm": round(realized_pl, 2),
            "realized_trade_count": realized_count,
            "unrealized_pl_rm": round(unrealized_pl, 2),
            "unrealized_trade_count": unrealized_count,
            "total_pl_rm": round(total_pl, 2),
            "open_exposure_rm": round(open_exposure, 2),
            "timestamp": "",
        },
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 3: calculate_position_size ────────────────────────────────────


def calculate_position_size(
    account_balance: float = 0.0,
    entry_price: float = 0.0,
    stop_loss: float = 0.0,
    risk_per_trade_pct: float = 1.0,
) -> dict:
    """Risk-based position sizing. Never trade without knowing max loss.

    Returns max shares, max position value, and risk per share.
    Hard gate: risk_per_trade_pct > 1% → UNSAFE.
    """
    warnings: List[str] = []
    missing: List[str] = []

    if account_balance <= 0:
        missing.append("account_balance")
    if entry_price <= 0:
        missing.append("entry_price")
    if stop_loss <= 0:
        missing.append("stop_loss")

    if missing:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": missing,
            "warnings": warnings,
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    if risk_per_trade_pct > 1.0:
        warnings.append(
            f"RISK_EXCESSIVE: risk_per_trade_pct = {risk_per_trade_pct}% exceeds 1% hard limit."
        )

    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share <= 0:
        return {
            "status": "ERROR",
            "verdict": "UNSAFE",
            "warnings": [
                "Stop loss must differ from entry price. Risk per share is zero."
            ],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    max_rm_risk = account_balance * (risk_per_trade_pct / 100.0)
    max_shares = int(max_rm_risk / risk_per_share)
    max_position_value = max_shares * entry_price
    position_pct = (
        (max_position_value / account_balance) * 100.0 if account_balance else 0.0
    )

    return {
        "status": "OK",
        "verdict": "UNSAFE" if risk_per_trade_pct > 1.0 else "SAFE_TO_STUDY",
        "result": {
            "account_balance_rm": round(account_balance, 2),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_per_trade_pct": risk_per_trade_pct,
            "max_rm_risk": round(max_rm_risk, 2),
            "risk_per_share": round(risk_per_share, 4),
            "max_shares": max_shares,
            "max_position_value": round(max_position_value, 2),
            "position_as_pct_of_account": round(position_pct, 1),
        },
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 4: calculate_r_multiple ───────────────────────────────────────


def calculate_r_multiple(
    entry_price: float = 0.0,
    stop_loss: float = 0.0,
    target_price: float = 0.0,
    direction: str = "long",
) -> dict:
    """Risk-reward geometry. R = reward / risk.

    Hard gates:
      R < 2.0 → UNSAFE (unless exceptional reason)
      R < 2.5 → WEAK_ASYMMETRY
      R >= 2.5 → acceptable asymmetry
      R >= 3.0 → strong asymmetry
    """
    missing: List[str] = []
    if entry_price <= 0:
        missing.append("entry_price")
    if stop_loss <= 0:
        missing.append("stop_loss")
    if target_price <= 0:
        missing.append("target_price")

    if missing:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": missing,
            "warnings": [],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    if direction == "long":
        risk = entry_price - stop_loss
        reward = target_price - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - target_price

    if risk <= 0:
        return {
            "status": "ERROR",
            "verdict": "UNSAFE",
            "warnings": [
                "Risk is zero or negative. Stop loss must be below entry (long) or above entry (short)."
            ],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    r_multiple = reward / risk
    risk_pct = (risk / entry_price) * 100.0
    reward_pct = (reward / entry_price) * 100.0

    if r_multiple >= 3.0:
        asymmetry = "STRONG"
        verdict = "SAFE_TO_STUDY"
    elif r_multiple >= 2.5:
        asymmetry = "ACCEPTABLE"
        verdict = "SAFE_TO_STUDY"
    elif r_multiple >= 2.0:
        asymmetry = "WEAK"
        verdict = "SAFE_TO_STUDY"
    else:
        asymmetry = "UNACCEPTABLE"
        verdict = "UNSAFE"

    return {
        "status": "OK",
        "verdict": verdict,
        "result": {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "direction": direction,
            "risk_per_share": round(risk, 4),
            "risk_pct": round(risk_pct, 2),
            "reward_per_share": round(reward, 4),
            "reward_pct": round(reward_pct, 2),
            "r_multiple": round(r_multiple, 2),
            "asymmetry_grade": asymmetry,
            "rule": "R >= 2.5 → acceptable. R >= 3.0 → strong. R < 2.0 → UNSAFE.",
        },
        "warnings": [f"R = {r_multiple:.2f} — {asymmetry}"]
        if asymmetry in ("WEAK", "UNACCEPTABLE")
        else [],
        "recommendation_only": True,
        "final_authority": "Arif",
    }
