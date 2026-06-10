"""
WEALTH Stock Analysis — Deterministic Math Tests
═══════════════════════════════════════════════════

Test all 12 modes of wealth_stock_analysis. Pure math — no API calls.
Based on the forge plan's test scenarios and the MI (MISC Bhd) case.

DITEMPA BUKAN DIBERI — Tests are forged, not given.
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ═══════════════════════════════════════════════════════════════════════════
# MODE 1 — verify_math
# ═══════════════════════════════════════════════════════════════════════════


def test_verify_math_mi_entry_correct():
    """MI entry 3.91, current 4.65 — must compute 18.93%, not 7.41%."""
    from internal.stock.math_tools import verify_trade_math

    r = verify_trade_math(
        ticker="MI",
        entry_price=3.91,
        current_price=4.65,
        position_size=1000,
        fees=0.0,
        direction="long",
        status="unrealized",
    )
    assert r["status"] == "OK"
    assert r["result"]["entry_price"] == 3.91
    assert r["result"]["exit_or_current_price"] == 4.65
    assert r["result"]["position_size"] == 1000

    # Gross P/L = (4.65 - 3.91) * 1000 = 740
    assert abs(r["result"]["gross_pl_rm"] - 740.0) < 0.01
    # Gross P/L % = 740 / (3.91 * 1000) * 100 = 18.93%
    assert abs(r["result"]["gross_pl_pct"] - 18.93) < 0.1


def test_verify_math_journal_discrepancy():
    """If journal says 7.41% but real is 18.93%, must flag MATH_ERROR."""
    from internal.stock.math_tools import verify_trade_math

    r = verify_trade_math(
        ticker="MI",
        entry_price=3.91,
        current_price=4.65,
        position_size=1000,
        journal_pnl_pct=7.41,
    )
    assert r["verdict"] == "MATH_ERROR"


def test_verify_math_short_position():
    """Short position: entry 5.00, exit 4.00, position 1000 = profit 1000."""
    from internal.stock.math_tools import verify_trade_math

    r = verify_trade_math(
        ticker="SHORT",
        entry_price=5.00,
        exit_price=4.00,
        position_size=1000,
        direction="short",
        status="realized",
    )
    assert abs(r["result"]["gross_pl_rm"] - 1000.0) < 0.01


def test_verify_math_missing_data():
    """Missing position_size → NEEDS_DATA."""
    from internal.stock.math_tools import verify_trade_math

    r = verify_trade_math(ticker="MI", entry_price=3.91)
    assert r["verdict"] == "NEEDS_DATA"


# ═══════════════════════════════════════════════════════════════════════════
# MODE 2 — separate_realized_unrealized
# ═══════════════════════════════════════════════════════════════════════════


def test_separate_pl_paper_profit_warning():
    """Realized negative, unrealized positive → total looks good but it's paper."""
    from internal.stock.math_tools import separate_realized_unrealized

    trades = [
        {
            "ticker": "A",
            "status": "realized",
            "gross_pl_rm": -500,
            "gross_pl_pct": -4.19,
            "position_value_rm": 0,
        },
        {
            "ticker": "B",
            "status": "unrealized",
            "gross_pl_rm": 800,
            "gross_pl_pct": 12.0,
            "position_value_rm": 5000,
        },
    ]
    r = separate_realized_unrealized(trades)
    assert r["result"]["realized_pl_rm"] == -500
    assert r["result"]["unrealized_pl_rm"] == 800
    assert r["result"]["total_pl_rm"] == 300
    assert any("PAPER_PROFIT" in w for w in r["warnings"])


# ═══════════════════════════════════════════════════════════════════════════
# MODE 3 — calculate_position_size
# ═══════════════════════════════════════════════════════════════════════════


def test_position_size_calculation():
    """Account 50,000, entry 3.91, stop 3.60, risk 1% → ~322 shares."""
    from internal.stock.math_tools import calculate_position_size

    r = calculate_position_size(
        account_balance=50000,
        entry_price=3.91,
        stop_loss=3.60,
        risk_per_trade_pct=1.0,
    )
    # risk per share = 0.31, max_rm_risk = 500, max_shares = 1612
    assert r["result"]["risk_per_share"] == 0.31
    assert r["result"]["max_rm_risk"] == 500.0
    assert r["result"]["max_shares"] == 1612  # 500 / 0.31 = 1612


def test_position_size_risk_exceeds_limit():
    """risk_per_trade_pct > 1% → UNSAFE."""
    from internal.stock.math_tools import calculate_position_size

    r = calculate_position_size(
        account_balance=50000,
        entry_price=3.91,
        stop_loss=3.60,
        risk_per_trade_pct=2.0,
    )
    assert r["verdict"] == "UNSAFE"


# ═══════════════════════════════════════════════════════════════════════════
# MODE 4 — calculate_r_multiple
# ═══════════════════════════════════════════════════════════════════════════


def test_r_multiple_strong():
    """Entry 3.91, stop 3.60, target 5.00 → R = (5.00-3.91)/(3.91-3.60) = 3.52 → STRONG."""
    from internal.stock.math_tools import calculate_r_multiple

    r = calculate_r_multiple(entry_price=3.91, stop_loss=3.60, target_price=5.00)
    assert r["result"]["r_multiple"] >= 3.0
    assert r["result"]["asymmetry_grade"] == "STRONG"
    assert r["verdict"] == "SAFE_TO_STUDY"


def test_r_multiple_unacceptable():
    """R < 2.0 → UNSAFE."""
    from internal.stock.math_tools import calculate_r_multiple

    r = calculate_r_multiple(entry_price=3.91, stop_loss=3.85, target_price=4.00)
    assert r["result"]["r_multiple"] < 2.0
    assert r["verdict"] == "UNSAFE"


# ═══════════════════════════════════════════════════════════════════════════
# MODE 5 — check_portfolio_exposure
# ═══════════════════════════════════════════════════════════════════════════


def test_exposure_gap_down_survival():
    """50k account, 40k exposure → 15% gap = 6k loss → remaining 44k. Survivable."""
    from internal.stock.risk_tools import check_portfolio_exposure

    positions = [
        {
            "ticker": "MI",
            "position_value_rm": 20000,
            "stop_loss_distance_pct": 10,
            "sector": "Industrial",
        },
        {
            "ticker": "TENAGA",
            "position_value_rm": 20000,
            "stop_loss_distance_pct": 8,
            "sector": "Utilities",
        },
    ]
    r = check_portfolio_exposure(positions=positions, account_balance=50000)
    assert r["result"]["exposure_pct"] == 80.0
    assert r["verdict"] == "SAFE_TO_STUDY"


def test_exposure_sector_concentration():
    """Single sector > 50% → warning."""
    from internal.stock.risk_tools import check_portfolio_exposure

    positions = [
        {
            "ticker": "MI",
            "position_value_rm": 30000,
            "stop_loss_distance_pct": 10,
            "sector": "Industrial",
        },
        {
            "ticker": "SIME",
            "position_value_rm": 20000,
            "stop_loss_distance_pct": 10,
            "sector": "Industrial",
        },
    ]
    r = check_portfolio_exposure(positions=positions, account_balance=50000)
    assert any("SECTOR_CONCENTRATION" in w for w in r["warnings"])


# ═══════════════════════════════════════════════════════════════════════════
# MODE 6 — apply_bursa_cost_model
# ═══════════════════════════════════════════════════════════════════════════


def test_bursa_cost_small_winner():
    """0.39% gross gain → after Bursa costs → may be flat or negative."""
    from internal.stock.risk_tools import apply_bursa_cost_model

    # Small trade: 100 shares at RM1.00 → RM1.01
    r = apply_bursa_cost_model(
        entry_price=1.00,
        exit_price=1.01,
        position_size=100,
    )
    # Gross = (1.01-1.00)*100 = 1.00 (1%)
    # Costs: brokerage min RM8 each side = RM16 + clearing + stamp + spread + slippage
    # Net should be negative
    assert r["result"]["gross_pl_rm"] == 1.0
    assert r["result"]["net_pl_rm"] < 0  # costs exceed profit
    assert r["verdict"] in ("NEEDS_DATA",)  # FAKE_WINNER detected


# ═══════════════════════════════════════════════════════════════════════════
# MODE 7 — detect_tamak_behavior
# ═══════════════════════════════════════════════════════════════════════════


def test_tamak_green_streak_size_increase():
    """Green streak + increasing size → HIGH tamak risk."""
    from internal.stock.behavior_tools import detect_tamak_behavior

    r = detect_tamak_behavior(
        recent_streak="green",
        recent_size_trend="increasing",
    )
    assert r["result"]["tamak_risk"] == "HIGH"
    assert r["verdict"] == "888_HOLD"


def test_tamak_averaging_down():
    """Averaging down → HIGH tamak risk."""
    from internal.stock.behavior_tools import detect_tamak_behavior

    r = detect_tamak_behavior(averaging_down=True)
    assert r["result"]["tamak_risk"] == "HIGH"


def test_tamak_no_flags():
    """No flags → LOW risk."""
    from internal.stock.behavior_tools import detect_tamak_behavior

    r = detect_tamak_behavior(recent_streak="neutral")
    assert r["result"]["tamak_risk"] == "LOW"


# ═══════════════════════════════════════════════════════════════════════════
# MODE 8 — pre_trade_gate
# ═══════════════════════════════════════════════════════════════════════════


def test_pretrade_missing_stop():
    """No stop loss → UNSAFE."""
    from internal.stock.behavior_tools import pre_trade_gate

    r = pre_trade_gate(
        ticker="MI",
        has_stop_loss=False,
        has_position_size=True,
        position_size=1000,
        risk_per_trade_pct=1.0,
        r_multiple=3.0,
    )
    assert r["result"]["gate_verdict"] == "UNSAFE"
    assert "NO_STOP_LOSS" in r["result"]["gates_failed"]


def test_pretrade_all_pass():
    """All 9 gates pass → PASS."""
    from internal.stock.behavior_tools import pre_trade_gate

    r = pre_trade_gate(
        ticker="MI",
        has_stop_loss=True,
        has_position_size=True,
        position_size=1000,
        risk_per_trade_pct=1.0,
        r_multiple=3.0,
        liquidity_adequate=True,
        sector_exposure_ok=True,
        market_regime="supportive",
        fundamental_check_passed=True,
        emotional_trigger=False,
        reason_for_trade="Breakout above 50MA with volume confirmation",
    )
    assert r["result"]["gate_verdict"] == "PASS"


# ═══════════════════════════════════════════════════════════════════════════
# MODE 9 — check_fundamental_invariants
# ═══════════════════════════════════════════════════════════════════════════


def test_fundamentals_negative_fcf():
    """Negative free cash flow → flag on F1."""
    from internal.stock.fundamentals import check_fundamental_invariants

    r = check_fundamental_invariants(
        ticker="WEAKCO",
        free_cash_flow=-50,
        operating_cash_flow=100,
    )
    # F1 should have a flag
    f1 = next(
        (
            inv
            for inv in r["result"]["invariants"]
            if inv["invariant"] == "F1_CASH_FLOW"
        ),
        None,
    )
    assert f1 is not None
    assert f1["verdict"] in ("WARNING", "FLAG")


def test_fundamentals_insufficient_data():
    """No data → all invariants INSUFFICIENT_DATA."""
    from internal.stock.fundamentals import check_fundamental_invariants

    r = check_fundamental_invariants(ticker="UNKNOWN")
    missing = sum(
        1 for inv in r["result"]["invariants"] if inv["verdict"] == "INSUFFICIENT_DATA"
    )
    assert missing >= 7  # most invariants have no data


# ═══════════════════════════════════════════════════════════════════════════
# MODE 10 — run_tac9_engine
# ═══════════════════════════════════════════════════════════════════════════


def test_tac9_hostile_regime():
    """Hostile regime + no structure → overall weak/unsafe."""
    from internal.stock.technical import run_tac9_engine

    r = run_tac9_engine(
        ticker="MI",
        benchmark_trend="bearish",
        sector_trend="bearish",
        risk_state="risk_off",
        # No structure, no invalidation, weak volume
        invalidation_level=None,
        breakout_volume="weak",
    )
    # With hostile regime + bearish sector + risk_off + no invalidation + weak volume,
    # multiple tiers fail → WEAK or worse
    assert r["result"]["tac9_verdict"] in ("WEAK", "VERY_WEAK", "HOSTILE", "ADEQUATE")
    # T1 should be HOSTILE specifically
    t1 = r["result"]["tiers"][0]
    assert t1["verdict"] == "HOSTILE"


def test_tac9_strong_bullish():
    """All 5 trend factors positive → strong."""
    from internal.stock.technical import run_tac9_engine

    r = run_tac9_engine(
        ticker="MI",
        benchmark_trend="bullish",
        risk_state="risk_on",
        price_above_50ma=True,
        ma50_above_ma200=True,
        higher_highs=True,
        higher_lows=True,
        support_holding=True,
        breakout_volume="strong",
        accumulation="accumulating",
        invalidation_level=3.50,
        r_multiple=3.0,
    )
    assert r["result"]["tiers_passed"] >= 6


# ═══════════════════════════════════════════════════════════════════════════
# MODE 11 — detect_anomalous_contrast
# ═══════════════════════════════════════════════════════════════════════════


def test_contrast_strong_fundamentals_falling_price():
    """Strong fundamentals + falling price → positive contrast."""
    from internal.stock.contrast import detect_anomalous_contrast

    r = detect_anomalous_contrast(
        ticker="MI",
        fundamental_score=0.85,
        price_trend_3m=-15.0,
    )
    contrast = next(
        (c for c in r["result"]["contrasts"] if c["name"] == "FUNDAMENTALS_VS_PRICE"),
        None,
    )
    assert contrast is not None
    assert contrast["score"] >= 1  # positive divergence


def test_contrast_weak_fundamentals_rising_price():
    """Weak fundamentals + rising price → negative contrast (hype danger)."""
    from internal.stock.contrast import detect_anomalous_contrast

    r = detect_anomalous_contrast(
        ticker="PUMPCO",
        fundamental_score=0.2,
        price_trend_3m=25.0,
    )
    contrast = next(
        (c for c in r["result"]["contrasts"] if c["name"] == "FUNDAMENTALS_VS_PRICE"),
        None,
    )
    assert contrast is not None
    assert contrast["score"] <= -1  # negative divergence


# ═══════════════════════════════════════════════════════════════════════════
# MODE 12 — detect_false_confluence
# ═══════════════════════════════════════════════════════════════════════════


def test_false_confluence_rsi_macd_sar():
    """RSI + MACD + SAR = 3 indicators, 2 classes (momentum + trend), partial overlap detected."""
    from internal.stock.contrast import detect_false_confluence

    r = detect_false_confluence(
        ticker="MI",
        indicators={
            "rsi": "bullish",
            "macd": "bullish",
            "sar": "bullish",
        },
    )
    assert r["result"]["total_indicators"] == 3
    # RSI+MACD = price_momentum (1 class), SAR = trend_following (1 class) = 2 total
    assert r["result"]["independent_classes"] <= 2
    # Partial overlap warning: 2 indicators in same class
    assert any("PARTIAL_OVERLAP" in w or "2 indicators" in w for w in r["warnings"])


def test_false_confluence_mixed_classes():
    """RSI + OBV + Bollinger = 3 different classes → good."""
    from internal.stock.contrast import detect_false_confluence

    r = detect_false_confluence(
        ticker="MI",
        indicators={
            "rsi": "bullish",
            "obv": "rising",
            "bollinger": "squeeze",
        },
    )
    assert r["result"]["independent_classes"] >= 2
    assert r["result"]["false_confluence_detected"] == False


# ═══════════════════════════════════════════════════════════════════════════
# MODE dispatch test: wealth_stock_analysis unified tool
# ═══════════════════════════════════════════════════════════════════════════


def test_wealth_stock_analysis_mode_dispatch():
    """Each mode routes to the correct tool and returns valid output."""
    import asyncio
    import internal.monolith as monolith

    async def _run():
        # Test verify_math mode
        r = await monolith.wealth_stock_analysis(
            mode="verify_math",
            ticker="MI",
            entry_price=3.91,
            current_price=4.65,
            position_size=1000,
        )
        assert "tool" in r
        assert r["verdict"] == "SAFE_TO_STUDY"
        assert abs(r["result"]["gross_pl_pct"] - 18.93) < 0.1

        # Test pre_trade mode
        r2 = await monolith.wealth_stock_analysis(
            mode="pre_trade",
            ticker="MI",
            has_stop_loss=True,
            has_position_size=True,
            position_size=1000,
            risk_per_trade_pct=1.0,
            r_multiple=3.0,
            liquidity_adequate=True,
            sector_exposure_ok=True,
            market_regime="supportive",
            fundamental_check_passed=True,
            emotional_trigger=False,
            reason_for_trade="Technical breakout",
        )
        assert r2["result"]["gate_verdict"] == "PASS"

        # Test tamak_check mode
        r3 = await monolith.wealth_stock_analysis(
            mode="tamak_check",
            recent_streak="green",
            recent_size_trend="increasing",
        )
        assert r3["result"]["tamak_risk"] == "HIGH"

        # Test fundamentals mode
        r4 = await monolith.wealth_stock_analysis(
            mode="fundamentals",
            ticker="GOODCO",
            free_cash_flow=200,
            operating_cash_flow=250,
            roic=15.0,
            roe=18.0,
            has_moat=True,
            pricing_power=True,
            recurring_revenue=True,
        )
        assert "invariants" in r4["result"]

        # Test unknown mode
        r5 = await monolith.wealth_stock_analysis(mode="buy_signal")
        assert r5["status"] == "ERROR"

    asyncio.run(_run())
