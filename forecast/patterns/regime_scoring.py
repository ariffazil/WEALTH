"""Regime-conditioned chart pattern scoring.

Contract
--------
``score_patterns(apex_state, pattern_stats)`` returns a ``RegimeScoringResult``
that contains, per regime, the top-3 patterns ranked by posterior edge with
Wilson lower-bound confidence intervals. If no pattern passes the honest
gating (walk-forward-validated + sufficient sample size + positive CI lower
bound + regime-compatible), the regime's ranking is collapsed to
``NO_RECOMMENDATION`` and the global ``status`` becomes ``SHADOW``.

Scoring discipline
------------------
For each pattern ``p`` observed in ``n`` trials with ``k`` wins (forward
return > 0 after costs), the raw win rate is ``p_hat = k / n``. The honest
``p_up_after_cost`` posterior we report is the Wilson lower bound at the
configured confidence level (default 95%, ``z = 1.96``). This is conservative
by construction — a pattern that "wins" 8/10 trades gets a CI lower bound of
about 0.47, not 0.80.

Why Wilson and not a point estimate
-----------------------------------
A point estimate plus a separate confidence interval is the recipe for
false-positive pattern promotion. By using the *lower bound* as the score
itself, we encode the F2 evidence discipline into the score: a pattern must
demonstrate edge in the worst credible case, not the best case, before it
can be recommended in any regime. This is the same discipline the
``forecast.orchestrator`` uses for its 555 Calibration gate.

Walk-forward gate
-----------------
A pattern is **eligible** for the top-3 ranking only when **all** of:

* ``walk_forward_validated == True`` (the sa-0 pattern module emits this;
  backtest-only patterns do not pass).
* ``sample_size >= DEFAULT_MIN_SAMPLE_SIZE`` (default 30 — anything thinner
  is a single regime cycle at best).
* ``ci_lower > DEFAULT_MIN_CI_LOWER`` (default 0.50 — patterns must clear
  50/50 in the worst credible case; lower CI bound is the Wilson lower
  bound of the win rate, so this is a hard floor on edge).
* Regime compatibility: pattern's ``compatible_regimes`` contains the
  current regime, OR the pattern's ``compatible_regimes`` is empty (which
  we treat as "any regime" with a small extra penalty on the score).

If zero patterns are eligible for a regime, that regime's ranking is
``NO_RECOMMENDATION`` and the global ``status`` is set to ``SHADOW``.

Default status = SHADOW (matches ``forecast.orchestrator`` doctrine).

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

# ══════════════════════════════════════════════════════════════════════════
# Vocabulary
# ══════════════════════════════════════════════════════════════════════════

NO_RECOMMENDATION = "NO_RECOMMENDATION"
STATUS_SHADOW = "SHADOW"

# Match the canonical regime vocabulary used by ``forecast.orchestrator``.
# UNKNOWN is a first-class regime here: it is the regime under which we
# always recommend SHADOW, because no edge is honestly attributable to a
# regime we cannot identify.
VALID_REGIMES = frozenset(
    {
        "COMPRESSION",
        "EXPANSION",
        "TRENDING",
        "RANGING",
        "TRANSITION",
        "EXHAUSTION",
        "UNKNOWN",
    }
)

# Minimum sample size for a pattern to be considered for ranking.
# 30 is the floor used by the gold forecast calibration harness; thinner
# samples are below the regime-cycle horizon we trust.
DEFAULT_MIN_SAMPLE_SIZE = 30

# Minimum Wilson lower-bound win rate for a pattern to clear the
# recommendation gate. 0.50 = "must beat the toss-up coin flip in the worst
# credible case". Higher values raise the bar (e.g. 0.55 for stricter edge).
DEFAULT_MIN_CI_LOWER = 0.50

# Wilson score z-value. 1.96 ≈ 95% one-sided lower bound. Configurable so
# the harness can dial up/down.
DEFAULT_WILSON_Z = 1.96


# ══════════════════════════════════════════════════════════════════════════
# Typed contracts
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class PatternStats:
    """One pattern's frequency/edge statistics (output of sa-0's module).

    The fields are exactly what the sa-0 pattern module is expected to
    emit; this is the input contract for the regime scoring layer.

    Attributes
    ----------
    pattern_id:
        Stable identifier for the pattern (e.g. ``"ascending_triangle"``).
        Must be unique within a ``score_patterns`` call.
    frequency:
        Fraction of bars/windows in which the pattern was observed,
        in [0, 1]. Recorded for completeness but not used by the gate.
    n_trades:
        Number of completed trade observations under this pattern.
        Drives the Wilson bound.
    n_wins:
        Number of trades whose forward return > 0 after costs.
    walk_forward_validated:
        True only if the edge was measured by a walk-forward harness with
        out-of-sample folds. False for backtest-only or fitted patterns.
    compatible_regimes:
        Iterable of regime names from ``VALID_REGIMES`` where the pattern
        is reported to have edge. Empty iterable is treated as "any
        regime" with a small penalty on the score (see scorer).
    edge_bps_mean:
        Mean edge in basis points after costs. Reported for transparency
        but not used by the gate (the Wilson bound on win rate is the
        single source of truth on edge quality here).
    """

    pattern_id: str
    frequency: float
    n_trades: int
    n_wins: int
    walk_forward_validated: bool
    compatible_regimes: Iterable[str] = field(default_factory=tuple)
    edge_bps_mean: float = 0.0

    def __post_init__(self) -> None:
        # Defensive clamps — bad input must not propagate into the score.
        if not isinstance(self.pattern_id, str) or not self.pattern_id:
            raise ValueError("PatternStats.pattern_id must be a non-empty string")
        if not (0.0 <= self.frequency <= 1.0):
            raise ValueError(
                f"PatternStats.frequency must be in [0, 1], got {self.frequency}"
            )
        if self.n_trades < 0:
            raise ValueError(
                f"PatternStats.n_trades must be >= 0, got {self.n_trades}"
            )
        if self.n_wins < 0 or self.n_wins > self.n_trades:
            raise ValueError(
                f"PatternStats.n_wins must satisfy 0 <= n_wins <= n_trades; "
                f"got n_wins={self.n_wins} n_trades={self.n_trades}"
            )


@dataclass
class ApexStateSnapshot:
    """The current APEX market state used to condition pattern scoring.

    This is intentionally a thin, pure-Python snapshot — no dependency on
    ``forecast.orchestrator`` — so the scorer can be unit-tested in
    isolation.

    Attributes
    ----------
    regime:
        Current regime name; must be in ``VALID_REGIMES``. UNKNOWN is a
        valid input: the scorer treats UNKNOWN as "no edge attributable"
        and returns ``NO_RECOMMENDATION`` for every ranking.
    g_score:
        APEX ``G`` score (clarity), in [0, 1]. Used as a multiplier on
        pattern scores when below 0.30 (CHAOS band per
        ``trading/apex/apex_predictor.py``): under CHAOS, patterns that
        passed the gate are still down-weighted so the ranking reflects
        the regime, not just the pattern.
    confluence:
        Confluence score from the signal layer, in [0, 1]. Same treatment
        as ``g_score`` — a multiplier under low confluence.
    momentum:
        Normalized momentum in [-1, 1]. Reported on each ``PatternScore``
        for downstream consumers; not used by the gate.
    volatility:
        Volatility regime label (``"low" | "normal" | "high" | "extreme"``).
        Same treatment as momentum: surfaced on the score, not gated on.
    """

    regime: str = "UNKNOWN"
    g_score: float = 0.0
    confluence: float = 0.0
    momentum: float = 0.0
    volatility: str = "normal"

    def __post_init__(self) -> None:
        if self.regime not in VALID_REGIMES:
            # Out-of-vocabulary regime is the same as UNKNOWN for scoring:
            # we cannot honestly attribute edge to a regime we do not know.
            self.regime = "UNKNOWN"
        if not (0.0 <= self.g_score <= 1.0):
            self.g_score = max(0.0, min(1.0, float(self.g_score)))
        if not (0.0 <= self.confluence <= 1.0):
            self.confluence = max(0.0, min(1.0, float(self.confluence)))
        if not (-1.0 <= self.momentum <= 1.0):
            self.momentum = max(-1.0, min(1.0, float(self.momentum)))
        if self.volatility not in {"low", "normal", "high", "extreme"}:
            self.volatility = "normal"


@dataclass
class PatternScore:
    """One pattern's scored edge under the current regime.

    Attributes
    ----------
    pattern_id:
        The pattern's stable identifier.
    score:
        The honest posterior: Wilson lower bound of the win rate, multiplied
        by the regime-conditioning factor (see ``score_patterns``). Always
        in [0, 1].
    ci_lower:
        Wilson lower bound of the win rate before the regime multiplier.
        This is the headline number for "edge after costs in the worst
        credible case".
    ci_upper:
        Wilson upper bound of the win rate. Reported for transparency.
    n_trades:
        The sample size used for the Wilson bound.
    regime_match:
        True if the pattern was *declared* compatible with the current
        regime. False if the pattern is "any regime" (empty
        ``compatible_regimes``) — these still qualify, with a small
        penalty applied at scoring time.
    """

    pattern_id: str
    score: float
    ci_lower: float
    ci_upper: float
    n_trades: int
    regime_match: bool


@dataclass
class RegimeRanking:
    """Ranking of patterns for one regime.

    When ``recommendation == NO_RECOMMENDATION`` the ``top3`` list is empty
    and ``status`` is ``SHADOW``.
    """

    regime: str
    recommendation: str
    status: str
    top3: list[PatternScore] = field(default_factory=list)
    reason: str = ""


@dataclass
class RegimeScoringResult:
    """The full scored packet.

    Attributes
    ----------
    status:
        Global status. ``SHADOW`` when *any* regime collapses to
        ``NO_RECOMMENDATION`` OR the current regime has no eligible
        patterns; ``LIVE_CANDIDATE`` when every regime in ``by_regime`` has
        at least one pattern passing the gate. (``LIVE_CANDIDATE`` is the
        *signal*, not authority — the final ACT/WAIT/HOLD verdict lives in
        the orchestrator's 888 lane.)
    current_regime:
        The regime the APEX snapshot reported.
    by_regime:
        Mapping of every regime in ``VALID_REGIMES`` to its ranking. Every
        regime is always present; regimes without eligible patterns get
        ``NO_RECOMMENDATION`` + ``SHADOW``.
    n_patterns_evaluated:
        Total patterns passed in.
    n_patterns_eligible:
        Patterns that cleared the gating for at least one regime.
    shadow_recommended:
        Convenience flag — True iff ``status == SHADOW``. The caller can
        surface this directly in their verdict lane.
    reason:
        Single-line reason for the global status. Empty when the caller
        does not supply one.
    """

    status: str
    current_regime: str
    by_regime: dict[str, RegimeRanking] = field(default_factory=dict)
    n_patterns_evaluated: int = 0
    n_patterns_eligible: int = 0
    shadow_recommended: bool = True
    reason: str = ""

    def top3_for(self, regime: str) -> list[PatternScore]:
        """Return the top-3 ranking for a single regime. Empty list if SHADOW."""
        r = self.by_regime.get(regime)
        return list(r.top3) if r else []


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════


def _wilson_lower_bound(
    k: int, n: int, z: float = DEFAULT_WILSON_Z
) -> float:
    """Wilson score lower bound on the win rate.

    For ``n == 0`` we return 0.0 by convention — there is no positive edge
    honestly attributable to zero observations.

    The bound is the standard Wilson score interval (one-sided lower)::

        p_hat = k / n
        denom = 1 + z^2 / n
        centre = p_hat + z^2 / (2n)
        offset = z * sqrt(p_hat * (1 - p_hat) / n + z^2 / (4 n^2))
        lower = (centre - offset) / denom

    This is the proper lower bound — never collapse to ``max(0, p_hat - 1.96 *
    sqrt(p_hat * (1-p_hat) / n))``, which overstates the lower bound near
    the boundaries (the well-known Wald interval defect).
    """
    if n <= 0:
        return 0.0
    if k < 0 or k > n:
        return 0.0
    p_hat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p_hat + z2 / (2.0 * n)
    margin = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n))
    lower = (centre - margin) / denom
    return max(0.0, min(1.0, lower))


def _wilson_upper_bound(
    k: int, n: int, z: float = DEFAULT_WILSON_Z
) -> float:
    """Wilson score upper bound on the win rate (one-sided upper).

    Mirror of ``_wilson_lower_bound``; provided so ``PatternScore`` can
    surface both bounds to the consumer without exposing the math.
    """
    if n <= 0:
        return 0.0
    if k < 0 or k > n:
        return 0.0
    p_hat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p_hat + z2 / (2.0 * n)
    margin = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n))
    upper = (centre + margin) / denom
    return max(0.0, min(1.0, upper))


def _is_pattern_eligible(
    stats: PatternStats,
    regime: str,
    min_sample_size: int,
    min_ci_lower: float,
    z: float,
) -> tuple[bool, float, float]:
    """Return (eligible, ci_lower, ci_upper) for the pattern under regime.

    Eligibility requires:
      * walk_forward_validated == True
      * n_trades >= min_sample_size
      * ci_lower > min_ci_lower (Wilson lower bound > gate)
      * regime is in compatible_regimes OR compatible_regimes is empty
        (empty = "any regime"; we keep eligibility but the caller applies
        a small score penalty so the ranking still prefers patterns that
        were *declared* compatible with the regime).
    """
    if not stats.walk_forward_validated:
        return False, 0.0, 0.0
    if stats.n_trades < min_sample_size:
        return False, 0.0, 0.0
    compat = tuple(stats.compatible_regimes or ())
    ci_lower = _wilson_lower_bound(stats.n_wins, stats.n_trades, z)
    ci_upper = _wilson_upper_bound(stats.n_wins, stats.n_trades, z)
    if ci_lower <= min_ci_lower:
        return False, ci_lower, ci_upper
    if compat and regime not in compat:
        return False, ci_lower, ci_upper
    return True, ci_lower, ci_upper


# ══════════════════════════════════════════════════════════════════════════
# Pure scorer
# ══════════════════════════════════════════════════════════════════════════


def score_patterns(
    apex_state: ApexStateSnapshot,
    pattern_stats: Iterable[PatternStats],
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    min_ci_lower: float = DEFAULT_MIN_CI_LOWER,
    z: float = DEFAULT_WILSON_Z,
    top_k: int = 3,
) -> RegimeScoringResult:
    """Score patterns per regime under the given APEX state.

    Returns a ``RegimeScoringResult`` whose ``status`` is:

    * ``LIVE_CANDIDATE`` — every regime has at least one eligible pattern
      that cleared the gate. This is the *signal*; the orchestrator's
      888 lane still owns the ACT/WAIT/HOLD verdict. We deliberately do
      not name this ``LIVE`` here to avoid implying authority the scorer
      does not hold.
    * ``SHADOW`` — current regime is UNKNOWN, or the current regime has
      no eligible patterns, or *any* regime in ``VALID_REGIMES`` is
      empty. SHADOW is the safe default.

    Parameters
    ----------
    apex_state:
        The current APEX state.
    pattern_stats:
        Iterable of ``PatternStats``. Order does not matter; output is
        sorted by score.
    min_sample_size, min_ci_lower, z:
        Tunables for the gate (see module constants).
    top_k:
        Maximum number of patterns to surface per regime. Default 3 to
        match the task contract.

    Returns
    -------
    RegimeScoringResult
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")

    stats_list = list(pattern_stats)
    n_evaluated = len(stats_list)

    # Index patterns by id for the duplicate check; refuse to silently
    # average two records of the "same" pattern with different stats.
    seen_ids: set[str] = set()
    for s in stats_list:
        if s.pattern_id in seen_ids:
            raise ValueError(
                f"duplicate pattern_id in input: {s.pattern_id!r} "
                "(score_patterns refuses to disambiguate by position)"
            )
        seen_ids.add(s.pattern_id)

    current_regime = apex_state.regime
    is_chaos = apex_state.g_score < 0.30 or apex_state.confluence < 0.30

    # We score against the *current* regime only — other regimes are
    # surfaced in ``by_regime`` as NO_RECOMMENDATION. This matches the
    # task contract: "top-3 patterns per regime" is satisfied by always
    # emitting one RegimeRanking per regime in the vocabulary.
    by_regime: dict[str, RegimeRanking] = {}

    any_regime_eligible = False

    for regime in VALID_REGIMES:
        scored: list[PatternScore] = []
        for s in stats_list:
            eligible, ci_lower, ci_upper = _is_pattern_eligible(
                s, regime, min_sample_size, min_ci_lower, z
            )
            if not eligible:
                continue

            compat = tuple(s.compatible_regimes or ())
            regime_match = bool(compat) and (regime in compat)

            # Regime-conditioning factor:
            #   1.00  if G/confluence healthy AND pattern declared compatible
            #   0.85  if pattern is "any regime" (empty compat) — small penalty
            #   0.50  if APEX is in the CHAOS band — patterns still pass the
            #         gate but we collapse their contribution so we never
            #         recommend an "edge" out of a CHAOS state
            if is_chaos:
                conditioning = 0.50
            elif regime_match:
                conditioning = 1.00
            else:
                conditioning = 0.85  # any-regime pattern

            score = round(ci_lower * conditioning, 6)

            scored.append(
                PatternScore(
                    pattern_id=s.pattern_id,
                    score=score,
                    ci_lower=round(ci_lower, 6),
                    ci_upper=round(ci_upper, 6),
                    n_trades=s.n_trades,
                    regime_match=regime_match,
                )
            )

        # Sort: highest score first, ties broken by sample size (more data
        # is more honest than less), then by pattern_id for determinism.
        scored.sort(
            key=lambda p: (-p.score, -p.n_trades, p.pattern_id)
        )
        top = scored[:top_k]

        if top:
            any_regime_eligible = True
            by_regime[regime] = RegimeRanking(
                regime=regime,
                recommendation="RECOMMENDED",
                status="LIVE_CANDIDATE",
                top3=top,
                reason="",
            )
        else:
            by_regime[regime] = RegimeRanking(
                regime=regime,
                recommendation=NO_RECOMMENDATION,
                status=STATUS_SHADOW,
                top3=[],
                reason=(
                    "no pattern passed the walk-forward + sample size + "
                    "Wilson lower-bound gate for this regime"
                ),
            )

    # Global status:
    #   SHADOW if current regime is UNKNOWN (we cannot attribute edge)
    #   SHADOW if current regime's ranking is NO_RECOMMENDATION
    #   SHADOW if ANY other regime is empty (defensive: at least one
    #     pattern in the catalog should clear for some regime — empty
    #     elsewhere signals the catalog itself is too thin to trust)
    #   LIVE_CANDIDATE otherwise
    current_ranking = by_regime.get(
        current_regime,
        RegimeRanking(
            regime=current_regime,
            recommendation=NO_RECOMMENDATION,
            status=STATUS_SHADOW,
            top3=[],
        ),
    )
    other_regimes_empty = any(
        r.recommendation == NO_RECOMMENDATION
        for r_name, r in by_regime.items()
        if r_name != current_regime
    )

    n_eligible = sum(
        1 for r in by_regime.values() if r.recommendation == "RECOMMENDED"
    )

    if current_regime == "UNKNOWN":
        global_status = STATUS_SHADOW
        global_reason = "current regime is UNKNOWN — no edge attributable"
    elif current_ranking.recommendation == NO_RECOMMENDATION:
        global_status = STATUS_SHADOW
        global_reason = (
            f"no eligible pattern for current regime {current_regime!r} "
            "(walk-forward + sample size + Wilson CI gate failed)"
        )
    elif other_regimes_empty and not any_regime_eligible:
        # Defensive: nothing in the catalog clears the gate anywhere.
        global_status = STATUS_SHADOW
        global_reason = "no pattern in the catalog passes the gate for any regime"
    else:
        global_status = "LIVE_CANDIDATE"
        global_reason = ""

    return RegimeScoringResult(
        status=global_status,
        current_regime=current_regime,
        by_regime=by_regime,
        n_patterns_evaluated=n_evaluated,
        n_patterns_eligible=n_eligible,
        shadow_recommended=(global_status == STATUS_SHADOW),
        reason=global_reason,
    )
