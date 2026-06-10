"""
WEALTH Stock Analysis — Anomalous Contrast Engine
══════════════════════════════════════════════════

Detect when market layers disagree. Opportunity or danger appears
when fundamentals, price, volume, volatility, sector, liquidity,
valuation, and sentiment send conflicting signals.

Also: false confluence detector — prevents treating multiple
same-class indicators as independent confirmation.

DITEMPA BUKAN DIBERI — Contrast is forged, not assumed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ─── Tool 11: detect_anomalous_contrast ─────────────────────────────────


def detect_anomalous_contrast(
    ticker: str = "",
    # Layer 1: Fundamentals
    fundamental_score: Optional[float] = None,  # 0.0-1.0, higher = stronger
    revenue_growth: Optional[float] = None,
    earnings_growth: Optional[float] = None,
    # Layer 2: Price
    price_trend_3m: Optional[float] = None,  # percent return
    price_trend_6m: Optional[float] = None,
    # Layer 3: Volume
    volume_trend: str = "normal",  # "increasing", "normal", "declining"
    accumulation: str = "neutral",  # "accumulating", "distributing", "neutral"
    # Layer 4: Volatility
    volatility_trend: str = "normal",  # "declining", "normal", "increasing"
    atr_pct: Optional[float] = None,
    # Layer 5: Sector
    sector_trend: str = "neutral",  # "bullish", "neutral", "bearish"
    sector_rotation: str = "neutral",  # "into", "neutral", "out_of"
    # Layer 6: Liquidity
    liquidity_quality: str = "normal",  # "good", "normal", "thin"
    spread: Optional[float] = None,
    # Layer 7: Valuation
    valuation_zone: str = "fair",  # "cheap", "fair", "expensive"
    # Layer 8: Sentiment
    sentiment: str = "neutral",  # "bullish", "neutral", "bearish", "extreme_bullish", "extreme_bearish"
) -> dict:
    """Detect disagreement between market layers.

    Contrast signals:
      +2 = strong positive divergence → possible neglected opportunity
      +1 = mild positive divergence
       0 = layers aligned
      -1 = mild negative divergence
      -2 = strong negative divergence → possible hype/danger
    """
    contrasts: List[Dict[str, Any]] = []
    flags: List[str] = []
    total_contrast = 0.0
    contrast_count = 0

    # ── Contrast 1: Fundamentals vs Price ──
    c1_score = 0
    c1_note = ""
    if fundamental_score is not None and price_trend_3m is not None:
        contrast_count += 1
        if fundamental_score > 0.7 and price_trend_3m < -10:
            c1_score = 2
            c1_note = "Fundamentals strong but price declining — possible accumulation opportunity (or hidden risk)"
        elif fundamental_score > 0.7 and price_trend_3m < 0:
            c1_score = 1
            c1_note = "Fundamentals strong, price flat/declining — mild divergence"
        elif (
            fundamental_score is not None and fundamental_score < 0.3
        ) and price_trend_3m > 20:
            c1_score = -2
            c1_note = "Weak fundamentals with strong price rally — possible hype/pump"
        elif (
            fundamental_score is not None and fundamental_score < 0.3
        ) and price_trend_3m > 10:
            c1_score = -1
            c1_note = "Weak fundamentals, price rising — mild warning"
        total_contrast += c1_score
    contrasts.append(
        {
            "name": "FUNDAMENTALS_VS_PRICE",
            "score": c1_score,
            "note": c1_note or "Insufficient data",
            "interpretation": "FUNDAMENTALS_STRONG_PRICE_WEAK"
            if c1_score > 0
            else "FUNDAMENTALS_WEAK_PRICE_STRONG"
            if c1_score < 0
            else "ALIGNED",
        }
    )

    # ── Contrast 2: Volume vs Price ──
    c2_score = 0
    c2_note = ""
    if price_trend_3m is not None:
        contrast_count += 1
        if price_trend_3m > 10 and volume_trend == "declining":
            c2_score = -1
            c2_note = "Price rising on declining volume — rally losing fuel"
        elif price_trend_3m > 10 and accumulation == "distributing":
            c2_score = -2
            c2_note = "Price rising but smart money distributing — danger signal"
        elif price_trend_3m < -10 and volume_trend == "declining":
            c2_score = 1
            c2_note = "Price falling on declining volume — selling pressure fading"
        elif price_trend_3m < -10 and accumulation == "accumulating":
            c2_score = 2
            c2_note = (
                "Price falling but smart money accumulating — possible base forming"
            )
        total_contrast += c2_score
    contrasts.append(
        {
            "name": "VOLUME_VS_PRICE",
            "score": c2_score,
            "note": c2_note or "Insufficient data",
            "interpretation": "VOLUME_CONFIRMS_PRICE"
            if c2_score == 0
            else "VOLUME_DIVERGES_PRICE",
        }
    )

    # ── Contrast 3: Sentiment vs Fundamentals ──
    c3_score = 0
    c3_note = ""
    if fundamental_score is not None:
        contrast_count += 1
        if fundamental_score > 0.7 and sentiment == "extreme_bearish":
            c3_score = 2
            c3_note = "Strong fundamentals, extreme bearish sentiment — contrarian opportunity (but check for hidden risk)"
        elif fundamental_score > 0.7 and sentiment == "bearish":
            c3_score = 1
            c3_note = "Strong fundamentals, bearish sentiment — mild contrarian signal"
        elif (
            fundamental_score is not None and fundamental_score < 0.3
        ) and sentiment == "extreme_bullish":
            c3_score = -2
            c3_note = "Weak fundamentals, extreme bullish sentiment — euphoria danger"
        elif (
            fundamental_score is not None and fundamental_score < 0.3
        ) and sentiment == "bullish":
            c3_score = -1
            c3_note = "Weak fundamentals, bullish sentiment — mild caution"
        total_contrast += c3_score
    contrasts.append(
        {
            "name": "SENTIMENT_VS_FUNDAMENTALS",
            "score": c3_score,
            "note": c3_note or "Insufficient data",
            "interpretation": "SENTIMENT_LAGS_FUNDAMENTALS"
            if c3_score > 0
            else "SENTIMENT_AHEAD_OF_FUNDAMENTALS"
            if c3_score < 0
            else "ALIGNED",
        }
    )

    # ── Contrast 4: Sector vs Stock ──
    c4_score = 0
    c4_note = ""
    if price_trend_3m is not None and sector_trend != "neutral":
        contrast_count += 1
        if price_trend_3m > 10 and sector_trend == "bearish":
            c4_score = 1
            c4_note = "Stock strong despite weak sector — genuine relative strength"
        elif price_trend_3m > 10 and sector_rotation == "out_of":
            c4_score = -1
            c4_note = (
                "Stock strong but money rotating out of sector — headwind building"
            )
        elif price_trend_3m < -10 and sector_trend == "bullish":
            c4_score = -1
            c4_note = "Stock weak despite strong sector — genuine underperformance"
        total_contrast += c4_score
    contrasts.append(
        {
            "name": "SECTOR_VS_STOCK",
            "score": c4_score,
            "note": c4_note or "Insufficient data",
            "interpretation": "STOCK_STRONGER_THAN_SECTOR"
            if c4_score > 0
            else "STOCK_WEAKER_THAN_SECTOR"
            if c4_score < 0
            else "ALIGNED",
        }
    )

    # ── Contrast 5: Liquidity vs Valuation ──
    c5_score = 0
    c5_note = ""
    if valuation_zone != "fair" and liquidity_quality != "normal":
        contrast_count += 1
        if valuation_zone == "cheap" and liquidity_quality == "thin":
            c5_score = -1
            c5_note = (
                "Cheap valuation but thin liquidity — may not be able to build position"
            )
        elif valuation_zone == "expensive" and liquidity_quality == "good":
            c5_score = -1
            c5_note = "Expensive with good liquidity — easy to buy, hard to justify"
        total_contrast += c5_score
    contrasts.append(
        {
            "name": "LIQUIDITY_VS_VALUATION",
            "score": c5_score,
            "note": c5_note or "Insufficient data",
            "interpretation": "LIQUIDITY_CONSTRAINS_VALUATION"
            if c5_score < 0
            else "ALIGNED",
        }
    )

    # ── Contrast 6: Volatility decompression ──
    c6_score = 0
    c6_note = ""
    if volatility_trend == "increasing" and atr_pct is not None and atr_pct > 8:
        c6_score = -2
        c6_note = "Volatility expanding + high ATR = position sizing must be reduced"
        contrast_count += 1
        total_contrast += c6_score
    elif volatility_trend == "declining" and atr_pct is not None and atr_pct < 3:
        c6_score = 0
        c6_note = "Low, declining volatility — quiet market, limited opportunity"
    contrasts.append(
        {
            "name": "VOLATILITY_DECOMPRESSION",
            "score": c6_score,
            "note": c6_note or "Normal volatility regime",
            "interpretation": "HIGH_RISK_ENVIRONMENT" if c6_score < 0 else "MANAGEABLE",
        }
    )

    # ── Overall contrast verdict ──
    avg_contrast = (
        round(total_contrast / contrast_count, 1) if contrast_count > 0 else 0.0
    )

    if avg_contrast >= 1.5:
        overall_note = "Multiple positive divergences — possible neglected opportunity. Verify with fundamental data."
        overall_verdict = "SAFE_TO_STUDY"
    elif avg_contrast >= 0.5:
        overall_note = "Mild positive divergences — worth deeper study."
        overall_verdict = "SAFE_TO_STUDY"
    elif avg_contrast <= -1.5:
        overall_note = "Multiple negative divergences — high risk of hype, pump, or hidden deterioration."
        overall_verdict = "UNSAFE"
        flags.append("MULTIPLE_NEGATIVE_DIVERGENCES")
    elif avg_contrast <= -0.5:
        overall_note = "Mild negative divergences — proceed with extra caution."
        overall_verdict = "NEEDS_DATA"
    else:
        overall_note = "Market layers broadly aligned — no anomalous contrast detected."
        overall_verdict = "SAFE_TO_STUDY"

    return {
        "status": "OK",
        "verdict": overall_verdict,
        "result": {
            "ticker": ticker.upper() if ticker else "?",
            "anomalous_contrast_score": avg_contrast,
            "contrast_layers_analyzed": len(contrasts),
            "overall_note": overall_note,
            "contrasts": contrasts,
            "interpretation_guide": {
                "+2": "Strong positive divergence — possible neglected opportunity",
                "+1": "Mild positive divergence",
                "0": "Layers aligned",
                "-1": "Mild negative divergence",
                "-2": "Strong negative divergence — possible hype/danger",
            },
        },
        "warnings": flags,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 12: detect_false_confluence ───────────────────────────────────


def detect_false_confluence(
    ticker: str = "",
    indicators: Optional[Dict[str, str]] = None,
) -> dict:
    """Detect when multiple indicators are secretly one signal class.

    Example: RSI bullish + MACD bullish + SAR bullish =
    3 indicators, but only 1 independent signal class (price-momentum).
    """

    # Define signal classes
    SIGNAL_CLASSES = {
        "price_momentum": ["rsi", "macd", "stochastic", "williams_r", "cci"],
        "trend_following": ["ma_cross", "sar", "adx", "ichimoku", "supertrend"],
        "volume": ["obv", "mfi", "volume_ratio", "accum_dist", "chaikin"],
        "volatility": ["bollinger", "atr", "keltner", "donchian"],
        "sentiment": ["put_call", "fear_greed", "vix"],
    }

    if not indicators:
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "result": {
                "ticker": ticker.upper() if ticker else "?",
                "false_confluence_detected": False,
                "independent_classes": 0,
                "total_indicators": 0,
                "note": "No indicators provided for analysis.",
            },
            "warnings": [],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    # Classify each indicator
    class_counts: Dict[str, int] = {}
    class_signals: Dict[str, List[str]] = {}
    for ind_name, ind_signal in indicators.items():
        found_class = "unknown"
        for cls_name, members in SIGNAL_CLASSES.items():
            if ind_name.lower() in members:
                found_class = cls_name
                break
        class_counts[found_class] = class_counts.get(found_class, 0) + 1
        if found_class not in class_signals:
            class_signals[found_class] = []
        class_signals[found_class].append(f"{ind_name}={ind_signal}")

    independent_classes = len(class_counts)
    total_indicators = len(indicators)

    # Detect false confluence
    warnings: List[str] = []
    false_confluence = False

    for cls_name, count in class_counts.items():
        if count >= 3:
            false_confluence = True
            warnings.append(
                f"FALSE_CONFLUENCE: {count} indicators ({', '.join(class_signals[cls_name])}) "
                f"are all in the '{cls_name}' class. This is 1 independent signal, not {count}."
            )
        elif count >= 2:
            warnings.append(
                f"PARTIAL_OVERLAP: {count} indicators from '{cls_name}' class — "
                f"they share the same source signal, not fully independent."
            )

    if independent_classes == total_indicators and total_indicators >= 3:
        assessment = "GOOD_CONFLUENCE — indicators from multiple independent classes."
        verdict = "SAFE_TO_STUDY"
    elif not false_confluence and independent_classes >= 2:
        assessment = (
            "ADEQUATE — some class overlap but multiple independent perspectives."
        )
        verdict = "SAFE_TO_STUDY"
    elif false_confluence:
        assessment = (
            f"FALSE_CONFLUENCE: {total_indicators} indicators but only "
            f"{independent_classes} independent signal class(es). "
            f"Do not count same-class indicators as separate confirmation."
        )
        verdict = "NEEDS_DATA"
    else:
        assessment = "INSUFFICIENT — not enough independent signal classes."
        verdict = "NEEDS_DATA"

    return {
        "status": "OK",
        "verdict": verdict,
        "result": {
            "ticker": ticker.upper() if ticker else "?",
            "false_confluence_detected": false_confluence,
            "total_indicators": total_indicators,
            "independent_classes": independent_classes,
            "class_breakdown": {k: len(v) for k, v in class_signals.items()},
            "class_details": class_signals,
            "assessment": assessment,
            "signal_classes_reference": {
                "price_momentum": "RSI, MACD, Stochastic, Williams %R, CCI — all measure price velocity in different ways",
                "trend_following": "MA crosses, SAR, ADX, Ichimoku, Supertrend — all measure trend direction",
                "volume": "OBV, MFI, Volume Ratio, Accumulation/Distribution, Chaikin — all measure volume behavior",
                "volatility": "Bollinger Bands, ATR, Keltner Channels, Donchian — all measure price dispersion",
                "sentiment": "Put/Call, Fear & Greed, VIX — all measure market emotion",
            },
        },
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }
