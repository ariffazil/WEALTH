"""M7.6 — Thesis half-life: autocorrelation decay of disagreement signal.

The "thesis" is the bundle of claims (F = fundamentals, T = technical,
D = distribution/M5) about why a position should make money. A thesis
that survives all three organs agreeing for a long time is durable.
A thesis that flips sign every hour is fragile.

We measure the half-life of the disagreement signal: how long until
the cross-organ agreement vector decorrelates from its initial state?

Approach
--------

The caller provides a disagreement time-series — typically the
disagreement vector over the past N hours/days. We compute:

    R_k = autocorrelation of disagreement magnitude at lag k
    half_life = first k where R_k <= 0.5

If the disagreement signal is constant (no variance), half-life is
"infinite" (stable thesis). If it flips every step, half-life is 1.

We also report the autocorrelation decay constant τ from the fit
    R_k ≈ exp(-k / τ)

and the persistence_score (1 - 1/half_life, capped) which is the
multiplicative penalty the downstream size engine uses:

    half_life_penalty = clamp(persistence_score, 0, 1)

Honest fallback
---------------

If the input series is empty or constant, we return
data_insufficient=True OR (when constant) treat as infinite half-life
(stable thesis — no penalty). The caller decides.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class ThesisHalfLifeResult:
    half_life_bars: float            # in input-series units (e.g. hours)
    decay_constant_tau: float        # τ from exp(-k/τ) fit (NaN if degenerate)
    persistence_score: float         # in [0, 1]; 1 = stable, 0 = immediate decay
    autocorrelation_at_lag1: float   # AR(1) coefficient
    n_bars: int
    disagreement_mean: float
    disagreement_std: float
    data_insufficient: bool = False
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _autocorr(x: np.ndarray, lag: int) -> float:
    """Pearson autocorrelation at the given lag (0 = 1.0)."""
    if lag == 0:
        return 1.0
    if len(x) <= lag or len(x) < 2:
        return float("nan")
    if np.std(x) == 0:
        return 1.0
    a = x[:-lag]
    b = x[lag:]
    if len(a) < 1 or len(b) < 1:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return 1.0
    # Add a tiny noise floor to avoid degenerate 1-element slices
    # (and the RuntimeWarning about degrees of freedom <= 0).
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _fit_decay_tau(autocorrs: np.ndarray) -> float:
    """Fit τ from autocorr_k ≈ exp(-k/τ) over k >= 1."""
    ks = np.arange(1, len(autocorrs), dtype=float)
    rs = np.asarray(autocorrs[1:], dtype=float)
    mask = (rs > 0) & np.isfinite(rs)
    if not np.any(mask):
        return float("nan")
    # Linear fit: log(R_k) = -k / τ
    y = np.log(rs[mask])
    x = ks[mask]
    # Use only the first ~10 lags to avoid noisy tail.
    if len(x) > 10:
        x = x[:10]
        y = y[:10]
    # Fit y = -x / τ  ⇒  τ = -sum(x*x) / sum(x*y)
    denom = float(np.sum(x * y))
    if denom >= 0 or not np.isfinite(denom):
        return float("nan")
    return float(-np.sum(x * x) / denom)


def compute_thesis_half_life(
    *,
    disagreement_series: list[float],
    max_lag: int = 24,
) -> ThesisHalfLifeResult:
    """Compute the thesis half-life in bars.

    Parameters
    ----------
    disagreement_series : list[float]
        The disagreement magnitude over time (e.g. |F - T| + |T - D| +
        |D - F| over each bar). Empty or constant ⇒ special handling.
    max_lag : int
        Maximum lag to consider for the autocorrelation. Default 24.
    """
    reasons: list[str] = []
    if not disagreement_series or len(disagreement_series) < 4:
        return ThesisHalfLifeResult(
            half_life_bars=float("nan"),
            decay_constant_tau=float("nan"),
            persistence_score=float("nan"),
            autocorrelation_at_lag1=float("nan"),
            n_bars=len(disagreement_series or []),
            disagreement_mean=float("nan"),
            disagreement_std=float("nan"),
            data_insufficient=True,
            notes="series_too_short",
            reasons=["series_too_short"],
        )

    x = np.asarray(disagreement_series, dtype=float)
    if not np.all(np.isfinite(x)):
        return ThesisHalfLifeResult(
            half_life_bars=float("nan"),
            decay_constant_tau=float("nan"),
            persistence_score=float("nan"),
            autocorrelation_at_lag1=float("nan"),
            n_bars=int(len(x)),
            disagreement_mean=float("nan"),
            disagreement_std=float("nan"),
            data_insufficient=True,
            notes="nonfinite_inputs",
            reasons=["nonfinite_inputs"],
        )

    mean = float(np.mean(x))
    std = float(np.std(x))

    # Constant series ⇒ perfect persistence, no decay.
    if std == 0:
        return ThesisHalfLifeResult(
            half_life_bars=float("inf"),
            decay_constant_tau=float("inf"),
            persistence_score=1.0,
            autocorrelation_at_lag1=1.0,
            n_bars=int(len(x)),
            disagreement_mean=mean,
            disagreement_std=std,
            notes="constant_series_infinite_half_life",
        )

    # Compute autocorrelations up to max_lag (or len(x)//2, whichever is smaller).
    max_lag_eff = min(max_lag, max(1, len(x) // 2))
    autocorrs = np.array([_autocorr(x, k) for k in range(max_lag_eff + 1)])

    ar1 = float(autocorrs[1]) if len(autocorrs) > 1 else float("nan")
    tau = _fit_decay_tau(autocorrs)

    # Find the half-life: first lag where R_k <= 0.5.
    half_life = float("inf")
    for k in range(1, len(autocorrs)):
        if np.isfinite(autocorrs[k]) and autocorrs[k] <= 0.5:
            half_life = float(k)
            break

    # Persistence score in [0, 1].
    if np.isinf(half_life):
        persistence = 1.0
    else:
        # Map half_life=1 → 0, half_life=∞ → 1, scale ~1/(1 + half_life)
        persistence = float(1.0 / (1.0 + half_life))
        persistence = max(0.0, min(1.0, persistence))

    return ThesisHalfLifeResult(
        half_life_bars=half_life,
        decay_constant_tau=tau,
        persistence_score=persistence,
        autocorrelation_at_lag1=ar1,
        n_bars=int(len(x)),
        disagreement_mean=mean,
        disagreement_std=std,
        notes="pearson_autocorr_then_50pct_threshold",
        reasons=reasons,
    )


__all__ = ["ThesisHalfLifeResult", "compute_thesis_half_life"]
