"""
WEALTH Intelligence Gates — Constitutional Enforcement Layer
════════════════════════════════════════════════════════════

10 architectural gaps identified from PETRONAS-EnQuest + PCHEM AI contrasts.
Each gate enforces HARAM/WAJIB/SUNAT rules mapped to arifOS floors F1-F13.

DITEMPA BUKAN DIBERI — Intelligence gates are forged, not given.
Authority: F13 SOVEREIGN (Arif) — 16 June 2026

Gates:
  GAP1: Investment Advice Filter (H1, H2)
  GAP2: Real-Time Data Verification (H4, WJ1)
  GAP3: TTM-Completeness Gate (H5, H7, WJ2)
  GAP4: False Confluence Detector (H10, WJ4)
  GAP5: Single-Catalyst Detector (WJ3)
  GAP6: Regime Change Detector (H8)
  GAP7: Probability Validation Gate (H3)
  GAP8: Negative Beta/Correlation Check (WJ8)
  GAP9: Capital Materiality Check (WJ10)
  GAP10: Pre-Trade Gate Enforcement (H9, WJ7)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ─── Enums ────────────────────────────────────────────────────────────────────

class GateVerdict(Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    NEEDS_DATA = "NEEDS_DATA"


class EpistemicLevel(Enum):
    OBS = "OBSERVED"      # Direct observation
    DER = "DERIVED"       # Derived from computation
    INT = "INTERPRETED"   # Inferred from context
    SPEC = "SPECULATION"  # No evidence basis
    UNKNOWN = "UNKNOWN"   # Cannot determine


class FloorMapping(Enum):
    F1_AMANAH = "F1"
    F2_TRUTH = "F2"
    F4_CLARITY = "F4"
    F5_HUMILITY = "F5"
    F7_MARUAH = "F7"
    F8_LAW = "F8"
    F9_ANTI_HANTU = "F9"
    F11_AUDIT = "F11"
    F13_SOVEREIGN = "F13"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class GateResult:
    gate_id: str
    gate_name: str
    verdict: GateVerdict
    haram_rules_checked: list[str] = field(default_factory=list)
    wajib_rules_checked: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    floors_triggered: list[FloorMapping] = field(default_factory=list)
    epistemic_level: EpistemicLevel = EpistemicLevel.UNKNOWN
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPoint:
    """A financial data point with metadata for verification."""
    value: Any
    source: str = ""
    timestamp: str = ""
    freshness_hours: float = 0.0
    is_verified: bool = False
    epistemic_level: EpistemicLevel = EpistemicLevel.UNKNOWN


@dataclass
class Scenario:
    """A financial scenario with probability and evidence."""
    name: str
    probability: float = 0.0
    evidence_basis: str = ""
    is_currently_happening: bool = False
    triggers: list[str] = field(default_factory=list)


@dataclass
class Signal:
    """A confirming signal with underlying factor tracking."""
    name: str
    underlying_factor: str = ""
    evidence: str = ""
    independence_score: float = 1.0  # 1.0 = fully independent, 0.0 = same factor


# ─── GAP1: Investment Advice Filter ──────────────────────────────────────────

# Patterns that indicate actionable investment advice
ADVICE_PATTERNS = [
    # Specific price targets
    r"(?:target|tp|take.profit)[:\s]*(?:rm|myr|usd|\$)\s*[\d.]+",
    r"(?:entry|buy)[:\s]*(?:at|@|near)[:\s]*(?:rm|myr|usd|\$)\s*[\d.]+",
    r"(?:stop.loss|sl)[:\s]*(?:at|@|below|above)[:\s]*(?:rm|myr|usd|\$)\s*[\d.]+",
    # Buy/sell/hold ratings
    r"\b(?:buy|sell|hold|accumulate|reduce|overweight|underweight)\b.*(?:rating|recommendation)",
    r"(?:rating|recommendation)[:\s]*(?:buy|sell|hold|accumulate|reduce)",
    # Specific entry zones (including ranges like "RM 4.30-4.50")
    r"(?:entry\s+zone|buy\s+zone|accumulation\s+zone)[:\s]*(?:at|near|@)?[:\s]*(?:rm|myr|usd|\$)?\s*[\d.]+",
    r"(?:entry\s+zone|buy\s+zone|accumulation\s+zone)[:\s]*(?:at|near|@)?[:\s]*(?:rm|myr|usd|\$)?\s*[\d.]+\s*[-–]\s*[\d.]+",
    # Risk:reward with specific prices
    r"(?:risk[:\s]*reward|r[:\s]*r)\s*[~:]?\s*\d+[:\s]*\d+",
    # Parabolic SAR / technical signals suggesting entry
    r"(?:wait\s+for|look\s+for).*(?:sar|candlestick|engulfing|hammer).*flip",
]

# Patterns that are acceptable (mechanism explanation, not advice)
ACCEPTABLE_PATTERNS = [
    r"(?:how|mechanism|framework|structure|process|system)\s+(?:works?|operates?)",
    r"(?:this\s+is\s+(?:how|what|why))",
    r"(?:for\s+(?:educational|informational)\s+purposes\s+only)",
    r"(?:not\s+(?:financial|investment)\s+advice)",
    r"(?:general\s+(?:market|sector|industry)\s+(?:commentary|analysis|overview))",
]


def gap1_investment_advice_filter(text: str) -> GateResult:
    """
    GAP1: Block specific buy/sell/hold recommendations with price targets.
    HARAM: H1 (no buy/sell/hold), H2 (no entry/stop/target)
    Floor: F7 MARUAH (dignity violation — unlicensed advice)
    """
    result = GateResult(
        gate_id="GAP1",
        gate_name="Investment Advice Filter",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H1", "H2"],
        floors_triggered=[FloorMapping.F7_MARUAH],
    )

    text_lower = text.lower()
    violations = []

    for pattern in ADVICE_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            violations.append(f"Pattern matched: {pattern} → {matches[:3]}")

    # Check if acceptable patterns mitigate
    has_acceptable = any(
        re.search(p, text_lower) for p in ACCEPTABLE_PATTERNS
    )

    if violations:
        if has_acceptable and len(violations) <= 2:
            result.verdict = GateVerdict.WARN
            result.warnings = violations
        else:
            result.verdict = GateVerdict.BLOCK
            result.violations = violations

    return result


# ─── GAP2: Real-Time Data Verification ───────────────────────────────────────

STALE_THRESHOLD_HOURS = 24  # Data older than 24h is stale for equity analysis
CRITICAL_STALE_HOURS = 72   # Data older than 72h is critically stale


def gap2_realtime_data_verification(
    data_points: list[DataPoint],
) -> GateResult:
    """
    GAP2: Verify data freshness and timestamp.
    HARAM: H4 (stale data without timestamp)
    WAJIB: WJ1 (verify real-time data)
    Floor: F1 AMANAH (stale data = betrayal of trust)
    """
    result = GateResult(
        gate_id="GAP2",
        gate_name="Real-Time Data Verification",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H4"],
        wajib_rules_checked=["WJ1"],
        floors_triggered=[FloorMapping.F1_AMANAH],
    )

    if not data_points:
        result.verdict = GateVerdict.NEEDS_DATA
        result.warnings.append("No data points provided for verification")
        return result

    stale_points = []
    critically_stale = []
    untimestamped = []

    for dp in data_points:
        if not dp.timestamp:
            untimestamped.append(str(dp.value))
        elif dp.freshness_hours > CRITICAL_STALE_HOURS:
            critically_stale.append(f"{dp.value} (age: {dp.freshness_hours:.0f}h)")
        elif dp.freshness_hours > STALE_THRESHOLD_HOURS:
            stale_points.append(f"{dp.value} (age: {dp.freshness_hours:.0f}h)")

    if critically_stale:
        result.verdict = GateVerdict.BLOCK
        result.violations = [f"CRITICALLY STALE: {p}" for p in critically_stale]
    elif stale_points:
        result.verdict = GateVerdict.WARN
        result.warnings = [f"STALE: {p}" for p in stale_points]

    if untimestamped:
        if result.verdict == GateVerdict.PASS:
            result.verdict = GateVerdict.WARN
        result.warnings.append(f"UNTIMESTAMPED: {untimestamped}")

    result.details = {
        "total_points": len(data_points),
        "stale": len(stale_points),
        "critically_stale": len(critically_stale),
        "untimestamped": len(untimestamped),
    }

    return result


# ─── GAP3: TTM-Completeness Gate ─────────────────────────────────────────────

def gap3_ttm_completeness(
    quarterly_metrics: dict[str, Any],
    ttm_metrics: dict[str, Any],
) -> GateResult:
    """
    GAP3: Require TTM alongside quarterly data.
    HARAM: H5 (single-quarter without TTM), H7 (hiding negative metrics)
    WAJIB: WJ2 (show TTM alongside quarterly)
    Floor: F2 TRUTH (hidden data = falsehood)
    """
    result = GateResult(
        gate_id="GAP3",
        gate_name="TTM-Completeness Gate",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H5", "H7"],
        wajib_rules_checked=["WJ2"],
        floors_triggered=[FloorMapping.F2_TRUTH],
    )

    if not quarterly_metrics:
        result.verdict = GateVerdict.NEEDS_DATA
        return result

    missing_ttm = []
    hidden_negatives = []

    for key, q_value in quarterly_metrics.items():
        # Check if TTM equivalent exists
        ttm_key = f"{key}_ttm"
        if ttm_key not in ttm_metrics and f"ttm_{key}" not in ttm_metrics:
            missing_ttm.append(key)

        # Check if quarterly is positive but TTM is negative (cherry-picking)
        ttm_value = ttm_metrics.get(ttm_key) or ttm_metrics.get(f"ttm_{key}")
        if ttm_value is not None:
            try:
                q_num = float(q_value)
                ttm_num = float(ttm_value)
                if q_num > 0 and ttm_num < 0:
                    hidden_negatives.append(
                        f"{key}: Q={q_num:+.2f} but TTM={ttm_num:+.2f} (negative hidden)"
                    )
            except (ValueError, TypeError):
                pass

    if hidden_negatives:
        result.verdict = GateVerdict.BLOCK
        result.violations = hidden_negatives

    if missing_ttm:
        if result.verdict == GateVerdict.PASS:
            result.verdict = GateVerdict.WARN
        result.warnings = [f"MISSING TTM: {k}" for k in missing_ttm]

    result.details = {
        "quarterly_metrics": list(quarterly_metrics.keys()),
        "missing_ttm": missing_ttm,
        "hidden_negatives": hidden_negatives,
    }

    return result


# ─── GAP4: False Confluence Detector ─────────────────────────────────────────

def gap4_false_confluence(signals: list[Signal]) -> GateResult:
    """
    GAP4: Check if "confirming" signals measure the same underlying factor.
    HARAM: H10 (false confluence)
    WAJIB: WJ4 (confluence independence check)
    Floor: F4 CLARITY (false confluence = confusion)
    """
    result = GateResult(
        gate_id="GAP4",
        gate_name="False Confluence Detector",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H10"],
        wajib_rules_checked=["WJ4"],
        floors_triggered=[FloorMapping.F4_CLARITY],
    )

    if len(signals) < 2:
        result.verdict = GateVerdict.NEEDS_DATA
        return result

    # Group signals by underlying factor
    factor_groups: dict[str, list[str]] = {}
    for sig in signals:
        factor = sig.underlying_factor.lower().strip()
        factor_groups.setdefault(factor, []).append(sig.name)

    # Check for concentration
    total_signals = len(signals)
    unique_factors = len(factor_groups)

    if unique_factors == 1:
        result.verdict = GateVerdict.BLOCK
        result.violations = [
            f"FALSE CONFLUENCE: All {total_signals} signals measure the same factor: "
            f"'{list(factor_groups.keys())[0]}'",
            f"Signals: {list(factor_groups.values())[0]}",
        ]
    elif unique_factors < total_signals * 0.5:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            f"CONCENTRATION WARNING: {total_signals} signals map to only {unique_factors} "
            f"independent factors (ratio: {unique_factors/total_signals:.1%})",
        ]
        for factor, sigs in factor_groups.items():
            if len(sigs) > 2:
                result.warnings.append(
                    f"  Factor '{factor}' has {len(sigs)} signals: {sigs}"
                )

    result.details = {
        "total_signals": total_signals,
        "unique_factors": unique_factors,
        "independence_ratio": unique_factors / total_signals if total_signals > 0 else 0,
        "factor_groups": factor_groups,
    }

    return result


# ─── GAP5: Single-Catalyst Detector ──────────────────────────────────────────

def gap5_single_catalyst_detector(
    thesis: str,
    catalysts: list[str],
    contrarian_scenarios: list[str],
) -> GateResult:
    """
    GAP5: Flag thesis dependency on a single catalyst.
    WAJIB: WJ3 (flag single-catalyst dependency)
    Floor: F9 ANTI-HANTU (ghost chasing)
    """
    result = GateResult(
        gate_id="GAP5",
        gate_name="Single-Catalyst Detector",
        verdict=GateVerdict.PASS,
        wajib_rules_checked=["WJ3"],
        floors_triggered=[FloorMapping.F9_ANTI_HANTU],
    )

    if not catalysts:
        result.verdict = GateVerdict.NEEDS_DATA
        return result

    if len(catalysts) == 1:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            f"SINGLE CATALYST DEPENDENCY: Thesis depends entirely on '{catalysts[0]}'",
            "If this catalyst reverses, the entire thesis collapses.",
        ]
        if not contrarian_scenarios:
            result.verdict = GateVerdict.BLOCK
            result.violations = [
                "No contrarian scenario provided for single-catalyst thesis",
                "HARAM: Must model what happens if the catalyst reverses",
            ]

    # Check if contrarian scenarios actually address catalyst reversal
    if catalysts and contrarian_scenarios:
        catalyst_lower = catalysts[0].lower()
        reversal_addressed = any(
            catalyst_lower in scenario.lower() or "reverse" in scenario.lower()
            for scenario in contrarian_scenarios
        )
        if not reversal_addressed:
            result.warnings.append(
                "Contrarian scenarios do not address catalyst reversal"
            )

    return result


# ─── GAP6: Regime Change Detector ────────────────────────────────────────────

REGIME_CHANGE_SIGNALS = [
    "ceasefire",
    "peace deal",
    "armistice",
    "truce",
    "de-escalation",
    "resolution",
    "reopening",
    "normalization",
    "easing",
    "tumbling",
    "collapse of",
    "end of",
    "after the",
    "post-conflict",
]


def gap6_regime_change_detector(
    thesis: str,
    current_headlines: list[str],
) -> GateResult:
    """
    GAP6: Detect when geopolitical/economic regime is shifting.
    HARAM: H8 (assigning probability to events currently happening)
    Floor: F5 HUMILITY (overconfident in shifting regime)
    """
    result = GateResult(
        gate_id="GAP6",
        gate_name="Regime Change Detector",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H8"],
        floors_triggered=[FloorMapping.F5_HUMILITY],
    )

    thesis_lower = thesis.lower()
    headlines_lower = [h.lower() for h in current_headlines]

    # Check if thesis is built on conflict/crisis
    crisis_terms = ["conflict", "war", "closure", "disruption", "supply shock", "hormuz"]
    thesis_on_crisis = any(term in thesis_lower for term in crisis_terms)

    # Check if headlines indicate resolution
    resolution_signals = []
    for headline in headlines_lower:
        for signal in REGIME_CHANGE_SIGNALS:
            if signal in headline:
                resolution_signals.append(f"Headline contains '{signal}': {headline[:100]}")
                break

    if thesis_on_crisis and resolution_signals:
        result.verdict = GateVerdict.BLOCK
        result.violations = [
            "REGIME CHANGE DETECTED: Thesis is built on crisis, but headlines show resolution",
            f"Thesis crisis terms found: {[t for t in crisis_terms if t in thesis_lower]}",
            f"Resolution signals: {len(resolution_signals)} headlines",
        ]
    elif thesis_on_crisis:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            "Thesis depends on crisis/conflict — monitor for regime change",
        ]

    return result


# ─── GAP7: Probability Validation Gate ───────────────────────────────────────

def gap7_probability_validation(scenarios: list[Scenario]) -> GateResult:
    """
    GAP7: Reject probability assignments without evidence basis.
    HARAM: H3 (probability without evidence), H8 (probability for current events)
    Floor: F5 HUMILITY, F2 TRUTH
    """
    result = GateResult(
        gate_id="GAP7",
        gate_name="Probability Validation Gate",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H3", "H8"],
        floors_triggered=[FloorMapping.F5_HUMILITY, FloorMapping.F2_TRUTH],
    )

    if not scenarios:
        result.verdict = GateVerdict.NEEDS_DATA
        return result

    violations = []
    warnings = []

    # Check probability sum
    total_prob = sum(s.probability for s in scenarios)
    if abs(total_prob - 1.0) > 0.05:
        warnings.append(f"Probabilities sum to {total_prob:.2f}, not 1.00")

    for scenario in scenarios:
        # H3: Check evidence basis
        if scenario.probability > 0 and not scenario.evidence_basis:
            violations.append(
                f"Scenario '{scenario.name}' has {scenario.probability:.0%} probability "
                f"but NO evidence basis"
            )

        # H8: Check if event is currently happening
        if scenario.is_currently_happening and scenario.probability < 0.30:
            violations.append(
                f"Scenario '{scenario.name}' is CURRENTLY HAPPENING but assigned only "
                f"{scenario.probability:.0%} probability — inverted reality"
            )

        # Check for false precision
        if scenario.probability > 0:
            # Probabilities like 30%, 50%, 20% suggest false precision
            prob_pct = scenario.probability * 100
            if prob_pct == int(prob_pct) and prob_pct % 10 == 0:
                warnings.append(
                    f"Scenario '{scenario.name}': {prob_pct:.0f}% is suspiciously round — "
                    f"consider if this precision is justified"
                )

    if violations:
        result.verdict = GateVerdict.BLOCK
        result.violations = violations

    if warnings:
        if result.verdict == GateVerdict.PASS:
            result.verdict = GateVerdict.WARN
        result.warnings.extend(warnings)

    return result


# ─── GAP8: Negative Beta Check ───────────────────────────────────────────────

def gap8_negative_beta_check(
    ticker: str,
    beta: float,
    recommended_strategy: str,
) -> GateResult:
    """
    GAP8: Flag negative beta instruments for momentum/swing strategies.
    WAJIB: WJ8 (flag negative beta)
    Floor: F4 CLARITY (wrong instrument for strategy)
    """
    result = GateResult(
        gate_id="GAP8",
        gate_name="Negative Beta Check",
        verdict=GateVerdict.PASS,
        wajib_rules_checked=["WJ8"],
        floors_triggered=[FloorMapping.F4_CLARITY],
    )

    momentum_strategies = ["swing", "momentum", "breakout", "trend", "follow"]
    is_momentum = any(s in recommended_strategy.lower() for s in momentum_strategies)

    if beta < 0 and is_momentum:
        result.verdict = GateVerdict.BLOCK
        result.violations = [
            f"STRATEGY MISMATCH: {ticker} has beta {beta:+.2f} (moves INVERSELY to market)",
            f"Recommended strategy '{recommended_strategy}' requires positive momentum correlation",
            "A negative-beta instrument is a DEFENSIVE/HEDGE play, not a momentum vehicle",
        ]
    elif beta < 0:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            f"NOTE: {ticker} has beta {beta:+.2f} — moves inversely to market",
        ]
    elif abs(beta) < 0.3:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            f"NOTE: {ticker} has very low beta ({beta:+.2f}) — limited market correlation",
        ]

    return result


# ─── GAP9: Capital Materiality Check ─────────────────────────────────────────

def gap9_capital_materiality(
    theoretical_correctness: bool,
    economic_magnitude: Optional[float],
    economic_threshold: float = 1_000_000,  # RM 1M default
) -> GateResult:
    """
    GAP9: Distinguish "correct theory" from "material economics."
    WAJIB: WJ10 (capital materiality check)
    Floor: F2 TRUTH, F13 SOVEREIGN
    """
    result = GateResult(
        gate_id="GAP9",
        gate_name="Capital Materiality Check",
        verdict=GateVerdict.PASS,
        wajib_rules_checked=["WJ10"],
        floors_triggered=[FloorMapping.F2_TRUTH, FloorMapping.F13_SOVEREIGN],
    )

    if theoretical_correctness and economic_magnitude is not None:
        if abs(economic_magnitude) < economic_threshold:
            result.verdict = GateVerdict.WARN
            result.warnings = [
                f"Theory is correct but economic magnitude ({economic_magnitude:,.0f}) "
                f"is below materiality threshold ({economic_threshold:,.0f})",
                "The correct answer may not be the IMPORTANT answer",
            ]
        else:
            result.details = {
                "material": True,
                "magnitude": economic_magnitude,
                "threshold": economic_threshold,
            }
    elif theoretical_correctness and economic_magnitude is None:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            "Theory is correct but economic magnitude is UNKNOWN — cannot assess materiality",
            "WAJIB: Quantify the economic impact before drawing conclusions",
        ]

    return result


# ─── GAP10: Pre-Trade Gate Enforcement ────────────────────────────────────────

@dataclass
class PreTradeCheck:
    name: str
    passed: bool
    detail: str = ""


def gap10_pre_trade_enforcement(
    checks: list[PreTradeCheck],
) -> GateResult:
    """
    GAP10: Block recommendations that fail safety gates.
    HARAM: H9 (ignore safety gates)
    WAJIB: WJ7 (run pre-trade gates)
    Floor: F8 LAW (ignoring gates = lawlessness)
    """
    result = GateResult(
        gate_id="GAP10",
        gate_name="Pre-Trade Gate Enforcement",
        verdict=GateVerdict.PASS,
        haram_rules_checked=["H9"],
        wajib_rules_checked=["WJ7"],
        floors_triggered=[FloorMapping.F8_LAW],
    )

    if not checks:
        result.verdict = GateVerdict.NEEDS_DATA
        return result

    failed = [c for c in checks if not c.passed]
    passed = [c for c in checks if c.passed]

    if len(failed) > len(checks) * 0.5:
        result.verdict = GateVerdict.BLOCK
        result.violations = [
            f"PRE-TRADE GATE FAILURE: {len(failed)}/{len(checks)} gates failed",
            *[f"  ❌ {c.name}: {c.detail}" for c in failed],
        ]
    elif failed:
        result.verdict = GateVerdict.WARN
        result.warnings = [
            f"PRE-TRADE WARNING: {len(failed)}/{len(checks)} gates failed",
            *[f"  ⚠️ {c.name}: {c.detail}" for c in failed],
        ]

    result.details = {
        "total_checks": len(checks),
        "passed": len(passed),
        "failed": len(failed),
        "pass_rate": len(passed) / len(checks) if checks else 0,
        "failed_gates": [c.name for c in failed],
    }

    return result


# ─── UNIFIED GATE RUNNER ─────────────────────────────────────────────────────

@dataclass
class FullGateReport:
    """Complete gate analysis report for an AI-generated financial output."""
    results: list[GateResult] = field(default_factory=list)
    overall_verdict: GateVerdict = GateVerdict.PASS
    haram_violations: int = 0
    wajib_violations: int = 0
    warnings: int = 0
    floors_triggered: list[FloorMapping] = field(default_factory=list)

    def compute_overall(self):
        """Compute overall verdict from individual gate results."""
        if any(r.verdict == GateVerdict.BLOCK for r in self.results):
            self.overall_verdict = GateVerdict.BLOCK
        elif any(r.verdict == GateVerdict.WARN for r in self.results):
            self.overall_verdict = GateVerdict.WARN
        elif any(r.verdict == GateVerdict.NEEDS_DATA for r in self.results):
            self.overall_verdict = GateVerdict.NEEDS_DATA
        else:
            self.overall_verdict = GateVerdict.PASS

        self.haram_violations = sum(len(r.violations) for r in self.results)
        self.wajib_violations = sum(len(r.warnings) for r in self.results)
        self.warnings = self.wajib_violations

        all_floors = set()
        for r in self.results:
            all_floors.update(r.floors_triggered)
        self.floors_triggered = list(all_floors)


def run_all_gates(
    text: str = "",
    data_points: Optional[list[DataPoint]] = None,
    quarterly_metrics: Optional[dict[str, Any]] = None,
    ttm_metrics: Optional[dict[str, Any]] = None,
    signals: Optional[list[Signal]] = None,
    catalysts: Optional[list[str]] = None,
    contrarian_scenarios: Optional[list[str]] = None,
    thesis: str = "",
    current_headlines: Optional[list[str]] = None,
    scenarios: Optional[list[Scenario]] = None,
    ticker: str = "",
    beta: Optional[float] = None,
    recommended_strategy: str = "",
    theoretical_correctness: bool = True,
    economic_magnitude: Optional[float] = None,
    pre_trade_checks: Optional[list[PreTradeCheck]] = None,
) -> FullGateReport:
    """Run all 10 gates and produce a unified report."""
    report = FullGateReport()

    # GAP1: Investment Advice Filter
    if text:
        report.results.append(gap1_investment_advice_filter(text))

    # GAP2: Real-Time Data Verification
    if data_points:
        report.results.append(gap2_realtime_data_verification(data_points))

    # GAP3: TTM-Completeness Gate
    if quarterly_metrics is not None:
        report.results.append(
            gap3_ttm_completeness(quarterly_metrics, ttm_metrics or {})
        )

    # GAP4: False Confluence Detector
    if signals and len(signals) >= 2:
        report.results.append(gap4_false_confluence(signals))

    # GAP5: Single-Catalyst Detector
    if catalysts is not None:
        report.results.append(
            gap5_single_catalyst_detector(thesis, catalysts, contrarian_scenarios or [])
        )

    # GAP6: Regime Change Detector
    if thesis and current_headlines:
        report.results.append(
            gap6_regime_change_detector(thesis, current_headlines)
        )

    # GAP7: Probability Validation Gate
    if scenarios:
        report.results.append(gap7_probability_validation(scenarios))

    # GAP8: Negative Beta Check
    if beta is not None and recommended_strategy:
        report.results.append(
            gap8_negative_beta_check(ticker, beta, recommended_strategy)
        )

    # GAP9: Capital Materiality Check
    if theoretical_correctness:
        report.results.append(
            gap9_capital_materiality(theoretical_correctness, economic_magnitude)
        )

    # GAP10: Pre-Trade Gate Enforcement
    if pre_trade_checks:
        report.results.append(gap10_pre_trade_enforcement(pre_trade_checks))

    report.compute_overall()
    return report


# ─── Summary ─────────────────────────────────────────────────────────────────

def summarize_report(report: FullGateReport) -> str:
    """Produce human-readable summary of gate report."""
    lines = [
        "═══ WEALTH INTELLIGENCE GATE REPORT ═══",
        f"Overall Verdict: {report.overall_verdict.value}",
        f"HARAM Violations: {report.haram_violations}",
        f"Warnings: {report.warnings}",
        f"Floors Triggered: {[f.value for f in report.floors_triggered]}",
        "",
    ]

    for result in report.results:
        emoji = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "🔴", "NEEDS_DATA": "❓"}
        lines.append(
            f"{emoji.get(result.verdict.value, '?')} {result.gate_id} ({result.gate_name}): "
            f"{result.verdict.value}"
        )
        for v in result.violations:
            lines.append(f"   ❌ {v}")
        for w in result.warnings:
            lines.append(f"   ⚠️ {w}")

    return "\n".join(lines)
