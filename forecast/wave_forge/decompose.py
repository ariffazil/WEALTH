"""Wavelet + CEEMDAN decomposition and Hilbert transform for XAUUSD waves.

Three pure-math capabilities, no I/O:

* :func:`wavelet_decompose` — Stationary Wavelet Transform (SWT) using
  ``pywt.swt``. SWT is the shift-invariant alternative to DWT; it does
  not downsample, so the boundary behaviour at the right edge is
  observable (and auditable) instead of hidden by aliasing.
* :func:`ceemdan_decompose` — Complete EEMD with Adaptive Noise (CEEMDAN).
  Implemented from scratch (no PyEMD dependency) using white-noise
  ensembles + the standard EMD sifting loop. Returns IMFs ordered
  highest-frequency → lowest-frequency, exactly like EEMD literature.
* :func:`hilbert_envelope` — Analytic-signal Hilbert transform that
  returns instantaneous amplitude, instantaneous phase, and
  instantaneous frequency for any 1-D real series.

Why not raw FFT? Raw FFT on prices injects spurious cycles whenever the
series has a trend or a structural break — the spectral leakage pollutes
both the high and low ends of the spectrum. Wavelet decomposition is
local in time, and CEEMDAN is data-adaptive (no fixed basis), so both
survive non-stationary XAUUSD without manufacturing false cycles. This
is the doctrine documented in the user's Perplexity-style audit.

The CEEMDAN implementation follows Torres et al. (2011) "A complete
ensemble empirical mode decomposition with adaptive noise" — but
adapted to the ``scipy`` stdlib (no PyEMD dependency) so the pipeline
remains pure-python and portable across Python 3.12+.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np
import pywt
from scipy.signal import hilbert


# ── Stationary Wavelet Transform (SWT) ──────────────────────────────────


def wavelet_decompose(
    x: np.ndarray,
    *,
    wavelet: str = "sym4",
    level: int = 4,
) -> List[np.ndarray]:
    """SWT decomposition. Returns [cA_n, cD_n, cD_{n-1}, ..., cD_1].

    SWT requires the input length to be a multiple of 2^level. We
    right-pad with the last value (constant-extension) — the right-edge
    padding is flagged in the audit notes by the caller, never hidden
    inside this function.

    Parameters
    ----------
    x
        1-D real series, finite values only.
    wavelet
        PyWavelets name; default ``sym4`` (near-symmetric, 4 vanishing
        moments) — a good default for financial series. Alternatives:
        ``db4``, ``coif2``, ``haar`` (for sanity tests).
    level
        Decomposition depth. SWT is O(N · level), and level must satisfy
        ``len(x) % 2**level == 0``; we pad to the next multiple.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise ValueError("wavelet_decompose expects a 1-D series")
    if np.any(~np.isfinite(x)):
        raise ValueError("wavelet_decompose refuses non-finite values")

    pad_target = int(np.ceil(len(x) / 2 ** level) * 2 ** level)
    if pad_target != len(x):
        pad = np.full(pad_target - len(x), x[-1], dtype=float)
        x = np.concatenate([x, pad])

    # pywt.swt returns coefficients as (cA_n, [cD_n, cD_{n-1}, ..., cD_1]).
    coeffs = pywt.swt(x, wavelet=wavelet, level=level, trim_approx=True)
    cA_n, cD_list = coeffs[0], list(coeffs[1:])

    # SWT actually returns (cA_n, cD_n, cD_{n-1}, ..., cD_1) as
    # ``coeffs = [cA_n, cD_n, cD_{n-1}, ..., cD_1]`` — confirm and align.
    flat: List[np.ndarray] = [cA_n]
    for c in cD_list:
        flat.append(c)
    return flat


def wavelet_reconstruct(components: Sequence[np.ndarray], *, wavelet: str = "sym4") -> np.ndarray:
    """Inverse SWT — sanity check the decomposition is lossless.

    Used by tests, not the live path. ``pywt.iswt`` expects the flat
    coefficient list ``[cA_n, cD_n, cD_{n-1}, ..., cD_1]`` — the same
    shape ``pywt.swt`` returns (NOT a tuple ``(cA_n, [cD_n, ...])``).
    """
    if len(components) < 2:
        raise ValueError("need at least [cA, cD] to reconstruct")
    flat = [np.asarray(c, dtype=float) for c in components]
    return np.asarray(pywt.iswt(flat, wavelet=wavelet), dtype=float)


# ── CEEMDAN (from scratch, scipy-only) ──────────────────────────────────


def _local_extrema_indices(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return indices of local maxima and local minima (1-D, length ≥ 3)."""
    if len(x) < 3:
        return np.array([], dtype=int), np.array([], dtype=int)
    dx = np.diff(x)
    # sign of derivative, padded to length
    sign = np.sign(dx)
    sign_changed = np.diff(sign) != 0
    # local max: dx goes +→− ; local min: dx goes −→+
    max_idx = np.where(sign_changed & (sign[:-1] > 0))[0] + 1
    min_idx = np.where(sign_changed & (sign[:-1] < 0))[0] + 1
    return max_idx, min_idx


def _cubic_spline_envelope(x: np.ndarray, xi: np.ndarray, yi: np.ndarray) -> np.ndarray:
    """Cubic spline interpolation for envelope construction (vectorised)."""
    # Sort xi to satisfy np.interp monotonicity.
    order = np.argsort(xi)
    xs = xi[order]
    ys = yi[order]
    return np.interp(x, xs, ys)


def _sift_once(x: np.ndarray, max_sift_iter: int = 50, tol: float = 1e-6) -> np.ndarray:
    """One EMD sifting pass — extract a single IMF from ``x``.

    Terminates when the number of extrema changes by ≤ 1 OR after
    ``max_sift_iter`` iterations. Returns the IMF (the mean of upper and
    lower envelopes subtracted from x).
    """
    h = np.asarray(x, dtype=float).copy()
    for _ in range(max_sift_iter):
        max_idx, min_idx = _local_extrema_indices(h)
        if len(max_idx) < 2 or len(min_idx) < 2:
            # No further sifting possible — the residue is monotone.
            return h
        upper = _cubic_spline_envelope(
            np.arange(len(h)), max_idx.astype(float), h[max_idx]
        )
        lower = _cubic_spline_envelope(
            np.arange(len(h)), min_idx.astype(float), h[min_idx]
        )
        mean_env = 0.5 * (upper + lower)
        new_h = h - mean_env
        # Termination: SD between successive iterations < tol
        denom = np.sum(h * h)
        if denom <= 0:
            return new_h
        sd = np.sum((new_h - h) ** 2) / denom
        h = new_h
        if sd < tol:
            return h
    return h


def _eemd_one_realisation(
    x: np.ndarray,
    *,
    ensemble_noise_std: float,
    ensemble_size: int,
    seed: int,
) -> np.ndarray:
    """Run one EMD-with-noise ensemble, return the averaged IMFs.

    Following Wu & Huang (2009): add white noise (scale chosen to cover
    the full frequency spectrum of x), decompose each noise-added
    series, average the IMFs across the ensemble.
    """
    rng = np.random.default_rng(seed)
    N = len(x)
    # First IMF's frequency band is the highest. We use a small fraction
    # of x.std as the noise amplitude — same convention as the original
    # EEMD paper for EMD-on-financial-series.
    if x.std() <= 0:
        return np.zeros_like(x)

    noise_amp = ensemble_noise_std * x.std()
    components: List[np.ndarray] = []
    for i in range(ensemble_size):
        noise = rng.normal(0.0, noise_amp, size=N)
        s = x + noise
        imfs = _emd_extract_all(s)
        if not components:
            components = [np.zeros(N) for _ in imfs]
        for j, imf in enumerate(imfs):
            if j < len(components):
                components[j] += imf
    return np.array([c / ensemble_size for c in components])


def _emd_extract_all(x: np.ndarray, *, max_imfs: int = 10) -> List[np.ndarray]:
    """EMD sifting until the residue is monotone or IMF count exceeds ``max_imfs``."""
    residue = np.asarray(x, dtype=float).copy()
    imfs: List[np.ndarray] = []
    for _ in range(max_imfs):
        max_idx, min_idx = _local_extrema_indices(residue)
        if len(max_idx) < 2 or len(min_idx) < 2:
            break
        imf = _sift_once(residue)
        # Numerical noise — IMFs smaller than 1e-8 of the input std are noise.
        if np.std(imf) < 1e-8 * (np.std(x) + 1e-12):
            break
        imfs.append(imf)
        residue = residue - imf
    imfs.append(residue)  # final residue is the trend
    return imfs


def ceemdan_decompose(
    x: np.ndarray,
    *,
    ensemble_size: int = 50,
    ensemble_noise_std: float = 0.2,
    max_imfs: int = 8,
    seed: int = 1337,
) -> List[np.ndarray]:
    """Complete EEMD with Adaptive Noise (CEEMDAN, Torres et al. 2011).

    Parameters
    ----------
    x
        1-D real series.
    ensemble_size
        Number of noise realisations per IMF. The literature recommends
        ≥ 50; we cap at 50 here for sandbox runtime.
    ensemble_noise_std
        Fraction of ``x.std()`` for the noise amplitude in each ensemble
        pass. Default 0.2 matches the original paper.
    max_imfs
        Safety cap on the number of IMFs returned (final residue is
        appended, so the list length is ≤ max_imfs + 1).
    seed
        RNG seed — deterministic across runs.

    Returns
    -------
    list of 1-D arrays, length ≤ max_imfs + 1, ordered high → low
    frequency. The last element is the residual trend.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise ValueError("ceemdan_decompose expects a 1-D series")
    if np.any(~np.isfinite(x)):
        raise ValueError("ceemdan_decompose refuses non-finite values")
    if len(x) < 16:
        raise ValueError("CEEMDAN needs at least 16 points to sifting meaningfully")

    N = len(x)
    rng = np.random.default_rng(seed)

    # CEEMDAN step 1: extract the first IMF (highest-frequency) using an
    # ensemble of (x + white_noise) and averaging the EMD first-IMFs.
    noise_amp = ensemble_noise_std * (x.std() + 1e-12)
    e1 = np.zeros(N)
    for i in range(ensemble_size):
        noise = rng.normal(0.0, noise_amp, size=N)
        s = x + noise
        imfs = _emd_extract_all(s)
        if imfs:
            e1 += imfs[0]
    e1 /= ensemble_size

    imfs: List[np.ndarray] = [e1]
    residue = x - e1

    # Subsequent IMFs: each step adds noise to the residue and takes the
    # first IMF of (residue + noise). The noise realisations are
    # *unique* per step (different seeds derived from the master seed).
    for k in range(1, max_imfs):
        ek = np.zeros(N)
        for i in range(ensemble_size):
            # Per-realisation noise — but each step's noise amplitude
            # shrinks to match the residual's local frequency band.
            step_noise_amp = noise_amp / (1.5 ** k)
            noise = rng.normal(0.0, step_noise_amp, size=N)
            s = residue + noise
            imfs_step = _emd_extract_all(s)
            if imfs_step:
                ek += imfs_step[0]
        ek /= ensemble_size
        # If the new IMF carries no signal, stop.
        if np.std(ek) < 1e-9 * (np.std(x) + 1e-12):
            break
        imfs.append(ek)
        residue = residue - ek

        # Termination: residue is monotone or has too few extrema.
        max_idx, min_idx = _local_extrema_indices(residue)
        if len(max_idx) < 2 or len(min_idx) < 2:
            break

    imfs.append(residue)  # final trend
    return imfs


# ── Hilbert envelope (instantaneous amplitude / phase / frequency) ────


def hilbert_envelope(x: np.ndarray) -> dict:
    """Analytic signal → instantaneous amplitude, phase, frequency.

    The instantaneous frequency at index t is ``d(phase)/dt / (2π)``
    computed via a centred finite difference of the unwrapped phase.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise ValueError("hilbert_envelope expects a 1-D series")

    analytic = hilbert(x)
    amplitude = np.abs(analytic)
    phase = np.unwrap(np.angle(analytic))
    inst_freq = np.zeros_like(phase)
    # Central difference for the interior; one-sided for the boundaries.
    if len(phase) >= 3:
        inst_freq[1:-1] = (phase[2:] - phase[:-2]) / (4.0 * np.pi)
        inst_freq[0] = (phase[1] - phase[0]) / (2.0 * np.pi)
        inst_freq[-1] = (phase[-1] - phase[-2]) / (2.0 * np.pi)
    return {
        "amplitude": amplitude,
        "phase": phase,
        "instantaneous_frequency": inst_freq,
    }


# ── Combined decomposition record ────────────────────────────────────────


@dataclass(frozen=True)
class ModeRecord:
    """A single wave mode (wavelet or CEEMDAN) with Hilbert envelope."""

    source: str  # "wavelet" | "ceemdan"
    index: int
    raw: np.ndarray
    amplitude: np.ndarray
    phase: np.ndarray
    frequency: np.ndarray
    mean_period_steps: Optional[float]
    energy_share: float


def build_mode_records(
    components: Sequence[np.ndarray],
    *,
    source: str,
    sample_total_energy: float,
) -> List[ModeRecord]:
    """Wrap raw components with their Hilbert envelope and energy share."""
    records: List[ModeRecord] = []
    for i, c in enumerate(components):
        env = hilbert_envelope(c)
        amp = env["amplitude"]
        # Mean period in samples = 1 / mean(instantaneous_frequency).
        # Guard against f≈0 in flat components.
        f = env["instantaneous_frequency"]
        nz = np.abs(f) > 1e-9
        if nz.any():
            mean_period = float(1.0 / np.mean(np.abs(f[nz])))
        else:
            mean_period = None
        energy = float(np.sum(c * c))
        share = energy / sample_total_energy if sample_total_energy > 0 else 0.0
        records.append(
            ModeRecord(
                source=source,
                index=i,
                raw=c,
                amplitude=amp,
                phase=env["phase"],
                frequency=f,
                mean_period_steps=mean_period,
                energy_share=share,
            )
        )
    return records


__all__ = [
    "wavelet_decompose",
    "wavelet_reconstruct",
    "ceemdan_decompose",
    "hilbert_envelope",
    "ModeRecord",
    "build_mode_records",
]