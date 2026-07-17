"""Shared utilities for institutional stress/risk modules."""
from __future__ import annotations


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, v))
