"""
WEALTH Simulative Exploitation Detection — Tool Tests (2026-07-08)

Tests the 4 new MCP tools:
  1. wealth_stress_convergence
  2. wealth_simulative_scan
  3. wealth_vulnerability_window
  4. wealth_cascade_map

Authority: Arif (F13 SOVEREIGN) spec at /root/forge_work/2026-07-08/wealth-simulative-tools-spec.md
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from internal.monolith import (
    wealth_stress_convergence,
    wealth_simulative_scan,
    wealth_vulnerability_window,
    wealth_cascade_map,
)


# ============================================================
# TOOL 1: wealth_stress_convergence
# ============================================================


class TestStressConvergence:
    """Test stress convergence detection."""

    def test_stress_convergence_convergent(self):
        """5 signals above threshold → is_convergent=True."""
        signals = [
            {"name": "bod_thinning", "value": 0.8, "weight": 0.25},
            {"name": "profit_decline", "value": 0.7, "weight": 0.20},
            {"name": "restructuring", "value": 0.9, "weight": 0.15},
            {"name": "legal_disputes", "value": 0.8, "weight": 0.20},
            {"name": "governance_transition", "value": 0.6, "weight": 0.20},
        ]
        result = wealth_stress_convergence(
            signals=signals, threshold=0.6, window_months=6
        )

        assert result["convergence_score"] > 0.6
        assert result["is_convergent"] is True
        assert result["vulnerability_class"] in ("HIGH", "CRITICAL")
        assert result["regime"] in ("simulative", "extractive")
        assert len(result["dominant_signals"]) == 3
        assert len(result["stress_vector"]) == 5
        assert "epistemic_tag" in result
        assert "confidence" in result

    def test_stress_convergence_not_convergent(self):
        """2 signals below threshold → is_convergent=False."""
        signals = [
            {"name": "bod_thinning", "value": 0.2, "weight": 0.25},
            {"name": "profit_decline", "value": 0.1, "weight": 0.20},
            {"name": "restructuring", "value": 0.0, "weight": 0.15},
            {"name": "legal_disputes", "value": 0.1, "weight": 0.20},
            {"name": "governance_transition", "value": 0.1, "weight": 0.20},
        ]
        result = wealth_stress_convergence(
            signals=signals, threshold=0.6, window_months=6
        )

        assert result["convergence_score"] < 0.3
        assert result["is_convergent"] is False
        assert result["vulnerability_class"] == "LOW"
        assert result["regime"] == "inclusive"

    def test_stress_convergence_empty_signals(self):
        """Empty signals → safe defaults."""
        result = wealth_stress_convergence(signals=[], threshold=0.6)

        assert result["convergence_score"] == 0.0
        assert result["is_convergent"] is False
        assert result["vulnerability_class"] == "LOW"
        assert result["confidence"] == 0.0


# ============================================================
# TOOL 2: wealth_simulative_scan
# ============================================================


class TestSimulativeScan:
    """Test simulative exploitation detection."""

    def test_simulative_scan_detected(self):
        """First litigation + neutral claims + value extraction → is_simulative=True."""
        actor = {
            "name": "Shell MDS",
            "claims": ["neutral_party", "caught_in_middle", "willing_to_pay"],
            "actions": ["interpleader_filed", "injunction_sought", "payment_suspended"],
            "value_extracted": 1_000_000_000,
            "duration_months": 14,
        }
        institution = {
            "name": "PETRONAS",
            "stress_convergence_score": 0.78,
            "governance_state": "THIN",
            "active_external_disputes": 3,
        }
        context = {
            "prior_relationship_years": 60,
            "prior_litigation_count": 0,
            "legal_mechanism_used": "interpleader",
        }
        result = wealth_simulative_scan(
            actor=actor, institution=institution, context=context
        )

        assert result["simulative_score"] >= 0.6
        assert result["is_simulative"] is True
        assert result["verdict"] == "SIMULATIVE_EXPLOITATION"
        assert result["regime"] == "simulative"
        assert len(result["evidence"]) > 0
        assert "exploitation_vector" in result
        ev = result["exploitation_vector"]
        assert ev["precedent_break"] == 1.0  # first litigation
        assert "epistemic_tag" in result
        assert "confidence" in result

    def test_simulative_scan_not_detected(self):
        """Normal dispute with prior litigation → is_simulative=False."""
        actor = {
            "name": "Regular Vendor",
            "claims": ["payment_owed"],
            "actions": ["demand_letter_sent"],
            "value_extracted": 5_000_000,
            "duration_months": 3,
        }
        institution = {
            "name": "Stable Corp",
            "stress_convergence_score": 0.2,
            "governance_state": "STRONG",
            "active_external_disputes": 1,
        }
        context = {
            "prior_relationship_years": 10,
            "prior_litigation_count": 5,
            "legal_mechanism_used": "damages",
        }
        result = wealth_simulative_scan(
            actor=actor, institution=institution, context=context
        )

        assert result["simulative_score"] < 0.6
        assert result["is_simulative"] is False
        assert result["verdict"] == "NORMAL_DISPUTE"
        assert result["regime"] == "inclusive"


# ============================================================
# TOOL 3: wealth_vulnerability_window
# ============================================================


class TestVulnerabilityWindow:
    """Test governance vulnerability window detection."""

    def test_vulnerability_window_open(self):
        """Unfilled seats + restructuring → is_vulnerable=True."""
        board_changes = [
            {
                "name": "Ibrahim Baki",
                "role": "NINED",
                "resigned": "2024-10-16",
                "replacement_date": None,
            },
            {
                "name": "Johan Mahmood",
                "role": "NINED",
                "resigned": "2025-01-15",
                "replacement_date": None,
            },
        ]
        result = wealth_vulnerability_window(
            board_changes=board_changes,
            current_board_size=7,
            normal_board_size=10,
            executive_changes=[],
            restructuring_active=True,
            external_threats_active=3,
        )

        assert result["vulnerability_score"] >= 0.5
        assert result["is_vulnerable"] is True
        assert result["window_status"] == "OPEN"
        assert result["unfilled_seats"] == 2
        assert result["board_ratio"] == 0.7
        assert len(result["risk_factors"]) > 0
        assert "epistemic_tag" in result
        assert "confidence" in result

    def test_vulnerability_window_closed(self):
        """All seats filled → is_vulnerable=False."""
        board_changes = [
            {
                "name": "Ibrahim Baki",
                "role": "NINED",
                "resigned": "2024-10-16",
                "replacement_date": "2024-11-01",
            },
        ]
        result = wealth_vulnerability_window(
            board_changes=board_changes,
            current_board_size=10,
            normal_board_size=10,
            executive_changes=[],
            restructuring_active=False,
            external_threats_active=0,
        )

        assert result["vulnerability_score"] < 0.5
        assert result["is_vulnerable"] is False
        assert result["window_status"] == "CLOSED"
        assert result["unfilled_seats"] == 0
        assert result["board_ratio"] == 1.0


# ============================================================
# TOOL 4: wealth_cascade_map
# ============================================================


class TestCascadeMap:
    """Test cascade trigger chain mapping."""

    def test_cascade_map_exponential(self):
        """5 triggers with amplification → EXPONENTIAL."""
        triggers = [
            {
                "id": "T1",
                "name": "BG Call",
                "date": "2024-10-01",
                "blast_radius": 0.3,
                "type": "ESCALATION",
            },
            {
                "id": "T2",
                "name": "Petros Sues",
                "date": "2024-10-15",
                "blast_radius": 0.5,
                "type": "LEGAL",
                "depends_on": ["T1"],
            },
            {
                "id": "T3",
                "name": "Shell Interpleader",
                "date": "2024-11-01",
                "blast_radius": 0.8,
                "type": "LEGAL",
                "depends_on": ["T2"],
            },
            {
                "id": "T4",
                "name": "Injunction",
                "date": "2024-12-19",
                "blast_radius": 0.9,
                "type": "FREEZE",
                "depends_on": ["T3"],
            },
            {
                "id": "T5",
                "name": "MBR Freeze",
                "date": "2025-02-17",
                "blast_radius": 0.6,
                "type": "STRATEGIC",
                "depends_on": ["T4"],
            },
        ]
        result = wealth_cascade_map(triggers=triggers)

        assert result["cascade_type"] == "EXPONENTIAL"
        assert result["cumulative_blast_radius"] > 0.9
        assert result["amplification_factor"] >= 2.0
        assert result["cascade_depth"] == 5
        assert result["critical_path"] == ["T1", "T2", "T3", "T4", "T5"]
        assert result["weakest_link"]["id"] == "T1"
        assert result["cascade_graph"]["T1"] == ["T2"]
        assert result["cascade_graph"]["T4"] == ["T5"]
        assert "epistemic_tag" in result
        assert "confidence" in result

    def test_cascade_map_linear(self):
        """2 triggers → LINEAR."""
        triggers = [
            {
                "id": "T1",
                "name": "Initial Event",
                "date": "2024-01-01",
                "blast_radius": 0.3,
                "type": "ESCALATION",
            },
            {
                "id": "T2",
                "name": "Follow Up",
                "date": "2024-02-01",
                "blast_radius": 0.4,
                "type": "LEGAL",
                "depends_on": ["T1"],
            },
        ]
        result = wealth_cascade_map(triggers=triggers)

        assert result["cascade_type"] == "LINEAR"
        assert result["cascade_depth"] == 2
        assert result["cumulative_blast_radius"] < 0.9
        assert result["amplification_factor"] < 2.0
        assert result["critical_path"] == ["T1", "T2"]

    def test_cascade_map_empty(self):
        """Empty triggers → safe defaults."""
        result = wealth_cascade_map(triggers=[])

        assert result["cascade_type"] == "LINEAR"
        assert result["cascade_depth"] == 0
        assert result["cumulative_blast_radius"] == 0.0
        assert result["confidence"] == 0.0
