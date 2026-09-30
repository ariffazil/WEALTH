"""M5.1 — conditional volatility: EWMA + HAR + GARCH-T candidates.

Three candidate volatility models, each producing a forecast of the
1H-ahead conditional variance σ²_t. Selection by QLIKE loss on a
calibration window.

    EWMA  — RiskMetrics λ-decay. σ²_t = (1-λ) r²_{t-1} + λ σ²_{t-1}.
    HAR   — Corsi's HAR-RV: σ²_t = β0 + β_d r²_{t-1d} + β_w r²_{t-1w} + β_m r²_{t-1m}.
    GARCH — Gaussian-GARCH(1,1) with Student-t innovations.

GARCH-T is implemented from scratch (no ``arch`` / ``statsmodels``); it
fits (ω, α, β) by approximate MLE with a Gaussian proxy score, then
re-scales σ by the Student-t scale factor (ν-2)/ν at inference.

QLIKE loss
==========
For a realised proxy r² and forecast variance h²:
    L = r²/h² - log(r²/h²) - 1
Mean QLIKE over the calibration window is the selection criterion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np
from scipy import optimize


@dataclass(frozen=True)
class VolCandidate:
    """A single volatility model fit result."""

    name: str  # "EWMA" | "HAR" | "GARCH-T"
    params: dict  # fitted parameters
    forecast_var_h1: float  # forecast 1H-ahead variance
    forecast_sigma_h1: float  # sqrt of forecast_var_h1 (1H)
    qlike_calibration: float  # mean QLIKE on the calibration window
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "params": self.params,
            "forecast_var_h1": self.forecast_var_h1,
            "forecast_sigma_h1": self.forecast_sigma_h1,
            "qlike_calibration": self.qlike_calibration,
            "notes": self.notes,
        }


# ── QLIKE ────────────────────────────────────────────────────────────────


def qlike_loss(realised_sq: np.ndarray, forecast_var: np.ndarray) -> float:
    """Mean QLIKE loss. Both arrays must be aligned.

    L_i = r_i / h_i - log(r_i / h_i) - 1
    """
    r = np.asarray(realised_sq, dtype=float)
    h = np.asarray(forecast_var, dtype=float)
    mask = (r > 0) & (h > 0) & np.isfinite(r) & np.isfinite(h)
    if not np.any(mask):
        return float("nan")
    ratio = r[mask] / h[mask]
    # Avoid log(0)
    ratio = np.clip(ratio, 1e-12, None)
    return float(np.mean(ratio - np.log(ratio) - 1.0))


# ── EWMA (RiskMetrics) ──────────────────────────────────────────────────


def fit_ewma(returns_sq: np.ndarray, *, lam: float = 0.94) -> VolCandidate:
    """Fit the EWMA variance recursion and return the 1H-ahead forecast."""
    r = np.asarray(returns_sq, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return VolCandidate(
            name="EWMA",
            params={"lambda": lam},
            forecast_var_h1=float("nan"),
            forecast_sigma_h1=float("nan"),
            qlike_calibration=float("nan"),
            notes="insufficient_history",
        )
    sigma2 = float(r[0])  # initialise at first observation
    h_list = []
    for i in range(1, r.size):
        h_list.append(sigma2)  # forecast for step i
        sigma2 = (1.0 - lam) * float(r[i - 1]) + lam * sigma2
    h_arr = np.asarray(h_list)
    # Trim to align with r[1:]
    r_tail = r[1:]
    ql = qlike_loss(r_tail, h_arr)
    forecast = (1.0 - lam) * float(r[-1]) + lam * sigma2
    return VolCandidate(
        name="EWMA",
        params={"lambda": lam},
        forecast_var_h1=float(forecast),
        forecast_sigma_h1=float(np.sqrt(max(forecast, 1e-18))),
        qlike_calibration=float(ql) if np.isfinite(ql) else float("inf"),
    )


def _select_lambda(returns_sq: np.ndarray, *, candidates: Iterable[float] = (0.90, 0.94, 0.96, 0.98)) -> tuple[float, float]:
    """Pick the EWMA λ that minimises QLIKE."""
    best_lam = float(next(iter(candidates)))
    best_ql = float("inf")
    for lam in candidates:
        cand = fit_ewma(returns_sq, lam=lam)
        if np.isfinite(cand.qlike_calibration) and cand.qlike_calibration < best_ql:
            best_ql = cand.qlike_calibration
            best_lam = float(lam)
    return best_lam, best_ql


# ── HAR-RV (Corsi, 2009 style, daily-aggregated) ────────────────────────


def _har_features_daily(returns_sq_hourly: np.ndarray, *, hours_per_day: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate hourly r² to daily r²_d, r²_w (5d), r²_m (22d).

    Returns (X, y) where X has columns [1, r²_dlag1, r²_wlag1, r²_mlag1]
    and y is r²_d (the daily realised-variance proxy). Aligns so X[i]
    predicts y[i+1].
    """
    r2 = np.asarray(returns_sq_hourly, dtype=float)
    r2 = r2[np.isfinite(r2)]
    n = (r2.size // hours_per_day) * hours_per_day
    r2 = r2[:n]
    if r2.size < hours_per_day * 22:
        return np.empty((0, 4)), np.empty((0,))
    daily = r2.reshape(-1, hours_per_day).sum(axis=1)  # sum -> daily RV proxy
    n_days = daily.size
    # Build rolling weekly (5d) and monthly (22d) means
    def _rolling_mean(arr: np.ndarray, win: int) -> np.ndarray:
        out = np.empty(arr.size)
        csum = np.cumsum(np.insert(arr, 0, 0.0))
        for i in range(arr.size):
            lo = max(0, i - win + 1)
            out[i] = (csum[i + 1] - csum[lo]) / (i - lo + 1)
        return out
    r2_d = daily
    r2_w = _rolling_mean(daily, 5)
    r2_m = _rolling_mean(daily, 22)
    # Build design matrix with lag-1 of d/w/m; y = r2_d (next day)
    X = np.column_stack([
        np.ones(n_days - 1),
        r2_d[:-1],
        r2_w[:-1],
        r2_m[:-1],
    ])
    y = r2_d[1:]
    return X, y


def fit_har(returns_sq: np.ndarray) -> VolCandidate:
    """Fit HAR-RV on the daily-aggregated proxy.

    Forecast variance is converted back to the per-hour scale by dividing
    by 24.
    """
    X, y = _har_features_daily(returns_sq)
    if X.size == 0 or y.size == 0:
        return VolCandidate(
            name="HAR",
            params={},
            forecast_var_h1=float("nan"),
            forecast_sigma_h1=float("nan"),
            qlike_calibration=float("nan"),
            notes="insufficient_history_for_daily_aggregation",
        )
    # OLS via numpy lstsq
    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except Exception as e:
        return VolCandidate(
            name="HAR",
            params={},
            forecast_var_h1=float("nan"),
            forecast_sigma_h1=float("nan"),
            qlike_calibration=float("nan"),
            notes=f"lstsq_error: {e}",
        )
    y_hat = X @ beta
    # QLIKE on daily r² space
    ql = qlike_loss(y, np.clip(y_hat, 1e-18, None))
    # Forecast next-day variance
    next_day_var = float(np.array([1.0, y[-1], float(np.mean(y[-5:])), float(np.mean(y[-22:]))]) @ beta)
    forecast_var_h1 = max(next_day_var / 24.0, 1e-18)
    return VolCandidate(
        name="HAR",
        params={"beta0": float(beta[0]), "beta_d": float(beta[1]), "beta_w": float(beta[2]), "beta_m": float(beta[3])},
        forecast_var_h1=forecast_var_h1,
        forecast_sigma_h1=float(np.sqrt(forecast_var_h1)),
        qlike_calibration=float(ql) if np.isfinite(ql) else float("inf"),
        notes="har_rv_daily_aggregated",
    )


# ── GARCH(1,1) with Gaussian score, Student-t scale ─────────────────────


def _garch_recursion(params: np.ndarray, returns: np.ndarray) -> np.ndarray:
    """Compute σ² sequence given (omega, alpha, beta)."""
    omega, alpha, beta = float(params[0]), float(params[1]), float(params[2])
    n = returns.size
    sigma2 = np.empty(n)
    s0 = float(np.var(returns[: max(1, n // 10)]) + 1e-12)
    sigma2[0] = s0
    for t in range(1, n):
        sigma2[t] = omega + alpha * (returns[t - 1] ** 2) + beta * sigma2[t - 1]
    return sigma2


def _garch_neg_loglik_gaussian(params: np.ndarray, returns: np.ndarray) -> float:
    """Gaussian quasi-MLE for GARCH(1,1). Negative because we minimise."""
    omega, alpha, beta = float(params[0]), float(params[1]), float(params[2])
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 0.999:
        return 1e10
    sigma2 = _garch_recursion(params, returns)
    sigma2 = np.clip(sigma2, 1e-12, None)
    sigma = np.sqrt(sigma2)
    # -loglik (drop the constant 0.5 log(2π))
    nll = 0.5 * float(np.sum(np.log(sigma2) + (returns ** 2) / sigma2))
    if not np.isfinite(nll):
        return 1e10
    return nll


def fit_garch_t(returns: np.ndarray, *, nu: float = 6.0) -> VolCandidate:
    """Fit GARCH(1,1) via Gaussian quasi-MLE, then report Student-t scale.

    With ν ≈ 6 the scale factor √((ν-2)/ν) inflates σ for a heavier-
    tailed distribution. We freeze ν at 6 (no separate MLE step) — a
    common, conservative choice for daily-1H log returns of gold.

    Returns a VolCandidate whose ``forecast_sigma_h1`` is the Gaussian
    GARCH σ scaled by √((ν-2)/ν).
    """
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 50:
        return VolCandidate(
            name="GARCH-T",
            params={},
            forecast_var_h1=float("nan"),
            forecast_sigma_h1=float("nan"),
            qlike_calibration=float("nan"),
            notes="insufficient_history_for_garch",
        )
    # Initialise from unconditional variance
    s0 = float(np.var(r) + 1e-12)
    omega0 = s0 * 0.05
    alpha0 = 0.07
    beta0 = 0.85
    x0 = np.array([omega0, alpha0, beta0])
    bounds = [(1e-10, None), (1e-6, 0.5), (0.0, 0.999)]
    try:
        res = optimize.minimize(
            _garch_neg_loglik_gaussian,
            x0,
            args=(r,),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 200, "ftol": 1e-9},
        )
        if not res.success:
            # Try Nelder-Mead fallback
            res = optimize.minimize(
                _garch_neg_loglik_gaussian,
                x0,
                args=(r,),
                method="Nelder-Mead",
                options={"maxiter": 500, "xatol": 1e-7, "fatol": 1e-7},
            )
        params = res.x
    except Exception as e:
        return VolCandidate(
            name="GARCH-T",
            params={},
            forecast_var_h1=float("nan"),
            forecast_sigma_h1=float("nan"),
            qlike_calibration=float("nan"),
            notes=f"garch_optim_failed: {e}",
        )
    omega, alpha, beta = float(params[0]), float(params[1]), float(params[2])
    sigma2_seq = _garch_recursion(params, r)
    forecast_var = omega + alpha * (r[-1] ** 2) + beta * float(sigma2_seq[-1])
    forecast_var = max(forecast_var, 1e-18)
    # QLIKE on r² (the realised proxy) vs σ² sequence
    ql = qlike_loss(r ** 2, sigma2_seq)
    # Student-t scale: σ_t = σ_Gauss * sqrt((ν-2)/ν)
    t_scale = float(np.sqrt(max((nu - 2.0) / nu, 1e-12)))
    sigma_t_h1 = float(np.sqrt(forecast_var)) * t_scale
    var_t_h1 = sigma_t_h1 ** 2
    return VolCandidate(
        name="GARCH-T",
        params={"omega": omega, "alpha": alpha, "beta": beta, "nu": nu, "t_scale": t_scale},
        forecast_var_h1=float(var_t_h1),
        forecast_sigma_h1=float(sigma_t_h1),
        qlike_calibration=float(ql) if np.isfinite(ql) else float("inf"),
        notes="garch11_gaussian_qmle_student_t_scale",
    )


# ── Selection + multi-horizon forecast ──────────────────────────────────


def select_best_vol(returns: np.ndarray, *, allow_fallback_to_ewma: bool = True) -> VolCandidate:
    """Fit all three candidates and return the one with the lowest QLIKE.

    If a candidate fails to fit, it gets QLIKE=inf and is never chosen.
    If all fail, falls back to EWMA (lambda=0.94) by default.
    """
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return fit_ewma(r ** 2, lam=0.94)
    # Pick the best EWMA λ
    best_lam, _ = _select_lambda(r ** 2)
    cands = [
        fit_ewma(r ** 2, lam=best_lam),
        fit_har(r ** 2),
        fit_garch_t(r),
    ]
    # Filter out the NaN/inf ones
    valid = [c for c in cands if np.isfinite(c.qlike_calibration) and c.qlike_calibration < float("inf")]
    if valid:
        return min(valid, key=lambda c: c.qlike_calibration)
    if allow_fallback_to_ewma:
        return fit_ewma(r ** 2, lam=0.94)
    # Last resort
    return VolCandidate(
        name="NONE",
        params={},
        forecast_var_h1=float("nan"),
        forecast_sigma_h1=float("nan"),
        qlike_calibration=float("inf"),
        notes="all_candidates_failed",
    )


def forecast_sigma_h(candidate: VolCandidate, *, horizon_h: int) -> float:
    """Project the 1H forecast σ to a multi-hour horizon.

    For EWMA / GARCH-T the √h rule applies on the conditional variance.
    HAR is already a 1-day-ahead variance which we scaled by /24 to
    become a 1H variance; same √h rule then applies for horizons > 1H.
    """
    if not np.isfinite(candidate.forecast_var_h1):
        return float("nan")
    var_h = candidate.forecast_var_h1 * float(horizon_h)
    return float(np.sqrt(max(var_h, 1e-18)))


__all__ = [
    "VolCandidate",
    "qlike_loss",
    "fit_ewma",
    "fit_har",
    "fit_garch_t",
    "select_best_vol",
    "forecast_sigma_h",
]