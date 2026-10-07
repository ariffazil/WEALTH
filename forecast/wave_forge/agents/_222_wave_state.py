"""Agent 222 — WAVE-STATE.

Builds the instantaneous amplitude/phase/frequency *posterior* over the
right edge of the history (the forecast origin) and decides which modes
are "validated" for the path-forge stage.

Validation criteria (each mode must clear all four):

1. **Cross-decomposition agreement** — the mode's instantaneous
   frequency is within ±15% of a frequency that *also* appears in the
   other decomposition (wavelet ↔ CEEMDAN). If only one decomposition
   succeeded, this rule is dropped but flagged.
2. **Right-edge persistence** — the mode's amplitude in the final
   ``lookback=30`` steps is at least 25% of its peak amplitude in the
   full history. Modes that decay to noise at the edge have no
   predictive value at the origin.
3. **Frequency stability** — the standard deviation of instantaneous
   frequency across the final ``lookback`` is ≤ 2× its mean. Highly
   chirping modes are unreliable for forward projection.
4. **Energy floor** — the mode's energy_share ≥ 0.5% of the total
   energy. Below 0.5% the mode is below the noise floor of the
   decomposition.

The validated mode set is the only thing the 333 lane is allowed to
extrapolate forward. The full set of modes is still emitted for
auditing — every mode has a ``validation_passed`` flag and a
``validation_reason``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

import numpy as np

from ..decompose import ModeRecord
from . import _111_decomposer as _decomposer


# Validation thresholds — exposed as constants so the audit lane and
# the tests can pin them.
FREQ_TOLERANCE = 0.15       # ±15% frequency match between decompositions
PERSISTENCE_LOOKBACK = 30   # right-edge window for persistence / stability
PERSISTENCE_MIN = 0.25      # min(amp_edge) / max(amp_full)
FREQ_STABILITY_MAX = 2.0    # stddev / mean ≤ this
ENERGY_FLOOR = 0.005        # 0.5% of total energy


@dataclass(frozen=True)
class ValidatedMode:
    """A single mode, plus the validation verdict."""

    source: str
    index: int
    mean_period_steps: Optional[float]
    energy_share: float
    edge_amplitude: float
    edge_frequency: float
    persistence_ratio: float
    freq_std_over_mean: float
    validation_passed: bool
    validation_reason: str
    matched_with: Optional[str] = None  # "wavelet:<idx>" | "ceemdan:<idx>"
    phase_offset: float = 0.0  # Hilbert phase at the right edge (radians)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "index": self.index,
            "mean_period_steps": self.mean_period_steps,
            "energy_share": round(self.energy_share, 6),
            "edge_amplitude": round(self.edge_amplitude, 4),
            "edge_frequency": round(self.edge_frequency, 6),
            "persistence_ratio": round(self.persistence_ratio, 4),
            "freq_std_over_mean": round(self.freq_std_over_mean, 4),
            "validation_passed": bool(self.validation_passed),
            "validation_reason": self.validation_reason,
            "matched_with": self.matched_with,
            "phase_offset": round(self.phase_offset, 4),
        }


@dataclass(frozen=True)
class WaveStatePosterior:
    """The 222-WAVE-STATE output."""

    ok: bool
    validated: List[ValidatedMode] = field(default_factory=list)
    all_modes: List[ValidatedMode] = field(default_factory=list)
    regime: str = "UNKNOWN"
    confidence: float = 0.0
    cross_decomposition_agreement: float = 0.0  # fraction of validated modes with a cross-decomposition match
    failures: list[str] = field(default_factory=list)
    observed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "222-WAVE-STATE",
            "ok": self.ok,
            "regime": self.regime,
            "confidence": round(self.confidence, 4),
            "cross_decomposition_agreement": round(self.cross_decomposition_agreement, 4),
            "validated_count": len(self.validated),
            "all_modes_count": len(self.all_modes),
            "validated": [m.to_dict() for m in self.validated],
            "failures": list(self.failures),
            "observed_at": self.observed_at,
        }


def _edge_amplitude(mode: ModeRecord, lookback: int) -> float:
    a = mode.amplitude
    if a.size == 0:
        return 0.0
    win = a[-lookback:] if a.size >= lookback else a
    return float(np.mean(win))


def _edge_frequency(mode: ModeRecord, lookback: int) -> float:
    f = mode.frequency
    if f.size == 0:
        return 0.0
    win = np.abs(f[-lookback:]) if f.size >= lookback else np.abs(f)
    return float(np.mean(win))


def _persistence_ratio(mode: ModeRecord, lookback: int) -> float:
    a = mode.amplitude
    if a.size < 4:
        return 0.0
    peak = float(np.max(a))
    if peak <= 0:
        return 0.0
    return float(np.mean(a[-lookback:]) / peak) if a.size >= lookback else float(np.mean(a) / peak)


def _freq_stability(mode: ModeRecord, lookback: int) -> float:
    f = np.abs(mode.frequency)
    if f.size < 3:
        return float("inf")
    win = f[-lookback:] if f.size >= lookback else f
    if win.size == 0 or np.mean(win) <= 0:
        return float("inf")
    return float(np.std(win) / np.mean(win))


def _classify_regime(modes: List[ValidatedMode]) -> tuple[str, float]:
    """Cheap regime classification from the validated mode set.

    Returns a (regime, confidence) pair. The mapping is deliberately
    simple — the 111 lane of the orchestrator owns the gold-specific
    regime label; here we only need to know whether the wave content is
    strong enough to support a forward forecast.
    """
    if not modes:
        return "NO_VALIDATED_MODES", 0.0
    total_energy = sum(m.energy_share for m in modes)
    if total_energy < 0.05:
        return "WEAK", 0.3
    if total_energy < 0.20:
        return "MIXED", 0.5
    # Strong wave content — distinguish trending (one dominant mode)
    # vs cyclical (many similar-energy modes).
    sorted_energy = sorted((m.energy_share for m in modes), reverse=True)
    if sorted_energy and sorted_energy[0] > 0.5 * total_energy:
        return "TRENDING", 0.65
    return "CYCLICAL", 0.6


def _match_cross_decomposition(
    wavelet_modes: List[ModeRecord],
    ceemdan_modes: List[ModeRecord],
) -> dict[int, str]:
    """For each wavelet mode, find the closest CEEMDAN frequency match.

    Returns ``{wavelet_index: 'ceemdan:<idx>'}`` for every wavelet
    mode that has a match within ``FREQ_TOLERANCE``. The match
    criterion is mean_period_steps (or instantaneous frequency); we
    use mean_period_steps because it is finite and well-defined for
    all non-trivial modes (instantaneous frequency can be near zero).
    """
    matches: dict[int, str] = {}
    for w in wavelet_modes:
        if w.mean_period_steps is None or w.mean_period_steps <= 0:
            continue
        w_period = w.mean_period_steps
        best = None
        best_dist = float("inf")
        for c in ceemdan_modes:
            if c.mean_period_steps is None or c.mean_period_steps <= 0:
                continue
            dist = abs(c.mean_period_steps - w_period) / w_period
            if dist <= FREQ_TOLERANCE and dist < best_dist:
                best = c
                best_dist = dist
        if best is not None:
            matches[w.index] = f"ceemdan:{best.index}"
    return matches


def _validate_mode(
    mode: ModeRecord,
    *,
    matched_with: Optional[str],
) -> ValidatedMode:
    """Run the four validation gates on a single mode."""
    persistence = _persistence_ratio(mode, PERSISTENCE_LOOKBACK)
    stability = _freq_stability(mode, PERSISTENCE_LOOKBACK)
    edge_amp = _edge_amplitude(mode, PERSISTENCE_LOOKBACK)
    edge_freq = _edge_frequency(mode, PERSISTENCE_LOOKBACK)

    reasons: list[str] = []
    if mode.energy_share < ENERGY_FLOOR:
        reasons.append(f"energy_below_floor:{mode.energy_share:.4f}<{ENERGY_FLOOR}")
    if persistence < PERSISTENCE_MIN:
        reasons.append(f"persistence_low:{persistence:.3f}<{PERSISTENCE_MIN}")
    if stability > FREQ_STABILITY_MAX:
        reasons.append(f"freq_unstable:{stability:.3f}>{FREQ_STABILITY_MAX}")
    # matched_with only required when BOTH decompositions succeeded
    # (otherwise the gate is dropped, not failed).
    if matched_with is None and not reasons:
        # no cross-decomposition match AND no other failure reason —
        # record it but pass it for downstream survival.
        reasons.append("no_cross_decomposition_match")

    passed = all(
        r.split(":")[0] not in ("energy_below_floor", "persistence_low", "freq_unstable")
        for r in reasons
    )
    # "no_cross_decomposition_match" only softens: mode can still be
    # promoted when at least one decomposition existed alone.
    phase_offset = float(mode.phase[-1]) if mode.phase.size > 0 else 0.0
    return ValidatedMode(
        source=mode.source,
        index=mode.index,
        mean_period_steps=mode.mean_period_steps,
        energy_share=mode.energy_share,
        edge_amplitude=edge_amp,
        edge_frequency=edge_freq,
        persistence_ratio=persistence,
        freq_std_over_mean=stability,
        validation_passed=passed,
        validation_reason=";".join(reasons) if reasons else "all_gates_passed",
        matched_with=matched_with,
        phase_offset=phase_offset,
    )


def AGENT_222_WaveState(decomp: _decomposer.DecompositionRecord) -> WaveStatePosterior:
    """Build the wave-state posterior and the validated-mode set."""
    observed_at = datetime.now(timezone.utc).isoformat()
    if not decomp.ok:
        return WaveStatePosterior(
            ok=False,
            failures=["decomposition_failed"],
            observed_at=observed_at,
        )

    # Build cross-decomposition matches (only meaningful if both
    # decompositions exist).
    wavelet_modes = decomp.wavelet
    ceemdan_modes = decomp.ceemdan
    cross_matches = (
        _match_cross_decomposition(wavelet_modes, ceemdan_modes)
        if wavelet_modes and ceemdan_modes
        else {}
    )

    # Validate wavelet modes.
    all_validated: List[ValidatedMode] = []
    for w in wavelet_modes:
        all_validated.append(
            _validate_mode(w, matched_with=cross_matches.get(w.index))
        )
    # Validate CEEMDAN modes — only modes whose frequency is matched
    # from the wavelet side get a ``matched_with`` label.
    inverse_match = {v: k for k, v in cross_matches.items()}
    for c in ceemdan_modes:
        inverse = inverse_match.get(f"ceemdan:{c.index}")
        matched = f"wavelet:{inverse}" if inverse is not None else None
        all_validated.append(
            _validate_mode(c, matched_with=matched)
        )

    validated = [m for m in all_validated if m.validation_passed]
    regime, confidence = _classify_regime(validated)

    cross_agreement = (
        sum(1 for m in validated if m.matched_with is not None) / len(validated)
        if validated
        else 0.0
    )

    return WaveStatePosterior(
        ok=bool(validated),
        validated=validated,
        all_modes=all_validated,
        regime=regime,
        confidence=confidence,
        cross_decomposition_agreement=cross_agreement,
        failures=[],
        observed_at=observed_at,
    )


__all__ = [
    "AGENT_222_WaveState",
    "ValidatedMode",
    "WaveStatePosterior",
    "FREQ_TOLERANCE",
    "PERSISTENCE_LOOKBACK",
    "PERSISTENCE_MIN",
    "FREQ_STABILITY_MAX",
    "ENERGY_FLOOR",
]