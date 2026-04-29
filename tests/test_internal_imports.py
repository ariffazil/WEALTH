import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.invariants import get_g_score
from internal.monolith import create_envelope


def test_g_score_engine_imports_and_runs():
    result = get_g_score({"trust_index": 0.7, "maruah_score": 0.6})

    assert set(
        {
            "g_score",
            "delta_s",
            "lyapunov_lambda",
            "omega_capacity",
            "entropy_s",
            "verdict",
            "regime",
        }
    ).issubset(result)


def test_create_envelope_exposes_g_score_metrics():
    envelope = create_envelope(
        tool="wealth_reason_npv",
        dimension="Allocation",
        primary={"npv": 1200.0, "irr": 0.18, "discount_rate": 0.1},
        secondary={},
        flags=[],
    )

    assert "g_score" in envelope
    assert "risk" in envelope
    assert "verdict" in envelope["risk"]
