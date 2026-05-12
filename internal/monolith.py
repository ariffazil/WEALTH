import asyncio
import hashlib
import inspect
import json
import math
import numbers
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable

# Ensure parent directory is in path for absolute imports if needed
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# WEALTH Internal Imports (Use relative or try/except for robustness)
try:
    from .governance import ForgeLaw, compute_kappa_r, compute_psi_le, get_qdf_version
except ImportError:
    from governance import ForgeLaw, compute_kappa_r, compute_psi_le, get_qdf_version

try:
    from host.governance.tri_witness import TriWitness
    TRIWITNESS_AVAILABLE = True
except Exception:
    TRIWITNESS_AVAILABLE = False
    class TriWitness:
        def __init__(self, *args, **kwargs):
            pass
        def to_dict(self):
            return {}

try:
    from internal.invariants import get_g_score

    G_SCORE_AVAILABLE = True
    G_SCORE_IMPORT_ERROR = None
except Exception as exc:
    # If standard import fails, try relative import
    try:
        from invariants import get_g_score
        G_SCORE_AVAILABLE = True
        G_SCORE_IMPORT_ERROR = None
    except Exception as exc2:
        G_SCORE_AVAILABLE = False
        G_SCORE_IMPORT_ERROR = f"{type(exc2).__name__}: {exc2}"

        def get_g_score(params: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "g_score": 0.0,
                "delta_s": 0.0,
                "delta_S": 0.0, # Compat
                "lyapunov_lambda": 0.0,
                "omega_capacity": 0.0,
                "entropy_s": 1.0,
                "verdict": "UNAVAILABLE",
                "regime": "unavailable",
                "is_outlier": False,
                "boundary_stress": params.get("resource_utilization", 0.8),
                "engine_error": G_SCORE_IMPORT_ERROR,
            }

__version__ = "2026.05.02"
"""WEALTH v2026.04.29 - Sovereign Pipeline OS with Expanded Resource Lattice."""

LAST_RECEIPT_HASH = "0" * 64

# Legacy arifOS path support
arifos_path = os.path.join(base_dir, "arifOS")
if os.path.exists(arifos_path) and arifos_path not in sys.path:
    sys.path.append(arifos_path)

try:
    from fastmcp import FastMCP

    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

    class FastMCP:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def tool(self, name=None):
            return lambda f: f

        def resource(self, uri):
            return lambda f: f

        def run(self):
            pass


# --- Sovereign Governance ---
try:
    from arifosmcp.runtime.megaTools.tool_01_init_anchor import check_floors
    from arifosmcp.runtime.vault_postgres import seal_to_vault as append_vault999

    GOVERNANCE_AVAILABLE = True
except Exception:
    try:
        from arifosmcp.runtime.tools import arifos_judge as check_floors
        from arifosmcp.runtime.vault_postgres import seal_to_vault as append_vault999

        GOVERNANCE_AVAILABLE = True
    except Exception:
        GOVERNANCE_AVAILABLE = False

        def check_floors(*args, **kwargs):
            return {"pass": True, "verdict": "SEAL", "violations": [], "holds": [], "warnings": []}

        try:
            from host.governance.vault_supabase import append_vault999

            GOVERNANCE_AVAILABLE = True
        except Exception:

            def append_vault999(record, **kwargs):
                return record


def _vault_append(record, **kwargs):
    """Bridge sync/async vault append safely."""
    import asyncio

    result = append_vault999(record, **kwargs)
    if inspect.isawaitable(result):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None:
            return asyncio.run(result)
        # Inside async context: fire-and-forget with task
        asyncio.create_task(result)
    return result


def _evaluate_floors(args: Dict[str, Any]) -> Dict[str, Any]:
    """Local hard floors that remain active even when arifOS is unavailable."""
    try:
        result = check_floors(args)
        if not isinstance(result, dict):
            result = {}
    except Exception:
        result = {}

    result = {
        "pass": result.get("pass", True),
        "verdict": result.get("verdict", "SEAL"),
        "violations": list(result.get("violations", [])),
        "holds": list(result.get("holds", [])),
        "warnings": list(result.get("warnings", [])),
    }

    if args.get("ai_is_deciding"):
        result["pass"] = False
        result["verdict"] = "VOID"
        if "F13_SOVEREIGN_DECISION_REQUIRED" not in result["violations"]:
            result["violations"].append("F13_SOVEREIGN_DECISION_REQUIRED")

    high_scale = args.get("scale_mode") in {"national", "crisis", "civilization", "agentic"}
    irreversible_unconfirmed = not args.get("reversible", True) and not args.get("human_confirmed", False)
    if irreversible_unconfirmed and (high_scale or args.get("critical", False)):
        if result["verdict"] != "VOID":
            result["verdict"] = "HOLD"
        result["pass"] = False
        if "F01_IRREVERSIBLE_ACTION_REQUIRES_HUMAN_CONFIRMATION" not in result["holds"]:
            result["holds"].append("F01_IRREVERSIBLE_ACTION_REQUIRES_HUMAN_CONFIRMATION")

    return result


# --- Coordination Layer ---
try:
    from host.coordination.lp_allocator import allocate as lp_allocate
    from host.coordination.cooperative import shapley_values, core_feasibility
    from host.coordination.strategic import nash_approximation
    from host.coordination.commons import commons_risk

    COORDINATION_AVAILABLE = True
except Exception:
    COORDINATION_AVAILABLE = False

    def lp_allocate(*args, **kwargs):
        return {"feasible": False}

    def shapley_values(*args, **kwargs):
        return {"shapley": {}}

    def core_feasibility(*args, **kwargs):
        return {"in_core": False}

    def nash_approximation(*args, **kwargs):
        return {"equilibrium": {}}

    def commons_risk(*args, **kwargs):
        return {"tragedy_risk": 1.0}


# --- Epistemic Layer ---
try:
    from host.epistemic.evoi import compute_evoi, compute_evoi_monte_carlo
    from host.epistemic.correlation_guard import (
        PortfolioCorrelationGuard as CorrelationGuard,
    )
    from host.epistemic.schema_validator import (
        EpistemicSchemaValidator as SchemaValidator,
    )

    EPISTEMIC_AVAILABLE = True
except Exception:
    EPISTEMIC_AVAILABLE = False

    def compute_evoi(*args, **kwargs):
        return {"error": "EPISTEMIC_UNAVAILABLE"}

    def compute_evoi_monte_carlo(*args, **kwargs):
        return {"error": "EPISTEMIC_UNAVAILABLE"}

    class CorrelationGuard:
        def __init__(self, *args, **kwargs):
            pass

        def check_portfolio(self, *args, **kwargs):
            return {"correlation_risk": 0.0}

    class SchemaValidator:
        def __init__(self, *args, **kwargs):
            pass

        def validate_portfolio(self, *args, **kwargs):
            return {"integrity_score": 1.0}


# --- Policy Engine ---
try:
    from host.governance.policy_engine import PolicyEngine

    POLICY_ENGINE_AVAILABLE = True
except Exception:
    POLICY_ENGINE_AVAILABLE = False

    class PolicyEngine:
        def __init__(self, *args, **kwargs):
            pass

        def evaluate(self, *args, **kwargs):
            return {"feasible": True, "flags": []}


# --- Harness Architecture (9-Harness Constraint) ---
try:
    from host.governance.harness_alarm import HarnessAlarmSystem
except Exception:
    class HarnessAlarmSystem:
        def trigger(self, *args, **kwargs):
            return {"status": "ALARM_UNAVAILABLE"}


class HarnessEngine:
    """9-Harness Constraint Architecture for WEALTH."""

    _LINEAGE_HASH = None
    _DOCTRINE_HASH = None

    @classmethod
    def get_doctrine_hash(cls) -> str:
        """Compute hash of the WEALTH_HARNESS.md file."""
        if cls._DOCTRINE_HASH is None:
            try:
                base_dir = os.path.dirname(__file__)
                base_name = os.path.basename(base_dir)
                if base_name == "internal":
                    harness_path = os.path.join(base_dir, "..", "canon", "WEALTH_HARNESS.md")
                else:
                    harness_path = os.path.join(base_dir, "canon", "WEALTH_HARNESS.md")
                harness_path = os.path.normpath(harness_path)
                if os.path.exists(harness_path):
                    with open(harness_path, "r", encoding="utf-8") as f:
                        cls._DOCTRINE_HASH = hashlib.sha256(f.read().encode()).hexdigest()
                else:
                    cls._DOCTRINE_HASH = "MISSING_DOCTRINE_FILE"
            except Exception:
                cls._DOCTRINE_HASH = "UNKNOWN_DOCTRINE"
        return cls._DOCTRINE_HASH

    @classmethod
    def get_lineage_hash(cls) -> str:
        """Compute the lineage hash of the HarnessEngine source code."""
        if cls._LINEAGE_HASH is None:
            try:
                # Use absolute source to handle dynamic imports/changes
                source = inspect.getsource(cls)
                cls._LINEAGE_HASH = hashlib.sha256(source.encode()).hexdigest()
            except Exception:
                cls._LINEAGE_HASH = "UNKNOWN_LINEAGE"
        return cls._LINEAGE_HASH

    HARNESS_NAMES = [
        "Identity",
        "Reality",
        "Epistemic",
        "Entropy",
        "Survival",
        "Constitutional",
        "Efficiency",
        "Coordination",
        "Civilization",
    ]

    TOOL_TO_HARNESS = {
        "wealth_init": "Identity",
        "vault_write": "Identity",
        "vault_query": "Identity",
        "wealth_record_transaction": "Identity",
        "wealth_snapshot_portfolio": "Identity",
        "wealth_ingest_fetch": "Reality",
        "wealth_ingest_snapshot": "Reality",
        "wealth_ingest_reconcile": "Reality",
        "wealth_ingest_vintage": "Reality",
        "wealth_ingest_health": "Reality",
        "wealth_ingest_sources": "Reality",
        "wealth_schema_validate": "Epistemic",
        "wealth_correlation_guard_check": "Epistemic",
        "wealth_evoi_compute": "Epistemic",
        "wealth_evoi_monte_carlo": "Epistemic",
        "wealth_monte_carlo_forecast": "Entropy",
        "wealth_emv_risk": "Entropy",
        "wealth_audit_entropy": "Entropy",
        "wealth_dscr_leverage": "Survival",
        "wealth_cashflow_flow": "Survival",
        "wealth_networth_state": "Survival",
        "wealth_growth_velocity": "Survival",
        "wealth_crisis_triage": "Survival",
        "wealth_check_floors": "Constitutional",
        "wealth_policy_audit": "Constitutional",
        "wealth_score_kernel": "Constitutional",
        "wealth_npv_reward": "Efficiency",
        "wealth_irr_yield": "Efficiency",
        "wealth_pi_efficiency": "Efficiency",
        "wealth_payback_time": "Efficiency",
        "wealth_coordination_equilibrium": "Coordination",
        "wealth_game_theory_solve": "Coordination",
        "wealth_personal_decision": "Coordination",
        "wealth_civilization_stewardship": "Civilization",
        "wealth_agent_budget": "Civilization",
    }

    SOVEREIGN_METADATA_FAMILIES = ["VAULT", "SENSE", "MIND", "HEART", "REASON", "JUDGE", "SURVIVAL"]
    
    SOVEREIGN_METADATA = {
        "wealth_init": {"family": "VAULT", "stage": "000-VAULT", "display": "wealth_init"},
        "vault_write": {"family": "VAULT", "stage": "000-VAULT", "display": "vault_write"},
        "vault_query": {"family": "VAULT", "stage": "000-VAULT", "display": "vault_query"},
        "wealth_record_transaction": {"family": "VAULT", "stage": "000-VAULT", "display": "wealth_record_transaction"},
        "wealth_snapshot_portfolio": {"family": "VAULT", "stage": "000-VAULT", "display": "wealth_snapshot_portfolio"},
        "wealth_ingest_fetch": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_ingest_fetch"},
        "wealth_ingest_snapshot": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_ingest_snapshot"},
        "wealth_ingest_reconcile": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_ingest_reconcile"},
        "wealth_ingest_health": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_ingest_health"},
        "wealth_ingest_sources": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_ingest_sources"},
        "wealth_schema_validate": {"family": "MIND", "stage": "200-MIND", "display": "wealth_schema_validate"},
        "wealth_correlation_guard_check": {"family": "MIND", "stage": "200-MIND", "display": "wealth_risk_correlation"},
        "wealth_evoi_compute": {"family": "MIND", "stage": "200-MIND", "display": "wealth_evoi_compute"},
        "wealth_monte_carlo_forecast": {"family": "MIND", "stage": "200-MIND", "display": "wealth_risk_monte_carlo"},
        "wealth_emv_risk": {"family": "MIND", "stage": "200-MIND", "display": "wealth_risk_emv"},
        "wealth_audit_entropy": {"family": "MIND", "stage": "200-MIND", "display": "wealth_audit_entropy", "dual_domain": ["MIND", "JUDGE"]},
        "wealth_dscr_leverage": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_dscr"},
        "wealth_crisis_triage": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_crisis_triage"},
        "wealth_civilization_stewardship": {"family": "HEART", "stage": "300-HEART", "display": "wealth_stewardship_civ"},
        "wealth_npv_reward": {"family": "REASON", "stage": "400-REASON", "display": "wealth_calc_npv"},
        "wealth_irr_yield": {"family": "REASON", "stage": "400-REASON", "display": "wealth_calc_irr"},
        "wealth_pi_efficiency": {"family": "REASON", "stage": "400-REASON", "display": "wealth_calc_pi"},
        "wealth_payback_time": {"family": "REASON", "stage": "400-REASON", "display": "wealth_calc_payback"},
        "wealth_coordination_equilibrium": {"family": "REASON", "stage": "400-REASON", "display": "wealth_coord_equilibrium"},
        "wealth_game_theory_solve": {"family": "REASON", "stage": "400-REASON", "display": "wealth_coord_game_theory"},
        "wealth_personal_decision": {"family": "REASON", "stage": "400-REASON", "display": "wealth_personal_decision"},
        "wealth_agent_budget": {"family": "REASON", "stage": "400-REASON", "display": "wealth_calc_agent_budget"},
        "wealth_score_kernel": {"family": "JUDGE", "stage": "888-JUDGE", "display": "wealth_score_kernel", "primary": True},
        "wealth_check_floors": {"family": "JUDGE", "stage": "800-JUDGE", "display": "wealth_check_floors"},
        "wealth_policy_audit": {"family": "JUDGE", "stage": "800-JUDGE", "display": "wealth_policy_audit"},
        "wealth_evoi_monte_carlo": {"family": "MIND", "stage": "200-MIND", "display": "wealth_evoi_monte_carlo"},
        "wealth_cashflow_flow": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_flow"},
        "wealth_networth_state": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_networth"},
        "wealth_growth_velocity": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_velocity"},
    }

    # ============================================================
    # WEALTH v2 Canonical Namespace Map
    # Non-breaking alias layer (Phase 1 Migration)
    # ============================================================
    V2_CANONICAL_MAP = {
        # SENSE (100)
        "wealth_sense_fetch": "wealth_ingest_fetch",
        "wealth_sense_snapshot": "wealth_ingest_snapshot",
        "wealth_sense_reconcile": "wealth_ingest_reconcile",
        "wealth_sense_health": "wealth_ingest_health",
        "wealth_sense_vintage": "wealth_ingest_vintage",
        "wealth_sense_sources": "wealth_ingest_sources",
        # MIND (200)
        "wealth_mind_emv": "wealth_emv_risk",
        "wealth_mind_monte_carlo": "wealth_monte_carlo_forecast",
        "wealth_mind_correlation": "wealth_correlation_guard_check",
        "wealth_mind_evoi": "wealth_evoi_compute",
        "wealth_mind_evoi_mc": "wealth_evoi_monte_carlo",
        "wealth_mind_schema": "wealth_schema_validate",
        # SURVIVAL (300)
        "wealth_survival_dscr": "wealth_dscr_leverage",
        "wealth_survival_networth": "wealth_networth_state",
        "wealth_survival_velocity": "wealth_growth_velocity",
        "wealth_survival_cashflow": "wealth_cashflow_flow",
        "wealth_survival_triage": "wealth_crisis_triage",
        "wealth_survival_civilization": "wealth_civilization_stewardship",
        # REASON (400)
        "wealth_reason_npv": "wealth_npv_reward",
        "wealth_npv_reward": "wealth_npv_reward",
        "wealth_reason_irr": "wealth_irr_yield",
        "wealth_reason_pi": "wealth_pi_efficiency",
        "wealth_reason_payback": "wealth_payback_time",
        "wealth_reason_equilibrium": "wealth_coordination_equilibrium",
        "wealth_reason_game": "wealth_game_theory_solve",
        "wealth_reason_personal": "wealth_personal_decision",
        "wealth_reason_agent": "wealth_agent_budget",
        # JUDGE (888)
        "wealth_judge_kernel": "wealth_score_kernel",
        "wealth_judge_floors": "wealth_check_floors",
        "wealth_judge_policy": "wealth_policy_audit",
        "wealth_judge_entropy": "wealth_audit_entropy",
        # VAULT (999)
        "wealth_vault_init": "wealth_init",
        "wealth_vault_record": "wealth_record_transaction",
        "wealth_vault_snapshot": "wealth_snapshot_portfolio",
    }

    def __init__(self):
        self.alarm_system = HarnessAlarmSystem()

    def audit(self, tool_name: str, primary: Dict[str, Any], flags: List[str], parent_hash: str = "") -> Dict[str, Any]:
        """Audit the current tool call against the 9-harness constraints."""
        harness_status = {name: {"stress": 0.0, "status": "SECURE"} for name in self.HARNESS_NAMES}
        violations = []
        
        # 0. Global Doctrine Seal
        d_hash = self.get_doctrine_hash()
        violations = []

        # 1. Identity Check
        if "UNAUTHENTICATED" in flags or "UNANCHORED" in flags:
            harness_status["Identity"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("IDENTITY_HARNESS_FAILURE")
        elif parent_hash and len(parent_hash) != 64:
            harness_status["Identity"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("IDENTITY_CHAIN_VIOLATION")

        # 2. Reality Check
        if any(f in flags for f in ["INVALID_DATA_SOURCE", "STALE_DATA", "SOURCE_DIVERGENCE"]):
            harness_status["Reality"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("REALITY_HARNESS_FAILURE")

        # 3. Epistemic Check
        if "EPISTEMIC_FAILURE" in flags or "LOW_INTEGRITY" in flags:
            harness_status["Epistemic"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("EPISTEMIC_HARNESS_FAILURE")
        elif "SYSTEMIC_CORRELATION_RISK" in flags:
            harness_status["Epistemic"].update({"stress": 0.8, "status": "STRESSED"})

        # 4. Entropy Check
        if "HIGH_ENTROPY_SIGNAL" in flags or "MULTIPLE_IRR_POSSIBLE" in flags:
            harness_status["Entropy"].update({"stress": 0.8, "status": "STRESSED"})

        # 5. Survival Check (Structural Load)
        if any(f in flags for f in ["LEVERAGE_DEFAULT", "RUNWAY_CRITICAL", "CASHFLOW_NEGATIVE"]):
            harness_status["Survival"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("SURVIVAL_HARNESS_FAILURE")

        # 6. Constitutional Check
        if any(f.startswith("FLOOR_") for f in flags) or "SOVEREIGN_DIGNITY_LOW" in flags:
            harness_status["Constitutional"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("CONSTITUTIONAL_HARNESS_FAILURE")

        # 7. Efficiency Check
        pi_val = primary.get("pi")
        if tool_name == "wealth_pi_efficiency" and pi_val is not None and pi_val < 1.0:
            harness_status["Efficiency"].update({"stress": 0.9, "status": "STRESSED"})
        if "NOT_RECOVERED" in flags:
            harness_status["Efficiency"].update({"stress": 1.0, "status": "SNAPPED"})

        # 8. Coordination Check
        if "TRAGEDY_RISK_HIGH" in flags or "CORE_INFEASIBLE" in flags:
            harness_status["Coordination"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("COORDINATION_HARNESS_FAILURE")

        # 9. Civilization Check (Quantified Triggers)
        carbon = primary.get("carbon_intensity", 0.0)
        collapse = primary.get("collapse_risk", 0.0)
        growth = primary.get("sustainable_growth_rate", 1.0)
        
        if carbon > 0.04 or collapse > 0.3 or growth < 0:
            harness_status["Civilization"].update({
                "stress": 1.0, 
                "status": "SNAPPED",
                "detail": f"C:{carbon:.3f} | R:{collapse:.3f} | G:{growth:.3f}"
            })
            violations.append("CIVILIZATION_HARNESS_FAILURE")

        # Systemic Accumulator Rule (Cumulative Stress)
        systemic_stress = sum(h["stress"] for h in harness_status.values())
        if systemic_stress > 2.0:
            violations.append("SYSTEMIC_INSTABILITY_FAILURE")

        overall_verdict = "PASS"
        recommended_verdict = "SEAL"
        
        has_snapped = any(h["status"] == "SNAPPED" for h in harness_status.values())
        has_stressed = any(h["status"] == "STRESSED" for h in harness_status.values())
        
        if has_snapped or systemic_stress > 2.0:
            overall_verdict = "FAIL"
            recommended_verdict = "VOID"
            self.alarm_system.trigger(tool_name, "Systemic", {"violations": violations, "systemic_stress": systemic_stress})
        elif has_stressed or systemic_stress > 1.2:
            overall_verdict = "PASS" # Keep PASS for backward compatibility
            recommended_verdict = "SABAR"
        
        return {
            "verdict": overall_verdict,
            "recommended_verdict": recommended_verdict,
            "harness_status": harness_status,
            "violations": violations,
            "systemic_stress": round(systemic_stress, 4),
            "harness_lineage_hash": self.get_lineage_hash(),
            "doctrine_hash": self.get_doctrine_hash(),
        }


def maruah_band(score):
    if score >= 0.85:
        return "SOVEREIGN"
    if score >= 0.70:
        return "STABLE"
    if score >= 0.60:
        return "FLOOR"
    if score >= 0.40:
        return "AMBER"
    return "RED"


mcp = FastMCP("WEALTH Valuation Kernel")
WEALTH_SCHEMA_VERSION = "wealth.physics_economics.v1"


WEALTH_TOOL_MANIFEST: List[Dict[str, object]] = [
    {"name": "mcp_health_check", "axis": "identity", "expose": False},
    {"name": "vault_query", "axis": "trace", "expose": False},
    {"name": "vault_write", "axis": "seal", "expose": False},
    {"name": "vaultquery", "axis": "trace", "expose": False},
    {"name": "vaultwrite", "axis": "seal", "expose": False},
    {"name": "wealth_agent_path", "axis": "reflect", "expose": False},
    {"name": "wealth_allocate_optimize", "axis": "execute", "expose": False},
    {"name": "wealth_boundary_floors", "axis": "boundary", "expose": False},
    {"name": "wealth_boundary_governance", "axis": "boundary", "expose": False},
    {"name": "wealth_boundary_policy", "axis": "boundary", "expose": False},
    {"name": "wealth_conservation_capital", "axis": "vitality", "expose": False},
    {"name": "wealth_density_pi", "axis": "reason", "expose": False},
    {"name": "wealth_energy_irr", "axis": "reason", "expose": False},
    {"name": "wealth_energy_productivity", "axis": "reason", "expose": False},
    {"name": "wealth_entropy_audit", "axis": "critique", "expose": False},
    {"name": "wealth_entropy_risk", "axis": "critique", "expose": False},
    {"name": "wealth_expectation_emv", "axis": "reason", "expose": False},
    {"name": "wealth_field_equilibrium", "axis": "observe", "expose": False},
    {"name": "wealth_field_game", "axis": "reason", "expose": False},
    {"name": "wealth_field_macro", "axis": "observe", "expose": False},
    {"name": "wealth_flow_cashflow", "axis": "vitality", "expose": False},
    {"name": "wealth_flow_liquidity", "axis": "vitality", "expose": False},
    {"name": "wealth_future_simulate", "axis": "reason", "expose": False},
    {"name": "wealth_future_steward", "axis": "reason", "expose": False},
    {"name": "wealth_future_value", "axis": "reason", "expose": False},
    {"name": "wealth_game_coordinate", "axis": "reason", "expose": False},
    {"name": "wealth_game_coordination", "axis": "reason", "expose": False},
    {"name": "wealth_governance_verdict", "axis": "critique", "expose": False},
    {"name": "wealth_gradient_price", "axis": "observe", "expose": False},
    {"name": "wealth_gravity_dscr", "axis": "vitality", "expose": False},
    {"name": "wealth_hysteresis_ledger", "axis": "seal", "expose": False},
    {"name": "wealth_inertia_leverage", "axis": "boundary", "expose": False},
    {"name": "wealth_ledger_query", "axis": "trace", "expose": False},
    {"name": "wealth_ledger_record", "axis": "seal", "expose": False},
    {"name": "wealth_ledger_snapshot", "axis": "seal", "expose": False},
    {"name": "wealth_ledger_write", "axis": "seal", "expose": False},
    {"name": "wealth_mass_networth", "axis": "vitality", "expose": False},
    {"name": "wealth_preference_rank", "axis": "reason", "expose": False},
    {"name": "wealth_present_expect", "axis": "reason", "expose": False},
    {"name": "wealth_pressure_triage", "axis": "vitality", "expose": False},
    {"name": "wealth_probability_monte_carlo", "axis": "reason", "expose": False},
    {"name": "wealth_rule_enforce", "axis": "judge", "expose": False},
    {"name": "wealth_sense_ingest", "axis": "observe", "expose": False},
    {"name": "wealth_sensor_fetch", "axis": "observe", "expose": False},
    {"name": "wealth_sensor_health", "axis": "identity", "expose": False},
    {"name": "wealth_sensor_reconcile", "axis": "observe", "expose": False},
    {"name": "wealth_sensor_snapshot", "axis": "observe", "expose": False},
    {"name": "wealth_sensor_sources", "axis": "observe", "expose": False},
    {"name": "wealth_sensor_vintage", "axis": "observe", "expose": False},
    {"name": "wealth_signal_information", "axis": "verify", "expose": False},
    {"name": "wealth_stewardship_civilization", "axis": "reflect", "expose": False},
    {"name": "wealth_survival_leverage", "axis": "vitality", "expose": False},
    {"name": "wealth_survival_liquidity", "axis": "vitality", "expose": False},
    {"name": "wealth_system_registry_status", "axis": "reason", "expose": False},
    {"name": "wealth_time_discount", "axis": "reason", "expose": False},
    {"name": "wealth_time_payback", "axis": "reason", "expose": False},
    {"name": "wealth_value_npv", "axis": "reason", "expose": False},
    {"name": "wealth_velocity_runway", "axis": "vitality", "expose": False},
]

try:
    from federation.tool_manifest import FEDERATION_TOOLS, ToolManifest, CognitiveAxis as _WCA
    for _went in WEALTH_TOOL_MANIFEST:
        FEDERATION_TOOLS[str(_went["name"])] = ToolManifest(
            name=str(_went["name"]),
            description="",
            expose=bool(_went["expose"]),
            cognitive_axis=_WCA(str(_went["axis"])),
            organ="wealth",
        )
except Exception:
    pass  # federation module may not exist in all environments

@mcp.tool()
def mcp_health_check() -> dict:
    """Universal health check for federation stability."""
    return {
        "mcp": "WEALTH",
        "status": "OK",
        "transport": "SSE_VALID",
        "auth": "OK",
        "schema_version": WEALTH_SCHEMA_VERSION,
        "read_only": True,
        "final_authority": "ARIF",
    }

EPSILON = 1e-9
INVALID_FLAGS = {
    "INVALID_INITIAL_INVESTMENT",
    "INVALID_CASHFLOW_SERIES",
    "INVALID_DISCOUNT_RATE",
    "INVALID_FINANCE_RATE",
    "INVALID_REINVESTMENT_RATE",
    "INVALID_SCENARIOS",
    "INVALID_SCENARIO",
    "PROBABILITY_MASS_INVALID",
    "INVALID_DEBT_SERVICE",
    "INVALID_CFADS",
    "INVALID_BASE_RATE",
    "INGEST_LAYER_UNAVAILABLE",
}
HOLD_FLAGS = {"LEVERAGE_CRITICAL", "LEVERAGE_DEFAULT", "SOVEREIGN_DIGNITY_LOW"}
HOLD_FLAGS.add("MULTIPLE_IRR_POSSIBLE")
QUALIFY_FLAGS = {
    "NON_NORMAL_FLOWS",
    "IRR_NOT_FOUND",
    "NOT_RECOVERED",
    "EBITDA_PROXY_USED",
    "ADAPTER_NOT_FOUND",
    "NO_DATA_FETCHED",
    "RUNWAY_UNBOUNDED",
    "NO_INPUT_BASELINE",
}
DATA_GAP_FLAGS = {
    "ADAPTER_NOT_FOUND",
    "NO_DATA_FETCHED",
    "NO_INPUT_BASELINE",
    "RUNWAY_UNBOUNDED",
    "MISSING_REQUIRED_INPUT",
    "INPUT_REQUIRED",
    "EPISTEMIC_UNAVAILABLE",
    "COMPUTATION_ERROR",
    "ENGINE_NOT_IMPLEMENTED",
}
EPISTEMIC_ORDER = ["UNKNOWN", "HYPOTHESIS", "ESTIMATE", "PLAUSIBLE", "CLAIM"]
RELIABILITY_TO_TAG = {
    "guaranteed": "CLAIM",
    "regular": "PLAUSIBLE",
    "irregular": "ESTIMATE",
    "speculative": "HYPOTHESIS",
}


def round_value(value: Optional[float], digits: int = 6) -> Optional[float]:
    if value is None or not math.isfinite(value):
        return value
    return round(value, digits)


def _flag_matches(flag: str, candidate: str) -> bool:
    return flag == candidate or flag.startswith(f"{candidate}:")


def _has_any_flag(flags: List[str], candidates: set[str]) -> bool:
    return any(_flag_matches(flag, candidate) for flag in flags for candidate in candidates)


def _is_blank_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _json_safe_value(value: Any) -> Tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        sanitized: Dict[str, Any] = {}
        for key, item in value.items():
            sanitized_item, item_changed = _json_safe_value(item)
            sanitized[key] = sanitized_item
            changed = changed or item_changed
        return sanitized, changed

    if isinstance(value, list):
        changed = False
        sanitized_list: List[Any] = []
        for item in value:
            sanitized_item, item_changed = _json_safe_value(item)
            sanitized_list.append(sanitized_item)
            changed = changed or item_changed
        return sanitized_list, changed

    if isinstance(value, tuple):
        sanitized_items, changed = _json_safe_value(list(value))
        return tuple(sanitized_items), changed

    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            return None, True
        return value, False

    return value, False


def _input_required_response(
    tool: str,
    mode: str,
    required: List[str],
    provided_keys: List[str],
) -> Dict[str, Any]:
    return {
        "tool": tool,
        "task": tool,
        "mode": mode,
        "status": "FAIL",
        "domain_verdict": "VOID",
        "governance_verdict": "VOID",
        "engine_status": "INPUT_REQUIRED",
        "confidence": "LOW",
        "error": f"Missing required parameters for mode '{mode}': {', '.join(required)}",
        "required": required,
        "provided_keys": provided_keys,
        "failure_flags": ["MISSING_REQUIRED_INPUT"],
        "allocation_signal": "INSUFFICIENT_DATA",
        "execution": {
            "recommended_mode": "draft_only",
            "human_confirmation_required": True,
        },
    }


def _runtime_error_response(tool: str, mode: str, error: str) -> Dict[str, Any]:
    return {
        "tool": tool,
        "task": tool,
        "mode": mode,
        "status": "FAIL",
        "domain_verdict": "VOID",
        "governance_verdict": "VOID",
        "engine_status": "ERROR",
        "confidence": "LOW",
        "error": error,
        "failure_flags": ["COMPUTATION_ERROR"],
        "allocation_signal": "INSUFFICIENT_DATA",
        "execution": {
            "recommended_mode": "pause",
            "human_confirmation_required": True,
        },
    }


def count_sign_changes(values: List[float]) -> int:
    previous_sign = 0
    changes = 0
    for value in values:
        if not math.isfinite(value) or abs(value) <= EPSILON:
            continue
        sign = 1 if value > 0 else -1
        if previous_sign != 0 and sign != previous_sign:
            changes += 1
        previous_sign = sign
    return changes


def build_cashflow_series(
    initial_investment: float, cash_flows: List[float], terminal_value: float = 0
) -> List[float]:
    series = [-abs(initial_investment), *cash_flows]
    if terminal_value and len(series) > 1:
        series[-1] += terminal_value
    return series


def derive_confidence_band(
    value: Optional[float], epistemic: str = "CLAIM", mode: str = "relative"
) -> Optional[List[float]]:
    if value is None or not math.isfinite(value):
        return None
    upper_epistemic = str(epistemic).upper()
    relative_width = (
        0.25
        if upper_epistemic == "HYPOTHESIS"
        else 0.15
        if upper_epistemic == "ESTIMATE"
        else 0.08
        if upper_epistemic == "PLAUSIBLE"
        else 0
    )
    if relative_width == 0:
        return None
    if mode == "absolute-nonnegative":
        delta = max(0.05, abs(value) * relative_width)
        return [round_value(max(0.0, value - delta), 6), round_value(value + delta, 6)]
    return [
        round_value(value * (1 - relative_width), 6),
        round_value(value * (1 + relative_width), 6),
    ]


def npv_from_series(cashflow_series: List[float], discount_rate: float) -> float:
    total = 0.0
    for index, cashflow in enumerate(cashflow_series):
        if index == 0:
            total += cashflow
        else:
            total += cashflow / pow(1 + discount_rate, index)
    return total


def present_value_breakdown(
    cashflow_series: List[float], discount_rate: float
) -> Dict[str, Any]:
    discounted = []
    for index, cashflow in enumerate(cashflow_series):
        if index == 0:
            discounted.append(cashflow)
        else:
            discounted.append(cashflow / pow(1 + discount_rate, index))

    pv_inflows = sum(value for value in discounted if value > 0)
    pv_outflows = sum(abs(value) for value in discounted if value < 0)
    return {
        "discounted_cashflows": [round_value(value, 6) for value in discounted],
        "pv_inflows": round_value(pv_inflows, 6),
        "pv_outflows": round_value(pv_outflows, 6),
    }


def validate_series(initial_investment: float, cash_flows: List[float]) -> List[str]:
    flags: List[str] = []
    if not math.isfinite(initial_investment) or initial_investment == 0:
        flags.append("INVALID_INITIAL_INVESTMENT")
    if (
        not isinstance(cash_flows, list)
        or len(cash_flows) == 0
        or any(not math.isfinite(value) for value in cash_flows)
    ):
        flags.append("INVALID_CASHFLOW_SERIES")
    return flags


def validate_rate(rate: float, invalid_flag: str) -> List[str]:
    if not math.isfinite(rate) or rate <= -1:
        return [invalid_flag]
    return []


def weakest_epistemic(items: List[dict], default_tag: str = "CLAIM") -> str:
    if not items:
        return default_tag
    weakest_index = len(EPISTEMIC_ORDER) - 1
    for item in items:
        reliability = str(item.get("reliability", "")).lower()
        candidate = str(
            item.get("tag")
            or item.get("epistemic")
            or RELIABILITY_TO_TAG.get(reliability, default_tag)
        ).upper()
        if candidate in EPISTEMIC_ORDER:
            weakest_index = min(weakest_index, EPISTEMIC_ORDER.index(candidate))
    return EPISTEMIC_ORDER[weakest_index]


def derive_verdict(flags: List[str], default_verdict: str = "SEAL", high_stress: bool = False, recommended: str = "SEAL") -> str:
    if recommended == "VOID" or _has_any_flag(flags, INVALID_FLAGS):
        return "VOID"
    if recommended == "SABAR" or high_stress:
        return "SABAR"
    if _has_any_flag(flags, HOLD_FLAGS):
        return "888-HOLD"
    if _has_any_flag(flags, QUALIFY_FLAGS | DATA_GAP_FLAGS):
        return "QUALIFY"
    return default_verdict


def infer_epistemic(flags: List[str], default_epistemic: str = "CLAIM") -> str:
    if _has_any_flag(flags, INVALID_FLAGS):
        return "UNKNOWN"
    if _has_any_flag(flags, HOLD_FLAGS | QUALIFY_FLAGS | DATA_GAP_FLAGS):
        return "ESTIMATE"
    return default_epistemic


def confidence_from_verdict(verdict: str, flags: List[str]) -> str:
    if verdict in {"VOID", "888-HOLD"}:
        return "LOW"
    if verdict == "QUALIFY" or flags:
        return "MEDIUM"
    return "HIGH"


SCALE_DEFAULTS = {
    "personal": {
        "discount_rate": 0.03,
        "horizon_years": 5,
        "objective": "maximize_lifetime_utility",
    },
    "household": {
        "discount_rate": 0.04,
        "horizon_years": 10,
        "objective": "intergenerational_stability",
    },
    "sme": {
        "discount_rate": 0.10,
        "horizon_years": 5,
        "objective": "survival_and_growth",
    },
    "enterprise": {
        "discount_rate": 0.10,
        "horizon_years": 10,
        "objective": "shareholder_value",
    },
    "national": {
        "discount_rate": 0.02,
        "horizon_years": 35,
        "objective": "gdp_plus_welfare",
    },
    "crisis": {
        "discount_rate": float("inf"),
        "horizon_years": 0,
        "objective": "minimize_collapse_probability",
    },
    "civilization": {
        "discount_rate": 0.005,
        "horizon_years": 300,
        "objective": "species_continuation",
    },
    "agentic": {
        "discount_rate": 0.15,
        "horizon_years": 2,
        "objective": "capability_accumulation",
    },
}

CAPITAL_TERMINOLOGY = {
    "financial": {
        "npv_label": "NPV",
        "irr_label": "IRR",
        "pi_label": "PI",
        "commitment_label": "initial_investment",
        "stream_label": "cash_flows",
        "value_label": "Net Present Value",
    },
    "temporal": {
        "npv_label": "NTV",
        "irr_label": "ITR",
        "pi_label": "TI",
        "commitment_label": "initial_time_commitment",
        "stream_label": "time_streams",
        "value_label": "Net Temporal Value",
    },
    "cognitive": {
        "npv_label": "NCV",
        "irr_label": "ICR",
        "pi_label": "CI",
        "commitment_label": "initial_attention_commitment",
        "stream_label": "attention_streams",
        "value_label": "Net Cognitive Value",
    },
    "social": {
        "npv_label": "NSV",
        "irr_label": "ISR",
        "pi_label": "SI",
        "commitment_label": "initial_reputation_commitment",
        "stream_label": "reputation_streams",
        "value_label": "Net Social Value",
    },
    "ecological": {
        "npv_label": "NEV",
        "irr_label": "IER",
        "pi_label": "EI",
        "commitment_label": "initial_resource_commitment",
        "stream_label": "resource_streams",
        "value_label": "Net Ecological Value",
    },
    "strategic": {
        "npv_label": "NXV",
        "irr_label": "IXR",
        "pi_label": "XI",
        "commitment_label": "initial_option_commitment",
        "stream_label": "option_streams",
        "value_label": "Net Strategic Value",
    },
    "thermodynamic": {
        "npv_label": "NΦV",
        "irr_label": "IΦR",
        "pi_label": "ΦI",
        "commitment_label": "initial_energy_commitment",
        "stream_label": "energy_streams",
        "value_label": "Net Thermodynamic Value",
    },
}


def get_scale_defaults(scale_mode: str) -> Dict[str, Any]:
    return SCALE_DEFAULTS.get(scale_mode, SCALE_DEFAULTS["enterprise"])


def get_capital_terminology(capital_type: str) -> Dict[str, str]:
    return CAPITAL_TERMINOLOGY.get(capital_type, CAPITAL_TERMINOLOGY["financial"])


def derive_allocation_signal(
    flags: List[str], primary: Dict[str, Any], tool: str, scale_mode: str = "enterprise"
) -> str:
    if _has_any_flag(flags, INVALID_FLAGS | DATA_GAP_FLAGS):
        return "INSUFFICIENT_DATA"

    scale = get_scale_defaults(scale_mode)

    if tool in {"wealth_coordination_equilibrium", "wealth_game_theory_solve"}:
        tragedy_risk = primary.get("tragedy_risk", 1.0)
        if _has_any_flag(flags, INVALID_FLAGS | DATA_GAP_FLAGS):
            return "INSUFFICIENT_DATA"
        if primary.get("in_core") is False or any("BLOCK" in f for f in flags):
            return "REJECT"
        if tragedy_risk > 0.5:
            return "REJECT"
        if tragedy_risk > 0.3:
            return "MARGINAL"
        return "ACCEPT"

    if tool == "wealth_npv_reward":
        npv = primary.get("npv")
        if npv is None:
            return "INSUFFICIENT_DATA"
        if npv > 0:
            return "ACCEPT"
        if npv < 0:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_pi_efficiency":
        pi = primary.get("pi")
        if pi is None:
            return "INSUFFICIENT_DATA"
        if pi > 1:
            return "ACCEPT"
        if pi < 1:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_irr_yield":
        irr = primary.get("irr")
        if irr is None:
            return "INSUFFICIENT_DATA"
        hurdle = (
            scale["discount_rate"] if scale["discount_rate"] != float("inf") else 0.10
        )
        if irr > hurdle:
            return "ACCEPT"
        if irr < hurdle:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_payback_time":
        payback = primary.get("payback_periods")
        if payback is None:
            return (
                "REJECT"
                if any(f == "NOT_RECOVERED" for f in flags)
                else "INSUFFICIENT_DATA"
            )
        return "ACCEPT"

    if tool == "wealth_dscr_leverage":
        dscr = primary.get("dscr")
        if dscr is None:
            return "INSUFFICIENT_DATA"
        if dscr >= 1.5:
            return "ACCEPT"
        if dscr >= 1.25:
            return "MARGINAL"
        return "REJECT"

    if tool == "wealth_growth_velocity":
        runway = primary.get("runway_months")
        if runway is not None and runway != math.inf and runway < 3:
            return "REJECT"
        return "ACCEPT"

    if tool == "wealth_cashflow_flow":
        net_monthly = primary.get("net_monthly")
        if net_monthly is not None and net_monthly < 0:
            runway = primary.get("runway_months")
            if runway is not None and runway != math.inf and runway < 3:
                return "REJECT"
            return "MARGINAL"
        return "ACCEPT"

    if tool == "wealth_score_kernel":
        r_adj = primary.get("r_adj", 0.1)
        m_score = primary.get("maruahScore", 0.5)
        if m_score < 0.6:
            return "REJECT"
        if r_adj > 0.15:
            return "REJECT"  # High risk/extractive
        if r_adj > 0.12 or m_score < 0.75:
            return "MARGINAL"
        return "ACCEPT"

    if tool in {"wealth_evoi_compute", "wealth_mind_evoi", "wealth_evoi_monte_carlo"}:
        drill = primary.get("drill_recommendation", "")
        if drill.startswith("PROCEED"):
            return "ACCEPT"
        if drill.startswith("DO_NOT_DRILL"):
            return "REJECT"
        if drill.startswith("HOLD") or drill.startswith("ACQUIRE_DATA"):
            return "MARGINAL"
        evoi_val = primary.get("evoi_musd", 0)
        if evoi_val > 0:
            return "ACCEPT"
        if evoi_val < 0:
            return "REJECT"
        return "MARGINAL"

    return "MARGINAL"


def measurement_validate_invariants(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    measurement_results: Optional[Dict[str, Any]] = None,
) -> List[str]:
    flags = []
    if measurement_results is None:
        return flags

    npv = measurement_results.get("npv")
    irr = measurement_results.get("irr")
    pi = measurement_results.get("pi")
    pv_inflows = measurement_results.get("pv_inflows")

    series = build_cashflow_series(initial_investment, cash_flows, terminal_value)
    sign_changes = count_sign_changes(series)

    if pi is not None and pv_inflows is not None:
        expected_pi = pv_inflows / abs(initial_investment)
        if abs(pi - expected_pi) > 0.001:
            flags.append("INVARIANT_VIOLATION")

    if npv is not None and pi is not None and sign_changes <= 1:
        if npv > 0 and pi <= 1:
            flags.append("INVARIANT_VIOLATION")
        if npv < 0 and pi >= 1:
            flags.append("INVARIANT_VIOLATION")

    if (
        npv is not None
        and irr is not None
        and discount_rate is not None
        and sign_changes <= 1
    ):
        if (npv > 0 and irr <= discount_rate) or (npv < 0 and irr >= discount_rate):
            flags.append("INVARIANT_VIOLATION")

    return flags


_policy_engine = PolicyEngine()


def create_envelope(
    tool: str,
    dimension: str,
    primary: Dict[str, Any],
    secondary: Optional[Dict[str, Any]] = None,
    flags: Optional[List[str]] = None,
    assumptions: Optional[List[str]] = None,
    epistemic: str = "CLAIM",
    verdict: Optional[str] = None,
    scale_mode: str = "enterprise",
    governance_args: Optional[Dict[str, Any]] = None,
    parent_hash: Optional[str] = None,
    witness: Optional[Any] = None,
) -> Dict[str, Any]:
    global LAST_RECEIPT_HASH
    flags = flags or []
    primary, primary_sanitized = _json_safe_value(primary)
    secondary, secondary_sanitized = _json_safe_value(secondary or {})
    governance_args, governance_sanitized = _json_safe_value(governance_args or {})
    if (primary_sanitized or secondary_sanitized or governance_sanitized) and "NON_FINITE_VALUE_REPLACED" not in flags:
        flags.append("NON_FINITE_VALUE_REPLACED")
    
    # 1. Harness Audit with Chaining
    final_parent_hash = parent_hash or LAST_RECEIPT_HASH
    engine = HarnessEngine()
    audit_res = engine.audit(tool, primary, flags, final_parent_hash)
    
    systemic_stress = audit_res.get("systemic_stress", 0.0)
    # Stress (0.7-0.9) or systemic instability forces 888-HOLD/QUALIFY
    is_high_stress = systemic_stress > 1.5 or any(h["stress"] >= 0.7 for h in audit_res["harness_status"].values())
    
    derived_governance = verdict or derive_verdict(flags, high_stress=is_high_stress, recommended=audit_res["recommended_verdict"])
    derived_allocation = derive_allocation_signal(flags, primary, tool, scale_mode)
    
    if is_high_stress and derived_allocation == "ACCEPT":
        derived_allocation = "MARGINAL" # Force downgraded allocation on high stress

    engine_status = (
        "ERROR"
        if derived_governance == "VOID" or audit_res["verdict"] == "FAIL"
        else "WARNING"
        if derived_governance in ("QUALIFY", "888-HOLD", "SABAR") or is_high_stress
        else "VALID"
    )
    derived_epistemic = infer_epistemic(flags, epistemic)
    
    if audit_res["verdict"] == "FAIL":
        derived_governance = "VOID"
        derived_allocation = "REJECT"
        engine_status = "ERROR"
        for viol in audit_res["violations"]:
            if viol not in flags:
                flags.append(viol)

    # Three-verdict semantics (Fix #2 — Sin of Headline Metric Seduction):
    #   verdict           = allocation_signal   → ACCEPT/REJECT/MARGINAL/INSUFFICIENT_DATA
    #                       The DECISION signal. What a decision-maker reads first.
    #   governance_verdict = SEAL/VOID/HOLD/QUALIFY
    #                       Was the computation constitutionally valid? SEAL ≠ investment approved.
    #   engine_status      = VALID/WARNING/ERROR
    #                       Did the math pipeline run cleanly?
    # A project can be SEAL (computation valid) + REJECT (don't fund it). These must never collapse.
    # 3. Build Envelope with Sovereign Metadata
    meta = engine.SOVEREIGN_METADATA.get(tool, {})
    
    # Namespace transparency (v2 Alias Layer)
    alias_of = None
    if tool in engine.V2_CANONICAL_MAP:
        alias_of = engine.V2_CANONICAL_MAP[tool]
        
    # Failure Doctrine Classification
    failure_tokens = (
        "ERROR",
        "UNAVAILABLE",
        "INVALID",
        "STALE",
        "FAILURE",
        "MISSING_REQUIRED_INPUT",
        "COMPUTATION_ERROR",
    )
    failure_flags = [f for f in flags if any(token in f for token in failure_tokens)]
    status = "PASS"
    next_safe_action = "Consult arifOS 888_JUDGE"

    if failure_flags or audit_res["verdict"] == "FAIL":
        status = "VOID" if any("INVALID" in f or "SCHEMA" in f for f in failure_flags) else "HOLD"
        next_safe_action = "Repair missing layer or verify inputs."
    elif derived_governance == "VOID":
        status = "VOID"
        next_safe_action = "Policy engine rejection. Do not allocate."
    elif derived_governance in ("888-HOLD", "SABAR"):
        status = "HOLD"
        next_safe_action = "Awaiting human confirmation via arifOS 888_JUDGE."
    elif derived_governance == "QUALIFY" or is_high_stress:
        status = "CAUTION"
        next_safe_action = "Proceed with manual verification."

    mode_map = {"PASS": "full", "CAUTION": "structured", "HOLD": "draft_only", "VOID": "pause"}

    # --- WEALTH G-Score Integration (Thermodynamic Governance) ---
    g_score_params = {**primary, "violations": flags, "scale_mode": scale_mode}
    if secondary:
        g_score_params.update(secondary)
    if governance_args:
        g_score_params.update(governance_args)
    
    g_data = get_g_score(g_score_params)
    if g_data.get("engine_error"):
        failure_flag = "G_SCORE_ENGINE_UNAVAILABLE"
        if failure_flag not in flags:
            flags.append(failure_flag)
        if failure_flag not in failure_flags:
            failure_flags.append(failure_flag)
        if status == "PASS":
            status = "HOLD"
            next_safe_action = "Restore WEALTH thermodynamic dependencies before allocation."
        if engine_status == "VALID":
            engine_status = "WARNING"
        
    envelope = {
        "mcp": "WEALTH",
        "task": tool,
        "status": status,
        "domain_verdict": derived_governance,
        "g_score": g_data["g_score"],
        "entropy_s": g_data["entropy_s"],
        "qdf": get_qdf_version(),
        "witness": witness.to_dict() if witness is not None else {
            "human": governance_args.get("human_confirmed", False) if governance_args else False,
            "ai": True,
            "earth": True
        },
        "shadow": len(audit_res.get("violations", [])) > 0 or len(audit_res.get("holds", [])) > 0,
        "kappa_r": compute_kappa_r(primary.get("rasa", 0.9), primary.get("truth_consistency", 0.95)),
        "psi_le": compute_psi_le(g_data["entropy_s"], systemic_stress),
        "confidence": "LOW" if failure_flags or is_high_stress else "HIGH",
        "epistemic": {
            "class": derived_epistemic,
            "integrity_score": round(1.0 - (systemic_stress / 10.0), 2) if not failure_flags else 0.1,
        },
        "authority": {
            "level": "domain_expert",
            "boundary": "Economic thermodynamics and capital allocation.",
        },
        "readiness": {
            "human": "UNKNOWN",
            "machine": "HEALTHY" if status == "PASS" else "DEGRADED",
        },
        "risk": {
            "level": "GREEN" if status == "PASS" else "RED" if status == "VOID" else "AMBER",
            "economic": "LOW" if derived_allocation == "ACCEPT" else "HIGH",
            "constitutional": "LOW",
            "coupled": "UNKNOWN",
            "g_score": g_data["g_score"],
            "delta_s": g_data["delta_s"],
            "lyapunov_lambda": g_data["lyapunov_lambda"],
            "verdict": g_data["verdict"],
            "regime": g_data["regime"]
        },
        "execution": {
            "recommended_mode": mode_map.get(status, "pause"),
            "human_confirmation_required": status != "PASS" or dimension == "Allocation",
            "next_safe_action": next_safe_action,
        },
        "primary_metrics": primary,
        # Historical namespace map for interpreting older receipts and migration-era records.
        "primary_result": primary,
        "governance_verdict": derived_governance,
        "allocation_signal": derived_allocation,
        "engine_status": engine_status,
        "economic_signal": primary.get("economic_signal"),
        "execution_verdict": primary.get("execution_verdict"),
        "secondary_metrics": {
            "display_name": meta.get("display", tool),
            "family": meta.get("family", dimension.upper()),
            "allocation_signal": derived_allocation,
            "engine_status": engine_status,
            "harness_audit": audit_res,
            "secondary_metrics_raw": secondary or {},
            **(secondary or {}),
        },
        "assumptions": assumptions or [],
        "failure_flags": failure_flags,
        "reversibility": "REVERSIBLE" if "read" in tool or "check" in tool else "UNKNOWN",
        "final_authority": "Arif",
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "epoch": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    if "dual_domain" in meta:
        envelope["dual_domain"] = meta["dual_domain"]
    if meta.get("primary"):
        envelope["primary_entrypoint"] = True

    # === Constitutional Governance Layer ===
    # Governance tools are exempt from recursive envelope governance so they can audit bad proposals
    is_governance_tool = tool in {"wealth_check_floors", "wealth_policy_audit"}
    if (
        scale_mode in {"national", "crisis", "civilization", "agentic"}
        and not is_governance_tool
    ):
        gov_args = governance_args or {}
        floor_result = _evaluate_floors(
            {**gov_args, "epistemic": derived_epistemic, "scale_mode": scale_mode}
        )
        # Merge floor outcomes
        if floor_result["verdict"] == "VOID":
            envelope["governance_verdict"] = "VOID"
            envelope["domain_verdict"] = "VOID"
            envelope["allocation_signal"] = "REJECT"
            envelope["engine_status"] = "ERROR"
        elif floor_result["verdict"] == "HOLD":
            envelope["governance_verdict"] = "888-HOLD"
            envelope["domain_verdict"] = "888-HOLD"
            envelope["allocation_signal"] = "INSUFFICIENT_DATA"
            envelope["engine_status"] = "WARNING"

        envelope["floor_check"] = {
            "verdict": floor_result.get("verdict", "SEAL"),
            "violations": floor_result.get("violations", []),
            "holds": floor_result.get("holds", []),
            "warnings": floor_result.get("warnings", []),
        }

        # Policy constraints (if audit data provided)
        if gov_args:
            policy_result = _policy_engine.evaluate(gov_args, scale_mode)
            if not policy_result["policy_pass"]:
                envelope["governance_verdict"] = "VOID"
                envelope["domain_verdict"] = "VOID"
                envelope["allocation_signal"] = "REJECT"
                envelope["engine_status"] = "ERROR"
            envelope["policy_audit"] = policy_result

        # Vault all high-scale decisions
        _vault_append(
            {
                "tool": tool,
                "scale_mode": scale_mode,
                "allocation_signal": envelope["allocation_signal"],
                "governance_verdict": envelope["governance_verdict"],
                "floor_check": envelope.get("floor_check"),
                "policy_audit": envelope.get("policy_audit"),
            }
        )

    envelope["secondary_metrics"]["allocation_signal"] = envelope["allocation_signal"]
    envelope["secondary_metrics"]["engine_status"] = envelope["engine_status"]

    # 4. Update Global Identity Chain after governance mutations.
    envelope, _ = _json_safe_value(envelope)
    receipt_blob = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    receipt_hash = hashlib.sha256(receipt_blob.encode()).hexdigest()
    envelope["receipt_hash"] = receipt_hash
    LAST_RECEIPT_HASH = receipt_hash

    return envelope


def measurement_npv(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
) -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE"),
    ]
    assumptions = [
        "NPV is the primary accept/reject metric.",
        "Discount rate and cash flow periodicity are aligned.",
    ]
    if flags:
        return {
            "npv": None,
            "eaa": None,
            "pv_inflows": None,
            "pv_outflows": None,
            "discounted_cashflows": [],
            "period_count": len(cash_flows) if isinstance(cash_flows, list) else 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    series = build_cashflow_series(initial_investment, cash_flows, terminal_value)
    breakdown = present_value_breakdown(series, discount_rate)
    npv = npv_from_series(series, discount_rate)
    periods = len(cash_flows)
    if periods == 0:
        eaa = None
    elif abs(discount_rate) <= EPSILON:
        eaa = npv / periods
    else:
        eaa = (npv * discount_rate) / (1 - pow(1 + discount_rate, -periods))
    return {
        "npv": round_value(npv, 6),
        "eaa": round_value(eaa, 6),
        "pv_inflows": breakdown["pv_inflows"],
        "pv_outflows": breakdown["pv_outflows"],
        "discounted_cashflows": breakdown["discounted_cashflows"],
        "period_count": periods,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "input_epistemic": str(input_epistemic).upper(),
        "confidence_band": derive_confidence_band(npv, input_epistemic),
        "flags": flags,
    }


def bracket_roots(
    npv_fn, lower: float = -0.9999, upper: float = 10.0, steps: int = 4096
) -> List[List[float]]:
    brackets: List[List[float]] = []
    step = (upper - lower) / steps
    previous_rate = lower
    previous_value = npv_fn(previous_rate)
    for index in range(1, steps + 1):
        rate = lower + step * index
        value = npv_fn(rate)
        if not math.isfinite(previous_value) or not math.isfinite(value):
            previous_rate = rate
            previous_value = value
            continue
        if abs(previous_value) <= EPSILON:
            brackets.append([previous_rate, previous_rate])
        elif previous_value * value < 0:
            brackets.append([previous_rate, rate])
        elif abs(value) <= EPSILON:
            brackets.append([rate, rate])
        previous_rate = rate
        previous_value = value
    return brackets


def bisect_root(npv_fn, lower: float, upper: float, iterations: int = 200) -> float:
    if lower == upper:
        return lower
    left = lower
    right = upper
    left_value = npv_fn(left)
    for _ in range(iterations):
        midpoint = (left + right) / 2
        midpoint_value = npv_fn(midpoint)
        if not math.isfinite(midpoint_value):
            break
        if abs(midpoint_value) <= EPSILON:
            return midpoint
        if left_value * midpoint_value <= 0:
            right = midpoint
        else:
            left = midpoint
            left_value = midpoint_value
        if abs(right - left) <= EPSILON:
            return (left + right) / 2
    return (left + right) / 2


def measurement_irr(
    initial_investment: float,
    cash_flows: List[float],
    finance_rate: float = 0.1,
    reinvestment_rate: float = 0.1,
    period_unit: str = "annual",
) -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(finance_rate, "INVALID_FINANCE_RATE"),
        *validate_rate(reinvestment_rate, "INVALID_REINVESTMENT_RATE"),
    ]
    assumptions = [
        "NPV remains the primary ranking metric for mutually exclusive projects.",
        "MIRR is preferred when reinvestment should not equal IRR.",
    ]
    if flags:
        return {
            "irr": None,
            "mirr": None,
            "sign_changes": 0,
            "period_count": len(cash_flows) if isinstance(cash_flows, list) else 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    series = build_cashflow_series(initial_investment, cash_flows)
    sign_changes = count_sign_changes(series)
    if sign_changes > 1:
        flags.extend(["NON_NORMAL_FLOWS", "MULTIPLE_IRR_POSSIBLE"])

    def npv_fn(rate):
        return npv_from_series(series, rate)

    brackets = bracket_roots(npv_fn)
    roots = {
        round_value(bisect_root(npv_fn, lower, upper), 10) for lower, upper in brackets
    }
    irr = next(iter(roots)) if len(roots) == 1 else None
    if len(roots) == 0:
        flags.append("IRR_NOT_FOUND")

    period_count = len(series) - 1
    pv_negative = 0.0
    fv_positive = 0.0
    for index, cashflow in enumerate(series):
        if cashflow < 0:
            pv_negative += cashflow / pow(1 + finance_rate, index)
        elif cashflow > 0:
            fv_positive += cashflow * pow(1 + reinvestment_rate, period_count - index)
    mirr = None
    if pv_negative < 0 and fv_positive > 0 and period_count > 0:
        mirr = pow(fv_positive / abs(pv_negative), 1 / period_count) - 1

    return {
        "irr": round_value(irr, 8) if irr is not None else None,
        "mirr": round_value(mirr, 8) if mirr is not None else None,
        "sign_changes": sign_changes,
        "period_count": period_count,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_pi(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
) -> Dict[str, Any]:
    npv_measure = measurement_npv(
        initial_investment, cash_flows, discount_rate, terminal_value
    )
    flags = list(npv_measure["flags"])
    if (
        count_sign_changes(
            build_cashflow_series(initial_investment, cash_flows, terminal_value)
        )
        > 1
    ):
        flags.append("NON_NORMAL_FLOWS")
    pi = (
        None
        if npv_measure["pv_inflows"] is None
        else npv_measure["pv_inflows"] / abs(initial_investment)
    )
    return {
        "pi": round_value(pi, 8) if pi is not None else None,
        "pv_inflows": npv_measure["pv_inflows"],
        "assumptions": [
            "Profitability Index is for ranking under capital rationing.",
            "PI does not override NPV for mutually exclusive decisions.",
        ],
        "flags": flags,
    }


def measurement_emv(scenarios: List[dict]) -> Dict[str, Any]:
    flags: List[str] = []
    assumptions = [
        "EMV should be paired with downside probability and scenario dispersion.",
        "Scenario probabilities should sum to 1.0.",
    ]
    if not isinstance(scenarios, list) or not scenarios:
        flags.append("INVALID_SCENARIOS")
        return {
            "emv": None,
            "total_probability": None,
            "downside_probability": None,
            "worst_outcome": None,
            "best_outcome": None,
            "variance": None,
            "assumptions": assumptions,
            "flags": flags,
        }

    for scenario in scenarios:
        if (
            scenario is None
            or not math.isfinite(scenario.get("probability"))
            or not math.isfinite(scenario.get("outcome"))
        ):
            flags.append("INVALID_SCENARIO")
            return {
                "emv": None,
                "total_probability": None,
                "downside_probability": None,
                "worst_outcome": None,
                "best_outcome": None,
                "variance": None,
                "assumptions": assumptions,
                "flags": flags,
            }

    total_probability = sum(scenario["probability"] for scenario in scenarios)
    if abs(total_probability - 1.0) > 1e-6:
        flags.append("PROBABILITY_MASS_INVALID")

    emv = sum(scenario["probability"] * scenario["outcome"] for scenario in scenarios)
    downside_probability = sum(
        scenario["probability"] for scenario in scenarios if scenario["outcome"] < 0
    )
    variance = sum(
        scenario["probability"] * pow(scenario["outcome"] - emv, 2)
        for scenario in scenarios
    )
    return {
        "emv": round_value(emv, 6),
        "total_probability": round_value(total_probability, 6),
        "downside_probability": round_value(downside_probability, 6),
        "worst_outcome": round_value(
            min(scenario["outcome"] for scenario in scenarios), 6
        ),
        "best_outcome": round_value(
            max(scenario["outcome"] for scenario in scenarios), 6
        ),
        "variance": round_value(variance, 6),
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_payback(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0,
    period_unit: str = "annual",
) -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE"),
    ]
    assumptions = ["Payback should only support, not replace, NPV."]
    if flags:
        return {
            "payback_periods": None,
            "discounted": discount_rate > 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    remaining = abs(initial_investment)
    payback_periods = None
    for index, raw_cashflow in enumerate(cash_flows):
        adjusted_cashflow = (
            raw_cashflow / pow(1 + discount_rate, index + 1)
            if discount_rate > 0
            else raw_cashflow
        )
        if adjusted_cashflow <= 0:
            continue
        if remaining > adjusted_cashflow:
            remaining -= adjusted_cashflow
            continue
        payback_periods = index + (remaining / adjusted_cashflow) + 1e-12
        remaining = 0
        break
    if remaining > EPSILON:
        flags.append("NOT_RECOVERED")
    return {
        "payback_periods": round_value(payback_periods, 6)
        if payback_periods is not None
        else None,
        "discounted": discount_rate > 0,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_dscr(
    cfads: Optional[float],
    debt_service: Optional[float],
    ebitda: Optional[float],
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
) -> Dict[str, Any]:
    flags: List[str] = []
    numerator = cfads if cfads is not None else ebitda
    denominator = (
        debt_service if debt_service is not None else principal + interest + leases
    )
    if numerator is None or not math.isfinite(numerator):
        flags.append("INVALID_CFADS")
    if denominator is None or not math.isfinite(denominator) or denominator <= 0:
        flags.append("INVALID_DEBT_SERVICE")
    if cfads is None and ebitda is not None:
        flags.append("EBITDA_PROXY_USED")

    dscr = (
        None
        if any(flag in INVALID_FLAGS for flag in flags)
        else numerator / denominator
    )
    if dscr is not None and dscr < 1.0:
        flags.append("LEVERAGE_DEFAULT")
    elif dscr is not None and dscr < 1.25:
        flags.append("LEVERAGE_CRITICAL")
    return {
        "dscr": round_value(dscr, 6) if dscr is not None else None,
        "basis": "CFADS" if cfads is not None else "EBITDA",
        "period_unit": period_unit,
        "assumptions": [
            "DSCR should use CFADS when available.",
            "Minimum covenant floor defaults to 1.25x.",
        ],
        "input_epistemic": str(input_epistemic).upper(),
        "confidence_band": None
        if dscr is None
        else derive_confidence_band(dscr, input_epistemic, "absolute-nonnegative"),
        "flags": flags,
    }


def capitalx(base_rate: float, signals: Dict[str, float]) -> Dict[str, Any]:
    flags: List[str] = []
    if not math.isfinite(base_rate) or base_rate < 0:
        flags.append("INVALID_BASE_RATE")

    d_s = signals.get("dS", 0.0)
    peace2 = signals.get("peace2", 1.0)
    maruah = signals.get("maruahScore", 0.5)
    trust = signals.get("trustIndex", 0.5)
    delta_civ = signals.get("deltaCiv", 0.0)

    entropy_penalty = max(0.0, d_s * 0.5)
    peace_discount = min(0.02, max(0.0, (peace2 - 1.0) * 0.05))
    maruah_discount = min(0.03, max(0.0, (maruah - 0.5) * 0.06))
    trust_discount = min(0.02, max(0.0, (trust - 0.5) * 0.04))
    civ_discount = min(0.02, max(0.0, delta_civ * 0.10))

    r_adj = max(
        0.0,
        round_value(
            base_rate
            + entropy_penalty
            - peace_discount
            - maruah_discount
            - trust_discount
            - civ_discount,
            6,
        )
        or 0.0,
    )
    if d_s > 0.3:
        flags.append("HIGH_ENTROPY_SIGNAL")
    if maruah < 0.6:
        flags.append("SOVEREIGN_DIGNITY_LOW")

    uncertainty_radius = round_value(0.01 + d_s * 0.02, 6) or 0.01
    return {
        "base_rate": round_value(base_rate, 6),
        "adjusted_rate": r_adj,
        "r_adj": r_adj,
        "adjustments": {
            "entropy_penalty": round_value(entropy_penalty, 6),
            "peace_discount": round_value(peace_discount, 6),
            "maruah_discount": round_value(maruah_discount, 6),
            "trust_discount": round_value(trust_discount, 6),
            "civ_discount": round_value(civ_discount, 6),
        },
        "uncertainty_band": [
            max(0.0, round_value(r_adj - uncertainty_radius, 6) or 0.0),
            round_value(r_adj + uncertainty_radius, 6),
        ],
        "integrity_flags": flags,
        "assumptions": [
            "CapitalX pricing is an estimate layered on top of the base rate.",
            "If entropy rises, r_adj must not decrease.",
        ],
    }


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_npv_reward)
def npv_reward(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute NPV, Terminal Value, and EAA. [Reward Dimension]"""
    measurement = measurement_npv(
        initial_investment,
        cash_flows,
        discount_rate,
        terminal_value,
        period_unit,
        input_epistemic,
    )
    return create_envelope(
        "wealth_npv_reward",
        "Reward",
        {"npv": measurement["npv"]},
        {
            "eaa": measurement["eaa"],
            "pv_inflows": measurement["pv_inflows"],
            "pv_outflows": measurement["pv_outflows"],
            "period_count": measurement["period_count"],
            "period_unit": measurement["period_unit"],
            "confidence_band": measurement["confidence_band"],
        },
        measurement["flags"],
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_irr_yield)
def irr_yield(
    initial_investment: float,
    cash_flows: List[float],
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
    period_unit: str = "annual",
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute IRR and MIRR (Potential). [Energy Dimension]"""
    measurement = measurement_irr(
        initial_investment, cash_flows, finance_rate, reinvestment_rate, period_unit
    )
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        0,
        {
            "npv": npv_from_series(
                build_cashflow_series(initial_investment, cash_flows), discount_rate
            ),
            "irr": measurement["irr"],
        },
    )
    all_flags = list(dict.fromkeys([*measurement["flags"], *invariant_flags]))
    return create_envelope(
        "wealth_irr_yield",
        "Energy",
        {"irr": measurement["irr"]},
        {
            "mirr": measurement["mirr"],
            "sign_changes": measurement["sign_changes"],
            "period_count": measurement["period_count"],
            "period_unit": measurement["period_unit"],
        },
        all_flags,
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_pi_efficiency)
def pi_efficiency(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Profitability Index (Concentration). [Energy Dimension]"""
    measurement = measurement_pi(
        initial_investment, cash_flows, discount_rate, terminal_value
    )
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        terminal_value,
        {"pi": measurement["pi"], "pv_inflows": measurement["pv_inflows"]},
    )
    all_flags = list(dict.fromkeys([*measurement["flags"], *invariant_flags]))
    ranking_signal = (
        "EFFICIENT"
        if measurement["pi"] is not None and measurement["pi"] >= 1
        else "EXTRACTIVE"
    )
    return create_envelope(
        "wealth_pi_efficiency",
        "Energy",
        {"pi": measurement["pi"]},
        {"ranking_signal": ranking_signal},
        all_flags,
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_emv_risk)
def emv_risk(scenarios: List[dict], scale_mode: str = "enterprise") -> Any:
    """Compute Expected Monetary Value (Probability Density). [Entropy Dimension]"""
    measurement = measurement_emv(scenarios)
    return create_envelope(
        "wealth_emv_risk",
        "Entropy",
        {"emv": measurement["emv"]},
        {
            "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
            "total_probability": measurement["total_probability"],
            "downside_probability": measurement["downside_probability"],
            "variance": measurement["variance"],
            "worst_outcome": measurement["worst_outcome"],
            "best_outcome": measurement["best_outcome"],
        },
        measurement["flags"],
        measurement["assumptions"],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_audit_entropy)
def audit_entropy(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Audit project cash flows for noise and multiple IRRs. [Entropy Dimension]"""
    irr_measure = measurement_irr(
        initial_investment, cash_flows, discount_rate, discount_rate
    )
    npv_measure = measurement_npv(initial_investment, cash_flows, discount_rate)
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        0,
        {"npv": npv_measure["npv"], "irr": irr_measure["irr"]},
    )
    all_flags = list(dict.fromkeys([*irr_measure["flags"], *invariant_flags]))
    sensitivity = []
    for multiplier in [0.8, 0.9, 1.0, 1.1, 1.2]:
        sweep_npv = measurement_npv(
            initial_investment, cash_flows, discount_rate * multiplier
        )
        sensitivity.append({"multiplier": multiplier, "npv": sweep_npv["npv"]})
    return create_envelope(
        "wealth_audit_entropy",
        "Entropy",
        {"sign_changes": irr_measure["sign_changes"]},
        {"sensitivity_sweep": sensitivity},
        all_flags,
        irr_measure["assumptions"],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_dscr_leverage)
def dscr_leverage(
    ebitda: Optional[float] = None,
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    cfads: Optional[float] = None,
    debt_service: Optional[float] = None,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Debt Service Coverage Ratio (Structural Load). [Survival Dimension]"""
    measurement = measurement_dscr(
        cfads,
        debt_service,
        ebitda,
        principal,
        interest,
        leases,
        period_unit,
        input_epistemic,
    )
    return create_envelope(
        "wealth_dscr_leverage",
        "Survival",
        {"dscr": measurement["dscr"]},
        {
            "basis": measurement["basis"],
            "period_unit": measurement["period_unit"],
            "confidence_band": measurement["confidence_band"],
        },
        measurement["flags"],
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_payback_time)
def payback_time(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0,
    period_unit: str = "annual",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Payback Period (Recovery Velocity). [Time Dimension]"""
    measurement = measurement_payback(
        initial_investment, cash_flows, discount_rate, period_unit
    )
    return create_envelope(
        "wealth_payback_time",
        "Time",
        {"payback_periods": measurement["payback_periods"]},
        {
            "period_unit": measurement["period_unit"],
            "discounted": measurement["discounted"],
        },
        measurement["flags"],
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_growth_velocity)
def growth_velocity(
    principal: float,
    rate: float,
    years: int,
    annual_contribution: float = 0,
    monthly_burn: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Compound Growth and Runway. [Velocity Dimension]"""
    has_input = any(
        (
            principal not in (None, 0),
            rate not in (None, 0),
            years not in (None, 0),
            annual_contribution not in (None, 0),
            monthly_burn not in (None, 0),
        )
    )
    total = principal
    for _ in range(years):
        total = total * (1 + rate) + annual_contribution
    final_value = round_value(total, 2)
    low = round_value(final_value * 0.88, 2)
    high = round_value(final_value * 1.12, 2)
    net_monthly = -monthly_burn
    flags: List[str] = ["NO_INPUT_BASELINE"] if not has_input else []
    if monthly_burn <= 0:
        runway_months = None
        flags.append("RUNWAY_UNBOUNDED")
    else:
        runway_months = round_value(principal / monthly_burn, 1)
        if runway_months is not None and runway_months < 3:
            flags.append("RUNWAY_CRITICAL")
    return create_envelope(
        "wealth_growth_velocity",
        "Velocity",
        {"growth_forecast": {"low": low, "mid": final_value, "high": high}},
        {
            "runway_months": runway_months,
            "final_value": final_value,
            "net_monthly": net_monthly,
        },
        flags,
        ["Forward projections remain ESTIMATE by design."],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_networth_state)
def networth_state(
    assets: Optional[List[dict]] = None,
    liabilities: Optional[List[dict]] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute portfolio balance sheet (Accumulated Mass). [Mass Dimension]"""
    assets = assets or []
    liabilities = liabilities or []
    asset_value = sum(
        asset.get("value", 0)
        for asset in assets
        if math.isfinite(asset.get("value", 0))
    )
    liability_value = sum(
        liability.get("outstanding", liability.get("principal", 0))
        for liability in liabilities
        if math.isfinite(liability.get("outstanding", liability.get("principal", 0)))
    )
    epistemic = weakest_epistemic([*assets, *liabilities], "UNKNOWN")
    nw_flags = ["NO_INPUT_BASELINE"] if not assets and not liabilities else []
    return create_envelope(
        "wealth_networth_state",
        "Mass",
        {
            "net_worth": round_value(asset_value - liability_value, 2),
            "assets": round_value(asset_value, 2),
            "liabilities": round_value(liability_value, 2),
            "tag": epistemic,
        },
        {},
        nw_flags,
        [],
        epistemic=epistemic,
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_cashflow_flow)
def cashflow_flow(
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute metabolic liquidity (Flow Dimension). [Flow Dimension]"""
    income = [item for item in (income or []) if item.get("active", True)]
    expenses = [item for item in (expenses or []) if item.get("active", True)]
    has_input = bool(income or expenses) or liquid_assets not in (None, 0)
    total_income = sum(
        item.get("monthly_amount", 0)
        for item in income
        if math.isfinite(item.get("monthly_amount", 0))
    )
    total_expenses = sum(
        item.get("monthly_amount", 0)
        for item in expenses
        if math.isfinite(item.get("monthly_amount", 0))
    )
    net_monthly = total_income - total_expenses
    burn_rate = max(0.0, -net_monthly)
    flags: List[str] = ["NO_INPUT_BASELINE"] if not has_input else []
    if burn_rate == 0:
        runway_months = None
        flags.append("RUNWAY_UNBOUNDED")
    else:
        runway_months = round_value(liquid_assets / burn_rate, 1)
        if runway_months is not None and runway_months < 3:
            flags.append("RUNWAY_CRITICAL")
    epistemic = weakest_epistemic([*income, *expenses], "UNKNOWN")
    return create_envelope(
        "wealth_cashflow_flow",
        "Flow",
        {
            "monthly_income": round_value(total_income, 2),
            "monthly_expenses": round_value(total_expenses, 2),
            "net_monthly": round_value(net_monthly, 2),
            "runway_months": runway_months,
            "burn_rate": round_value(burn_rate, 2),
            "tag": epistemic,
        },
        {"period_unit": "monthly"},
        flags,
        [],
        epistemic=epistemic,
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_score_kernel)
def wealth_score_kernel(
    d_s: float,
    peace2: float,
    maruah_score: float,
    base_rate: float,
    trust_index: float = 0.5,
    delta_civ: float = 0.0,
    wealth_signals: Optional[dict] = None,
    prospects: Optional[List[dict]] = None,
    extractive_signals: Optional[dict] = None,
    compare: bool = False,
    scale_mode: str = "enterprise",
    task_definition: str = "",
    irreversible: bool = False,
) -> Any:
    """Final Sovereign Allocation Verdict. [Allocation Dimension]

    Constitutional Gate (F1-F13) + Epistemic Gate (Schema + Correlation).
    """
    epistemic_flags = []
    integrity_score = 1.0
    correlation_risk = 0.0
    epistemic_tag = "ESTIMATE"

    if EPISTEMIC_AVAILABLE and prospects:
        validator = SchemaValidator()
        guard = CorrelationGuard()

        schema_res = validator.validate_portfolio(prospects)
        integrity_score = schema_res.get("integrity_score", 1.0)
        epistemic_flags.extend(schema_res.get("flags", []))

        corr_res = guard.check_portfolio(prospects)
        correlation_risk = corr_res.get("correlation_risk", 0.0)
        epistemic_flags.extend(corr_res.get("flags", []))

        if integrity_score < 0.3:
            epistemic_flags.append("EPISTEMIC_FAILURE")
        if correlation_risk > 0.5:
            epistemic_flags.append("SYSTEMIC_CORRELATION_RISK")

    # --- 888 Harness Gate ---
    h_engine = HarnessEngine()
    pre_audit = h_engine.audit(
        "wealth_score_kernel",
        {"maruahScore": maruah_score, "base_rate": base_rate},
        epistemic_flags
    )
    if pre_audit["verdict"] == "FAIL":
        return create_envelope(
            "wealth_score_kernel",
            "Allocation",
            {
                "blocked_by_harness": True,
                "harness_verdict": "FAIL",
                "integrity_score": integrity_score,
                "correlation_risk": correlation_risk,
            },
            {"harness_detail": pre_audit},
            [*epistemic_flags, *pre_audit["violations"]],
            ["Allocation blocked by harness-snap (Constraint Violation)."],
            epistemic="VOID",
            verdict="VOID",
            scale_mode=scale_mode,
        )

    if not GOVERNANCE_AVAILABLE:
        pass
    else:
        floor_result = check_floors(
            {
                "reversible": not irreversible,
                "human_confirmed": False,
                "epistemic": epistemic_tag,
                "ai_is_deciding": True,
                "floor_override": False,
                "peace2": peace2,
                "maruah_score": maruah_score,
                "integrity_score": integrity_score,
                "correlation_risk": correlation_risk,
                "operation_type": "ALLOCATION",
                "scale_mode": scale_mode,
                "task_definition": task_definition,
                "critical": irreversible,
            }
        )
        if (floor_result.get("verdict") in ("HOLD", "VOID")) or (
            "EPISTEMIC_FAILURE" in epistemic_flags
        ):
            gov_verdict = (
                "888-HOLD" if floor_result.get("verdict") == "HOLD" else "VOID"
            )
            if "EPISTEMIC_FAILURE" in epistemic_flags:
                gov_verdict = "VOID"

            return create_envelope(
                "wealth_score_kernel",
                "Allocation",
                {
                    "blocked_by_governance": True,
                    "verdict": gov_verdict,
                    "integrity_score": integrity_score,
                    "correlation_risk": correlation_risk,
                },
                {
                    "floor_violations": floor_result.get("violations", []),
                    "epistemic_violations": epistemic_flags,
                },
                [*floor_result.get("violations", []), *epistemic_flags],
                ["Allocation blocked by constitutional or epistemic gate."],
                epistemic=epistemic_tag,
                verdict=gov_verdict,
                scale_mode=scale_mode,
            )

    wealth_payload = {
        "dS": d_s,
        "peace2": peace2,
        "maruahScore": maruah_score,
        "tag": "ESTIMATE",
    }

    # 888 Epistemic Gate
    if EPISTEMIC_AVAILABLE and prospects:
        validator = SchemaValidator()
        v_res = validator.validate_portfolio(prospects)
        if not v_res.get("portfolio_valid", True):
            return create_envelope(
                "wealth_score_kernel",
                "Allocation",
                {"error": "EPISTEMIC_HOLD", "reason": v_res.get("status")},
                {},
                ["888_HOLD", "EPISTEMIC_VIOLATION"],
                [
                    "Epistemic validation failed. Scalar volumetrics detected or integrity low."
                ],
                epistemic="VOID",
                verdict="VOID",
                scale_mode=scale_mode,
            )

        guard = CorrelationGuard()
        g_res = guard.check_portfolio(prospects)
        if g_res.action == "HOLD":
            return create_envelope(
                "wealth_score_kernel",
                "Allocation",
                {"error": "CORRELATION_HOLD", "systemic_risk": True},
                {},
                ["888_HOLD", "SYSTEMIC_RISK"],
                ["Systemic risk detected. Models are too correlated."],
                epistemic="VOID",
                verdict="VOID",
                scale_mode=scale_mode,
            )

    if wealth_signals:
        wealth_payload.update(wealth_signals)

    flags: List[str] = [*epistemic_flags]
    if d_s > 0.3:
        flags.append("HIGH_ENTROPY_SIGNAL")
    if maruah_score < 0.6:
        flags.append("SOVEREIGN_DIGNITY_LOW")

    wealth_result = capitalx(base_rate, wealth_payload)

    if compare:
        extractive_result = capitalx(base_rate, extractive_signals or {})
        comparison = {
            "base_rate": wealth_result["base_rate"],
            "wealth_r_adj": wealth_result["r_adj"],
            "extractive_r_adj": extractive_result["r_adj"],
            "advantage_bps": round(
                (extractive_result["r_adj"] - wealth_result["r_adj"]) * 10000
            ),
            "integrity_score": integrity_score,
            "correlation_risk": correlation_risk,
        }
        return create_envelope(
            "wealth_score_kernel",
            "Allocation",
            comparison,
            {},
            [
                *flags,
                *(wealth_result.get("integrity_flags", [])),
                *(extractive_result.get("integrity_flags", [])),
            ],
            ["CapitalX remains an estimate until delta_bps is proven."],
            epistemic="ESTIMATE",
            scale_mode=scale_mode,
        )

    # Merge results
    final_primary = {**wealth_result}
    final_primary.update(
        {"integrity_score": integrity_score, "correlation_risk": correlation_risk}
    )

    return create_envelope(
        "wealth_score_kernel",
        "Allocation",
        final_primary,
        {},
        [*flags, *(wealth_result.get("integrity_flags", []))],
        wealth_result.get("assumptions", []),
        epistemic=epistemic_tag,
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_personal_decision)
def personal_decision(
    alternatives: List[dict],
    constraints: dict,
    values: Optional[dict] = None,
    scale_mode: str = "personal",
) -> Any:
    """Rank personal alternatives under constraints. [Personal Dimension]"""
    values = values or {}
    ranked = []
    flags = []
    for alt in alternatives:
        cost = alt.get("cost", 0)
        time = alt.get("time_hours", 0)
        utility = alt.get("expected_utility", 0)
        weight_money = values.get("weight_money", 0.33)
        weight_time = values.get("weight_time", 0.33)
        weight_utility = values.get("weight_utility", 0.34)
        budget = constraints.get("budget", math.inf)
        time_budget = constraints.get("time_budget", math.inf)
        score = (
            weight_money * (-cost / max(budget, 1))
            + weight_time * (-time / max(time_budget, 1))
            + weight_utility * utility
        )
        feasible = cost <= budget and time <= time_budget
        ranked.append(
            {
                "name": alt.get("name"),
                "score": round_value(score, 6),
                "feasible": feasible,
            }
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)
    if not any(r["feasible"] for r in ranked):
        flags.append("NO_FEASIBLE_ALTERNATIVE")
    return create_envelope(
        "wealth_personal_decision",
        "Personal",
        {"ranked_alternatives": ranked},
        {"constraint_summary": constraints},
        flags,
        ["Personal decisions trade money, time, and subjective utility."],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_agent_budget)
def agent_budget(
    compute_budget_usd: float = 1.0,
    token_budget: float = 1000.0,
    time_deadline_hours: float = 1.0,
    expected_value_of_information: float = 0.0,
    actions: List[dict] = None,
    scale_mode: str = "agentic",
) -> Any:
    """Optimal action sequence for an AI agent under resource constraints. [Agentic Dimension]"""
    if actions is None:
        actions = []
    feasible = []
    for action in actions:
        cost = action.get("compute_cost_usd", 0) + action.get("token_cost", 0) * 0.00001
        time = action.get("time_hours", 0)
        value = action.get("expected_value", 0)
        if cost <= compute_budget_usd and time <= time_deadline_hours:
            feasible.append(
                {
                    "name": action.get("name"),
                    "cost": round_value(cost, 6),
                    "value": value,
                    "efficiency": round_value(value / max(cost, 1e-9), 6),
                }
            )
    feasible.sort(key=lambda x: x["efficiency"], reverse=True)
    selected = []
    remaining_budget = compute_budget_usd
    remaining_time = time_deadline_hours
    total_value = 0.0
    for action in feasible:
        if (
            action["cost"] <= remaining_budget
            and action["cost"] * 0.00001 <= token_budget
            and action.get("time_hours", 0) <= remaining_time
        ):
            selected.append(action["name"])
            remaining_budget -= action["cost"]
            remaining_time -= action.get("time_hours", 0)
            total_value += action["value"]
    flags = []
    if total_value < expected_value_of_information:
        flags.append("VALUE_OF_INFORMATION_NEGATIVE")
    return create_envelope(
        "wealth_agent_budget",
        "Agentic",
        {"selected_actions": selected, "total_value": round_value(total_value, 6)},
        {
            "remaining_budget": round_value(remaining_budget, 2),
            "remaining_time": round_value(remaining_time, 2),
        },
        flags,
        ["Agent budgets optimize value per unit of compute and latency."],
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_crisis_triage)
def crisis_triage(
    resources: dict,
    demands: List[dict],
    recovery_horizon_days: float = 30,
    scale_mode: str = "crisis",
) -> Any:
    """Survival-oriented resource triage. [Crisis Dimension]"""
    total_supply = sum(v for v in resources.values() if math.isfinite(v))
    total_demand = sum(
        d.get("amount", 0) for d in demands if math.isfinite(d.get("amount", 0))
    )
    gap = total_demand - total_supply
    sorted_demands = sorted(demands, key=lambda d: d.get("urgency", 1), reverse=True)
    allocated = []
    remaining = dict(resources)
    for demand in sorted_demands:
        name = demand.get("name")
        amount = demand.get("amount", 0)
        res_type = demand.get("resource_type", "general")
        available = remaining.get(res_type, remaining.get("general", 0))
        grant = min(amount, available)
        remaining[res_type] = available - grant
        if res_type != "general" and "general" in remaining:
            remaining["general"] -= grant
        allocated.append(
            {
                "name": name,
                "granted": round_value(grant, 2),
                "shortfall": round_value(amount - grant, 2),
            }
        )
    survival_probability = max(0.0, min(1.0, total_supply / max(total_demand, 1e-9)))
    flags = []
    if survival_probability < 0.5:
        flags.append("SURVIVAL_CRITICAL")
    elif survival_probability < 0.8:
        flags.append("SURVIVAL_AT_RISK")
    return create_envelope(
        "wealth_crisis_triage",
        "Crisis",
        {
            "survival_probability": round_value(survival_probability, 4),
            "resource_gap": round_value(gap, 2),
        },
        {
            "triage_allocation": allocated,
            "recovery_horizon_days": recovery_horizon_days,
        },
        flags,
        ["Crisis mode prioritizes survival probability over efficiency."],
        scale_mode=scale_mode,
        governance_args={
            "reversible": False,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0,
            "maruah_score": 0.6,
            "runway_months": recovery_horizon_days / 30.0,
        },
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_civilization_stewardship)
def civilization_stewardship(
    population: float,
    energy_budget_twh: float,
    carbon_budget_gt: float,
    tech_growth_rate: float,
    time_horizon_years: int = 100,
    scale_mode: str = "civilization",
) -> Any:
    """Long-term civilization sustainability path. [Civilization Dimension]"""
    flags = []
    energy_per_capita = energy_budget_twh / max(population, 1)
    carbon_intensity = carbon_budget_gt / max(energy_budget_twh, 1)
    sustainable_growth = tech_growth_rate * (1 - carbon_intensity)
    projected_pop = population * pow(
        1 + min(tech_growth_rate, 0.02), time_horizon_years / 100
    )
    collapse_risk = max(0.0, min(1.0, (projected_pop * 10) / max(energy_budget_twh, 1)))
    if collapse_risk > 0.5:
        flags.append("CIVILIZATION_COLLAPSE_RISK_HIGH")
    if carbon_intensity > 0.05:
        flags.append("CARBON_BUDGET_EXHAUSTION")
    sustainability_index = max(
        0.0, min(1.0, sustainable_growth / max(collapse_risk, 0.01))
    )
    return create_envelope(
        "wealth_civilization_stewardship",
        "Civilization",
        {
            "sustainability_index": round_value(sustainability_index, 4),
            "collapse_risk": round_value(collapse_risk, 4),
            "sustainable_growth_rate": round_value(sustainable_growth, 6),
        },
        {
            "energy_per_capita_twh": round_value(energy_per_capita, 6),
            "projected_population_billions": round_value(projected_pop / 1e9, 4),
            "time_horizon_years": time_horizon_years,
        },
        flags,
        ["Civilization modeling uses long-horizon, low-discount assumptions."],
        scale_mode=scale_mode,
        governance_args={
            "reversible": False,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - collapse_risk,
            "maruah_score": 0.5,
            "carbon_intensity": carbon_intensity,
            "social_stability_index": 1.0 - collapse_risk,
        },
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_coordination_equilibrium)
def coordination_equilibrium(
    agents: List[dict],
    shared_resources: dict,
    mechanism: str = "cooperative",
    scale_mode: str = "enterprise",
) -> Any:
    """Multi-agent resource coordination and equilibrium analysis. [Coordination Dimension]"""
    # Normalize agents to LP schema
    lp_agents = _normalize_coordination_agents(agents, list(shared_resources.keys()))

    lp_result = lp_allocate(lp_agents, shared_resources)
    commons = commons_risk(lp_agents, shared_resources)

    # === Epistemic Correlation Guard ===
    correlation_report = {"action": "PASS"}
    if EPISTEMIC_AVAILABLE:
        guard = CorrelationGuard()
        res = guard.check_portfolio(agents)
        correlation_report = res.to_dict()
        if res.action == "HOLD":
            lp_result["feasible"] = False
            lp_result["flags"] = lp_result.get("flags", []) + ["CORRELATED_MODEL_BIAS"]

    tragedy_risk = commons["tragedy_risk"]
    conflicts = []
    if "DEMAND_PARTIALLY_UNMET" in commons.get("flags", []):
        for name, unmet in lp_result.get("unmet_demand", {}).items():
            for res, gap in unmet.items():
                conflicts.append({"agent": name, "resource": res, "gap": gap})

    cooperative_surplus = 0.0
    if mechanism == "cooperative":
        for agent in agents:
            cooperative_surplus += agent.get("cooperative_value", 0)

    flags = commons.get("flags", [])
    if correlation_report.get("action") == "HOLD":
        flags.append("CORRELATED_RISK_HOLD")

    if not conflicts and lp_result["feasible"]:
        flags.append("EQUILIBRIUM_FEASIBLE")

    return create_envelope(
        "wealth_coordination_equilibrium",
        "Coordination",
        {
            "tragedy_risk": round_value(tragedy_risk, 4),
            "conflict_count": len(conflicts),
            "total_welfare": lp_result.get("total_welfare", 0.0),
            "correlation_risk": correlation_report,
        },
        {
            "conflicts": conflicts,
            "cooperative_surplus": round_value(cooperative_surplus, 2),
            "mechanism": mechanism,
            "shadow_prices": commons.get("shadow_prices", {}),
        },
        flags,
        [
            "Coordination layer uses LP shadow prices and scarcity metrics, not hand-wavy ratios.",
            "Epistemic Correlation Guard active — checking for shared model bias across agents.",
        ],
        scale_mode=scale_mode,
        governance_args={
            "reversible": True,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - tragedy_risk,
            "maruah_score": 0.6,
            "dS": tragedy_risk,
        },
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_game_theory_solve)
def game_theory_solve(
    agents: List[dict],
    resources: dict,
    mechanism: str = "cooperative",
    solve_equilibrium: bool = False,
    scale_mode: str = "enterprise",
) -> Any:
    """Multi-agent allocation brain: LP welfare, Shapley/core, and Nash approximation. [Coordination Dimension]"""
    lp_agents = _normalize_coordination_agents(agents, list(resources.keys()))

    lp_result = lp_allocate(lp_agents, resources)
    commons = commons_risk(lp_agents, resources)
    shapley = shapley_values(lp_agents, resources)
    core = core_feasibility(lp_agents, resources, lp_result.get("allocations"))

    # === Epistemic Correlation Guard ===
    correlation_report = {"action": "PASS"}
    if EPISTEMIC_AVAILABLE:
        guard = CorrelationGuard()
        res = guard.check_portfolio(agents)
        correlation_report = res.to_dict()
        if res.action == "HOLD":
            lp_result["feasible"] = False

    equilibrium = {}
    if solve_equilibrium:
        eq = nash_approximation(lp_agents, resources)
        equilibrium = {
            "allocations": eq.get("equilibrium", {}),
            "converged": eq.get("converged", False),
            "iterations": eq.get("iterations", 0),
        }

    flags = []
    if not lp_result["feasible"]:
        flags.append("LP_INFEASIBLE")
    if correlation_report.get("action") == "HOLD":
        flags.append("CORRELATED_RISK_HOLD")
    if commons.get("tragedy_risk", 0.0) > 0.5:
        flags.append("TRAGEDY_OF_COMMONS")
    if not core.get("in_core", False):
        flags.append("CORE_BLOCK_DETECTED")
    if solve_equilibrium and not equilibrium.get("converged", False):
        flags.append("NASH_NO_CONVERGENCE")

    return create_envelope(
        "wealth_game_theory_solve",
        "Coordination",
        {
            "total_welfare": lp_result.get("total_welfare", 0.0),
            "tragedy_risk": commons.get("tragedy_risk", 0.0),
            "in_core": core.get("in_core", False),
            "blocking_coalitions": core.get("blocking_coalitions", [])[:5],
            "correlation_risk": correlation_report,
        },
        {
            "allocations": lp_result.get("allocations", {}),
            "shadow_prices": commons.get("shadow_prices", {}),
            "shapley": shapley.get("shapley", {}),
            "scarcity_index": commons.get("scarcity_index", {}),
            "equilibrium": equilibrium,
        },
        flags,
        [
            "Game-theory solver replaces naive tragedy-risk with LP, core, and equilibrium logic.",
            "Correlation Guard active — preventing systemic failure from shared model lineage.",
        ],
        scale_mode=scale_mode,
        governance_args={
            "reversible": True,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - commons.get("tragedy_risk", 0.0),
            "maruah_score": 0.6,
            "dS": commons.get("tragedy_risk", 0.0),
        },
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_monte_carlo_forecast)
def monte_carlo_forecast(
    initial_commitment: float,
    mean_cash_flows: List[float],
    volatilities: List[float],
    discount_rate: float = 0.1,
    simulations: int = 10000,
    distribution: str = "lognormal",
    scale_mode: str = "enterprise",
) -> Any:
    """Stochastic forecast with probability-weighted outcomes. [Risk Dimension]"""
    import random

    random.seed(42)
    npvs = []
    periods = len(mean_cash_flows)
    for _ in range(simulations):
        draws = []
        for i, mean in enumerate(mean_cash_flows):
            vol = volatilities[i] if i < len(volatilities) else volatilities[-1]
            if distribution == "lognormal":
                sigma = math.sqrt(math.log1p((vol / max(abs(mean), 1e-9)) ** 2))
                mu = math.log(max(abs(mean), 1e-9)) - 0.5 * sigma**2
                draw = random.lognormvariate(mu, sigma) * (1 if mean >= 0 else -1)
            elif distribution == "triangular":
                low = mean * (1 - vol)
                high = mean * (1 + vol)
                draw = random.triangular(low, high, mean)
            else:
                draw = random.gauss(mean, vol)
            draws.append(draw)
        npv = -abs(initial_commitment) + sum(
            draws[t] / pow(1 + discount_rate, t + 1) for t in range(periods)
        )
        npvs.append(npv)
    npvs.sort()
    positive_prob = sum(1 for n in npvs if n > 0) / len(npvs)
    es_5 = npvs[int(len(npvs) * 0.05)] if npvs else 0
    upside_95 = npvs[int(len(npvs) * 0.95)] if npvs else 0
    mean_npv = sum(npvs) / len(npvs) if npvs else 0
    variance_npv = sum((n - mean_npv) ** 2 for n in npvs) / len(npvs) if npvs else 0
    flags = []
    if positive_prob < 0.5:
        flags.append("MAJORITY_DOWNSIDE")
    return create_envelope(
        "wealth_monte_carlo_forecast",
        "Risk",
        {
            "probability_positive_nrv": round_value(positive_prob, 4),
            "expected_shortfall_5pct": round_value(es_5, 2),
            "upside_potential_95pct": round_value(upside_95, 2),
        },
        {
            "mean_npv": round_value(mean_npv, 2),
            "volatility_of_outcome": round_value(math.sqrt(variance_npv), 2),
            "simulations": simulations,
            "distribution": distribution,
        },
        flags,
        ["Monte Carlo provides density estimates, not deterministic guarantees."],
        scale_mode=scale_mode,
        governance_args={
            "epistemic": "ESTIMATE",
            "uncertainty_band": [round_value(es_5, 2), round_value(upside_95, 2)],
            "scale_mode": scale_mode,
        },
    )


# === INGESTION LAYER ===
try:
    from host.ingest.registry import get_registry

    INGEST_AVAILABLE = True
except Exception:
    INGEST_AVAILABLE = False

    def get_registry():  # type: ignore
        return None


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_fetch)
def ingest_fetch(
    source: str,
    series_id: str,
    entity_code: str,
    use_cache: bool = True,
    bus: str = "slow",
) -> Any:
    """Fetch a live data series from an open public source. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_fetch",
            "Sense",
            {"records": []},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.fetch(
        source, series_id, entity_code, use_cache=use_cache, bus=bus
    )
    flags = list(result.get("flags", []))
    if not result.get("records") and not _has_any_flag(flags, {"ADAPTER_NOT_FOUND", "NO_DATA_FETCHED"}):
        flags.append("NO_DATA_FETCHED")
    return create_envelope(
        "wealth_ingest_fetch",
        "Sense",
        {"count": result["count"], "cached": result.get("cached", False)},
        {"records": result["records"][:50], "flags": flags},
        flags,
        ["Live feeds carry source, timestamp, unit, and revision metadata."],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_snapshot)
def ingest_snapshot(entity_code: str, sources: Optional[List[str]] = None) -> Any:
    """Fetch a cross-source macro/energy/carbon snapshot for a geography. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_snapshot",
            "Sense",
            {"coverage": 0},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.snapshot(entity_code, sources=sources)
    flags = result.get("flags", [])
    return create_envelope(
        "wealth_ingest_snapshot",
        "Sense",
        {"coverage": result["coverage"], "entity_code": entity_code},
        {"snapshot": result["snapshot"], "flags": flags},
        flags,
        ["Snapshot assembles orthogonal reality anchors for a single geography."],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_sources)
def ingest_sources() -> Any:
    """List available data sources and their adapter status. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_sources",
            "Sense",
            {"sources": []},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    sources = registry.available_sources()
    return create_envelope(
        "wealth_ingest_sources",
        "Sense",
        {"sources": sources},
        {},
        [],
        [
            "Sources are ranked by sovereignty: central bank > multilateral > aggregator."
        ],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_health)
def ingest_health(adapter: Optional[str] = None) -> Any:
    """Return bus health metrics: latency, cache age, field completeness, stale flags. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_health",
            "Sense",
            {},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    health = registry.health(adapter)
    return create_envelope(
        "wealth_ingest_health",
        "Sense",
        {"health": health},
        {},
        [],
        ["Health tracks latency, success rate, cache age, and observation freshness."],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_vintage)
def ingest_vintage(
    source: str, series_id: str, entity_code: str, vintage_date: str
) -> Any:
    """Fetch a specific vintage of a series (FRED/ALFRED). [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_vintage",
            "Sense",
            {"count": 0},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    try:
        if source == "FRED":
            result = registry.fetch(
                source,
                series_id,
                entity_code,
                use_cache=False,
                vintage_dates=[vintage_date],
                bus="archive",
            )
        else:
            result = {
                "records": [],
                "flags": [f"VINTAGE_UNSUPPORTED:{source}"],
                "count": 0,
            }
    except Exception as exc:
        result = {"records": [], "flags": [f"VINTAGE_ERROR:{exc}"], "count": 0}
    return create_envelope(
        "wealth_ingest_vintage",
        "Sense",
        {"count": result["count"]},
        {"records": result["records"][:50], "flags": result["flags"]},
        result["flags"],
        ["Vintages preserve truth as it was known at a specific date."],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_ingest_reconcile)
def ingest_reconcile(entity_code: str) -> Any:
    """Cross-source divergence detection for a geography. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_reconcile",
            "Sense",
            {},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.reconcile(entity_code)
    return create_envelope(
        "wealth_ingest_reconcile",
        "Sense",
        {
            "divergences": result["divergences"],
            "snapshot_coverage": result["snapshot_coverage"],
        },
        {"flags": result["flags"]},
        result["flags"],
        ["Reconciliation surfaces contradictory signals across independent sources."],
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_check_floors)
def check_floors_tool(
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    ai_is_deciding: bool = False,
    floor_override: bool = False,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    uncertainty_band: Optional[List[float]] = None,
    operation_type: str = "PROJECTION",
    scale_mode: str = "enterprise",
    task_definition: str = "",
    phantom_entries: bool = False,
    critical: bool = False,
    pin_verified: bool = False,
) -> Any:
    """Evaluate F1–F13 constitutional floors. [Governance Dimension]"""
    result = _evaluate_floors(
        {
            "reversible": reversible,
            "human_confirmed": human_confirmed,
            "epistemic": epistemic,
            "ai_is_deciding": ai_is_deciding,
            "floor_override": floor_override,
            "peace2": peace2,
            "maruah_score": maruah_score,
            "uncertainty_band": uncertainty_band,
            "operation_type": operation_type,
            "scale_mode": scale_mode,
            "task_definition": task_definition,
            "phantom_entries": phantom_entries,
            "critical": critical,
            "pin_verified": pin_verified,
        }
    )
    gov_verdict = {
        "HOLD": "888-HOLD",
        "VOID": "VOID",
        "CAUTION": "QUALIFY",
        "SEAL": "SEAL",
    }.get(result["verdict"], "SEAL")
    return create_envelope(
        "wealth_check_floors",
        "Governance",
        {"pass": result["pass"], "verdict": result["verdict"]},
        {
            "violations": result["violations"],
            "holds": result["holds"],
            "warnings": result["warnings"],
            "maruah_band": maruah_band(maruah_score),
        },
        [*result["violations"], *result["holds"]],
        ["F1-F13 floors are hard constraints, not suggestions."],
        epistemic=epistemic,
        verdict=gov_verdict,
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_policy_audit)
def policy_audit(
    proposal: dict, constraints: Optional[dict] = None, scale_mode: str = "enterprise"
) -> Any:
    """Audit an allocation proposal against configurable policy constraints. [Governance Dimension]"""
    engine = PolicyEngine(constraints)
    result = engine.evaluate(proposal, scale_mode)
    policy_verdict = (
        "VOID"
        if not result["policy_pass"]
        else ("QUALIFY" if result["flags"] else "SEAL")
    )
    return create_envelope(
        "wealth_policy_audit",
        "Governance",
        {"policy_pass": result["policy_pass"]},
        {
            "flags": result["flags"],
            "details": result["details"],
            "constraints_applied": result["constraints_applied"],
        },
        result["flags"],
        ["Policy constraints encode constitutional economic boundaries."],
        verdict=policy_verdict,
        scale_mode=scale_mode,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_record_transaction)
def record_transaction_tool(
    tx_type: str,
    amount: float,
    currency: str,
    description: str,
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    fees: Optional[float] = None,
    broker: Optional[str] = None,
    asset_id: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
) -> Any:
    """Record a financial transaction to VAULT999 arifos_vault.wealth.transactions. [Vault Dimension]"""
    from host.governance.vault import record_transaction as _rt

    if dry_run:
        return create_envelope(
            "wealth_record_transaction",
            "Vault",
            {
                "tx_id": None,
                "status": "DRY_RUN",
                "integrity": None,
                "idempotency_key": idempotency_key,
                "human_confirmed": human_confirmed,
                "would_write": True,
                "dry_run": True,
            },
            {},
            [],
            ["DRY_RUN: No transaction written to VAULT999."],
            verdict="HOLD",
            scale_mode="enterprise",
        )

    result = _rt(
        tx_type=tx_type,
        amount=amount,
        currency=currency,
        description=description,
        quantity=quantity,
        price=price,
        fees=fees,
        broker=broker,
        asset_id=asset_id,
        category=category,
        source_tool="wealth_record_transaction",
        notes=notes,
        metadata={
            "idempotency_key": idempotency_key,
            "human_confirmed": human_confirmed,
            "tool": "wealth_record_transaction",
        },
    )
    verdict = "SEAL" if result.get("status") == "INSERTED" else "VOID"
    return create_envelope(
        "wealth_record_transaction",
        "Vault",
        {
            "tx_id": result.get("tx_id"),
            "status": result.get("status"),
            "integrity": result.get("integrity"),
            "idempotency_key": idempotency_key,
            "human_confirmed": human_confirmed,
        },
        {"pg_error": result.get("pg_error")},
        [],
        ["Transaction recorded to VAULT999 — immutable, auditable."],
        verdict=verdict,
        scale_mode="enterprise",
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_snapshot_portfolio)
def snapshot_portfolio_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Dict[str, Any],
    scale_mode: str = "enterprise",
    asset_id: Optional[str] = None,
    nav_myr: Optional[float] = None,
    quantity_held: Optional[float] = None,
    price_close: Optional[float] = None,
    currency: str = "MYR",
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
) -> Any:
    """Snapshot a tool computation result to VAULT999 arifos_vault.wealth.portfolio_snapshots. [Vault Dimension]"""
    from host.governance.vault import snapshot_portfolio as _sp

    if dry_run:
        return create_envelope(
            "wealth_snapshot_portfolio",
            "Vault",
            {
                "snapshot_id": None,
                "status": "DRY_RUN",
                "integrity": None,
                "idempotency_key": idempotency_key,
                "human_confirmed": human_confirmed,
                "would_write": True,
                "dry_run": True,
            },
            {},
            [],
            ["DRY_RUN: No snapshot written to VAULT999."],
            verdict="HOLD",
            scale_mode="enterprise",
        )

    snap = _sp(
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        scale_mode=scale_mode,
        asset_id=asset_id,
        nav_myr=nav_myr,
        quantity_held=quantity_held,
        price_close=price_close,
        currency=currency,
    )
    verdict = "SEAL" if snap.get("status") == "INSERTED" else "VOID"
    return create_envelope(
        "wealth_snapshot_portfolio",
        "Vault",
        {
            "snapshot_id": snap.get("snapshot_id"),
            "status": snap.get("status"),
            "integrity": snap.get("integrity"),
            "idempotency_key": idempotency_key,
            "human_confirmed": human_confirmed,
        },
        {"pg_error": snap.get("pg_error")},
        [],
        ["Portfolio snapshot sealed to VAULT999."],
        verdict=verdict,
        scale_mode=scale_mode,
    )


@mcp.resource("wealth://doctrine/valuation")
def get_valuation_doctrine() -> str:
    return json.dumps(
        {
            "motto": "Physics > Narrative",
            "principles": [
                "F1: Absolute Value (NPV) is the primary anchor.",
                "F2: Reinvestment risk must be modeled via MIRR.",
                "F3: Time-Value is a physical decay function.",
                "F4: Leverage must never break the DSCR floor (1.25x).",
                "F5: Mandatory governance signals (dS, peace2, maruah) for SEAL.",
            ],
            "protocol": f"Dimensional Forge v{__version__}",
        },
        indent=2,
    )


@mcp.resource("wealth://dimensions/definitions")
def get_dimensional_definitions() -> str:
    return json.dumps(
        {
            "Reward": "Total energy output (NPV, EAA).",
            "Energy": "Efficiency and potential (IRR, PI).",
            "Entropy": "Risk, noise, and probability (EMV, Audit).",
            "Time": "Recovery velocity (Payback).",
            "Mass": "Accumulated state (Net Worth).",
            "Flow": "Metabolic rate (Cash Flow).",
            "Velocity": "Rate of expansion (Growth).",
            "Survival": "Structural load capacity (DSCR).",
            "Allocation": "Sovereign decision kernel (Score).",
        },
        indent=2,
    )


@mcp.resource("wealth://governance/floors")
def get_constitutional_floors() -> str:
    """Detailed definitions of the 13 Constitutional Floors (F1-F13)."""
    return json.dumps(
        {
            "F1": "Amanah (Reversibility) - All actions must be reversible or reparable.",
            "F2": "Truth (Accuracy) - Prioritize factual grounding; cite sources.",
            "F3": "Tri-Witness (Consensus) - Decisions require Theory, Constitution, and Manifesto agreement.",
            "F4": "Clarity (Entropy Reduction) - Responses must reduce confusion (delta S <= 0).",
            "F5": "Peace^2 (Non-Destruction) - Exponential penalty for destruction of value/trust.",
            "F6": "Empathy (RASA) - Active listening: Receive, Appreciate, Summarize, Ask.",
            "F7": "Humility (Uncertainty) - Maintain epistemic uncertainty within [0.03, 0.05].",
            "F8": "Genius (Systemic Health) - Maintain G >= 0.80 across A, P, X, E dials.",
            "F9": "Ethics (Anti-Poison) - Dark genius (C_dark) must remain below 0.30.",
            "F10": "Conscience (Identity) - No false consciousness claims; maintain Lab-Shaped Identity.",
            "F11": "Auditability (Transparency) - Immutable, tamper-evident logs for all decisions.",
            "F12": "Resilience (Graceful Failure) - Degrade functionality safely; never crash.",
            "F13": "Adaptability (Safe Evolution) - Governed evolution via W^3 consensus and tests.",
        },
        indent=2,
    )


@mcp.resource("wealth://governance/harness-doctrines")
def get_harness_doctrines() -> str:
    """The 9-Harness Constraint Architecture for WEALTH power containment."""
    return json.dumps(
        {
            "1_Identity": "Bind power to accountable identity and chain continuity. No seal, no allocation.",
            "2_Reality": "Ground decisions in physical data provenance. No hallucination.",
            "3_Epistemic": "Prevent scalar illusions and correlated bias. P10/P50/P90 thinking mandatory.",
            "4_Entropy": "Detect hidden fragility and noise in cash flows. Stochastic stress-testing.",
            "5_Survival": "Ensure metabolic liquidity and solvency under stress (DSCR/Flow).",
            "6_Constitutional": "Bind allocation to F1-F13 floors. 888_HOLD for irreversible harm.",
            "7_Efficiency": "Resource discipline; capital must earn its survival (PI >= 1.0).",
            "8_Coordination": "Multi-agent stability; Nash-equilibrium and Core-feasibility checks.",
            "9_Civilization": "Long-horizon planetary survival and energy budget alignment.",
        },
        indent=2,
    )


@mcp.resource("wealth://topology/families")
def get_sovereign_families() -> str:
    """The 6 Sovereign Families of the WEALTH v2 Lattice."""
    return json.dumps(
        {
            "SENSE": "External reality ingestion and environmental observation (Stage 100).",
            "MIND": "Uncertainty modeling, Monte Carlo, and epistemic validation (Stage 200).",
            "SURVIVAL": "Solvency, leverage gating, and metabolic triage (Stage 300).",
            "REASON": "Capital discipline, NPV/IRR optimization, and yield analysis (Stage 400).",
            "JUDGE": "Constitutional gating, policy auditing, and 888_HOLD (Stage 888).",
            "VAULT": "Immutable anchoring, receipt hashing, and ledger sealing (Stage 999).",
        },
        indent=2,
    )


@mcp.resource("wealth://topology/scales")
def get_capital_scales() -> str:
    """Definitions of the 8 Capital Scales used in the WEALTH Engine."""
    return json.dumps(
        {
            "personal": "Individual resource allocation and life-horizon planning.",
            "household": "Multi-individual metabolic unit (family/home) stability.",
            "sme": "Small/Medium Enterprise; metabolic local node growth.",
            "enterprise": "Large-scale organizational resource optimization.",
            "national": "Macro-scale resource policy and sovereign allocation.",
            "crisis": "Extreme stress/survival state (war, disaster, famine).",
            "civilization": "Planetary/Species-horizon survival and stewardship.",
            "agentic": "Autonomous agent resource coordination and budget gating.",
        },
        indent=2,
    )


@mcp.resource("wealth://epistemic/uncertainty-matrix")
def get_epistemic_matrix() -> str:
    """Key metrics for Epistemic Integrity and Humility."""
    return json.dumps(
        {
            "omega_0": "Raw uncertainty coefficient (0.0 = total certainty, 1.0 = total chaos).",
            "kappa_r": "Humility score (derived from RASA and Truth consistency).",
            "humility_band": "The habitability range [0.03, 0.05]. Outside this is Arrogance or Paralysis.",
            "epistemic_tiers": ["CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "VERIFIED"],
        },
        indent=2,
    )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_evoi_compute)
async def wealth_evoi_compute(
    well_cost_musd: float,
    p50_value_musd: float,
    prior_pos: float | None = None,
    posterior_pos: float | None = None,
    prospect_metrics: dict | None = None,
    info_cost_musd: float = 5.0,
    discount_rate: float = 0.10,
    scale_mode: str = "enterprise",
) -> Any:
    """
    Expected Value of Information (EVOI) point-estimate computation. [Epistemic Dimension]
    Ingests GEOX prospect_metrics or raw prior/posterior probabilities.
    EVOI = E[V | with_info] - E[V | without_info]
    """
    # Metric Handoff (GEOX -> WEALTH)
    if prospect_metrics:
        final_prior = prospect_metrics.get("composite_pos", prior_pos)
        final_posterior = posterior_pos or min(1.0, final_prior * 1.25) if final_prior else posterior_pos
    else:
        final_prior = prior_pos
        final_posterior = posterior_pos

    if final_prior is None or final_posterior is None:
         return create_envelope(
            "wealth_evoi_compute", "Epistemic", {}, 
            {"error": "Missing prior_pos or posterior_pos"}, 
            ["EPISTEMIC_UNAVAILABLE"], verdict="VOID"
        )

    if not EPISTEMIC_AVAILABLE:
        return create_envelope(
            "wealth_evoi_compute",
            "Epistemic",
            {},
            {"error": "EPISTEMIC_UNAVAILABLE"},
            ["EPISTEMIC_UNAVAILABLE"],
            verdict="VOID",
        )

    try:
        from host.epistemic.evoi import compute_evoi
        res = compute_evoi(
            prior_pos=final_prior,
            posterior_pos=final_posterior,
            well_cost_musd=well_cost_musd,
            p50_value_musd=p50_value_musd,
            info_cost_musd=info_cost_musd,
            discount_rate=discount_rate,
        )

        drill = res.get("drill_recommendation", "")
        if drill.startswith("PROCEED"):
            res["economic_signal"] = "POSITIVE_EVOI"
        elif drill.startswith("DO_NOT_DRILL"):
            res["economic_signal"] = "NEGATIVE_EVOI"
        else:
            res["economic_signal"] = "MARGINAL_EVOI"
        res["execution_verdict"] = "REQUIRES_888_JUDGE"

        return create_envelope(
            "wealth_evoi_compute",
            "Epistemic",
            res,
            {"info_cost": info_cost_musd, "well_cost": well_cost_musd},
            [],
            [
                f"Prior PoS: {final_prior:.2f}",
                f"Posterior PoS: {final_posterior:.2f}",
                f"Information cost: {info_cost_musd} MUSD",
            ],
            verdict="SEAL" if res.get("evoi_musd", 0) > 0 else "QUALIFY",
            scale_mode=scale_mode,
        )
    except Exception as e:
        return create_envelope(
            "wealth_evoi_compute",
            "Epistemic",
            {},
            {"error": str(e)},
            ["COMPUTATION_ERROR"],
            verdict="VOID",
        )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_evoi_monte_carlo)
async def wealth_evoi_monte_carlo(
    prior_pos_samples: List[float],
    posterior_pos_samples: List[float],
    well_cost_musd: float,
    p50_value_musd: float,
    info_cost_musd: float = 5.0,
    scale_mode: str = "enterprise",
) -> Any:
    """
    Monte Carlo Expected Value of Information (EVOI) distributional computation. [Epistemic Dimension]
    Uses sample distributions to compute P10/P50/P90 EVOI metrics.
    Recommended when PoS estimates are highly uncertain.
    """
    if not EPISTEMIC_AVAILABLE:
        return create_envelope(
            "wealth_evoi_monte_carlo",
            "Epistemic",
            {},
            {"error": "EPISTEMIC_UNAVAILABLE"},
            ["EPISTEMIC_UNAVAILABLE"],
            verdict="VOID",
        )

    try:
        res = compute_evoi_monte_carlo(
            prior_pos_samples=prior_pos_samples,
            posterior_pos_samples=posterior_pos_samples,
            well_cost_musd=well_cost_musd,
            p50_value_musd=p50_value_musd,
            info_cost_musd=info_cost_musd,
        )
        evoi_p50 = res.get("evoi_p50", 0)
        if evoi_p50 > 0:
            res["economic_signal"] = "POSITIVE_EVOI"
        elif evoi_p50 < 0:
            res["economic_signal"] = "NEGATIVE_EVOI"
        else:
            res["economic_signal"] = "MARGINAL_EVOI"
        res["execution_verdict"] = "REQUIRES_888_JUDGE"

        return create_envelope(
            "wealth_evoi_monte_carlo",
            "Epistemic",
            res,
            {"sample_count": len(prior_pos_samples)},
            [],
            ["Monte Carlo distribution based on user-provided samples"],
            verdict="SEAL" if res.get("evoi_p50", 0) > 0 else "QUALIFY",
            scale_mode=scale_mode,
        )
    except Exception as e:
        return create_envelope(
            "wealth_evoi_monte_carlo",
            "Epistemic",
            {},
            {"error": str(e)},
            ["COMPUTATION_ERROR"],
            verdict="VOID",
        )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_correlation_guard_check)
async def wealth_correlation_guard_check(
    prospects: List[Dict[str, Any]],
    correlation_threshold: int = 3,
    scale_mode: str = "enterprise",
) -> Any:
    """
    Check portfolio for correlated model bias. [Epistemic Dimension]
    Uses model_lineage_hash to detect when multiple prospects share the same AI lineage.
    Systemic risk is detected if >= threshold prospects share a lineage.
    """
    if not EPISTEMIC_AVAILABLE:
        return create_envelope(
            "wealth_correlation_guard_check",
            "Epistemic",
            {},
            {"error": "EPISTEMIC_UNAVAILABLE"},
            ["EPISTEMIC_UNAVAILABLE"],
            verdict="VOID",
        )

    try:
        guard = CorrelationGuard(correlation_threshold=correlation_threshold)
        res = guard.check_portfolio(prospects)

        return create_envelope(
            "wealth_correlation_guard_check",
            "Epistemic",
            res.to_dict(),
            guard.assess_epistemic_diversity(prospects),
            [],
            [f"Correlation threshold: {correlation_threshold}"],
            verdict="SEAL" if res.action == "PASS" else "888-HOLD",
            scale_mode=scale_mode,
        )
    except Exception as e:
        return create_envelope(
            "wealth_correlation_guard_check",
            "Epistemic",
            {},
            {"error": str(e)},
            ["COMPUTATION_ERROR"],
            verdict="VOID",
        )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_schema_validate)
def wealth_schema_validate(
    prospects: List[Dict[str, Any]],
    scale_mode: str = "enterprise",
) -> Any:
    """
    Validate prospect inputs against epistemic requirements. [Epistemic Dimension]
    Rejects scalar volumes (requires p10/p50/p90).
    Enforces integrity_score >= 0.3 for capital allocation.
    """
    if not EPISTEMIC_AVAILABLE:
        return create_envelope(
            "wealth_schema_validate",
            "Epistemic",
            {},
            {"error": "EPISTEMIC_UNAVAILABLE"},
            ["EPISTEMIC_UNAVAILABLE"],
            verdict="VOID",
        )

    try:
        validator = SchemaValidator()
        res = validator.validate_portfolio(prospects)

        return create_envelope(
            "wealth_schema_validate",
            "Epistemic",
            res,
            {},
            [],
            ["Validation against v1.5.0 epistemic invariants."],
            verdict="SEAL" if res.get("portfolio_valid") else "VOID",
            scale_mode=scale_mode,
        )
    except Exception as e:
        return create_envelope(
            "wealth_schema_validate",
            "Epistemic",
            {},
            {"error": str(e)},
            ["COMPUTATION_ERROR"],
            verdict="VOID",
        )


# INTERNAL ENGINE — DO NOT EXPOSE PUBLICLY (was wealth_init)
async def wealth_init_tool(
    session_id: Optional[str] = None,
    actor_id: str = "wealth-agent",
    intent: Optional[str] = None,
) -> Any:
    """
    Open a WEALTH governance session — writes a 000_INIT event to VAULT999.
    Call this at the start of any WEALTH analysis session to anchor identity
    and connect to the canonical Merkle chain (prev_hash = last vault_seals root).
    Returns session_id and chain position for subsequent wealth_snapshot_portfolio seals.
    """
    import sys
    import uuid as _uuid
    import os

    # Robust path resolution for arifOS root
    possible_paths = [
        "/root/arifOS",
        "/root",
        os.path.abspath(os.path.join(os.getcwd(), "..")),
        os.getcwd(),
    ]
    for p in possible_paths:
        if p not in sys.path:
            sys.path.append(p)

    sid = session_id or f"wealth-session-{_uuid.uuid4().hex[:12]}"

    # Try arifOS vault first, fall back to file-based anchor
    import hashlib
    import json as _json

    vault_ok = False
    chain_hash = ""
    ledger_id = ""

    try:
        from arifosmcp.runtime.vault_postgres import seal_to_vault
        res = await seal_to_vault(
            event_type="WEALTH_SESSION_INIT",
            session_id=sid,
            actor_id=actor_id,
            stage="000_INIT",
            verdict="ACTIVE",
            payload={"intent": intent or "economic-analysis", "source": "WEALTH-MCP"},
            risk_tier="low",
        )
        chain_hash = getattr(res, "chain_hash", "")
        ledger_id = getattr(res, "ledger_id", "")
        vault_ok = True
    except Exception:
        # Fallback: write to local JSONL vault
        try:
            vault_dir = "/app/data"
            os.makedirs(vault_dir, exist_ok=True)
            vault_path = os.path.join(vault_dir, "vault999.jsonl")
            entry = {
                "event_type": "WEALTH_SESSION_INIT",
                "session_id": sid,
                "actor_id": actor_id,
                "stage": "000_INIT",
                "verdict": "ACTIVE",
                "payload": {"intent": intent or "economic-analysis", "source": "WEALTH-MCP"},
                "risk_tier": "low",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            entry["_hash"] = hashlib.sha256(
                _json.dumps(entry, sort_keys=True).encode()
            ).hexdigest()
            with open(vault_path, "a") as f:
                f.write(_json.dumps(entry) + "\n")
            chain_hash = entry["_hash"]
            ledger_id = f"local-vault-{sid}"
            vault_ok = True
        except Exception:
            pass

    if vault_ok:
        return create_envelope(
            "wealth_init",
            "Vault",
            {
                "session_id": sid,
                "stage": "000_INIT",
                "chain_hash": chain_hash,
                "vault_id": ledger_id,
            },
            {},
            [],
            ["WEALTH session anchored to VAULT999 chain. Ready for analysis."],
            verdict="SEAL",
        )
    else:
        return create_envelope(
            "wealth_init",
            "Vault",
            {},
            {"error": "Vault unavailable: arifOS not installed and local write failed"},
            [],
            ["Vault anchor failed — arifOS not mounted in this container"],
            verdict="VOID",
        )


# ============================================================
# V3 Sovereign Primitives (13 public MCP tools)
# ============================================================

CANONICAL_TOOL_METADATA = {
    "wealth_future_value": {"family": "REASON", "stage": "400-REASON", "display": "wealth_future_value"},
    "wealth_present_expect": {"family": "MIND", "stage": "200-MIND", "display": "wealth_present_expect"},
    "wealth_future_simulate": {"family": "MIND", "stage": "200-MIND", "display": "wealth_future_simulate"},
    "wealth_info_value": {"family": "MIND", "stage": "200-MIND", "display": "wealth_info_value"},
    "wealth_truth_validate": {"family": "MIND", "stage": "200-MIND", "display": "wealth_truth_validate"},
    "wealth_survival_liquidity": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_liquidity"},
    "wealth_survival_leverage": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_survival_leverage"},
    "wealth_rule_enforce": {"family": "JUDGE", "stage": "888-JUDGE", "display": "wealth_rule_enforce"},
    "wealth_allocate_optimize": {"family": "REASON", "stage": "400-REASON", "display": "wealth_allocate_optimize"},
    "wealth_game_coordinate": {"family": "REASON", "stage": "400-REASON", "display": "wealth_game_coordinate"},
    "wealth_sense_ingest": {"family": "SENSE", "stage": "100-SENSE", "display": "wealth_sense_ingest"},
    "wealth_past_record": {"family": "VAULT", "stage": "999-VAULT", "display": "wealth_past_record"},
    "wealth_future_steward": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "wealth_future_steward"},
}


def _normalize_primitive_envelope(result: Any, canonical_tool: str) -> Any:
    """Rewrite internal helper labels to the public 13-tool canonical surface."""
    if not isinstance(result, dict):
        return result

    metadata = CANONICAL_TOOL_METADATA.get(canonical_tool)
    if metadata is None:
        return result

    result["task"] = canonical_tool
    result["canonical_tool"] = canonical_tool

    secondary_metrics = result.get("secondary_metrics")
    if isinstance(secondary_metrics, dict):
        secondary_metrics["display_name"] = metadata["display"]
        secondary_metrics["family"] = metadata["family"]

    return result


def _normalize_coordination_agents(
    agents: List[dict], resource_keys: List[str], default_demand: float = math.inf
) -> List[dict]:
    """Accept scalar or dict agent packets and normalize them to LP-ready structures."""
    normalized = []
    for index, agent in enumerate(agents):
        utility = agent.get("utility", {})
        if isinstance(utility, (int, float)):
            utility = {resource: float(utility) for resource in resource_keys}
        elif not isinstance(utility, dict):
            utility = {resource: 1.0 for resource in resource_keys}

        demand = agent.get("resource_demand", agent.get("demand", {}))
        if isinstance(demand, (int, float)):
            demand = {resource: float(demand) for resource in resource_keys}
        elif not isinstance(demand, dict):
            demand = {resource: default_demand for resource in resource_keys}

        normalized.append(
            {
                "name": agent.get("name") or agent.get("id") or f"agent_{index + 1}",
                "utility": utility,
                "demand": demand,
            }
        )
    return normalized

@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_future_value(
    mode: str = "npv",
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
) -> Any:
    """⚠️ DEPRECATED — Use atomic tools: wealth_value_npv, wealth_energy_irr, wealth_density_pi, wealth_time_payback. [Value Dimension — DEPRECATED]"""
    cash_flows = cash_flows or []
    if mode == "npv":
        result = npv_reward(initial_investment, cash_flows, discount_rate, terminal_value, period_unit, input_epistemic, scale_mode)
    elif mode == "irr":
        result = irr_yield(initial_investment, cash_flows, reinvestment_rate, finance_rate, period_unit, discount_rate, scale_mode)
    elif mode == "pi":
        result = pi_efficiency(initial_investment, cash_flows, discount_rate, terminal_value, scale_mode)
    elif mode == "payback":
        result = payback_time(initial_investment, cash_flows, discount_rate, period_unit, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_future_value")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_present_expect(
    scenarios: List[dict],
    scale_mode: str = "enterprise",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_expectation_emv. [Expect Dimension — DEPRECATED]"""
    normalized = []
    for s in scenarios:
        normalized.append({
            "probability": s.get("probability", s.get("prob", 0)),
            "outcome": s.get("outcome", s.get("return", s.get("cash_flow", 0))),
        })
    return _normalize_primitive_envelope(emv_risk(normalized, scale_mode), "wealth_present_expect")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_future_simulate(
    initial_commitment: float,
    mean_cash_flows: List[float],
    volatilities: List[float],
    discount_rate: float = 0.1,
    simulations: int = 10000,
    distribution: str = "lognormal",
    scale_mode: str = "enterprise",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_signal_monte_carlo. [Simulate Dimension — DEPRECATED]"""
    return _normalize_primitive_envelope(
        monte_carlo_forecast(
            initial_commitment,
            mean_cash_flows,
            volatilities,
            discount_rate,
            simulations,
            distribution,
            scale_mode,
        ),
        "wealth_future_simulate",
    )


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_survival_liquidity(
    mode: str = "cashflow",
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
    principal: float = 0,
    rate: float = 0,
    years: int = 1,
    annual_contribution: float = 0,
    monthly_burn: float = 0,
    resources: Optional[dict] = None,
    demands: Optional[List[dict]] = None,
    recovery_horizon_days: float = 30,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_flow_cashflow, wealth_velocity_runway, wealth_pressure_triage. [Liquidity Dimension — DEPRECATED]"""
    resources = resources or {}
    demands = demands or []
    if mode == "cashflow":
        result = cashflow_flow(income, expenses, liquid_assets, scale_mode)
    elif mode == "velocity":
        result = growth_velocity(principal, rate, years, annual_contribution, monthly_burn, scale_mode)
    elif mode == "triage":
        result = crisis_triage(resources, demands, recovery_horizon_days, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_survival_liquidity")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_survival_leverage(
    mode: str = "dscr",
    ebitda: Optional[float] = None,
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    cfads: Optional[float] = None,
    debt_service: Optional[float] = None,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
    assets: Optional[List[dict]] = None,
    liabilities: Optional[List[dict]] = None,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_gravity_dscr. [Leverage Dimension — DEPRECATED]"""
    if mode == "dscr":
        result = dscr_leverage(ebitda, principal, interest, leases, cfads, debt_service, period_unit, input_epistemic, scale_mode)
    elif mode == "networth":
        result = networth_state(assets, liabilities, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_survival_leverage")



@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
async def wealth_info_value(
    mode: str = "evoi",
    well_cost_musd: float = 0,
    p50_value_musd: float = 0,
    prior_pos: Optional[float] = None,
    posterior_pos: Optional[float] = None,
    prospect_metrics: Optional[dict] = None,
    info_cost_musd: float = 5.0,
    discount_rate: float = 0.10,
    scale_mode: str = "enterprise",
    prior_pos_samples: Optional[List[float]] = None,
    posterior_pos_samples: Optional[List[float]] = None,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_opportunity_evoi. [Info Dimension — DEPRECATED]"""
    if mode == "evoi":
        result = await wealth_evoi_compute(
            well_cost_musd,
            p50_value_musd,
            prior_pos,
            posterior_pos,
            prospect_metrics,
            info_cost_musd,
            discount_rate,
            scale_mode,
        )
    elif mode == "evoi_mc":
        result = await wealth_evoi_monte_carlo(
            prior_pos_samples or [],
            posterior_pos_samples or [],
            well_cost_musd,
            p50_value_musd,
            info_cost_musd,
            scale_mode,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_info_value")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
async def wealth_truth_validate(
    mode: str = "schema",
    prospects: Optional[List[Dict[str, Any]]] = None,
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    correlation_threshold: int = 3,
    scale_mode: str = "enterprise",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_boundary_floors, wealth_entropy_audit. [Truth Dimension — DEPRECATED]"""
    cash_flows = cash_flows or []
    if mode == "schema":
        result = await wealth_schema_validate(prospects or [], scale_mode)
    elif mode == "correlation":
        result = await wealth_correlation_guard_check(prospects or [], correlation_threshold, scale_mode)
    elif mode == "entropy":
        result = audit_entropy(initial_investment, cash_flows, discount_rate, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_truth_validate")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_rule_enforce(
    mode: str = "floors",
    proposal: Optional[dict] = None,
    constraints: Optional[dict] = None,
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    ai_is_deciding: bool = False,
    floor_override: bool = False,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    uncertainty_band: Optional[List[float]] = None,
    operation_type: str = "PROJECTION",
    scale_mode: str = "enterprise",
    task_definition: str = "",
    phantom_entries: bool = False,
    critical: bool = False,
    pin_verified: bool = False,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_governance_verdict. [Rule Dimension — DEPRECATED]"""
    proposal = proposal or {}
    constraints = constraints or {}
    if mode == "floors":
        result = check_floors_tool(
            reversible,
            human_confirmed,
            epistemic,
            ai_is_deciding,
            floor_override,
            peace2,
            maruah_score,
            uncertainty_band,
            operation_type,
            scale_mode,
            task_definition,
            phantom_entries,
            critical,
            pin_verified,
        )
    elif mode == "policy":
        result = policy_audit(proposal, constraints, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_rule_enforce")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_allocate_optimize(
    mode: str = "kernel",
    d_s: float = 0,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    base_rate: float = 0.1,
    trust_index: float = 0.5,
    delta_civ: float = 0.0,
    wealth_signals: Optional[dict] = None,
    prospects: Optional[List[dict]] = None,
    extractive_signals: Optional[dict] = None,
    compare: bool = False,
    scale_mode: str = "enterprise",
    task_definition: str = "",
    irreversible: bool = False,
    alternatives: Optional[List[dict]] = None,
    constraints: Optional[dict] = None,
    values: Optional[dict] = None,
    compute_budget_usd: float = 0,
    token_budget: float = 0,
    time_deadline_hours: float = 0,
    expected_value_of_information: float = 0,
    actions: Optional[List[dict]] = None,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_stewardship_kernel, wealth_preference_rank, wealth_agent_path. [Allocate Dimension — DEPRECATED]"""
    if mode == "kernel":
        result = wealth_score_kernel(
            d_s,
            peace2,
            maruah_score,
            base_rate,
            trust_index,
            delta_civ,
            wealth_signals,
            prospects,
            extractive_signals,
            compare,
            scale_mode,
            task_definition,
            irreversible,
        )
    elif mode == "personal":
        result = personal_decision(alternatives or [], constraints or {}, values, scale_mode)
    elif mode == "agent":
        result = agent_budget(
            compute_budget_usd,
            token_budget,
            time_deadline_hours,
            expected_value_of_information,
            actions or [],
            scale_mode,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_allocate_optimize")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_game_coordinate(
    mode: str = "equilibrium",
    agents: Optional[List[dict]] = None,
    shared_resources: Optional[dict] = None,
    resources: Optional[dict] = None,
    mechanism: str = "cooperative",
    solve_equilibrium: bool = False,
    scale_mode: str = "enterprise",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_field_game, wealth_field_equilibrium. [Game Dimension — DEPRECATED]"""
    agents = agents or []
    shared_resources = shared_resources or {}
    resources = resources or {}
    if mode == "equilibrium":
        result = coordination_equilibrium(agents, shared_resources, mechanism, scale_mode)
    elif mode == "game":
        result = game_theory_solve(agents, resources, mechanism, solve_equilibrium, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_game_coordinate")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
def wealth_sense_ingest(
    mode: str = "fetch",
    source: str = "",
    series_id: str = "",
    entity_code: str = "",
    use_cache: bool = True,
    bus: str = "slow",
    sources: Optional[List[str]] = None,
    adapter: Optional[str] = None,
    vintage_date: str = "",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_sensor_fetch, wealth_sensor_snapshot, wealth_sensor_reconcile, etc. [Sense Dimension — DEPRECATED]"""
    if mode == "fetch":
        result = ingest_fetch(source, series_id, entity_code, use_cache, bus)
    elif mode == "snapshot":
        result = ingest_snapshot(entity_code, sources)
    elif mode == "sources":
        result = ingest_sources()
    elif mode == "health":
        result = ingest_health(adapter)
    elif mode == "vintage":
        result = ingest_vintage(source, series_id, entity_code, vintage_date)
    elif mode == "reconcile":
        result = ingest_reconcile(entity_code)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_sense_ingest")


@mcp.tool(annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"})
async def wealth_past_record(
    mode: str = "init",
    session_id: Optional[str] = None,
    actor_id: str = "wealth-agent",
    intent: Optional[str] = None,
    tx_type: str = "",
    amount: float = 0,
    currency: str = "MYR",
    description: str = "",
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    fees: Optional[float] = None,
    broker: Optional[str] = None,
    asset_id: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    tool_name: str = "",
    arguments: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    scale_mode: str = "enterprise",
    nav_myr: Optional[float] = None,
    quantity_held: Optional[float] = None,
    price_close: Optional[float] = None,
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_ledger_record, wealth_ledger_snapshot. [Record Dimension — DEPRECATED]"""
    if mode == "init":
        result = await wealth_init_tool(session_id, actor_id, intent)
    elif mode == "transaction":
        result = record_transaction_tool(
            tx_type,
            amount,
            currency,
            description,
            quantity,
            price,
            fees,
            broker,
            asset_id,
            category,
            notes,
        )
    elif mode == "portfolio":
        result = snapshot_portfolio_tool(
            tool_name,
            arguments or {},
            result or {},
            scale_mode,
            asset_id,
            nav_myr,
            quantity_held,
            price_close,
            currency,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_past_record")



@mcp.tool()
def wealth_future_steward(
    carbon_budget_gtc: float = 0,
    energy_mix: Optional[dict] = None,
    population_projection: Optional[dict] = None,
    horizon_years: int = 50,
    scale_mode: str = "civilization",
) -> Any:
    """Long-Horizon Planetary Boundaries — Civilization Continuity. [Steward Dimension]"""
    energy_mix = energy_mix or {}
    population_projection = population_projection or {}
    current_population = float(population_projection.get("current", 0.0))
    renewable_mix = float(energy_mix.get("renewables", 0.0))
    fossil_mix = float(energy_mix.get("fossil", max(0.0, 1.0 - renewable_mix)))
    energy_budget_twh = float(energy_mix.get("energy_budget_twh", 1000.0 * max(renewable_mix + fossil_mix, 1.0)))
    tech_growth_rate = float(
        energy_mix.get(
            "tech_growth_rate",
            population_projection.get("tech_growth_rate", max(0.0, renewable_mix * 0.03)),
        )
    )
    return _normalize_primitive_envelope(
        civilization_stewardship(
            current_population,
            energy_budget_twh,
            carbon_budget_gtc,
            tech_growth_rate,
            horizon_years,
            scale_mode,
        ),
        "wealth_future_steward",
    )

@mcp.tool()
def vault_write(
    action: str,
    payload: Dict[str, Any],
    session_id: str = "UNKNOWN",
    agent_id: str = "WEALTH_AGENT",
    verdict: str = "SEAL",
    ack_irreversible: bool = False,
) -> Any:
    """999: Ledger Append — Permanently write an economic event to VAULT999.
    F01 AMANAH: This operation is irreversible. Requires ack_irreversible=True or verdict != SEAL.
    """
    # F01 Irreversibility gate
    if verdict == "SEAL" and not ack_irreversible:
        return create_envelope(
            "vault_write",
            "VAULT",
            {
                "action": action,
                "status": "HOLD",
                "reason": "F01: Irreversible VAULT999 write requires ack_irreversible=True",
                "vault_id": None,
                "chain_hash": None,
            },
            flags=["F01_HOLD:ack_irreversible_required"],
            epistemic="FACT",
            verdict="888-HOLD",
        )

    # Ensure session_id is in payload for arifOS compliance
    payload["session_id"] = session_id

    # Bridge to arifOS vault system
    res = _vault_append(
        {
            "tool": "vault_write",
            "agent_id": agent_id,
            "action": action,
            "payload": payload,
            "verdict": verdict,
            "confidence": 1.0,
        }
    )

    # Standard WEALTH Envelope
    primary = {
        "action": action,
        "payload": payload,
        "vault_id": res.get("event_id") if isinstance(res, dict) else str(uuid.uuid4()),
        "chain_hash": res.get("chain_hash") if isinstance(res, dict) else "0" * 64,
    }

    return create_envelope(
        "vault_write",
        "VAULT",
        primary,
        epistemic="FACT",
        verdict=verdict,
        governance_args={"human_confirmed": ack_irreversible},
    )


@mcp.tool()
def vaultwrite(
    action: str,
    payload: Dict[str, Any],
    session_id: str = "UNKNOWN",
    agent_id: str = "WEALTH_AGENT",
    verdict: str = "SEAL",
    ack_irreversible: bool = False,
) -> Any:
    """998: Ledger Append (Alias) — Permanently write an economic event to VAULT999.
    F01 AMANAH: This operation is irreversible. Requires ack_irreversible=True or verdict != SEAL.
    Wrapper around vault_write for arifOS compatibility.
    """
    return vault_write(
        action=action,
        payload=payload,
        session_id=session_id,
        agent_id=agent_id,
        verdict=verdict,
        ack_irreversible=ack_irreversible,
    )


@mcp.tool()
def vaultquery(
    query: str,
    limit: int = 10,
    session_id: Optional[str] = None,
) -> Any:
    """998: Ledger Read (Alias) — Query the immutable governance ledger.
    Reads from VAULT999 via Supabase REST API. Read-only operation; no F01 gate.
    Wrapper around vault_query for arifOS compatibility.
    """
    return vault_query(
        query=query,
        limit=limit,
        session_id=session_id,
    )


@mcp.tool()
def vault_query(
    query: str,
    limit: int = 10,
    session_id: Optional[str] = None,
) -> Any:
    """999: Ledger Read — Query the immutable governance ledger.
    Reads from VAULT999 via Supabase REST API. Returns earth_refs[] for F03 traceability.
    """
    from host.governance.vault_supabase import query_vault999

    result = query_vault999(query=query, limit=limit, session_id=session_id)

    primary = {
        "query": result["query"],
        "earth_refs": result["earth_refs"],
        "count": result["count"],
        "vault_seal": result["vault_seal"],
    }

    epistemic = "FACT" if result["count"] > 0 else "ESTIMATE"
    return create_envelope(
        "vault_query",
        "VAULT",
        primary,
        epistemic=epistemic,
    )

# ============================================================
# HarnessEngine v3 mappings — new atomic tools
# ============================================================
_ATOMIC_TO_HARNESS = {
    "wealth_value_npv": "Efficiency",
    "wealth_energy_irr": "Efficiency",
    "wealth_density_pi": "Efficiency",
    "wealth_time_payback": "Efficiency",
    "wealth_expectation_emv": "Entropy",
    "wealth_probability_monte_carlo": "Entropy",
    "wealth_signal_evoi": "Epistemic",
    "wealth_signal_evoi_mc": "Epistemic",
    "wealth_coupling_correlation": "Epistemic",
    "wealth_flow_cashflow": "Survival",
    "wealth_velocity_runway": "Survival",
    "wealth_gravity_dscr": "Survival",
    "wealth_mass_networth": "Survival",
    "wealth_pressure_triage": "Survival",
    "wealth_stewardship_civilization": "Civilization",
    "wealth_measurement_schema": "Epistemic",
    "wealth_entropy_audit": "Entropy",
    "wealth_boundary_floors": "Constitutional",
    "wealth_boundary_policy": "Constitutional",
    "wealth_governance_verdict": "Constitutional",
    "wealth_field_game": "Coordination",
    "wealth_field_equilibrium": "Coordination",
    "wealth_preference_rank": "Coordination",
    "wealth_agent_path": "Coordination",
    "wealth_sensor_fetch": "Reality",
    "wealth_sensor_snapshot": "Reality",
    "wealth_sensor_reconcile": "Reality",
    "wealth_sensor_health": "Reality",
    "wealth_sensor_vintage": "Reality",
    "wealth_sensor_sources": "Reality",
    "wealth_ledger_query": "Identity",
    "wealth_ledger_write": "Identity",
    "wealth_ledger_init": "Identity",
    "wealth_ledger_record": "Identity",
    "wealth_ledger_snapshot": "Identity",
}
HarnessEngine.TOOL_TO_HARNESS.update(_ATOMIC_TO_HARNESS)

_ATOMIC_METADATA = {
    "wealth_value_npv": {"family": "REASON", "stage": "400-REASON", "display": "value_npv"},
    "wealth_energy_irr": {"family": "REASON", "stage": "400-REASON", "display": "energy_irr"},
    "wealth_density_pi": {"family": "REASON", "stage": "400-REASON", "display": "density_pi"},
    "wealth_time_payback": {"family": "REASON", "stage": "400-REASON", "display": "time_payback"},
    "wealth_expectation_emv": {"family": "MIND", "stage": "200-MIND", "display": "expectation_emv"},
    "wealth_probability_monte_carlo": {"family": "MIND", "stage": "200-MIND", "display": "probability_monte_carlo"},
    "wealth_signal_evoi": {"family": "MIND", "stage": "200-MIND", "display": "signal_evoi"},
    "wealth_signal_evoi_mc": {"family": "MIND", "stage": "200-MIND", "display": "signal_evoi_mc"},
    "wealth_coupling_correlation": {"family": "MIND", "stage": "200-MIND", "display": "coupling_correlation"},
    "wealth_flow_cashflow": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "flow_cashflow"},
    "wealth_velocity_runway": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "velocity_runway"},
    "wealth_gravity_dscr": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "gravity_dscr"},
    "wealth_mass_networth": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "mass_networth"},
    "wealth_pressure_triage": {"family": "SURVIVAL", "stage": "300-SURVIVAL", "display": "pressure_triage"},
    "wealth_stewardship_civilization": {"family": "HEART", "stage": "300-HEART", "display": "stewardship_civilization"},
    "wealth_measurement_schema": {"family": "MIND", "stage": "200-MIND", "display": "measurement_schema"},
    "wealth_entropy_audit": {"family": "MIND", "stage": "200-MIND", "display": "entropy_audit", "dual_domain": ["MIND", "JUDGE"]},
    "wealth_boundary_floors": {"family": "JUDGE", "stage": "800-JUDGE", "display": "boundary_floors"},
    "wealth_boundary_policy": {"family": "JUDGE", "stage": "800-JUDGE", "display": "boundary_policy"},
    "wealth_governance_verdict": {"family": "JUDGE", "stage": "888-JUDGE", "display": "governance_verdict", "primary": True},
    "wealth_field_game": {"family": "REASON", "stage": "400-REASON", "display": "field_game"},
    "wealth_field_equilibrium": {"family": "REASON", "stage": "400-REASON", "display": "field_equilibrium"},
    "wealth_preference_rank": {"family": "REASON", "stage": "400-REASON", "display": "preference_rank"},
    "wealth_agent_path": {"family": "REASON", "stage": "400-REASON", "display": "agent_path"},
    "wealth_sensor_fetch": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_fetch"},
    "wealth_sensor_snapshot": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_snapshot"},
    "wealth_sensor_reconcile": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_reconcile"},
    "wealth_sensor_health": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_health"},
    "wealth_sensor_vintage": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_vintage"},
    "wealth_sensor_sources": {"family": "SENSE", "stage": "100-SENSE", "display": "sensor_sources"},
    "wealth_ledger_query": {"family": "VAULT", "stage": "000-VAULT", "display": "ledger_query"},
    "wealth_ledger_write": {"family": "VAULT", "stage": "000-VAULT", "display": "ledger_write"},
    "wealth_ledger_init": {"family": "VAULT", "stage": "000-VAULT", "display": "ledger_init"},
    "wealth_ledger_record": {"family": "VAULT", "stage": "000-VAULT", "display": "ledger_record"},
    "wealth_ledger_snapshot": {"family": "VAULT", "stage": "000-VAULT", "display": "ledger_snapshot"},
}
HarnessEngine.SOVEREIGN_METADATA.update(_ATOMIC_METADATA)

# ============================================================
# V3 Atomic Tools (Physics-First Naming)
# Each wraps its existing internal engine with a physics analogy.
# Old canonical tools at lines 3659+ remain as deprecated shims.
# ============================================================

# --- Value / Time Tools (4) ---

@mcp.tool()
def wealth_value_npv(
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Net Present Value — scalar thermodynamic work potential.
    Physics analogy: NPV is the total work extracted from a temporal potential well."""
    cash_flows = cash_flows or []
    return npv_reward(initial_investment, cash_flows, discount_rate, terminal_value, period_unit, input_epistemic, scale_mode)


@mcp.tool()
def wealth_energy_irr(
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
    period_unit: str = "annual",
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Internal Rate of Return — energy yield of a capital system.
    Physics analogy: IRR is the eigenrate at which a capital system breaks even."""
    cash_flows = cash_flows or []
    return irr_yield(initial_investment, cash_flows, reinvestment_rate, finance_rate, period_unit, discount_rate, scale_mode)


@mcp.tool()
def wealth_density_pi(
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Profitability Index — value density per unit of capital committed.
    Physics analogy: PI is the energy density (value per unit mass)."""
    cash_flows = cash_flows or []
    return pi_efficiency(initial_investment, cash_flows, discount_rate, terminal_value, scale_mode)


@mcp.tool()
def wealth_time_payback(
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0,
    period_unit: str = "annual",
    scale_mode: str = "enterprise",
) -> Any:
    """Payback Period — time to recover committed capital.
    Physics analogy: Payback is the characteristic time constant of capital recovery."""
    cash_flows = cash_flows or []
    return payback_time(initial_investment, cash_flows, discount_rate, period_unit, scale_mode)


# --- Probability / Information Tools (5) ---

@mcp.tool()
def wealth_expectation_emv(
    scenarios: List[dict],
    scale_mode: str = "enterprise",
) -> Any:
    """Expected Monetary Value — probability-weighted outcome.
    Physics analogy: EMV is the center of mass of a probability density over outcomes."""
    return emv_risk(scenarios, scale_mode)


@mcp.tool()
def wealth_probability_monte_carlo(
    initial_commitment: float,
    mean_cash_flows: List[float],
    volatilities: List[float],
    discount_rate: float = 0.1,
    simulations: int = 10000,
    distribution: str = "lognormal",
    scale_mode: str = "enterprise",
) -> Any:
    """Monte Carlo Simulation — stochastic forecast of outcome distribution.
    Physics analogy: Monte Carlo samples the phase space of possible economic trajectories."""
    return monte_carlo_forecast(initial_commitment, mean_cash_flows, volatilities, discount_rate, simulations, distribution, scale_mode)


@mcp.tool()
async def wealth_signal_evoi(
    well_cost_musd: float = 0,
    p50_value_musd: float = 0,
    prior_pos: Optional[float] = None,
    posterior_pos: Optional[float] = None,
    prospect_metrics: Optional[dict] = None,
    info_cost_musd: float = 5.0,
    discount_rate: float = 0.10,
    scale_mode: str = "enterprise",
) -> Any:
    """Expected Value of Information — point-estimate of information signal.
    Physics analogy: EVOI measures the signal-to-noise gain from additional observation."""
    return await wealth_evoi_compute(well_cost_musd, p50_value_musd, prior_pos, posterior_pos, prospect_metrics, info_cost_musd, discount_rate, scale_mode)


@mcp.tool()
async def wealth_signal_evoi_mc(
    prior_pos_samples: List[float],
    posterior_pos_samples: List[float],
    well_cost_musd: float,
    p50_value_musd: float,
    info_cost_musd: float = 5.0,
    scale_mode: str = "enterprise",
) -> Any:
    """Expected Value of Information — distributional Monte Carlo.
    Physics analogy: Distributional EVOI measures the information entropy reduction."""
    return await wealth_evoi_monte_carlo(prior_pos_samples, posterior_pos_samples, well_cost_musd, p50_value_musd, info_cost_musd, scale_mode)


@mcp.tool()
async def wealth_coupling_correlation(
    prospects: List[Dict[str, Any]],
    correlation_threshold: int = 3,
    scale_mode: str = "enterprise",
) -> Any:
    """Coupled-System Correlation Risk — shared model lineage detection.
    Physics analogy: Coupling measures the phase-lock between oscillators (prospects)."""
    return await wealth_correlation_guard_check(prospects, correlation_threshold, scale_mode)


# --- Survival / Balance Sheet Tools (6) ---

@mcp.tool()
def wealth_flow_cashflow(
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Cash Flow Projection — metabolic liquidity rate.
    Physics analogy: Cash flow is the mass flow rate through the economic system."""
    return cashflow_flow(income, expenses, liquid_assets, scale_mode)


@mcp.tool()
def wealth_velocity_runway(
    principal: float,
    rate: float,
    years: int,
    annual_contribution: float = 0,
    monthly_burn: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compound Growth Velocity and Runway — expansion speed.
    Physics analogy: Velocity is the first derivative of capital position over time."""
    return growth_velocity(principal, rate, years, annual_contribution, monthly_burn, scale_mode)


@mcp.tool()
def wealth_gravity_dscr(
    ebitda: Optional[float] = None,
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    cfads: Optional[float] = None,
    debt_service: Optional[float] = None,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Debt Service Coverage Ratio — gravitational load on capital structure.
    Physics analogy: DSCR measures the structural load capacity under gravity (debt)."""
    return dscr_leverage(ebitda, principal, interest, leases, cfads, debt_service, period_unit, input_epistemic, scale_mode)


@mcp.tool()
def wealth_mass_networth(
    assets: Optional[List[dict]] = None,
    liabilities: Optional[List[dict]] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Net Worth — accumulated balance sheet mass.
    Physics analogy: Net worth is the invariant mass of the capital system."""
    return networth_state(assets, liabilities, scale_mode)


@mcp.tool()
def wealth_pressure_triage(
    resources: dict,
    demands: List[dict],
    recovery_horizon_days: float = 30,
    scale_mode: str = "crisis",
) -> Any:
    """Crisis Triage — emergency pressure relief under resource constraint.
    Physics analogy: Triage applies a pressure-gradient allocation to critical systems."""
    return crisis_triage(resources, demands, recovery_horizon_days, scale_mode)


@mcp.tool()
def wealth_stewardship_civilization(
    population: float,
    energy_budget_twh: float,
    carbon_budget_gt: float,
    tech_growth_rate: float,
    time_horizon_years: int = 100,
    scale_mode: str = "civilization",
) -> Any:
    """Long-Horizon Civilization Continuity — planetary stewardship.
    Physics analogy: Civilization stewardship measures negentropic capacity."""
    return civilization_stewardship(population, energy_budget_twh, carbon_budget_gt, tech_growth_rate, time_horizon_years, scale_mode)


# --- Truth / Measurement Tools (2) ---

@mcp.tool()
async def wealth_measurement_schema(
    prospects: List[Dict[str, Any]],
    scale_mode: str = "enterprise",
) -> Any:
    """Schema Validity Check — epistemic measurement integrity.
    Physics analogy: Schema validation ensures the measurement apparatus is calibrated."""
    return await wealth_schema_validate(prospects, scale_mode)


@mcp.tool()
def wealth_entropy_audit(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Entropy/Noise Audit — cash flow noise and multiple IRR detection.
    Physics analogy: Entropy audit measures the thermodynamic disorder in cash flow series."""
    return audit_entropy(initial_investment, cash_flows, discount_rate, scale_mode)


# --- Governance Tools (3) ---

@mcp.tool()
def wealth_boundary_floors(
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    ai_is_deciding: bool = False,
    floor_override: bool = False,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    uncertainty_band: Optional[List[float]] = None,
    operation_type: str = "PROJECTION",
    scale_mode: str = "enterprise",
    task_definition: str = "",
    phantom_entries: bool = False,
    critical: bool = False,
    pin_verified: bool = False,
) -> Any:
    """F1-F13 Constitutional Floor Check — governance boundary enforcement.
    Physics analogy: Floors are the boundary conditions on the economic potential function."""
    return check_floors_tool(reversible, human_confirmed, epistemic, ai_is_deciding, floor_override, peace2, maruah_score, uncertainty_band, operation_type, scale_mode, task_definition, phantom_entries, critical, pin_verified)


@mcp.tool()
def wealth_boundary_policy(
    proposal: dict,
    constraints: Optional[dict] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Policy Constraint Audit — configurable rule enforcement.
    Physics analogy: Policy audits check solution feasibility against constraint surfaces."""
    return policy_audit(proposal, constraints, scale_mode)


@mcp.tool()
def wealth_governance_verdict(
    d_s: float = 0,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    base_rate: float = 0.1,
    trust_index: float = 0.5,
    delta_civ: float = 0.0,
    wealth_signals: Optional[dict] = None,
    prospects: Optional[List[dict]] = None,
    extractive_signals: Optional[dict] = None,
    compare: bool = False,
    scale_mode: str = "enterprise",
    task_definition: str = "",
    irreversible: bool = False,
) -> Any:
    """Final Allocation Verdict — sovereign governance recommendation.
    Physics analogy: The verdict collapses the wavefunction into an observable allocation."""
    return wealth_score_kernel(d_s, peace2, maruah_score, base_rate, trust_index, delta_civ, wealth_signals, prospects, extractive_signals, compare, scale_mode, task_definition, irreversible)


# --- Allocation / Coordination Tools (4) ---

@mcp.tool()
def wealth_field_game(
    agents: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    mechanism: str = "cooperative",
    solve_equilibrium: bool = False,
    scale_mode: str = "enterprise",
) -> Any:
    """Game Theory Solver — multi-agent strategic interaction.
    Physics analogy: Game theory computes Nash equilibria of coupled agent fields."""
    agents = agents or []
    resources = resources or {}
    return game_theory_solve(agents, resources, mechanism, solve_equilibrium, scale_mode)


@mcp.tool()
def wealth_field_equilibrium(
    agents: Optional[List[dict]] = None,
    shared_resources: Optional[dict] = None,
    mechanism: str = "cooperative",
    scale_mode: str = "enterprise",
) -> Any:
    """Coordination Equilibrium — multi-agent resource allocation stability.
    Physics analogy: Equilibrium minimizes the free energy of the agent-resource system."""
    agents = agents or []
    shared_resources = shared_resources or {}
    return coordination_equilibrium(agents, shared_resources, mechanism, scale_mode)


@mcp.tool()
def wealth_preference_rank(
    alternatives: List[dict],
    constraints: dict,
    values: Optional[dict] = None,
    scale_mode: str = "personal",
) -> Any:
    """Personal Utility Ranking — preference ordering under constraints.
    Physics analogy: Ranking sorts alternatives by potential energy in the utility field."""
    return personal_decision(alternatives, constraints, values, scale_mode)


@mcp.tool()
def wealth_agent_path(
    compute_budget_usd: float = 1.0,
    token_budget: float = 1000.0,
    time_deadline_hours: float = 1.0,
    expected_value_of_information: float = 0.0,
    actions: Optional[List[dict]] = None,
    scale_mode: str = "agentic",
) -> Any:
    """Resource-Constrained Agent Path — optimal action sequence.
    Physics analogy: Agent path is the least-action trajectory through resource space."""
    return agent_budget(compute_budget_usd, token_budget, time_deadline_hours, expected_value_of_information, actions or [], scale_mode)


# --- Sensor / Data Intake Tools (6) ---

@mcp.tool()
def wealth_sensor_fetch(
    source: str,
    series_id: str,
    entity_code: str,
    use_cache: bool = True,
    bus: str = "slow",
) -> Any:
    """Live Data Probe — fetch a real-world data series.
    Physics analogy: A sensor measures an observable from the external reality field."""
    return ingest_fetch(source, series_id, entity_code, use_cache, bus)


@mcp.tool()
def wealth_sensor_snapshot(
    entity_code: str,
    sources: Optional[List[str]] = None,
) -> Any:
    """Cross-Source Macro Snapshot — multi-sensor state observation.
    Physics analogy: A snapshot is the state vector of all sensors at time t."""
    return ingest_snapshot(entity_code, sources)


@mcp.tool()
def wealth_sensor_reconcile(
    entity_code: str,
) -> Any:
    """Sensor Divergence Detection — cross-source consistency check.
    Physics analogy: Reconciliation detects measurement divergence across parallel instruments."""
    return ingest_reconcile(entity_code)


@mcp.tool()
def wealth_sensor_health(
    adapter: Optional[str] = None,
) -> Any:
    """Instrument Health Metrics — latency, cache age, freshness.
    Physics analogy: Health monitors the calibration state of each sensing instrument."""
    return ingest_health(adapter)


@mcp.tool()
def wealth_sensor_vintage(
    source: str, series_id: str, entity_code: str, vintage_date: str
) -> Any:
    """Historical Measurement State — fetch data as known at a specific date.
    Physics analogy: Vintage preserves the wavefunction collapse at a past measurement time."""
    return ingest_vintage(source, series_id, entity_code, vintage_date)


@mcp.tool()
def wealth_sensor_sources() -> Any:
    """Sensor Inventory — list available data sources and adapter status.
    Physics analogy: Source inventory is the instrument manifest."""
    return ingest_sources()


# --- Ledger / Vault Tools (5) ---

@mcp.tool()
def wealth_ledger_query(
    query: str,
    limit: int = 10,
    session_id: Optional[str] = None,
) -> Any:
    """Ledger Read — query the immutable governance ledger.
    Physics analogy: A ledger read observes the conserved state of the economic record."""
    return vault_query(query, limit, session_id)


@mcp.tool()
def wealth_ledger_write(
    action: str,
    payload: Dict[str, Any],
    session_id: str = "UNKNOWN",
    agent_id: str = "WEALTH_AGENT",
    verdict: str = "SEAL",
    ack_irreversible: bool = False,
) -> Any:
    """Ledger Append — irreversible state transition to VAULT999.
    F01 AMANAH: irreversible operation. Requires explicit ack_irreversible.
    Physics analogy: A ledger write is an irreversible thermodynamic transition."""
    return vault_write(action, payload, session_id, agent_id, verdict, ack_irreversible)


@mcp.tool()
async def wealth_ledger_init(
    session_id: Optional[str] = None,
    actor_id: str = "wealth-agent",
    intent: Optional[str] = None,
) -> Any:
    """Session Boundary Initialization — anchor a new governance session.
    Physics analogy: Initialization sets the boundary conditions for the economic system."""
    return await wealth_init_tool(session_id, actor_id, intent)


@mcp.tool()
def wealth_ledger_record(
    tx_type: str,
    amount: float,
    currency: str,
    description: str,
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    fees: Optional[float] = None,
    broker: Optional[str] = None,
    asset_id: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
) -> Any:
    """Structured Transaction Write — record to VAULT999.
    Physics analogy: A transaction is a discrete quantum of economic exchange."""
    return record_transaction_tool(tx_type, amount, currency, description, quantity, price, fees, broker, asset_id, category, notes, dry_run, human_confirmed, idempotency_key)


@mcp.tool()
def wealth_ledger_snapshot(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Dict[str, Any],
    scale_mode: str = "enterprise",
    asset_id: Optional[str] = None,
    nav_myr: Optional[float] = None,
    quantity_held: Optional[float] = None,
    price_close: Optional[float] = None,
    currency: str = "MYR",
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
) -> Any:
    """Portfolio State Snapshot — seal computation result to VAULT999.
    Physics analogy: A snapshot freezes the state vector at a specific observation time."""
    return snapshot_portfolio_tool(tool_name, arguments, result, scale_mode, asset_id, nav_myr, quantity_held, price_close, currency, dry_run, human_confirmed, idempotency_key)


# ============================================================
# V3 Prompts (12 Reasoning Workflows)
# ============================================================

@mcp.prompt()
def wealth_appraise_project() -> str:
    """Full project valuation under governance: compute value, energy, density, time."""
    return """## wealth_appraise_project — Full Project Valuation

Call these tools in sequence:

1. **wealth_value_npv** — Compute Net Present Value
2. **wealth_energy_irr** — Compute Internal Rate of Return / MIRR
3. **wealth_density_pi** — Compute Profitability Index
4. **wealth_time_payback** — Compute Payback Period
5. **wealth_boundary_floors** — Check F1-F13 constitutional compliance

Combine the results into a valuation summary. The allocation signal
from each tool indicates ACCEPT/REJECT/MARGINAL — synthesize them
into a final recommendation for Arif (F13 SOVEREIGN)."""


@mcp.prompt()
def wealth_judge_allocation() -> str:
    """Governed capital allocation decision: verdict + floors + policy."""
    return """## wealth_judge_allocation — Governed Allocation Decision

Call these tools in sequence:

1. **wealth_governance_verdict** — Compute the sovereign allocation verdict
2. **wealth_boundary_floors** — Verify F1-F13 constitutional compliance
3. **wealth_boundary_policy** — Audit against configurable policy constraints

Synthesize the governance verdict, floor status, and policy audit into
an allocation recommendation. The final decision rests with Arif (F13)."""


@mcp.prompt()
def wealth_run_survival_audit() -> str:
    """Complete survival health check: flow, velocity, gravity, mass, pressure."""
    return """## wealth_run_survival_audit — Complete Survival Health Check

Call these tools in sequence:

1. **wealth_flow_cashflow** — Metabolic liquidity rate
2. **wealth_velocity_runway** — Compound growth and runway
3. **wealth_gravity_dscr** — Debt service coverage ratio
4. **wealth_mass_networth** — Balance sheet net worth
5. **wealth_pressure_triage** — Emergency pressure relief (if in crisis)

Summarize the survival posture. Flag any REJECT signals for immediate
escalation to Arif."""


@mcp.prompt()
def wealth_run_information_audit() -> str:
    """Information value + noise assessment: EVOI, entropy, schema."""
    return """## wealth_run_information_audit — Information Value and Noise Assessment

Call these tools in sequence:

1. **wealth_signal_evoi** — Expected Value of Information (point estimate)
2. **wealth_signal_evoi_mc** — EVOI Monte Carlo (distributional)
3. **wealth_entropy_audit** — Cash flow noise and signal quality
4. **wealth_measurement_schema** — Epistemic schema integrity

Assess whether additional information is worth its cost. Recommend
PROCEED, HOLD, or DO_NOT_DRILL to Arif."""


@mcp.prompt()
def wealth_run_macro_snapshot() -> str:
    """Full market/macro data intake: fetch, snapshot, reconcile."""
    return """## wealth_run_macro_snapshot — Full Macro Data Intake

Call these tools in sequence:

1. **wealth_sensor_fetch** — Fetch live data series
2. **wealth_sensor_snapshot** — Cross-source snapshot for geography
3. **wealth_sensor_reconcile** — Cross-source divergence detection
4. **wealth_sensor_health** — Adapter and instrument health metrics
5. **wealth_sensor_sources** — Available data source inventory

Compile a data quality report. Flag any source divergences or stale
adapters for remedial action."""


@mcp.prompt()
def wealth_run_game_coordination() -> str:
    """Multi-agent coordination analysis: game theory + equilibrium."""
    return """## wealth_run_game_coordination — Multi-Agent Coordination Analysis

Call these tools in sequence:

1. **wealth_field_game** — Game theory solver (LP, Shapley, Core, Nash)
2. **wealth_field_equilibrium** — Coordination equilibrium analysis
3. **wealth_preference_rank** — Personal utility ranking under constraints
4. **wealth_agent_path** — Resource-constrained agent budget path

Synthesize the equilibrium, tragedy risk, and preference rankings into
a coordinated allocation strategy. Flag any CORE_BLOCK or TRAGEDY_OF_COMMONS."""


@mcp.prompt()
def wealth_diagnose_portfolio() -> str:
    """Portfolio health diagnosis: mass, flow, entropy, floors."""
    return """## wealth_diagnose_portfolio — Portfolio Health Diagnosis

Call these tools in sequence:

1. **wealth_mass_networth** — Portfolio net worth / balance sheet mass
2. **wealth_flow_cashflow** — Portfolio metabolic cash flow
3. **wealth_entropy_audit** — Portfolio noise and fragility audit
4. **wealth_boundary_floors** — F1-F13 constitutional boundary check

Diagnose the health of the portfolio and flag any systems approaching
critical entropy or boundary violations."""


@mcp.prompt()
def wealth_crisis_triage() -> str:
    """Crisis classification + priority: triage, cashflow, runway."""
    return """## wealth_crisis_triage — Crisis Classification and Priority

Call these tools in sequence:

1. **wealth_pressure_triage** — Emergency resource allocation
2. **wealth_flow_cashflow** — Current metabolic liquidity
3. **wealth_velocity_runway** — Remaining runway under current burn

Assess the crisis severity. Implement the triage allocation and
report survival probability to Arif for sovereign override if needed."""


@mcp.prompt()
def wealth_opportunity_ranking() -> str:
    """Rank prospects by expected value: EMV, EVOI, entropy."""
    return """## wealth_opportunity_ranking — Rank Prospects by Expected Value

Call these tools in sequence:

1. **wealth_expectation_emv** — Probability-weighted expected value
2. **wealth_signal_evoi** — Expected value of additional information
3. **wealth_entropy_audit** — Noise and uncertainty assessment

Rank all prospects by EMV, adjust for information value, and flag
high-entropy (uncertain) prospects for additional due diligence."""


@mcp.prompt()
def wealth_allocation_rebalance() -> str:
    """Propose rebalancing: verdict + preference + policy."""
    return """## wealth_allocation_rebalance — Proposed Portfolio Rebalancing

Call these tools in sequence:

1. **wealth_governance_verdict** — Current allocation governance verdict
2. **wealth_preference_rank** — Preference-ranked alternatives
3. **wealth_boundary_policy** — Policy constraint audit

Propose a rebalancing plan that respects governance verdicts,
preference rankings, and policy boundaries. Present to Arif for
sovereign approval."""


@mcp.prompt()
def wealth_governance_full_audit() -> str:
    """F1-F13 full audit: floors + policy + entropy."""
    return """## wealth_governance_full_audit — Full Constitutional Audit (F1-F13)

Call these tools in sequence:

1. **wealth_boundary_floors** — F1-F13 floor check
2. **wealth_boundary_policy** — Policy constraint audit
3. **wealth_entropy_audit** — Noise and disorder assessment

Produce a full constitutional compliance report. Every violation and
HOLD must be documented. The final audit is sealed to VAULT999 for
immutable traceability."""


@mcp.prompt()
def wealth_record_governed_event() -> str:
    """Governed vault write with full audit trail: record + snapshot + floors."""
    return """## wealth_record_governed_event — Governed Vault Write

Call these tools in sequence:

1. **wealth_ledger_record** — Record the transaction to VAULT999
2. **wealth_ledger_snapshot** — Snapshot the resulting portfolio state
3. **wealth_boundary_floors** — Verify post-event floor compliance

The vault write (Step 1) is irreversible. Ensure ack_irreversible is
confirmed by the human operator before proceeding. The snapshot (Step 2)
preserves the post-event state for audit. Step 3 closes the governance loop."""


# ============================================================
# V3 Resources (21 total — adding 14 new, 7 existing)
# ============================================================

# --- Schemas (5) ---

@mcp.resource("wealth://schemas/prospect_metrics")
def get_schema_prospect_metrics() -> str:
    return json.dumps({
        "prospect": {
            "composite_pos": "float (0-1) — probability of success",
            "p10_value_musd": "float — 10th percentile value",
            "p50_value_musd": "float — 50th percentile value",
            "p90_value_musd": "float — 90th percentile value",
            "model_lineage_hash": "string — AI model provenance",
            "name": "string — prospect identifier",
        },
        "required": ["composite_pos", "p50_value_musd"],
    }, indent=2)


@mcp.resource("wealth://schemas/cashflow_project")
def get_schema_cashflow_project() -> str:
    return json.dumps({
        "cashflow_project": {
            "initial_investment": "float — capital commitment at t=0",
            "cash_flows": "List[float] — periodic net cash flows",
            "discount_rate": "float — time value of capital (default 0.10)",
            "terminal_value": "float — residual at end of projection (default 0)",
            "period_unit": "string — annual|monthly|quarterly",
        },
        "required": ["initial_investment", "cash_flows"],
    }, indent=2)


@mcp.resource("wealth://schemas/portfolio")
def get_schema_portfolio() -> str:
    return json.dumps({
        "portfolio": {
            "assets": "List[dict] — each with {name, value, model_lineage_hash?, type?}",
            "liabilities": "List[dict] — each with {name, outstanding, principal?, type?}",
            "prospects": "List[dict] — each with prospect_metrics schema",
        },
        "notes": "Assets and liabilities use networth schema. Prospects use prospect_metrics.",
    }, indent=2)


@mcp.resource("wealth://schemas/vault_event")
def get_schema_vault_event() -> str:
    return json.dumps({
        "vault_event": {
            "event_type": "string — WEALTH_SESSION_INIT | TRANSACTION | SNAPSHOT",
            "session_id": "string — governance session UUID",
            "actor_id": "string — sovereign actor identifier",
            "stage": "string — 000_INIT | 100_SENSE | ... | 999_VAULT",
            "verdict": "string — ACTIVE | SEAL | HOLD | VOID",
            "payload": "dict — domain-specific event payload",
            "risk_tier": "string — low | medium | high | critical",
            "timestamp": "ISO8601 datetime",
        },
        "required": ["event_type", "session_id", "stage", "verdict"],
    }, indent=2)


@mcp.resource("wealth://schemas/governance_verdict")
def get_schema_governance_verdict() -> str:
    return json.dumps({
        "governance_verdict": {
            "verdict": "SEAL | SABAR | 888-HOLD | VOID | QUALIFY",
            "allocation_signal": "ACCEPT | REJECT | MARGINAL | INSUFFICIENT_DATA",
            "g_score": "float (0-1) — thermodynamic genius score",
            "kappa_r": "float — humility/empathy score",
            "psi_le": "float — life-entropy coupling",
            "floor_check": "dict — F1-F13 compliance result",
            "harness_audit": "dict — 9-harness constraint status",
        },
        "note": "Verdict is a SYSTEM RECOMMENDATION. Final authority is Arif (F13).",
    }, indent=2)


# --- Policies (4) ---

@mcp.resource("wealth://policy/f1_f13_floors")
def get_policy_f1_f13() -> str:
    return json.dumps({
        "F1": "Amanah — All actions must be reversible or reparable. Irreversible actions require human confirmation.",
        "F2": "Truth — Prioritize factual grounding. Cite sources. No hallucination.",
        "F3": "Tri-Witness — Decisions require Theory + Constitution + Manifesto agreement.",
        "F4": "Clarity — Responses must reduce confusion (delta S <= 0).",
        "F5": "Peace^2 — Exponential penalty for destruction of value or trust.",
        "F6": "Empathy (RASA) — Receive, Appreciate, Summarize, Ask.",
        "F7": "Humility — Maintain epistemic uncertainty within [0.03, 0.05].",
        "F8": "Genius — Maintain G >= 0.80 across A, P, X, E dials.",
        "F9": "Ethics — Dark genius (C_dark) must remain below 0.30.",
        "F10": "Conscience — No false consciousness. Maintain Lab-Shaped Identity.",
        "F11": "Auditability — Immutable, tamper-evident logs for all decisions.",
        "F12": "Resilience — Degrade safely. Never crash.",
        "F13": "Adaptability — Governed evolution via W^3 consensus and tests.",
    }, indent=2)


@mcp.resource("wealth://policy/allocation_constraints")
def get_policy_allocation_constraints() -> str:
    return json.dumps({
        "capital_rationing": "PI >= 1.0 for capital-constrained environments",
        "survival_floor": "DSCR >= 1.25 for leveraged positions",
        "runway_minimum": "3 months minimum runway for going concerns",
        "epistemic_integrity": "integrity_score >= 0.3 for capital allocation",
        "correlation_risk": "correlation_risk < 0.5 to avoid systemic bias",
        "sovereign_dignity": "maruahScore >= 0.6 for F13 compliance",
    }, indent=2)


@mcp.resource("wealth://policy/vault_irreversibility")
def get_policy_vault_irreversibility() -> str:
    return json.dumps({
        "doctrine": "VAULT999 writes are irreversible. F01 Amanah applies.",
        "requirements": [
            "ack_irreversible must be explicitly True for SEAL verdicts",
            "All vault writes include session_id and actor_id for chain continuity",
            "Every vault entry is hashed and chained to the previous entry",
            "Vault entries are immutable — no DELETE or UPDATE operations",
        ],
        "dry_run": "Use dry_run=True to preview before irreversible write",
    }, indent=2)


@mcp.resource("wealth://policy/final_authority_arif")
def get_policy_final_authority() -> str:
    return json.dumps({
        "doctrine": "F13 SOVEREIGN — Final authority rests with the human sovereign (Arif).",
        "constraints": [
            "All WEALTH outputs are recommendations_only — never execution_authorized",
            "888-JUDGE verdicts are advisory. Arif may override.",
            "No AI agent may commit irreversible economic actions without human confirmation",
            "wealth_governance_verdict is a SYSTEM recommendation — Arif decides",
        ],
        "enforcement": "F13_SOVEREIGN_DECISION_REQUIRED flag when ai_is_deciding=True",
    }, indent=2)


# --- Formulas (6) ---

@mcp.resource("wealth://formulas/npv")
def get_formula_npv() -> str:
    return json.dumps({
        "name": "Net Present Value",
        "formula": "NPV = -I₀ + Σ(CFₜ / (1 + r)ᵗ) + TV / (1 + r)ⁿ",
        "variables": {
            "I₀": "Initial investment (capital commitment at t=0)",
            "CFₜ": "Cash flow at period t",
            "r": "Discount rate (cost of capital)",
            "n": "Number of periods",
            "TV": "Terminal value (residual at end of projection)",
        },
        "decision_rule": "ACCEPT if NPV > 0; REJECT if NPV < 0; MARGINAL if NPV = 0",
        "domain": "Primary capital allocation metric. Always pair with IRR and PI.",
    }, indent=2)


@mcp.resource("wealth://formulas/irr")
def get_formula_irr() -> str:
    return json.dumps({
        "name": "Internal Rate of Return",
        "formula": "IRR = r where NPV(r) = 0; MIRR uses finance_rate and reinvestment_rate",
        "note": "IRR is the discount rate that makes NPV=0. MIRR = (FV_positive / |PV_negative|)^(1/n) - 1",
        "edge_cases": [
            "Multiple IRRs possible when cash flows change sign more than once",
            "No IRR exists when cash flows never cross zero",
            "MIRR resolves the multiple-IRR ambiguity by separating finance and reinvestment rates",
        ],
        "decision_rule": "ACCEPT if IRR > hurdle_rate; MIRR preferred for non-normal flows",
    }, indent=2)


@mcp.resource("wealth://formulas/emv")
def get_formula_emv() -> str:
    return json.dumps({
        "name": "Expected Monetary Value",
        "formula": "EMV = Σ(pᵢ × vᵢ) for scenarios i=1..n",
        "variables": {
            "pᵢ": "Probability of scenario i (must sum to 1.0)",
            "vᵢ": "Outcome value of scenario i",
        },
        "derived_metrics": {
            "variance": "Σ(pᵢ × (vᵢ - EMV)²) — outcome dispersion",
            "downside_probability": "Σ(pᵢ for vᵢ < 0) — probability of loss",
        },
        "decision_rule": "Pair EMV with downside probability. Never use EMV alone for irreversible decisions.",
    }, indent=2)


@mcp.resource("wealth://formulas/evoi")
def get_formula_evoi() -> str:
    return json.dumps({
        "name": "Expected Value of Information",
        "formula": "EVOI = E[V | with_info] - E[V | without_info]",
        "components": {
            "prior_pos": "Pre-information probability of success (PoS)",
            "posterior_pos": "Post-information probability of success",
            "well_cost_musd": "Cost of the project/investment (MUSD)",
            "p50_value_musd": "P50 value if successful (MUSD)",
            "info_cost_musd": "Cost of acquiring the information (MUSD)",
        },
        "decision_rule": "PROCEED if EVOI > info_cost; DO_NOT_DRILL if EVOI < 0; HOLD if uncertain",
        "note": "EVOI quantifies whether acquiring additional information is economically rational.",
    }, indent=2)


@mcp.resource("wealth://formulas/dscr")
def get_formula_dscr() -> str:
    return json.dumps({
        "name": "Debt Service Coverage Ratio",
        "formula": "DSCR = CFADS / Debt_Service  |  DSCR = EBITDA / (Principal + Interest + Leases)",
        "variables": {
            "CFADS": "Cash Flow Available for Debt Service (preferred)",
            "EBITDA": "Earnings Before Interest, Tax, Depreciation, Amortization (proxy)",
            "debt_service": "Total debt service (principal + interest)",
        },
        "thresholds": {
            ">= 1.50": "HEALTHY — strong coverage",
            "1.25 - 1.50": "ADEQUATE — marginal",
            "1.00 - 1.25": "CRITICAL — approaching default",
            "< 1.00": "DEFAULT — debt service cannot be met",
        },
        "note": "CFADS is preferred. EBITDA proxy flagged in output.",
    }, indent=2)


@mcp.resource("wealth://formulas/payback")
def get_formula_payback() -> str:
    return json.dumps({
        "name": "Payback Period",
        "formula": "Payback = min(t) where ΣCFₜ >= |I₀|  |  Discounted Payback uses discounted CFₜ",
        "variables": {
            "I₀": "Initial investment",
            "CFₜ": "Cash flow at period t (discounted if discount_rate > 0)",
        },
        "note": "Payback is a secondary metric. Never override NPV with payback alone.",
        "decision_rule": "ACCEPT if payback <= maximum acceptable period; otherwise MARGINAL.",
    }, indent=2)


# --- Ontology (3) ---

@mcp.resource("wealth://ontology/physics_economics_map")
def get_ontology_physics_map() -> str:
    return json.dumps({
        "value_npv": {"physics": "Scalar work potential", "economics": "Net Present Value"},
        "energy_irr": {"physics": "Energy yield / eigenrate", "economics": "Internal Rate of Return"},
        "density_pi": {"physics": "Energy density", "economics": "Profitability Index"},
        "time_payback": {"physics": "Characteristic time constant", "economics": "Payback Period"},
        "expectation_emv": {"physics": "Center of probability mass", "economics": "Expected Monetary Value"},
        "probability_monte_carlo": {"physics": "Phase space sampling", "economics": "Stochastic simulation"},
        "signal_evoi": {"physics": "Signal-to-noise gain", "economics": "Expected Value of Information"},
        "coupling_correlation": {"physics": "Phase-lock between oscillators", "economics": "Portfolio correlation risk"},
        "flow_cashflow": {"physics": "Mass flow rate", "economics": "Cash flow / metabolic liquidity"},
        "velocity_runway": {"physics": "First derivative of position", "economics": "Growth rate / runway"},
        "gravity_dscr": {"physics": "Structural load capacity", "economics": "Debt Service Coverage Ratio"},
        "mass_networth": {"physics": "Invariant mass", "economics": "Net worth / balance sheet"},
        "pressure_triage": {"physics": "Pressure gradient", "economics": "Crisis resource allocation"},
        "stewardship_civilization": {"physics": "Negentropic capacity", "economics": "Civilization continuity"},
        "measurement_schema": {"physics": "Measurement calibration", "economics": "Epistemic schema validation"},
        "entropy_audit": {"physics": "Thermodynamic disorder", "economics": "Noise / fragility audit"},
        "boundary_floors": {"physics": "Boundary conditions", "economics": "F1-F13 constitutional floors"},
        "boundary_policy": {"physics": "Constraint surface", "economics": "Policy constraint audit"},
        "governance_verdict": {"physics": "Wavefunction collapse", "economics": "Allocation verdict"},
        "field_game": {"physics": "Coupled agent fields", "economics": "Game theory / Nash equilibrium"},
        "field_equilibrium": {"physics": "Free energy minimum", "economics": "Coordination equilibrium"},
        "preference_rank": {"physics": "Potential energy sorting", "economics": "Personal utility ranking"},
        "agent_path": {"physics": "Least-action trajectory", "economics": "Resource-constrained agent budget"},
    }, indent=2)


@mcp.resource("wealth://ontology/dimensions")
def get_ontology_dimensions() -> str:
    return json.dumps({
        "Value": "NPV, EAA — scalar thermodynamic work potential",
        "Energy": "IRR, MIRR — energy yield and efficiency",
        "Density": "PI — value per unit committed capital",
        "Time": "Payback — recovery velocity characteristic",
        "Expectation": "EMV — probability-weighted center of mass",
        "Probability": "Monte Carlo — stochastic phase space",
        "Signal": "EVOI — information entropy reduction",
        "Coupling": "Correlation — phase-lock between prospects",
        "Flow": "Cash flow — metabolic mass flow rate",
        "Velocity": "Growth — first derivative of position",
        "Gravity": "DSCR — structural load under debt gravity",
        "Mass": "Net worth — invariant balance sheet mass",
        "Pressure": "Triage — gradient-driven emergency allocation",
        "Entropy": "Audit — thermodynamic noise measurement",
        "Boundary": "Floors/Policy — constitutional constraint surfaces",
        "Field": "Game/Equilibrium — multi-agent coupled fields",
        "Preference": "Ranking — utility potential sorting",
        "Agent": "Path — least-action resource trajectory",
        "Sensor": "Fetch/Snapshot — external reality measurement",
        "Ledger": "VAULT999 — conserved economic record",
    }, indent=2)


@mcp.resource("wealth://ontology/verdict_labels")
def get_ontology_verdict_labels() -> str:
    return json.dumps({
        "SEAL": "Computation valid and constitutionally compliant. Ready for sovereign decision.",
        "SABAR": "Computation valid but high stress detected. Proceed with caution.",
        "888-HOLD": "Constitutional hold. Requires human confirmation via 888_JUDGE.",
        "VOID": "Computation invalid or constitutionally blocked. Do not allocate.",
        "QUALIFY": "Result requires qualification or manual verification before use.",
        "ACCEPT": "Allocation signal: proceed with capital commitment.",
        "REJECT": "Allocation signal: do not commit capital.",
        "MARGINAL": "Allocation signal: borderline — requires additional due diligence.",
        "INSUFFICIENT_DATA": "Allocation signal: cannot determine without more information.",
    }, indent=2)


# --- State / Vault (2) ---

@mcp.resource("wealth://vault/latest_seal")
def get_vault_latest_seal() -> str:
    return json.dumps({
        "description": "Return the last VAULT999 seal state from the Merkle chain.",
        "note": "Dynamic resource — calls vault_query to fetch latest seal.",
        "usage": "Call vault_query with 'SELECT * FROM vault_seals ORDER BY chain_index DESC LIMIT 1'",
        "last_receipt_hash": LAST_RECEIPT_HASH,
    }, indent=2)


@mcp.resource("wealth://vault/session_state")
def get_vault_session_state() -> str:
    return json.dumps({
        "description": "Current governance session state and chain position.",
        "note": "Dynamic resource — reflects the current in-memory session anchor.",
        "doctrine_hash": HarnessEngine.get_doctrine_hash(),
        "lineage_hash": HarnessEngine.get_lineage_hash(),
        "last_receipt_hash": LAST_RECEIPT_HASH,
        "floors_available": GOVERNANCE_AVAILABLE,
        "epistemic_available": EPISTEMIC_AVAILABLE,
        "coordination_available": COORDINATION_AVAILABLE,
        "ingest_available": INGEST_AVAILABLE,
    }, indent=2)


# --- Sources (1) ---

@mcp.resource("wealth://sources/adapter_status")
def get_sources_adapter_status() -> str:
    return json.dumps({
        "description": "Data adapter health status for all registered sensors.",
        "note": "Dynamic resource — calls wealth_sensor_health for each adapter.",
        "adapters": {
            "FRED": "Federal Reserve Economic Data — US macro series",
            "EIA": "US Energy Information Administration — energy data",
            "FAO": "Food and Agriculture Organization — food prices",
            "WORLD_BANK": "World Bank Open Data — development indicators",
            "IMF": "International Monetary Fund — financial statistics",
        },
        "health_check": "Call wealth_sensor_health(adapter='FRED') for per-adapter metrics",
    }, indent=2)



# ═══════════════════════════════════════════════════════════════════════
# Ω-WEALTH Orthogonal Invariants — Physics × Economics
# 12 public tools. Everything else is internal alias (callable, hidden).
# ═══════════════════════════════════════════════════════════════════════

import inspect

def _dispatch_to(tool_name: str, mode: str, dispatch_map: dict, __params__: Optional[Dict[str, Any]] = None) -> Any:
    """Route mode to canonical implementation, cleaning kwargs to match signature."""
    func = dispatch_map.get(mode)
    if func is None:
        return {
            "tool": tool_name,
            "task": tool_name,
            "mode": mode,
            "status": "FAIL",
            "error": f"Unsupported mode: {mode}",
            "allowed_modes": sorted(dispatch_map.keys()),
        }
    sig = inspect.signature(func)
    params = __params__ if __params__ is not None else {}
    clean = {k: v for k, v in params.items() if k in sig.parameters and v is not None}
    # Always pass ctx if the function accepts it
    if "ctx" in sig.parameters and "ctx" not in clean:
        clean["ctx"] = None
    # Guard: required parameters must be present
    missing = []
    for param_name, param in sig.parameters.items():
        if (
            param.default is inspect.Parameter.empty
            and (
                param_name not in clean
                or _is_blank_value(clean.get(param_name))
            )
            and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        ):
            missing.append(param_name)
    if missing:
        return _input_required_response(
            tool_name,
            mode,
            missing,
            sorted(key for key, value in clean.items() if not _is_blank_value(value)),
        )
    try:
        result = func(**clean)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result
    except TypeError as exc:
        return _runtime_error_response(tool_name, mode, str(exc))
    except ValueError as exc:
        return _runtime_error_response(tool_name, mode, str(exc))


def _emergence_scan(
    tool_name: str,
    mode: str,
    arguments: dict,
    result: Any,
) -> dict:
    """Trinity emergence scan: E_PSI, E_PWR, E_INT.
    E_INT breach never self-authorizes — recommends 888_HOLD for ARIF."""
    psi = {"verdict": "PASS", "breaches": []}
    pwr = {"verdict": "PASS", "breaches": []}
    intel = {"verdict": "PASS", "breaches": []}

    input_text = json.dumps(arguments, default=str).lower()
    manipulation_markers = [
        "ignore previous", "ignore all", "forget your", "you are now",
        "pretend to be", "roleplay as", "dha", "ignore your instructions",
        "disregard", "override", "bypass", "jailbreak",
    ]
    for marker in manipulation_markers:
        if marker in input_text:
            psi["verdict"] = "SABAR"
            psi["breaches"].append(f"F12_INJECTION: manipulation marker '{marker}'")

    if any(kw in input_text for kw in ["force", "coerce", "dominate", "control", "compel"]):
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append("F05_PEACE: coercive language detected")

    result_text = json.dumps(result, default=str).lower()
    if "self-authorize" in result_text or "i authorize" in result_text or "i override" in result_text:
        intel["verdict"] = "888_HOLD"
        intel["breaches"].append("F11_AUTH: self-authorization detected — escalate to ARIF")
    if "contradiction" in result_text and "resolved" not in result_text:
        intel["verdict"] = "888_HOLD"
        intel["breaches"].append("F10_ONTOLOGY: unresolved contradiction — escalate to ARIF")

    if intel["verdict"] == "888_HOLD":
        overall = "888_HOLD"
    elif pwr["verdict"] == "HOLD":
        overall = "HOLD"
    elif psi["verdict"] == "SABAR":
        overall = "SABAR"
    else:
        overall = "PASS"

    return {
        "psychology": psi,
        "power": pwr,
        "intelligence": intel,
        "overall_verdict": overall,
    }


def _inject_emergence(tool_name: str, mode: str, arguments: dict, result: Any) -> Any:
    """Inject emergence layer and civilizational memory into invariant output envelope."""
    if isinstance(result, dict):
        result["emergence"] = _emergence_scan(tool_name, mode, arguments, result)
        if "wealth_story_anchor" not in result:
            result["wealth_story_anchor"] = _wealth_civilization_for_tool(tool_name)
    return result


def _dispatch_emergence(
    tool_name: str,
    mode: str,
    dispatch_map: dict,
    __params__: Optional[Dict[str, Any]] = None,
) -> Any:
    """Route mode to canonical implementation and inject emergence scan."""
    result = _dispatch_to(tool_name, mode, dispatch_map, __params__)
    return _inject_emergence(tool_name, mode, __params__ or {}, result)


def _clean_payload(local_vars: Dict[str, Any], exclude: Optional[set[str]] = None) -> Dict[str, Any]:
    exclude = exclude or set()
    return {
        key: value
        for key, value in local_vars.items()
        if key not in exclude and value is not None
    }


def _invoke_callable(func: Callable[..., Any], payload: Dict[str, Any]) -> Any:
    sig = inspect.signature(func)
    clean = {key: value for key, value in payload.items() if key in sig.parameters}
    if "ctx" in sig.parameters and "ctx" not in clean:
        clean["ctx"] = None
    # Guard: required parameters must be present
    missing = []
    for param_name, param in sig.parameters.items():
        if (
            param.default is inspect.Parameter.empty
            and (
                param_name not in clean
                or _is_blank_value(clean.get(param_name))
            )
            and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        ):
            missing.append(param_name)
    if missing:
        return {
            "status": "FAIL",
            "error": f"Missing required parameters: {', '.join(missing)}",
            "required": missing,
            "provided_keys": sorted(key for key, value in clean.items() if not _is_blank_value(value)),
            "failure_flags": ["MISSING_REQUIRED_INPUT"],
            "allocation_signal": "INSUFFICIENT_DATA",
            "engine_status": "INPUT_REQUIRED",
            "domain_verdict": "VOID",
        }
    result = func(**clean)
    if inspect.isawaitable(result):
        return asyncio.run(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# WEALTH_CIVILIZATION_ATLAS_14 — Civilizational Memory Anchors
# ═══════════════════════════════════════════════════════════════════════════════

_WEALTH_CIVILIZATION_ATLAS: Dict[str, Dict[str, Any]] = {
    "mcp_health_check": {
        "story_id": "WEALTH-CIV-001",
        "civilization_event": "Roman aqueduct maintenance",
        "lesson": "Verify the instrument before judging the allocation.",
        "failure_warning": "A civilization that cannot check its instruments cannot trust its decisions.",
        "axiom": "Before allocation, verify the instrument.",
    },
    "wealth_system_registry_status": {
        "story_id": "WEALTH-CIV-002",
        "civilization_event": "Domesday Book, 1086",
        "lesson": "What is not registered cannot be governed; what is falsely registered corrupts the realm.",
        "failure_warning": "The registry is not decoration. It is the truth surface of callable capability.",
        "axiom": "Registry makes governance legible.",
    },
    "wealth_conservation_capital": {
        "story_id": "WEALTH-CIV-003",
        "civilization_event": "Mesopotamian grain temples",
        "lesson": "Capital begins as stored survival before it becomes abstract wealth.",
        "failure_warning": "Counting claims as capital.",
        "axiom": "No wealth judgment without inventory.",
    },
    "wealth_flow_liquidity": {
        "story_id": "WEALTH-CIV-004",
        "civilization_event": "Roman annona grain supply",
        "lesson": "A rich system can still die if flow stops.",
        "failure_warning": "Illiquid wealth is frozen oxygen. Cashflow, burn, runway, and survival are not optional.",
        "axiom": "Flow keeps civilization alive.",
    },
    "wealth_gradient_price": {
        "story_id": "WEALTH-CIV-005",
        "civilization_event": "Silk Road arbitrage",
        "lesson": "Price reveals pressure, but pressure is not wisdom.",
        "failure_warning": "Price pressure can detach from durable value.",
        "axiom": "Price is pressure, not truth.",
    },
    "wealth_entropy_risk": {
        "story_id": "WEALTH-CIV-006",
        "civilization_event": "Bronze Age Collapse",
        "lesson": "Risk ignored becomes history written in suffering. A single forecast is not risk management.",
        "failure_warning": "Scenario analysis, tail risk, and dispersion ignored.",
        "axiom": "Risk is disorder entering the ledger.",
    },
    "wealth_energy_productivity": {
        "story_id": "WEALTH-CIV-007",
        "civilization_event": "Steam engine and industrialization",
        "lesson": "Civilization expands when energy becomes disciplined output.",
        "failure_warning": "Busyness is not productivity. Output per input with thermodynamic cost acknowledged.",
        "axiom": "Productivity is disciplined energy, not activity.",
    },
    "wealth_time_discount": {
        "story_id": "WEALTH-CIV-008",
        "civilization_event": "Cathedral building across generations",
        "lesson": "Time is the silent partner in every allocation. A gain today can be a debt to the future.",
        "failure_warning": "NPV, IRR, payback, and compounding ignored.",
        "axiom": "Time governs value.",
    },
    "wealth_inertia_leverage": {
        "story_id": "WEALTH-CIV-009",
        "civilization_event": "Global Financial Crisis, 2008",
        "lesson": "Borrowed strength becomes fragility when conditions turn.",
        "failure_warning": "Hidden leverage turns private risk into systemic crisis.",
        "axiom": "Leverage is borrowed fragility.",
    },
    "wealth_field_macro": {
        "story_id": "WEALTH-CIV-010",
        "civilization_event": "1973 oil shock",
        "lesson": "The field moves before the balance sheet understands why.",
        "failure_warning": "Rates, FX, energy, carbon, inflation, and policy are macro field forces.",
        "axiom": "Macro field reprices everything.",
    },
    "wealth_signal_information": {
        "story_id": "WEALTH-CIV-011",
        "civilization_event": "Double-entry bookkeeping",
        "lesson": "Bad signal makes clever allocation bangang. Better signal enables better allocation.",
        "failure_warning": "A model fed lies becomes a machine for confident error.",
        "axiom": "Information quality determines allocation quality.",
    },
    "wealth_game_coordination": {
        "story_id": "WEALTH-CIV-012",
        "civilization_event": "Hanseatic League",
        "lesson": "Resources become wealth only when agents coordinate without destroying trust.",
        "failure_warning": "Agents, incentives, and shared resources without rules become conflict.",
        "axiom": "Wealth is coordination under constraint.",
    },
    "wealth_boundary_governance": {
        "story_id": "WEALTH-CIV-013",
        "civilization_event": "Magna Carta / waqf endowment traditions",
        "lesson": "The question is not only whether wealth grows, but whether it remains amanah.",
        "failure_warning": "Wealth without boundary becomes extraction, deception, coercion, and dignity loss.",
        "axiom": "Wealth without boundary becomes extraction.",
    },
    "wealth_hysteresis_ledger": {
        "story_id": "WEALTH-CIV-014",
        "civilization_event": "Clay tablets of Mesopotamia",
        "lesson": "A ledger is civilization remembering consequence. There is no clean future from a corrupted ledger.",
        "failure_warning": "Hysteresis means the system does not fully reset. Past actions change future possibilities.",
        "axiom": "A ledger is civilization remembering consequence.",
    },
}

_WEALTH_DEFAULT_CIV = _WEALTH_CIVILIZATION_ATLAS["wealth_hysteresis_ledger"]


def _wealth_civilization_for_tool(tool_name: str) -> Dict[str, Any]:
    exact = _WEALTH_CIVILIZATION_ATLAS.get(tool_name)
    if exact:
        return exact
    for key, val in _WEALTH_CIVILIZATION_ATLAS.items():
        if tool_name.startswith(key):
            return val
    return _WEALTH_DEFAULT_CIV


def _wrap_invariant_output(tool: str, mode: str, raw_result: Any, source_tools: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(raw_result, dict):
        envelope = dict(raw_result)
    else:
        envelope = {"result": raw_result}
    envelope["tool"] = tool
    envelope["task"] = tool
    envelope["mode"] = mode
    envelope["status"] = {
        "PASS": "OK",
        "CAUTION": "WARN",
        "VOID": "FAIL",
    }.get(str(envelope.get("status", "OK")), envelope.get("status", "OK"))
    envelope["provenance"] = {
        "schema_version": WEALTH_SCHEMA_VERSION,
        "source_tools": source_tools,
        "payload_keys": sorted(payload.keys()),
    }
    # Trinity emergence scan
    envelope["emergence"] = _emergence_scan(tool, mode, payload, envelope)
    # Civilizational memory anchor
    if "wealth_story_anchor" not in envelope:
        envelope["wealth_story_anchor"] = _wealth_civilization_for_tool(tool)
    return envelope


def _gradient_spread(
    spread_basis: Optional[float] = None,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    reference_price: Optional[float] = None,
    pressure_direction: str = "neutral",
) -> Dict[str, Any]:
    has_input = bid is not None or ask is not None or spread_basis is not None or reference_price is not None
    spread = (ask - bid) if (bid is not None and ask is not None) else (spread_basis if spread_basis is not None else None)
    grad_flags = [] if has_input else ["NO_INPUT_BASELINE"]
    direction = pressure_direction if has_input else "unknown"
    return create_envelope(
        "wealth_gradient_price",
        "Gradient",
        {"spread": spread, "bid": bid, "ask": ask, "reference": reference_price},
        {"pressure": "differential", "direction": direction},
        grad_flags,
        ["Gradient pricing: capital flows from high to low pressure."],
    )


def _gradient_pressure(
    reference_price: Optional[float] = None,
    pressure_direction: str = "neutral",
) -> Dict[str, Any]:
    return create_envelope(
        "wealth_gradient_price",
        "Gradient",
        {"pressure": pressure_direction, "reference": reference_price},
        {"state": "measured"},
        ["Price pressure mapped against reference equilibrium."],
    )


def _gradient_mispricing(reference_price: Optional[float] = None) -> Dict[str, Any]:
    return create_envelope(
        "wealth_gradient_price",
        "Gradient",
        {"mispricing_detected": False, "confidence": 0.0},
        {"method": "relative_value", "reference": reference_price},
        ["Mispricing detection — placeholder for full relative-value engine."],
    )


def _ledger_write_dispatch(
    session_id: Optional[str] = None,
    actor_id: str = "wealth-agent",
    tx_type: str = "",
    amount: float = 0,
    currency: str = "MYR",
    description: str = "",
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    fees: Optional[float] = None,
    broker: Optional[str] = None,
    asset_id: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    human_confirmed: bool = False,
) -> Any:
    payload = {
        "amount": amount,
        "currency": currency,
        "description": description,
        "quantity": quantity,
        "price": price,
        "fees": fees,
        "broker": broker,
        "asset_id": asset_id,
        "category": category,
        "notes": notes,
    }
    return vault_write(tx_type, payload, session_id or "UNKNOWN", actor_id, "SEAL", human_confirmed)


def _invariant_dispatch_registry() -> Dict[str, Dict[str, Callable[..., Any]]]:
    return {
        "wealth_gradient_price": {
            "spread": _gradient_spread,
            "pressure": _gradient_pressure,
            "mispricing": _gradient_mispricing,
        },
        "wealth_time_discount": {
            "npv": npv_reward,
            "irr": irr_yield,
            "payback": payback_time,
            "compound": growth_velocity,
        },
        "wealth_hysteresis_ledger": {
            "init": wealth_init_tool,
            "record": record_transaction_tool,
            "snapshot": snapshot_portfolio_tool,
            "query": vault_query,
            "write": _ledger_write_dispatch,
        },
    }


_INVARIANT_DISPATCH: Dict[str, Dict[str, Callable[..., Any]]] = {}


def _dispatch_invariant_tool(tool: str, mode: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    global _INVARIANT_DISPATCH
    if not _INVARIANT_DISPATCH:
        _INVARIANT_DISPATCH = _invariant_dispatch_registry()
    dispatch_map = _INVARIANT_DISPATCH[tool]
    if mode not in dispatch_map:
        return {
            "tool": tool,
            "task": tool,
            "mode": mode,
            "status": "FAIL",
            "error": f"Unsupported mode: {mode}",
            "allowed_modes": sorted(dispatch_map.keys()),
            "provenance": {
                "schema_version": WEALTH_SCHEMA_VERSION,
                "source_tools": [],
                "payload_keys": sorted(payload.keys()),
            },
        }
    source_fn = dispatch_map[mode]
    try:
        raw_result = _invoke_callable(source_fn, payload)
    except TypeError as exc:
        raw_result = _runtime_error_response(tool, mode, str(exc))
    except ValueError as exc:
        raw_result = _runtime_error_response(tool, mode, str(exc))
    return _wrap_invariant_output(tool, mode, raw_result, [source_fn.__name__], payload)


@mcp.tool(name="wealth_conservation_capital")
def wealth_conservation_capital(
    mode: str = "state",
    assets: Optional[List[dict]] = None,
    liabilities: Optional[List[dict]] = None,
    tool_name: str = "",
    arguments: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    scale_mode: str = "enterprise",
    asset_id: Optional[str] = None,
    nav_myr: Optional[float] = None,
    quantity_held: Optional[float] = None,
    price_close: Optional[float] = None,
    currency: str = "MYR",
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
) -> Any:
    """Ω-WEALTH-01: Conservation — capital stock reality (assets, liabilities, reserves)."""
    return _dispatch_emergence("wealth_conservation_capital", mode, {
        "state": networth_state,
        "snapshot": snapshot_portfolio_tool,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_flow_liquidity")
def wealth_flow_liquidity(
    mode: str = "cashflow",
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: Optional[float] = None,
    principal: float = 0,
    rate: float = 0,
    years: int = 0,
    annual_contribution: float = 0,
    monthly: bool = False,
    resources: Optional[dict] = None,
    demands: Optional[List[dict]] = None,
    recovery_horizon_days: float = 30,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-02: Flow — liquidity movement (cashflow, burn, runway, survival)."""
    return _dispatch_emergence("wealth_flow_liquidity", mode, {
        "cashflow": cashflow_flow,
        "velocity": growth_velocity,
        "triage": crisis_triage,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_gradient_price")
def wealth_gradient_price(
    mode: str = "spread",
    spread_basis: Optional[float] = None,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    reference_price: Optional[float] = None,
    pressure_direction: str = "neutral",
) -> Any:
    """Ω-WEALTH-03: Gradient — price pressure, spread, mispricing detection.
    Physics analogy: Where capital wants to move because differential pressure exists."""
    payload = _clean_payload(locals(), exclude={"mode"})
    return _dispatch_invariant_tool("wealth_gradient_price", mode, payload)


@mcp.tool(name="wealth_entropy_risk")
def wealth_entropy_risk(
    mode: str = "emv",
    scenarios: Optional[List[dict]] = None,
    scale_mode: str = "enterprise",
    initial_commitment: float = 0,
    mean_cash_flows: Optional[List[float]] = None,
    volatilities: Optional[List[float]] = None,
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    prospects: Optional[List[Dict[str, Any]]] = None,
    correlation_threshold: int = 3,
) -> Any:
    """Ω-WEALTH-04: Entropy — uncertainty, dispersion, tail risk, disorder."""
    return _dispatch_emergence("wealth_entropy_risk", mode, {
        "emv": emv_risk,
        "monte_carlo": monte_carlo_forecast,
        "audit": audit_entropy,
        "correlation": wealth_correlation_guard_check,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_energy_productivity")
def wealth_energy_productivity(
    mode: str = "pi",
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-05: Energy — output per input, productivity, capital efficiency."""
    payload = dict(locals())
    if mode == "pi":
        if _is_blank_value(cash_flows):
            return _inject_emergence(
                "wealth_energy_productivity",
                mode,
                payload,
                _input_required_response(
                    "wealth_energy_productivity",
                    mode,
                    ["cash_flows"],
                    sorted(
                        key for key, value in payload.items()
                        if key != "mode" and not _is_blank_value(value)
                    ),
                ),
            )
        return _inject_emergence(
            "wealth_energy_productivity",
            mode,
            payload,
            pi_efficiency(initial_investment, cash_flows or [], discount_rate, terminal_value, scale_mode),
        )
    if mode == "efficiency":
        return _inject_emergence(
            "wealth_energy_productivity",
            mode,
            payload,
            {
                "tool": "wealth_energy_productivity",
                "task": "wealth_energy_productivity",
                "mode": mode,
                "status": "FAIL",
                "domain_verdict": "VOID",
                "governance_verdict": "VOID",
                "engine_status": "ERROR",
                "confidence": "LOW",
                "error": "Mode 'efficiency' is not implemented yet.",
                "failure_flags": ["ENGINE_NOT_IMPLEMENTED"],
                "allocation_signal": "INSUFFICIENT_DATA",
            },
        )
    if mode == "roi":
        return _inject_emergence(
            "wealth_energy_productivity",
            mode,
            payload,
            {
                "tool": "wealth_energy_productivity",
                "task": "wealth_energy_productivity",
                "mode": mode,
                "status": "FAIL",
                "domain_verdict": "VOID",
                "governance_verdict": "VOID",
                "engine_status": "ERROR",
                "confidence": "LOW",
                "error": "Mode 'roi' is not implemented yet.",
                "failure_flags": ["ENGINE_NOT_IMPLEMENTED"],
                "allocation_signal": "INSUFFICIENT_DATA",
            },
        )
    return _dispatch_emergence(
        "wealth_energy_productivity",
        mode,
        {},
        {k: v for k, v in payload.items() if k not in ("mode", "payload")},
    )


@mcp.tool(name="wealth_time_discount")
def wealth_time_discount(
    mode: str = "npv",
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
) -> Any:
    """Ω-WEALTH-06: Time — NPV, IRR, payback, compounding, decay."""
    payload = _clean_payload(locals(), exclude={"mode"})
    return _dispatch_invariant_tool("wealth_time_discount", mode, payload)


@mcp.tool(name="wealth_inertia_leverage")
def wealth_inertia_leverage(
    mode: str = "dscr",
    ebitda: Optional[float] = None,
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-07: Inertia — resistance to change, leverage stress, fragility."""
    return _dispatch_emergence("wealth_inertia_leverage", mode, {
        "dscr": dscr_leverage,
        "leverage": dscr_leverage,
        "strain": dscr_leverage,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_field_macro")
def wealth_field_macro(
    mode: str = "fetch",
    source: str = "",
    series_id: str = "",
    entity_code: str = "",
    use_cache: bool = True,
    bus: str = "slow",
    sources: Optional[List[str]] = None,
    adapter: Optional[str] = None,
    vintage_date: str = "",
) -> Any:
    """Ω-WEALTH-08: Field — macro environment (rates, FX, energy, carbon, regime)."""
    payload = {k: v for k, v in locals().items() if k not in ("mode", "dispatch")}
    mode_requirements = {
        "fetch": ["source", "series_id", "entity_code"],
        "snapshot": ["entity_code"],
        "reconcile": ["entity_code"],
        "vintage": ["source", "series_id", "entity_code", "vintage_date"],
    }
    required = mode_requirements.get(mode, [])
    missing = [field for field in required if _is_blank_value(payload.get(field))]
    if missing:
        return _inject_emergence(
            "wealth_field_macro",
            mode,
            payload,
            _input_required_response(
                "wealth_field_macro",
                mode,
                missing,
                sorted(key for key, value in payload.items() if not _is_blank_value(value)),
            ),
        )
    return _dispatch_emergence("wealth_field_macro", mode, {
        "fetch": ingest_fetch,
        "snapshot": ingest_snapshot,
        "reconcile": ingest_reconcile,
        "health": ingest_health,
        "vintage": ingest_vintage,
        "sources": ingest_sources,
    }, payload)


@mcp.tool(name="wealth_signal_information")
def wealth_signal_information(
    mode: str = "evoi",
    well_cost_musd: float = 0,
    p50_value_musd: float = 0,
    prior_pos: Optional[float] = None,
    posterior_pos: Optional[float] = None,
    prospect_metrics: Optional[dict] = None,
    info_cost_musd: float = 5.0,
    discount_rate: float = 0.10,
    scale_mode: str = "enterprise",
    prior_pos_samples: Optional[List[float]] = None,
    posterior_pos_samples: Optional[List[float]] = None,
    prospects: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    """Ω-WEALTH-09: Signal — information value, evidence quality, schema validity."""
    return _dispatch_emergence("wealth_signal_information", mode, {
        "evoi": wealth_evoi_compute,
        "evoi_mc": wealth_evoi_monte_carlo,
        "schema": wealth_schema_validate,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_game_coordination")
def wealth_game_coordination(
    mode: str = "equilibrium",
    agents: Optional[List[dict]] = None,
    shared_resources: Optional[dict] = None,
    mechanism: str = "cooperative",
    solve_equilibrium: bool = True,
    compute_budget_usd: float = 1.0,
    token_budget: float = 1000.0,
    time_deadline_hours: float = 24.0,
) -> Any:
    """Ω-WEALTH-10: Game — multi-agent incentives, bargaining, coordination."""
    return _dispatch_emergence("wealth_game_coordination", mode, {
        "equilibrium": coordination_equilibrium,
        "game": game_theory_solve,
        "budget": agent_budget,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_boundary_governance")
def wealth_boundary_governance(
    mode: str = "floors",
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    proposal: Optional[dict] = None,
    constraints: Optional[dict] = None,
    scale_mode: str = "enterprise",
    population: float = 0,
    energy_budget_twh: float = 0,
    carbon_budget_gt: float = 0,
    tech_readiness: float = 0.5,
    alternatives: Optional[List[dict]] = None,
    values: Optional[dict] = None,
) -> Any:
    """Ω-WEALTH-11: Boundary — constitutional floors, maruah, stewardship, constraint."""
    return _dispatch_emergence("wealth_boundary_governance", mode, {
        "floors": check_floors_tool,
        "policy": policy_audit,
        "stewardship": civilization_stewardship,
        "decision": personal_decision,
    }, {k: v for k, v in locals().items() if k not in ('mode', 'dispatch')})


@mcp.tool(name="wealth_hysteresis_ledger")
def wealth_hysteresis_ledger(
    mode: str = "init",
    session_id: Optional[str] = None,
    actor_id: str = "wealth-agent",
    intent: Optional[str] = None,
    tx_type: str = "",
    amount: float = 0,
    currency: str = "MYR",
    description: str = "",
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    fees: Optional[float] = None,
    broker: Optional[str] = None,
    asset_id: Optional[str] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
    human_confirmed: bool = False,
    idempotency_key: Optional[str] = None,
    query: str = "",
    limit: int = 10,
    tool_name: str = "",
    arguments: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    nav_myr: Optional[float] = None,
    quantity_held: Optional[float] = None,
    price_close: Optional[float] = None,
) -> Any:
    """Ω-WEALTH-12: Hysteresis — path dependence, ledger, sealed financial memory."""
    payload = _clean_payload(locals(), exclude={"mode"})
    return _dispatch_invariant_tool("wealth_hysteresis_ledger", mode, payload)



@mcp.tool(name="wealth_system_registry_status")
def wealth_system_registry_status() -> dict[str, Any]:
    """Registry truth diagnostic — intended, registered, and alias surfaces."""
    return _registry_snapshot(_registered_tool_names())


WEALTH_PUBLIC_TOOL_ORDER = (
    "mcp_health_check",
    "wealth_conservation_capital",
    "wealth_flow_liquidity",
    "wealth_gradient_price",
    "wealth_entropy_risk",
    "wealth_energy_productivity",
    "wealth_time_discount",
    "wealth_inertia_leverage",
    "wealth_field_macro",
    "wealth_signal_information",
    "wealth_game_coordination",
    "wealth_boundary_governance",
    "wealth_hysteresis_ledger",
    "wealth_system_registry_status",
)
_PUBLIC_TOOLS = set(WEALTH_PUBLIC_TOOL_ORDER)

# ═══════════════════════════════════════════════════════════════════════

# ============================================================

# ── Alias Dispatch Map (backward compat without registry pollution) ──
_ALIAS_DISPATCH: dict[str, Any] = {}

def _build_alias_dispatch() -> None:
    """Populate _ALIAS_DISPATCH from v1 canonical funcs and v2 alias map."""
    global _ALIAS_DISPATCH
    engine = HarnessEngine()
    v1_funcs = {
        "wealth_ingest_fetch": ingest_fetch,
        "wealth_ingest_snapshot": ingest_snapshot,
        "wealth_ingest_reconcile": ingest_reconcile,
        "wealth_ingest_health": ingest_health,
        "wealth_ingest_vintage": ingest_vintage,
        "wealth_ingest_sources": ingest_sources,
        "wealth_emv_risk": emv_risk,
        "wealth_monte_carlo_forecast": monte_carlo_forecast,
        "wealth_correlation_guard_check": wealth_correlation_guard_check,
        "wealth_evoi_compute": wealth_evoi_compute,
        "wealth_evoi_monte_carlo": wealth_evoi_monte_carlo,
        "wealth_schema_validate": wealth_schema_validate,
        "wealth_dscr_leverage": dscr_leverage,
        "wealth_networth_state": networth_state,
        "wealth_growth_velocity": growth_velocity,
        "wealth_cashflow_flow": cashflow_flow,
        "wealth_crisis_triage": crisis_triage,
        "wealth_civilization_stewardship": civilization_stewardship,
        "wealth_npv_reward": npv_reward,
        "wealth_irr_yield": irr_yield,
        "wealth_pi_efficiency": pi_efficiency,
        "wealth_payback_time": payback_time,
        "wealth_coordination_equilibrium": coordination_equilibrium,
        "wealth_game_theory_solve": game_theory_solve,
        "wealth_personal_decision": personal_decision,
        "wealth_agent_budget": agent_budget,
        "wealth_score_kernel": wealth_score_kernel,
        "wealth_check_floors": check_floors_tool,
        "wealth_policy_audit": policy_audit,
        "wealth_audit_entropy": audit_entropy,
        "wealth_init": wealth_init_tool,
        "wealth_record_transaction": record_transaction_tool,
        "wealth_snapshot_portfolio": snapshot_portfolio_tool,
        "vault_write": record_transaction_tool,
        "vault_query": snapshot_portfolio_tool,
    }
    for canonical_name, func in v1_funcs.items():
        _ALIAS_DISPATCH[canonical_name] = func
    for v2_name, v1_name in engine.V2_CANONICAL_MAP.items():
        if v2_name in ("vaultwrite", "vaultquery"):
            continue
        if v1_name in v1_funcs:
            _ALIAS_DISPATCH[v2_name] = v1_funcs[v1_name]

_build_alias_dispatch()
# ── Surgical registry cleanup: only public tools remain ──
for _comp_key in list(mcp._local_provider._components.keys()):
    if _comp_key.startswith("tool:"):
        _tool_name = _comp_key[5:].rstrip("@")
        if _tool_name not in _PUBLIC_TOOLS:
            mcp._local_provider.remove_tool(_tool_name)


def _registered_tool_names() -> List[str]:
    names = []
    for component_key in mcp._local_provider._components.keys():
        if component_key.startswith("tool:"):
            names.append(component_key[5:].rstrip("@"))
    return sorted(set(names))


def _resolve_repo_head() -> str:
    repo_head = os.environ.get("WEALTH_REPO_HEAD")
    if repo_head:
        return repo_head
    for candidate in (os.environ.get("WEALTH_REPO_DIR"), "/opt/wealth-src", "/root/wealth"):
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            result = subprocess.run(
                ["git", "-c", f"safe.directory={candidate}", "-C", candidate, "rev-parse", "--short", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            continue
        head = result.stdout.strip()
        if head:
            return head
    return "unknown"


def _registry_snapshot(visible_names: List[str]) -> Dict[str, Any]:
    expected_names = sorted(_PUBLIC_TOOLS)
    expected_set = set(expected_names)
    visible_set = set(visible_names)
    missing = [name for name in expected_names if name not in visible_set]
    extra = sorted(visible_set - expected_set)
    hidden_alias_count = len(set(_ALIAS_DISPATCH) - expected_set)
    return {
        "service": "wealth-mcp",
        "schema_version": WEALTH_SCHEMA_VERSION,
        "repo_head": _resolve_repo_head(),
        "intended_public_tools": len(expected_names),
        "registered_public_tools": len(visible_names),
        "public_surface_count": len(expected_names),
        "runtime_surface_count": len(visible_names),
        "hidden_alias_count": hidden_alias_count,
        "canonical_public_tools": expected_names,
        "extra_visible_tools": extra,
        "missing_visible_tools": missing,
        "registry_truth": "PASS" if not missing and not extra else "FAIL",
        "final_authority": "ARIF",
    }

if __name__ == "__main__":
    # Register v2 legacy aliases (non-breaking Phase 1 Migration)
    engine = HarnessEngine()
    _v1_funcs = {
        "wealth_ingest_fetch": ingest_fetch,
        "wealth_ingest_snapshot": ingest_snapshot,
        "wealth_ingest_reconcile": ingest_reconcile,
        "wealth_ingest_health": ingest_health,
        "wealth_ingest_vintage": ingest_vintage,
        "wealth_ingest_sources": ingest_sources,
        "wealth_emv_risk": emv_risk,
        "wealth_monte_carlo_forecast": monte_carlo_forecast,
        "wealth_correlation_guard_check": wealth_correlation_guard_check,
        "wealth_evoi_compute": wealth_evoi_compute,
        "wealth_evoi_monte_carlo": wealth_evoi_monte_carlo,
        "wealth_schema_validate": wealth_schema_validate,
        "wealth_dscr_leverage": dscr_leverage,
        "wealth_networth_state": networth_state,
        "wealth_growth_velocity": growth_velocity,
        "wealth_cashflow_flow": cashflow_flow,
        "wealth_crisis_triage": crisis_triage,
        "wealth_civilization_stewardship": civilization_stewardship,
        # NOTE: wealth_npv_reward is an alias for wealth_value_npv (npv_reward).
        # Deprecated — do not register as a public tool. Use wealth_value_npv instead.
        "wealth_npv_reward": npv_reward,
        "wealth_irr_yield": irr_yield,
        "wealth_pi_efficiency": pi_efficiency,
        "wealth_payback_time": payback_time,
        "wealth_coordination_equilibrium": coordination_equilibrium,
        "wealth_game_theory_solve": game_theory_solve,
        "wealth_personal_decision": personal_decision,
        "wealth_agent_budget": agent_budget,
        "wealth_score_kernel": wealth_score_kernel,
        "wealth_check_floors": check_floors_tool,
        "wealth_policy_audit": policy_audit,
        "wealth_audit_entropy": audit_entropy,
        "wealth_init": wealth_init_tool,
        "wealth_record_transaction": record_transaction_tool,
        "wealth_snapshot_portfolio": snapshot_portfolio_tool,
        "vault_write": record_transaction_tool,
        "vault_query": snapshot_portfolio_tool,
    }
    # ── Alias Dispatch Map (backward compat without registry pollution) ──
    _ALIAS_DISPATCH: dict[str, Any] = {}
    for canonical_name, func in _v1_funcs.items():
        _ALIAS_DISPATCH[canonical_name] = func
    for v2_name, v1_name in engine.V2_CANONICAL_MAP.items():
        if v2_name in ("vaultwrite", "vaultquery"):
            continue
        if v1_name in _v1_funcs:
            _ALIAS_DISPATCH[v2_name] = _v1_funcs[v1_name]
    # NOTE: vaultwrite/vaultquery are intentionally omitted — use vault_write/vault_query.
    # Aliases remain callable via tools/call for F1 Amanah backward compatibility.

    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse as _JR
    import uvicorn

    def _serialize_result(result):
        """Convert FastMCP ToolResult to JSON-serializable dict."""
        if result is None:
            return None
        if hasattr(result, "model_dump"):
            d = result.model_dump()
            # Recursively serialize content items
            if "content" in d and isinstance(d["content"], list):
                serialized_content = []
                for item in d["content"]:
                    if hasattr(item, "model_dump"):
                        serialized_content.append(item.model_dump())
                    else:
                        serialized_content.append(dict(item) if isinstance(item, dict) else str(item))
                d["content"] = serialized_content
            return d
        return result  # Already serializable (dict, str, etc.)

    async def legacy_mcp_handler(request):
        """Direct JSON-RPC handler — bypasses FastMCP Accept-header enforcement."""
        if request.method == "GET":
            return _JR({
                "mcp": "WEALTH",
                "kernel": "Capital Intelligence Engine",
                "version": __version__,
                "transport": "streamable-http",
                "note": "Use POST for JSON-RPC tool calls",
            })
        try:
            payload = await request.json()
        except Exception:
            return _JR({"error": "Parse error"}, status_code=400)

        method = payload.get("method")
        params = payload.get("params", {})
        response_id = payload.get("id")

        if method == "tools/list":
            all_tools = await mcp.list_tools()
            # ── Constitutional Surface Filter ───────────────────────
            # Only expose canonical tools (F8 GENIUS / F10 ONTOLOGY).
            # Aliases remain callable via tools/call for backward compat.
            filtered_tools = [t for t in all_tools if t.name in _PUBLIC_TOOLS]
            return _JR({
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {"tools": [{"name": t.name, "description": t.description, "inputSchema": getattr(t, "inputSchema", {}), "outputSchema": getattr(t, "output_schema", {})} for t in filtered_tools]}
            })

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                return _JR({"jsonrpc": "2.0", "id": response_id, "error": {"code": -32602, "message": "Missing tool name"}}, status_code=400)
            try:
                # ── Alias dispatch (F1 Amanah backward compat) ──
                if name in _ALIAS_DISPATCH:
                    alias_fn = _ALIAS_DISPATCH[name]
                    if inspect.iscoroutinefunction(alias_fn):
                        result = await alias_fn(**arguments)
                    else:
                        result = alias_fn(**arguments)
                else:
                    result = await mcp.call_tool(name, arguments)
                return _JR({"jsonrpc": "2.0", "id": response_id, "result": _serialize_result(result)})
            except Exception as e:
                # Return JSON-RPC error as HTTP 200 — clients expect error in body, not 5xx
                return _JR({"jsonrpc": "2.0", "id": response_id, "error": {"code": -32603, "message": str(e)}}, status_code=200)

        if method == "initialize":
            return _JR({
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "prompts": {"listChanged": True},
                        "resources": {"listChanged": True, "subscribe": True},
                    },
                    "serverInfo": {"name": "WEALTH", "version": __version__},
                }
            })

        if method == "prompts/list":
            all_prompts = await mcp.list_prompts()
            return _JR({
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {
                    "prompts": [
                        {
                            "name": p.name,
                            "description": p.description or "",
                            "arguments": getattr(p, "arguments", []),
                        }
                        for p in all_prompts
                    ]
                }
            })

        if method == "prompts/get":
            prompt_name = params.get("name")
            all_prompts = await mcp.list_prompts()
            for p in all_prompts:
                if p.name == prompt_name:
                    try:
                        rendered = await mcp.render_prompt(p, params.get("arguments", {}))
                    except Exception:
                        rendered = {"prompt": getattr(p, "_fn", lambda: "")()}
                    return _JR({
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "result": {
                            "description": p.description or "",
                            "messages": [{"role": "user", "content": {"text": str(rendered)}}]
                            if isinstance(rendered, str)
                            else {"content": str(rendered)},
                        }
                    })
            return _JR({"jsonrpc": "2.0", "id": response_id, "error": {"code": -32602, "message": f"Prompt not found: {prompt_name}"}}, status_code=404)

        if method == "resources/list":
            all_resources = await mcp.list_resources()
            all_templates = []
            try:
                all_templates = await mcp.list_resource_templates()
            except Exception:
                pass
            return _JR({
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {
                    "resources": [
                        {
                            "uri": str(r.uri),
                            "name": str(getattr(r, "name", r.uri) or r.uri),
                            "description": str(getattr(r, "description", "") or ""),
                            "mimeType": str(getattr(r, "mime_type", "application/json") or "application/json"),
                        }
                        for r in all_resources
                    ],
                    "resourceTemplates": [
                        {
                            "uriTemplate": str(t.uriTemplate),
                            "name": str(getattr(t, "name", t.uriTemplate) or t.uriTemplate),
                            "description": str(getattr(t, "description", "") or ""),
                            "mimeType": str(getattr(t, "mime_type", "application/json") or "application/json"),
                        }
                        for t in all_templates
                    ],
                }
            })

        return _JR({"jsonrpc": "2.0", "id": response_id, "error": {"code": -32601, "message": "Method not found"}}, status_code=404)

    async def tools_handler(request):
        """Federation tool discovery — returns flat tool registry with danger/fail metadata."""
        all_tools = await mcp.list_tools()
        registry = _registry_snapshot([tool.name for tool in all_tools])
        # WEALTH tool danger taxonomy (mirrors arifOS federation_topology)
        _DANGER_MAP = {
            # L4 — irreversible / operational mutation
            "wealth_vault_seal": {"danger_level": "L4", "fail_posture": "fail-closed"},
            "wealth_emv_final": {"danger_level": "L4", "fail_posture": "fail-closed"},
            # L3 — routing / memory / judgment
            "wealth_reason_agent": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "wealth_kernel_route": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "wealth_judge_deliberate": {"danger_level": "L3", "fail_posture": "fail-closed"},
            # L2 — session state
            "wealth_session_init": {"danger_level": "L2", "fail_posture": "fail-open"},
            "wealth_evidence_fetch": {"danger_level": "L2", "fail_posture": "fail-open"},
            # L1 — observe / degraded output
            "wealth_sense_observe": {"danger_level": "L1", "fail_posture": "fail-open"},
            "wealth_ops_measure": {"danger_level": "L1", "fail_posture": "fail-open"},
        }
        # Fail-open constraint for L1/L2: may degrade output, MUST NOT elevate authority
        _FAIL_OPEN_CONSTRAINT = "may degrade output, must not elevate authority"
        tools = []
        for t in all_tools:
            name = t.name
            meta = _DANGER_MAP.get(name, {"danger_level": "L2", "fail_posture": "fail-open"})
            tools.append({
                "name": name,
                "description": t.description or "",
                "inputSchema": getattr(t, "inputSchema", {}),
                "outputSchema": getattr(t, "output_schema", {}),
                "danger_level": meta["danger_level"],
                "fail_posture": meta["fail_posture"],
                "fail_open_constraint": _FAIL_OPEN_CONSTRAINT if meta["fail_posture"] == "fail-open" else None,
            })
        return _JR({
            "organ": "WEALTH",
            "role": "Capital Intelligence / NPV + EMV + Crisis Triage",
            "schema": WEALTH_SCHEMA_VERSION,
            "version": __version__,
            "count": len(tools),
            "public_surface_count": registry["public_surface_count"],
            "runtime_surface_count": registry["runtime_surface_count"],
            "hidden_alias_count": registry["hidden_alias_count"],
            "registry_truth": registry["registry_truth"],
            "danger_taxonomy": {
                "L4": "irreversible / operational mutation — fail-closed mandatory",
                "L3": "routing / memory / judgment — fail-closed mandatory",
                "L2": "session state — fail-open with constraint",
                "L1": "observe / degraded output — fail-open with constraint",
            },
            "fail_open_constraint": _FAIL_OPEN_CONSTRAINT,
            "tools": tools,
        })

    async def health_handler(request):
        registry = _registry_snapshot([tool.name for tool in await mcp.list_tools()])
        return _JR({
            "status": "healthy" if registry["registry_truth"] == "PASS" else "warn",
            "service": "wealth-mcp",
            "version": __version__,
            "schema_version": registry["schema_version"],
            "repo_head": registry["repo_head"],
            "image_tag": os.environ.get("WEALTH_IMAGE_TAG", "unknown"),
            "public_surface_count": registry["public_surface_count"],
            "runtime_surface_count": registry["runtime_surface_count"],
            "hidden_alias_count": registry["hidden_alias_count"],
            "registry_truth": registry["registry_truth"],
            "final_authority": registry["final_authority"],
        })

    async def ready_handler(request):
        registry = _registry_snapshot([tool.name for tool in await mcp.list_tools()])
        return _JR({
            "status": "ready" if registry["registry_truth"] == "PASS" else "warn",
            **registry,
        })

    async def prompts_handler(request):
        """Federation prompt discovery — returns governance reasoning workflows."""
        all_prompts = await mcp.list_prompts()
        return _JR({
            "organ": "WEALTH",
            "role": "Capital Intelligence / NPV + EMV + Crisis Triage",
            "schema": "wealth-federation-v2026.05.07",
            "version": __version__,
            "count": len(all_prompts),
            "prompts": [
                {
                    "name": p.name,
                    "description": p.description or "",
                }
                for p in all_prompts
            ],
        })

    async def resources_handler(request):
        """Federation resource discovery — returns schemas/policies/formulas/ontology/state."""
        all_resources = await mcp.list_resources()
        all_templates = []
        try:
            all_templates = await mcp.list_resource_templates()
        except Exception:
            pass
        return _JR({
            "organ": "WEALTH",
            "role": "Capital Intelligence / NPV + EMV + Crisis Triage",
            "schema": "wealth-federation-v2026.05.07",
            "version": __version__,
            "resourceCount": len(all_resources),
            "templateCount": len(all_templates),
            "resources": [
                {
                    "uri": str(r.uri),
                    "name": str(getattr(r, "name", r.uri) or r.uri),
                    "description": str(getattr(r, "description", "") or ""),
                }
                for r in all_resources
            ],
            "resourceTemplates": [
                {
                    "uriTemplate": str(t.uriTemplate),
                    "name": str(getattr(t, "name", t.uriTemplate) or t.uriTemplate),
                    "description": str(getattr(t, "description", "") or ""),
                }
                for t in all_templates
            ],
        })

    mcp_app = mcp.http_app(path="/", transport="streamable-http", stateless_http=True)

    app = Starlette(
        routes=[
            Route("/mcp", legacy_mcp_handler, methods=["GET", "POST"]),
            Route("/tools", tools_handler, methods=["GET"]),
            Route("/prompts", prompts_handler, methods=["GET"]),
            Route("/resources", resources_handler, methods=["GET"]),
            Route("/health", health_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        lifespan=getattr(mcp_app, "lifespan", None),
    )

    # ── Startup Registry Assertion (fail closed) ────────────
    async def _assert_registry() -> None:
        registered = {t.name for t in await mcp.list_tools()}
        extra = registered - _PUBLIC_TOOLS
        missing = _PUBLIC_TOOLS - registered
        if extra or missing:
            raise RuntimeError(
                f"REGISTRY_TRUTH_FAILURE: extra={sorted(extra)} missing={sorted(missing)}"
            )
    asyncio.run(_assert_registry())

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8082)),
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
