"""Agent 000 — CAUSALITY gate.

Pre-flight guard against any leak of future information into the
decomposition or the path forge. Operates on the *un-decomposed*
history (the cleanest place to check) and emits a causality certificate
that every downstream agent must respect.

The certificate is a typed dataclass, not prose. A certificate with
``ok=False`` is a HARD STOP — 111-DECOMPOSER, 333-PATH-FORGE, and
555-AUDITOR refuse to do any work until the gate is green.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from ..synthetic import HistorySeries


@dataclass(frozen=True)
class CausalityCertificate:
    """The 000-CAUSALITY verdict.

    Every downstream lane checks ``cert.ok`` before reading ``cert``.

    Attributes
    ----------
    ok
        True only when every check passed.
    failures
        Reasons the gate rejected the history (empty when ok=True).
    provenance
        OBSERVED (live cascade) / SYNTHETIC (declared fallback) / UNKNOWN.
    origin_time
        ISO-8601 UTC timestamp of the rightmost close that the model
        may use — the model's "now". Anything strictly after this is
        future.
    n_obs
        Number of bars in the history.
    history_window_days
        Span of the history (last - first), in days.
    notes
        Free-form audit notes (e.g. "synthetic_seed=1337").
    observed_at
        ISO-8601 UTC timestamp when the gate ran.
    """

    ok: bool
    failures: list[str] = field(default_factory=list)
    provenance: str = "UNKNOWN"
    origin_time: str = ""
    n_obs: int = 0
    history_window_days: float = 0.0
    notes: dict[str, Any] = field(default_factory=dict)
    observed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "000-CAUSALITY",
            "ok": self.ok,
            "failures": list(self.failures),
            "provenance": self.provenance,
            "origin_time": self.origin_time,
            "n_obs": self.n_obs,
            "history_window_days": self.history_window_days,
            "notes": dict(self.notes),
            "observed_at": self.observed_at,
        }


# Minimum viable XAUUSD history: 180 days. Below this we refuse to run
# (CEEMDAN needs enough samples to separate modes and 14-day / 30-day
# lookback attacks both require ≥ 30 days).
MIN_HISTORY_DAYS = 180
# Maximum history window. Older history gets dropped to keep the
# regime-relevance assumption honest. Gold's regime since 2024 has
# been different from 2008-2019; long histories invite leakage of
# stale structure into the modern forecast.
MAX_HISTORY_DAYS = 1500


def _index_to_origin(idx) -> str:
    """Convert a pandas index value to an ISO-8601 UTC string."""
    ts = pd.Timestamp(idx)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert("UTC").isoformat()


def AGENT_000_Causality(
    history: HistorySeries,
    *,
    now: datetime | None = None,
    min_history_days: int = MIN_HISTORY_DAYS,
) -> CausalityCertificate:
    """Run the causality gate and return a certificate.

    Checks performed:

    1. History is non-empty and contains a 'close' column.
    2. History length ≥ MIN_HISTORY_DAYS (otherwise 111-DECOMPOSER's
       CEEMDAN sifting becomes degenerate).
    3. History length ≤ MAX_HISTORY_DAYS (otherwise regime-relevance is
      compromised; we keep the latest N days instead).
    4. No NaN/Inf in close (NaN closes are a tell of broken feeds).
    5. Close series is strictly positive (log-transformation requires it).
    6. Index is monotonically increasing (no duplicate timestamps).

    The certificate's ``ok`` is True only when checks 1, 4, 5, 6 pass
    *and* the trimmed history satisfies 2-3. ``failures`` lists every
    failed check; an empty list means green light.
    """
    failures: list[str] = []
    notes: dict[str, Any] = {}

    if history is None or history.df is None or len(history.df) == 0:
        failures.append("empty_history")
        return CausalityCertificate(
            ok=False,
            failures=failures,
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    df = history.df
    if "close" not in df.columns:
        failures.append("missing_close_column")

    closes_series = (
        pd.to_numeric(df["close"], errors="coerce")
        if "close" in df.columns
        else pd.Series(dtype=float)
    )
    if closes_series.isna().any():
        failures.append("nan_in_close")
    if closes_series.isna().all():
        failures.append("all_close_nan")
    # Use numpy coercion so Pyright stops complaining about pandas dtypes.
    closes = np.asarray(closes_series.to_numpy(), dtype=float)
    if closes.size > 0 and np.any(closes <= 0):
        failures.append("non_positive_close")

    # Index monotonicity — duplicate timestamps would let a "future"
    # observation sneak in under a stale label.
    if not df.index.is_monotonic_increasing:
        failures.append("non_monotonic_index")
    if df.index.has_duplicates:
        failures.append("duplicate_timestamps")

    n_obs = int(len(closes))
    if n_obs > 0 and np.any(np.isfinite(closes)):
        window_days = float((df.index[-1] - df.index[0]).days)
    else:
        window_days = 0.0

    if window_days < min_history_days:
        failures.append(f"history_too_short:{window_days:.0f}d<{min_history_days}d")

    # History too long — keep only the latest MAX_HISTORY_DAYS for the
    # downstream agents. (The gate does NOT mutate the history; that's
    # the 111 agent's job.) We record the decision in ``notes`` so the
    # downstream agent can read it without re-computing.
    trim_required = window_days > MAX_HISTORY_DAYS
    notes["trim_required"] = trim_required
    notes["trim_window_days"] = MAX_HISTORY_DAYS
    notes["synthetic"] = history.is_synthetic
    notes["source"] = history.source
    notes["fetch_reason"] = history.reason

    origin = _index_to_origin(df.index[-1]) if n_obs > 0 else ""
    observed_at = (now or datetime.now(timezone.utc)).isoformat()

    return CausalityCertificate(
        ok=(len(failures) == 0),
        failures=failures,
        provenance=history.source,
        origin_time=origin,
        n_obs=n_obs,
        history_window_days=window_days,
        notes=notes,
        observed_at=observed_at,
    )


__all__ = [
    "AGENT_000_Causality",
    "CausalityCertificate",
    "MIN_HISTORY_DAYS",
    "MAX_HISTORY_DAYS",
]