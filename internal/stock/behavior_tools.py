"""
WEALTH Stock Analysis — Human Behavior Tools
════════════════════════════════════════════

Tamak (greed) detection and pre-trade safety gate.
Purpose: Catch the human before the damage.

DITEMPA BUKAN DIBERI — Discipline is forged, not given.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ─── Tool 7: detect_tamak_behavior ──────────────────────────────────────


def detect_tamak_behavior(
    recent_trades: Optional[List[Dict[str, Any]]] = None,
    current_open_positions: int = 0,
    recent_streak: str = "neutral",  # "green", "red", "mixed", "neutral"
    recent_size_trend: str = "stable",  # "increasing", "decreasing", "stable"
    stop_loss_moved_lower: bool = False,
    averaging_down: bool = False,
    revenge_pattern: bool = False,
    chasing_call: bool = False,
    position_count: int = 0,
    max_recommended: int = 5,
) -> dict:
    """Detect tamak (greed) behavior patterns.

    Flags:
      - increasing size after green streak
      - forcing "close green" target
      - refusing to cut loss
      - averaging down
      - revenge trading
      - chasing analyst call
      - treating paper profit as skill
      - too many open trades
      - moving stop lower
    """
    flags: List[str] = []
    reasons: List[str] = []
    risk_level = "LOW"

    # 1. Size increase after green streak
    if recent_streak == "green" and recent_size_trend == "increasing":
        flags.append("SIZE_ESCALATION_AFTER_GREEN")
        reasons.append(
            "Position size increasing after winning streak. Classic overconfidence pattern."
        )
        risk_level = "HIGH"

    # 2. Averaging down
    if averaging_down:
        flags.append("AVERAGING_DOWN")
        reasons.append(
            "Adding to losing position. 'It will come back' thinking. Classic loss-amplification pattern."
        )
        if risk_level != "HIGH":
            risk_level = "HIGH"

    # 3. Revenge trading
    if revenge_pattern:
        flags.append("REVENGE_TRADING")
        reasons.append("Trading to recover from prior loss. Emotional, not analytical.")
        risk_level = "HIGH"

    # 4. Chasing analyst call
    if chasing_call:
        flags.append("CHASING_CALL")
        reasons.append("Entering because someone said so. No independent verification.")
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    # 5. Moving stop lower
    if stop_loss_moved_lower:
        flags.append("STOP_MOVED_LOWER")
        reasons.append(
            "Moving stop further from entry = increasing risk to avoid admitting loss."
        )
        risk_level = "HIGH"

    # 6. Too many open trades
    if position_count > max_recommended:
        flags.append("OVER_TRADED")
        reasons.append(
            f"{position_count} open positions vs {max_recommended} recommended max. "
            "Diluted attention, diluted capital, harder to manage."
        )
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    # 7. Green streak without flags = mild caution
    if recent_streak == "green" and not flags:
        reasons.append(
            "Recent green streak noted. Stay disciplined — skill vs luck not yet distinguishable."
        )
        risk_level = "MEDIUM"

    # ── Required actions ──
    actions: List[str] = []
    if "AVERAGING_DOWN" in flags:
        actions.append(
            "STOP averaging down. Cut the losing position or hold at original size only."
        )
    if "SIZE_ESCALATION_AFTER_GREEN" in flags:
        actions.append(
            "Return position size to baseline. Green streak is NOT a reason to increase size."
        )
    if "REVENGE_TRADING" in flags:
        actions.append(
            "Step away. No trades for 24 hours. Review the loss with cold eyes."
        )
    if "STOP_MOVED_LOWER" in flags:
        actions.append(
            "Restore original stop loss. If original stop would be hit, accept the loss."
        )
    if "OVER_TRADED" in flags:
        actions.append("Close weakest positions until count ≤ recommended max.")

    return {
        "status": "OK",
        "verdict": "888_HOLD"
        if risk_level == "HIGH"
        else ("NEEDS_DATA" if risk_level == "MEDIUM" else "SAFE_TO_STUDY"),
        "result": {
            "tamak_risk": risk_level,
            "flags": flags,
            "reasons": reasons,
            "required_actions": actions,
            "position_count": position_count,
            "max_recommended": max_recommended,
        },
        "warnings": reasons,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 8: pre_trade_gate ─────────────────────────────────────────────


def pre_trade_gate(
    ticker: str = "",
    has_stop_loss: bool = False,
    has_position_size: bool = False,
    position_size: int = 0,
    risk_per_trade_pct: float = 0.0,
    r_multiple: float = 0.0,
    liquidity_adequate: bool = False,
    sector_exposure_ok: bool = False,
    market_regime: str = "neutral",  # "supportive", "neutral", "hostile"
    fundamental_check_passed: bool = False,
    emotional_trigger: bool = False,
    reason_for_trade: str = "",
) -> dict:
    """Pre-trade safety gate. All checks must pass before any trade.

    Mandatory checks:
      1. Stop loss exists
      2. Position size calculated
      3. Risk ≤ 1%
      4. R ≥ 2.5
      5. Liquidity sufficient
      6. Sector exposure acceptable
      7. Market regime not hostile
      8. No emotional trigger
      9. Reason documented
    """
    checks: List[Dict[str, Any]] = []
    failed: List[str] = []

    # 1. Stop loss
    checks.append(
        {
            "check": "stop_loss_exists",
            "passed": has_stop_loss,
            "detail": "Stop loss is defined"
            if has_stop_loss
            else "NO STOP LOSS — cannot enter without invalidation",
        }
    )
    if not has_stop_loss:
        failed.append("NO_STOP_LOSS")

    # 2. Position size
    checks.append(
        {
            "check": "position_size_calculated",
            "passed": has_position_size and position_size > 0,
            "detail": f"Position size = {position_size} shares"
            if (has_position_size and position_size > 0)
            else "Position size not calculated",
        }
    )
    if not (has_position_size and position_size > 0):
        failed.append("NO_POSITION_SIZE")

    # 3. Risk ≤ 1%
    risk_ok = 0 < risk_per_trade_pct <= 1.0
    checks.append(
        {
            "check": "risk_under_1pct",
            "passed": risk_ok,
            "detail": f"Risk = {risk_per_trade_pct}%"
            if risk_per_trade_pct > 0
            else "Risk not calculated",
        }
    )
    if not risk_ok:
        failed.append(
            "RISK_EXCEEDS_1PCT" if risk_per_trade_pct > 1.0 else "RISK_NOT_CALCULATED"
        )

    # 4. R ≥ 2.5
    r_ok = r_multiple >= 2.5
    checks.append(
        {
            "check": "r_multiple_acceptable",
            "passed": r_ok,
            "detail": f"R = {r_multiple}" if r_multiple > 0 else "R not calculated",
        }
    )
    if not r_ok:
        failed.append("WEAK_ASYMMETRY" if r_multiple >= 2.0 else "R_TOO_LOW")

    # 5. Liquidity
    checks.append(
        {
            "check": "liquidity_adequate",
            "passed": liquidity_adequate,
            "detail": "Sufficient liquidity"
            if liquidity_adequate
            else "INSUFFICIENT LIQUIDITY — position too large for market",
        }
    )
    if not liquidity_adequate:
        failed.append("LIQUIDITY_TRAP")

    # 6. Sector exposure
    checks.append(
        {
            "check": "sector_exposure_ok",
            "passed": sector_exposure_ok,
            "detail": "Sector exposure within limits"
            if sector_exposure_ok
            else "SECTOR_OVERCONCENTRATED",
        }
    )
    if not sector_exposure_ok:
        failed.append("SECTOR_OVERCONCENTRATION")

    # 7. Market regime
    regime_ok = market_regime != "hostile"
    checks.append(
        {
            "check": "market_regime",
            "passed": regime_ok,
            "detail": f"Regime = {market_regime}"
            + (" — hostile, reduce exposure" if not regime_ok else ""),
        }
    )
    if not regime_ok:
        failed.append("HOSTILE_REGIME")

    # 8. Emotional trigger
    checks.append(
        {
            "check": "no_emotional_trigger",
            "passed": not emotional_trigger,
            "detail": "No emotional trigger detected"
            if not emotional_trigger
            else "EMOTIONAL TRIGGER — do not trade from emotion",
        }
    )
    if emotional_trigger:
        failed.append("EMOTIONAL_TRIGGER")

    # 9. Reason documented
    has_reason = bool(reason_for_trade.strip())
    checks.append(
        {
            "check": "reason_documented",
            "passed": has_reason,
            "detail": reason_for_trade
            if has_reason
            else "NO REASON DOCUMENTED — why are you entering?",
        }
    )
    if not has_reason:
        failed.append("NO_REASON_DOCUMENTED")

    # ── Final verdict ──
    if not failed:
        verdict = "PASS"
        message = "All checks passed. Proceed per plan."
    elif (
        "NO_STOP_LOSS" in failed
        or "EMOTIONAL_TRIGGER" in failed
        or "RISK_EXCEEDS_1PCT" in failed
    ):
        verdict = "UNSAFE"
        message = f"{len(failed)} gate(s) failed: {', '.join(failed)}"
    else:
        verdict = "NEEDS_DATA"
        message = f"{len(failed)} gate(s) failed: {', '.join(failed)}"

    return {
        "status": "OK",
        "verdict": verdict if verdict != "PASS" else "SAFE_TO_STUDY",
        "result": {
            "ticker": ticker.upper() if ticker else "?",
            "gate_verdict": verdict,
            "gates_passed": sum(1 for c in checks if c["passed"]),
            "gates_total": len(checks),
            "gates_failed": failed,
            "checks": checks,
            "message": message,
        },
        "warnings": [] if verdict == "PASS" else [message],
        "recommendation_only": True,
        "final_authority": "Arif",
    }
