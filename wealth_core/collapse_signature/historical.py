"""
WEALTH Core — Historical Pre-Collapse Corpus Loader.

Loads Enron, PDVSA, Pemex, Petrobras, WorldCom, Lehman, 1MDB
pre-collapse documents from /root/WEALTH/wealth_core/collapse_signature/corpus/
and provides them as text for collapse_signature_scan calibration.

Acquired corpora:
- enron_1999_ar.txt — Enron 1999 Annual Report (from UChicago Picker archive)
- enron_2000_ar.txt — Enron 2000 Annual Report (from UChicago Picker archive)

Pending corpora (must be acquired):
- pdvsa_2001_ar.txt — PDVSA 2001 Annual Report (Memoria Anual)
- pemex_2010_ar.txt — Pemex pre-crisis annual report
- petrobras_2013_ar.txt — Petrobras pre-Lava-Jato
- worldcom_2001_ar.txt — WorldCom 2001 10-K
- lehman_2007_ar.txt — Lehman Brothers 2007 Annual Report
- 1mdb_audit_2016.pdf — 1MDB audit documents (Malaysia AG report)

DITEMPA BUKAN DIBEI — Real corpora, not synthetic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

CORPUS_DIR = Path(__file__).parent / "corpus"


def list_available_corpora() -> Dict[str, dict]:
    """List all available pre-collapse corpora on disk.

    Returns dict of {corpus_id: {path, size_bytes, line_count, sample_text}}.
    """
    corpora: Dict[str, dict] = {}
    if not CORPUS_DIR.exists():
        return corpora

    for txt_path in sorted(CORPUS_DIR.glob("*.txt")):
        corpus_id = txt_path.stem
        try:
            text = txt_path.read_text(encoding="utf-8", errors="replace")
            corpora[corpus_id] = {
                "path": str(txt_path),
                "size_bytes": txt_path.stat().st_size,
                "line_count": len(text.splitlines()),
                "char_count": len(text),
                "sample_text": text[:600],
                "available": True,
            }
        except Exception as e:
            corpora[corpus_id] = {
                "path": str(txt_path),
                "available": False,
                "error": str(e),
            }
    return corpora


def load_corpus(corpus_id: str) -> Optional[str]:
    """Load a corpus by ID (filename stem).

    Examples: 'enron_1999_ar', 'enron_2000_ar', 'pdvsa_2001_ar'.
    Returns full text or None if not available.
    """
    txt_path = CORPUS_DIR / f"{corpus_id}.txt"
    if not txt_path.exists():
        return None
    try:
        return txt_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR loading corpus {corpus_id}: {e}]"


def extract_signature_signals(corpus_id: str, max_chars: int = 50000) -> Optional[dict]:
    """Extract institutional-collapse signature signals from a corpus.

    For calibration: runs the patterns library against the corpus
    text and returns the full 6-axis signature profile.
    """
    text = load_corpus(corpus_id)
    if text is None:
        return None

    # Subsample if very long
    if len(text) > max_chars:
        # Take first N chars (most important front-matter narrative)
        text = text[:max_chars]

    from .patterns import full_signature_profile, collapse_risk_score

    profile = full_signature_profile(text)
    risk = collapse_risk_score(profile)

    return {
        "corpus_id": corpus_id,
        "char_count": len(text),
        "profile": profile,
        "risk": risk,
    }


def compare_corpus_to_current(
    current_scenario: str,
    historical_corpus_id: str,
    max_chars: int = 50000,
) -> Optional[dict]:
    """Compare a current scenario signature to a historical pre-collapse
    corpus signature. Returns the delta per axis and overall risk delta.
    """
    historical = extract_signature_signals(historical_corpus_id, max_chars=max_chars)
    if historical is None:
        return None

    from .patterns import full_signature_profile, collapse_risk_score

    current_profile = full_signature_profile(current_scenario)
    current_risk = collapse_risk_score(current_profile)

    # Compute axis-by-axis delta (current - historical)
    deltas = {}
    for axis_name in current_profile:
        if axis_name == "related_party_jurisdiction_structural":
            continue
        cur = current_profile[axis_name]["signal_count"]
        hist = historical["profile"][axis_name]["signal_count"]
        deltas[axis_name] = {
            "current_signal_count": cur,
            "historical_signal_count": hist,
            "delta": cur - hist,
            "ratio": (cur / hist) if hist > 0 else float("inf"),
        }

    return {
        "current_risk": current_risk,
        "historical_corpus_id": historical_corpus_id,
        "historical_risk": historical["risk"],
        "axis_deltas": deltas,
        "comparison_recommendation": _build_comparison_recommendation(
            current_risk["risk_level"], historical["risk"]["risk_level"]
        ),
    }


def _build_comparison_recommendation(
    current_level: str, historical_level: str
) -> str:
    """Build human-readable recommendation from risk-level comparison."""
    levels = ["MINIMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    cur_idx = levels.index(current_level) if current_level in levels else 0
    hist_idx = levels.index(historical_level) if historical_level in levels else 0

    delta = cur_idx - hist_idx
    if delta >= 2:
        return (
            f"Current scenario signature ({current_level}) is significantly "
            f"HIGHER than historical pre-collapse baseline ({historical_level}). "
            f"888_HOLD warranted."
        )
    elif delta == 1:
        return (
            f"Current signature ({current_level}) exceeds historical "
            f"baseline ({historical_level}). Verify with KPI differential."
        )
    elif delta == 0:
        return (
            f"Current signature matches historical baseline ({current_level}). "
            f"High watch — operate as if at pre-collapse threshold."
        )
    elif delta == -1:
        return (
            f"Current signature ({current_level}) is below historical "
            f"baseline ({historical_level}). Lower concern, monitor axes."
        )
    else:
        return (
            f"Current signature ({current_level}) is significantly lower "
            f"than historical baseline ({historical_level})."
        )


__all__ = [
    "CORPUS_DIR",
    "list_available_corpora",
    "load_corpus",
    "extract_signature_signals",
    "compare_corpus_to_current",
]