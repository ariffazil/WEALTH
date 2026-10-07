"""M5.5 — conformal recalibration layer.

A split-conformal recalibration that adjusts the predicted quantile
widths so that the empirical coverage on a calibration set matches the
target.

Mechanics
---------

1. Run M5 on a calibration window of origins, recording
   ``q_hat_i = forecast_sigma_i * z_q``  for each quantile.
2. After the fact, compute ``score_i = |y_i - median_i| / q_hat_i_median``
   (non-conformity score).
3. Take the (1-α)(1 + 1/n) quantile of the scores as the multiplier
   ``Q_α``.
4. At inference time, multiply every quantile width by ``Q_α``.

This is a strict split-conformal procedure. It does NOT change P50
(median = M0). It widens / narrows the tails symmetrically. We add an
*asymmetry multiplier* so that if the empirical upper scores exceed
the lower scores, the upper band is widened more — this lets M5
absorb the empirical fat tail of log returns.

The calibrator is *stateful* — it accumulates a window of past
non-conformity scores. Recalibration runs on every walk-forward origin
in O(n log n) (sort the scores), and the calibration set is bounded
to the last ``window`` origins (default 96).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class ConformalCalibrator:
    """Split-conformal quantile calibrator.

    Parameters
    ----------
    target_coverage_p10_p90
        Target coverage of [P10, P90] band, default 0.80.
    target_coverage_p25_p75
        Target coverage of [P25, P75] band, default 0.50.
    window
        Maximum number of calibration scores to keep. Older scores are
        discarded FIFO.
    """

    target_coverage_p10_p90: float = 0.80
    target_coverage_p25_p75: float = 0.50
    window: int = 96
    scores_abs: list[float] = field(default_factory=list)
    scores_upper: list[float] = field(default_factory=list)
    scores_lower: list[float] = field(default_factory=list)
    last_recalibration: dict = field(default_factory=dict)

    def record(self, *, realised: float, p50: float, p10: float, p25: float, p75: float, p90: float) -> None:
        """Record one (realised, forecast) outcome."""
        # Score = |realised - median| / sigma_band
        # We use the half-width of P10/P90 as the unit.
        band = max((p90 - p10) * 0.5, 1e-12)
        score_abs = float(abs(realised - p50) / band)
        if not np.isfinite(score_abs):
            return
        self.scores_abs.append(score_abs)
        if realised > p90:
            self.scores_upper.append((realised - p90) / max(p90 - p50, 1e-12))
        elif realised < p10:
            self.scores_lower.append((p10 - realised) / max(p50 - p10, 1e-12))
        # Trim window
        if len(self.scores_abs) > self.window:
            self.scores_abs = self.scores_abs[-self.window :]
            self.scores_upper = self.scores_upper[-self.window :]
            self.scores_lower = self.scores_lower[-self.window :]

    def recalibrate(
        self,
        *,
        p10: float,
        p25: float,
        p50: float,
        p75: float,
        p90: float,
    ) -> tuple[float, float, float, float, float]:
        """Apply recalibration to a fresh set of quantiles.

        Returns (p10', p25', p50, p75', p90'). P50 is unchanged.
        """
        # Required: at least 8 scores for a meaningful recalibration
        if len(self.scores_abs) < 8:
            self.last_recalibration = {
                "applied": False,
                "reason": "insufficient_calibration_window",
                "n_scores": len(self.scores_abs),
            }
            return p10, p25, p50, p75, p90

        scores = np.asarray(self.scores_abs, dtype=float)
        # Coverage-adjusted multiplier for the P10/P90 band
        q_alpha = self._conformal_quantile(scores, alpha=1.0 - self.target_coverage_p10_p90)
        # Coverage-adjusted multiplier for the P25/P75 band
        q_beta = self._conformal_quantile(scores, alpha=1.0 - self.target_coverage_p25_p75)

        # Apply — scale widths around the median
        half_10_90 = (p90 - p50)
        half_25_75 = (p75 - p50)
        new_p10 = p50 - half_10_90 * float(q_alpha)
        new_p90 = p50 + half_10_90 * float(q_alpha)
        new_p25 = p50 - half_25_75 * float(q_beta)
        new_p75 = p50 + half_25_75 * float(q_beta)

        # Asymmetry multiplier (heavier tail detection)
        asym_mult = 1.0
        if self.scores_upper and self.scores_lower:
            u = float(np.mean(self.scores_upper))
            l = float(np.mean(self.scores_lower))
            if (u + l) > 0:
                ratio = u / (u + l)  # > 0.5 means heavier upper tail
                # Map ratio∈[0.3, 0.7] to multiplier∈[0.85, 1.15]
                asym_mult = float(np.clip(0.85 + 0.30 * (ratio - 0.3) / 0.4, 0.85, 1.15))
                # Apply the multiplier asymmetrically
                new_p90 = p50 + (new_p90 - p50) * asym_mult
                new_p10 = p50 + (new_p10 - p50) * (2.0 - asym_mult)

        self.last_recalibration = {
            "applied": True,
            "n_scores": int(len(scores)),
            "q_alpha_p10_p90": float(q_alpha),
            "q_beta_p25_p75": float(q_beta),
            "asymmetry_multiplier": float(asym_mult),
        }

        return float(new_p10), float(new_p25), float(p50), float(new_p75), float(new_p90)

    @staticmethod
    def _conformal_quantile(scores: np.ndarray, *, alpha: float) -> float:
        # Split-conformal: take ceil((n+1)(1-α))/n quantile
        n = scores.size
        if n == 0:
            return 1.0
        # Standard finite-sample correction
        q_idx = int(np.ceil((n + 1) * (1.0 - alpha))) - 1
        q_idx = max(0, min(q_idx, n - 1))
        return float(np.partition(scores, q_idx)[q_idx])

    def state(self) -> dict:
        return {
            "n_scores_abs": len(self.scores_abs),
            "n_scores_upper": len(self.scores_upper),
            "n_scores_lower": len(self.scores_lower),
            "last_recalibration": dict(self.last_recalibration),
        }


def recalibrate_quantiles(calibrator: ConformalCalibrator, p10: float, p25: float, p50: float, p75: float, p90: float) -> tuple[float, float, float, float, float]:
    """Free-function wrapper around :meth:`ConformalCalibrator.recalibrate`."""
    return calibrator.recalibrate(p10=p10, p25=p25, p50=p50, p75=p75, p90=p90)


__all__ = ["ConformalCalibrator", "recalibrate_quantiles"]