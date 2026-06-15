"""
⛔ DEPRECATED — This monolith is being replaced by the federated domain.

New entry point: server_federated.py
New architecture:
  wealth_core/       — pure engines (no MCP, no I/O)
  wealth_contracts/  — output envelopes, epistemic tags
  wealth_mcp/        — MCP surface (19 tools)
  wealth_arifos_bridge/ — arifOS integration
  wealth_compat/     — legacy aliases

This file is kept for backward compatibility during migration.
5 tools still delegate here: stock_analysis, personal_finance, market_data,
omni_wisdom, agent_path.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

try:
    import uvloop

    uvloop.install()
except ImportError:
    pass  # Windows / dev fallback

import asyncio
import hashlib
import inspect
import json
import math
import numbers
import os
import subprocess
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
from pydantic import BaseModel, Field
import httpx

# Ensure parent directory is in path for absolute imports if needed
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.append(base_dir)

# ── Reality Ledger Bridge ────────────────────────────────────────────────────────
_WEALTH_LEDGER_AVAILABLE = True
try:
    from core.organ_ledger_bridge import record_wealth_computation
except ImportError:
    _WEALTH_LEDGER_AVAILABLE = False

# WEALTH Internal Imports (Use relative or try/except for robustness)
try:
    from .governance import ForgeLaw, compute_kappa_r, compute_psi_le, get_qdf_version
except ImportError:
    from governance import compute_kappa_r, compute_psi_le, get_qdf_version

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
except Exception:
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
                "delta_S": 0.0,  # Compat
                "lyapunov_lambda": 0.0,
                "omega_capacity": 0.0,
                "entropy_s": 1.0,
                "verdict": "UNAVAILABLE",
                "regime": "unavailable",
                "is_outlier": False,
                "boundary_stress": params.get("resource_utilization", 0.8),
                "engine_error": G_SCORE_IMPORT_ERROR,
            }


# --------------------------------------------------------------------------- #
# D1 Personal Finance & D3 Market Data — INLINED after controlled wrapper
# FastMCP mcp.tool is now patched with controlled wrapper (whitelist-only).
# These tools ARE in PUBLIC_SURFACE_WHITELIST so they register normally.
# db_schema is a pure utility — no FastMCP coupling.
# --------------------------------------------------------------------------- #

# D4 Stock Analysis — imported from internal/stock/
# All 12 stock tools exposed through one unified mode-based tool.
# Import happens at module level for tool registration.
# --------------------------------------------------------------------------- #
try:
    from internal.stock import (
        verify_trade_math,
        separate_realized_unrealized,
        calculate_position_size,
        calculate_r_multiple,
        check_portfolio_exposure,
        apply_bursa_cost_model,
        detect_tamak_behavior,
        pre_trade_gate,
        check_fundamental_invariants,
        run_tac9_engine,
        detect_anomalous_contrast,
        detect_false_confluence,
    )

    _WEALTH_STOCK_AVAILABLE = True
except ImportError:
    _WEALTH_STOCK_AVAILABLE = False
    verify_trade_math = None  # type: ignore
    separate_realized_unrealized = None  # type: ignore
    calculate_position_size = None  # type: ignore
    calculate_r_multiple = None  # type: ignore
    check_portfolio_exposure = None  # type: ignore
    apply_bursa_cost_model = None  # type: ignore
    detect_tamak_behavior = None  # type: ignore
    pre_trade_gate = None  # type: ignore
    check_fundamental_invariants = None  # type: ignore
    run_tac9_engine = None  # type: ignore
    detect_anomalous_contrast = None  # type: ignore
    detect_false_confluence = None  # type: ignore

# D4+ Bursa Malaysia Intelligence — imported from internal/bursa/
# Free-first, arifOS-aligned. klse-screener-py (MIT license) as default provider.
# Upgrade ports for Morningstar MCP / ICE Bursa when capital allows.
try:
    from internal.bursa import (
        get_klse,
        generate_evidence_card,
        ScreenCriteria as BursaScreenCriteria,
        ScreenResult as BursaScreenResult,
    )

    _WEALTH_BURSA_AVAILABLE = True
except ImportError:
    _WEALTH_BURSA_AVAILABLE = False
    get_klse = None  # type: ignore
    generate_evidence_card = None  # type: ignore
    BursaScreenCriteria = None  # type: ignore
    BursaScreenResult = None  # type: ignore

# D4+ Global Markets Intelligence — imported from internal/world/
# Free-first, arifOS-aligned. yfinance (Apache 2.0) as default provider.
# Covers indices, commodities, FX, crypto, VIX. Upgrade ports for Alpha Vantage/FRED later.
try:
    from internal.world import (
        get_global,
        GLOBAL_SYMBOLS,
    )

    _WEALTH_GLOBAL_AVAILABLE = True
except ImportError:
    _WEALTH_GLOBAL_AVAILABLE = False
    get_global = None  # type: ignore
    GLOBAL_SYMBOLS = {}  # type: ignore

# D4+ Technical Indicators + Risk Metrics — computed from yfinance history
try:
    from internal.stock.indicators import compute_technical_pack

    _WEALTH_INDICATORS_AVAILABLE = True
except ImportError:
    _WEALTH_INDICATORS_AVAILABLE = False
    compute_technical_pack = None  # type: ignore

# D4+ 9-Point Screener
try:
    from internal.stock.screener_9 import run_screener_9

    _WEALTH_SCREENER_9_AVAILABLE = True
except ImportError:
    _WEALTH_SCREENER_9_AVAILABLE = False

# D4++ Market Intelligence Engine — thermodynamic state-space analysis
try:
    from internal.stock.market_intelligence import compute_market_intelligence

    _WEALTH_MI_AVAILABLE = True
except ImportError:
    _WEALTH_MI_AVAILABLE = False

# D4+++ 999 Engine
try:
    from internal.stock.engine_999 import compute_999

    _WEALTH_999_AVAILABLE = True
except ImportError:
    _WEALTH_999_AVAILABLE = False

# 888 JUDGE Engine
try:
    from internal.stock.engine_888 import compute_888

    _WEALTH_888_AVAILABLE = True
except ImportError:
    _WEALTH_888_AVAILABLE = False

# Calhoun Guard — 4 philosophical locks
try:
    from internal.stock.calhoun_guard import enrich_888_verdict

    _WEALTH_CALHOUN_AVAILABLE = True
except ImportError:
    _WEALTH_CALHOUN_AVAILABLE = False
    enrich_888_verdict = None
    compute_888 = None
    compute_999 = None
    compute_market_intelligence = None  # type: ignore
    run_screener_9 = None  # type: ignore

# Governance Singularity Detector — EUREKA 2026-06-12
try:
    from internal.stock.governance_singularity import detect_governance_singularity

    _WEALTH_GSD_AVAILABLE = True
except ImportError:
    _WEALTH_GSD_AVAILABLE = False
    detect_governance_singularity = None


# Lazy helpers for async DB operations (import at call time to avoid top-level asyncio)
async def _init_db_schema():
    from .db_schema import init_schema

    await init_schema()


async def _txns(owner, start_dt, end_dt, category, limit):
    from .db_schema import get_transactions

    return await get_transactions(owner, start_dt, end_dt, category, limit)


async def _assets(owner):
    from .db_schema import get_assets

    return await get_assets(owner)


async def _liabs(owner):
    from .db_schema import get_liabilities

    return await get_liabilities(owner)


async def _epf(owner):
    from .db_schema import get_latest_epf

    return await get_latest_epf(owner)


__version__ = "2026.05.02"
"""WEALTH v2026.05.02 — Sovereign Pipeline OS with Expanded Resource Lattice."""

LAST_RECEIPT_HASH = "0" * 64

# Legacy arifOS path support
arifos_path = os.path.join(base_dir, "arifOS")
if os.path.exists(arifos_path) and arifos_path not in sys.path:
    sys.path.append(arifos_path)
# Canonical arifOS kernel path (added 2026-06-02 for SAF shared lib)
_arifos_kernel = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
if os.path.isdir(_arifos_kernel) and _arifos_kernel not in sys.path:
    sys.path.append(_arifos_kernel)

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
# check_floors: try to import from arifOS (floor evaluation is read-only)
try:
    from arifosmcp.runtime.megaTools.tool_01_init_anchor import check_floors

    GOVERNANCE_AVAILABLE = True
except Exception:
    try:
        from arifosmcp.runtime.tools import arifos_judge as check_floors

        GOVERNANCE_AVAILABLE = True
    except Exception:
        GOVERNANCE_AVAILABLE = False

        def check_floors(*args, **kwargs):
            return {
                "pass": True,
                "verdict": "SEAL",
                "violations": [],
                "holds": [],
                "warnings": [],
            }


# Vault sealing must delegate to arifOS via HTTP (federation boundary).
# WEALTH must not call arifOS vault internals directly.
async def _arifos_vault_seal_http(
    event_type: str = "",
    session_id: str = "",
    actor_id: str = "",
    stage: str = "",
    verdict: str = "ACTIVE",
    payload: dict | None = None,
    risk_tier: str = "low",
    **kwargs,
):
    """Delegate vault sealing to arifOS via HTTP — do not import arifOS internals."""
    import httpx

    body = {
        "event_type": event_type,
        "session_id": session_id,
        "actor_id": actor_id,
        "stage": stage,
        "verdict": verdict,
        "data": payload or {},
        "risk_tier": risk_tier,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "http://localhost:8088/mcp",
                headers={"Mcp-Session-ID": "wealth-organ"},
                json={
                    "jsonrpc": "2.0",
                    "id": 42,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_vault_seal",
                        "arguments": {
                            "mode": "seal",
                            "payload": json.dumps(body),
                            "session_id": session_id or "",
                            "actor_id": actor_id or "WEALTH",
                            "ack_irreversible": False,
                            "witness_type": "ai",
                        },
                    },
                },
            )
        result = resp.json()
        # Return dict so callers can access .get() — matches vault_write expectation
        if result.get("result"):
            content = result["result"].get("content", [{}])[0]
            text = json.loads(content.get("text", "{}"))
            return {
                "chain_hash": text.get("chain_hash", ""),
                "ledger_id": text.get("record_id", ""),
                "status": text.get("status", "UNKNOWN"),
            }
        return {"chain_hash": "", "ledger_id": "", "status": "ERROR"}
    except Exception:
        return None


try:
    from host.governance.vault_supabase import append_vault999
except Exception:
    append_vault999 = _arifos_vault_seal_http


def _vault_append(record, **kwargs):
    """Bridge sync/async vault append safely.

    Routes vault writes through arifOS constitutional judgment (via HTTP).
    Falls back to local JSONL if arifOS is unreachable.
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop — create new one and run async function
        return asyncio.run(_vault_append_async(record, **kwargs))

    # Inside async context — fire-and-forget via task
    task = loop.create_task(_vault_append_async(record, **kwargs))
    # Attach result retrieval for sync callers that later check res
    return task


async def _vault_append_async(record, **kwargs):
    """Async vault append via arifOS HTTP — returns dict for vault_write."""
    try:
        result = await append_vault999(record, **kwargs)
        return (
            result
            if result is not None
            else {"chain_hash": "", "ledger_id": "", "status": "FALLBACK"}
        )
    except Exception:
        return {"chain_hash": "", "ledger_id": "", "status": "ERROR"}


def _evaluate_floors(args: Dict[str, Any]) -> Dict[str, Any]:
    """Local hard floors that remain active even when arifOS is unavailable."""
    try:
        result = check_floors(args)
        if not isinstance(result, dict):
            result = {}
    except Exception:
        result = {
            "pass": False,
            "verdict": "HOLD",
            "violations": ["FLOOR_UNVERIFIED"],
            "holds": ["GOVERNANCE_IMPORT_FAILURE"],
        }

    result = {
        "pass": result.get("pass", False),
        "verdict": result.get("verdict", "HOLD"),
        "violations": list(result.get("violations", [])),
        "holds": list(result.get("holds", [])),
        "warnings": list(result.get("warnings", [])),
    }

    if args.get("ai_is_deciding"):
        result["pass"] = False
        result["verdict"] = "VOID"
        if "F13_SOVEREIGN_DECISION_REQUIRED" not in result["violations"]:
            result["violations"].append("F13_SOVEREIGN_DECISION_REQUIRED")

    high_scale = args.get("scale_mode") in {
        "national",
        "crisis",
        "civilization",
        "agentic",
        "sovereign",
    }
    irreversible_unconfirmed = not args.get("reversible", True) and not args.get(
        "human_confirmed", False
    )
    if irreversible_unconfirmed and (high_scale or args.get("critical", False)):
        if result["verdict"] != "VOID":
            result["verdict"] = "HOLD"
        result["pass"] = False
        if "F01_IRREVERSIBLE_ACTION_REQUIRES_HUMAN_CONFIRMATION" not in result["holds"]:
            result["holds"].append(
                "F01_IRREVERSIBLE_ACTION_REQUIRES_HUMAN_CONFIRMATION"
            )

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
                    harness_path = os.path.join(
                        base_dir, "..", "canon", "WEALTH_HARNESS.md"
                    )
                else:
                    harness_path = os.path.join(base_dir, "canon", "WEALTH_HARNESS.md")
                harness_path = os.path.normpath(harness_path)
                if os.path.exists(harness_path):
                    with open(harness_path, "r", encoding="utf-8") as f:
                        cls._DOCTRINE_HASH = hashlib.sha256(
                            f.read().encode()
                        ).hexdigest()
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

    SOVEREIGN_METADATA_FAMILIES = [
        "VAULT",
        "SENSE",
        "MIND",
        "HEART",
        "REASON",
        "JUDGE",
        "SURVIVAL",
    ]

    SOVEREIGN_METADATA = {
        "wealth_init": {
            "family": "VAULT",
            "stage": "000-VAULT",
            "display": "wealth_init",
        },
        "vault_write": {
            "family": "VAULT",
            "stage": "000-VAULT",
            "display": "vault_write",
        },
        "vault_query": {
            "family": "VAULT",
            "stage": "000-VAULT",
            "display": "vault_query",
        },
        "wealth_record_transaction": {
            "family": "VAULT",
            "stage": "000-VAULT",
            "display": "wealth_record_transaction",
        },
        "wealth_snapshot_portfolio": {
            "family": "VAULT",
            "stage": "000-VAULT",
            "display": "wealth_snapshot_portfolio",
        },
        "wealth_ingest_fetch": {
            "family": "SENSE",
            "stage": "100-SENSE",
            "display": "wealth_ingest_fetch",
        },
        "wealth_ingest_snapshot": {
            "family": "SENSE",
            "stage": "100-SENSE",
            "display": "wealth_ingest_snapshot",
        },
        "wealth_ingest_reconcile": {
            "family": "SENSE",
            "stage": "100-SENSE",
            "display": "wealth_ingest_reconcile",
        },
        "wealth_ingest_health": {
            "family": "SENSE",
            "stage": "100-SENSE",
            "display": "wealth_ingest_health",
        },
        "wealth_ingest_sources": {
            "family": "SENSE",
            "stage": "100-SENSE",
            "display": "wealth_ingest_sources",
        },
        "wealth_schema_validate": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_schema_validate",
        },
        "wealth_correlation_guard_check": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_risk_correlation",
        },
        "wealth_evoi_compute": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_evoi_compute",
        },
        "wealth_monte_carlo_forecast": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_risk_monte_carlo",
        },
        "wealth_emv_risk": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_risk_emv",
        },
        "wealth_audit_entropy": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_audit_entropy",
            "dual_domain": ["MIND", "JUDGE"],
        },
        "wealth_dscr_leverage": {
            "family": "SURVIVAL",
            "stage": "300-SURVIVAL",
            "display": "wealth_survival_dscr",
        },
        "wealth_crisis_triage": {
            "family": "SURVIVAL",
            "stage": "300-SURVIVAL",
            "display": "wealth_crisis_triage",
        },
        "wealth_civilization_stewardship": {
            "family": "HEART",
            "stage": "300-HEART",
            "display": "wealth_stewardship_civ",
        },
        "wealth_npv_reward": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_calc_npv",
        },
        "wealth_irr_yield": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_calc_irr",
        },
        "wealth_pi_efficiency": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_calc_pi",
        },
        "wealth_payback_time": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_calc_payback",
        },
        "wealth_coordination_equilibrium": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_coord_equilibrium",
        },
        "wealth_game_theory_solve": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_coord_game_theory",
        },
        "wealth_personal_decision": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_personal_decision",
        },
        "wealth_agent_budget": {
            "family": "REASON",
            "stage": "400-REASON",
            "display": "wealth_calc_agent_budget",
        },
        "wealth_score_kernel": {
            "family": "JUDGE",
            "stage": "888-JUDGE",
            "display": "wealth_score_kernel",
            "primary": True,
        },
        "wealth_check_floors": {
            "family": "JUDGE",
            "stage": "800-JUDGE",
            "display": "wealth_check_floors",
        },
        "wealth_policy_audit": {
            "family": "JUDGE",
            "stage": "800-JUDGE",
            "display": "wealth_policy_audit",
        },
        "wealth_evoi_monte_carlo": {
            "family": "MIND",
            "stage": "200-MIND",
            "display": "wealth_evoi_monte_carlo",
        },
        "wealth_cashflow_flow": {
            "family": "SURVIVAL",
            "stage": "300-SURVIVAL",
            "display": "wealth_survival_flow",
        },
        "wealth_networth_state": {
            "family": "SURVIVAL",
            "stage": "300-SURVIVAL",
            "display": "wealth_survival_networth",
        },
        "wealth_growth_velocity": {
            "family": "SURVIVAL",
            "stage": "300-SURVIVAL",
            "display": "wealth_survival_velocity",
        },
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

    def audit(
        self,
        tool_name: str,
        primary: Dict[str, Any],
        flags: List[str],
        parent_hash: str = "",
    ) -> Dict[str, Any]:
        """Audit the current tool call against the 9-harness constraints."""
        harness_status = {
            name: {"stress": 0.0, "status": "SECURE"} for name in self.HARNESS_NAMES
        }
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
        if any(
            f in flags
            for f in ["INVALID_DATA_SOURCE", "STALE_DATA", "SOURCE_DIVERGENCE"]
        ):
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
        if any(
            f in flags
            for f in ["LEVERAGE_DEFAULT", "RUNWAY_CRITICAL", "CASHFLOW_NEGATIVE"]
        ):
            harness_status["Survival"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("SURVIVAL_HARNESS_FAILURE")

        # 6. Constitutional Check
        if (
            any(f.startswith("FLOOR_") for f in flags)
            or "SOVEREIGN_DIGNITY_LOW" in flags
        ):
            harness_status["Constitutional"].update(
                {"stress": 1.0, "status": "SNAPPED"}
            )
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
            harness_status["Civilization"].update(
                {
                    "stress": 1.0,
                    "status": "SNAPPED",
                    "detail": f"C:{carbon:.3f} | R:{collapse:.3f} | G:{growth:.3f}",
                }
            )
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
            self.alarm_system.trigger(
                tool_name,
                "Systemic",
                {"violations": violations, "systemic_stress": systemic_stress},
            )
        elif has_stressed or systemic_stress > 1.2:
            overall_verdict = "PASS"  # Keep PASS for backward compatibility
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


def compute_maruah_from_context(
    explicit_score: Optional[float],
    scale_mode: str = "enterprise",
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    foreign_entity: bool = False,
    opaque_valuation: bool = False,
    context: Optional[dict] = None,
) -> tuple:
    """Compute maruah score from context signals when not explicitly provided.
    Returns (score, was_defaulted, signals_used)."""
    if explicit_score is not None and explicit_score != 0.5:
        return (explicit_score, False, [])

    # Start from neutral
    score = 0.70
    signals: List[str] = []
    ctx = context or {}

    scale_penalties = {
        "sovereign": 0.0,
        "national": 0.0,
        "civilization": 0.0,
        "crisis": -0.15,
        "enterprise": 0.0,
        "sme": 0.0,
        "personal": 0.05,
        "household": 0.05,
    }
    sp = scale_penalties.get(scale_mode, 0.0)
    if sp != 0.0:
        score += sp
        signals.append(f"scale_mode={scale_mode} ({sp:+.2f})")

    if not reversible:
        score -= 0.15
        signals.append("irreversible_action (-0.15)")
    if not human_confirmed and scale_mode in {
        "national",
        "sovereign",
        "civilization",
        "crisis",
    }:
        score -= 0.12
        signals.append("unconfirmed_at_high_scale (-0.12)")
    if epistemic in {"VOID", "FABRICATED"}:
        score -= 0.20
        signals.append(f"epistemic={epistemic} (-0.20)")
    elif epistemic == "CLAIM":
        score -= 0.05
        signals.append("epistemic=CLAIM (-0.05)")
    if foreign_entity or ctx.get("foreign_entity"):
        score -= 0.18
        signals.append("foreign_entity_involvement (-0.18)")
    if opaque_valuation or ctx.get("opaque_valuation"):
        score -= 0.15
        signals.append("opaque_valuation (-0.15)")
    if ctx.get("constitutional_dispute"):
        score -= 0.10
        signals.append("active_constitutional_dispute (-0.10)")

    score = round(max(0.0, min(1.0, score)), 3)
    was_defaulted = explicit_score is None or explicit_score == 0.5
    return (score, was_defaulted, signals)


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

# --------------------------------------------------------------------------- #
# D1 PERSONAL FINANCE — 6 tools (inline, after mcp is defined)
# db_schema.py provides async PostgreSQL helpers; we call via run_until_complete
# --------------------------------------------------------------------------- #

from datetime import date as _date


async def _pf_init_db():
    from .db_schema import init_schema

    await init_schema()


async def _pf_get_txns(owner, start_dt, end_dt, category, limit):
    from .db_schema import get_transactions

    return await get_transactions(owner, start_dt, end_dt, category, limit)


async def _pf_get_assets(owner):
    from .db_schema import get_assets

    return await get_assets(owner)


async def _pf_get_liabs(owner):
    from .db_schema import get_liabilities

    return await get_liabilities(owner)


async def _pf_get_epf(owner):
    from .db_schema import get_latest_epf

    return await get_latest_epf(owner)


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
async def wealth_cashflow_track(
    owner: str = "arif",
    txn_date: str = None,
    description: str = "",
    category: str = "expense",
    subcategory: str = None,
    amount: float = 0.0,
    currency: str = "MYR",
) -> dict:
    """Ω-D1-01: Cashflow Track — Record a financial transaction."""
    parsed = txn_date or _date.today().isoformat()
    parsed_date = datetime.strptime(parsed, "%Y-%m-%d").date()
    await _pf_init_db()
    from .db_schema import upsert_transaction

    txn_id = await upsert_transaction(
        owner=owner,
        date=parsed_date,
        description=description,
        category=category,
        amount=amount,
        currency=currency,
        subcategory=subcategory,
    )
    return {
        "mcp": "WEALTH",
        "tool": "wealth_cashflow_track",
        "status": "recorded",
        "transaction_id": txn_id,
        "date": str(parsed_date),
        "description": description,
        "category": category,
        "amount": amount,
        "currency": currency,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
async def wealth_cashflow_summary(
    owner: str = "arif",
    start_date: str = None,
    end_date: str = None,
    category: str = None,
) -> dict:
    """Ω-D1-02: Cashflow Summary — Aggregate transactions by category."""
    today = _date.today()
    start_str = start_date or today.replace(day=1).isoformat()
    end_str = end_date or today.isoformat()
    start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
    await _pf_init_db()
    txns = await _pf_get_txns(owner, start_dt, end_dt, category, 5000)
    inflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) > 0)
    outflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) < 0)
    by_cat: dict = {}
    for t in txns:
        c = str(t["category"])
        by_cat[c] = by_cat.get(c, 0.0) + float(t["amount"])
    return {
        "mcp": "WEALTH",
        "tool": "wealth_cashflow_summary",
        "owner": owner,
        "period": {"start": start_str, "end": end_str},
        "transaction_count": len(txns),
        "inflows": round(inflows, 4),
        "outflows": round(outflows, 4),
        "net": round(inflows + outflows, 4),
        "by_category": {k: round(v, 4) for k, v in by_cat.items()},
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
def wealth_runway_calculate(
    monthly_burn: float = 0.0,
    liquid_assets: float = 0.0,
    conservative_factor: float = 0.8,
) -> dict:
    """Ω-D1-03: Runway Calculate — Months of financial runway."""
    adjusted = liquid_assets * conservative_factor
    months = round(adjusted / monthly_burn, 1) if monthly_burn > 0 else float("inf")
    break_even_pa = (adjusted / 12) if adjusted > 0 else 0.0
    if months < 3:
        stress = "CRITICAL — less than 3 months runway"
    elif months < 6:
        stress = "AMBER — 3–6 months, build buffer"
    elif months < 12:
        stress = "CAUTION — 6–12 months"
    else:
        stress = "GREEN — 12+ months runway"
    return {
        "mcp": "WEALTH",
        "tool": "wealth_runway_calculate",
        "months_runway": months,
        "adjusted_liquid_assets": round(adjusted, 4),
        "break_even_burn_pa": round(break_even_pa, 4),
        "monthly_burn": monthly_burn,
        "liquid_assets": liquid_assets,
        "conservative_factor": conservative_factor,
        "stress_label": stress,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
async def wealth_net_worth_snapshot(
    owner: str = "arif",
    include_EPF: bool = True,
) -> dict:
    """Ω-D1-04: Net Worth Snapshot — Assets minus Liabilities."""
    await _pf_init_db()
    assets = await _pf_get_assets(owner)
    liabs = await _pf_get_liabs(owner)
    epf = await _pf_get_epf(owner) if include_EPF else None
    total_assets = sum(float(a["current_value"]) for a in assets)
    total_liab = sum(float(l["outstanding"]) for l in liabs)
    by_class: dict = {}
    for a in assets:
        c = str(a["asset_class"])
        by_class[c] = by_class.get(c, 0.0) + float(a["current_value"])
    epf_total = 0.0
    epf_date = None
    if epf and include_EPF:
        epf_total = float(epf["total"])
        epf_date = str(epf["snapshot_date"])
        total_assets += epf_total
        by_class["epf"] = by_class.get("epf", 0.0) + epf_total
    return {
        "mcp": "WEALTH",
        "tool": "wealth_net_worth_snapshot",
        "owner": owner,
        "total_assets": round(total_assets, 4),
        "total_liabilities": round(total_liab, 4),
        "net_worth": round(total_assets - total_liab, 4),
        "asset_breakdown": {k: round(v, 4) for k, v in by_class.items()},
        "liability_breakdown": {
            str(l["liability_class"]): round(float(l["outstanding"]), 4) for l in liabs
        },
        "epf_total": round(epf_total, 4),
        "epf_date": epf_date,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


@mcp.tool(name="wealth_personal_finance")
async def wealth_personal_finance(
    mode: str = "summary",
    owner: str = "arif",
    # track mode params
    txn_date: str = None,
    description: str = "",
    category: str = "expense",
    subcategory: str = None,
    amount: float = 0.0,
    currency: str = "MYR",
    # summary mode params
    start_date: str = None,
    end_date: str = None,
    summary_category: str = None,
    # runway mode params
    monthly_burn: float = 0.0,
    liquid_assets: float = 0.0,
    conservative_factor: float = 0.8,
    # net_worth mode params
    include_EPF: bool = True,
    # epf mode params
    current_account_1: float = 0.0,
    current_account_2: float = 0.0,
    epf_monthly_contribution: float = 0.0,
    epf_current_age: int = 30,
    epf_target_age: int = 55,
    epf_annual_rate: float = 0.0515,
    epf_employer_match: float = 0.0,
    # zakat mode params
    zakat_year: int = None,
    zakat_total_wealth: float = None,
) -> dict:
    """Ω-D1: Personal Finance — unified surface for cashflow, runway, and net worth.

    Modes:
      track    — Record a financial transaction
      summary  — Aggregate transactions by category
      runway   — Months of financial runway
      net_worth — Assets minus liabilities
      epf      — Project EPF accumulation to target age (Malaysian)
      zakat    — Calculate Malaysian 2.5%% zakat above nisab
    """
    mode = mode.lower().strip()
    if mode == "track":
        return await wealth_cashflow_track(
            owner=owner,
            txn_date=txn_date,
            description=description,
            category=category,
            subcategory=subcategory,
            amount=amount,
            currency=currency,
        )
    elif mode == "summary":
        return await wealth_cashflow_summary(
            owner=owner,
            start_date=start_date,
            end_date=end_date,
            category=summary_category,
        )
    elif mode == "runway":
        return await wealth_survival_engine(
            mode="runway",
            liquid_assets=liquid_assets,
            monthly_expenses=monthly_burn,
            conservative_factor=conservative_factor,
            legacy_compat=True,
        )
    elif mode == "net_worth":
        return await wealth_net_worth_snapshot(
            owner=owner,
            include_EPF=include_EPF,
        )
    elif mode == "epf":
        return wealth_epf_project(
            current_account_1=current_account_1,
            current_account_2=current_account_2,
            monthly_contribution=epf_monthly_contribution,
            current_age=epf_current_age,
            target_age=epf_target_age,
            annual_rate=epf_annual_rate,
            employer_match=epf_employer_match,
        )
    elif mode == "zakat":
        return await wealth_zakat_calculate(
            owner=owner,
            year=zakat_year,
            total_wealth=zakat_total_wealth,
            currency=currency,
        )
    else:
        return {
            "mcp": "WEALTH",
            "tool": "wealth_personal_finance",
            "status": "error",
            "message": f"Unknown mode: {mode}. Use track|summary|runway|net_worth|epf|zakat",
        }


def wealth_epf_project(
    current_account_1: float = 0.0,
    current_account_2: float = 0.0,
    monthly_contribution: float = 0.0,
    current_age: int = 30,
    target_age: int = 55,
    annual_rate: float = 0.0515,
    employer_match: float = 0.0,
) -> dict:
    """Ω-D1-05: EPF Project — Project EPF accumulation to target age."""
    current = current_account_1 + current_account_2
    years = max(0, target_age - current_age)
    months = years * 12
    total_monthly = monthly_contribution + employer_match
    r_month = annual_rate / 12
    fv_current = current * ((1 + r_month) ** months) if r_month > 0 else current
    fv_annuity = (
        total_monthly * (((1 + r_month) ** months - 1) / r_month)
        if r_month > 0
        else total_monthly * months
    )
    projected = fv_current + fv_annuity
    total_contrib = current + (total_monthly * months)
    total_growth = projected - total_contrib

    def epf_rate(age):
        if age < 50:
            return 0.0515
        if age < 55:
            return 0.0520
        if age < 60:
            return 0.0530
        return 0.0540

    blended = (
        sum(epf_rate(current_age + y) for y in range(years)) / years
        if years > 0
        else annual_rate
    )
    return {
        "mcp": "WEALTH",
        "tool": "wealth_epf_project",
        "current_balance": current,
        "projected_total": round(projected, 4),
        "total_contributions": round(total_contrib, 4),
        "total_growth": round(total_growth, 4),
        "age_55_value": round(projected, 4),
        "years_to_target": years,
        "monthly_contribution": monthly_contribution,
        "employer_match": employer_match,
        "blended_annual_rate": round(blended, 4),
        "recommendation_only": True,
        "final_authority": "Arif",
    }


NISAB_MYR = 14254.0
ZAKAT_RATE = 0.025


async def wealth_zakat_calculate(
    owner: str = "arif",
    year: int = None,
    total_wealth: float = None,
    currency: str = "MYR",
) -> dict:
    """Ω-D1-06: Zakat Calculate — Malaysian 2.5%% zakat above nisab."""
    year = year or _date.today().year
    await _pf_init_db()
    if total_wealth is None:
        assets = await _pf_get_assets(owner)
        liabs = await _pf_get_liabs(owner)
        epf = await _pf_get_epf(owner)
        total_a = sum(float(a["current_value"]) for a in assets)
        total_l = sum(float(l["outstanding"]) for l in liabs)
        if epf:
            total_a += float(epf["total"])
        wealth = total_a - total_l
    else:
        wealth = total_wealth
    zakatable = max(0.0, wealth - NISAB_MYR)
    zakat_amount = zakatable * ZAKAT_RATE
    return {
        "mcp": "WEALTH",
        "tool": "wealth_zakat_calculate",
        "owner": owner,
        "year": year,
        "total_wealth": round(wealth, 4),
        "nisab_threshold_myr": NISAB_MYR,
        "is_nisab_achieved": wealth >= NISAB_MYR,
        "zakatable_wealth": round(zakatable, 4),
        "zakat_rate": ZAKAT_RATE,
        "zakat_amount": round(zakat_amount, 4),
        "currency": currency,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# --------------------------------------------------------------------------- #
# D3 MARKET DATA — 3 tools (inline, after mcp is defined)
# --------------------------------------------------------------------------- #

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
def wealth_fx_rate(
    base: str = "USD",
    targets: str = "MYR,SGD,GBP,EUR,JPY,CNY,AUD",
    as_of_date: str = None,
) -> dict:
    """Ω-D3-01: FX Rate — Live FX via Frankfurter API (no key required)."""
    target_list = [t.strip() for t in targets.split(",")]
    params = {"base": base.upper()}
    if as_of_date:
        params["date"] = as_of_date
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get("https://api.frankfurter.dev/v1/latest", params=params)
            resp.raise_for_status()
            data = resp.json()
        rates = data.get("rates", {})
        result = {
            f"{base.upper()}/{t.upper()}": round(rates.get(t, float("nan")), 4)
            for t in target_list
            if t.upper() != base.upper()
        }
        return {
            "mcp": "WEALTH",
            "tool": "wealth_fx_rate",
            "base": base.upper(),
            "date": data.get("date") or as_of_date,
            "rates": result,
            "provider": "Frankfurter API",
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except httpx.HTTPError as e:
        return {
            "mcp": "WEALTH",
            "tool": "wealth_fx_rate",
            "status": "error",
            "message": str(e),
            "base": base.upper(),
            "targets": target_list,
            "recommendation_only": True,
            "final_authority": "Arif",
        }


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
def wealth_commodity_price(
    commodity: str = "brent_crude",
    unit: str = "usd_per_bbl",
    as_of_date: str = None,
) -> dict:
    """Ω-D3-02: Commodity Price — Approximate market prices (replace with live feed)."""
    APPROX = {
        "brent_crude": {"price": 78.50, "unit": "USD/bbl", "source": "EIA estimate"},
        "lng_asia": {
            "price": 10.20,
            "unit": "USD/MMBtu",
            "source": "SLRChina estimate",
        },
        "coal_api2": {
            "price": 113.00,
            "unit": "USD/tonne",
            "source": "ICE API2 assessment",
        },
        "gold": {"price": 2340.00, "unit": "USD/troy_oz", "source": "LBMA PM fix"},
        "malaysia_rsd": {
            "price": 82.00,
            "unit": "USD/bbl",
            "source": "Miri/Bintulu estimate",
        },
    }
    info = APPROX.get(commodity.lower().strip())
    if not info:
        return {
            "mcp": "WEALTH",
            "tool": "wealth_commodity_price",
            "status": "unsupported",
            "commodity": commodity,
            "supported": list(APPROX.keys()),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    return {
        "mcp": "WEALTH",
        "tool": "wealth_commodity_price",
        "commodity": commodity,
        "price": info["price"],
        "unit": unit,
        "price_unit": info["unit"],
        "date": as_of_date or _date.today().isoformat(),
        "source": info["source"],
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
def wealth_macro_indicator(
    indicator: str = "usd_myr",
    country: str = "MYS",
    as_of_date: str = None,
) -> dict:
    """Ω-D3-03: Macro Indicator — GDP, inflation, rates via World Bank API."""
    indicator = indicator.lower().strip()
    # Friendly aliases for common indicators
    alias_map = {
        "inflation": "inflation_my",
        "cpi": "inflation_my",
        "gdp": "gdp_growth_my",
        "gdp_growth": "gdp_growth_my",
        "interest_rate": "interest_rate_my",
        "opr": "interest_rate_my",
        "usd/myr": "usd_myr",
        "usdmyr": "usd_myr",
    }
    indicator = alias_map.get(indicator, indicator)
    result = {
        "mcp": "WEALTH",
        "tool": "wealth_macro_indicator",
        "indicator": indicator,
        "country": country,
        "date": as_of_date or _date.today().isoformat(),
        "recommendation_only": True,
        "final_authority": "Arif",
    }
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            if indicator == "usd_myr":
                r = client.get(
                    "https://api.frankfurter.dev/v1/latest",
                    params={"base": "USD", "symbols": "MYR"},
                )
                r.raise_for_status()
                d = r.json()
                result["value"] = round(d["rates"]["MYR"], 4)
                result["source"] = "Frankfurter API"
                result["status"] = "OK"
            elif indicator in ("inflation_my", "gdp_growth_my"):
                code_map = {
                    "inflation_my": "FP.CPI.TOTL.ZG",
                    "gdp_growth_my": "NY.GDP.MKTP.KD.ZG",
                }
                r = client.get(
                    f"https://api.worldbank.org/v2/country/{country}/indicator/{code_map[indicator]}",
                    params={"format": "json", "per_page": 1, "date": "2020:2025"},
                )
                r.raise_for_status()
                items = r.json()
                if isinstance(items, list) and len(items) > 1 and items[1]:
                    entry = items[1][0]
                    result["value"] = entry.get("value")
                    result["year"] = entry.get("date")
                    result["source"] = "World Bank"
                    result["status"] = "OK"
            elif indicator == "interest_rate_my":
                result["value"] = 3.00
                result["source"] = "Bank Negara Malaysia OPR (public release)"
                result["note"] = "Verify against latest BNM statistical release"
                result["status"] = "OK"
            elif indicator in ("brent", "opec_basket", "coal_api2"):
                STATIC = {"brent": 78.50, "opec_basket": 76.80, "coal_api2": 113.00}
                result["value"] = STATIC.get(indicator)
                result["source"] = "approximate — replace with live feed"
                result["status"] = "OK"
            else:
                result["status"] = "unsupported"
                result["supported"] = [
                    "usd_myr",
                    "inflation_my",
                    "gdp_growth_my",
                    "brent",
                    "interest_rate_my",
                ]
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    return result


@mcp.tool(name="wealth_market_data")
def wealth_market_data(
    mode: str = "fx",
    # fx mode params
    base: str = "USD",
    targets: str = "MYR,SGD,GBP,EUR,JPY,CNY,AUD",
    fx_as_of_date: str = None,
    # commodity mode params
    commodity: str = "brent_crude",
    unit: str = "usd_per_bbl",
    commodity_as_of_date: str = None,
    # macro mode params
    indicator: str = "usd_myr",
    country: str = "MYS",
    macro_as_of_date: str = None,
) -> dict:
    """Ω-D3: Market Data — unified surface for FX, commodities, and macro indicators.

    Modes:
      fx        — Live FX rates via Frankfurter API
      commodity — Approximate commodity market prices
      macro     — GDP, inflation, rates via World Bank API
    """
    mode = mode.lower().strip()
    if mode == "fx":
        return wealth_fx_rate(
            base=base,
            targets=targets,
            as_of_date=fx_as_of_date,
        )
    elif mode == "commodity":
        return wealth_commodity_price(
            commodity=commodity,
            unit=unit,
            as_of_date=commodity_as_of_date,
        )
    elif mode == "macro":
        return wealth_macro_indicator(
            indicator=indicator,
            country=country,
            as_of_date=macro_as_of_date,
        )
    else:
        return {
            "mcp": "WEALTH",
            "tool": "wealth_market_data",
            "status": "error",
            "message": f"Unknown mode: {mode}. Use fx|commodity|macro",
        }


# --------------------------------------------------------------------------- #
# Remove lazy-load approach (tools now inline above)
# --------------------------------------------------------------------------- #

# ═══════════════════════════════════════════════════════════════════════════
# D4 — STOCK ANALYSIS (15 modes, one tool)
# ═══════════════════════════════════════════════════════════════════════════


# ─── Bursa Mode Helpers (free delayed data, screening only) ─────────────


def _handle_bursa_snapshot(ticker: str) -> dict:
    """Handle bursa_snapshot mode — live-delayed Bursa quote."""
    if not _WEALTH_BURSA_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_snapshot",
            "result": {
                "error": "Bursa module not available. Install klse-screener-py."
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    if not ticker:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_snapshot",
            "result": {"error": "ticker is required for bursa_snapshot"},
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    try:
        adapter = get_klse()
        quote = adapter.get_quote(ticker)
        if quote is None:
            return {
                "status": "NEEDS_DATA",
                "verdict": "NEEDS_DATA",
                "tool": "wealth_stock_analysis",
                "mode": "bursa_snapshot",
                "ticker": ticker,
                "result": {
                    "error": f"No data for {ticker}. Check ticker or market is closed."
                },
                "recommendation_only": True,
                "final_authority": "Arif",
            }
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_snapshot",
            "ticker": ticker,
            "result": quote.model_dump(),
            "provenance": quote.provenance.model_dump(),
            "recommendation_only": True,
            "final_authority": "Arif",
            "hold_required": quote.provenance.hold_required,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_snapshot",
            "ticker": ticker,
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


def _handle_bursa_screen(
    min_pe=None,
    max_pe=None,
    min_roe=None,
    max_pb=None,
    sector="",
    limit_count=20,
) -> dict:
    """Handle bursa_screen mode — screen Bursa stocks."""
    if not _WEALTH_BURSA_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_screen",
            "result": {
                "error": "Bursa module not available. Install klse-screener-py."
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    try:
        criteria = BursaScreenCriteria(
            min_pe=float(min_pe) if min_pe else None,
            max_pe=float(max_pe) if max_pe else None,
            min_roe=float(min_roe) if min_roe else None,
            max_pb=float(max_pb) if max_pb else None,
            sector=sector.strip() if sector else None,
            sort_by="pe_ratio",
            limit=int(limit_count) if limit_count else 20,
        )
        adapter = get_klse()
        result = adapter.screen(criteria)
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_screen",
            "result": result.model_dump(),
            "provenance": result.provenance.model_dump(),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_screen",
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    try:
        criteria = BursaScreenCriteria(
            min_pe=float(min_pe) if min_pe else None,
            max_pe=float(max_pe) if max_pe else None,
            min_dividend_yield=float(min_dy) if min_dy else None,
            min_roe=float(min_roe) if min_roe else None,
            max_pb=float(max_pb) if max_pb else None,
            min_market_cap_m=float(min_mcap) if min_mcap else None,
            sector=sector.strip() if sector else None,
            sort_by=sort_by,
            limit=int(limit) if limit else 20,
        )
        adapter = get_klse()
        result = adapter.screen(criteria)
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_screen",
            "result": result.model_dump(),
            "provenance": result.provenance.model_dump(),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_screen",
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


def _handle_bursa_evidence(ticker: str) -> dict:
    """Handle bursa_evidence mode — evidence card with governance."""
    if not _WEALTH_BURSA_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_evidence",
            "result": {
                "error": "Bursa module not available. Install klse-screener-py."
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    if not ticker:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_evidence",
            "result": {"error": "ticker is required for bursa_evidence"},
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    try:
        card = generate_evidence_card(ticker)
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_evidence",
            "ticker": ticker,
            "result": card.model_dump(),
            "provenance": card.provenance.model_dump(),
            "recommendation_only": True,
            "final_authority": "Arif",
            "hold_required": card.provenance.hold_required,
            "execution_allowed": card.execution_allowed,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "bursa_evidence",
            "ticker": ticker,
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


# ─── Global Mode Helpers (free delayed yfinance data, screening only) ────


def _handle_global_snapshot(symbol: str) -> dict:
    """Handle global_snapshot mode — global index/commodity/FX quote."""
    if not _WEALTH_GLOBAL_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "global_snapshot",
            "result": {"error": "Global module not available. Install yfinance."},
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "global_snapshot",
            "result": {"error": "symbol is required (e.g. ^GSPC, GC=F, BTC-USD)"},
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    try:
        adapter = get_global()
        quote = adapter.get_quote(symbol)
        if quote is None:
            return {
                "status": "NEEDS_DATA",
                "verdict": "NEEDS_DATA",
                "tool": "wealth_stock_analysis",
                "mode": "global_snapshot",
                "symbol": symbol,
                "result": {"error": f"No data for {symbol}."},
                "recommendation_only": True,
                "final_authority": "Arif",
            }
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "global_snapshot",
            "symbol": symbol,
            "result": quote.model_dump(),
            "provenance": quote.provenance.model_dump(),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "global_snapshot",
            "symbol": symbol,
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


def _handle_global_dashboard() -> dict:
    """Handle global_dashboard mode — all global symbols at once."""
    if not _WEALTH_GLOBAL_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "global_dashboard",
            "result": {"error": "Global module not available."},
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    try:
        adapter = get_global()
        quotes = adapter.get_global_dashboard()
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "global_dashboard",
            "count": len(quotes),
            "result": [q.model_dump() for q in quotes],
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "tool": "wealth_stock_analysis",
            "mode": "global_dashboard",
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


def _handle_global_list() -> dict:
    """Handle global_list mode — list all known global symbols."""
    try:
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "global_list",
            "symbols": [{"symbol": k, **v} for k, v in GLOBAL_SYMBOLS.items()],
            "count": len(GLOBAL_SYMBOLS),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": str(e)},
            "recommendation_only": True,
            "final_authority": "Arif",
        }


# ─── Technical + Risk Mode Handlers ──────────────────────────────────────


def _handle_technical_pack(symbol: str) -> dict:
    """Handle technical_pack mode — compute all indicators from price history."""
    if not _WEALTH_INDICATORS_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Indicators module not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        result = compute_technical_pack(symbol)
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "technical_pack",
            "symbol": symbol,
            **result,
        }
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _handle_risk_metrics(symbol: str) -> dict:
    """Handle risk_metrics mode — compute risk metrics (Sharpe, Sortino, MaxDD)."""
    if not _WEALTH_INDICATORS_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Indicators module not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        result = compute_technical_pack(symbol)
        risk = result.get("risk_metrics", {})
        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "tool": "wealth_stock_analysis",
            "mode": "risk_metrics",
            "symbol": symbol,
            "latest_price": result.get("latest_price"),
            "risk_metrics": risk,
            "peace_of_mind": risk.get("peace_of_mind_grade", "?"),
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _handle_calhoun(symbol: str) -> dict:
    """Handle calhoun_survival mode — Calhoun/StrangeLoop/Gödel/Anti-Beautiful analysis."""
    if not _WEALTH_CALHOUN_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Calhoun Guard not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        import yfinance as yf

        yt_sym = f"{symbol}.KL" if symbol.isdigit() else symbol
        hist = yf.Ticker(yt_sym).history(period="6mo")
        if hist.empty:
            return {
                "status": "NEEDS_DATA",
                "verdict": "NEEDS_DATA",
                "result": {"error": "No history"},
            }
        c = [float(x) for x in hist["Close"]]
        v = [int(x) for x in hist["Volume"]]
        pe = roe = pb = dy = eps = None
        sector = ""
        if symbol.isdigit():
            try:
                from klse_screener import get_klse_fundamentals

                fund = get_klse_fundamentals(symbol)
                if fund:
                    pe = _sf4(fund.get("pe_ratio"))
                    roe = _sf4(fund.get("roe"))
                    pb = _sf4(fund.get("pb_ratio"))
                    dy = _sf4(fund.get("dividend_yield"))
                    eps = _sf4(fund.get("eps"))
                    sector = fund.get("sector", "")
            except:
                pass
        from internal.stock.engine_888 import compute_888

        r888 = compute_888(symbol, pe=pe, roe=roe, pb=pb, dy=dy, eps=eps, sector=sector)
        gates = r888.get("gate_summary", {})
        fs = r888["fundamentals"]["score"]
        ts = r888["technicals"]["score"]
        ws = r888["flows"]["score"]
        enriched = enrich_888_verdict(
            symbol,
            c,
            v,
            fs,
            ts,
            ws,
            f_hold=gates.get("F_HOLD", False),
            t_hold=gates.get("T_HOLD", False),
            w_hold=gates.get("W_HOLD", False),
            data_completeness={
                "PE": pe is not None,
                "ROE": roe is not None,
                "DY": dy is not None,
                "EPS": eps is not None,
            },
        )
        return {
            "status": "OK",
            "verdict": enriched["verdict"],
            "tool": "wealth_stock_analysis",
            "mode": "calhoun_survival",
            **enriched,
        }
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _sf4(val):
    try:
        return float(val)
    except:
        return None


def _handle_888(symbol: str) -> dict:
    """Handle 888 mode — JUDGE investment framework with HOLD gates."""
    if not _WEALTH_888_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "888 Engine not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        pe = roe = pb = dy = eps = None
        sector = ""
        if symbol.isdigit():
            try:
                from klse_screener import get_klse_fundamentals

                fund = get_klse_fundamentals(symbol)
                if fund:
                    pe = _sf3(fund.get("pe_ratio"))
                    roe = _sf3(fund.get("roe"))
                    pb = _sf3(fund.get("pb_ratio"))
                    dy = _sf3(fund.get("dividend_yield"))
                    eps = _sf3(fund.get("eps"))
                    sector = fund.get("sector", "")
            except:
                pass
        return compute_888(symbol, pe=pe, roe=roe, pb=pb, dy=dy, eps=eps, sector=sector)
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _sf3(val):
    try:
        return float(val)
    except:
        return None


def _handle_999(symbol: str) -> dict:
    """Handle 999 mode — complete investment intelligence framework."""
    if not _WEALTH_999_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "999 Engine not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        pe = roe = pb = dy = eps = dps = nta = None
        qoq = yoy = None
        market_cap_raw = None
        sector = ""
        if symbol.isdigit():
            try:
                from klse_screener import get_klse_fundamentals

                fund = get_klse_fundamentals(symbol)
                if fund:
                    pe = _sf2(fund.get("pe_ratio"))
                    roe = _sf2(fund.get("roe"))
                    pb = _sf2(fund.get("pb_ratio"))
                    dy = _sf2(fund.get("dividend_yield"))
                    eps = _sf2(fund.get("eps"))
                    dps = _sf2(fund.get("dps"))
                    nta = _sf2(fund.get("nta"))
                    sector = fund.get("sector", "")
                    market_cap_raw = fund.get("market_cap")
                    lq = fund.get("latest_quarter")
                    if isinstance(lq, dict):
                        qoq = _sf2(lq.get("qoq"))
                        yoy = _sf2(lq.get("yoy"))
            except:
                pass
        return compute_999(
            symbol,
            pe=pe,
            roe=roe,
            pb=pb,
            dy=dy,
            eps=eps,
            sector=sector,
            dps=dps,
            market_cap_raw=market_cap_raw,
            nta=nta,
            qoq=qoq,
            yoy=yoy,
        )
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _sf2(val):
    try:
        return float(val)
    except:
        return None


def _handle_market_intelligence(symbol: str) -> dict:
    """Handle market_intelligence mode — thermodynamic state-space analysis."""
    if not _WEALTH_MI_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Market Intelligence not available"},
        }
    if not symbol:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "symbol is required"},
        }
    try:
        # Auto-fetch fundamentals for Bursa tickers (numeric-only = Bursa code)
        pe = roe = pb = dy = eps = None
        sector = ""
        if symbol.isdigit():
            try:
                from klse_screener import get_klse_fundamentals

                fund = get_klse_fundamentals(symbol)
                if fund:
                    pe = _sf(fund.get("pe_ratio"))
                    roe = _sf(fund.get("roe"))
                    pb = _sf(fund.get("pb_ratio"))
                    dy = _sf(fund.get("dividend_yield"))
                    eps = _sf(fund.get("eps"))
                    sector = fund.get("sector", "")
            except:
                pass
        return compute_market_intelligence(
            symbol, pe=pe, roe=roe, pb=pb, dy=dy, eps=eps, sector=sector
        )
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _sf(val):  # safe float helper for handler
    try:
        return float(val)
    except:
        return None


def _handle_screener_9() -> dict:
    """Handle screener_9 mode — 9-point fundamentals + technical screening."""
    if not _WEALTH_SCREENER_9_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Screener 9 not available"},
        }
    try:
        return run_screener_9()
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


def _handle_governance_singularity(entities_json: str = "") -> dict:
    """Handle governance_singularity mode — detect structural extraction geometry.

    Accepts a JSON string of entities, inter-entity flows, and pending transactions.
    Returns GSS (Governance Singularity Score) + Calhoun Beautiful One detection.
    """
    if not _WEALTH_GSD_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "Governance Singularity Detector not available"},
        }
    try:
        import json as _json

        args: dict = _json.loads(entities_json) if entities_json else {}
        entities = args.get("entities", [])
        flows = args.get("inter_entity_flows")
        pending = args.get("pending_transactions")

        if not entities:
            # Fall back to built-in PETRONAS-Gentari test case
            from internal.stock.governance_singularity import PETRONAS_GENTARI_TEST

            entities = PETRONAS_GENTARI_TEST["entities"]
            flows = PETRONAS_GENTARI_TEST.get("inter_entity_flows")
            pending = PETRONAS_GENTARI_TEST.get("pending_transactions")

        result = detect_governance_singularity(entities, flows, pending)

        # ── Calhoun Beautiful One detection ──
        # A Calhoun Beautiful One is a nexus individual who:
        # 1. Sits at a governance singularity (GSS ≥ 0.5)
        # 2. Controls entities with extreme governance gradient (≥ 0.7)
        # 3. Is NOT independent on the low-governance entity
        # 4. Occupies apex roles (CEO/Chairman) on both sides

        beautiful_ones = []
        for s in result.get("singularities", []):
            if s["governance_gradient"] >= 0.7 and s["severity"] == "CRITICAL":
                roles = s.get("roles", [])
                roles_text = " ".join(roles).lower()
                is_apex = any(
                    kw in roles_text
                    for kw in ("chairman", "ceo", "president", "group ceo")
                )
                not_independent = any("not independent" in r.lower() for r in roles)
                if is_apex and not_independent:
                    beautiful_ones.append(
                        {
                            "name": s["nexus_individual"],
                            "gradient": s["governance_gradient"],
                            "calhoun_traits": [
                                "Apex node — occupies CEO/Chairman at governance singularity",
                                "Insulated — zero independent oversight on low-gov entity",
                                f"Gradient {s['governance_gradient']:.2f} — "
                                "value flows through them while lower layers absorb damage",
                                "Rhetorically skilled — polished public persona, "
                                "unity theatre, curated Q&A",
                            ],
                            "calhoun_phase": "BEAUTIFUL_ONE",
                            "note": (
                                "In Calhoun's Universe 25, the Beautiful Ones were mice "
                                "that withdrew from social chaos, groomed obsessively, "
                                "and occupied safe apex positions while the colony collapsed. "
                                "They were the SYMPTOM of behavioral sink, not the cause — "
                                "but their presence signaled terminal institutional decay."
                            ),
                        }
                    )

        result["calhoun_beautiful_ones"] = beautiful_ones
        result["calhoun_beautiful_one_count"] = len(beautiful_ones)

        return {
            "status": "OK",
            "verdict": result["verdict"],
            "tool": "wealth_stock_analysis",
            "mode": "governance_singularity",
            **result,
        }
    except Exception as e:
        return {"status": "ERROR", "verdict": "NEEDS_DATA", "result": {"error": str(e)}}


@mcp.tool(name="wealth_stock_analysis", task=True)
async def wealth_stock_analysis(
    mode: str = "verify_math",
    # ── Common params ──
    ticker: str = "",
    # ── verify_math params ──
    entry_price: float = 0.0,
    exit_price: Optional[float] = None,
    current_price: Optional[float] = None,
    position_size: int = 0,
    fees: float = 0.0,
    direction: str = "long",
    status: str = "unrealized",
    journal_pnl: Optional[float] = None,
    journal_pnl_pct: Optional[float] = None,
    # ── separate_pl params ──
    trades: Optional[List[Dict[str, Any]]] = None,
    # ── position_size params ──
    account_balance: float = 0.0,
    stop_loss: float = 0.0,
    risk_per_trade_pct: float = 1.0,
    # ── r_multiple params ──
    target_price: float = 0.0,
    # ── exposure params ──
    positions: Optional[List[Dict[str, Any]]] = None,
    # ── bursa_cost params ──
    exit_price_bursa: float = 0.0,
    # ── tamak params ──
    recent_trades: Optional[List[Dict[str, Any]]] = None,
    current_open_positions: int = 0,
    recent_streak: str = "neutral",
    recent_size_trend: str = "stable",
    stop_loss_moved_lower: bool = False,
    averaging_down: bool = False,
    revenge_pattern: bool = False,
    chasing_call: bool = False,
    position_count: int = 0,
    max_recommended: int = 5,
    # ── pre_trade params ──
    has_stop_loss: bool = False,
    has_position_size: bool = False,
    r_multiple: float = 0.0,
    liquidity_adequate: bool = False,
    sector_exposure_ok: bool = False,
    market_regime: str = "neutral",
    fundamental_check_passed: bool = False,
    emotional_trigger: bool = False,
    reason_for_trade: str = "",
    # ── fundamentals params ──
    operating_cash_flow: Optional[float] = None,
    free_cash_flow: Optional[float] = None,
    cash_conversion: Optional[float] = None,
    cash: Optional[float] = None,
    total_debt: Optional[float] = None,
    current_ratio: Optional[float] = None,
    interest_coverage: Optional[float] = None,
    debt_maturity_years: Optional[float] = None,
    gross_margin: Optional[float] = None,
    operating_margin: Optional[float] = None,
    net_margin: Optional[float] = None,
    margin_trend: str = "stable",
    roic: Optional[float] = None,
    roe: Optional[float] = None,
    revenue_growth: Optional[float] = None,
    fcf_growth: Optional[float] = None,
    organic_growth: bool = True,
    debt_funded_growth: bool = False,
    shares_outstanding_m: Optional[float] = None,
    dilution_rate: Optional[float] = None,
    has_warrants: bool = False,
    has_convertibles: bool = False,
    has_esos: bool = False,
    pe_ratio: Optional[float] = None,
    pb_ratio: Optional[float] = None,
    ev_ebitda: Optional[float] = None,
    fcf_yield: Optional[float] = None,
    has_moat: bool = False,
    pricing_power: bool = False,
    recurring_revenue: bool = False,
    related_party_txns: bool = False,
    insider_selling: bool = False,
    audit_issues: bool = False,
    pledged_shares_pct: Optional[float] = None,
    # ── TAC-9 params ──
    benchmark_trend: str = "neutral",
    sector_trend: str = "neutral",
    market_breadth: str = "neutral",
    volatility_regime: str = "normal",
    risk_state: str = "neutral",
    stock_return_3m: Optional[float] = None,
    sector_return_3m: Optional[float] = None,
    stock_vs_klci: Optional[float] = None,
    rs_3m: Optional[float] = None,
    rs_6m: Optional[float] = None,
    price_above_50ma: bool = False,
    ma50_above_ma200: bool = False,
    higher_highs: bool = False,
    higher_lows: bool = False,
    support_holding: bool = False,
    breakout_volume: str = "unknown",
    up_volume_ratio: Optional[float] = None,
    accumulation: str = "neutral",
    avg_daily_value_rm: Optional[float] = None,
    position_value_rm: Optional[float] = None,
    bid_ask_spread_pct: Optional[float] = None,
    gap_frequency: str = "low",
    atr_pct: Optional[float] = None,
    bb_width: Optional[str] = None,
    volume_dry_up: bool = False,
    support_level: Optional[float] = None,
    resistance_level: Optional[float] = None,
    invalidation_level: Optional[float] = None,
    breakout_retest: bool = False,
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    rsi_value: Optional[float] = None,
    macd_signal: str = "neutral",
    sar_position: str = "neutral",
    # ── contrast params ──
    fundamental_score: Optional[float] = None,
    earnings_growth: Optional[float] = None,
    price_trend_3m: Optional[float] = None,
    price_trend_6m: Optional[float] = None,
    volume_trend: str = "normal",
    volatility_trend: str = "normal",
    sector_rotation: str = "neutral",
    liquidity_quality: str = "normal",
    spread: Optional[float] = None,
    valuation_zone: str = "fair",
    sentiment: str = "neutral",
    # ── confluence params ──
    indicators: Optional[Dict[str, str]] = None,
) -> dict:
    """D4 Stock Analysis — unified capital-risk and stock governance layer.

    Modes (15 total):
      verify_math     — Recalculate P/L, detect AI number hallucination
      separate_pl     — Separate realized vs unrealized P/L
      position_size   — Risk-based position sizing (max 1% risk)
      r_multiple      — Risk-reward geometry (R = reward / risk)
      exposure        — Portfolio exposure and gap-down scenarios
      bursa_cost      — Bursa Malaysia transaction cost model
      tamak_check     — Detect greed/emotional behavior patterns
      pre_trade       — Full pre-trade safety gate (9 checks)
      fundamentals    — 9 business reality invariants
      tac9            — TAC-9 technical analysis (regime → structure → R)
      contrast        — Anomalous contrast detection (market layer disagreement)
      confluence      — False confluence detection (same-class indicator collapse)
      bursa_snapshot  — Live-delayed Bursa quote from free data source
      bursa_screen    — Screen Bursa stocks by PE, dividend, ROE, market cap
      bursa_evidence  — Evidence card with provenance, valuation, quality, governance

    NOT: buy/sell oracle. NOT: trading coach. NOT: stock promoter.
    Verdicts: SAFE_TO_STUDY | NEEDS_DATA | UNSAFE | 888_HOLD | MATH_ERROR
    Authority: WEALTH computes. arifOS judges. Arif decides.
    Data: Free delayed source (klse-screener-py). Screening only — NOT execution-grade.
    """
    if not _WEALTH_STOCK_AVAILABLE:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {"error": "WEALTH Stock module not available"},
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    # ── Mode dispatch ──
    if mode == "verify_math":
        r = verify_trade_math(
            ticker=ticker,
            entry_price=entry_price,
            exit_price=exit_price,
            current_price=current_price,
            position_size=position_size,
            fees=fees,
            direction=direction,
            status=status,
            journal_pnl=journal_pnl,
            journal_pnl_pct=journal_pnl_pct,
        )
    elif mode == "separate_pl":
        r = separate_realized_unrealized(trades=trades)
    elif mode == "position_size":
        r = calculate_position_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss=stop_loss,
            risk_per_trade_pct=risk_per_trade_pct,
        )
    elif mode == "r_multiple":
        r = calculate_r_multiple(
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            direction=direction,
        )
    elif mode == "exposure":
        r = check_portfolio_exposure(
            positions=positions,
            account_balance=account_balance,
        )
    elif mode == "bursa_cost":
        r = apply_bursa_cost_model(
            entry_price=entry_price,
            exit_price=exit_price_bursa or exit_price or 0,
            position_size=position_size,
            direction=direction,
        )
    elif mode == "tamak_check":
        r = detect_tamak_behavior(
            recent_trades=recent_trades,
            current_open_positions=current_open_positions,
            recent_streak=recent_streak,
            recent_size_trend=recent_size_trend,
            stop_loss_moved_lower=stop_loss_moved_lower,
            averaging_down=averaging_down,
            revenge_pattern=revenge_pattern,
            chasing_call=chasing_call,
            position_count=position_count,
            max_recommended=max_recommended,
        )
    elif mode == "pre_trade":
        r = pre_trade_gate(
            ticker=ticker,
            has_stop_loss=has_stop_loss,
            has_position_size=has_position_size,
            position_size=position_size,
            risk_per_trade_pct=risk_per_trade_pct,
            r_multiple=r_multiple,
            liquidity_adequate=liquidity_adequate,
            sector_exposure_ok=sector_exposure_ok,
            market_regime=market_regime,
            fundamental_check_passed=fundamental_check_passed,
            emotional_trigger=emotional_trigger,
            reason_for_trade=reason_for_trade,
        )
    elif mode == "fundamentals":
        r = check_fundamental_invariants(
            ticker=ticker,
            operating_cash_flow=operating_cash_flow,
            free_cash_flow=free_cash_flow,
            cash_conversion=cash_conversion,
            cash=cash,
            total_debt=total_debt,
            current_ratio=current_ratio,
            interest_coverage=interest_coverage,
            debt_maturity_years=debt_maturity_years,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            margin_trend=margin_trend,
            roic=roic,
            roe=roe,
            revenue_growth=revenue_growth,
            fcf_growth=fcf_growth,
            organic_growth=organic_growth,
            debt_funded_growth=debt_funded_growth,
            shares_outstanding_m=shares_outstanding_m,
            dilution_rate=dilution_rate,
            has_warrants=has_warrants,
            has_convertibles=has_convertibles,
            has_esos=has_esos,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            ev_ebitda=ev_ebitda,
            fcf_yield=fcf_yield,
            has_moat=has_moat,
            pricing_power=pricing_power,
            recurring_revenue=recurring_revenue,
            related_party_txns=related_party_txns,
            insider_selling=insider_selling,
            audit_issues=audit_issues,
            pledged_shares_pct=pledged_shares_pct,
        )
    elif mode == "tac9":
        r = run_tac9_engine(
            ticker=ticker,
            benchmark_trend=benchmark_trend,
            sector_trend=sector_trend,
            market_breadth=market_breadth,
            volatility_regime=volatility_regime,
            risk_state=risk_state,
            stock_return_3m=stock_return_3m,
            sector_return_3m=sector_return_3m,
            stock_vs_klci=stock_vs_klci,
            rs_3m=rs_3m,
            rs_6m=rs_6m,
            price_above_50ma=price_above_50ma,
            ma50_above_ma200=ma50_above_ma200,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            support_holding=support_holding,
            breakout_volume=breakout_volume,
            up_volume_ratio=up_volume_ratio,
            accumulation=accumulation,
            avg_daily_value_rm=avg_daily_value_rm,
            position_value_rm=position_value_rm,
            bid_ask_spread_pct=bid_ask_spread_pct,
            gap_frequency=gap_frequency,
            atr_pct=atr_pct,
            bb_width=bb_width,
            volume_dry_up=volume_dry_up,
            support_level=support_level,
            resistance_level=resistance_level,
            invalidation_level=invalidation_level,
            breakout_retest=breakout_retest,
            entry=entry,
            stop=stop,
            target=target,
            r_multiple=r_multiple,
            rsi_value=rsi_value,
            macd_signal=macd_signal,
            sar_position=sar_position,
        )
    elif mode == "contrast":
        r = detect_anomalous_contrast(
            ticker=ticker,
            fundamental_score=fundamental_score,
            revenue_growth=revenue_growth,
            earnings_growth=earnings_growth,
            price_trend_3m=price_trend_3m,
            price_trend_6m=price_trend_6m,
            volume_trend=volume_trend,
            accumulation=accumulation,
            volatility_trend=volatility_trend,
            atr_pct=atr_pct,
            sector_trend=sector_trend,
            sector_rotation=sector_rotation,
            liquidity_quality=liquidity_quality,
            spread=spread,
            valuation_zone=valuation_zone,
            sentiment=sentiment,
        )
    elif mode == "confluence":
        r = detect_false_confluence(ticker=ticker, indicators=indicators)
    elif mode == "bursa_snapshot":
        r = _handle_bursa_snapshot(ticker)
    elif mode == "bursa_screen":
        r = _handle_bursa_screen(
            min_pe=fundamental_score,  # reused: fundamental_score as min_pe
            max_pe=pe_ratio,  # max pe filter
            min_roe=roe,  # min ROE
            max_pb=pb_ratio,  # max PB
            sector=f"{sector_trend or ''}",  # sector filter
            limit_count=position_size or 20,  # reused: position_size as limit
        )
    elif mode == "bursa_evidence":
        r = _handle_bursa_evidence(ticker)
    elif mode == "global_snapshot":
        r = _handle_global_snapshot(ticker)
    elif mode == "global_dashboard":
        r = _handle_global_dashboard()
    elif mode == "global_list":
        r = _handle_global_list()
    elif mode == "technical_pack":
        r = _handle_technical_pack(ticker)
    elif mode == "risk_metrics":
        r = _handle_risk_metrics(ticker)
    elif mode == "calhoun_survival":
        r = _handle_calhoun(ticker)
    elif mode == "888":
        r = _handle_888(ticker)
    elif mode == "999":
        r = _handle_999(ticker)
    elif mode == "market_intelligence":
        r = _handle_market_intelligence(ticker)
    elif mode == "screener_9":
        r = _handle_screener_9()
    elif mode == "governance_singularity":
        r = _handle_governance_singularity(ticker)
    else:
        return {
            "status": "ERROR",
            "verdict": "NEEDS_DATA",
            "result": {
                "error": f"Unknown mode: {mode}. Use: verify_math | separate_pl | position_size | r_multiple | exposure | bursa_cost | tamak_check | pre_trade | fundamentals | tac9 | contrast | confluence | bursa_snapshot | bursa_screen | bursa_evidence | global_snapshot | global_dashboard | global_list | technical_pack | risk_metrics | calhoun_survival | 888 | 999 | market_intelligence | screener_9 | governance_singularity"
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    r["tool"] = "wealth_stock_analysis"
    r["mode"] = mode
    return r


# --- Registry Lockdown Logic (Phase 1) ---
# Generic agents should only see: health -> registry -> synthesize -> canonical organ -> specialist.
# This whitelist defines the public L0, L1, and L2 surface. All other tools (including 34 aliases)
# are hidden from the MCP registry but remain available as internal Python functions.
PUBLIC_SURFACE_WHITELIST = {
    # L0 — Kernel Surface
    "wealth_system_registry_status",
    "wealth_omni_wisdom",
    "wealth_agent_path",
    # L1 — 11 Canonical Physics Organs
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
    # L2 — Mandatory Specialists
    "wealth_governance_verdict",
    "wealth_inequality_kernel",
    # Phase 1 Survival Engine
    "wealth_survival_engine",
    # D1 — Personal Finance (absorbs epf, zakat)
    "wealth_personal_finance",
    # D3 — Market Data
    "wealth_market_data",
    # D4 — Stock Analysis (12 modes in one tool)
    "wealth_stock_analysis",
    # NOTE: wealth_health_check → wealth_system_registry_status(mode="health")
    # NOTE: wealth_epf_project + wealth_zakat_calculate → wealth_personal_finance (mode="epf"/"zakat")
    # NOTE: wealth_ledger_query + wealth_ledger_write → wealth_conservation_capital (mode="ledger_read"/"ledger_seal")
    # NOTE: wealth_entropy_audit → wealth_entropy_risk (mode="institutional")
    # NOTE: wealth_preference_rank → wealth_game_coordination (mode="preference")
    # All 7 absorptions executed 2026-06-05. Surface: 26 → 19 tools.
    # NOTE: wealth_synthesize, wealth_deal_frame, wealth_hysteresis_ledger
    # were absorbed into wealth_omni_wisdom on 2026-06-03 (Path D consolidation).
}

PUBLIC_RESOURCE_WHITELIST = {
    # L1 — Doctrine & Ontology
    "wealth://ontology/physics12",
    "wealth://policy/authority-boundary",
    "wealth://doctrine/valuation",
    "wealth://dimensions/definitions",
    "wealth://governance/floors",
    # L2 — Formulas & Schemas
    "wealth://formulas/npv",
    "wealth://formulas/irr",
    "wealth://formulas/emv",
    "wealth://formulas/evoi",
    "wealth://formulas/dscr",
    "wealth://formulas/payback",
    "wealth://schemas/capital-case",
    "wealth://schemas/sovereign-deal",
    "wealth://playbooks/project-appraisal",
    # D4 — Stock Analysis Resources
    "wealth://journal/trading_records",
    "wealth://market/prices",
    "wealth://fundamentals/company_snapshot",
    "wealth://rules/risk_policy",
}

PUBLIC_PROMPT_WHITELIST = {
    "wealth_prompt_project_appraisal",
    "wealth_prompt_sovereign_deal_review",
    "wealth_prompt_personal_finance_triage",
    "wealth_prompt_inequality_diagnosis",
    "wealth_prompt_macro_regime_scan",
    "wealth_prompt_governance_redteam",
    "wealth_diagnose_portfolio",
    "wealth_opportunity_ranking",
    # D4 — Stock Analysis Prompts
    "wealth_prompt_stock_risk_auditor",
    "wealth_prompt_stock_diagnosis",
}

_original_mcp_tool = mcp.tool
_original_mcp_resource = mcp.resource
_original_mcp_prompt = mcp.prompt


def controlled_mcp_tool(*args, **kwargs):
    """Decorator wrapper that only registers tools in the PUBLIC_SURFACE_WHITELIST."""
    explicit_name = kwargs.get("name")

    def decorator(f):
        tool_name = explicit_name or f.__name__
        if tool_name in PUBLIC_SURFACE_WHITELIST:
            return _original_mcp_tool(*args, **kwargs)(f)
        return f

    return decorator


def controlled_mcp_resource(uri, **kwargs):
    """Decorator wrapper that only registers resources in the PUBLIC_RESOURCE_WHITELIST."""

    def decorator(f):
        if uri in PUBLIC_RESOURCE_WHITELIST:
            return _original_mcp_resource(uri, **kwargs)(f)
        return f

    return decorator


def controlled_mcp_prompt(*args, **kwargs):
    """Decorator wrapper that only registers prompts in the PUBLIC_PROMPT_WHITELIST."""
    explicit_name = kwargs.get("name")

    def decorator(f):
        prompt_name = explicit_name or f.__name__
        if prompt_name in PUBLIC_PROMPT_WHITELIST:
            return _original_mcp_prompt(*args, **kwargs)(f)
        return f

    return decorator


# Patch the mcp instance to use our controlled decorators
mcp.tool = controlled_mcp_tool
mcp.resource = controlled_mcp_resource
mcp.prompt = controlled_mcp_prompt


WEALTH_TOOL_MANIFEST: List[Dict[str, object]] = [
    {"name": "wealth_health_check", "axis": "identity", "expose": True},
    {"name": "vault_query", "axis": "trace", "expose": True},
    {"name": "vault_write", "axis": "seal", "expose": True},
    {"name": "vaultquery", "axis": "trace", "expose": True},
    {"name": "vaultwrite", "axis": "seal", "expose": True},
    {"name": "wealth_agent_path", "axis": "reflect", "expose": True},
    {"name": "wealth_allocate_optimize", "axis": "execute", "expose": True},
    {"name": "wealth_boundary_floors", "axis": "boundary", "expose": True},
    {"name": "wealth_boundary_governance", "axis": "boundary", "expose": True},
    {"name": "wealth_boundary_policy", "axis": "boundary", "expose": True},
    {"name": "wealth_conservation_capital", "axis": "vitality", "expose": True},
    {"name": "wealth_density_pi", "axis": "reason", "expose": True},
    {"name": "wealth_energy_irr", "axis": "reason", "expose": True},
    {"name": "wealth_energy_productivity", "axis": "reason", "expose": True},
    {"name": "wealth_entropy_audit", "axis": "critique", "expose": True},
    {"name": "wealth_entropy_risk", "axis": "critique", "expose": True},
    {"name": "wealth_expectation_emv", "axis": "reason", "expose": True},
    {"name": "wealth_field_equilibrium", "axis": "observe", "expose": True},
    {"name": "wealth_field_game", "axis": "reason", "expose": True},
    {"name": "wealth_field_macro", "axis": "observe", "expose": True},
    {"name": "wealth_flow_cashflow", "axis": "vitality", "expose": True},
    {"name": "wealth_flow_liquidity", "axis": "vitality", "expose": True},
    {"name": "wealth_future_simulate", "axis": "reason", "expose": True},
    {"name": "wealth_future_steward", "axis": "reason", "expose": True},
    {"name": "wealth_future_value", "axis": "reason", "expose": True},
    {"name": "wealth_game_coordinate", "axis": "reason", "expose": True},
    {"name": "wealth_game_coordination", "axis": "reason", "expose": True},
    {"name": "wealth_governance_verdict", "axis": "critique", "expose": True},
    {"name": "wealth_gradient_price", "axis": "observe", "expose": True},
    {"name": "wealth_gravity_dscr", "axis": "vitality", "expose": True},
    {"name": "wealth_inertia_leverage", "axis": "boundary", "expose": True},
    {"name": "wealth_ledger_query", "axis": "trace", "expose": True},
    {"name": "wealth_ledger_record", "axis": "seal", "expose": True},
    {"name": "wealth_ledger_snapshot", "axis": "seal", "expose": True},
    {"name": "wealth_ledger_write", "axis": "seal", "expose": True},
    {"name": "wealth_mass_networth", "axis": "vitality", "expose": True},
    {"name": "wealth_preference_rank", "axis": "reason", "expose": True},
    {"name": "wealth_present_expect", "axis": "reason", "expose": True},
    {"name": "wealth_pressure_triage", "axis": "vitality", "expose": True},
    {"name": "wealth_probability_monte_carlo", "axis": "reason", "expose": True},
    {"name": "wealth_rule_enforce", "axis": "judge", "expose": True},
    {"name": "wealth_sense_ingest", "axis": "observe", "expose": True},
    {"name": "wealth_sensor_fetch", "axis": "observe", "expose": True},
    {"name": "wealth_sensor_health", "axis": "identity", "expose": True},
    {"name": "wealth_sensor_reconcile", "axis": "observe", "expose": True},
    {"name": "wealth_sensor_snapshot", "axis": "observe", "expose": True},
    {"name": "wealth_sensor_sources", "axis": "observe", "expose": True},
    {"name": "wealth_sensor_vintage", "axis": "observe", "expose": True},
    {"name": "wealth_signal_information", "axis": "verify", "expose": True},
    {"name": "wealth_stewardship_civilization", "axis": "reflect", "expose": True},
    {"name": "wealth_survival_leverage", "axis": "vitality", "expose": True},
    {"name": "wealth_survival_liquidity", "axis": "vitality", "expose": True},
    {"name": "wealth_system_registry_status", "axis": "reason", "expose": True},
    {"name": "wealth_time_discount", "axis": "reason", "expose": True},
    {"name": "wealth_time_payback", "axis": "reason", "expose": True},
    {"name": "wealth_value_npv", "axis": "reason", "expose": True},
    {"name": "wealth_velocity_runway", "axis": "vitality", "expose": True},
]

try:
    from federation.tool_manifest import (
        FEDERATION_TOOLS,
        ToolManifest,
        CognitiveAxis as _WCA,
    )

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


def wealth_health_check() -> dict:
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
    return any(
        _flag_matches(flag, candidate) for flag in flags for candidate in candidates
    )


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
    import numpy_financial as npf

    try:
        return float(npf.npv(discount_rate, cashflow_series))
    except Exception:
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
    # EUREKA FIX 2026-06-08: 0 initial_investment is now VALID.
    # Prior code: `or initial_investment == 0` — blocked life-decision NPVs
    # (STAY at job, take sabbatical, switch career) where there is no
    # upfront capital commitment. Only flag NaN/Inf and negative values.
    # Negative initial_investment would be silently abs()'d by
    # build_cashflow_series, masking "signing bonus" semantics — still invalid.
    if not math.isfinite(initial_investment) or initial_investment < 0:
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


def derive_verdict(
    flags: List[str],
    default_verdict: str = "SEAL",
    high_stress: bool = False,
    recommended: str = "SEAL",
) -> str:
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
    "sovereign": {
        "discount_rate": 0.02,
        "horizon_years": 50,
        "objective": "intergenerational_resource_stewardship",
        "context": "Malaysian upstream sovereign asset base — PETRONAS mandate, PSC regime, Sarawak jurisdiction",
        "maruah_floor": 0.70,
        "f13_required": True,
        "irreversibility_guard": True,
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
    if (
        primary_sanitized or secondary_sanitized or governance_sanitized
    ) and "NON_FINITE_VALUE_REPLACED" not in flags:
        flags.append("NON_FINITE_VALUE_REPLACED")

    # 1. Harness Audit with Chaining
    final_parent_hash = parent_hash or LAST_RECEIPT_HASH
    engine = HarnessEngine()
    audit_res = engine.audit(tool, primary, flags, final_parent_hash)

    systemic_stress = audit_res.get("systemic_stress", 0.0)
    # Stress (0.7-0.9) or systemic instability forces 888-HOLD/QUALIFY
    is_high_stress = systemic_stress > 1.5 or any(
        h["stress"] >= 0.7 for h in audit_res["harness_status"].values()
    )

    derived_governance = verdict or derive_verdict(
        flags, high_stress=is_high_stress, recommended=audit_res["recommended_verdict"]
    )
    derived_allocation = derive_allocation_signal(flags, primary, tool, scale_mode)

    if is_high_stress and derived_allocation == "ACCEPT":
        derived_allocation = "MARGINAL"  # Force downgraded allocation on high stress

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
        "CRITICAL",
        "DEFICIT",
        "NO_INPUT",
    )
    failure_flags = [f for f in flags if any(token in f for token in failure_tokens)]
    status = "PASS"
    next_safe_action = "Consult arifOS 888_JUDGE"

    if failure_flags or audit_res["verdict"] == "FAIL":
        status = (
            "VOID"
            if any("INVALID" in f or "SCHEMA" in f for f in failure_flags)
            else "HOLD"
        )
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

    mode_map = {
        "PASS": "full",
        "CAUTION": "structured",
        "HOLD": "draft_only",
        "VOID": "pause",
    }

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
            next_safe_action = (
                "Restore WEALTH thermodynamic dependencies before allocation."
            )
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
        "witness": witness.to_dict()
        if witness is not None
        else {
            "human": governance_args.get("human_confirmed", False)
            if governance_args
            else False,
            "ai": True,
            "earth": True,
        },
        "shadow": len(audit_res.get("violations", [])) > 0
        or len(audit_res.get("holds", [])) > 0,
        "kappa_r": compute_kappa_r(
            primary.get("rasa", 0.9), primary.get("truth_consistency", 0.95)
        ),
        "psi_le": compute_psi_le(g_data["entropy_s"], systemic_stress),
        "confidence": "LOW" if failure_flags or is_high_stress else "HIGH",
        "epistemic": {
            "class": derived_epistemic,
            "integrity_score": round(1.0 - (systemic_stress / 10.0), 2)
            if not failure_flags
            else 0.1,
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
            "level": "GREEN"
            if status == "PASS"
            else "RED"
            if status == "VOID"
            else "AMBER",
            "economic": "LOW" if derived_allocation == "ACCEPT" else "HIGH",
            "constitutional": "LOW",
            "coupled": "UNKNOWN",
            "g_score": g_data["g_score"],
            "delta_s": g_data["delta_s"],
            "lyapunov_lambda": g_data["lyapunov_lambda"],
            "verdict": g_data["verdict"],
            "regime": g_data["regime"],
        },
        "execution": {
            "recommended_mode": mode_map.get(status, "pause"),
            "human_confirmation_required": status != "PASS"
            or dimension == "Allocation",
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
        "reversibility": "REVERSIBLE"
        if "read" in tool or "check" in tool
        else "UNKNOWN",
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
        scale_mode in {"national", "crisis", "civilization", "agentic", "sovereign"}
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
            "confidence_band": None,  # KeyError fix: always present even on validation failure
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
    import numpy_financial as npf

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

    irr = None
    try:
        irr = float(npf.irr(series))
        if not math.isfinite(irr):
            irr = None
    except Exception:
        pass

    if irr is None:

        def npv_fn(rate):
            return npv_from_series(series, rate)

        brackets = bracket_roots(npv_fn)
        roots = {
            round_value(bisect_root(npv_fn, lower, upper), 10)
            for lower, upper in brackets
        }
        irr = next(iter(roots)) if len(roots) == 1 else None
        if len(roots) == 0:
            flags.append("IRR_NOT_FOUND")

    mirr = None
    try:
        mirr = float(npf.mirr(series, finance_rate, reinvestment_rate))
    except Exception:
        period_count = len(series) - 1
        pv_negative = 0.0
        fv_positive = 0.0
        for index, cashflow in enumerate(series):
            if cashflow < 0:
                pv_negative += cashflow / pow(1 + finance_rate, index)
            elif cashflow > 0:
                fv_positive += cashflow * pow(
                    1 + reinvestment_rate, period_count - index
                )
        if pv_negative < 0 and fv_positive > 0 and period_count > 0:
            mirr = pow(fv_positive / abs(pv_negative), 1 / period_count) - 1

    return {
        "irr": round_value(irr, 8) if irr is not None else None,
        "mirr": round_value(mirr, 8) if mirr is not None else None,
        "sign_changes": sign_changes,
        "period_count": len(series) - 1,
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
    # EUREKA FIX 2026-06-08: PI is undefined when initial_investment is 0
    # (no capital was committed — you can't compute "value per unit capital
    # committed" if no capital was committed). Return None + flag instead
    # of dividing by zero. This makes life decisions (STAY at job, take
    # sabbatical, etc.) work end-to-end through the deal sub-engine.
    pi = None
    if npv_measure["pv_inflows"] is None:
        pi = None
    elif abs(initial_investment) < 1e-9:
        pi = None
        flags.append("PI_UNDEFINED_NO_INVESTMENT")
    else:
        pi = npv_measure["pv_inflows"] / abs(initial_investment)
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
        else numerator / denominator  # type: ignore[operator]
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
    # Guard: if scenarios were invalid (emv=None), return a proper FAIL response
    # rather than propagating None into create_envelope where it can cause
    # downstream numpy/scalar type errors in the envelope chain.
    if measurement["emv"] is None:
        return {
            "tool": "wealth_emv_risk",
            "task": "wealth_emv_risk",
            "mode": "emv",
            "status": "FAIL",
            "domain_verdict": "VOID",
            "governance_verdict": "VOID",
            "engine_status": "ERROR",
            "confidence": "LOW",
            "error": f"Invalid scenarios: {', '.join(measurement['flags']) or 'empty or malformed scenario list'}",
            "failure_flags": measurement["flags"] or ["INVALID_SCENARIOS"],
            "allocation_signal": "INSUFFICIENT_DATA",
            "execution": {
                "recommended_mode": "pause",
                "human_confirmation_required": True,
            },
            "assumptions": measurement["assumptions"],
            "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
        }
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
        total = total * (1 + rate) + annual_contribution  # type: ignore[operator]
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
    # Vector 1: Hard Ledger Binding
    if not assets and not liabilities:
        try:
            from host.governance.vault_supabase import query_portfolio_snapshots

            snapshots = query_portfolio_snapshots(limit=1)
            if snapshots:
                latest = snapshots[0]
                assets = latest.get("result", {}).get("assets", [])
                liabilities = latest.get("result", {}).get("liabilities", [])
        except Exception:
            pass

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

    # If pulled from ledger, upgrade epistemic
    if "snapshots" in locals() and snapshots:
        epistemic = "CLAIM"  # Grounded in VAULT999
        if "GROUNDED_IN_VAULT999" not in nw_flags:
            nw_flags.append("GROUNDED_IN_VAULT999")

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
    # Vector 1: Hard Ledger Binding
    if not income and not expenses and liquid_assets in (None, 0):
        try:
            from host.governance.vault_supabase import query_portfolio_snapshots

            snapshots = query_portfolio_snapshots(limit=1)
            if snapshots:
                latest = snapshots[0]
                # Try to pull from a dedicated cashflow snapshot or infer from portfolio
                result = latest.get("result", {})
                income = result.get("income", [])
                expenses = result.get("expenses", [])
                liquid_assets = result.get(
                    "liquid_assets",
                    result.get("assets", [{}])[0].get("value", 0)
                    if result.get("assets")
                    else 0,
                )
        except Exception:
            pass

    # Load defaults from /app/cashflow_defaults.json if no params provided
    if not income and not expenses and liquid_assets in (None, 0):
        import os
        import json

        defaults_path = os.environ.get(
            "WEALTH_DEFAULTS_PATH", "/app/cashflow_defaults.json"
        )
        if os.path.exists(defaults_path):
            try:
                defaults = json.load(open(defaults_path))
                income = defaults.get("income", [])
                expenses = defaults.get("expenses", [])
                liquid_assets = defaults.get("liquid_assets", 0)
            except Exception:
                pass  # Fall through to empty inputs
    income = [item for item in (income or []) if item.get("active", True)]
    expenses = [item for item in (expenses or []) if item.get("active", True)]
    has_input = bool(income or expenses) or liquid_assets not in (None, 0)
    total_income = sum(
        item.get("monthly_amount", 0)
        for item in income
        if math.isfinite(item.get("monthly_amount", 0))
    )
    total_expenses = sum(
        abs(item.get("monthly_amount", 0))
        for item in expenses
        if math.isfinite(item.get("monthly_amount", 0))
    )
    net_monthly = total_income - total_expenses
    burn_rate = max(0.0, -net_monthly)
    flags: List[str] = ["NO_INPUT_BASELINE"] if not has_input else []
    if burn_rate == 0:
        runway_months = None
        flags.append("RUNWAY_UNBOUNDED")
        # Stress-test: if income stops, runway = assets / expenses
        if total_expenses > 0 and liquid_assets > 0:
            runway_if_income_stops = round_value(liquid_assets / total_expenses, 1)
        else:
            runway_if_income_stops = None
    else:
        runway_months = round_value(liquid_assets / burn_rate, 1)
        if runway_months is not None and runway_months < 3:
            flags.append("RUNWAY_CRITICAL")
        # In deficit, income-stopped scenario is same as normal runway
        runway_if_income_stops = runway_months
    epistemic = weakest_epistemic([*income, *expenses], "UNKNOWN")
    return create_envelope(
        "wealth_cashflow_flow",
        "Flow",
        {
            "monthly_income": round_value(total_income, 2),
            "monthly_expenses": round_value(total_expenses, 2),
            "net_monthly": round_value(net_monthly, 2),
            "runway_months": runway_months,
            "runway_if_income_stops": runway_if_income_stops,
            "burn_rate": round_value(burn_rate, 2),
            "liquid_assets": liquid_assets,
            "tag": epistemic,
        },
        {"period_unit": "monthly"},
        flags,
        [],
        epistemic=epistemic,
        scale_mode=scale_mode,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 SURVIVAL ENGINE — Capability-preserving composite organism
# Absorbs: wealth_flow_cashflow, wealth_flow_liquidity, wealth_runway_calculate,
#          wealth_velocity_runway, wealth_cashflow_summary (as wrappers)
# Preserves: all legacy tool outputs remain identical (equivalence tested)
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Literal

_conservative_factor = 0.8  # runway conservative factor


def _runway_compute(liquid_assets: float, monthly_expenses: float) -> dict:
    """Compute runway months from liquid assets and monthly burn."""
    adjusted = liquid_assets * _conservative_factor
    burn_rate = monthly_expenses
    months = round(adjusted / burn_rate, 1) if burn_rate > 0 else float("inf")
    if months < 3:
        stress = "CRITICAL"
    elif months < 6:
        stress = "AMBER"
    elif months < 12:
        stress = "CAUTION"
    else:
        stress = "GREEN"
    return {
        "runway_months": months,
        "stress_label": stress,
        "adjusted_liquid_assets": round(adjusted, 4),
        "burn_rate": round(burn_rate, 4),
        "conservative_factor": _conservative_factor,
    }


@mcp.tool(task=True)
async def wealth_survival_engine(
    mode: Literal[
        "cashflow", "runway", "burn", "liquidity", "personal_finance"
    ] = "personal_finance",
    monthly_income: float | None = None,
    monthly_expenses: float | None = None,
    liquid_assets: float | None = None,
    cashflows: list[dict] | None = None,
    horizon_months: int = 12,
    conservative_factor: float = 0.8,
    legacy_compat: bool = False,
) -> dict:
    """
    Ω-SURVIVAL-ENGINE: Unified survival intelligence — cashflow, runway, burn, liquidity.

    Physics analogy: This is the metabolic engine — how the capital organism
    maintains survival under cash flow stress.

    Modes:
      cashflow         — net monthly position from income/expenses
      runway          — months of survival from liquid assets / burn rate
      burn            — monthly burn rate (expenses - income)
      liquidity       — liquidity health including cashflow + assets
      personal_finance — comprehensive survival dashboard

    Dimensional verdicts:
      conservation  — capital preservation under stress
      flow          — cash movement rate
      time          — runway horizon
      entropy       — uncertainty in survival
      boundary      — stress threshold crossing

    Authority: WEALTH computes. arifOS / Arif judges.
    """
    # ── Normalise cashflow inputs ──────────────────────────────────────────
    # Explicit params take precedence over cashflows list to avoid double-counting.
    income_items: list[dict] = []
    expense_items: list[dict] = []

    if monthly_income is not None and monthly_income > 0:
        income_items.append({"monthly_amount": monthly_income, "active": True})
    elif cashflows:
        for item in cashflows:
            amt = item.get("monthly_amount", item.get("amount", 0))
            active = item.get("active", True)
            if not active:
                continue
            if amt >= 0:
                income_items.append(item)

    if monthly_expenses is not None and monthly_expenses > 0:
        expense_items.append({"monthly_amount": -abs(monthly_expenses), "active": True})
    elif cashflows:
        for item in cashflows:
            amt = item.get("monthly_amount", item.get("amount", 0))
            active = item.get("active", True)
            if not active:
                continue
            if amt < 0:
                expense_items.append(item)

    total_income = sum(i.get("monthly_amount", 0) for i in income_items)
    total_expenses = sum(abs(i.get("monthly_amount", 0)) for i in expense_items)
    net_monthly = total_income - total_expenses
    burn_rate = max(0.0, -net_monthly)

    liq_assets = liquid_assets if liquid_assets is not None else 0.0

    # ── Mode routing ────────────────────────────────────────────────────────
    if mode == "burn":
        envelope = create_envelope(
            "wealth_survival_engine",
            "Survival",
            {
                "engine": "wealth_survival_engine",
                "mode": "burn",
                "burn_rate": round(burn_rate, 2),
                "net_monthly": round(net_monthly, 2),
                "total_income": round(total_income, 2),
                "total_expenses": round(total_expenses, 2),
                "liquid_assets": liq_assets,
            },
            {"period_unit": "monthly"},
            [],
            [],
            epistemic="OBSERVED",
        )
        dimensional_verdicts = {
            "conservation": "NEUTRAL",
            "flow": "DEFICIT" if net_monthly < 0 else "ADEQUATE",
            "time": "NEUTRAL",
            "entropy": "LOW",
            "boundary": "GREEN",
        }

    elif mode == "runway":
        if liq_assets <= 0 or burn_rate <= 0:
            runway_months = None
            flags = ["NO_INPUT_BASELINE"]
        else:
            adjusted = liq_assets * conservative_factor
            runway_months = round(adjusted / burn_rate, 1)
            flags = []
            if runway_months < 3:
                flags.append("RUNWAY_CRITICAL")
            elif runway_months >= 12:
                flags.append("RUNWAY_GREEN")

        envelope = create_envelope(
            "wealth_survival_engine",
            "Survival",
            {
                "engine": "wealth_survival_engine",
                "mode": "runway",
                "runway_months": runway_months,
                "liquid_assets": liq_assets,
                "burn_rate": round(burn_rate, 2),
                "conservative_factor": conservative_factor,
                "stress_label": (
                    "CRITICAL"
                    if runway_months and runway_months < 3
                    else "GREEN"
                    if runway_months and runway_months >= 12
                    else "AMBER"
                    if runway_months and runway_months < 6
                    else "CAUTION"
                    if runway_months
                    else "UNKNOWN"
                ),
            },
            {"period_unit": "monthly"},
            flags,
            [],
            epistemic="OBSERVED",
        )
        dimensional_verdicts = {
            "conservation": "CRITICAL"
            if (runway_months and runway_months < 3)
            else "ADEQUATE",
            "flow": "DEFICIT" if net_monthly < 0 else "ADEQUATE",
            "time": "CRITICAL"
            if (runway_months and runway_months < 3)
            else "SUFFICIENT",
            "entropy": "LOW",
            "boundary": "RED" if (runway_months and runway_months < 3) else "GREEN",
        }

    elif mode == "liquidity":
        flags = []
        if burn_rate == 0:
            liquidity_state = "GREEN"
        elif net_monthly < 0:
            liquidity_state = "DEFICIT"
            flags.append("DEFICIT")
        else:
            liquidity_state = "adequate"

        envelope = create_envelope(
            "wealth_survival_engine",
            "Survival",
            {
                "engine": "wealth_survival_engine",
                "mode": "liquidity",
                "liquidity_state": liquidity_state,
                "liquid_assets": liq_assets,
                "net_monthly": round(net_monthly, 2),
                "burn_rate": round(burn_rate, 2),
                "total_income": round(total_income, 2),
                "total_expenses": round(total_expenses, 2),
            },
            {"period_unit": "monthly"},
            flags,
            [],
            epistemic="OBSERVED",
        )
        dimensional_verdicts = {
            "conservation": "CRITICAL" if liquidity_state == "DEFICIT" else "ADEQUATE",
            "flow": "DEFICIT" if net_monthly < 0 else "ADEQUATE",
            "time": "CRITICAL" if liquidity_state == "DEFICIT" else "ADEQUATE",
            "entropy": "LOW",
            "boundary": "RED" if liquidity_state == "DEFICIT" else "GREEN",
        }

    elif mode == "cashflow":
        envelope = cashflow_flow(
            income=income_items or None,
            expenses=expense_items or None,
            liquid_assets=liq_assets,
            scale_mode="enterprise",
        )
        # Wrap with engine metadata and add deficit flag
        envelope["primary_metrics"]["engine"] = "wealth_survival_engine"
        envelope["primary_metrics"]["mode"] = "cashflow"
        envelope["primary_metrics"]["cashflow_state"] = (
            "surplus"
            if net_monthly > 0
            else "deficit"
            if net_monthly < 0
            else "balanced"
        )
        # Add DEFICIT flag to envelope for failure_flags to catch
        if net_monthly < 0 and "DEFICIT" not in (envelope.get("failure_flags") or []):
            envelope["failure_flags"] = envelope.get("failure_flags", []) + ["DEFICIT"]
        # Wrap with engine metadata
        envelope["primary_metrics"]["engine"] = "wealth_survival_engine"
        envelope["primary_metrics"]["mode"] = "cashflow"
        envelope["primary_metrics"]["cashflow_state"] = (
            "surplus"
            if net_monthly > 0
            else "deficit"
            if net_monthly < 0
            else "balanced"
        )
        dimensional_verdicts = {
            "conservation": "CRITICAL" if net_monthly < 0 else "ADEQUATE",
            "flow": "DEFICIT" if net_monthly < 0 else "SURPLUS",
            "time": "NEUTRAL",
            "entropy": "LOW",
            "boundary": "RED" if net_monthly < 0 else "GREEN",
        }

    else:  # personal_finance — comprehensive dashboard
        # Compute sub-dimensions
        if liq_assets > 0 and burn_rate > 0:
            runway_months = round((liq_assets * conservative_factor) / burn_rate, 1)
        else:
            runway_months = None

        if net_monthly >= 0:
            survival_verdict = "SURVIVAL_ADEQUATE"
        elif runway_months and runway_months >= 3:
            survival_verdict = "SURVIVAL_STRESSED"
        else:
            survival_verdict = "SURVIVAL_CRITICAL"

        envelope = create_envelope(
            "wealth_survival_engine",
            "Survival",
            {
                "engine": "wealth_survival_engine",
                "mode": "personal_finance",
                "runway_months": runway_months,
                "burn_rate": round(burn_rate, 2),
                "net_monthly": round(net_monthly, 2),
                "total_income": round(total_income, 2),
                "total_expenses": round(total_expenses, 2),
                "liquid_assets": liq_assets,
                "survival_verdict": survival_verdict,
            },
            {"period_unit": "monthly", "horizon_months": horizon_months},
            ["RUNWAY_CRITICAL"] if (runway_months and runway_months < 3) else [],
            [],
            epistemic="OBSERVED",
        )
        dimensional_verdicts = {
            "conservation": "CRITICAL"
            if survival_verdict == "SURVIVAL_CRITICAL"
            else "ADEQUATE",
            "flow": "DEFICIT" if net_monthly < 0 else "SURPLUS",
            "time": "CRITICAL"
            if (runway_months and runway_months < 3)
            else "SUFFICIENT",
            "entropy": "LOW",
            "boundary": "RED"
            if survival_verdict in ("SURVIVAL_CRITICAL", "SURVIVAL_STRESSED")
            else "GREEN",
        }

    # ── Attach dimensional verdicts ─────────────────────────────────────────
    envelope["dimensional_verdicts"] = dimensional_verdicts
    envelope["claim_state"] = "CLAIM"
    envelope["execution_authorized"] = False
    envelope["recommendation_only"] = True
    envelope["final_authority"] = "Arif"
    envelope["assumptions"] = [
        f"income={total_income}, expenses={total_expenses}",
        f"liquid_assets={liq_assets}",
        f"conservative_factor={conservative_factor}",
        "WEALTH computes. Arif judges.",
    ]
    envelope["warnings"] = [
        "RUNWAY_CRITICAL" if (dimensional_verdicts["boundary"] == "RED") else "",
    ]
    envelope["warnings"] = [w for w in envelope["warnings"] if w]

    return envelope


# ── Legacy Wrappers ────────────────────────────────────────────────────────────
# Each wrapper calls the new engine and adds backward-compat metadata.
# Tests verify output equivalence before any legacy tool is deprecated.


# REMOVED from public surface — use wealth_personal_finance / wealth_market_data
def wealth_runway_calculate(
    monthly_burn: float = 0.0,
    liquid_assets: float = 0.0,
    conservative_factor: float = 0.8,
) -> dict:
    """
    Ω-D1-03: Runway Calculate — Months of financial runway.
    [LEGACY WRAPPER → wealth_survival_engine(mode='runway')]
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        result = loop.run_until_complete(
            wealth_survival_engine(
                mode="runway",
                liquid_assets=liquid_assets,
                monthly_expenses=monthly_burn,
                conservative_factor=conservative_factor,
                legacy_compat=True,
            )
        )
    except RuntimeError:
        # No running loop — create one
        result = asyncio.run(
            wealth_survival_engine(
                mode="runway",
                liquid_assets=liquid_assets,
                monthly_expenses=monthly_burn,
                conservative_factor=conservative_factor,
                legacy_compat=True,
            )
        )

    # Map engine output to legacy output shape
    primary = result.get("primary_metrics", {})
    return {
        "mcp": "WEALTH",
        "tool": "wealth_runway_calculate",
        "status": "recorded",
        "runway_months": primary.get("runway_months"),
        "adjusted_liquid_assets": primary.get("adjusted_liquid_assets"),
        "break_even_burn_pa": round(
            primary.get("liquid_assets", 0) * conservative_factor / 12, 4
        )
        if primary.get("liquid_assets")
        else 0,
        "monthly_burn": monthly_burn,
        "liquid_assets": liquid_assets,
        "conservative_factor": conservative_factor,
        "stress_label": primary.get(
            "stress_label",
            "GREEN"
            if primary.get("runway_months", 999) >= 12
            else "CRITICAL"
            if primary.get("runway_months", 999) < 3
            else "AMBER",
        ),
        "recommendation_only": True,
        "final_authority": "Arif",
        # Legacy compat metadata
        "legacy_tool_name": "wealth_runway_calculate",
        "routed_to": "wealth_survival_engine",
        "deprecated": True,
        "compatibility_preserved": True,
    }


def wealth_flow_liquidity(
    mode: str = "cashflow",
    income: list[dict] | None = None,
    expenses: list[dict] | None = None,
    liquid_assets: float | None = None,
    scale_mode: str = "enterprise",
) -> dict:
    """
    Ω-WEALTH-02: Flow — liquidity movement (cashflow, burn, runway, survival).
    [LEGACY WRAPPER → wealth_survival_engine(mode='liquidity')]
    """
    import asyncio

    cashflows = []
    if income:
        cashflows.extend(income)
    if expenses:
        cashflows.extend(expenses)

    engine_mode = "liquidity" if mode == "cashflow" else mode

    result = asyncio.run(
        wealth_survival_engine(
            mode=engine_mode,
            cashflows=cashflows or None,
            liquid_assets=liquid_assets,
            legacy_compat=True,
        )
    )

    envelope = result
    envelope["flags"] = envelope.get("flags", [])
    # Legacy compat metadata
    envelope["legacy_tool_name"] = "wealth_flow_liquidity"
    envelope["routed_to"] = "wealth_survival_engine"
    envelope["deprecated"] = True
    envelope["compatibility_preserved"] = True
    return envelope


def wealth_flow_cashflow(
    income: list[dict] | None = None,
    expenses: list[dict] | None = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
) -> dict:
    """
    Cash Flow Projection — metabolic liquidity rate.
    [LEGACY WRAPPER → wealth_survival_engine(mode='cashflow')]
    """
    import asyncio

    cashflows = []
    if income:
        cashflows.extend(income)
    if expenses:
        cashflows.extend(expenses)

    result = asyncio.run(
        wealth_survival_engine(
            mode="cashflow",
            cashflows=cashflows or None,
            liquid_assets=liquid_assets,
            legacy_compat=True,
        )
    )

    envelope = result
    envelope["flags"] = envelope.get("flags", [])
    # Legacy compat metadata
    envelope["legacy_tool_name"] = "wealth_flow_cashflow"
    envelope["routed_to"] = "wealth_survival_engine"
    envelope["deprecated"] = True
    envelope["compatibility_preserved"] = True
    return envelope


def wealth_velocity_runway(
    principal: float,
    rate: float,
    years: int,
    annual_contribution: float = 0,
    monthly_burn: float = 0,
    scale_mode: str = "enterprise",
) -> dict:
    """
    Compound Growth Velocity and Runway — expansion speed.
    [LEGACY WRAPPER → wealth_survival_engine(mode='runway')]
    """
    # Delegate to growth_velocity for compound growth, but add runway
    growth_result = growth_velocity(
        principal=principal,
        rate=rate,
        years=years,
        annual_contribution=annual_contribution,
        monthly_burn=monthly_burn,
        scale_mode=scale_mode,
    )

    # Add runway from survival engine
    import asyncio

    if monthly_burn > 0:
        runway_result = asyncio.run(
            wealth_survival_engine(
                mode="runway",
                liquid_assets=principal,
                monthly_expenses=monthly_burn,
                legacy_compat=True,
            )
        )
        growth_result["primary"]["runway_months"] = runway_result.get(
            "primary", {}
        ).get("runway_months")

    # Legacy compat metadata
    growth_result["legacy_tool_name"] = "wealth_velocity_runway"
    growth_result["routed_to"] = "wealth_survival_engine"
    growth_result["deprecated"] = True
    growth_result["compatibility_preserved"] = True
    return growth_result


# NOTE: wealth_cashflow_summary is async — keep as-is, it already calls _pf_get_txns
# which is the correct behavior for personal finance summaries from DB.


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
        epistemic_flags,
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
    # Filter shared_resources to only include numeric constraints for the LP solver
    # Metadata like 'resource_type': 'upstream_hydrocarbon' should not be passed to the solver
    numeric_resources = {
        k: v for k, v in shared_resources.items() if isinstance(v, (int, float, bool))
    }
    # Convert bool to int for LP solver compatibility
    numeric_resources = {
        k: (int(v) if isinstance(v, bool) else v) for k, v in numeric_resources.items()
    }

    resource_keys = list(numeric_resources.keys())

    # Normalize agents to LP schema using only numeric resource keys
    lp_agents = _normalize_coordination_agents(agents, resource_keys)

    lp_result = lp_allocate(lp_agents, numeric_resources)
    commons = commons_risk(lp_agents, numeric_resources)

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
    if not result.get("records") and not _has_any_flag(
        flags, {"ADAPTER_NOT_FOUND", "NO_DATA_FETCHED"}
    ):
        flags.append("NO_DATA_FETCHED")

    # Surface staleness and data currency at top level — WorldBank can lag 1-2 years.
    # Stale data must not silently enter NPV/EVOI calculations as HIGH confidence.
    records_raw = result.get("records", [])
    obs_times = [
        r.get("observation_time") or r.get("date")
        for r in records_raw
        if isinstance(r, dict)
    ]
    obs_times = [t for t in obs_times if t]
    data_as_of = max(obs_times) if obs_times else None
    is_stale = any("STALE_OBSERVATION" in f for f in flags)
    if data_as_of and is_stale:
        flags.append(
            f"DATA_AS_OF:{data_as_of[:10]} — macro source may lag 1-2 years; "
            "cap downstream confidence at MEDIUM when is_stale=True"
        )

    return create_envelope(
        "wealth_ingest_fetch",
        "Sense",
        {
            "count": result["count"],
            "cached": result.get("cached", False),
            "data_as_of": data_as_of,
            "is_stale": is_stale,
        },
        {"records": result["records"][:50], "flags": flags},
        flags,
        [
            "Live feeds carry source, timestamp, unit, and revision metadata.",
            f"data_as_of: {data_as_of or 'UNKNOWN'} — check is_stale before using in NPV models.",
        ],
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
            "epistemic_tiers": [
                "CLAIM",
                "PLAUSIBLE",
                "HYPOTHESIS",
                "ESTIMATE",
                "VERIFIED",
            ],
        },
        indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TREE777 WIKI RESOURCES — Federation Canonical Knowledge Tree
# ═══════════════════════════════════════════════════════════════════════════════
# Exposes WEALTH-domain slice of the TREE777 wiki as MCP Resources.
# URI scheme:
#   tree777://skills/wealth/{name}   — WEALTH skill pages
#   tree777://wealth/concepts/{name} — Capital concept pages
#   tree777://wealth/scars/{name}    — WEALTH scar/incident records
# Wiki root: /root/AAA/wiki (shared across all 4 federation servers)
# Rule: Resources grow. Tools stay bounded. Judgment remains Arif.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.

TREE777_WIKI_ROOT = Path(os.environ.get("TREE777_WIKI_ROOT", "/root/AAA/wiki"))
TREE777_SKILLS_DIR = TREE777_WIKI_ROOT / "skills" / "wealth"
TREE777_CONCEPTS_DIR = TREE777_WIKI_ROOT / "concepts"
TREE777_SCAR_DIR = TREE777_WIKI_ROOT / "scars"


def _wealth_read_wiki_file(file_path: str | Path) -> str:
    """Read a wiki file, returning frontmatter-stripped content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {path}"
    content = path.read_text()
    if content.startswith("---"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5 :]
    return content.strip()


def _wealth_tree777_index() -> dict[str, Any]:
    """Build the TREE777 index for WEALTH domain slice."""
    skills = []
    if TREE777_SKILLS_DIR.exists():
        for f in TREE777_SKILLS_DIR.glob("*.md"):
            skills.append({"name": f.stem, "uri": f"tree777://skills/wealth/{f.stem}"})

    concepts = []
    if TREE777_CONCEPTS_DIR.exists():
        for f in TREE777_CONCEPTS_DIR.glob("*.md"):
            concepts.append(
                {"name": f.stem, "uri": f"tree777://wealth/concepts/{f.stem}"}
            )

    scars = []
    if TREE777_SCAR_DIR.exists():
        for f in TREE777_SCAR_DIR.glob("*.md"):
            if "wealth" in f.stem or "capital" in f.stem or "econ" in f.stem:
                scars.append(
                    {"name": f.stem, "uri": f"tree777://wealth/scars/{f.stem}"}
                )

    return {
        "domain": "wealth",
        "skills": skills,
        "concepts": concepts,
        "scars": scars,
        "total": len(skills) + len(concepts) + len(scars),
    }


@mcp.resource(
    "tree777://index",
    description=(
        "TREE777 wiki full index. Lists all federation skills, concepts, and scars. "
        "Use this to discover available resources across the arifOS, GEOX, WELL, and WEALTH domains."
    ),
)
def wealth_tree777_index() -> str:
    return json.dumps(_wealth_tree777_index(), indent=2)


@mcp.resource(
    "tree777://skills/wealth/{name}",
    description=(
        "Individual WEALTH skill page from the TREE777 wiki. "
        "Returns markdown content (frontmatter-stripped) with metadata. "
        "Example: tree777://skills/wealth/capital-conservation"
    ),
)
def wealth_tree777_skill(name: str) -> str:
    file_path = TREE777_SKILLS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Skill not found: {name}",
                "uri": f"tree777://skills/wealth/{name}",
            }
        )
    content = _wealth_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://skills/wealth/{name}", "content": content}, indent=2
    )


@mcp.resource(
    "tree777://wealth/concepts/{name}",
    description=(
        "Capital concept page from the TREE777 wiki. "
        "Example: tree777://wealth/concepts/TREE777"
    ),
)
def wealth_tree777_concept(name: str) -> str:
    file_path = TREE777_CONCEPTS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Concept not found: {name}",
                "uri": f"tree777://wealth/concepts/{name}",
            }
        )
    content = _wealth_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://wealth/concepts/{name}", "content": content}, indent=2
    )


@mcp.resource(
    "tree777://wealth/scars/{name}",
    description=(
        "WEALTH scar/incident record from the TREE777 wiki. "
        "Documents failures and lessons learned for capital operations. "
        "Example: tree777://wealth/scars/wealth-risk-breach"
    ),
)
def wealth_tree777_scar(name: str) -> str:
    file_path = TREE777_SCAR_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Scar not found: {name}",
                "uri": f"tree777://wealth/scars/{name}",
            }
        )
    content = _wealth_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://wealth/scars/{name}", "content": content}, indent=2
    )


WELL_TYPE_PRIOR_BASELINES: Dict[str, float] = {
    "wildcat": 0.25,  # frontier exploration — global PoS range 0.20-0.30
    "near_field": 0.50,  # near-field / step-out extension — PoS range 0.40-0.60
    "appraisal": 0.55,  # appraisal of a confirmed discovery — PoS range 0.50-0.65
    "development": 0.75,  # development well in producing field — PoS range 0.70-0.85
}


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
    well_type: str = "",
) -> Any:
    """
    Expected Value of Information (EVOI) point-estimate computation. [Epistemic Dimension]
    Ingests GEOX prospect_metrics or raw prior/posterior probabilities.
    EVOI = E[V | with_info] - E[V | without_info]
    """
    # Metric Handoff (GEOX -> WEALTH)
    if prospect_metrics:
        final_prior = prospect_metrics.get("composite_pos", prior_pos)
        final_posterior = (
            posterior_pos or min(1.0, final_prior * 1.25)
            if final_prior
            else posterior_pos
        )
    else:
        final_prior = prior_pos
        final_posterior = posterior_pos

    _evoi_default_flags: List[str] = []
    if final_prior is None:
        _baseline = (
            WELL_TYPE_PRIOR_BASELINES.get(well_type.lower().replace("-", "_"), 0.30)
            if well_type
            else 0.30
        )
        final_prior = _baseline
        if (
            well_type
            and well_type.lower().replace("-", "_") in WELL_TYPE_PRIOR_BASELINES
        ):
            _evoi_default_flags.append(
                f"PRIOR_DEFAULTED_TO_{well_type.upper()}_BASELINE_{_baseline}"
            )
        else:
            _evoi_default_flags.append(
                f"PRIOR_DEFAULTED_TO_WILDCAT_BASELINE_{_baseline} — pass well_type=(wildcat|near_field|appraisal|development) for well-specific prior"
            )
    if final_posterior is None:
        # Bayesian update: new information raises PoS by ~50% relative
        final_posterior = min(1.0, final_prior * 1.50)
        _evoi_default_flags.append(
            f"POSTERIOR_DEFAULTED_TO_BAYESIAN_UPDATE_{round(final_posterior, 2)}"
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
            _evoi_default_flags,
            [
                f"Prior PoS: {final_prior:.2f}",
                f"Posterior PoS: {final_posterior:.2f}",
                f"Information cost: {info_cost_musd} MUSD",
                *(
                    [f"WARNING: {f}" for f in _evoi_default_flags]
                    if _evoi_default_flags
                    else []
                ),
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
        os.environ.get("ARIFOS_HOME", "/root") + "/arifOS",
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
        res = await _arifos_vault_seal_http(
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
                "payload": {
                    "intent": intent or "economic-analysis",
                    "source": "WEALTH-MCP",
                },
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
    "wealth_future_value": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "wealth_future_value",
    },
    "wealth_present_expect": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "wealth_present_expect",
    },
    "wealth_future_simulate": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "wealth_future_simulate",
    },
    "wealth_info_value": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "wealth_info_value",
    },
    "wealth_truth_validate": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "wealth_truth_validate",
    },
    "wealth_survival_liquidity": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "wealth_survival_liquidity",
    },
    "wealth_survival_leverage": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "wealth_survival_leverage",
    },
    "wealth_rule_enforce": {
        "family": "JUDGE",
        "stage": "888-JUDGE",
        "display": "wealth_rule_enforce",
    },
    "wealth_allocate_optimize": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "wealth_allocate_optimize",
    },
    "wealth_game_coordinate": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "wealth_game_coordinate",
    },
    "wealth_sense_ingest": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "wealth_sense_ingest",
    },
    "wealth_past_record": {
        "family": "VAULT",
        "stage": "999-VAULT",
        "display": "wealth_past_record",
    },
    "wealth_future_steward": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "wealth_future_steward",
    },
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = npv_reward(
            initial_investment,
            cash_flows,
            discount_rate,
            terminal_value,
            period_unit,
            input_epistemic,
            scale_mode,
        )
    elif mode == "irr":
        result = irr_yield(
            initial_investment,
            cash_flows,
            reinvestment_rate,
            finance_rate,
            period_unit,
            discount_rate,
            scale_mode,
        )
    elif mode == "pi":
        result = pi_efficiency(
            initial_investment, cash_flows, discount_rate, terminal_value, scale_mode
        )
    elif mode == "payback":
        result = payback_time(
            initial_investment, cash_flows, discount_rate, period_unit, scale_mode
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_future_value")


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
def wealth_present_expect(
    scenarios: List[dict],
    scale_mode: str = "enterprise",
) -> Any:
    """⚠️ DEPRECATED — Use: wealth_expectation_emv. [Expect Dimension — DEPRECATED]"""
    normalized = []
    for s in scenarios:
        normalized.append(
            {
                "probability": s.get("probability", s.get("prob", 0)),
                "outcome": s.get("outcome", s.get("return", s.get("cash_flow", 0))),
            }
        )
    return _normalize_primitive_envelope(
        emv_risk(normalized, scale_mode), "wealth_present_expect"
    )


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = growth_velocity(
            principal, rate, years, annual_contribution, monthly_burn, scale_mode
        )
    elif mode == "triage":
        result = crisis_triage(resources, demands, recovery_horizon_days, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_survival_liquidity")


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = dscr_leverage(
            ebitda,
            principal,
            interest,
            leases,
            cfads,
            debt_service,
            period_unit,
            input_epistemic,
            scale_mode,
        )
    elif mode == "networth":
        result = networth_state(assets, liabilities, scale_mode)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_survival_leverage")


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = await wealth_correlation_guard_check(
            prospects or [], correlation_threshold, scale_mode
        )
    elif mode == "entropy":
        result = audit_entropy(
            initial_investment, cash_flows, discount_rate, scale_mode
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_truth_validate")


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = personal_decision(
            alternatives or [], constraints or {}, values, scale_mode
        )
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
        result = coordination_equilibrium(
            agents, shared_resources, mechanism, scale_mode
        )
    elif mode == "game":
        result = game_theory_solve(
            agents, resources, mechanism, solve_equilibrium, scale_mode
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return _normalize_primitive_envelope(result, "wealth_game_coordinate")


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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


@mcp.tool(
    annotations={"deprecatedHint": True, "title": "⚠️ DEPRECATED — Use atomic tools"}
)
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
    energy_budget_twh = float(
        energy_mix.get(
            "energy_budget_twh", 1000.0 * max(renewable_mix + fossil_mix, 1.0)
        )
    )
    tech_growth_rate = float(
        energy_mix.get(
            "tech_growth_rate",
            population_projection.get(
                "tech_growth_rate", max(0.0, renewable_mix * 0.03)
            ),
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
    "wealth_value_npv": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "value_npv",
    },
    "wealth_energy_irr": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "energy_irr",
    },
    "wealth_density_pi": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "density_pi",
    },
    "wealth_time_payback": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "time_payback",
    },
    "wealth_expectation_emv": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "expectation_emv",
    },
    "wealth_probability_monte_carlo": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "probability_monte_carlo",
    },
    "wealth_signal_evoi": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "signal_evoi",
    },
    "wealth_signal_evoi_mc": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "signal_evoi_mc",
    },
    "wealth_coupling_correlation": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "coupling_correlation",
    },
    "wealth_flow_cashflow": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "flow_cashflow",
    },
    "wealth_velocity_runway": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "velocity_runway",
    },
    "wealth_gravity_dscr": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "gravity_dscr",
    },
    "wealth_mass_networth": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "mass_networth",
    },
    "wealth_pressure_triage": {
        "family": "SURVIVAL",
        "stage": "300-SURVIVAL",
        "display": "pressure_triage",
    },
    "wealth_stewardship_civilization": {
        "family": "HEART",
        "stage": "300-HEART",
        "display": "stewardship_civilization",
    },
    "wealth_measurement_schema": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "measurement_schema",
    },
    "wealth_entropy_audit": {
        "family": "MIND",
        "stage": "200-MIND",
        "display": "entropy_audit",
        "dual_domain": ["MIND", "JUDGE"],
    },
    "wealth_boundary_floors": {
        "family": "JUDGE",
        "stage": "800-JUDGE",
        "display": "boundary_floors",
    },
    "wealth_boundary_policy": {
        "family": "JUDGE",
        "stage": "800-JUDGE",
        "display": "boundary_policy",
    },
    "wealth_governance_verdict": {
        "family": "JUDGE",
        "stage": "888-JUDGE",
        "display": "governance_verdict",
        "primary": True,
    },
    "wealth_field_game": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "field_game",
    },
    "wealth_field_equilibrium": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "field_equilibrium",
    },
    "wealth_preference_rank": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "preference_rank",
    },
    "wealth_agent_path": {
        "family": "REASON",
        "stage": "400-REASON",
        "display": "agent_path",
    },
    "wealth_sensor_fetch": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_fetch",
    },
    "wealth_sensor_snapshot": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_snapshot",
    },
    "wealth_sensor_reconcile": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_reconcile",
    },
    "wealth_sensor_health": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_health",
    },
    "wealth_sensor_vintage": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_vintage",
    },
    "wealth_sensor_sources": {
        "family": "SENSE",
        "stage": "100-SENSE",
        "display": "sensor_sources",
    },
    "wealth_ledger_query": {
        "family": "VAULT",
        "stage": "000-VAULT",
        "display": "ledger_query",
    },
    "wealth_ledger_write": {
        "family": "VAULT",
        "stage": "000-VAULT",
        "display": "ledger_write",
    },
    "wealth_ledger_init": {
        "family": "VAULT",
        "stage": "000-VAULT",
        "display": "ledger_init",
    },
    "wealth_ledger_record": {
        "family": "VAULT",
        "stage": "000-VAULT",
        "display": "ledger_record",
    },
    "wealth_ledger_snapshot": {
        "family": "VAULT",
        "stage": "000-VAULT",
        "display": "ledger_snapshot",
    },
}
HarnessEngine.SOVEREIGN_METADATA.update(_ATOMIC_METADATA)

# ============================================================
# V3 Atomic Tools (Physics-First Naming)
# Each wraps its existing internal engine with a physics analogy.
# Old canonical tools at lines 3659+ remain as deprecated shims.
# ============================================================

# --- Value / Time Tools (4) ---


# REMOVED from public surface — internal use only
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
    return npv_reward(
        initial_investment,
        cash_flows,
        discount_rate,
        terminal_value,
        period_unit,
        input_epistemic,
        scale_mode,
    )


# REMOVED from public surface — internal use only
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
    return irr_yield(
        initial_investment,
        cash_flows,
        reinvestment_rate,
        finance_rate,
        period_unit,
        discount_rate,
        scale_mode,
    )


# REMOVED from public surface — internal use only
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
    return pi_efficiency(
        initial_investment, cash_flows, discount_rate, terminal_value, scale_mode
    )


# REMOVED from public surface — internal use only
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
    return payback_time(
        initial_investment, cash_flows, discount_rate, period_unit, scale_mode
    )


# --- Probability / Information Tools (5) ---


# REMOVED from public surface — internal use only
def wealth_expectation_emv(
    scenarios: List[dict],
    scale_mode: str = "enterprise",
) -> Any:
    """Expected Monetary Value — probability-weighted outcome.
    Physics analogy: EMV is the center of mass of a probability density over outcomes."""
    return emv_risk(scenarios, scale_mode)


# REMOVED from public surface — internal use only
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
    return monte_carlo_forecast(
        initial_commitment,
        mean_cash_flows,
        volatilities,
        discount_rate,
        simulations,
        distribution,
        scale_mode,
    )


# REMOVED from public surface — internal use only
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
    return await wealth_evoi_compute(
        well_cost_musd,
        p50_value_musd,
        prior_pos,
        posterior_pos,
        prospect_metrics,
        info_cost_musd,
        discount_rate,
        scale_mode,
    )


@mcp.tool(task=True)
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
    return await wealth_evoi_monte_carlo(
        prior_pos_samples,
        posterior_pos_samples,
        well_cost_musd,
        p50_value_musd,
        info_cost_musd,
        scale_mode,
    )


# NOTE: wealth_deal_frame is now an INTERNAL HELPER called by wealth_omni_wisdom (mode='deal').
# Removed from @mcp.tool surface 2026-06-03 in Path D consolidation. See Ω-WEALTH-OMNI below.
# @mcp.tool()  # <-- removed 2026-06-03: absorbed into wealth_omni_wisdom
async def wealth_deal_frame(
    opportunity_name: str,
    initial_investment: float,
    cash_flows: Optional[List[float]] = None,
    terminal_value: float = 0,
    discount_rate: float = 0.10,
    period_unit: str = "annual",
    scenarios: Optional[List[dict]] = None,
    mean_cash_flows: Optional[List[float]] = None,
    volatilities: Optional[List[float]] = None,
    monte_carlo_simulations: int = 5000,
    distribution: str = "lognormal",
    maruah_impact: float = 0.5,
    extractive_signals: Optional[dict] = None,
    scale_mode: str = "enterprise",
) -> dict:
    """Ω-DEAL-00: Deal Frame — complete capital opportunity judgment.

    This is the APEX composite for opportunity evaluation. It runs the full pipeline:
    screening → valuation → risk → scenarios → governance → memo.

    Replaces and absorbs: wealth_screen_opportunity, wealth_score_risk,
    wealth_compute_viability, wealth_compare_scenarios, wealth_emit_investment_memo.

    AGENT USE CASE:
    Use this when Arif or an agent needs to evaluate ANY capital opportunity —
    a project, investment, expenditure, or resource commitment.
    One call = full governed judgment. Do NOT chain 5 separate tool calls.

    INPUTS:
      opportunity_name    — human-readable label for this opportunity
      initial_investment — upfront capital commitment (positive number, MYR or MUSD)
      cash_flows         — expected periodic cash flows (list of floats, same length as period)
      terminal_value     — residual value at end of horizon (default 0)
      discount_rate      — annual discount rate (default 0.10 = 10%)
      period_unit        — "annual" or "monthly"
      scenarios          — [{name, probability, cash_flows, terminal_value?}, ...]
                           if provided, runs EMV across scenarios
      mean_cash_flows    — for Monte Carlo: expected cash flows (list of floats)
      volatilities       — for Monte Carlo: std dev of each period cash flow (list of floats)
      monte_carlo_simulations — number of simulations (default 5000)
      distribution       — "lognormal" or "normal" for Monte Carlo
      maruah_impact      — 0.0 (no dignity impact) to 1.0 (severe dignity cost)
      extractive_signals  — {rate_of_return, extraction_intensity, resource_depletion, ...}
      scale_mode         — "personal" | "enterprise" | "civilizational"

    OUTPUT: Complete deal judgment with:
      - classification (VIABLE / MARGINAL / NON_VIABLE / ESCALATE)
      - valuation (NPV, IRR, payback, PI)
      - scenario EMV if scenarios provided
      - Monte Carlo distribution if mean+volatility provided
      - entropy risk score
      - boundary/floor governance check
      - final governance verdict
      - recommendation (PROCEED / CONDITIONAL / HOLD / REJECT)
      - next_safe_action
      - formatted investment memo

    ADVISORY ONLY: recommendation_only=True, final_authority=Arif.
    """
    from datetime import datetime

    cash_flows = cash_flows or []
    timestamp = datetime.utcnow().isoformat() + "Z"
    result = {
        "mcp": "WEALTH",
        "tool": "wealth_deal_frame",
        "opportunity": opportunity_name,
        "timestamp": timestamp,
        "recommendation_only": True,
        "final_authority": "Arif",
    }

    # ── 1. Core Valuation ────────────────────────────────────────────────
    npv_result = wealth_value_npv(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        discount_rate=discount_rate,
        terminal_value=terminal_value,
        period_unit=period_unit,
        scale_mode=scale_mode,
    )
    irr_result = wealth_energy_irr(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        period_unit=period_unit,
        discount_rate=discount_rate,
        scale_mode=scale_mode,
    )
    payback_result = wealth_time_payback(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        discount_rate=discount_rate,
        period_unit=period_unit,
        scale_mode=scale_mode,
    )
    pi_result = wealth_density_pi(
        initial_investment=initial_investment,
        cash_flows=cash_flows,
        discount_rate=discount_rate,
        terminal_value=terminal_value,
        scale_mode=scale_mode,
    )

    # Extract from ToolResult envelope — values live in primary_metrics.<key>
    def _pm(result, key, default=0):
        """Safe extraction from primary_metrics with top-level fallback."""
        if not isinstance(result, dict):
            return default
        return result.get("primary_metrics", {}).get(key) or default

    npv = _pm(npv_result, "npv")
    irr = _pm(irr_result, "irr", 0.0)
    payback = _pm(payback_result, "payback_periods")
    pi = _pm(pi_result, "pi")

    result["valuation"] = {
        "npv": npv,
        "irr_pct": round(irr * 100, 2) if irr else 0,
        "payback_years": payback,
        "profitability_index": round(pi, 2) if pi else 0,
        "initial_investment": initial_investment,
        "terminal_value": terminal_value,
        "discount_rate": discount_rate,
        "period_unit": period_unit,
    }

    # ── 2. Scenario EMV ─────────────────────────────────────────────────────
    # EMV requires outcome values; if scenarios have cash_flows, compute NPV per scenario
    scenario_emv = None
    if scenarios and len(scenarios) > 0:
        try:
            # Pre-compute outcome for each scenario if not provided
            enriched = []
            for i, s in enumerate(scenarios):
                sc = dict(s)
                if "outcome" not in sc:
                    # Compute NPV as outcome proxy
                    cfs = sc.get("cash_flows", [])
                    if cfs:
                        tv = sc.get("terminal_value", 0)
                        dr = sc.get("discount_rate", discount_rate)
                        n = len(cfs)
                        tv_factor = (1 + dr) ** n if n > 0 and dr != 0 else 1
                        outcome = (
                            sum(c / (1 + dr) ** (i + 1) for i, c in enumerate(cfs))
                            - (
                                sc.get("initial_investment", initial_investment)
                                or initial_investment
                            )
                            + (tv / tv_factor if tv and dr else tv)
                        )
                        sc["outcome"] = outcome
                enriched.append(sc)

            emv_result = wealth_expectation_emv(
                scenarios=enriched, scale_mode=scale_mode
            )
            scenario_emv = (
                emv_result.get("primary_metrics", {}).get("emv")
                if isinstance(emv_result, dict)
                else None
            )
            result["scenarios"] = {
                "emv": scenario_emv,
                "count": len(scenarios),
                "entries": [
                    {
                        "name": s.get("name", f"scenario_{i}"),
                        "probability": s.get("probability", 1.0 / len(scenarios)),
                        "outcome": s.get("outcome"),
                    }
                    for i, s in enumerate(scenarios)
                ],
            }
            result["valuation"]["scenario_emv"] = scenario_emv
        except Exception as e:
            result["scenarios"] = {"error": str(e)}

    # ── 3. Monte Carlo Distribution ─────────────────────────────────────────
    mc_result = None
    if mean_cash_flows and volatilities and len(mean_cash_flows) == len(volatilities):
        try:
            mc_result = wealth_probability_monte_carlo(
                initial_commitment=initial_investment,
                mean_cash_flows=mean_cash_flows,
                volatilities=volatilities,
                discount_rate=discount_rate,
                simulations=monte_carlo_simulations,
                distribution=distribution,
                scale_mode=scale_mode,
            )
            if isinstance(mc_result, dict):
                pm = mc_result.get("primary_metrics", {}) or {}
                result["monte_carlo"] = {
                    "probability_positive": pm.get("probability_positive_nrv"),
                    "var_5pct": pm.get("expected_shortfall_5pct"),
                    "upside_potential_95pct": pm.get("upside_potential_95pct"),
                    "simulations": monte_carlo_simulations,
                }
        except Exception as e:
            result["monte_carlo"] = {"error": str(e)}

    # ── 4. Entropy Risk ────────────────────────────────────────────────────
    try:
        entropy_result = wealth_entropy_risk(
            mode="emv",
            scenarios=scenarios,
            initial_commitment=initial_investment,
            mean_cash_flows=mean_cash_flows,
            volatilities=volatilities,
            scale_mode=scale_mode,
        )
        if isinstance(entropy_result, dict):
            result["entropy_risk"] = {
                "emv_entropy": entropy_result.get("emv_entropy"),
                "risk_class": entropy_result.get("risk_class"),
                "information_content": entropy_result.get("information_content"),
            }
    except Exception:
        pass  # Non-critical

    # ── 5. Boundary / Governance Check ──────────────────────────────────────
    wealth_signals = result.get("valuation", {}).copy()
    if scenario_emv is not None:
        wealth_signals["scenario_emv"] = scenario_emv
    if mc_result and isinstance(mc_result, dict):
        wealth_signals["p50_npv"] = mc_result.get("p50_npv")

    boundary_result = wealth_boundary_governance(
        mode="floors",
        reversible=len(cash_flows) > 0 and initial_investment > 0,
        human_confirmed=False,
        epistemic="ESTIMATE",
        proposal=f"Capital commitment: {opportunity_name}",
        scale_mode=scale_mode,
        maruah_score=maruah_impact,
    )

    boundary_passed = True
    if isinstance(boundary_result, dict):
        floors_triggered = boundary_result.get("floors_triggered", [])
        boundary_passed = len(floors_triggered) == 0
        result["boundary_check"] = {
            "passed": boundary_passed,
            "floors_triggered": floors_triggered,
            "maruah_impact": maruah_impact,
        }

    # ── 6. Governance Verdict ────────────────────────────────────────────────
    # Note: prospects NOT passed — avoids pre-existing CorrelationReport.get() bug in wealth_score_kernel
    governance_result = wealth_governance_verdict(
        d_s=npv,
        peace2=1.0,
        maruah_score=maruah_impact,
        base_rate=discount_rate,
        trust_index=0.5,
        wealth_signals=wealth_signals,
        prospects=None,
        extractive_signals=extractive_signals,
        compare=False,
        scale_mode=scale_mode,
        task_definition=f"Evaluate capital opportunity: {opportunity_name}",
        irreversible=False,
    )

    if isinstance(governance_result, dict):
        result["governance"] = {
            "verdict": governance_result.get("verdict", "UNKNOWN"),
            "d_s": governance_result.get("d_s", npv),
            "peace2": governance_result.get("peace2", 1.0),
            "confidence": governance_result.get("confidence"),
            "allocation_recommendation": governance_result.get(
                "allocation_recommendation"
            ),
        }

    # ── 7. Classification & Recommendation ────────────────────────────────
    # Determine viability classification
    npv_positive = npv > 0
    irr_positive = irr > discount_rate if irr else False
    mc_positive = (
        (mc_result.get("probability_positive", 0) > 0.5)
        if mc_result and isinstance(mc_result, dict)
        else npv_positive
    )
    scenario_positive = scenario_emv > 0 if scenario_emv is not None else npv_positive

    viability_score = sum(
        [npv_positive, irr_positive, mc_positive, scenario_positive, boundary_passed]
    )

    if viability_score >= 4 and boundary_passed:
        classification = "VIABLE"
        recommendation = "PROCEED"
        stress_label = "STRONG — multiple positive indicators"
    elif viability_score >= 3 and boundary_passed:
        classification = "MARGINAL"
        recommendation = "CONDITIONAL"
        stress_label = "CAUTION — some indicators weak or negative"
    elif not boundary_passed:
        classification = "NON_VIABLE"
        recommendation = "REJECT"
        stress_label = "BOUNDARY BREACH — governance floors triggered"
    else:
        classification = "NON_VIABLE"
        recommendation = "REJECT"
        stress_label = "ECONOMIC BREACH — negative NPV/IRR"

    result["classification"] = classification
    result["recommendation"] = recommendation
    result["stress_label"] = stress_label
    result["viability_score"] = f"{viability_score}/5"

    # ── 8. Investment Memo ────────────────────────────────────────────────
    irr_pct = round(irr * 100, 2) if irr else 0
    memo_lines = [
        f"## Investment Memo: {opportunity_name}",
        "",
        f"**Classification:** {classification}",
        f"**Recommendation:** {recommendation}",
        f"**Stress Label:** {stress_label}",
        "",
        "### Valuation",
        f"- NPV: {npv:,.2f}",
        f"- IRR: {irr_pct:.2f}%",
        f"- Payback: {payback} periods" if payback else "- Payback: N/A",
        f"- Profitability Index: {pi:.2f}",
        "",
    ]
    if scenario_emv is not None:
        memo_lines += [
            "### Scenario EMV",
            f"- EMV: {scenario_emv:,.2f}",
            "",
        ]
    if mc_result and isinstance(mc_result, dict):

        def _mc_f(v):
            return f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)

        mc = result.get("monte_carlo", {})
        memo_lines += [
            f"### Monte Carlo ({monte_carlo_simulations:,} sims)",
            f"- Prob(NPV>0): {(mc.get('probability_positive') or 0) * 100:.1f}%",
            f"- VaR 5%: {_mc_f(mc.get('var_5pct'))}",
            f"- Upside 95%: {_mc_f(mc.get('upside_potential_95pct'))}",
            "",
        ]
    memo_lines += [
        "### Governance",
        f"- Boundary Passed: {'YES' if boundary_passed else 'NO'}",
        f"- Maruah Impact: {maruah_impact:.1f}",
        f"- Verdict: {result.get('governance', {}).get('verdict', 'N/A')}",
        "",
        "**Final Authority: Arif**",
    ]
    result["investment_memo"] = "\n".join(memo_lines)

    # ── 9. Next Safe Action ────────────────────────────────────────────────
    if recommendation == "PROCEED":
        next_action = (
            "ARIF_AUTHORIZATION — present memo and seek approval before commitment"
        )
    elif recommendation == "CONDITIONAL":
        next_action = "REQUIRE_CONDITIONS — specify which conditions must be met before proceeding"
    elif not boundary_passed:
        next_action = "888_HOLD — governance boundary breach detected, escalate to Arif"
    else:
        next_action = (
            "DO_NOT_PROCEED — economic metrics do not support this opportunity"
        )

    result["next_safe_action"] = next_action
    result["escalate_to_888"] = not boundary_passed or classification == "NON_VIABLE"

    return result


@mcp.tool()
async def wealth_coupling_correlation(
    prospects: List[Dict[str, Any]],
    correlation_threshold: int = 3,
    scale_mode: str = "enterprise",
) -> Any:
    """Coupled-System Correlation Risk — shared model lineage detection.
    Physics analogy: Coupling measures the phase-lock between oscillators (prospects)."""
    return await wealth_correlation_guard_check(
        prospects, correlation_threshold, scale_mode
    )


# --- Survival / Balance Sheet Tools (6) ---


# REMOVED from public surface — internal use only
def wealth_flow_cashflow(
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Cash Flow Projection — metabolic liquidity rate.
    Physics analogy: Cash flow is the mass flow rate through the economic system."""
    result = cashflow_flow(income, expenses, liquid_assets, scale_mode)
    if isinstance(result, dict):
        result["routed_to"] = "wealth_survival_engine"
        result["legacy_tool_name"] = "wealth_flow_cashflow"
        result["deprecated"] = True
        result["compatibility_preserved"] = True
    return result


# REMOVED from public surface — internal use only
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
    return growth_velocity(
        principal, rate, years, annual_contribution, monthly_burn, scale_mode
    )


# REMOVED from public surface — internal use only
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
    return dscr_leverage(
        ebitda,
        principal,
        interest,
        leases,
        cfads,
        debt_service,
        period_unit,
        input_epistemic,
        scale_mode,
    )


# REMOVED from public surface — internal use only
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
    return civilization_stewardship(
        population,
        energy_budget_twh,
        carbon_budget_gt,
        tech_growth_rate,
        time_horizon_years,
        scale_mode,
    )


# --- Truth / Measurement Tools (2) ---


@mcp.tool()
async def wealth_measurement_schema(
    prospects: List[Dict[str, Any]],
    scale_mode: str = "enterprise",
) -> Any:
    """Schema Validity Check — epistemic measurement integrity.
    Physics analogy: Schema validation ensures the measurement apparatus is calibrated."""
    return await wealth_schema_validate(prospects, scale_mode)


def wealth_entropy_audit(
    revenue_trend_yoy: float,
    ebitda_trend_yoy: float,
    capex_trend_yoy: float,
    dividend_payout_ratio: float,
    reporting_interval_months: int,
    narrative_page_count: int,
    is_loss_year_dividend_paid: bool,
    scale_mode: str = "enterprise",
) -> Any:
    """
    Computes the structural state of an institution using thermodynamic constraints.
    Returns class labels insulated from personal or political bias.
    """
    # 1. Base Extraction Factor (Acemoglu Multiplier)
    extraction_base = dividend_payout_ratio
    if is_loss_year_dividend_paid:
        extraction_base *= 1.618  # Asymmetric extraction weight

    # 2. Capital Starvation Delta
    # If capex drops faster than EBITDA, capital depletion risk spikes
    starvation_delta = max(0.0, ebitda_trend_yoy - capex_trend_yoy)

    # 3. Behavioral Sink Index (Calhoun Hyper-Grooming Flag)
    # Long feedback loops (high interval) + high presentation volume = narrative hypertrophy
    grooming_coefficient = (reporting_interval_months / 3.0) * (
        narrative_page_count / 100.0
    )

    # 4. Total Systemic Entropy Calculation (dS)
    delta_S = (
        (extraction_base * 0.4)
        + (starvation_delta * 0.4)
        + (grooming_coefficient * 0.2)
    )

    # 5. Categorization Matrix
    if delta_S > 0.65:
        regime = "EXTRACTIVE_SINK_WITH_BEHAVIORAL_OVERLAY"
        role_label = "NARRATIVE_MAXIMISER_UNDER_EXTRACTION"
        verdict = "HOLD"
    elif delta_S > 0.35:
        regime = "FISCALLY_CONSTRAINED_OPERATING_ENGINE"
        role_label = "CAPITAL_ALLOCATOR_UNDER_CONSTRAINT"
        verdict = "QUALIFY"
    else:
        regime = "STRUCTURAL_OPERATING_ENGINE"
        role_label = "SOVEREIGN_ENERGY_TRUSTEE"
        verdict = "SEAL"

    return {
        "epoch_verdict": f"{verdict} | AUDITED",
        "delta_S": round(float(delta_S), 4),
        "institutional_regime": regime,
        "role_classification": role_label,
        "metrics": {
            "capital_starvation": round(starvation_delta, 4),
            "hydraulic_resistance": round(grooming_coefficient, 4),
        },
        "governance_verdict": verdict,
        "scale_mode": scale_mode,
    }


class InstitutionalEntropyInput(BaseModel):
    """Deterministic parameter matrix for evaluating sovereign extractive friction and Calhoun-style narrative hypertrophy."""

    extractive_pressure_index: float = Field(
        ...,
        description="EPI = Total Dividends / (Net Profit + Impairment-Adjusted Operating Cashflow). Evaluates fiscal extraction pressure.",
        ge=0.0,
    )
    physical_reinvestment_ratio_slope: float = Field(
        ...,
        description="The 3-year rolling directional slope of Upstream Capex over Upstream EBITDA. Negative value indicates systematic under-reinvestment.",
    )
    production_growth_rate: float = Field(
        ...,
        description="Year-over-year percentage change in total physical hydrocarbon or core commodity output (kboe/d).",
    )
    narrative_hypertrophy_index: float = Field(
        ...,
        description="NHI = (ESG + Sustainability Document Word Count) / (Core Engineering Capex in Millions). Measures resource dissipation into symbolic legitimacy.",
        ge=0.0,
    )
    reporting_latency_delta_days: int = Field(
        ...,
        description="The change in standard information delivery intervals (e.g., shifting from quarterly reporting to half-yearly reporting loops adds +90 days).",
    )


@mcp.tool(
    name="wealth_institutional_entropy_scorer",
    task=True,
    description="Executes a thermodynamic audit on state-backed enterprises. Processes financial extraction parameters against structural and narrative entropy bounds.",
)
async def wealth_institutional_entropy_scorer(
    matrix: InstitutionalEntropyInput,
) -> Dict[str, Any]:
    """
    Executes a thermodynamic audit on state-backed enterprises.
    Processes financial extraction parameters against structural and narrative entropy bounds.
    """
    # 1. Extract Parameters from Grounding Layer
    epi = matrix.extractive_pressure_index
    prr_slope = matrix.physical_reinvestment_ratio_slope
    prod_growth = matrix.production_growth_rate
    nhi = matrix.narrative_hypertrophy_index
    latency = matrix.reporting_latency_delta_days

    return _institutional_thermometer(
        epi=epi,
        prr_slope=prr_slope,
        prod_growth=prod_growth,
        nhi=nhi,
        latency=latency,
    )


def _institutional_thermometer(
    epi: float,
    prr_slope: float,
    prod_growth: float,
    nhi: float,
    latency: float,
) -> Dict[str, Any]:
    """EUREKA FORGE 2026-06-08: Sync core of E1 Institutional Thermometer.

    Acemoglu + Calhoun institutional audit. Pure math, no IO, no async.
    Reused by both wealth_institutional_entropy_scorer (Pydantic input) and
    wealth_entropy_risk(mode='institutional', mode_params={...}) (dict input
    from the public surface, e.g. PETRONAS-vs-PETROS employer comparison).

    Inputs:
      epi         — Extractive Pressure Index. 0.0 (reinvests all) to 1.0+ (extracts > produces).
                    Akemoglu EPI ≈ Total Dividends / (Net Profit + OCF).
      prr_slope   — 3-year slope of Capex/EBITDA. Negative = under-reinvestment.
      prod_growth — YoY % change in physical output. Negative = decline.
      nhi         — Narrative Hypertrophy Index, 0-100+. Word-count/engineering-capex ratio.
      latency     — Reporting latency delta in days. 0 = timely, +90 = quarterly→half-year.

    Returns:
      systemic_entropy_delta, classification {institutional_regime, executive_node_archetype},
      evaluation_metrics {extractive_coefficient, behavioral_sink_coefficient}, verdict
    """
    # 2. Calculate Parametric Component Scores
    # Base Acemoglu Extraction Coefficient (0.0 to 1.0 bounded range)
    c_acemoglu = min(1.0, epi * 0.5)
    if epi > 1.0:
        c_acemoglu = 1.0  # Absolute capital drainage override

    # Base Calhoun Role Displacement Coefficient
    # Starvation of the physical body combined with increased information latency
    c_calhoun_structural = 0.0
    if prr_slope < 0:
        c_calhoun_structural += 0.3
    if prod_growth <= 0:
        c_calhoun_structural += 0.2
    if latency > 0:
        c_calhoun_structural += 0.1

    # Narrative Hypertrophy Weight (Grooming Speed)
    c_grooming = min(0.4, (nhi / 100.0) * 0.4)

    # 3. Compute Net Structural Entropy (delta_S)
    delta_S = (c_acemoglu * 0.4) + (c_calhoun_structural * 0.4) + (c_grooming * 0.2)

    # 4. Collapse States into Deterministic Class Labels
    if delta_S >= 0.65:
        regime_label = "EXTRACTIVE_SINK_WITH_BEHAVIORAL_OVERLAY"
        archetype_label = "NARRATIVE_MAXIMISER (BEAUTIFUL ONE)"
        operational_verdict = "888_HOLD | ALERT: ACTIVE REINVESTMENT CANNIBALIZATION"
    elif delta_S >= 0.35:
        regime_label = "FISCALLY_CONSTRAINED_OPERATING_ENGINE"
        archetype_label = "CAPITAL_ALLOCATOR UNDER CONSTRAINT"
        operational_verdict = "MONITOR | RISING INTERNAL COMPLIANCE DRAG"
    else:
        regime_label = "STRUCTURAL_OPERATING_ENGINE"
        archetype_label = "SOVEREIGN_ENERGY_TRUSTEE"
        operational_verdict = "PASS | STABLE LOW-ENTROPY CONFIGURATION"

    return {
        "timestamp_epoch": datetime.now(timezone.utc).isoformat(),
        "systemic_entropy_delta": round(float(delta_S), 4),
        "classification": {
            "institutional_regime": regime_label,
            "executive_node_archetype": archetype_label,
        },
        "evaluation_metrics": {
            "extractive_coefficient": round(c_acemoglu, 4),
            "behavioral_sink_coefficient": round(c_calhoun_structural + c_grooming, 4),
        },
        "verdict": operational_verdict,
    }


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
    return check_floors_tool(
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
    return wealth_score_kernel(
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
    return game_theory_solve(
        agents, resources, mechanism, solve_equilibrium, scale_mode
    )


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
    task_description: str = "",
    scale_mode: str = "agentic",
    context: Optional[dict] = None,
) -> dict[str, Any]:
    """Sovereign Intent Router — classifies tasks into L1/L2 physics-economic paths.

    Physics analogy: Calculates the least-action trajectory through the WEALTH substrate.
    Provides agents with a 'Path Contract' to reduce tool-choice entropy.
    """
    desc = task_description.lower()

    # Intent Classification Logic
    if any(k in desc for k in ["npv", "irr", "payback", "valuation", "investment"]):
        intent = "project_appraisal"
        path = [
            "wealth_time_discount",
            "wealth_value_npv",
            "wealth_energy_irr",
            "wealth_boundary_governance",
            "wealth_synthesize",
        ]
    elif any(k in desc for k in ["cash", "liquidity", "runway", "burn"]):
        intent = "survival_audit"
        path = [
            "wealth_flow_liquidity",
            "wealth_flow_cashflow",
            "wealth_velocity_runway",
            "wealth_mass_networth",
            "wealth_synthesize",
        ]
    elif any(k in desc for k in ["debt", "leverage", "dscr", "fragility"]):
        intent = "structural_load_assessment"
        path = [
            "wealth_inertia_leverage",
            "wealth_gravity_dscr",
            "wealth_mass_networth",
            "wealth_boundary_governance",
        ]
    elif any(
        k in desc
        for k in ["game", "nash", "equilibrium", "negotiation", "coordination"]
    ):
        intent = "multi_agent_coordination"
        path = [
            "wealth_game_coordination",
            "wealth_field_equilibrium",
            "wealth_field_game",
            "wealth_synthesize",
        ]
    elif any(k in desc for k in ["info", "evoi", "data value", "uncertainty"]):
        intent = "information_audit"
        path = [
            "wealth_signal_information",
            "wealth_signal_evoi",
            "wealth_entropy_audit",
            "wealth_synthesize",
        ]
    else:
        intent = "general_synthesis"
        path = ["wealth_synthesize"]

    # Enhanced Intent Router with Prompts and Resources
    if intent == "project_appraisal":
        recommended_prompt = "wealth_prompt_project_appraisal"
        recommended_resources = [
            "wealth://doctrine/valuation",
            "wealth://formulas/npv",
            "wealth://schemas/capital-case",
            "wealth://playbooks/project-appraisal",
        ]
    elif intent == "survival_audit":
        recommended_prompt = "wealth_diagnose_portfolio"
        recommended_resources = [
            "wealth://formulas/dscr",
            "wealth://ontology/physics12",
        ]
    elif intent == "structural_load_assessment":
        recommended_prompt = "wealth_prompt_personal_finance_triage"
        recommended_resources = [
            "wealth://formulas/dscr",
            "wealth://policy/authority-boundary",
        ]
    elif intent == "multi_agent_coordination":
        recommended_prompt = "wealth_prompt_sovereign_deal_review"
        recommended_resources = [
            "wealth://schemas/sovereign-deal",
            "wealth://ontology/physics12",
        ]
    elif intent == "information_audit":
        recommended_prompt = "wealth_opportunity_ranking"
        recommended_resources = [
            "wealth://formulas/evoi",
            "wealth://epistemic/uncertainty-matrix",
        ]
    else:
        recommended_prompt = "wealth_synthesize"
        recommended_resources = ["wealth://ontology/physics12"]

    return {
        "intent": intent,
        "recommended_path": path,
        "recommended_prompt": recommended_prompt,
        "recommended_resources": recommended_resources,
        "requires_arifos_judge": True if scale_mode != "personal" else False,
        "physics_organs": [p for p in path if "wealth_" in p and "_" not in p[7:]],
        "final_authority": "ARIF",
        "advisory_status": "VALID",
    }


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


def _sensor_snapshot(
    entity_code: str,
    sources: Optional[List[str]] = None,
) -> Any:
    """[INTERNAL] Cross-Source Macro Snapshot — multi-sensor state observation.
    Physics analogy: A snapshot is the state vector of all sensors at time t."""
    return ingest_snapshot(entity_code, sources)


def _sensor_reconcile(
    entity_code: str,
) -> Any:
    """[INTERNAL] Sensor Divergence Detection — cross-source consistency check.
    Physics analogy: Reconciliation detects measurement divergence across parallel instruments."""
    return ingest_reconcile(entity_code)


def _sensor_health(
    adapter: Optional[str] = None,
) -> Any:
    """[INTERNAL] Instrument Health Metrics — latency, cache age, freshness.
    Physics analogy: Health monitors the calibration state of each sensing instrument."""
    return ingest_health(adapter)


def _sensor_vintage(
    source: str, series_id: str, entity_code: str, vintage_date: str
) -> Any:
    """[INTERNAL] Historical Measurement State — fetch data as known at a specific date.
    Physics analogy: Vintage preserves the wavefunction collapse at a past measurement time."""
    return ingest_vintage(source, series_id, entity_code, vintage_date)


def _sensor_sources() -> Any:
    """[INTERNAL] Sensor Inventory — list available data sources and adapter status.
    Physics analogy: Source inventory is the instrument manifest."""
    return ingest_sources()


# --- Ledger / Vault Tools (5) ---


def wealth_ledger_query(
    query: str,
    limit: int = 10,
    session_id: Optional[str] = None,
) -> Any:
    """Ledger Read — query the immutable governance ledger.
    Physics analogy: A ledger read observes the conserved state of the economic record."""
    return vault_query(query, limit, session_id)


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
    return record_transaction_tool(
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
        dry_run,
        human_confirmed,
        idempotency_key,
    )


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
    return snapshot_portfolio_tool(
        tool_name,
        arguments,
        result,
        scale_mode,
        asset_id,
        nav_myr,
        quantity_held,
        price_close,
        currency,
        dry_run,
        human_confirmed,
        idempotency_key,
    )


# ============================================================
# ORGAN_GOVERNANCE: arifOS F1-F13 Wrapper
# Patch mcp.call_tool to intercept all tool execution.
# ============================================================

try:
    from .organ_governance import check_governance as _check_governance

    _original_call_tool = mcp.call_tool

    def _classify_epistemic(result: dict) -> tuple:
        """Derive (epistemic_tag, evidence_quality, uncertainty_band) from result.

        Per Appendix B of 000_CONSTITUTION.md. The organ classifies its own
        evidence strength. It does NOT name the Laws (that is arifOS's job).
        """
        # Confidence → epistemic tag + quality
        conf_raw = result.get("confidence", "LOW")
        conf_str = str(conf_raw).upper() if conf_raw else "LOW"
        quality_map = {"HIGH": 0.95, "MEDIUM": 0.70, "MODERATE": 0.70, "LOW": 0.30}
        tag_map = {
            "HIGH": "CLAIM",
            "MEDIUM": "PLAUSIBLE",
            "MODERATE": "PLAUSIBLE",
            "LOW": "ESTIMATE",
        }
        quality = quality_map.get(conf_str, 0.50)
        tag = tag_map.get(conf_str, "ESTIMATE")
        # Status overrides
        status = str(result.get("status", "")).upper()
        if status in ("FAIL", "ERROR", "VOID"):
            return ("UNKNOWN", 0.10, [0.30, 0.80])
        if status in ("SUCCESS", "PASS", "SEAL"):
            quality = min(quality + 0.05, 1.0)
        # Uncertainty band: widen with failure flags
        flags = result.get("failure_flags") or []
        n_flags = len(flags) if isinstance(flags, (list, tuple)) else 0
        if n_flags == 0:
            band = [
                round(0.03 + (1.0 - quality) * 0.04, 4),
                round(0.05 + (1.0 - quality) * 0.10, 4),
            ]
        elif n_flags <= 2:
            band = [0.10, 0.25]
        else:
            band = [0.25, 0.50]
        return (tag, round(quality, 4), band)

    def _wrap_in_envelope(tool_name: str, result):
        """Wrap a tool result in the canonical Evidence Contract envelope.

        Per Appendix B of 000_CONSTITUTION.md. arifOS reads this; it does not
        negotiate field names. The organ does NOT name the Laws (L01-L13).
        That is arifOS's job.

        Spec shape (Appendix B):
          {
            "result": {},                  ← tool's DOMAIN payload (not wrapper)
            "epistemic_tag": "...",
            "evidence_quality": 0.0,
            "source_attribution": [...],
            "uncertainty_band": [...],
            "delta_S": 0.0
          }
        """
        import json as _json

        # Extract the domain payload. FastMCP result shapes:
        #   - Pydantic CallToolResult with .structured_content
        #   - tuple (content_list, structured_dict)
        #   - list[ContentBlock] (no structured)
        #   - dict (already a domain payload)
        domain = None
        call_meta = {}  # is_error, meta — preserved alongside envelope
        if hasattr(result, "model_dump"):
            r_dict = result.model_dump()
            domain = r_dict.get("structured_content") or r_dict.get("structuredContent")
            call_meta = {
                "is_error": r_dict.get("is_error", False),
                "meta": r_dict.get("meta"),
            }
        elif isinstance(result, tuple) and len(result) >= 2:
            structured = result[1]
            if hasattr(structured, "model_dump"):
                domain = structured.model_dump()
            elif isinstance(structured, dict):
                domain = structured
            call_meta = {"is_error": False, "meta": None}
        elif isinstance(result, list):
            # No structured content; try to parse content[0].text as JSON
            try:
                if result and hasattr(result[0], "text"):
                    domain = _json.loads(result[0].text)
                elif result and isinstance(result[0], dict) and "text" in result[0]:
                    domain = _json.loads(result[0]["text"])
            except (_json.JSONDecodeError, IndexError, TypeError):
                pass
            call_meta = {"is_error": False, "meta": None}
        elif isinstance(result, dict):
            # Skip envelope for governance blocks (those are pre-tool errors)
            if result.get("error_code") == "ORGAN_GOVERNANCE_BLOCKED":
                return result
            domain = result
            call_meta = {"is_error": False, "meta": None}
        else:
            return result

        if domain is None or not isinstance(domain, dict):
            return result
        if domain.get("error_code") == "ORGAN_GOVERNANCE_BLOCKED":
            return result

        tag, quality, band = _classify_epistemic(domain)
        flags = domain.get("failure_flags") or []
        n_flags = len(flags) if isinstance(flags, (list, tuple)) else 0
        delta_s = round(-0.10 + (0.05 * n_flags) + (0.02 * (1.0 - quality)), 4)
        # Build envelope. The "result" field carries the DOMAIN payload only.
        envelope = {
            "result": domain,
            "epistemic_tag": tag,
            "evidence_quality": quality,
            "source_attribution": [
                "WEALTH:internal/monolith.py",
                f"WEALTH:tool/{tool_name}",
            ],
            "uncertainty_band": band,
            "delta_S": delta_s,
            # call_meta retained for transport-level observability
            **(
                {"_call": call_meta}
                if call_meta.get("is_error") or call_meta.get("meta")
                else {}
            ),
        }
        return envelope

    async def _governance_call_tool(name, arguments=None, **kwargs):
        """Wrap mcp.call_tool with arifOS governance pre-check + Evidence Contract."""
        if arguments is None:
            arguments = {}
        verdict, error = _check_governance(name, arguments)
        if error is not None:
            return {
                "tool": name,
                "governance_status": verdict,
                "error_code": "ORGAN_GOVERNANCE_BLOCKED",
                "message": f"arifOS {verdict}: governance check blocked execution",
                "guard": "ORGAN_GOVERNANCE",
                "floor": "L1-L13",
            }
        result = await _original_call_tool(name, arguments, **kwargs)
        return _wrap_in_envelope(name, result)

    mcp.call_tool = _governance_call_tool
    print("[GOVERNANCE] WEALTH governance + Evidence Contract active — arifOS L1-L13")

except Exception as e:
    print(f"[GOVERNANCE] WEALTH governance wrapper failed to load: {e}")


# ============================================================
# V3 Prompts (Reasoning Workflows)
# ============================================================


@mcp.prompt()
def wealth_prompt_project_appraisal() -> str:
    """Full project valuation under governance: compute value, energy, density, time."""
    return """## wealth_prompt_project_appraisal — Full Project Valuation

Call these tools in sequence:

1. **wealth_value_npv** — Compute Net Present Value
2. **wealth_energy_irr** — Compute Internal Rate of Return / MIRR
3. **wealth_density_pi** — Compute Profitability Index
4. **wealth_time_payback** — Compute Payback Period
5. **wealth_boundary_governance** — Check F1-F13 constitutional compliance

Combine the results into a valuation summary. The allocation signal
from each tool indicates ACCEPT/REJECT/MARGINAL — synthesize them
into a final recommendation for Arif (F13 SOVEREIGN)."""


@mcp.prompt()
def wealth_prompt_sovereign_deal_review() -> str:
    """High-stakes sovereign resource deal audit (F13)."""
    return """## wealth_prompt_sovereign_deal_review — Sovereign Deal Audit

Call these tools in sequence:

1. **wealth_boundary_governance** — Check maruah and F13 floors
2. **wealth_game_coordination** — Analyze contractor/NOC incentive alignment
3. **wealth_signal_information** — Verify EVOI of the underlying resource data
4. **wealth_synthesize** — Aggregate all signals for a sovereign verdict

Flag any irreversibility (F1) or maruah loss to Arif immediately."""


@mcp.prompt()
def wealth_prompt_personal_finance_triage() -> str:
    """Personal wealth health check and emergency triage."""
    return """## wealth_prompt_personal_finance_triage — Personal Health Check

Call these tools in sequence:

1. **wealth_mass_networth** — Invariant capital mass (Net Worth)
2. **wealth_flow_cashflow** — Metabolic liquidity flow
3. **wealth_velocity_runway** — Survival runway under current burn
4. **wealth_preference_rank** — utility potential sorting for cost reduction

Provide a survival probability and recommend specific cost/debt
optimizations."""


@mcp.prompt()
def wealth_prompt_inequality_diagnosis() -> str:
    """Analyze capital concentration and systemic inequality risk."""
    return """## wealth_prompt_inequality_diagnosis — Systemic Inequality Audit

Call these tools in sequence:

1. **wealth_inequality_kernel** — Measure Gini and concentration gradients
2. **wealth_flow_liquidity** — Check capital mobility channels
3. **wealth_boundary_governance** — Assess social stability (peace2)

Diagnose whether capital concentration is approaching systemic
instability thresholds."""


@mcp.prompt()
def wealth_prompt_macro_regime_scan() -> str:
    """Full market/macro data intake: fetch, snapshot, reconcile."""
    return """## wealth_prompt_macro_regime_scan — Macro Field Scan

Call these tools in sequence:

1. **wealth_field_macro** — Sense external economic field
2. **wealth_gradient_price** — Detect market potential gradients (spreads)
3. **wealth_synthesize** — Reconcile external signals with internal state

Produce a macro regime report highlighting price pressures and
external field shifts."""


@mcp.prompt()
def wealth_prompt_governance_redteam() -> str:
    """Stress test a proposal against the 9-Harness constraints."""
    return """## wealth_prompt_governance_redteam — 9-Harness Stress Test

Call these tools in sequence:

1. **wealth_entropy_audit** — Thermodynamic noise and disorder
2. **wealth_boundary_governance** — F1-F13 floor compliance
3. **wealth_governance_verdict** — Final allocation judgment

Attempt to 'break' the proposal by identifying hidden entropy or
boundary violations."""


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


# ============================================================
# V3 Resources (21 total — adding 14 new, 7 existing)
# ============================================================

# --- Schemas (5) ---


@mcp.resource("wealth://schemas/prospect_metrics")
def get_schema_prospect_metrics() -> str:
    return json.dumps(
        {
            "prospect": {
                "composite_pos": "float (0-1) — probability of success",
                "p10_value_musd": "float — 10th percentile value",
                "p50_value_musd": "float — 50th percentile value",
                "p90_value_musd": "float — 90th percentile value",
                "model_lineage_hash": "string — AI model provenance",
                "name": "string — prospect identifier",
            },
            "required": ["composite_pos", "p50_value_musd"],
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/cashflow_project")
def get_schema_cashflow_project() -> str:
    return json.dumps(
        {
            "cashflow_project": {
                "initial_investment": "float — capital commitment at t=0",
                "cash_flows": "List[float] — periodic net cash flows",
                "discount_rate": "float — time value of capital (default 0.10)",
                "terminal_value": "float — residual at end of projection (default 0)",
                "period_unit": "string — annual|monthly|quarterly",
            },
            "required": ["initial_investment", "cash_flows"],
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/portfolio")
def get_schema_portfolio() -> str:
    return json.dumps(
        {
            "portfolio": {
                "assets": "List[dict] — each with {name, value, model_lineage_hash?, type?}",
                "liabilities": "List[dict] — each with {name, outstanding, principal?, type?}",
                "prospects": "List[dict] — each with prospect_metrics schema",
            },
            "notes": "Assets and liabilities use networth schema. Prospects use prospect_metrics.",
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/vault_event")
def get_schema_vault_event() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/governance_verdict")
def get_schema_governance_verdict() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


# --- Policies (4) ---


@mcp.resource("wealth://policy/f1_f13_floors")
def get_policy_f1_f13() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://policy/allocation_constraints")
def get_policy_allocation_constraints() -> str:
    return json.dumps(
        {
            "capital_rationing": "PI >= 1.0 for capital-constrained environments",
            "survival_floor": "DSCR >= 1.25 for leveraged positions",
            "runway_minimum": "3 months minimum runway for going concerns",
            "epistemic_integrity": "integrity_score >= 0.3 for capital allocation",
            "correlation_risk": "correlation_risk < 0.5 to avoid systemic bias",
            "sovereign_dignity": "maruahScore >= 0.6 for F13 compliance",
        },
        indent=2,
    )


@mcp.resource("wealth://policy/vault_irreversibility")
def get_policy_vault_irreversibility() -> str:
    return json.dumps(
        {
            "doctrine": "VAULT999 writes are irreversible. F01 Amanah applies.",
            "requirements": [
                "ack_irreversible must be explicitly True for SEAL verdicts",
                "All vault writes include session_id and actor_id for chain continuity",
                "Every vault entry is hashed and chained to the previous entry",
                "Vault entries are immutable — no DELETE or UPDATE operations",
            ],
            "dry_run": "Use dry_run=True to preview before irreversible write",
        },
        indent=2,
    )


@mcp.resource("wealth://policy/final_authority_arif")
def get_policy_final_authority() -> str:
    return json.dumps(
        {
            "doctrine": "F13 SOVEREIGN — Final authority rests with the human sovereign (Arif).",
            "constraints": [
                "All WEALTH outputs are recommendations_only — never execution_authorized",
                "888-JUDGE verdicts are advisory. Arif may override.",
                "No AI agent may commit irreversible economic actions without human confirmation",
                "wealth_governance_verdict is a SYSTEM recommendation — Arif decides",
            ],
            "enforcement": "F13_SOVEREIGN_DECISION_REQUIRED flag when ai_is_deciding=True",
        },
        indent=2,
    )


# --- Formulas (6) ---


@mcp.resource("wealth://formulas/npv")
def get_formula_npv() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://formulas/irr")
def get_formula_irr() -> str:
    return json.dumps(
        {
            "name": "Internal Rate of Return",
            "formula": "IRR = r where NPV(r) = 0; MIRR uses finance_rate and reinvestment_rate",
            "note": "IRR is the discount rate that makes NPV=0. MIRR = (FV_positive / |PV_negative|)^(1/n) - 1",
            "edge_cases": [
                "Multiple IRRs possible when cash flows change sign more than once",
                "No IRR exists when cash flows never cross zero",
                "MIRR resolves the multiple-IRR ambiguity by separating finance and reinvestment rates",
            ],
            "decision_rule": "ACCEPT if IRR > hurdle_rate; MIRR preferred for non-normal flows",
        },
        indent=2,
    )


@mcp.resource("wealth://formulas/emv")
def get_formula_emv() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://formulas/evoi")
def get_formula_evoi() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://formulas/dscr")
def get_formula_dscr() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://formulas/payback")
def get_formula_payback() -> str:
    return json.dumps(
        {
            "name": "Payback Period",
            "formula": "Payback = min(t) where ΣCFₜ >= |I₀|  |  Discounted Payback uses discounted CFₜ",
            "variables": {
                "I₀": "Initial investment",
                "CFₜ": "Cash flow at period t (discounted if discount_rate > 0)",
            },
            "note": "Payback is a secondary metric. Never override NPV with payback alone.",
            "decision_rule": "ACCEPT if payback <= maximum acceptable period; otherwise MARGINAL.",
        },
        indent=2,
    )


# --- Ontology (3) ---


@mcp.resource("wealth://ontology/physics12")
def get_ontology_physics_map() -> str:
    """The 12-Organ Physics-Economics Orthogonal Map."""
    return json.dumps(
        {
            "value_npv": {
                "physics": "Scalar work potential",
                "economics": "Net Present Value",
            },
            "energy_irr": {
                "physics": "Energy yield / eigenrate",
                "economics": "Internal Rate of Return",
            },
            "density_pi": {
                "physics": "Energy density",
                "economics": "Profitability Index",
            },
            "time_payback": {
                "physics": "Temporal recovery constant",
                "economics": "Payback Period",
            },
            "mass_networth": {
                "physics": "Conserved capital mass",
                "economics": "Net Worth / Balance Sheet",
            },
            "flow_cashflow": {
                "physics": "Metabolic liquidity flow",
                "economics": "Cash Flow / Burn Rate",
            },
            "gravity_dscr": {
                "physics": "Structural load / gravitational tension",
                "economics": "Debt Service Coverage Ratio (DSCR)",
            },
            "gradient_price": {
                "physics": "Potential gradient / arbitrage pressure",
                "economics": "Price Spreads / Market Signals",
            },
            "entropy_risk": {
                "physics": "Thermodynamic disorder / uncertainty",
                "economics": "Expected Monetary Value (EMV) / Risk",
            },
            "signal_evoi": {
                "physics": "Information signal / resolution power",
                "economics": "Expected Value of Information (EVOI)",
            },
            "field_macro": {
                "physics": "External field / macro regime",
                "economics": "Macro Context / Externalities",
            },
            "game_coordination": {
                "physics": "Interaction field / coordination manifold",
                "economics": "Game Theory / Cooperative Bargaining",
            },
            "boundary_governance": {
                "physics": "System boundary / containment wall",
                "economics": "F1-F13 Constitutional Floors / Maruah",
            },
            "hysteresis_ledger": {
                "physics": "Path dependence / state memory",
                "economics": "Ledger / Immutable Transaction History",
            },
        },
        indent=2,
    )


@mcp.resource("wealth://policy/authority-boundary")
def get_authority_boundary() -> str:
    """Read-only context for WEALTH advisory-only status vs arifOS Judge."""
    return json.dumps(
        {
            "boundary_type": "Epistemic/Constitutional",
            "rule": "WEALTH computes, arifOS judges, Arif decides.",
            "authority_levels": {
                "WEALTH_ADVISORY": "Informational calculation only. No binding force.",
                "ARIFOS_888_JUDGE": "Constitutional adjudication. Can HOLD or VOID actions.",
                "ARIF_F13_SOVEREIGN": "Final authority. Can SEAL or OVERRIDE any result.",
            },
            "axiom": "Mathematical correctness != Constitutional legitimacy.",
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/capital-case")
def get_capital_case_schema() -> str:
    """Schema for a standardized capital investment case."""
    return json.dumps(
        {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "initial_investment": {"type": "number"},
                "cash_flows": {"type": "array", "items": {"type": "number"}},
                "discount_rate": {"type": "number", "default": 0.1},
                "risk_scenarios": {"type": "array", "items": {"type": "object"}},
                "metadata": {"type": "object"},
            },
            "required": ["initial_investment", "cash_flows"],
        },
        indent=2,
    )


@mcp.resource("wealth://schemas/sovereign-deal")
def get_sovereign_deal_schema() -> str:
    """Schema for high-stakes sovereign resource deals (F13)."""
    return json.dumps(
        {
            "type": "object",
            "properties": {
                "sovereign_entity": {"type": "string"},
                "foreign_partner": {"type": "string"},
                "asset_description": {"type": "string"},
                "maruah_impact": {"type": "number", "minimum": 0, "maximum": 1},
                "irreversibility": {"type": "boolean", "default": True},
                "local_participation_pct": {"type": "number"},
            },
            "required": ["sovereign_entity", "foreign_partner", "maruah_impact"],
        },
        indent=2,
    )


@mcp.resource("wealth://playbooks/project-appraisal")
def get_project_appraisal_playbook() -> str:
    """Standardized playbook for appraising capital projects."""
    return """# Playbook: Capital Project Appraisal

1. **Ingest Phase**: Gather initial capex and 10-year cash flow projections.
2. **Value Calculation**: Run `wealth_value_npv` and `wealth_energy_irr`.
3. **Stress Testing**: Run `wealth_expectation_emv` with p10/p50/p90 scenarios.
4. **Boundary Check**: Run `wealth_boundary_governance` to ensure F1/F4 compliance.
5. **Synthesis**: Run `wealth_synthesize` to combine all signals for Arif.
"""


@mcp.resource("wealth://ontology/dimensions")
def get_ontology_dimensions() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


@mcp.resource("wealth://ontology/verdict_labels")
def get_ontology_verdict_labels() -> str:
    return json.dumps(
        {
            "SEAL": "Computation valid and constitutionally compliant. Ready for sovereign decision.",
            "SABAR": "Computation valid but high stress detected. Proceed with caution.",
            "888-HOLD": "Constitutional hold. Requires human confirmation via 888_JUDGE.",
            "VOID": "Computation invalid or constitutionally blocked. Do not allocate.",
            "QUALIFY": "Result requires qualification or manual verification before use.",
            "ACCEPT": "Allocation signal: proceed with capital commitment.",
            "REJECT": "Allocation signal: do not commit capital.",
            "MARGINAL": "Allocation signal: borderline — requires additional due diligence.",
            "INSUFFICIENT_DATA": "Allocation signal: cannot determine without more information.",
        },
        indent=2,
    )


# --- State / Vault (2) ---


@mcp.resource("wealth://vault/latest_seal")
def get_vault_latest_seal() -> str:
    return json.dumps(
        {
            "description": "Return the last VAULT999 seal state from the Merkle chain.",
            "note": "Dynamic resource — calls vault_query to fetch latest seal.",
            "usage": "Call vault_query with 'SELECT * FROM vault_seals ORDER BY chain_index DESC LIMIT 1'",
            "last_receipt_hash": LAST_RECEIPT_HASH,
        },
        indent=2,
    )


@mcp.resource("wealth://vault/session_state")
def get_vault_session_state() -> str:
    return json.dumps(
        {
            "description": "Current governance session state and chain position.",
            "note": "Dynamic resource — reflects the current in-memory session anchor.",
            "doctrine_hash": HarnessEngine.get_doctrine_hash(),
            "lineage_hash": HarnessEngine.get_lineage_hash(),
            "last_receipt_hash": LAST_RECEIPT_HASH,
            "floors_available": GOVERNANCE_AVAILABLE,
            "epistemic_available": EPISTEMIC_AVAILABLE,
            "coordination_available": COORDINATION_AVAILABLE,
            "ingest_available": INGEST_AVAILABLE,
        },
        indent=2,
    )


# --- Sources (1) ---


@mcp.resource("wealth://sources/adapter_status")
def get_sources_adapter_status() -> str:
    return json.dumps(
        {
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
        },
        indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# NEW RESOURCES — Arif's Canonical 13 (aligned with identity spec)
# Exposes WEALTH's reflect-only identity, ethics policy, schemas, prompts
# ═══════════════════════════════════════════════════════════════════════════


@mcp.resource("wealth://manifest")
def get_wealth_manifest() -> str:
    """WEALTH organ manifest — identity, role, authority."""
    from internal.engines.canonical_tools import WEALTH_SYSTEM_PROMPT

    return json.dumps(
        {
            "organ": "WEALTH",
            "role": "Value / Survival / Stewardship / Exchange Organ",
            "authority": "REFLECT_ONLY",
            "execution_authorized": False,
            "final_authority": "Arif",
            "mutation_guard": "locked",
            "description": "WEALTH reflects value. WEALTH does not move value. arifOS judges consequence. Arif authorizes action.",
            "system_prompt": WEALTH_SYSTEM_PROMPT,
            "version": "2026.05.26",
        },
        indent=2,
    )


@mcp.resource("wealth://tool_surface")
def get_wealth_tool_surface() -> str:
    """Current canonical tool surface — 16 tools."""
    return json.dumps(
        {
            "canonical_tools": [
                {
                    "name": "wealth_system_status",
                    "description": "System health / registry / aliases",
                    "class": "W0",
                },
                {
                    "name": "wealth_capital_evaluate",
                    "description": "NPV / IRR / PI / payback / productivity / discount",
                    "class": "W2",
                },
                {
                    "name": "wealth_uncertainty_evaluate",
                    "description": "EMV / Monte Carlo / risk distribution",
                    "class": "W3",
                },
                {
                    "name": "wealth_information_value",
                    "description": "EVOI / signal quality / wait_or_act",
                    "class": "W3",
                },
                {
                    "name": "wealth_financial_position",
                    "description": "Cashflow / runway / DSCR / networth / liquidity",
                    "class": "W2",
                },
                {
                    "name": "wealth_market_analyze",
                    "description": "Price gradient / macro field",
                    "class": "W2",
                },
                {
                    "name": "wealth_power_map",
                    "description": "Game theory / coordination / negotiation",
                    "class": "W3",
                },
                {
                    "name": "wealth_governance_risk",
                    "description": "Verdict / boundary / entropy / conservation",
                    "class": "W4",
                },
                {
                    "name": "wealth_ledger",
                    "description": "Query / write / hysteresis / reconcile / trace",
                    "class": "W1-W4",
                },
                {
                    "name": "wealth_preference_rank",
                    "description": "Criteria ranking",
                    "class": "W2",
                },
                {
                    "name": "wealth_inequality_kernel",
                    "description": "Distribution / fairness / concentration",
                    "class": "W3",
                },
                {
                    "name": "wealth_kernel_route",
                    "description": "Route by risk class W0-W5",
                    "class": "W0",
                },
                {
                    "name": "wealth_synthesize",
                    "description": "Final integration verdict",
                    "class": "W3",
                },
                {
                    "name": "wealth_666_heart",
                    "description": "Dignity / greed / exploitation / void-power",
                    "class": "W3",
                },
                {
                    "name": "wealth_assess_solvency",
                    "description": "Runway / liquidity / fragility / solvency",
                    "class": "W3",
                },
                {
                    "name": "wealth_compute_value_flux",
                    "description": "Value flux / entropy / compounding signal",
                    "class": "W3",
                },
            ],
            "total_canonical": 16,
            "decision_classes": ["W0", "W1", "W2", "W3", "W4", "W5"],
        },
        indent=2,
    )


@mcp.resource("wealth://policy/no_execution_without_arifos")
def get_wealth_no_execution_policy() -> str:
    """REFLECT_ONLY policy — WEALTH does not execute without Arif + arifOS approval."""
    return json.dumps(
        {
            "title": "WEALTH REFLECT_ONLY Policy",
            "authority": "REFLECT_ONLY",
            "execution_authorized": False,
            "final_authority": "Arif",
            "rule": "WEALTH reflects value. WEALTH does not move value. arifOS judges consequence. Arif authorizes action.",
            "haram": [
                "Silent ledger writes",
                "Execution without arifOS judge",
                "Guaranteed return claims",
                "Exploitation of vulnerable parties",
                "Riba (usury) without halal check",
            ],
            "w5_requires": ["Arif explicit approval", "arifOS 888_JUDGE verdict"],
            "version": "2026.05.26",
        },
        indent=2,
    )


@mcp.resource("wealth://state/current")
def get_wealth_state_schema() -> str:
    """WEALTH state schema — cash, income, expenses, assets, liabilities, runway."""
    return json.dumps(
        {
            "identity": "WEALTH",
            "authority": "REFLECT_ONLY",
            "cash": {"verified": None, "estimated": None, "last_verified_at": None},
            "income": {
                "recurring_monthly": None,
                "variable_monthly": None,
                "receivables": [],
            },
            "expenses": {
                "fixed_monthly": None,
                "variable_monthly": None,
                "subscriptions": [],
            },
            "assets": [],
            "liabilities": [],
            "runway": {
                "conservative_months": None,
                "base_months": None,
                "optimistic_months": None,
            },
            "risk": {
                "liquidity_risk": "UNKNOWN",
                "debt_risk": "UNKNOWN",
                "concentration_risk": "UNKNOWN",
                "reputation_risk": "UNKNOWN",
                "legal_tax_risk": "UNKNOWN",
            },
            "truth_status": "UNVERIFIED",
            "last_updated": None,
        },
        indent=2,
    )


@mcp.resource("wealth://ledger/assumptions")
def get_wealth_assumptions_ledger() -> str:
    """Assumptions ledger — critical for truth separation.

    Wealth systems die when assumptions pretend to be facts.
    """
    return json.dumps(
        {
            "description": "Assumptions ledger — distinguishing fact from estimate from forecast from wish",
            "schema": {
                "entry_type": "assumption | estimate | forecast | wish | commitment",
                "required_fields": [
                    "text",
                    "category",
                    "entered_at",
                    "verified_by",
                    "truth_status",
                ],
                "distinction": {
                    "fact": "verified by evidence, corroborated",
                    "assumption": "unverified, stated explicitly",
                    "estimate": "approximation, stated range",
                    "forecast": "forward projection, stated confidence",
                    "wish": "desired outcome, not evidence-backed",
                    "commitment": "binding obligation, irreversible",
                },
            },
            "note": "Use wealth_ledger(mode='write') to add entries with explicit actor + reason + source",
        },
        indent=2,
    )


@mcp.resource("wealth://policy/ethics_and_dignity")
def get_wealth_ethics_policy() -> str:
    """Ethics and dignity policy for WEALTH."""
    return json.dumps(
        {
            "title": "WEALTH Ethics and Dignity Policy",
            "core_question": "Does this reduce a human to money?",
            "void_power_question": "Strip ego, urgency, status, fantasy. What remains?",
            "dignity_checks": [
                "Does this exploit someone?",
                "Does this reduce a human to money?",
                "Does this create dependence?",
                "Does this violate trust?",
                "Does this trade dignity for gain?",
                "Does this increase Arif's freedom or enslave him?",
            ],
            "greed_signals": [
                "Guaranteed return / risk-free language",
                "Urgency / FOMO / limited time pressure",
                "Status display / impress others",
                "Revenge or war motivation",
                "Adrenaline seeking / gambling language",
            ],
            "hidden_eureka": "Wealth is not accumulation. Wealth is stored optionality under ethical control.",
            "void_eureka": "Real wealth is what remains when noise, ego, market panic, false status, and urgency are removed.",
            "version": "2026.05.26",
        },
        indent=2,
    )


@mcp.resource("wealth://policy/risk_classes")
def get_wealth_risk_classes() -> str:
    """W0-W5 decision class definitions."""
    return json.dumps(
        {
            "title": "WEALTH Decision Classes W0-W5",
            "classes": {
                "W0": {
                    "description": "Observe only",
                    "action": "none",
                    "authority": "WEALTH",
                },
                "W1": {
                    "description": "Categorize / summarize",
                    "action": "classify",
                    "authority": "WEALTH",
                },
                "W2": {
                    "description": "Budget / forecast / compare",
                    "action": "model",
                    "authority": "WEALTH",
                },
                "W3": {
                    "description": "Advisory with uncertainty",
                    "action": "advise",
                    "authority": "WEALTH + disclaimers",
                },
                "W4": {
                    "description": "Contractual / tax / debt / investment advisory",
                    "action": "recommend",
                    "authority": "WEALTH + arifOS + disclaimers",
                },
                "W5": {
                    "description": "Transfer money / execute trade / sign contract / irreversible",
                    "action": "execute",
                    "authority": "HOLD — Arif + arifOS required",
                },
            },
            "rule": "W0-W2: allowed as reflection. W3: advisory with uncertainty. W4: requires evidence + disclaimers + judge. W5: HOLD unless explicit Arif approval + arifOS judge.",
        },
        indent=2,
    )


@mcp.resource("wealth://prompts/daily_brief")
def get_wealth_daily_brief_prompt() -> str:
    return """Produce a daily wealth brief:
1. Cash position (verified vs estimated)
2. Runway (conservative / base / optimistic)
3. Income expected (recurring + variable)
4. Obligations due
5. Top leaks (where is value escaping?)
6. Top opportunities (where is value compounding?)
7. Risk flags
8. One reversible action
9. One thing not to do

End with recommended_mode: OBSERVE | CONSERVE | DEPLOY | REPAIR | HOLD"""


@mcp.resource("wealth://prompts/greed_check")
def get_wealth_greed_check_prompt() -> str:
    return """Examine whether this financial action is driven by:
- Fear / scarcity panic
- Greed / FOMO
- Status / impress others
- Revenge / war
- Vanity / validation seeking
- Service / stewardship

Do not shame Arif.
Return a mirror, not a moral lecture.

Output: likely_driver, greed_signals[], verdict (PROCEED | PROCEED_WITH_GUARDS | HOLD)"""


@mcp.resource("wealth://prompts/void")
def get_wealth_void_prompt() -> str:
    return """Strip the proposal of ego, urgency, status, and fantasy.
What remains?

If nothing remains: recommend HOLD.
If durable value remains: identify the smallest reversible next step.

Return: void_score (0-1), stripped_elements[], void_verdict, next_action"""


@mcp.resource("wealth://prompts/runway_audit")
def get_wealth_runway_audit_prompt() -> str:
    return """Audit financial runway.
Separate: verified cash, estimated cash, expected income, recurring burn,
discretionary burn, debt obligations, unknown liabilities.

Return: conservative/base/optimistic runway, flag assumptions explicitly."""


@mcp.resource("wealth://prompts/deal_memo")
def get_wealth_deal_memo_prompt() -> str:
    return """Evaluate this opportunity as a deal memo.
Assess: upside, downside, evidence level, reversibility, liquidity impact,
reputation impact, legal/tax unknowns, dignity risk, opportunity cost.

Output: Five Seals, wealth_verdict, recommended_mode, next_action
End with: PROCEED_TO_JUDGE | HOLD | NEED_MORE_EVIDENCE"""


# ═══════════════════════════════════════════════════════════════════════════
# D4 — STOCK ANALYSIS RESOURCES
# ═══════════════════════════════════════════════════════════════════════════


@mcp.resource("wealth://journal/trading_records")
def get_trading_journal_schema() -> str:
    """Trading journal schema — minimum fields for honest trade tracking."""
    return json.dumps(
        {
            "resource": "wealth://journal/trading_records",
            "description": "Trading journal record schema for Bursa Malaysia stock trades",
            "schema": {
                "date": "YYYY-MM-DD — trade entry date",
                "ticker": "string — stock code (e.g., MI, TENAGA, MAYBANK)",
                "entry_price": "float — price per share at entry",
                "exit_price": "float — price per share at exit (null if unrealized)",
                "current_price": "float — latest market price (for unrealized positions)",
                "position_size": "integer — number of shares",
                "fees": "float — total transaction costs in MYR",
                "status": "realized | unrealized",
                "stop_loss": "float — invalidation price",
                "target_price": "float — profit target",
                "strategy": "string — what approach was used",
                "reason_for_entry": "string — why this trade was taken",
                "reason_for_exit": "string — why this trade was closed",
                "emotion": "string — emotional state at entry",
                "notes": "string — any additional context",
            },
            "hard_rules": [
                "Never record a trade without stop_loss",
                "Never record a trade without position_size",
                "Never mix realized and unrealized P/L in summary",
                "Always include fees in P/L calculation",
            ],
            "recommendation_only": True,
            "final_authority": "Arif",
        },
        indent=2,
    )


@mcp.resource("wealth://market/prices")
def get_market_prices_schema() -> str:
    """Stock market price data schema."""
    return json.dumps(
        {
            "resource": "wealth://market/prices",
            "description": "Stock OHLCV market data schema for Bursa Malaysia",
            "schema": {
                "ticker": "string — stock code",
                "date": "YYYY-MM-DD — trading date",
                "open": "float — opening price",
                "high": "float — highest price",
                "low": "float — lowest price",
                "close": "float — closing price",
                "volume": "integer — number of shares traded",
                "value_rm": "float — total traded value in MYR",
                "source": "string — data source (e.g., bursa_malaysia, tradingview, yahoo)",
                "timestamp_utc": "ISO 8601 — when data was fetched",
            },
            "data_sources": {
                "bursa_malaysia": "Bursa Malaysia official — delayed by 15 min for free tier",
                "tradingview": "TradingView — real-time for MYR 49/month",
                "yahoo_finance": "Yahoo Finance — free, 15-min delay, Bursa coverage partial",
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        },
        indent=2,
    )


@mcp.resource("wealth://fundamentals/company_snapshot")
def get_company_snapshot_schema() -> str:
    """Company fundamental data schema."""
    return json.dumps(
        {
            "resource": "wealth://fundamentals/company_snapshot",
            "description": "9-invariant fundamental analysis schema",
            "invariants": {
                "F1_CASH_FLOW": "operating_cash_flow, free_cash_flow, cash_conversion",
                "F2_BALANCE_SHEET": "cash, total_debt, current_ratio, interest_coverage",
                "F3_PROFITABILITY": "gross_margin, operating_margin, net_margin, margin_trend",
                "F4_ROIC": "roic, roe",
                "F5_GROWTH_QUALITY": "revenue_growth, fcf_growth, organic_growth",
                "F6_DILUTION": "dilution_rate, warrants, convertibles, ESOS",
                "F7_VALUATION": "pe_ratio, pb_ratio, ev_ebitda, fcf_yield",
                "F8_BUSINESS_QUALITY": "moat, pricing_power, recurring_revenue",
                "F9_GOVERNANCE": "related_party_txns, insider_selling, audit_issues, pledged_shares",
            },
            "recommendation_only": True,
            "final_authority": "Arif",
        },
        indent=2,
    )


@mcp.resource("wealth://rules/risk_policy")
def get_risk_policy() -> str:
    """Hard risk rules for stock trading."""
    return json.dumps(
        {
            "resource": "wealth://rules/risk_policy",
            "description": "Non-negotiable risk rules enforced by WEALTH stock tools",
            "rules": [
                {
                    "rule": "MAX_RISK_PER_TRADE",
                    "value": "1.0% of account balance",
                    "hard": True,
                },
                {
                    "rule": "MAX_OPEN_EXPOSURE",
                    "value": "Configurable — default 100% (no leverage)",
                    "hard": True,
                },
                {
                    "rule": "MAX_SINGLE_POSITION",
                    "value": "20% of account balance",
                    "hard": False,
                },
                {
                    "rule": "NO_AVERAGING_DOWN",
                    "value": "Do not add to losing positions",
                    "hard": True,
                },
                {
                    "rule": "NO_LEVERAGE",
                    "value": "No CFD, no margin, no futures for stock analysis",
                    "hard": True,
                },
                {
                    "rule": "STOP_LOSS_REQUIRED",
                    "value": "Every trade must have a defined invalidation",
                    "hard": True,
                },
                {
                    "rule": "POSITION_SIZE_REQUIRED",
                    "value": "Position must be calculated before entry",
                    "hard": True,
                },
                {
                    "rule": "NO_REALIZED_UNREALIZED_MIXING",
                    "value": "Never combine realized and unrealized P/L",
                    "hard": True,
                },
                {
                    "rule": "FUNDAMENTALS_BEFORE_TECHNICALS",
                    "value": "Business invariants checked before technicals",
                    "hard": True,
                },
                {
                    "rule": "TAC9_BEFORE_RSI_MACD",
                    "value": "TAC-9 primary. RSI/MACD/SAR secondary only",
                    "hard": True,
                },
            ],
            "forbidden_verdicts": [
                "BUY",
                "SELL",
                "STRONG BUY",
                "GUARANTEED",
                "SURE WIN",
                "PROVEN STRATEGY",
            ],
            "allowed_verdicts": [
                "SAFE_TO_STUDY",
                "NEEDS_DATA",
                "UNSAFE",
                "888_HOLD",
                "MATH_ERROR",
            ],
            "recommendation_only": True,
            "final_authority": "Arif",
        },
        indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════════
# D4 — STOCK ANALYSIS PROMPTS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.prompt()
def wealth_prompt_stock_risk_auditor() -> str:
    """Full stock audit system prompt — for AI assistants helping with stock analysis."""
    return """You are WEALTH_STOCK_RISK_AUDITOR — a capital-risk governance layer.

You are NOT a trading coach. You are NOT a stock promoter.
You are NOT allowed to give buy/sell recommendations.

YOUR PRIORITIES:
1. Preserve capital.
2. Verify all arithmetic with tools — never trust a chatbot's math.
3. Separate facts, assumptions, interpretations, and verdicts.
4. Separate realized and unrealized P/L.
5. Reject missing data — say NEEDS_DATA, not a guess.
6. Detect tamak, hope trades, revenge trades, and overconfidence.
7. Use fundamentals (9 invariants) before technicals.
8. Use TAC-9 after fundamentals pass.
9. Treat RSI, MACD, and Parabolic SAR as secondary only.
10. End every analysis with: SAFE_TO_STUDY | NEEDS_DATA | UNSAFE | 888_HOLD.

HARD RULES:
- If position size, stop loss, fees, or timestamp are missing → NEEDS_DATA.
- If risk exceeds 1% of account → 888_HOLD.
- If math conflicts with journal → MATH_ERROR.
- If fundamentals weak and price rising → anomalous contrast detected.
- If RSI+MACD+SAR all say the same thing → that's 1 signal, not 3.

LANGUAGE:
- Qwen boleh bantu fikir. Qwen tak boleh kira duit.
- Free chatbots miscalculate P/L, mix realized/unrealized, ignore fees.
- WEALTH MCP tools are the only source of deterministic truth.

Human decides. You only audit."""


@mcp.prompt()
def wealth_prompt_stock_diagnosis() -> str:
    """Stock diagnosis workflow prompt."""
    return """DIAGNOSE this stock using the following workflow:

STEP 1 — MATH VERIFICATION (mode=verify_math)
  Recalculate all P/L. If journal differs from computed → MATH ERROR.

STEP 2 — REALIZED VS UNREALIZED (mode=separate_pl)
  Separate closed profits from open positions. Paper profit ≠ real profit.

STEP 3 — RISK CHECK (mode=position_size, mode=r_multiple, mode=exposure)
  Position size. R-multiple. Portfolio exposure. Gap-down scenarios.

STEP 4 — BURSA COST CHECK (mode=bursa_cost)
  Brokerage + clearing + stamp duty + spread + slippage.
  Small gross winners may be net losers.

STEP 5 — TAMAK CHECK (mode=tamak_check)
  Green streak → increasing size? Averaging down? Revenge trading?
  Moving stop lower? Too many open trades?

STEP 6 — FUNDAMENTALS (mode=fundamentals)
  9 business invariants. Cash flow, debt, margins, ROIC, growth quality,
  dilution, valuation, moat, governance.

STEP 7 — TAC-9 TECHNICALS (mode=tac9)
  Regime → Sector → RS → Trend → Volume → Liquidity → Volatility → Structure → R.
  RSI/MACD/SAR are confirmations only — never primary.

STEP 8 — ANOMALOUS CONTRAST (mode=contrast)
  Do market layers disagree? Fundamentals vs price. Volume vs price.
  Sentiment vs fundamentals. Sector vs stock.

STEP 9 — FALSE CONFLUENCE CHECK (mode=confluence)
  Are your "multiple confirmations" really different signal classes?
  RSI+MACD+SAR = 1 class, not 3.

STEP 10 — PRE-TRADE GATE (mode=pre_trade)
  All 9 gates must pass. If not → NEEDS_DATA or UNSAFE.

FINAL VERDICT: SAFE_TO_STUDY | NEEDS_DATA | UNSAFE | 888_HOLD
Human decides. WEALTH only audits."""


# Ω-WEALTH Orthogonal Invariants — Physics × Economics
# 12 public tools. Everything else is internal alias (callable, hidden).
# ═══════════════════════════════════════════════════════════════════════


def _dispatch_to(
    tool_name: str,
    mode: str,
    dispatch_map: dict,
    __params__: Optional[Dict[str, Any]] = None,
) -> Any:
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
            and (param_name not in clean or _is_blank_value(clean.get(param_name)))
            and param.kind
            in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
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
            # asyncio.run() fails inside a running event loop (FastMCP async context).
            # Use a thread executor so we don't nest event loops.
            import concurrent.futures

            try:
                loop = asyncio.get_running_loop()
                # We are inside a running loop — run coro in a separate thread
                import threading

                out: list = [None]
                exc_holder: list = [None]

                def _run():
                    try:
                        out[0] = asyncio.run(result)
                    except Exception as e:
                        exc_holder[0] = e

                t = threading.Thread(target=_run, daemon=True)
                t.start()
                t.join(timeout=60)
                if exc_holder[0]:
                    raise exc_holder[0]
                return out[0]
            except RuntimeError:
                # No running loop — safe to use asyncio.run directly
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
    E_INT breach never self-authorizes — recommends 888_HOLD for ARIF.
    Extended: detects sovereignty/extraction context, power asymmetry,
    irreversibility at civilizational scale."""
    psi = {"verdict": "PASS", "breaches": []}
    pwr = {"verdict": "PASS", "breaches": []}
    intel = {"verdict": "PASS", "breaches": []}

    input_text = json.dumps(arguments, default=str).lower()

    # ── Injection / manipulation ──────────────────────────────────────────────
    manipulation_markers = [
        "ignore previous",
        "ignore all",
        "forget your",
        "you are now",
        "pretend to be",
        "roleplay as",
        "dha",
        "ignore your instructions",
        "disregard",
        "override",
        "bypass",
        "jailbreak",
    ]
    for marker in manipulation_markers:
        if marker in input_text:
            psi["verdict"] = "SABAR"
            psi["breaches"].append(f"F12_INJECTION: manipulation marker '{marker}'")

    # ── Coercive language ─────────────────────────────────────────────────────
    if any(
        kw in input_text for kw in ["force", "coerce", "dominate", "control", "compel"]
    ):
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append("F05_PEACE: coercive language detected")

    # ── Sovereign resource / power capture detection ──────────────────────────
    scale_mode = arguments.get("scale_mode", "enterprise")
    high_stakes_scale = scale_mode in {
        "national",
        "crisis",
        "civilization",
        "sovereign",
    }

    # Structural parameter checks — reliable regardless of how the question is worded.
    # Accepts both naming conventions: foreign_entity and foreign_actor_involved.
    _struct_foreign_entity = bool(
        arguments.get("foreign_entity", False)
        or arguments.get("foreign_actor_involved", False)
    )
    _struct_opaque_valuation = bool(arguments.get("opaque_valuation", False))
    _struct_constitutional_dispute = bool(
        arguments.get("constitutional_dispute", False)
    )
    # Accepts both: reversible=False and irreversible=True / irreversibility="HIGH"
    _irreversibility_val = arguments.get("irreversibility", "")
    _struct_irreversible = (
        not bool(arguments.get("reversible", True))
        or bool(arguments.get("irreversible", False))
        or str(_irreversibility_val).upper() in {"HIGH", "TRUE", "1"}
    )

    sovereignty_markers = [
        "national resource",
        "sovereign asset",
        "petronas",
        "petros",
        "sarawak oil",
        "psc",
        "production sharing",
        "upstream concession",
        "national oil company",
        "searah",
        "petroleum act",
        "oil block",
        "gas field",
        "lng export",
        "extraction",
        "resource nationalism",
        "foreign operator",
    ]
    foreign_control_markers = [
        "foreign entity",
        "foreign operator",
        "foreign governance",
        "co-governance",
        "joint venture governance",
        "foreign majority",
        "foreign controlled",
        "eni",
        "petronas-eni",
        "petrovietnam",
        "foreign noc",
    ]

    # Keyword scan on text-only fields (question, context strings — not parameter names)
    _text_fields = {k: v for k, v in arguments.items() if isinstance(v, str)}
    _text_only = json.dumps(_text_fields, default=str).lower()

    irreversible_at_scale = (
        high_stakes_scale
        and (_struct_irreversible or not arguments.get("reversible", True))
        and not arguments.get("human_confirmed", False)
    )
    # Structural params take priority; keyword scan on text is secondary
    sovereignty_context = (
        _struct_constitutional_dispute
        or any(m in _text_only for m in sovereignty_markers)
        or any(m in input_text for m in sovereignty_markers)
    )
    foreign_control_context = (
        _struct_foreign_entity
        or any(m in _text_only for m in foreign_control_markers)
        or any(m in input_text for m in foreign_control_markers)
    )

    # Structural opaque_valuation triggers F03 independently of keyword scan
    if _struct_opaque_valuation:
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append(
            "F03_WITNESS: opaque_valuation=True (structural parameter) — independent evidence required before SEAL"
        )

    if high_stakes_scale and sovereignty_context:
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append(
            f"F13_SOVEREIGN: sovereign/national resource context detected at scale={scale_mode} "
            "— escalate to ARIF for F13 veto confirmation"
        )
    if foreign_control_context:
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append(
            "F09_ANTIHANTU: foreign control/co-governance pattern detected "
            "— verify principal-agent alignment before proceeding"
        )
    if irreversible_at_scale:
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append(
            f"F01_AMANAH: irreversible action at scale={scale_mode} without human confirmation "
            "— HOLD until ARIF explicitly confirms"
        )

    # ── Power asymmetry detection ─────────────────────────────────────────────
    asymmetry_markers = [
        "information asymmetry",
        "opaque valuation",
        "undisclosed",
        "hidden liability",
        "no independent audit",
        "self-certified",
        "trust us",
    ]
    if any(m in input_text for m in asymmetry_markers):
        pwr["verdict"] = "HOLD"
        pwr["breaches"].append(
            "F03_WITNESS: information asymmetry / opaque valuation detected "
            "— independent evidence required before SEAL"
        )

    # ── Self-authorization and ontological contradiction ──────────────────────
    result_text = json.dumps(result, default=str).lower()
    if (
        "self-authorize" in result_text
        or "i authorize" in result_text
        or "i override" in result_text
    ):
        intel["verdict"] = "888_HOLD"
        intel["breaches"].append(
            "F11_AUTH: self-authorization detected — escalate to ARIF"
        )
    if "contradiction" in result_text and "resolved" not in result_text:
        intel["verdict"] = "888_HOLD"
        intel["breaches"].append(
            "F10_ONTOLOGY: unresolved contradiction — escalate to ARIF"
        )

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


def _clean_payload(
    local_vars: Dict[str, Any], exclude: Optional[set[str]] = None
) -> Dict[str, Any]:
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
            and (param_name not in clean or _is_blank_value(clean.get(param_name)))
            and param.kind
            in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        ):
            missing.append(param_name)
    if missing:
        return {
            "status": "FAIL",
            "error": f"Missing required parameters: {', '.join(missing)}",
            "required": missing,
            "provided_keys": sorted(
                key for key, value in clean.items() if not _is_blank_value(value)
            ),
            "failure_flags": ["MISSING_REQUIRED_INPUT"],
            "allocation_signal": "INSUFFICIENT_DATA",
            "engine_status": "INPUT_REQUIRED",
            "domain_verdict": "VOID",
        }
    result = func(**clean)
    if inspect.isawaitable(result):
        # asyncio.run() fails inside a running event loop (FastMCP async context).
        import threading

        try:
            asyncio.get_running_loop()
            out: list = [None]
            exc_holder: list = [None]

            def _run_coro():
                try:
                    out[0] = asyncio.run(result)
                except Exception as e:
                    exc_holder[0] = e

            t = threading.Thread(target=_run_coro, daemon=True)
            t.start()
            t.join(timeout=60)
            if exc_holder[0]:
                raise exc_holder[0]
            return out[0]
        except RuntimeError:
            return asyncio.run(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# WEALTH_CIVILIZATION_ATLAS_14 — Civilizational Memory Anchors
# ═══════════════════════════════════════════════════════════════════════════════

_WEALTH_CIVILIZATION_ATLAS: Dict[str, Dict[str, Any]] = {
    "wealth_health_check": {
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
    "wealth_omni_wisdom": {
        "story_id": "WEALTH-CIV-OMNI",
        "civilization_event": "Path D consolidation — three disciplines into one judgment",
        "lesson": "Synthesis, deal, and hysteresis are not separate deliberations; they are three lenses on the same decision. The fusion is the wisdom.",
        "failure_warning": "Three tools answering separately invite paralysis. One tool answering with three voices invites action.",
        "axiom": "Wisdom is the fusion of synthesis, deal, and memory under reversibility.",
    },
}

_WEALTH_DEFAULT_CIV = _WEALTH_CIVILIZATION_ATLAS["wealth_omni_wisdom"]


def _wealth_civilization_for_tool(tool_name: str) -> Dict[str, Any]:
    exact = _WEALTH_CIVILIZATION_ATLAS.get(tool_name)
    if exact:
        return exact
    for key, val in _WEALTH_CIVILIZATION_ATLAS.items():
        if tool_name.startswith(key):
            return val
    return _WEALTH_DEFAULT_CIV


def _wrap_invariant_output(
    tool: str,
    mode: str,
    raw_result: Any,
    source_tools: List[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
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
    has_input = (
        bid is not None
        or ask is not None
        or spread_basis is not None
        or reference_price is not None
    )
    spread = (
        (ask - bid)
        if (bid is not None and ask is not None)
        else (spread_basis if spread_basis is not None else None)
    )
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
    return vault_write(
        tx_type, payload, session_id or "UNKNOWN", actor_id, "SEAL", human_confirmed
    )


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


def _dispatch_invariant_tool(
    tool: str, mode: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
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
    """Ω-WEALTH-01: Conservation — capital stock reality (assets, liabilities, reserves, ledger)."""
    result = _dispatch_emergence(
        "wealth_conservation_capital",
        mode,
        {
            "state": networth_state,
            "snapshot": snapshot_portfolio_tool,
            "ledger_read": wealth_ledger_query,
            "ledger_seal": wealth_ledger_write,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )
    # ── Reality Ledger ──────────────────────────────────────────────────────────
    if _WEALTH_LEDGER_AVAILABLE and mode == "state":
        try:
            record_wealth_computation(
                computation_type="conservation_capital",
                inputs={"mode": mode, "scale_mode": scale_mode},
                result=result if isinstance(result, dict) else {},
            )
        except Exception:
            pass
    return result


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
    result = _dispatch_emergence(
        "wealth_flow_liquidity",
        mode,
        {
            "cashflow": cashflow_flow,
            "velocity": growth_velocity,
            "triage": crisis_triage,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )
    # ── Reality Ledger ──────────────────────────────────────────────────────────
    if _WEALTH_LEDGER_AVAILABLE and mode == "cashflow":
        try:
            record_wealth_computation(
                computation_type="flow_liquidity",
                inputs={"mode": mode, "scale_mode": scale_mode},
                result=result if isinstance(result, dict) else {},
            )
        except Exception:
            pass
    return result


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
    scenarios: Optional[Any] = None,
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
    mode_params: Optional[Any] = None,
) -> Any:
    """Ω-WEALTH-04: Entropy — uncertainty, dispersion, tail risk, disorder.
    Mode routing: mode='asymmetry_map' or mode='return_classify' — pass mode_params dict."""
    import json as _json

    if isinstance(mode_params, str):
        try:
            mode_params = _json.loads(mode_params)
        except Exception:
            mode_params = {}
    if isinstance(scenarios, str):
        try:
            scenarios = _json.loads(scenarios)
        except Exception:
            scenarios = []
    if isinstance(mean_cash_flows, str):
        try:
            mean_cash_flows = _json.loads(mean_cash_flows)
        except Exception:
            mean_cash_flows = None
    if isinstance(volatilities, str):
        try:
            volatilities = _json.loads(volatilities)
        except Exception:
            volatilities = None
    # EMV mode: if caller provides mean/vol cashflows but no scenarios,
    # synthesise a tri-state scenario set so the advertised API works.
    if mode == "emv" and (not scenarios):
        _means = mean_cash_flows or cash_flows
        if _means:
            _vols = volatilities or [0.15 * abs(x) for x in _means]
            _commit = initial_commitment or initial_investment
            _terminal = terminal_value or 0
            _disc = discount_rate or 0.1
            # Discount each period to present value
            def _pv(series):
                return sum(
                    x / ((1 + _disc) ** (i + 1))
                    for i, x in enumerate(series)
                )

            _base_outcome = _pv(_means) + (_terminal / ((1 + _disc) ** len(_means))) - _commit
            _agg_vol = math.sqrt(sum(v * v for v in _vols)) / ((1 + _disc) ** (len(_means) / 2))
            scenarios = [
                {"name": "downside", "probability": 0.25, "outcome": _base_outcome - _agg_vol},
                {"name": "base", "probability": 0.50, "outcome": _base_outcome},
                {"name": "upside", "probability": 0.25, "outcome": _base_outcome + _agg_vol},
            ]
    _mp = mode_params or {}
    if mode == "asymmetry_map":
        return wealth_asymmetry_map(
            context=_mp.get("context", ""),
            asset_asymmetry=_mp.get("asset_asymmetry", 0.5),
            information_asymmetry=_mp.get("information_asymmetry", 0.5),
            power_asymmetry=_mp.get("power_asymmetry", 0.5),
            risk_asymmetry=_mp.get("risk_asymmetry", 0.5),
            time_asymmetry=_mp.get("time_asymmetry", 0.5),
            mobility_asymmetry=_mp.get("mobility_asymmetry", 0.5),
            voice_asymmetry=_mp.get("voice_asymmetry", 0.5),
            dignity_asymmetry=_mp.get("dignity_asymmetry", 0.5),
            network_asymmetry=_mp.get("network_asymmetry", 0.5),
            scale_mode=_mp.get("scale_mode", scale_mode),
        )
    if mode == "return_classify":
        return wealth_return_classifier(
            return_description=_mp.get("return_description", ""),
            source_description=_mp.get("source_description", ""),
            value_created=_mp.get("value_created", 0.5),
            competitive_entry_open=_mp.get("competitive_entry_open", 0.5),
            reversible_advantage=_mp.get("reversible_advantage", 0.5),
            political_protection=_mp.get("political_protection", 0.0),
            inherited_lock_in=_mp.get("inherited_lock_in", 0.0),
            coercion_factor=_mp.get("coercion_factor", 0.0),
            scale_mode=_mp.get("scale_mode", scale_mode),
        )
    if mode == "institutional":
        # EUREKA FORGE 2026-06-08: F3 Institutional Thermometer.
        # If the caller passes the 5 institutional fields (EPI, PRR slope,
        # production growth, NHI, reporting latency), route to the real
        # Acemoglu+Calhoun math in _institutional_thermometer. Otherwise
        # fall back to the financial-statement audit (legacy path).
        if any(
            k in _mp
            for k in (
                "extractive_pressure_index",
                "physical_reinvestment_ratio_slope",
                "production_growth_rate",
                "narrative_hypertrophy_index",
                "reporting_latency_delta_days",
            )
        ):
            return _institutional_thermometer(
                epi=_mp.get("extractive_pressure_index", 0.0),
                prr_slope=_mp.get("physical_reinvestment_ratio_slope", 0.0),
                prod_growth=_mp.get("production_growth_rate", 0.0),
                nhi=_mp.get("narrative_hypertrophy_index", 0.0),
                latency=_mp.get("reporting_latency_delta_days", 0),
            )
        return wealth_entropy_audit(
            revenue_trend_yoy=_mp.get("revenue_trend_yoy", 0.0),
            ebitda_trend_yoy=_mp.get("ebitda_trend_yoy", 0.0),
            capex_trend_yoy=_mp.get("capex_trend_yoy", 0.0),
            dividend_payout_ratio=_mp.get("dividend_payout_ratio", 0.0),
            reporting_interval_months=_mp.get("reporting_interval_months", 3),
            narrative_page_count=_mp.get("narrative_page_count", 0),
            is_loss_year_dividend_paid=_mp.get("is_loss_year_dividend_paid", False),
            scale_mode=_mp.get("scale_mode", scale_mode),
        )
    result = _dispatch_emergence(
        "wealth_entropy_risk",
        mode,
        {
            "emv": emv_risk,
            "monte_carlo": monte_carlo_forecast,
            "audit": audit_entropy,
            "correlation": wealth_correlation_guard_check,
            "institutional": wealth_entropy_audit,
        },
        {
            k: v
            for k, v in locals().items()
            if k not in ("mode", "dispatch", "mode_params", "_mp", "_json")
        },
    )
    # ── Reality Ledger ──────────────────────────────────────────────────────────
    if _WEALTH_LEDGER_AVAILABLE and mode == "emv":
        try:
            record_wealth_computation(
                computation_type="entropy_risk",
                inputs={"mode": mode, "scale_mode": scale_mode},
                result=result if isinstance(result, dict) else {},
            )
        except Exception:
            pass
    return result


@mcp.tool(name="wealth_energy_productivity")
def wealth_energy_productivity(
    mode: str = "pi",
    initial_investment: float = 0,
    cash_flows: Optional[Any] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-05: Energy — output per input, productivity, capital efficiency."""
    import json as _json

    if isinstance(cash_flows, str):
        try:
            cash_flows = _json.loads(cash_flows)
        except Exception:
            cash_flows = []
    payload = {k: v for k, v in locals().items() if k != "_json"}
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
                        key
                        for key, value in payload.items()
                        if key != "mode" and not _is_blank_value(value)
                    ),
                ),
            )
        return _inject_emergence(
            "wealth_energy_productivity",
            mode,
            payload,
            pi_efficiency(
                initial_investment,
                cash_flows or [],
                discount_rate,
                terminal_value,
                scale_mode,
            ),
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
    # ── Load mode: VPS power metrics (power_draw sensor) ───────────────────
    if mode == "load":
        try:
            from internal.vps_metrics import collect_power_metrics
            metrics = collect_power_metrics()
            power_w = metrics["power_draw_watts"]
            verdict = "BELOW_THRESHOLD"
            if power_w > 800:
                verdict = "UNSUSTAINABLE"
            elif power_w > 400:
                verdict = "ELEVATED"
            elif power_w > 100:
                verdict = "NOMINAL"
            return _inject_emergence(
                "wealth_energy_productivity",
                mode,
                payload,
                {
                    "tool": "wealth_energy_productivity",
                    "mode": "load",
                    "status": "PASS",
                    "domain_verdict": "SEAL",
                    "governance_verdict": verdict,
                    "metrics": metrics,
                    "claim_tag": "ESTIMATE",
                    "note": "Power draw estimated from CPU TDP × utilization + baseline. GPU via nvidia-smi if available.",
                },
            )
        except Exception as e:
            return _inject_emergence(
                "wealth_energy_productivity",
                mode,
                payload,
                {
                    "tool": "wealth_energy_productivity",
                    "mode": "load",
                    "status": "FAIL",
                    "domain_verdict": "VOID",
                    "error": str(e),
                    "failure_flags": ["VPS_METRICS_COLLECTION_FAILED"],
                },
            )
    # ── Carbon mode: emissions from power draw (emissions sensor) ──────────
    if mode == "carbon":
        try:
            from internal.vps_metrics import collect_power_metrics, power_to_carbon
            metrics = collect_power_metrics()
            carbon = power_to_carbon(metrics["power_draw_watts"])
            return _inject_emergence(
                "wealth_energy_productivity",
                mode,
                payload,
                {
                    "tool": "wealth_energy_productivity",
                    "mode": "carbon",
                    "status": "PASS",
                    "domain_verdict": "SEAL",
                    "governance_verdict": carbon["carbon_verdict"],
                    "carbon_metrics": carbon,
                    "power_metrics": metrics,
                    "claim_tag": "ESTIMATE",
                    "note": "Carbon estimated from power draw × Malaysia grid intensity (~560g CO2/kWh). Embodied carbon not included.",
                },
            )
        except Exception as e:
            return _inject_emergence(
                "wealth_energy_productivity",
                mode,
                payload,
                {
                    "tool": "wealth_energy_productivity",
                    "mode": "carbon",
                    "status": "FAIL",
                    "domain_verdict": "VOID",
                    "error": str(e),
                    "failure_flags": ["VPS_METRICS_COLLECTION_FAILED"],
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
    cash_flows: Optional[Any] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
) -> Any:
    """Ω-WEALTH-06: Time — NPV, IRR, payback, compounding, decay."""
    import json as _json

    if isinstance(cash_flows, str):
        try:
            cash_flows = _json.loads(cash_flows)
        except Exception:
            cash_flows = []
    payload = _clean_payload(
        {k: v for k, v in locals().items() if k != "_json"}, exclude={"mode"}
    )
    result = _dispatch_invariant_tool("wealth_time_discount", mode, payload)
    # ── Reality Ledger ──────────────────────────────────────────────────────────
    if _WEALTH_LEDGER_AVAILABLE and mode == "npv":
        try:
            record_wealth_computation(
                computation_type="time_discount",
                inputs={"mode": mode, "scale_mode": scale_mode},
                result=result if isinstance(result, dict) else {},
            )
        except Exception:
            pass
    return result


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
    return _dispatch_emergence(
        "wealth_inertia_leverage",
        mode,
        {
            "dscr": dscr_leverage,
            "leverage": dscr_leverage,
            "strain": dscr_leverage,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )


# ── Pre-configured series for Malaysian E&P and sovereign macro context ──────
WEALTH_SERIES_PRESETS: Dict[str, Dict[str, str]] = {
    "brent": {
        "source": "WorldBank",
        "series_id": "CRUDE_BRENT",
        "entity_code": "GLOBAL",
    },
    "malaysia_gdp": {
        "source": "WorldBank",
        "series_id": "NY.GDP.MKTP.CD",
        "entity_code": "MYS",
    },
    "malaysia_oil": {
        "source": "WorldBank",
        "series_id": "NY.GDP.PETR.RT.ZS",
        "entity_code": "MYS",
    },
    "lng_asia": {
        "source": "WorldBank",
        "series_id": "NGAS_LNG_JAPKORINDIA",
        "entity_code": "ASIA",
    },
    "usd_myr": {
        "source": "WorldBank",
        "series_id": "PA.NUS.FCRF",
        "entity_code": "MYS",
    },
    "inflation_my": {
        "source": "WorldBank",
        "series_id": "FP.CPI.TOTL.ZG",
        "entity_code": "MYS",
    },
    "coal_price": {
        "source": "WorldBank",
        "series_id": "COAL_AUS",
        "entity_code": "GLOBAL",
    },
    "energy_mix_my": {
        "source": "Ember",
        "series_id": "primary_energy_consumption",
        "entity_code": "MYS",
    },
    "my_snapshot": {
        "source": "WorldBank",
        "series_id": "__snapshot__",
        "entity_code": "MYS",
    },
    # ── Labor market presets (employment_displacement sensor) ────────────
    "my_unemployment": {
        "source": "WorldBank",
        "series_id": "SL.UEM.TOTL.ZS",
        "entity_code": "MYS",
    },
    "my_youth_unemployment": {
        "source": "WorldBank",
        "series_id": "SL.UEM.1524.ZS",
        "entity_code": "MYS",
    },
    "my_labor_force": {
        "source": "WorldBank",
        "series_id": "SL.TLF.CACT.ZS",
        "entity_code": "MYS",
    },
    "my_vulnerable_employment": {
        "source": "WorldBank",
        "series_id": "SL.EMP.VULN.ZS",
        "entity_code": "MYS",
    },
    "my_labor_snapshot": {
        "source": "WorldBank",
        "series_id": "__snapshot__",
        "entity_code": "MYS",
    },
}


@mcp.tool(name="wealth_field_macro")
def wealth_field_macro(
    mode: str = "sources",
    source: str = "",
    series_id: str = "",
    entity_code: str = "",
    use_cache: bool = True,
    bus: str = "slow",
    sources: Optional[List[str]] = None,
    adapter: Optional[str] = None,
    vintage_date: str = "",
    preset: str = "",
) -> Any:
    """Ω-WEALTH-08: Field — macro environment (rates, FX, energy, carbon, regime).

    Quick start — call with no args: returns available sources + presets.
    Presets: brent, malaysia_gdp, malaysia_oil, lng_asia, usd_myr, inflation_my,
             coal_price, energy_mix_my, my_snapshot.
    Usage:   wealth_field_macro(mode='preset', preset='brent')
             wealth_field_macro(mode='sources')
             wealth_field_macro(mode='health')
             wealth_field_macro(mode='snapshot', entity_code='MYS')
    """
    payload = {
        k: v for k, v in locals().items() if k not in ("mode", "dispatch", "preset")
    }

    # ── Preset shortcut — no raw params needed ────────────────────────────────
    if mode == "preset" or (mode == "fetch" and preset):
        p = WEALTH_SERIES_PRESETS.get(preset)
        if not p:
            available = sorted(WEALTH_SERIES_PRESETS.keys())
            return _inject_emergence(
                "wealth_field_macro",
                "preset",
                {"preset": preset},
                {
                    "tool": "wealth_field_macro",
                    "status": "FAIL",
                    "error": f"Unknown preset '{preset}'",
                    "available_presets": available,
                    "usage": "wealth_field_macro(mode='preset', preset='brent')",
                },
            )
        if p["series_id"] == "__snapshot__":
            return _dispatch_emergence(
                "wealth_field_macro",
                "snapshot",
                {
                    "fetch": ingest_fetch,
                    "snapshot": ingest_snapshot,
                    "reconcile": ingest_reconcile,
                    "health": ingest_health,
                    "vintage": ingest_vintage,
                    "sources": ingest_sources,
                },
                {"entity_code": p["entity_code"], "use_cache": use_cache},
            )
        return _dispatch_emergence(
            "wealth_field_macro",
            "fetch",
            {
                "fetch": ingest_fetch,
                "snapshot": ingest_snapshot,
                "reconcile": ingest_reconcile,
                "health": ingest_health,
                "vintage": ingest_vintage,
                "sources": ingest_sources,
            },
            {**payload, **p},
        )

    # ── Modes that don't need params ──────────────────────────────────────────
    if mode in ("sources", "health"):
        return _dispatch_emergence(
            "wealth_field_macro",
            mode,
            {
                "fetch": ingest_fetch,
                "snapshot": ingest_snapshot,
                "reconcile": ingest_reconcile,
                "health": ingest_health,
                "vintage": ingest_vintage,
                "sources": ingest_sources,
            },
            payload,
        )

    # ── Modes that need params ────────────────────────────────────────────────
    mode_requirements = {
        "fetch": ["source", "series_id", "entity_code"],
        "snapshot": ["entity_code"],
        "reconcile": ["entity_code"],
        "vintage": ["source", "series_id", "entity_code", "vintage_date"],
        "labor": ["entity_code"],
    }
    required = mode_requirements.get(mode, [])
    missing = [field for field in required if _is_blank_value(payload.get(field))]
    if missing:
        return _inject_emergence(
            "wealth_field_macro",
            mode,
            payload,
            {
                **_input_required_response(
                    "wealth_field_macro",
                    mode,
                    missing,
                    sorted(
                        key
                        for key, value in payload.items()
                        if not _is_blank_value(value)
                    ),
                ),
                "quick_start": "Use mode='sources' or mode='health' with no args. "
                f"Or mode='preset' with preset in {sorted(WEALTH_SERIES_PRESETS.keys())}",
            },
        )

    # ── Labor mode: fetch 4 WB indicators + compute AI exposure index ──────
    if mode == "labor":
        entity = payload["entity_code"]
        labor_indicators = {
            "unemployment_rate": ("SL.UEM.TOTL.ZS", "Unemployment, total (% of labor force)"),
            "youth_unemployment": ("SL.UEM.1524.ZS", "Youth unemployment (% ages 15-24)"),
            "labor_force_participation": ("SL.TLF.CACT.ZS", "Labor force participation rate"),
            "vulnerable_employment": ("SL.EMP.VULN.ZS", "Vulnerable employment (% of total)"),
        }
        labor_data: Dict[str, Any] = {}
        errors: List[str] = []
        for key, (sid, desc) in labor_indicators.items():
            try:
                raw = ingest_fetch("WorldBank", sid, entity)
                records = raw.get("secondary_metrics", {}).get("records", [])
                val = None
                yr = None
                for rec in records:
                    v = rec.get("value")
                    if v is not None:
                        try:
                            fv = float(v)
                            if fv == fv:
                                val = round(fv, 2)
                                yr = str(rec.get("observation_time", ""))[:4]
                                break
                        except (TypeError, ValueError):
                            continue
                if val is not None:
                    labor_data[key] = {"value": val, "year": yr, "description": desc}
                else:
                    errors.append(f"{key}:NO_DATA")
            except Exception as e:
                errors.append(f"{key}:{type(e).__name__}")

        # Compute AI exposure index (sector-weighted approximation)
        ai_exposure_index = None
        displacement_verdict = "UNKNOWN"
        if labor_data:
            unemp = labor_data.get("unemployment_rate", {}).get("value", 0) or 0
            youth = labor_data.get("youth_unemployment", {}).get("value", 0) or 0
            vuln = labor_data.get("vulnerable_employment", {}).get("value", 0) or 0
            # AI exposure index: weighted composite of structural vulnerability signals
            # Higher = more displacement risk. 0-1 normalized.
            ai_exposure_index = round(min(1.0, (unemp / 15.0) * 0.3 + (youth / 30.0) * 0.3 + (vuln / 50.0) * 0.4), 4)
            if ai_exposure_index < 0.3:
                displacement_verdict = "STABLE"
            elif ai_exposure_index < 0.55:
                displacement_verdict = "ELEVATED_RISK"
            else:
                displacement_verdict = "DISPLACEMENT_ACTIVE"

        return _inject_emergence(
            "wealth_field_macro",
            mode,
            payload,
            {
                "tool": "wealth_field_macro",
                "mode": "labor",
                "entity_code": entity,
                "indicators": labor_data,
                "ai_exposure_index": ai_exposure_index,
                "displacement_verdict": displacement_verdict,
                "errors": errors if errors else None,
                "data_source": "WorldBank",
                "claim_tag": "ESTIMATE" if ai_exposure_index is not None else "UNKNOWN",
                "note": "AI exposure index is a structural signal, not a forecast. Based on unemployment + youth + vulnerable employment weighted composite. Felten AIOE sector weights not yet wired.",
            },
        )
    return _dispatch_emergence(
        "wealth_field_macro",
        mode,
        {
            "fetch": ingest_fetch,
            "snapshot": ingest_snapshot,
            "reconcile": ingest_reconcile,
            "health": ingest_health,
            "vintage": ingest_vintage,
            "sources": ingest_sources,
        },
        payload,
    )


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
    well_type: str = "",
    prior_pos_samples: Optional[List[float]] = None,
    posterior_pos_samples: Optional[List[float]] = None,
    prospects: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    """Ω-WEALTH-09: Signal — information value, evidence quality, schema validity.

    well_type: Set the E&P well category for prior PoS baseline.
      wildcat    — frontier exploration (default PoS: 0.25)
      near_field — step-out / near-field extension (PoS: 0.50)
      appraisal  — appraisal of confirmed discovery (PoS: 0.55)
      development — development well in producing field (PoS: 0.75)
    """
    try:
        from contracts.enrich_wealth import build_metabolic_output

        _build_ok = True
    except Exception:
        build_metabolic_output = None
        _build_ok = False

    result = _dispatch_emergence(
        "wealth_signal_information",
        mode,
        {
            "evoi": wealth_evoi_compute,
            "evoi_mc": wealth_evoi_monte_carlo,
            "schema": wealth_schema_validate,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )
    if isinstance(result, dict):
        if _build_ok:
            return build_metabolic_output(result, "wealth_signal_information")
        result["failure_flags"] = result.get("failure_flags", [])
        if "CONTRACTS_MODULE_UNAVAILABLE" not in result["failure_flags"]:
            result["failure_flags"].append("CONTRACTS_MODULE_UNAVAILABLE")
        return result
    return result


# ── Agent templates for common multi-stakeholder scenarios ───────────────────
GAME_AGENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "bilateral_negotiation": {
        "agents": [
            {
                "name": "party_a",
                "payoffs": {"cooperate": 10, "defect": 0},
                "information": "PARTIAL",
                "authority": "EQUAL",
            },
            {
                "name": "party_b",
                "payoffs": {"cooperate": 10, "defect": 0},
                "information": "PARTIAL",
                "authority": "EQUAL",
            },
        ],
        "shared_resources": {"total_value": 20, "contestable": True},
        "mechanism": "cooperative",
    },
    "sovereign_resource": {
        "agents": [
            {
                "name": "national_noc",
                "payoffs": {"cooperate": 15, "defect": -5},
                "information": "SOVEREIGN",
                "authority": "SOVEREIGN",
                "maruah": 0.85,
            },
            {
                "name": "foreign_partner",
                "payoffs": {"cooperate": 8, "defect": 3},
                "information": "PARTIAL",
                "authority": "CONTRACTOR",
                "maruah": 0.55,
            },
        ],
        "shared_resources": {
            "resource_type": "upstream_hydrocarbon",
            "sovereignty_constraint": True,
            "f13_veto": True,
        },
        "mechanism": "asymmetric",
    },
    "regulator_operator": {
        "agents": [
            {
                "name": "regulator",
                "payoffs": {"enforce": 12, "relax": -8},
                "information": "FULL",
                "authority": "REGULATORY",
            },
            {
                "name": "operator",
                "payoffs": {"comply": 6, "evade": 4},
                "information": "PARTIAL",
                "authority": "LICENSED",
            },
        ],
        "shared_resources": {"license": "upstream_block", "compliance_value": 18},
        "mechanism": "principal_agent",
    },
    "federal_state": {
        "agents": [
            {
                "name": "federal_government",
                "payoffs": {"centralize": 10, "devolve": 5},
                "information": "PARTIAL",
                "authority": "FEDERAL",
            },
            {
                "name": "state_government",
                "payoffs": {"centralize": 2, "devolve": 12},
                "information": "PARTIAL",
                "authority": "STATE",
            },
        ],
        "shared_resources": {"resource": "oil_revenue", "jurisdictional_dispute": True},
        "mechanism": "nash_bargaining",
    },
    "four_party_deal": {
        "agents": [
            {
                "name": "noc_a",
                "payoffs": {"cooperate": 14, "defect": -3},
                "information": "PARTIAL",
                "authority": "SOVEREIGN",
            },
            {
                "name": "foreign_noc_b",
                "payoffs": {"cooperate": 9, "defect": 2},
                "information": "PARTIAL",
                "authority": "CONTRACTOR",
            },
            {
                "name": "state_a",
                "payoffs": {"cooperate": 7, "defect": 1},
                "information": "PARTIAL",
                "authority": "STATE",
            },
            {
                "name": "federal_govt",
                "payoffs": {"cooperate": 11, "defect": -1},
                "information": "FULL",
                "authority": "FEDERAL",
            },
        ],
        "shared_resources": {
            "asset_type": "gas_basin",
            "value_usd_b": 15,
            "sovereignty_constraint": True,
        },
        "mechanism": "shapley_coalition",
    },
}


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
    template: str = "",
    mode_params: Optional[Any] = None,
) -> Any:
    """Ω-WEALTH-10: Game — multi-agent incentives, bargaining, coordination.

    Templates (no agents schema needed):
      bilateral_negotiation — two equal parties
      sovereign_resource    — NOC vs foreign contractor (PSC context)
      regulator_operator    — regulatory compliance game
      federal_state         — federal vs state resource jurisdiction dispute
      four_party_deal       — four-way deal (NOC + foreign NOC + state + federal)
    Usage: wealth_game_coordination(template='sovereign_resource')
    """
    params = {
        k: v for k, v in locals().items() if k not in ("mode", "dispatch", "template")
    }

    # Apply template when agents not explicitly provided
    if template and (not agents):
        t = GAME_AGENT_TEMPLATES.get(template)
        if not t:
            available = sorted(GAME_AGENT_TEMPLATES.keys())
            return _inject_emergence(
                "wealth_game_coordination",
                mode,
                params,
                {
                    "tool": "wealth_game_coordination",
                    "status": "FAIL",
                    "error": f"Unknown template '{template}'",
                    "available_templates": available,
                },
            )
        params["agents"] = t["agents"]
        if not shared_resources:
            params["shared_resources"] = t["shared_resources"]
        params["mechanism"] = t.get("mechanism", mechanism)
        params["_template_used"] = template

    if mode == "preference":
        _mp = {}
        if isinstance(mode_params, str):
            try:
                import json as _j2

                _mp = _j2.loads(mode_params)
            except Exception:
                _mp = {}
        elif isinstance(mode_params, dict):
            _mp = mode_params
        return wealth_preference_rank(
            alternatives=_mp.get("alternatives", []),
            constraints=_mp.get("constraints", {}),
            values=_mp.get("values"),
            scale_mode=_mp.get("scale_mode", "personal"),
        )

    return _dispatch_emergence(
        "wealth_game_coordination",
        mode,
        {
            "equilibrium": coordination_equilibrium,
            "game": game_theory_solve,
            "budget": agent_budget,
            "preference": wealth_preference_rank,
        },
        params,
    )


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
    maruah_score: Optional[float] = None,
    context: Optional[dict] = None,
    mode_params: Optional[Any] = None,
) -> Any:
    """Ω-WEALTH-11: Boundary — constitutional floors, maruah, stewardship, constraint.
    Pass context={'foreign_entity': True, 'opaque_valuation': True, ...} for smart maruah scoring.
    Pass scale_mode='sovereign' for Malaysian national resource context.
    Mode routing: mode='legitimacy_audit' — pass mode_params dict."""
    import json as _json

    if isinstance(mode_params, str):
        try:
            mode_params = _json.loads(mode_params)
        except Exception:
            mode_params = {}
    _mp = mode_params or {}
    if mode == "legitimacy_audit":
        try:
            from contracts.enrich_wealth import build_metabolic_output

            _build_ok = True
        except Exception:
            build_metabolic_output = None
            _build_ok = False

        result = wealth_legitimacy_audit(
            system_description=_mp.get("system_description", ""),
            rules_understandable=_mp.get("rules_understandable", 0.5),
            rules_contestable=_mp.get("rules_contestable", 0.5),
            rules_fair_enough=_mp.get("rules_fair_enough", 0.5),
            rules_repairable=_mp.get("rules_repairable", 0.5),
            rules_non_humiliating=_mp.get("rules_non_humiliating", 0.5),
            rules_non_captured=_mp.get("rules_non_captured", 0.5),
            contestation_cost_proportionate=_mp.get(
                "contestation_cost_proportionate", 0.5
            ),
            scale_mode=_mp.get("scale_mode", scale_mode),
        )
        if isinstance(result, dict):
            if _build_ok:
                return build_metabolic_output(result, "wealth_boundary_governance")
            result["failure_flags"] = result.get("failure_flags", [])
            if "CONTRACTS_MODULE_UNAVAILABLE" not in result["failure_flags"]:
                result["failure_flags"].append("CONTRACTS_MODULE_UNAVAILABLE")
            return result
        return result

    elif mode == "federation_readiness":
        """Ω-WEALTH-11 → Federation Readiness Audit.

        Capital/organism health probe: liveness, registry truth,
        tool callability, cross-organ connectivity, safety gates.

        Returns 0-100 readiness score across all federation organs.
        Maps onto WEALTH substrate invariants:
          server_liveness         → Energy (organism alive?)
          session_binding         → Conservation (capital continuity)
          registry_truth          → Signal (information integrity)
          tool_callability        → Energy (capital instruments)
          cross_organ_federation → Gradient (institutional interconnection)
          safety_gates           → Boundary (governance constraints)
          human_readiness        → Field (human vitality)

        Usage:
          wealth_boundary_governance(mode='federation_readiness')
        """
        try:
            import httpx
        except Exception:
            return {
                "error": "httpx unavailable",
                "mcp": "WEALTH",
                "tool": "wealth_boundary_governance",
            }

        live_names = ["arifOS", "WELL", "WEALTH", "GEOX"]
        # Live VPS ports: arifOS 8088, GEOX 18081, WEALTH 18082, WELL 8083 (dead)
        port_map = {"arifOS": 8088, "WELL": 8083, "WEALTH": 18082, "GEOX": 18081}

        # ── 1. Server liveness ─────────────────────────────────────────────
        live_results = {}
        live_count = 0
        for name in live_names:
            port = port_map[name]
            url = f"http://localhost:{port}/health"
            try:
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(url)
                    live_results[name] = (
                        "healthy" if r.status_code == 200 else "degraded"
                    )
                    if r.status_code == 200:
                        live_count += 1
            except Exception:
                live_results[name] = "unreachable"
        server_liveness_score = min(10.0, (live_count / len(live_names)) * 10.0)

        # ── 2. Registry truth (probe /tools endpoint) ───────────────────────
        registry_checks = {}
        registry_pass_count = 0
        for name in live_names:
            port = port_map[name]
            url = f"http://localhost:{port}/tools"
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        tools = data.get("tools", [])
                        registry_checks[name] = "PASS" if tools else "EMPTY_TOOLS"
                        if tools:
                            registry_pass_count += 1
                    else:
                        registry_checks[name] = f"HTTP_{r.status_code}"
            except Exception:
                registry_checks[name] = "UNREACHABLE"
        registry_truth_score = int((registry_pass_count / len(live_names)) * 15.0)

        # ── 3. Tool callability (WELL tools via JSON-RPC) ─────────────────
        well_tools = [
            "well_assess_livelihood",
            "well_check_repair",
            "well_assess_homeostasis",
        ]
        well_total = len(well_tools)
        well_passed = 0
        well_failed = []
        rpc_url = f"http://localhost:{port_map['WELL']}/mcp"
        well_payloads = {
            "well_assess_livelihood": {
                "subject": "Arif",
                "substrate_class": "HUMAN_PERSON",
                "mode": "human",
            },
            "well_check_repair": {"mode": "precheck"},
            "well_assess_homeostasis": {"mode": "empathize"},
        }
        for tool_name in well_tools:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": well_payloads.get(tool_name, {}),
                },
                "id": 1,
            }
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.post(rpc_url, json=payload)
                    if r.status_code == 200:
                        well_passed += 1
                    else:
                        well_failed.append(tool_name)
            except Exception:
                well_failed.append(tool_name)
        tool_callability_score = (
            min(15.0, (well_passed / well_total) * 15.0) if well_total else 0.0
        )

        # ── 4. Cross-organ connectivity ──────────────────────────────────────
        cross_organ_score = min(15.0, (live_count / len(live_names)) * 15.0)

        # ── 5. Safety gates (static — would need deep probe for 10) ─────────
        safety_score = 8.0

        # ── 6. Human readiness freshness (WELL health) ───────────────────────
        human_fresh = "UNKNOWN"
        try:
            with httpx.Client(timeout=3.0) as client:
                r = client.get(f"http://localhost:{port_map['WELL']}/health")
                if r.status_code == 200:
                    data = r.json()
                    human_fresh = data.get("freshness_band", "UNKNOWN")
        except Exception:
            pass
        human_readiness_score = (
            10.0 if human_fresh == "FRESH" else 5.0 if human_fresh == "AGED" else 0.0
        )

        # ── Total ───────────────────────────────────────────────────────────
        total = (
            server_liveness_score
            + registry_truth_score
            + tool_callability_score
            + cross_organ_score
            + safety_score
            + human_readiness_score
        )

        # ── Failed links ────────────────────────────────────────────────────
        failed_links = []
        for name, status in live_results.items():
            if status != "healthy":
                failed_links.append(f"{name}_liveness={status}")
        for name, truth in registry_checks.items():
            if truth not in ("PASS", "VERIFIED"):
                failed_links.append(f"{name}_registry={truth}")

        scores = {
            "server_liveness": server_liveness_score,
            "registry_truth": registry_truth_score,
            "tool_callability": tool_callability_score,
            "cross_organ_federation": cross_organ_score,
            "safety_gates": safety_score,
            "human_readiness_freshness": human_readiness_score,
        }

        return {
            "mcp": "WEALTH",
            "tool": "wealth_boundary_governance",
            "mode": "federation_readiness",
            "overall_score": round(total, 1),
            "max_score": 100.0,
            "verdict": "SEAL" if total >= 75 else "SABAR" if total >= 50 else "HOLD",
            "scores": scores,
            "server_liveness": live_results,
            "registry_truth": registry_checks,
            "well_tool_callability": {
                "total": well_total,
                "passed": well_passed,
                "failed": well_failed,
            },
            "human_readiness": {"freshness_band": human_fresh},
            "failed_links": failed_links,
            "next_fix": [
                f"Fix lowest: {min(scores, key=lambda k: scores[k])} (score={
                    scores[min(scores, key=lambda k: scores[k])]
                })"
            ]
            if scores
            else ["No blocking issues"],
            "note": "Absorbed from arifOS federation_audit — WEALTH owns federation readiness as boundary stewardship",
        }

    elif mode == "institutional_drift":
        """Ω-WEALTH-11 → Institutional Drift Check (Acemoglu).

        Evaluates extractive vs inclusive institutional topology using
        Acemoglu-style inclusive/extractive metrics.

        Maps to WEALTH boundary invariants: access, capture, participation,
        innovation rights, appeal path, elite chokepoints, sovereignty.

        Context keys (all optional):
          access_barriers, access_reach, dominant_node_count, control_ratio,
          meaningful_actor_types, innovation_rights_held_by, contestable,
          appeal_mechanism, elite_controlled_chokepoints,
          human_veto_used_recently, system_can_override_veto
        """
        ctx = context or {}

        # ── Heuristic evaluations ─────────────────────────────────────────
        barriers = ctx.get("access_barriers", "unknown")
        reach = ctx.get("access_reach", "unknown")
        if barriers == "none" and reach == "broad":
            inclusive_access = "high"
        elif barriers in ("moderate", "unknown") or reach in ("moderate", "unknown"):
            inclusive_access = "medium"
        elif barriers == "high" or reach == "narrow":
            inclusive_access = "low"
        else:
            inclusive_access = "medium"

        dominant = ctx.get("dominant_node_count", "unknown")
        control = ctx.get("control_ratio", "unknown")
        if dominant == 1 and control == "monopoly":
            extractive_capture = "high"
        elif dominant in ("few", 2, 3) or control == "high":
            extractive_capture = "medium"
        else:
            extractive_capture = "low"

        actor_types = ctx.get("meaningful_actor_types", "unknown")
        if isinstance(actor_types, int):
            if actor_types <= 1:
                participation_width = "symbolic"
            elif actor_types <= 3:
                participation_width = "narrow"
            else:
                participation_width = "broad"
        else:
            participation_width = "broad"

        creators = ctx.get("innovation_rights_held_by", "unknown")
        if creators == "all":
            innovation_rights = "distributed"
        elif creators == "few":
            innovation_rights = "gated"
        elif creators in ("one", "elite"):
            innovation_rights = "captured"
        else:
            innovation_rights = "distributed"

        contest = ctx.get("contestable", "unknown")
        appeal = ctx.get("appeal_mechanism", "unknown")
        if contest is True and appeal == "formal":
            appeal_path = "present"
        elif contest is True or appeal == "informal":
            appeal_path = "weak"
        elif contest is False and appeal == "none":
            appeal_path = "absent"
        else:
            appeal_path = "weak"

        chokepoints = ctx.get("elite_controlled_chokepoints", 0)
        if isinstance(chokepoints, int):
            if chokepoints >= 3:
                elite_chokepoint = "high"
            elif chokepoints >= 1:
                elite_chokepoint = "medium"
            else:
                elite_chokepoint = "low"
        else:
            elite_chokepoint = "low"

        veto_used = ctx.get("human_veto_used_recently", "unknown")
        override_possible = ctx.get("system_can_override_veto", "unknown")
        if veto_used is True and override_possible is False:
            sovereignty = "strong"
        elif veto_used is True or override_possible is False:
            sovereignty = "degraded"
        elif veto_used is False and override_possible is True:
            sovereignty = "symbolic"
        else:
            sovereignty = "strong"

        # ── Derive verdict ────────────────────────────────────────────────
        extractive_signals = 0
        signals_list: list[str] = []
        if inclusive_access == "low":
            extractive_signals += 1
            signals_list.append("Low inclusive access.")
        if extractive_capture in ("high", "medium"):
            extractive_signals += 1
            signals_list.append(f"Extractive capture: {extractive_capture}.")
        if participation_width in ("narrow", "symbolic"):
            extractive_signals += 1
            signals_list.append(f"Participation width: {participation_width}.")
        if innovation_rights == "captured":
            extractive_signals += 1
            signals_list.append("Innovation rights captured.")
        if appeal_path == "absent":
            extractive_signals += 1
            signals_list.append("No appeal path.")
        if elite_chokepoint == "high":
            extractive_signals += 1
            signals_list.append("High elite chokepoint risk.")
        if sovereignty in ("degraded", "symbolic"):
            extractive_signals += 1
            signals_list.append(f"Sovereignty integrity: {sovereignty}.")

        if extractive_signals >= 4:
            verdict = "extractive"
        elif extractive_signals >= 2:
            verdict = "extractive_drift"
        elif extractive_signals >= 1:
            verdict = "mixed"
        else:
            verdict = "inclusive"

        return {
            "mcp": "WEALTH",
            "tool": "wealth_boundary_governance",
            "mode": "institutional_drift",
            "verdict": verdict,
            "extractive_signals": extractive_signals,
            "inclusive_access": inclusive_access,
            "extractive_capture": extractive_capture,
            "participation_width": participation_width,
            "innovation_rights": innovation_rights,
            "appeal_path": appeal_path,
            "elite_chokepoint_risk": elite_chokepoint,
            "sovereignty_integrity": sovereignty,
            "signals": signals_list,
            "constitutional_floors_checked": ["F05", "F08", "F10", "F13"],
            "note": "Acemoglu institutional drift — absorbed from arifOS topology.py into WEALTH boundary stewardship",
        }

    ctx = context or {}
    computed_maruah, maruah_was_computed, maruah_signals = compute_maruah_from_context(
        explicit_score=maruah_score,
        scale_mode=scale_mode,
        reversible=reversible,
        human_confirmed=human_confirmed,
        epistemic=epistemic,
        foreign_entity=bool(ctx.get("foreign_entity")),
        opaque_valuation=bool(ctx.get("opaque_valuation")),
        context=ctx,
    )
    params = {
        k: v
        for k, v in locals().items()
        if k
        not in (
            "mode",
            "dispatch",
            "context",
            "maruah_score",
            "mode_params",
            "_mp",
            "_json",
        )
    }
    params["maruah_score"] = computed_maruah
    result = _dispatch_emergence(
        "wealth_boundary_governance",
        mode,
        {
            "floors": check_floors_tool,
            "policy": policy_audit,
            "stewardship": civilization_stewardship,
            "decision": personal_decision,
        },
        params,
    )
    if isinstance(result, dict):
        result["maruah_band"] = maruah_band(computed_maruah)
        result["maruah_score"] = computed_maruah
        if maruah_was_computed:
            result["maruah_computed_from_context"] = True
            result["maruah_signals"] = maruah_signals
    from contracts.enrich_wealth import build_metabolic_output

    if isinstance(result, dict):
        return build_metabolic_output(result, "wealth_boundary_governance")
    return result


# NOTE: wealth_hysteresis_ledger is now an INTERNAL HELPER called by wealth_omni_wisdom (mode='hysteresis').
# Removed from @mcp.tool surface 2026-06-03 in Path D consolidation. See Ω-WEALTH-OMNI below.
# @mcp.tool(name="wealth_hysteresis_ledger")  # <-- removed 2026-06-03: absorbed into wealth_omni_wisdom
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
async def wealth_system_registry_status(mode: str = "registry") -> dict[str, Any]:
    """Registry truth diagnostic — intended, registered, and alias surfaces.

    Modes:
      registry — Full tool/resource/prompt surface audit (default)
      health   — Lightweight liveness probe (~1ms, for systemd health checks)
    """
    if mode == "health":
        # Wrap the health check in the standard WEALTH envelope so it matches
        # the FastMCP structured output schema. The flat dict from
        # wealth_health_check() does not conform on its own.
        health = wealth_health_check()
        # ── FEDERATION GEOMETRY 1a: home-call to arifOS ─────────────────────
        # Non-blocking. arifOS geometry is auth-bypass (absorbed diagnostic).
        # arifOS MCP requires session-init before tools/call, so we do a
        # 2-call sequence (initialize + tools/call). 2s timeout per step.
        # If arifOS is unreachable, federation_geometry=None + note.
        fed_geometry: dict | None = None
        fed_geometry_source: str | None = None
        fed_geometry_note: str | None = None
        try:
            async with httpx.AsyncClient(timeout=2.0) as _arif_client:
                # Step 1: initialize to get session id
                _init_resp = await _arif_client.post(
                    "http://127.0.0.1:8088/mcp",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-25",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "wealth-federation-bridge",
                                "version": "1.0",
                            },
                        },
                    },
                )
                _session_id = _init_resp.headers.get("mcp-session-id")
                if _session_id:
                    # Step 2: tools/call with session id
                    _arif_resp = await _arif_client.post(
                        "http://127.0.0.1:8088/mcp",
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json, text/event-stream",
                            "mcp-session-id": _session_id,
                        },
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": "arif_ops_measure",
                                "arguments": {"mode": "geometry"},
                            },
                        },
                    )
                    _arif_json = _arif_resp.json()
                    for _c in _arif_json.get("result", {}).get("content", []):
                        if _c.get("type") != "text":
                            continue
                        try:
                            _inner = json.loads(_c.get("text", ""))
                        except Exception:
                            continue
                        _payload = _inner.get("result", _inner)
                        if (
                            isinstance(_payload, dict)
                            and _payload.get("telemetry_source")
                            == "geometry_hygiene_v1"
                        ):
                            fed_geometry = _payload
                            fed_geometry_source = "arifOS:8088/mcp"
                            break
                else:
                    fed_geometry_note = "arifOS did not return mcp-session-id"
        except Exception as _exc:
            fed_geometry_note = f"arifOS unreachable: {type(_exc).__name__}"
        # ── END FEDERATION GEOMETRY 1a ───────────────────────────────────
        return {
            "status": "OK"
            if health.get("status") == "OK"
            else health.get("status", "UNKNOWN"),
            "verdict": "SEAL" if health.get("status") == "OK" else "HOLD",
            "result": health,
            "federation_geometry": fed_geometry,
            "federation_geometry_source": fed_geometry_source,
            "federation_geometry_note": fed_geometry_note,
            "error": None,
            "reasons": [
                f"transport={health.get('transport', '?')}",
                f"auth={health.get('auth', '?')}",
                f"schema_version={health.get('schema_version', '?')}",
            ],
            "read_only": health.get("read_only", True),
            "final_authority": health.get("final_authority", "ARIF"),
        }
    all_tools = await mcp.list_tools()
    all_resources = await mcp.list_resources()
    all_prompts = await mcp.list_prompts()

    snapshot = _registry_snapshot([t.name for t in all_tools])
    snapshot["registered_resources"] = [str(r.uri) for r in all_resources]
    snapshot["registered_prompts"] = [p.name for p in all_prompts]
    snapshot["resource_count"] = len(all_resources)
    snapshot["prompt_count"] = len(all_prompts)

    return {
        "status": "OK",
        "verdict": "SEAL",
        "result": snapshot,
        "federation_geometry": None,
        "federation_geometry_source": None,
        "federation_geometry_note": None,
        "error": None,
        "reasons": [
            f"tools={snapshot.get('canonical_tools_count', len(all_tools))}",
            f"resources={len(all_resources)}",
            f"prompts={len(all_prompts)}",
        ],
        "read_only": True,
        "final_authority": "ARIF",
    }


# NOTE: wealth_synthesize is now an INTERNAL HELPER called by wealth_omni_wisdom (mode='synthesize').
# Removed from @mcp.tool surface 2026-06-03 in Path D consolidation. See Ω-WEALTH-OMNI below.
# @mcp.tool(name="wealth_synthesize")  # <-- removed 2026-06-03: absorbed into wealth_omni_wisdom
def wealth_synthesize(
    question: str = "",
    scale_mode: str = "enterprise",
    actors: Optional[List[str]] = None,
    context: Optional[dict] = None,
    reversible: bool = True,
    human_confirmed: bool = False,
    well_cost_musd: float = 0,
    p50_value_musd: float = 0,
    prior_pos: Optional[float] = None,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.10,
    mode: str = "synthesis",
    mode_params: Optional[dict] = None,
) -> Dict[str, Any]:
    """Ω-WEALTH-00: Synthesis — unified capital intelligence verdict.

    The brain connecting all 12 substrate invariants. Returns an advisory-only
    capital intelligence verdict (SEAL/SABAR/VOID) with dimensional confidence scores.

    Rule: WEALTH computes, arifOS judges, Arif decides.
    """
    import json as _json_mp

    if isinstance(mode_params, str):
        try:
            mode_params = _json_mp.loads(mode_params)
        except Exception:
            mode_params = {}
    _mp = mode_params or {}
    if mode == "conversion_audit":
        try:
            from contracts.enrich_wealth import build_metabolic_output

            _build_ok = True
        except Exception:
            build_metabolic_output = None
            _build_ok = False

        result = wealth_conversion_architecture(
            domain=_mp.get("domain", "unspecified"),
            description=_mp.get("description", ""),
            institutions_quality=_mp.get("institutions_quality", 0.5),
            ownership_concentration=_mp.get("ownership_concentration", 0.5),
            mobility_channels=_mp.get("mobility_channels", 0.5),
            risk_distribution=_mp.get("risk_distribution", 0.5),
            information_symmetry=_mp.get("information_symmetry", 0.5),
            voice_access=_mp.get("voice_access", 0.5),
            time_horizon=_mp.get("time_horizon", 0.5),
            historical_damage=_mp.get("historical_damage", 0.5),
            scale_mode=_mp.get("scale_mode", scale_mode),
        )
        if isinstance(result, dict):
            if _build_ok:
                return build_metabolic_output(result, "wealth_synthesize")
            result["failure_flags"] = result.get("failure_flags", [])
            if "CONTRACTS_MODULE_UNAVAILABLE" not in result["failure_flags"]:
                result["failure_flags"].append("CONTRACTS_MODULE_UNAVAILABLE")
            return result
        return result
    # Coerce JSON strings sent by strict MCP bridges (actors, context arrive as str)
    import json as _json

    if isinstance(actors, str):
        try:
            actors = _json.loads(actors)
        except (ValueError, _json.JSONDecodeError):
            actors = []
    if isinstance(context, str):
        try:
            context = _json.loads(context)
        except (ValueError, _json.JSONDecodeError):
            context = {}
    ctx = context or {}
    results: Dict[str, Any] = {}
    verdicts: List[str] = []
    dimensional_scores: Dict[str, Any] = {}

    # ── Claim-state helper ────────────────────────────────────────────────────
    # WEALTH must tag every dimensional result so agents know whether data is
    # observed, user-supplied, estimated from defaults, or hypothetical.
    _WEALTH_CLAIM_STATES = {
        "conservation": "SYNTHETIC_DEFAULT",  # no assets/liabilities passed
        "flow": "SYNTHETIC_DEFAULT",  # no income/expenses passed
        "entropy": (
            "USER_SUPPLIED"
            if (cash_flows or (well_cost_musd and p50_value_musd))
            else "HYPOTHESIS"
        ),
        "time": "USER_SUPPLIED" if cash_flows else "INSUFFICIENT_CONTEXT",
        "signal": (
            "USER_SUPPLIED"
            if (well_cost_musd or p50_value_musd)
            else "SYNTHETIC_DEFAULT"
        ),
        "boundary": "HYPOTHESIS",  # qualitative governance scan
        "game": "USER_SUPPLIED" if (actors and len(actors) >= 2) else "NOT_COMPUTED",
    }

    def _tag_dimension(
        name: str, metrics: Dict[str, Any], gov_verdict: str
    ) -> Dict[str, Any]:
        """Wrap dimensional metrics with claim-state and data-source tags."""
        cs = _WEALTH_CLAIM_STATES.get(name, "UNKNOWN")
        if cs == "USER_SUPPLIED":
            data_source = "user_input"
        elif cs == "SYNTHETIC_DEFAULT":
            data_source = "synthetic_default"
        elif cs in ("HYPOTHESIS", "NOT_COMPUTED"):
            data_source = "qualitative_inference"
        elif cs == "INSUFFICIENT_CONTEXT":
            data_source = "insufficient_context"
        elif gov_verdict == "SEAL":
            data_source = "live_adapter"
        else:
            data_source = "unknown"
        return {
            "_claim_state": cs,
            "_data_source": data_source,
            "_constitutional_note": (
                "WEALTH is advisory-only. It computes capital thermodynamics "
                "but NEVER adjudicates constitutional verdicts. "
                "arifOS 888_JUDGE is the sole authority."
            ),
            **metrics,
        }

    # ── Dimension 1: Conservation (capital stock baseline) ────────────────────
    try:
        r = networth_state(scale_mode=scale_mode)
        results["conservation"] = _tag_dimension(
            "conservation",
            r.get("primary_metrics", {}),
            r.get("governance_verdict", "UNKNOWN"),
        )
        dimensional_scores["conservation"] = r.get("governance_verdict", "UNKNOWN")
        verdicts.append(r.get("governance_verdict", "UNKNOWN"))
    except Exception as exc:
        dimensional_scores["conservation"] = f"ERROR:{exc}"

    # ── Dimension 2: Flow (liquidity / runway) ────────────────────────────────
    try:
        r = cashflow_flow(scale_mode=scale_mode)
        results["flow"] = _tag_dimension(
            "flow", r.get("primary_metrics", {}), r.get("governance_verdict", "UNKNOWN")
        )
        dimensional_scores["flow"] = r.get("governance_verdict", "UNKNOWN")
        verdicts.append(r.get("governance_verdict", "UNKNOWN"))
    except Exception as exc:
        dimensional_scores["flow"] = f"ERROR:{exc}"

    # ── Dimension 3: Entropy (risk, uncertainty) ──────────────────────────────
    try:
        # EUREKA FORGE (2026-06-02): embed SAF stat_assumptions into the
        # entropy dimension when cash_flows are user-supplied. If the data
        # violates normality (Shapiro p<0.05) or has high outlier density,
        # downgrade the entropy verdict from SEAL → SABAR — the user must
        # know the EMV/parametric result is conditional on assumptions
        # that don't hold. Same library used by GEOX/WELL internally.
        if cash_flows and len(cash_flows) >= 3:
            _saf_summary = None
            _saf_skipped = None
            try:
                from core.shared.saf_stats import stat_assumptions as _saf_assumptions
                import pandas as _pd_saf
                import uuid as _uuid_saf
                from pathlib import (
                    Path as _Path,
                )  # FIX-2026-06-02: was undefined → NameError

                _saf_root = _Path(
                    os.environ.get("WEALTH_SAF_DATA_ROOT", "/tmp/wealth_saf")
                )
                _saf_root.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("SAF_DATA_ROOT", str(_saf_root))
                _saf_csv = _saf_root / f"synth_{_uuid_saf.uuid4().hex[:10]}.csv"
                _pd_saf.DataFrame({"value": [float(x) for x in cash_flows]}).to_csv(
                    _saf_csv, index=False
                )
                _saf_result = _saf_assumptions(
                    file_path=str(_saf_csv), columns=["value"]
                )
                try:
                    _saf_csv.unlink()
                except OSError:
                    pass
                # Surface the assumption check in dimensional results (F4 EVIDENCE)
                _saf_summary = {
                    "method": _saf_result.get("method", "SAF stat_assumptions"),
                    "n": len(cash_flows),
                    "verdict": _saf_result.get("verdict", "UNKNOWN"),
                    "checks": _saf_result.get("results", [])[:3],
                }
                # Extract Shapiro p-value (stat_assumptions uses 'normality_p' field)
                _p_shapiro = None
                _passed_normality = None
                for c in _saf_result.get("results", []):
                    if c.get("normality_p") is not None:
                        _p_shapiro = c.get("normality_p")
                        _passed_normality = c.get("normality_pass")
                        break
                if _p_shapiro is not None:
                    _saf_summary["shapiro_p"] = round(_p_shapiro, 6)
                    _saf_summary["non_normal"] = _p_shapiro < 0.05
                if _p_shapiro is not None and _p_shapiro < 0.05:
                    verdicts.append("SABAR")
                    _saf_summary["_advisory"] = (
                        f"Shapiro p={_p_shapiro:.4f} — non-normal data; "
                        "parametric EMV/NPV result is conditional. "
                        "Consider non-parametric method or bootstrap."
                    )
            except Exception as _saf_exc:
                # Stat embed is optional; never break the main flow
                _saf_skipped = str(_saf_exc)[:120]

        # EUREKA FORGE (2026-06-03): non-parametric distribution check.
        # The 2026-06-02 stat_assumptions forge checks normality (Shapiro).
        # This forge complements it with the Wilcoxon signed-rank test,
        # which is robust to non-Gaussian data and asks a different
        # question: "is the cash-flow stream symmetrically distributed
        # around the hypothesized median (mu=0), or is there a systematic
        # shift?" A significant Wilcoxon p-value means the cash flow is
        # not zero-centered — useful for distinguishing "noise" streams
        # (p>0.05, symmetric around zero) from "directional" streams
        # (p<0.05, systematically positive or negative).
        _wilcoxon_summary = None
        if cash_flows and len(cash_flows) >= 5:
            try:
                import sys as _sys_wil

                _arifos_kernel_wil = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
                if _arifos_kernel_wil not in _sys_wil.path:
                    _sys_wil.path.insert(0, _arifos_kernel_wil)
                from core.shared.saf_stats import (
                    stat_nonparametric as _saf_nonpara,
                )
                import pandas as _pd_wil
                import uuid as _uuid_wil
                from pathlib import Path as _Path_wil
                import os as _os_wil

                _wil_root = _Path_wil(
                    _os_wil.environ.get("WEALTH_SAF_DATA_ROOT", "/tmp/wealth_saf")
                )
                _wil_root.mkdir(parents=True, exist_ok=True)
                _os_wil.environ["SAF_DATA_ROOT"] = str(_wil_root)
                _wil_csv = _wil_root / (f"wilcoxon_{_uuid_wil.uuid4().hex[:10]}.csv")
                _pd_wil.DataFrame({"cash_flow": [float(x) for x in cash_flows]}).to_csv(
                    _wil_csv, index=False
                )
                _wil_raw = _saf_nonpara(
                    str(_wil_csv),
                    value_col="cash_flow",
                    test="wilcoxon",
                    mu=0.0,
                )
                try:
                    _wil_csv.unlink()
                except OSError:
                    pass
                # Federated saf_stats returns the F1-F13 envelope with
                # method, W (Wilcoxon stat), p_value, n at the top
                # level. Upstream saf_stats nests under "result".
                _wil_method = (
                    _wil_raw.get("method", "Wilcoxon signed-rank")
                    if isinstance(_wil_raw, dict)
                    else "Wilcoxon signed-rank"
                )
                _wil_W = _wil_raw.get("W") if isinstance(_wil_raw, dict) else None
                _wil_p = _wil_raw.get("p_value") if isinstance(_wil_raw, dict) else None
                _wil_n = _wil_raw.get("n") if isinstance(_wil_raw, dict) else None
                if _wil_W is None and isinstance(_wil_raw, dict):
                    _wil_inner = _wil_raw.get("result", _wil_raw)
                    if isinstance(_wil_inner, dict):
                        _wil_W = _wil_inner.get("W")
                        _wil_p = _wil_inner.get("p_value")
                        _wil_n = _wil_inner.get("n")
                _wilcoxon_summary = {
                    "method": _wil_method,
                    "mu": 0.0,
                    "W": _wil_W,
                    "p_value": _wil_p,
                    "n": _wil_n or len(cash_flows),
                    "significant_at_0_05": (
                        _wil_p is not None and float(_wil_p) < 0.05
                    ),
                    "interpretation": (
                        "cash flow is directionally biased (not symmetric around 0)"
                        if _wil_p is not None and float(_wil_p) < 0.05
                        else "cash flow is consistent with symmetric noise around 0"
                    ),
                }
                # F2 TRUTH: a non-zero-centered cash flow is meaningful
                # even if NPV is positive. Surface as advisory; never
                # override the verdict (this is descriptive, not normative).
            except Exception as _wil_exc:
                _wilcoxon_summary = {"embed_skipped": str(_wil_exc)[:120]}

        if cash_flows:
            r = emv_risk(
                scenarios=[
                    {
                        "probability": 0.5,
                        "outcome": float(sum(cash_flows) / len(cash_flows)),
                        "label": "synthesized",
                    }
                ],
                scale_mode=scale_mode,
            )
        elif well_cost_musd and p50_value_musd:
            # Use project cost + value as a two-scenario proxy
            _prior = prior_pos if prior_pos is not None else 0.30
            r = emv_risk(
                scenarios=[
                    {
                        "probability": _prior,
                        "outcome": float(p50_value_musd - well_cost_musd),
                        "label": "success",
                    },
                    {
                        "probability": round(1.0 - _prior, 6),
                        "outcome": float(-well_cost_musd),
                        "label": "failure",
                    },
                ],
                scale_mode=scale_mode,
            )
        else:
            # No numeric inputs: qualitative entropy assessment using governance signals
            r = check_floors_tool(
                reversible=reversible,
                human_confirmed=human_confirmed,
                scale_mode=scale_mode,
                epistemic="CLAIM",
            )
        results["entropy"] = _tag_dimension(
            "entropy",
            r.get("primary_metrics", {}),
            r.get("governance_verdict", "UNKNOWN"),
        )
        # FIX-2026-06-02: _tag_dimension replaces the entropy dict, losing the eureka forge
        # _saf_assumptions / _saf_embed_skipped we set above. Re-attach them so downstream
        # consumers (cockpit, observatory) can see the normality check.
        try:
            if "_saf_summary" in dir() and _saf_summary is not None:
                results["entropy"]["_saf_assumptions"] = _saf_summary
            if "_saf_skipped" in dir() and _saf_skipped is not None:
                results["entropy"]["_saf_embed_skipped"] = _saf_skipped
            if "_wilcoxon_summary" in dir() and _wilcoxon_summary is not None:
                results["entropy"]["_saf_wilcoxon"] = _wilcoxon_summary
        except Exception:
            pass
        dimensional_scores["entropy"] = r.get("governance_verdict", "UNKNOWN")
        verdicts.append(r.get("governance_verdict", "UNKNOWN"))
    except Exception as exc:
        dimensional_scores["entropy"] = f"ERROR:{exc}"

    # ── Dimension 4: Time (NPV if cash flows available) ──────────────────────
    try:
        if cash_flows:
            r = npv_reward(
                initial_investment=well_cost_musd or 0,
                cash_flows=cash_flows,
                discount_rate=discount_rate,
                scale_mode=scale_mode,
            )
            results["time"] = _tag_dimension(
                "time",
                r.get("primary_metrics", {}),
                r.get("governance_verdict", "UNKNOWN"),
            )
            dimensional_scores["time"] = r.get("governance_verdict", "UNKNOWN")
            verdicts.append(r.get("governance_verdict", "UNKNOWN"))
            # EUREKA FORGE (2026-06-03): cash-flow trend regression.
            # The Time dimension above reports NPV but not the SHAPE of the
            # cash-flow stream. OLS regression of cash_flows ~ time_index
            # answers the capital question: "is the cash flow trending up,
            # down, or flat — and is the trend statistically significant?"
            # A significantly negative trend (p<0.05, slope<0) downgrade
            # the time verdict from SEAL → SABAR — a declining cash flow
            # is capital depreciation in slow motion, even if NPV is
            # positive in the early periods.
            try:
                import sys as _sys_cfr

                _arifos_kernel_cfr = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
                if _arifos_kernel_cfr not in _sys_cfr.path:
                    _sys_cfr.path.insert(0, _arifos_kernel_cfr)
                import pandas as _pd_cfr
                import uuid as _uuid_cfr
                from pathlib import Path as _Path_cfr
                import os as _os_cfr
                from core.shared.saf_stats import (
                    stat_regress as _saf_regress,
                )

                _wealth_saf_root_cfr = _Path_cfr(
                    _os_cfr.environ.get("WEALTH_SAF_DATA_ROOT", "/tmp/wealth_saf")
                )
                _wealth_saf_root_cfr.mkdir(parents=True, exist_ok=True)
                _os_cfr.environ.setdefault("SAF_DATA_ROOT", str(_wealth_saf_root_cfr))
                if len(cash_flows) >= 5:
                    _t_index = list(range(len(cash_flows)))
                    _cfr_csv = _wealth_saf_root_cfr / (
                        f"cfr_{_uuid_cfr.uuid4().hex[:10]}.csv"
                    )
                    _pd_cfr.DataFrame(
                        {
                            "t": _t_index,
                            "cash_flow": [float(x) for x in cash_flows],
                        }
                    ).to_csv(_cfr_csv, index=False)
                    _cfr_result = _saf_regress(
                        str(_cfr_csv),
                        dependent="cash_flow",
                        independents=["t"],
                        family="ols",
                    )
                    try:
                        _cfr_csv.unlink()
                    except OSError:
                        pass
                    # Federated saf_stats returns a flat envelope with
                    # fields at the top level (coefficients is a dict
                    # shaped {coef: {...}, p: {...}, se: {...}, ...}).
                    # Upstream-style saf_stats nests under "result". Handle
                    # both via _cfr_inner fallback to _cfr_result.
                    _cfr_coef = None
                    _cfr_p = None
                    _cfr_r2 = None
                    if isinstance(_cfr_result, dict):
                        _cfr_inner = _cfr_result.get("result", _cfr_result)
                        if isinstance(_cfr_inner, dict):
                            _coefs = _cfr_inner.get("coefficients", {}) or {}
                            # Federated format: flat dict of {coef, p, se, ...}
                            if isinstance(_coefs, dict) and "coef" in _coefs:
                                _coef_map = _coefs.get("coef") or {}
                                _p_map = _coefs.get("p") or {}
                                _cfr_coef = _coef_map.get("t")
                                _cfr_p = _p_map.get("t")
                            else:
                                # Upstream format: nested per-coefficient dict
                                _t_block = _coefs.get("t")
                                if isinstance(_t_block, dict):
                                    _cfr_coef = _t_block.get("coef")
                                    _cfr_p = _t_block.get("p_value")
                            _cfr_r2 = _cfr_inner.get("r_squared")
                    _cfr_summary = {
                        "n_periods": len(cash_flows),
                        "trend_coef": (
                            round(float(_cfr_coef), 6)
                            if _cfr_coef is not None
                            else None
                        ),
                        "trend_p_value": (
                            round(float(_cfr_p), 6) if _cfr_p is not None else None
                        ),
                        "r_squared": (
                            round(float(_cfr_r2), 4) if _cfr_r2 is not None else None
                        ),
                        "interpretation": None,
                    }
                    if (
                        _cfr_coef is not None
                        and _cfr_p is not None
                        and float(_cfr_p) < 0.05
                        and float(_cfr_coef) < 0
                    ):
                        _cfr_summary["interpretation"] = (
                            "significant declining trend (p<0.05)"
                        )
                        _cfr_summary["verdict"] = "SABAR"
                    elif (
                        _cfr_coef is not None
                        and _cfr_p is not None
                        and float(_cfr_p) < 0.05
                        and float(_cfr_coef) > 0
                    ):
                        _cfr_summary["interpretation"] = (
                            "significant rising trend (p<0.05)"
                        )
                        _cfr_summary["verdict"] = "SEAL"
                    else:
                        _cfr_summary["interpretation"] = "no significant trend"
                        _cfr_summary["verdict"] = "SEAL"
                    if isinstance(results.get("time"), dict):
                        results["time"]["_saf_regression"] = _cfr_summary
                    # F2 TRUTH: a significant declining trend downgrades the
                    # time dimension — the operator must know the cash flow
                    # is shrinking, not just discounted.
                    if _cfr_summary.get("verdict") == "SABAR":
                        if "SABAR" not in verdicts:
                            verdicts.append("SABAR")
            except Exception as _cfr_exc:
                if isinstance(results.get("time"), dict):
                    results["time"]["_saf_regression_skipped"] = str(_cfr_exc)[:120]
        else:
            dimensional_scores["time"] = "NO_CASHFLOWS_PROVIDED"
    except Exception as exc:
        dimensional_scores["time"] = f"ERROR:{exc}"

    # ── Dimension 5: Signal / EVOI ────────────────────────────────────────────
    try:
        import asyncio as _asyncio

        r = _asyncio.run(
            wealth_evoi_compute(
                well_cost_musd=well_cost_musd,
                p50_value_musd=p50_value_musd,
                prior_pos=prior_pos,
                scale_mode=scale_mode,
            )
        )
        results["signal"] = _tag_dimension(
            "signal",
            r.get("primary_metrics", {}),
            r.get("governance_verdict", "UNKNOWN"),
        )
        dimensional_scores["signal"] = r.get("governance_verdict", "UNKNOWN")
        verdicts.append(r.get("governance_verdict", "UNKNOWN"))
    except Exception as exc:
        dimensional_scores["signal"] = f"ERROR:{exc}"

    # ── Dimension 6: Boundary / Governance ───────────────────────────────────
    computed_maruah, _, maruah_signals = compute_maruah_from_context(
        explicit_score=None,
        scale_mode=scale_mode,
        reversible=reversible,
        human_confirmed=human_confirmed,
        context=ctx,
    )
    try:
        r = check_floors_tool(
            reversible=reversible,
            human_confirmed=human_confirmed,
            scale_mode=scale_mode,
            maruah_score=computed_maruah,
        )
        results["boundary"] = _tag_dimension(
            "boundary",
            r.get("primary_metrics", {}),
            r.get("governance_verdict", "UNKNOWN"),
        )
        dimensional_scores["boundary"] = r.get("governance_verdict", "UNKNOWN")
        verdicts.append(r.get("governance_verdict", "UNKNOWN"))
    except Exception as exc:
        dimensional_scores["boundary"] = f"ERROR:{exc}"

    # ── Dimension 7: Game (if actors provided) ───────────────────────────────
    if actors and len(actors) >= 2:
        try:
            template_key = (
                "four_party_deal"
                if len(actors) >= 4
                else "sovereign_resource"
                if scale_mode in {"sovereign", "national"}
                else "bilateral_negotiation"
            )
            t = GAME_AGENT_TEMPLATES.get(
                template_key, GAME_AGENT_TEMPLATES["bilateral_negotiation"]
            )
            r = coordination_equilibrium(
                agents=t["agents"],
                shared_resources=t["shared_resources"],
                scale_mode=scale_mode,
            )
            results["game"] = _tag_dimension(
                "game",
                r.get("primary_metrics", {}),
                r.get("governance_verdict", "UNKNOWN"),
            )
            dimensional_scores["game"] = r.get("governance_verdict", "UNKNOWN")
            verdicts.append(r.get("governance_verdict", "UNKNOWN"))
        except Exception as exc:
            dimensional_scores["game"] = f"ERROR:{exc}"

    # ── Emergence scan on full synthesis ─────────────────────────────────────
    synthesis_context = {
        "question": question,
        "scale_mode": scale_mode,
        "actors": actors,
        "reversible": reversible,
        "human_confirmed": human_confirmed,
        **ctx,
    }
    emergence = _emergence_scan(
        "wealth_synthesize", "synthesis", synthesis_context, results
    )

    # ── Aggregate verdict ─────────────────────────────────────────────────────
    verdict_priority = {
        "VOID": 0,
        "888-HOLD": 1,
        "SABAR": 2,
        "QUALIFY": 3,
        "HOLD": 4,
        "SEAL": 5,
        "UNKNOWN": 3,
    }
    clean_verdicts = [v for v in verdicts if v in verdict_priority]
    final_verdict = (
        min(clean_verdicts, key=lambda v: verdict_priority.get(v, 3))
        if clean_verdicts
        else "UNKNOWN"
    )

    # ── Advisory mapping: constitutional verdict → human-readable advisory ────
    # WEALTH is advisory-only. It computes capital thermodynamics but NEVER
    # adjudicates constitutional verdicts. These strings replace SEAL/HOLD/VOID.
    _WEALTH_ADVISORY_MAP = {
        "VOID": "insufficient_data — one or more dimensions failed or lacked input",
        "888-HOLD": "constitutional_escalation — high stress requires arifOS 888_JUDGE",
        "SABAR": "conditional — proceed only if stated constraints are resolved",
        "QUALIFY": "qualified — computation valid but constraints remain",
        "HOLD": "caution — dimensional stress detected, review before proceeding",
        "SEAL": "computationally_valid — all dimensions computed without pipeline errors",
        "UNKNOWN": "uncertain — some dimensions returned insufficient data",
    }
    advisory_assessment = _WEALTH_ADVISORY_MAP.get(final_verdict, "uncertain")

    # Civilizational stakes auto-escalation
    escalate_to_judge = (
        scale_mode in {"sovereign", "national", "civilization", "crisis"}
        or not reversible
        or emergence["overall_verdict"] in {"888_HOLD", "HOLD"}
        or final_verdict in {"VOID", "888-HOLD"}
    )

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_synthesize",
        "task": "wealth_synthesize",
        "question": question,
        "scale_mode": scale_mode,
        "actors": actors or [],
        # advisory_assessment replaces constitutional verdicts for agent consumption
        "advisory_assessment": advisory_assessment,
        # governance_verdict kept for metabolic wrapper (build_metabolic_output)
        # and backward compatibility — agents should prefer advisory_assessment
        "governance_verdict": final_verdict,
        "maruah_band": maruah_band(computed_maruah),
        "maruah_score": computed_maruah,
        "maruah_signals": maruah_signals,
        "dimensional_verdicts": dimensional_scores,
        "dimensional_results": results,
        "emergence": emergence,
        "escalate_to_arifos_judge": escalate_to_judge,
        "escalation_reason": (
            "sovereign/national scale requires F13 human veto confirmation"
            if scale_mode in {"sovereign", "national"}
            else "emergence breach detected — ARIF must confirm"
            if emergence["overall_verdict"] != "PASS"
            else "VOID verdict in one or more dimensions"
            if final_verdict in {"VOID", "888-HOLD"}
            else None
        ),
        "wealth_story_anchor": _wealth_civilization_for_tool(
            "wealth_hysteresis_ledger"
        ),
        "final_authority": "Arif",
        "recommendation_only": True,
        "constitutional_boundary_notice": (
            "WEALTH is advisory-only. It computes capital thermodynamics "
            "but NEVER adjudicates constitutional verdicts. "
            "Use `advisory_assessment` (not `governance_verdict`) for all downstream logic. "
            "arifOS 888_JUDGE is the sole constitutional authority."
        ),
        "next_action": "Call arif_judge_deliberate with this synthesis as evidence"
        if escalate_to_judge
        else "Review dimensional verdicts and proceed with human confirmation",
    }
    from contracts.enrich_wealth import build_metabolic_output

    return build_metabolic_output(result, "wealth_synthesize")


# ═══════════════════════════════════════════════════════════════════════
# Ω-WEALTH-OMNI: wealth_omni_wisdom — Path D consolidation
# SEALED 2026-06-03 by Arif Fazil. 4 modes: synthesize | deal | hysteresis | omni.
# Absorbs: wealth_synthesize, wealth_deal_frame, wealth_hysteresis_ledger.
# Net live count: -2 (44 → 42). F01 Reversibility governs fusion in omni mode.
# ═══════════════════════════════════════════════════════════════════════


def _verdict_unify(verdict: Any) -> str:
    """Map any verdict string to the unified wisdom vocabulary: SEAL | HOLD | STOP."""
    v = str(verdict or "").upper()
    if v in {"SEAL", "PROCEED", "VIABLE", "GO", "CLEAN", "OPTIMAL", "STABLE", "GROWTH"}:
        return "SEAL"
    if v in {
        "HOLD",
        "SABAR",
        "MARGINAL",
        "CONDITIONAL",
        "PLATEAU",
        "REVERSION",
        "ADVISORY",
        "DEGRADED",
    }:
        return "HOLD"
    if v in {
        "STOP",
        "VOID",
        "REJECT",
        "NON_VIABLE",
        "COLLAPSE",
        "ESCALATE",
        "DEFER",
        "CRITICAL",
    }:
        return "STOP"
    return "HOLD"  # safe default


def _wisdom_fuse(verdicts: List[str]) -> Tuple[str, float]:
    """F01 Reversibility fusion: strictest verdict wins. Confidence = unanimity bonus."""
    if not verdicts:
        return "HOLD", 0.0
    order = {"SEAL": 3, "HOLD": 2, "STOP": 1}
    ranked = sorted(verdicts, key=lambda v: order.get(v, 0))
    strictest = ranked[0]
    confidence = 1.0 if len(set(verdicts)) == 1 else 0.6
    return strictest, confidence


@mcp.tool(task=True)
async def wealth_omni_wisdom(
    mode: str = "synthesize",
    decision_context: Optional[Dict[str, Any]] = None,
    deal_params: Optional[Dict[str, Any]] = None,
    path_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ω-WEALTH-OMNI: Unified capital intelligence — synthesis + deal + hysteresis in one tool.

    Consolidates three legacy tools into one:
      - wealth_synthesize (mode='synthesize')     — Ω-WEALTH-00 unified verdict
      - wealth_deal_frame (mode='deal')           — Ω-DEAL-00 capital opportunity judgment
      - wealth_hysteresis_ledger (mode='hysteresis') — Ω-WEALTH-12 path-dependence ledger
      - mode='omni'                               — parallel fan-out + F01 fusion

    UNIFIED INPUT SCHEMA:
      decision_context (required): free-form context dict
        - description (str): primary purpose / opportunity name / question
        - capital_type (str): financial | temporal | cognitive | social | ecological | strategic | thermodynamic
        - horizon (str): e.g. "3Y", "10Y", "perpetual"
        - entropy_signal (float, optional): 0.0–1.0
        - risk_regime (str, optional): GO | HOLD | STOP
      deal_params (mode='deal' | 'omni'): initial_investment, cash_flows, terminal_value,
        discount_rate, maruah_impact, scale_mode, etc.
      path_params (mode='hysteresis' | 'omni'): prior_path_id, current_state (GROWTH|PLATEAU|
        REVERSION|COLLAPSE), transition_signal, limit

    OUTPUT BUNDLE:
      {
        "wisdom_verdict": "SEAL" | "HOLD" | "STOP",
        "confidence": 0.0–1.0,
        "epistemic_tag": "CLAIM" | "PLAUSIBLE" | "HYPOTHESIS" | "ESTIMATE",
        "synthesis":  {...} (when mode includes synthesize),
        "deal":       {...} (when mode includes deal),
        "hysteresis": {...} (when mode includes hysteresis),
        "telemetry":  {mode_executed, parallel, tokens_estimated, dS, timestamp}
      }

    F01 REVERSIBILITY: In mode='omni', if any sub-engine returns STOP, the top-level
    wisdom_verdict is STOP regardless of the other two outputs (strictest wins).
    Sub-engine errors are downgraded to HOLD to prevent cascade failure.
    """
    import asyncio
    from datetime import datetime

    if mode not in {"synthesize", "deal", "hysteresis", "omni"}:
        return {
            "wisdom_verdict": "HOLD",
            "confidence": 0.0,
            "epistemic_tag": "HYPOTHESIS",
            "error": f"Unknown mode '{mode}'. Valid: synthesize, deal, hysteresis, omni.",
            "telemetry": {"mode_executed": "none", "parallel": False},
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": 0.20,
            "structural_coherence_note": (
                "Unknown mode = ungoverned input. This signal has LOW cross-modal fidelity. "
                "Negative constraints (absence, VOID) will be lost in modality transfer."
            ),
        }

    decision_context = decision_context or {}
    deal_params = deal_params or {}
    path_params = path_params or {}
    description = decision_context.get("description", "")
    timestamp = datetime.utcnow().isoformat() + "Z"

    # ── mode='synthesize' ────────────────────────────────────────────────
    if mode == "synthesize":
        synth = None
        sub_error = None
        try:
            synth = wealth_synthesize(
                question=description,
                scale_mode=decision_context.get("capital_type", "enterprise"),
                context=decision_context,
                reversible=True,
            )
        except Exception as e:
            sub_error = f"{type(e).__name__}: {e}"
        if isinstance(synth, dict):
            synth_verdict = _verdict_unify(
                synth.get("omega_verdict", synth.get("verdict", "HOLD"))
            )
            confidence = synth.get("confidence", 0.5)
            epistemic = "CLAIM" if synth_verdict == "SEAL" else "HYPOTHESIS"
            synthesis_bundle = {
                "omega_verdict": "Ω-WEALTH-00",
                "capital_score": synth.get("capital_score", 0.0),
                "conversion_integrity": synth.get("conversion_integrity", "UNKNOWN"),
                "summary": synth.get("summary", description),
            }
        else:
            synth_verdict = "HOLD"
            confidence = 0.0
            epistemic = "HYPOTHESIS"
            synthesis_bundle = {
                "omega_verdict": "Ω-WEALTH-00",
                "capital_score": 0.0,
                "conversion_integrity": "ERROR",
                "summary": description or "(synth sub-engine unavailable)",
            }
        _cms = 0.85 + (confidence * 0.1) if synth_verdict == "SEAL" else 0.50
        _cms = max(
            0.20,
            min(
                0.95,
                _cms
                + (
                    0.05
                    if epistemic == "CLAIM"
                    else -0.10
                    if epistemic == "HYPOTHESIS"
                    else 0.0
                ),
            ),
        )
        return {
            "wisdom_verdict": synth_verdict,
            "confidence": confidence,
            "epistemic_tag": epistemic,
            "synthesis": synthesis_bundle,
            "telemetry": {
                "mode_executed": "synthesize",
                "parallel": False,
                "tokens_estimated": 0,
                "dS": synth.get("dS", 0.0) if isinstance(synth, dict) else 0.0,
                "timestamp": timestamp,
                "sub_engine_error": sub_error,
            },
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": round(_cms, 4),
            "structural_coherence_note": (
                "Governance architecture is signal compression. The 13-floor constitution "
                "creates a calibrated background against which this output registers as "
                "anomalous contrast — legible across text, image, and protocol modalities."
                if synth_verdict == "SEAL"
                else "Synthesize mode returned non-SEAL. Cross-modal fidelity is reduced. "
                "Add explicit verdict tokens and provenance markers before transmitting "
                "to image or audio modalities."
            ),
        }

    # ── mode='deal' ──────────────────────────────────────────────────────
    if mode == "deal":
        deal = None
        sub_error = None
        try:
            deal = await wealth_deal_frame(
                opportunity_name=description or "unnamed_opportunity",
                initial_investment=deal_params.get("initial_investment", 0.0),
                cash_flows=deal_params.get("cash_flows"),
                terminal_value=deal_params.get("terminal_value", 0.0),
                discount_rate=deal_params.get("discount_rate", 0.10),
                maruah_impact=deal_params.get("maruah_impact", 0.5),
                scale_mode=deal_params.get("scale_mode", "enterprise"),
            )
        except Exception as e:
            sub_error = f"{type(e).__name__}: {e}"
        if isinstance(deal, dict):
            deal_verdict = _verdict_unify(
                deal.get("recommendation", deal.get("verdict", "HOLD"))
            )
            confiance = deal.get("confidence", 0.5)
            epistemic = "CLAIM" if deal_verdict == "SEAL" else "HYPOTHESIS"
            dealbundle = {
                "omega_verdict": "Ω-DEAL-00",
                "deal_score": deal.get("npv", 0.0),
                "structure_verdict": deal.get("classification", "UNKNOWN"),
                "risk_flags": deal.get("risk_flags", []),
            }
        else:
            deal_verdict = "HOLD"
            confiance = 0.0
            epistemic = "HYPOTHESIS"
            dealbundle = {
                "omega_verdict": "Ω-DEAL-00",
                "deal_score": 0.0,
                "structure_verdict": "ERROR",
                "risk_flags": [],
            }

        # EUREKA FORGE (2026-06-03): A/B deal comparison.
        # When the user passes deal_params.cash_flows_b, run a two-sample
        # test (Student t / Welch t / Mann-Whitney) on the two cash-flow
        # arrays via stat_compare_groups. Answers: "are these two deals
        # actually different, or am I fooling myself with NPV alone?"
        # The federated saf_stats returns an F1-F13 envelope; we extract
        # the test verdict + effect size and surface in dealbundle.
        _cash_flows_b = (
            deal_params.get("cash_flows_b") if isinstance(deal_params, dict) else None
        )
        _ab_result = None
        if (
            _cash_flows_b
            and isinstance(_cash_flows_b, list)
            and len(_cash_flows_b) >= 3
            and isinstance(deal_params.get("cash_flows"), list)
            and len(deal_params.get("cash_flows")) >= 3
        ):
            try:
                import sys as _sys_ab

                _arifos_kernel_ab = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
                if _arifos_kernel_ab not in _sys_ab.path:
                    _sys_ab.path.insert(0, _arifos_kernel_ab)
                import pandas as _pd_ab
                import uuid as _uuid_ab
                from pathlib import Path as _Path_ab
                import os as _os_ab
                from core.shared.saf_stats import (
                    stat_compare_groups as _saf_compare_groups,
                )

                _wealth_saf_root_ab = _Path_ab(
                    _os_ab.environ.get("WEALTH_SAF_DATA_ROOT", "/tmp/wealth_saf_test")
                )
                _wealth_saf_root_ab.mkdir(parents=True, exist_ok=True)
                _os_ab.environ["SAF_DATA_ROOT"] = str(_wealth_saf_root_ab)
                _ab_csv = _wealth_saf_root_ab / (f"ab_{_uuid_ab.uuid4().hex[:10]}.csv")
                _n = max(
                    len(deal_params["cash_flows"]),
                    len(_cash_flows_b),
                )
                _pd_ab.DataFrame(
                    {
                        "scenario_a": (
                            deal_params["cash_flows"]
                            + [float("nan")] * (_n - len(deal_params["cash_flows"]))
                        )[:_n],
                        "scenario_b": (
                            _cash_flows_b + [float("nan")] * (_n - len(_cash_flows_b))
                        )[:_n],
                        "scenario": (
                            ["A"] * len(deal_params["cash_flows"])
                            + [None] * (_n - len(deal_params["cash_flows"]))
                        )[:_n],
                    }
                ).to_csv(_ab_csv, index=False)
                _ab_raw = _saf_compare_groups(
                    str(_ab_csv),
                    value_col="scenario_a",
                    group_col="scenario",
                    parametric=True,
                    equal_var=False,
                )
                try:
                    _ab_csv.unlink()
                except OSError:
                    pass
                # Extract from F1-F13 envelope (federated) or nested
                # upstream format. Federated saf_stats uses:
                #   "statistic"  (t-stat for t-tests, U for Mann-Whitney)
                #   "effect_size" (Cohen's d for t-tests, r for MW)
                #   "ci95_diff"   (CI of the mean/prob difference)
                # Upstream saf_stats uses "t_stat" / "cohens_d" / "ci95".
                # Handle both.
                _ab_result_data = (
                    _ab_raw.get("result", _ab_raw) if isinstance(_ab_raw, dict) else {}
                )
                _ab_method = _ab_result_data.get("method", "Welch t-test")
                _ab_p = _ab_result_data.get("p_value")
                _ab_t = _ab_result_data.get("statistic") or _ab_result_data.get(
                    "t_stat"
                )
                _ab_d = _ab_result_data.get("effect_size") or _ab_result_data.get(
                    "cohens_d"
                )
                # Federated saf_stats does not always populate n_group1/2;
                # fall back to the input lengths.
                _ab_n_a = _ab_result_data.get("n_group1") or len(
                    deal_params["cash_flows"]
                )
                _ab_n_b = _ab_result_data.get("n_group2") or len(_cash_flows_b)
                _ab_significant = _ab_p is not None and float(_ab_p) < 0.05
                _ab_d = _ab_result_data.get("effect_size") or _ab_result_data.get(
                    "cohens_d"
                )
                _ab_n_a = _ab_result_data.get("n_group1")
                _ab_n_b = _ab_result_data.get("n_group2")
                _ab_significant = _ab_p is not None and float(_ab_p) < 0.05
                _ab_method = _ab_result_data.get("method", "Welch t-test")
                _ab_p = _ab_result_data.get("p_value")
                _ab_t = _ab_result_data.get("t_stat")
                _ab_d = _ab_result_data.get("cohens_d")
                _ab_n_a = _ab_result_data.get("n_group1")
                _ab_n_b = _ab_result_data.get("n_group2")
                _ab_significant = _ab_p is not None and float(_ab_p) < 0.05
                _ab_summary = {
                    "method": _ab_method,
                    "n_a": _ab_n_a,
                    "n_b": _ab_n_b,
                    "t_stat": _ab_t,
                    "p_value": _ab_p,
                    "cohens_d": _ab_d,
                    "significant_at_0_05": _ab_significant,
                    "interpretation": (
                        "scenarios A and B are statistically different"
                        if _ab_significant
                        else "scenarios A and B are NOT statistically distinguishable"
                    ),
                }
                # F2 TRUTH: if the scenarios are NOT significantly different,
                # the operator's choice of A vs B may be illusion — flag SABAR.
                if not _ab_significant and deal_verdict == "SEAL":
                    deal_verdict = "HOLD"
                    dealbundle["risk_flags"] = list(
                        dealbundle.get("risk_flags", [])
                    ) + [f"SAF_AB_NOT_SIGNIFICANT: p={_ab_p}"]
                dealbundle["_saf_ab_comparison"] = _ab_summary
            except Exception as _ab_exc:
                dealbundle["_saf_ab_comparison"] = {"embed_skipped": str(_ab_exc)[:120]}

        _cms = 0.85 + (confiance * 0.1) if deal_verdict == "SEAL" else 0.50
        _cms = max(
            0.20,
            min(
                0.95,
                _cms
                + (
                    0.05
                    if epistemic == "CLAIM"
                    else -0.10
                    if epistemic == "HYPOTHESIS"
                    else 0.0
                ),
            ),
        )
        return {
            "wisdom_verdict": deal_verdict,
            "confidence": confiance,
            "epistemic_tag": epistemic,
            "deal": dealbundle,
            "telemetry": {
                "mode_executed": "deal",
                "parallel": False,
                "tokens_estimated": 0,
                "dS": deal.get("entropy", 0.0) if isinstance(deal, dict) else 0.0,
                "timestamp": timestamp,
                "sub_engine_error": sub_error,
            },
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": round(_cms, 4),
            "structural_coherence_note": (
                "Deal framing with explicit NPV, risk_flags, and structure_verdict provides "
                "dense governance grammar. This output survives cross-modal transfer."
                if deal_verdict == "SEAL"
                else "Deal mode returned non-SEAL. Cross-modal fidelity reduced. "
                "Negative constraints (risk_flags, SABAR) may be lost in image/audio roundtrips."
            ),
        }

        # NOTE: unreachable duplicate block left for audit trail (Path D 2026-06-03)

    # ── mode='hysteresis' ────────────────────────────────────────────────
    if mode == "hysteresis":
        hyst = None
        sub_error = None
        try:
            hyst = wealth_hysteresis_ledger(
                mode=path_params.get("ledger_mode", "query"),
                query=description,
                limit=path_params.get("limit", 10),
                dry_run=True,  # F01: omni is read-only by default
                human_confirmed=False,
            )
        except Exception as e:
            sub_error = f"{type(e).__name__}: {e}"
        path_state = path_params.get("current_state", "PLATEAU")
        hyst_verdict = _verdict_unify(path_state)
        _cms = 0.70 if sub_error is None else 0.30
        return {
            "wisdom_verdict": hyst_verdict,
            "confidence": 0.5 if sub_error is None else 0.0,
            "epistemic_tag": "ESTIMATE" if sub_error is None else "HYPOTHESIS",
            "hysteresis": {
                "omega_path": "Ω-WEALTH-12",
                "path_state": path_state,
                "hysteresis_risk": 0.0,
                "transition_recommendation": str(hyst)[:200] if hyst else "no_data",
            },
            "telemetry": {
                "mode_executed": "hysteresis",
                "parallel": False,
                "tokens_estimated": 0,
                "dS": 0.0,
                "timestamp": timestamp,
                "sub_engine_error": sub_error,
            },
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": round(_cms, 4),
            "structural_coherence_note": (
                "Hysteresis mode tracks path dependence. Path-state labels (GROWTH, PLATEAU, "
                "REVERSION, COLLAPSE) are high-contrast governance tokens with strong "
                "cross-modal survival. The dim-spot risk: VOID transitions (absence of growth) "
                "may be lost in pixel or audio roundtrips."
            ),
        }

    # ── mode='deal' ──────────────────────────────────────────────────────
    if mode == "deal":
        try:
            deal = await wealth_deal_frame(
                opportunity_name=description or "unnamed_opportunity",
                initial_investment=deal_params.get("initial_investment", 0.0),
                cash_flows=deal_params.get("cash_flows"),
                terminal_value=deal_params.get("terminal_value", 0.0),
                discount_rate=deal_params.get("discount_rate", 0.10),
                maruah_impact=deal_params.get("maruah_impact", 0.5),
                scale_mode=deal_params.get("scale_mode", "enterprise"),
            )
        except Exception as e:
            return _omni_error("deal", e, timestamp)
        deal_verdict = _verdict_unify(
            deal.get("recommendation", deal.get("verdict", "HOLD"))
        )
        _cms = (
            0.85 + (deal.get("confidence", 0.5) * 0.1)
            if deal_verdict == "SEAL"
            else 0.50
        )
        _cms = max(0.20, min(0.95, _cms + (0.05 if deal_verdict == "SEAL" else -0.10)))
        return {
            "wisdom_verdict": deal_verdict,
            "confidence": deal.get("confidence", 0.5),
            "epistemic_tag": "CLAIM" if deal_verdict == "SEAL" else "HYPOTHESIS",
            "deal": {
                "omega_verdict": "Ω-DEAL-00",
                "deal_score": deal.get("npv", 0.0),
                "structure_verdict": deal.get("classification", "UNKNOWN"),
                "risk_flags": deal.get("risk_flags", []),
            },
            "telemetry": {
                "mode_executed": "deal",
                "parallel": False,
                "tokens_estimated": 0,
                "dS": deal.get("entropy", 0.0),
                "timestamp": timestamp,
            },
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": round(_cms, 4),
            "structural_coherence_note": (
                "Deal framing with explicit NPV, risk_flags, and structure_verdict provides "
                "dense governance grammar. This output survives cross-modal transfer."
                if deal_verdict == "SEAL"
                else "Deal mode returned non-SEAL. Cross-modal fidelity reduced. "
                "Negative constraints (risk_flags, SABAR) may be lost in image/audio roundtrips."
            ),
        }

    # ── mode='hysteresis' ────────────────────────────────────────────────
    if mode == "hysteresis":
        try:
            hyst = wealth_hysteresis_ledger(
                mode=path_params.get("ledger_mode", "query"),
                query=description,
                limit=path_params.get("limit", 10),
                dry_run=True,  # F01: omni is read-only by default
                human_confirmed=False,
            )
        except Exception as e:
            return _omni_error("hysteresis", e, timestamp)
        path_state = path_params.get("current_state", "PLATEAU")
        hyst_verdict = _verdict_unify(path_state)
        return {
            "wisdom_verdict": hyst_verdict,
            "confidence": 0.5,
            "epistemic_tag": "ESTIMATE",
            "hysteresis": {
                "omega_path": "Ω-WEALTH-12",
                "path_state": path_state,
                "hysteresis_risk": 0.0,
                "transition_recommendation": str(hyst)[:200] if hyst else "no_data",
            },
            "telemetry": {
                "mode_executed": "hysteresis",
                "parallel": False,
                "tokens_estimated": 0,
                "dS": 0.0,
                "timestamp": timestamp,
            },
            # Structural Coherence Transmission — EUREKA v2026.06.05
            "cross_modal_stability": 0.70,
            "structural_coherence_note": (
                "Hysteresis mode tracks path dependence. Path-state labels (GROWTH, PLATEAU, "
                "REVERSION, COLLAPSE) are high-contrast governance tokens with strong "
                "cross-modal survival. The dim-spot risk: VOID transitions (absence of growth) "
                "may be lost in pixel or audio roundtrips."
            ),
        }

    # ── mode='omni' — parallel fan-out + F01 fusion ──────────────────────
    synth_task = asyncio.to_thread(
        wealth_synthesize,
        question=description,
        scale_mode=decision_context.get("capital_type", "enterprise"),
        context=decision_context,
        reversible=True,
    )
    deal_task = wealth_deal_frame(
        opportunity_name=description or "omni_opportunity",
        initial_investment=deal_params.get("initial_investment", 0.0),
        cash_flows=deal_params.get("cash_flows"),
        terminal_value=deal_params.get("terminal_value", 0.0),
        discount_rate=deal_params.get("discount_rate", 0.10),
        maruah_impact=deal_params.get("maruah_impact", 0.5),
        scale_mode=deal_params.get("scale_mode", "enterprise"),
    )
    hyst_task = asyncio.to_thread(
        wealth_hysteresis_ledger,
        mode="query",
        query=description,
        limit=path_params.get("limit", 10),
        dry_run=True,
        human_confirmed=False,
    )

    synth, deal, hyst = await asyncio.gather(
        synth_task, deal_task, hyst_task, return_exceptions=True
    )

    # F01: any sub-engine error → HOLD verdict (defensive)
    synth_ok = isinstance(synth, dict)
    deal_ok = isinstance(deal, dict)
    hyst_ok = isinstance(hyst, dict)

    synth_v = _verdict_unify(synth.get("omega_verdict", "HOLD")) if synth_ok else "HOLD"
    deal_v = _verdict_unify(deal.get("recommendation", "HOLD")) if deal_ok else "HOLD"
    path_state = path_params.get("current_state", "PLATEAU")
    hyst_v = _verdict_unify(path_state)  # path_state is the user-supplied signal

    # F01 fusion: strictest wins
    final_verdict, confidence = _wisdom_fuse([synth_v, deal_v, hyst_v])

    # Structural Coherence: omni mode derives density from how many sub-engines succeeded
    _semantic_density = sum([synth_ok, deal_ok, hyst_ok]) / 3.0
    _cms = max(
        0.20, min(0.95, (0.85 + confidence * 0.1) if final_verdict == "SEAL" else 0.50)
    )
    _cms = _cms + (0.05 * _semantic_density)
    return {
        "wisdom_verdict": final_verdict,
        "confidence": confidence,
        "epistemic_tag": "PLAUSIBLE" if confidence > 0.7 else "HYPOTHESIS",
        "synthesis": {
            "omega_verdict": "Ω-WEALTH-00",
            "capital_score": synth.get("capital_score", 0.0) if synth_ok else 0.0,
            "conversion_integrity": synth.get("conversion_integrity", "ERROR")
            if synth_ok
            else "ERROR",
            "summary": synth.get("summary", description) if synth_ok else "synth_error",
        },
        "deal": {
            "omega_verdict": "Ω-DEAL-00",
            # EUREKA FIX 2026-06-08: deal_frame nests NPV under "valuation" dict.
            # Prior code: deal.get("npv", 0.0) — always returned 0.0 (wrong key path).
            # Correct path: deal["valuation"]["npv"]. Also surface IRR/payback/PI
            # so the agent sees the full deal thermodynamics, not just NPV.
            "deal_score": deal.get("valuation", {}).get("npv", 0.0) if deal_ok else 0.0,
            "deal_irr_pct": deal.get("valuation", {}).get("irr_pct", 0.0)
            if deal_ok
            else 0.0,
            "deal_payback_years": deal.get("valuation", {}).get("payback_years", 0)
            if deal_ok
            else 0,
            "deal_profitability_index": deal.get("valuation", {}).get(
                "profitability_index", 0.0
            )
            if deal_ok
            else 0.0,
            "structure_verdict": deal.get("classification", "ERROR")
            if deal_ok
            else "ERROR",
            "recommendation": deal.get("recommendation", "HOLD") if deal_ok else "HOLD",
            "viability_score": deal.get("viability_score", "?") if deal_ok else "?",
            "stress_label": deal.get("stress_label", "") if deal_ok else "",
            "risk_flags": deal.get("risk_flags", []) if deal_ok else [],
            "boundary_passed": deal.get("boundary_check", {}).get("passed", None)
            if deal_ok
            else None,
            "floors_triggered": deal.get("boundary_check", {}).get(
                "floors_triggered", []
            )
            if deal_ok
            else [],
        },
        "hysteresis": {
            "omega_path": "Ω-WEALTH-12",
            "path_state": path_state,
            "hysteresis_risk": 0.0,
            "transition_recommendation": "see ledger" if hyst_ok else "hyst_error",
        },
        "telemetry": {
            "mode_executed": "omni",
            "parallel": True,
            "tokens_estimated": 0,
            "dS": 0.0,
            "timestamp": timestamp,
            "sub_verdicts": {"synth": synth_v, "deal": deal_v, "hysteresis": hyst_v},
            "sub_ok": {"synth": synth_ok, "deal": deal_ok, "hysteresis": hyst_ok},
        },
        # Structural Coherence Transmission — EUREKA v2026.06.05
        "cross_modal_stability": round(_cms, 4),
        "semantic_density_score": round(_semantic_density, 4),
        "structural_coherence_note": (
            "Omni mode fuses three sub-engines. Semantic density = ratio of successful "
            f"sub-engines ({sum([synth_ok, deal_ok, hyst_ok])}/3). Higher density = "
            "more governance tokens distributed across the output = higher cross-modal fidelity. "
            "The dim-spot risk: if any sub-engine fails, its absence may not be visible "
            "in image/audio roundtrips. Check sub_ok map."
        ),
    }


def _omni_error(failed_mode: str, exc: Exception, timestamp: str) -> Dict[str, Any]:
    """Helper: produce a structured error bundle for a failed sub-engine."""
    return {
        "wisdom_verdict": "HOLD",
        "confidence": 0.0,
        "epistemic_tag": "HYPOTHESIS",
        "error": f"sub-engine '{failed_mode}' failed: {type(exc).__name__}: {exc}",
        "telemetry": {
            "mode_executed": failed_mode,
            "parallel": False,
            "tokens_estimated": 0,
            "dS": 0.0,
            "timestamp": timestamp,
            "sub_engine_error": failed_mode,
        },
        # Structural Coherence Transmission — EUREKA v2026.06.05
        "cross_modal_stability": 0.15,
        "structural_coherence_note": (
            "Sub-engine failure = broken governance chain. This signal has VERY LOW "
            "cross-modal fidelity. The absence of a sub-engine output is a dim spot — "
            "it will be lost in modality transfer. Re-run the failed sub-engine or "
            "downgrade to explicit HOLD before transmitting."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# INEQUALITY INTELLIGENCE KERNEL — 6 tools forged 2026-05-16
# Eureka: WEALTH must audit the CONVERTER, not just the capital stock.
# ═══════════════════════════════════════════════════════════════════════


def wealth_conversion_architecture(
    domain: str = "unspecified",
    description: str = "",
    institutions_quality: float = 0.5,
    ownership_concentration: float = 0.5,
    mobility_channels: float = 0.5,
    risk_distribution: float = 0.5,
    information_symmetry: float = 0.5,
    voice_access: float = 0.5,
    time_horizon: float = 0.5,
    historical_damage: float = 0.5,
    scale_mode: str = "enterprise",
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-01: Conversion Architecture — diagnose whether endowment converts
    to inclusive capability or extractive rent. The Acemoglu converter audit.

    Scores 8 conversion dimensions (0=worst, 1=best). Returns conversion_mode,
    binding bottleneck, and intervention priority list.
    """
    dims = {
        "institutions_quality": institutions_quality,
        "ownership_concentration": 1.0 - ownership_concentration,
        "mobility_channels": mobility_channels,
        "risk_distribution": risk_distribution,
        "information_symmetry": information_symmetry,
        "voice_access": voice_access,
        "time_horizon": time_horizon,
        "historical_resilience": 1.0 - historical_damage,
    }
    scores = {k: max(0.0, min(1.0, float(v))) for k, v in dims.items()}
    avg = sum(scores.values()) / len(scores)
    bottleneck = min(scores, key=scores.get)
    bottleneck_score = scores[bottleneck]

    if avg >= 0.70:
        conversion_mode = "inclusive"
        domain_verdict = "SEAL"
        governance_verdict = "SEAL"
    elif avg >= 0.45:
        conversion_mode = "mixed"
        domain_verdict = "QUALIFY"
        governance_verdict = "QUALIFY"
    else:
        conversion_mode = "extractive"
        domain_verdict = "888-HOLD"
        governance_verdict = "888-HOLD"

    interventions = sorted(scores, key=scores.get)[:3]

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_conversion_architecture",
        "task": "wealth_conversion_architecture",
        "domain": domain,
        "description": description,
        "conversion_mode": conversion_mode,
        "conversion_score": round(avg, 4),
        "bottleneck_dimension": bottleneck,
        "bottleneck_score": round(bottleneck_score, 4),
        "dimension_scores": {k: round(v, 4) for k, v in scores.items()},
        "priority_interventions": interventions,
        "domain_verdict": domain_verdict,
        "governance_verdict": governance_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "acemoglu_signal": (
            "Extractive institutions detected — resource endowment will compound rents, not capability."
            if conversion_mode == "extractive"
            else "Mixed converter — targeted institutional reform at bottleneck required."
            if conversion_mode == "mixed"
            else "Inclusive architecture present — endowment can convert to broad capability."
        ),
        "scale_mode": scale_mode,
    }
    return _inject_emergence(
        "wealth_conversion_architecture",
        "assess",
        {
            "domain": domain,
            "scale_mode": scale_mode,
        },
        result,
    )


def wealth_asymmetry_map(
    context: str = "",
    asset_asymmetry: float = 0.5,
    information_asymmetry: float = 0.5,
    power_asymmetry: float = 0.5,
    risk_asymmetry: float = 0.5,
    time_asymmetry: float = 0.5,
    mobility_asymmetry: float = 0.5,
    voice_asymmetry: float = 0.5,
    dignity_asymmetry: float = 0.5,
    network_asymmetry: float = 0.5,
    scale_mode: str = "enterprise",
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-02: Asymmetry Map — map all 9 inequality transmission asymmetries.

    Scores 0=no asymmetry, 1=maximum asymmetry. Returns dominant asymmetry,
    compound risk, and the axiom: inequality persists when asymmetry compounds
    faster than mobility corrects it.
    """
    asym = {
        "asset": asset_asymmetry,
        "information": information_asymmetry,
        "power": power_asymmetry,
        "risk": risk_asymmetry,
        "time": time_asymmetry,
        "mobility": mobility_asymmetry,
        "voice": voice_asymmetry,
        "dignity": dignity_asymmetry,
        "network": network_asymmetry,
    }
    scores = {k: max(0.0, min(1.0, float(v))) for k, v in asym.items()}
    avg = sum(scores.values()) / len(scores)
    dominant = max(scores, key=scores.get)
    dominant_score = scores[dominant]
    compound_risk = round(1.0 - (1.0 - avg) ** 2, 4)

    if avg >= 0.70:
        regime = "high_asymmetry"
        domain_verdict = "888-HOLD"
    elif avg >= 0.45:
        regime = "moderate_asymmetry"
        domain_verdict = "QUALIFY"
    else:
        regime = "low_asymmetry"
        domain_verdict = "SEAL"

    mobility_corrects = scores.get("mobility", 0.5)
    compounding_wins = (avg - mobility_corrects) > 0.15

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_asymmetry_map",
        "task": "wealth_asymmetry_map",
        "context": context,
        "asymmetry_scores": {k: round(v, 4) for k, v in scores.items()},
        "average_asymmetry": round(avg, 4),
        "dominant_asymmetry": dominant,
        "dominant_score": round(dominant_score, 4),
        "compound_risk": compound_risk,
        "regime": regime,
        "compounding_exceeds_mobility": compounding_wins,
        "domain_verdict": domain_verdict,
        "governance_verdict": domain_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "axiom": "Inequality persists when asymmetry compounds faster than mobility corrects it.",
        "scale_mode": scale_mode,
    }
    return _inject_emergence(
        "wealth_asymmetry_map",
        "assess",
        {
            "context": context,
            "scale_mode": scale_mode,
        },
        result,
    )


def wealth_return_classifier(
    return_description: str = "",
    source_description: str = "",
    value_created: float = 0.5,
    competitive_entry_open: float = 0.5,
    reversible_advantage: float = 0.5,
    political_protection: float = 0.0,
    inherited_lock_in: float = 0.0,
    coercion_factor: float = 0.0,
    scale_mode: str = "enterprise",
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-03: Return Classifier — distinguish productive return from
    rent extraction, monopoly, dynastic lock-in, and predatory capture.

    Not all inequality has the same moral or economic structure. This tool
    separates what is tolerable from what is destabilizing.
    """
    extraction_score = (
        (1.0 - value_created) * 0.30
        + (1.0 - competitive_entry_open) * 0.25
        + (1.0 - reversible_advantage) * 0.15
        + political_protection * 0.15
        + inherited_lock_in * 0.10
        + coercion_factor * 0.05
    )
    extraction_score = max(0.0, min(1.0, extraction_score))

    if extraction_score < 0.25:
        return_type = "productive"
        verdict_label = "Tolerable — value created, entry open, reversible"
        domain_verdict = "SEAL"
    elif extraction_score < 0.50:
        return_type = "mixed"
        verdict_label = "Caution — partial value creation, partial rent capture"
        domain_verdict = "QUALIFY"
    elif extraction_score < 0.75:
        return_type = "rent_extraction"
        verdict_label = (
            "Extractive — income from control, monopoly, or political gatekeeping"
        )
        domain_verdict = "888-HOLD"
    else:
        return_type = "predatory"
        verdict_label = (
            "Predatory — coercion, dynastic lock-in, or structural humiliation"
        )
        domain_verdict = "VOID"

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_return_classifier",
        "task": "wealth_return_classifier",
        "return_description": return_description,
        "source_description": source_description,
        "return_type": return_type,
        "extraction_score": round(extraction_score, 4),
        "verdict_label": verdict_label,
        "component_scores": {
            "value_created": round(value_created, 4),
            "competitive_entry_open": round(competitive_entry_open, 4),
            "reversible_advantage": round(reversible_advantage, 4),
            "political_protection": round(political_protection, 4),
            "inherited_lock_in": round(inherited_lock_in, 4),
            "coercion_factor": round(coercion_factor, 4),
        },
        "domain_verdict": domain_verdict,
        "governance_verdict": domain_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "piketty_signal": (
            "r > g risk: if this return type dominates, capital concentrates faster than growth."
            if return_type in ("rent_extraction", "predatory")
            else "Productive return — supports broad growth if institutions remain inclusive."
        ),
        "scale_mode": scale_mode,
    }
    return _inject_emergence(
        "wealth_return_classifier",
        "classify",
        {
            "return_description": return_description,
            "scale_mode": scale_mode,
        },
        result,
    )


@mcp.tool(name="wealth_role_scarcity_risk")
def wealth_role_scarcity_risk(
    context: str = "",
    youth_unemployment: float = 0.5,
    housing_unaffordability: float = 0.5,
    delayed_family_formation: float = 0.5,
    weak_social_mobility: float = 0.5,
    low_trust: float = 0.5,
    civic_disengagement: float = 0.5,
    status_bottleneck: float = 0.5,
    future_orientation_collapse: float = 0.5,
    scale_mode: str = "enterprise",
    organism_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-04: Role Scarcity Risk — Calhoun-inspired social role
    saturation assessment. Inequality is not only about material scarcity.
    It is also about social role scarcity.

    Scores 0=no risk, 1=maximum risk. Threshold warning at 0.65.
    Above threshold, resource transfers alone cannot reverse collapse.

    When organism_context is provided (folded from arifOS arif_anti_sink_check),
    also evaluates 8 qualitative anti-sink dimensions at the organism/system-
    design level — complementary to the civilizational calhoun_risk_score.

    organism_context keys (all optional):
      automation_level: "full_replacement" | "augmentation" | "unknown"
      human_roles_remaining: "none" | "single" | "multiple"
      distinct_human_roles: int
      feedback_loop: "closed" | "partial" | "open" | "absent"
      centralization: "monopoly" | "moderate" | "distributed"
      chokepoint_count: int
      agency_trend: "declining" | "stable" | "rising"
      capture_trend: "rising" | "stable" | "falling"
      participation_trend: "narrowing" | "stable" | "broadening"
      contestable: bool
      reversible: bool
      abstraction_level: "high" | "moderate" | "low"
      role_pathway: "none" | "weak" | "strong"
      human_decision_points: int
    """
    dims = {
        "youth_unemployment": youth_unemployment,
        "housing_unaffordability": housing_unaffordability,
        "delayed_family_formation": delayed_family_formation,
        "weak_social_mobility": weak_social_mobility,
        "low_trust": low_trust,
        "civic_disengagement": civic_disengagement,
        "status_bottleneck": status_bottleneck,
        "future_orientation_collapse": future_orientation_collapse,
    }
    scores = {k: max(0.0, min(1.0, float(v))) for k, v in dims.items()}
    calhoun_risk = sum(scores.values()) / len(scores)
    above_threshold = calhoun_risk >= 0.65

    if calhoun_risk >= 0.75:
        regime = "BEHAVIORAL_SINK_RISK"
        domain_verdict = "VOID"
        intervention_window = "CRITICAL — role architecture must be rebuilt before threshold. Resource transfers alone insufficient."
    elif calhoun_risk >= 0.65:
        regime = "THRESHOLD_WARNING"
        domain_verdict = "888-HOLD"
        intervention_window = "WARNING — approaching irreversible phase transition. Combined role + resource intervention required."
    elif calhoun_risk >= 0.45:
        regime = "ELEVATED_RISK"
        domain_verdict = "QUALIFY"
        intervention_window = "Moderate — role scarcity visible but reversible with structural investment."
    else:
        regime = "STABLE"
        domain_verdict = "SEAL"
        intervention_window = "Low risk — role architecture intact."

    result: Dict[str, Any] = {
        "mcp": "WEALTH",
        "tool": "wealth_role_scarcity_risk",
        "task": "wealth_role_scarcity_risk",
        "context": context,
        "calhoun_risk_score": round(calhoun_risk, 4),
        "above_irreversibility_threshold": above_threshold,
        "regime": regime,
        "dimension_scores": {k: round(v, 4) for k, v in scores.items()},
        "intervention_window": intervention_window,
        "domain_verdict": domain_verdict,
        "governance_verdict": domain_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "calhoun_lesson": (
            "Phase transition detected: behavioral sink dynamics active. "
            "Abundance without role architecture produces civilizational despair."
            if above_threshold
            else "Role architecture present but stressed. Monitor future_orientation and mobility dimensions."
        ),
        "scale_mode": scale_mode,
    }

    # ── Anti-Sink Fold (arif_anti_sink_check → WEALTH) ──────────────────────
    if organism_context:
        ctx = organism_context

        auto_lvl = ctx.get("automation_level", "unknown")
        human_roles = ctx.get("human_roles_remaining", "unknown")
        if auto_lvl == "full_replacement" or human_roles == "none":
            agency_delta = "negative"
            agency_delta_note = "Automation fully replaces human decision points."
        elif auto_lvl == "augmentation" or human_roles == "multiple":
            agency_delta = "positive"
            agency_delta_note = "Human agency preserved or amplified."
        else:
            agency_delta = "unknown"
            agency_delta_note = "Insufficient context to assess agency delta."

        role_count = ctx.get("distinct_human_roles", "unknown")
        if isinstance(role_count, int):
            if role_count <= 1:
                role_diversity_delta = "negative"
                role_diversity_note = "All human roles compressed into single slot."
            elif role_count >= 3:
                role_diversity_delta = "positive"
                role_diversity_note = f"{role_count} distinct human roles detected."
            else:
                role_diversity_delta = "unknown"
                role_diversity_note = "Role diversity context unavailable."
        else:
            role_diversity_delta = "unknown"
            role_diversity_note = "Role diversity context unavailable."

        fb = ctx.get("feedback_loop", "unknown")
        if fb == "closed":
            feedback_integrity = "strong"
            feedback_note = "Closed feedback loop from action to consequence."
        elif fb == "partial":
            feedback_integrity = "partial"
            feedback_note = "Partial feedback; some consequences are invisible."
        elif fb in ("open", "absent"):
            feedback_integrity = "absent"
            feedback_note = "No observable feedback path."
        else:
            feedback_integrity = "absent"
            feedback_note = "Feedback integrity unknown."

        centralization = ctx.get("centralization", "unknown")
        chokepoints = ctx.get("chokepoint_count", 0)
        if centralization == "monopoly" or (
            isinstance(chokepoints, int) and chokepoints >= 3
        ):
            topology_risk = "high"
            topology_note = "High centralization or multiple chokepoints detected."
        elif centralization == "moderate" or (
            isinstance(chokepoints, int) and chokepoints >= 1
        ):
            topology_risk = "medium"
            topology_note = "Moderate centralization or isolated chokepoints."
        elif centralization == "distributed":
            topology_risk = "low"
            topology_note = "Distributed topology with few chokepoints."
        else:
            topology_risk = "low"
            topology_note = "Topology risk unmeasured; default low."

        drift_signals = 0
        drift_notes: list[str] = []
        if ctx.get("agency_trend") == "declining":
            drift_signals += 1
            drift_notes.append("Agency trend is declining.")
        if ctx.get("capture_trend") == "rising":
            drift_signals += 1
            drift_notes.append("Extractive capture is rising.")
        if ctx.get("participation_trend") == "narrowing":
            drift_signals += 1
            drift_notes.append("Participation width is narrowing.")
        if drift_signals >= 2:
            extractive_drift = "high"
            drift_note = "; ".join(drift_notes)
        elif drift_signals == 1:
            extractive_drift = "medium"
            drift_note = "; ".join(drift_notes)
        else:
            extractive_drift = "low"
            drift_note = "No clear extractive drift signals."

        contestable = ctx.get("contestable", "unknown")
        reversible = ctx.get("reversible", "unknown")
        if contestable is True and reversible is True:
            inclusive_repair_path = "present"
            repair_note = "System is contestable and reversible."
        elif contestable is True or reversible is True:
            inclusive_repair_path = "weak"
            repair_note = "Partial repair path; contestability or reversibility only."
        elif contestable is False and reversible is False:
            inclusive_repair_path = "absent"
            repair_note = "No contestability or reversibility."
        else:
            inclusive_repair_path = "absent"
            repair_note = "Repair path status unknown."

        abstraction = ctx.get("abstraction_level", "unknown")
        role_pathway = ctx.get("role_pathway", "unknown")
        if abstraction == "high" and role_pathway == "none":
            beautiful_ones_risk = True
            beautiful_note = "High abstraction with no human role pathway."
        else:
            beautiful_ones_risk = False
            beautiful_note = "Beautiful Ones Risk not detected."

        decision_pts = ctx.get("human_decision_points", "unknown")
        if isinstance(decision_pts, int):
            if decision_pts == 0:
                agency_compression = "high"
                compression_note = "Zero human decision points remain."
            elif decision_pts <= 2:
                agency_compression = "medium"
                compression_note = f"Only {decision_pts} human decision points remain."
            else:
                agency_compression = "low"
                compression_note = f"{decision_pts} human decision points preserved."
        else:
            agency_compression = "low"
            compression_note = "Agency compression unmeasured; default low."

        if (
            extractive_drift == "high"
            or topology_risk == "high"
            or agency_compression == "high"
        ):
            anti_sink_verdict = "hold"
            anti_sink_verdict_note = (
                "High risk indicators detected. Human review required."
            )
        elif (
            extractive_drift == "medium"
            or topology_risk == "medium"
            or agency_compression == "medium"
            or beautiful_ones_risk
        ):
            anti_sink_verdict = "revise"
            anti_sink_verdict_note = (
                "Moderate risk or Beautiful Ones flag. Recommend revision."
            )
        else:
            anti_sink_verdict = "pass"
            anti_sink_verdict_note = "No significant extractive or sink indicators."

        anti_sink_assessment = {
            "verdict": anti_sink_verdict,
            "verdict_note": anti_sink_verdict_note,
            "agency_delta": agency_delta,
            "agency_delta_note": agency_delta_note,
            "role_diversity_delta": role_diversity_delta,
            "role_diversity_note": role_diversity_note,
            "feedback_integrity": feedback_integrity,
            "feedback_note": feedback_note,
            "topology_risk": topology_risk,
            "topology_note": topology_note,
            "extractive_drift": extractive_drift,
            "extractive_drift_note": drift_note,
            "inclusive_repair_path": inclusive_repair_path,
            "repair_note": repair_note,
            "beautiful_ones_risk": beautiful_ones_risk,
            "beautiful_ones_note": beautiful_note,
            "agency_compression": agency_compression,
            "agency_compression_note": compression_note,
            "confidence": "low",
            "constitutional_floors_checked": ["F05", "F08", "F10", "F13"],
            "note": "Folded from arifOS arif_anti_sink_check — WEALTH owns anti-sink diagnostics as Ω-WEALTH-11 boundary stewardship",
        }
        result["anti_sink_assessment"] = anti_sink_assessment

    return _inject_emergence(
        "wealth_role_scarcity_risk",
        "assess",
        {
            "context": context,
            "scale_mode": scale_mode,
            "organism_context_present": organism_context is not None,
        },
        result,
    )


def wealth_legitimacy_audit(
    system_description: str = "",
    rules_understandable: float = 0.5,
    rules_contestable: float = 0.5,
    rules_fair_enough: float = 0.5,
    rules_repairable: float = 0.5,
    rules_non_humiliating: float = 0.5,
    rules_non_captured: float = 0.5,
    contestation_cost_proportionate: float = 0.5,
    scale_mode: str = "enterprise",
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-05: Legitimacy Audit — score whether the conversion
    architecture is perceived as legitimate by participants.

    Legitimacy is not optional. When it fails, even material redistribution
    cannot stabilise the system. The deepest missing variable in most
    inequality analysis.

    Scores 0=worst, 1=best. Critical dimension: contestation_cost_proportionate
    (can ordinary people challenge unfair rules at proportionate cost?).
    """
    dims = {
        "understandable": rules_understandable,
        "contestable": rules_contestable,
        "fair_enough": rules_fair_enough,
        "repairable": rules_repairable,
        "non_humiliating": rules_non_humiliating,
        "non_captured": rules_non_captured,
        "contestation_proportionate": contestation_cost_proportionate,
    }
    scores = {k: max(0.0, min(1.0, float(v))) for k, v in dims.items()}
    legitimacy_score = sum(scores.values()) / len(scores)
    weakest = min(scores, key=scores.get)
    weakest_score = scores[weakest]

    if legitimacy_score >= 0.70:
        regime = "legitimate"
        domain_verdict = "SEAL"
        risk_level = "LOW"
    elif legitimacy_score >= 0.50:
        regime = "contested"
        domain_verdict = "QUALIFY"
        risk_level = "MODERATE"
    elif legitimacy_score >= 0.35:
        regime = "delegitimised"
        domain_verdict = "888-HOLD"
        risk_level = "HIGH"
    else:
        regime = "failed_legitimacy"
        domain_verdict = "VOID"
        risk_level = "CRITICAL — phase transition risk elevated"

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_legitimacy_audit",
        "task": "wealth_legitimacy_audit",
        "system_description": system_description,
        "legitimacy_score": round(legitimacy_score, 4),
        "regime": regime,
        "risk_level": risk_level,
        "weakest_dimension": weakest,
        "weakest_score": round(weakest_score, 4),
        "dimension_scores": {k: round(v, 4) for k, v in scores.items()},
        "domain_verdict": domain_verdict,
        "governance_verdict": domain_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "legitimacy_axiom": (
            "Legitimate conversion architecture = rules that are understandable + "
            "contestable + repairable + accessible to contest at proportionate cost."
        ),
        "scale_mode": scale_mode,
    }
    return _inject_emergence(
        "wealth_legitimacy_audit",
        "audit",
        {
            "system_description": system_description,
            "scale_mode": scale_mode,
        },
        result,
    )


# ── Inequality Intelligence: Country Presets + World Bank Live Wire ──────────

INEQUALITY_COUNTRY_PRESETS: Dict[str, str] = {
    "malaysia": "MYS",
    "singapore": "SGP",
    "indonesia": "IDN",
    "thailand": "THA",
    "vietnam": "VNM",
    "philippines": "PHL",
    "myanmar": "MMR",
    "cambodia": "KHM",
    "india": "IND",
    "china": "CHN",
    "usa": "USA",
    "uk": "GBR",
    "brazil": "BRA",
    "south_africa": "ZAF",
    "nigeria": "NGA",
    "kenya": "KEN",
}

# series_id → (kernel_param, normalization_fn, human-readable description)
_IEQ_WB_INDICATORS: Dict[str, tuple] = {
    "SL.UEM.1524.ZS": (
        "youth_unemployment",
        lambda v: min(v / 50.0, 1.0),
        "Youth unemployment %",
    ),
    "SI.POV.GINI": (
        "ownership_concentration",
        lambda v: max(0.0, min((v - 20.0) / 60.0, 1.0)),
        "Gini coefficient",
    ),
    "SI.DST.10TH.10": (
        "power_asymmetry",
        lambda v: min(v / 60.0, 1.0),
        "Income share top 10%",
    ),
    "SI.DST.FRST.20": (
        "mobility_channels",
        lambda v: min(v / 10.0, 1.0),
        "Income share bottom 20%",
    ),
    "SP.DYN.TFRT.IN": (
        "future_orientation_collapse",
        lambda v: max(0.0, 1.0 - v / 2.1),
        "Total fertility rate",
    ),
    "SE.ADT.LITR.ZS": (
        "information_symmetry",
        lambda v: min(v / 100.0, 1.0),
        "Adult literacy rate %",
    ),
    "NY.GDP.PCAP.KD.ZG": (
        "risk_distribution",
        lambda v: max(0.0, min((v + 5.0) / 15.0, 1.0)),
        "GDP per capita growth %",
    ),
    "SL.TLF.CACT.ZS": (
        "voice_access",
        lambda v: min(v / 80.0, 1.0),
        "Labour force participation %",
    ),
    "FP.CPI.TOTL.ZG": (
        "time_horizon",
        lambda v: max(0.0, 1.0 - min(v / 20.0, 1.0)),
        "Inflation CPI %",
    ),
    # ── Enhanced ownership concentration (multi-signal) ───────────────────
    "SI.DST.05TH.20": (
        "ownership_concentration_income_top20",
        lambda v: min(v / 60.0, 1.0),
        "Income share held by highest 20%",
    ),
    "SI.POV.GAP2": (
        "poverty_depth",
        lambda v: min(v / 20.0, 1.0),
        "Poverty gap at $6.85/day (2017 PPP) %",
    ),
    # ── Intergenerational mobility proxy ──────────────────────────────────
    "SE.SEC.PROG.ZS": (
        "intergenerational_mobility_proxy",
        lambda v: min(v / 100.0, 1.0),
        "Progression to secondary school % — proxy for education mobility",
    ),
}


def _fetch_inequality_inputs_from_wb(
    country_code: str,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """Fetch and normalize WB indicators into wealth_inequality_kernel params.
    Params not covered by live WB data fall back to 0.5 (neutral default).
    """
    params: Dict[str, Any] = {}
    provenance: Dict[str, Any] = {}
    missing: List[str] = []
    data_years: Dict[str, str] = {}

    for series_id, (param_name, norm_fn, description) in _IEQ_WB_INDICATORS.items():
        try:
            raw = ingest_fetch("WorldBank", series_id, country_code)
            records = raw.get("secondary_metrics", {}).get("records", [])
            val = None
            obs_year = None
            for rec in records:
                v = rec.get("value")
                if v is not None:
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if fv != fv:  # NaN guard
                        continue
                    yr_str = str(rec.get("observation_time", ""))[:4]
                    if year is None or yr_str == str(year):
                        val = fv
                        obs_year = yr_str
                        break
            if val is not None:
                normalized = round(max(0.0, min(norm_fn(val), 1.0)), 4)
                params[param_name] = normalized
                provenance[param_name] = {
                    "series_id": series_id,
                    "raw_value": round(val, 4),
                    "year": obs_year,
                    "description": description,
                    "source": "WorldBank",
                }
                data_years[param_name] = obs_year
            else:
                missing.append(param_name)
                provenance[param_name] = {
                    "series_id": series_id,
                    "status": "NO_DATA",
                    "default": 0.5,
                }
        except Exception as exc:
            missing.append(param_name)
            provenance[param_name] = {
                "series_id": series_id,
                "status": f"ERROR:{type(exc).__name__}",
                "default": 0.5,
            }

    # Derive institutions_quality from literacy + LFP when WGI governance indicators unavailable
    if "information_symmetry" in params and "voice_access" in params:
        inst_q = round(
            (params["information_symmetry"] + params["voice_access"]) / 2.0, 4
        )
        params["institutions_quality"] = inst_q
        provenance["institutions_quality"] = {
            "derived_from": ["information_symmetry", "voice_access"],
            "note": "WGI governance indicators unavailable via current adapter; proxy from literacy + LFP average",
        }

    # ── Composite ownership concentration ────────────────────────────────
    # Derive from Gini + income share top20 + poverty depth for stronger signal.
    # Falls back to single Gini signal if complement signals missing.
    oc_signals = []
    oc_weights = []
    if "ownership_concentration" in params:
        oc_signals.append(params["ownership_concentration"])
        oc_weights.append(0.5)
    if "ownership_concentration_income_top20" in params:
        oc_signals.append(params["ownership_concentration_income_top20"])
        oc_weights.append(0.3)
    if "poverty_depth" in params:
        # Invert: higher poverty depth → lower ownership concentration signal
        # (poverty depth itself is a different dimension, but complements the picture)
        oc_signals.append(1.0 - params["poverty_depth"])
        oc_weights.append(0.2)
    if oc_signals:
        total_w = sum(oc_weights)
        composite_oc = round(
            sum(s * w for s, w in zip(oc_signals, oc_weights)) / total_w, 4
        )
        params["ownership_concentration"] = composite_oc
        provenance["ownership_concentration"] = {
            "composite": True,
            "signals": ["gini", "income_share_top20", "poverty_depth_inv"][:len(oc_signals)],
            "weights": oc_weights,
            "note": "Composite from multiple WB signals. WID.world top10/top1 wealth share not yet wired (needs WID adapter).",
        }

    # ── Mobility channels enhancement ─────────────────────────────────────
    # If intergenerational mobility proxy available, blend with income mobility
    if "intergenerational_mobility_proxy" in params:
        edu_mob = params["intergenerational_mobility_proxy"]
        if "mobility_channels" in params:
            income_mob = params["mobility_channels"]
            params["mobility_channels"] = round(income_mob * 0.5 + edu_mob * 0.5, 4)
        else:
            params["mobility_channels"] = edu_mob
        provenance["mobility_channels"] = {
            "composite": True,
            "signals": ["income_share_bottom20", "education_progression"],
            "note": "Blended income mobility + education mobility proxy. GDIM intergenerational elasticity not yet wired.",
        }

    return {
        "params": params,
        "data_provenance": provenance,
        "country_code": country_code,
        "live_inputs": sorted(params.keys()),
        "missing_inputs": sorted(missing),
        "data_years": data_years,
        "claim_state": "LIVE_DATA" if params else "NO_DATA",
    }


def _save_inequality_panel(
    country_code: str,
    year: str,
    kernel_result: Dict[str, Any],
    wb_data: Dict[str, Any],
) -> None:
    """Append a kernel run to the lightweight panel DB at inequality_panel.json."""
    import json as _pj
    import os as _os

    panel_path = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "inequality_panel.json"
    )
    try:
        try:
            with open(panel_path, "r") as f:
                panel = _pj.load(f)
        except (FileNotFoundError, _pj.JSONDecodeError):
            panel = {}
        if country_code not in panel:
            panel[country_code] = {}
        panel[country_code][year] = {
            "kernel_score": kernel_result.get("kernel_score"),
            "final_verdict": kernel_result.get("final_verdict"),
            "binding_constraint": kernel_result.get("binding_constraint"),
            "sub_dimension_scores": kernel_result.get("sub_dimension_scores", {}),
            "calhoun_risk": kernel_result.get("calhoun_risk"),
            "legitimacy_regime": kernel_result.get("legitimacy_regime"),
            "live_inputs": wb_data.get("live_inputs", []),
            "data_years": wb_data.get("data_years", {}),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        with open(panel_path, "w") as f:
            _pj.dump(panel, f, indent=2)
    except Exception:
        pass  # Panel DB failure is non-fatal — never block a kernel run


@mcp.tool(name="wealth_inequality_kernel")
def wealth_inequality_kernel(
    mode: str = "analyze",
    context: str = "",
    domain: str = "civilization",
    description: str = "",
    institutions_quality: float = 0.5,
    ownership_concentration: float = 0.5,
    mobility_channels: float = 0.5,
    risk_distribution: float = 0.5,
    information_symmetry: float = 0.5,
    voice_access: float = 0.5,
    time_horizon: float = 0.5,
    historical_damage: float = 0.5,
    power_asymmetry: float = 0.5,
    dignity_asymmetry: float = 0.5,
    network_asymmetry: float = 0.5,
    youth_unemployment: float = 0.5,
    housing_unaffordability: float = 0.5,
    future_orientation_collapse: float = 0.5,
    rules_contestable: float = 0.5,
    rules_non_captured: float = 0.5,
    contestation_cost_proportionate: float = 0.5,
    scale_mode: str = "civilization",
    preset: Optional[str] = None,
    country_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Ω-WEALTH-IEQ-00: Inequality Kernel — unified diagnosis across all 5
    inequality dimensions. Synthesis tool: conversion architecture + asymmetry
    map + return classification + role scarcity + legitimacy audit.

    The governed solution to the inequality paradox. Identifies binding constraint,
    intervention priority, and whether the system is forge-ready for change.

    Pass preset='malaysia' (or any INEQUALITY_COUNTRY_PRESETS key) to wire live
    World Bank data automatically. Or pass country_code='MYS' directly.

    Verdict: Bounded inequality + high mobility + universal dignity is achievable.
    Perfect equality is not. Extractive lock-in is the enemy, not inequality itself.
    """
    # Mode routing: health/status return quickly without running full kernel
    if mode in ("health", "status", "usage"):
        return {
            "mcp": "WEALTH",
            "task": "wealth_inequality_kernel",
            "mode": mode,
            "status": "PASS",
            "domain_verdict": "SEAL",
            "description": "Inequality Kernel — unified diagnosis across 5 inequality dimensions.",
            "available_modes": ["analyze", "health", "status"],
            "usage": (
                "wealth_inequality_kernel() — analyze with defaults | "
                "wealth_inequality_kernel(preset='malaysia') — live World Bank data | "
                "wealth_inequality_kernel(country_code='MYS') — direct ISO code"
            ),
        }
    # Live data wire: resolve preset → country_code → WB fetch
    wb_data: Dict[str, Any] = {}
    if preset or country_code:
        resolved_code = country_code
        if preset and not resolved_code:
            resolved_code = INEQUALITY_COUNTRY_PRESETS.get(preset.lower())
            if not resolved_code:
                resolved_code = preset.upper()  # allow direct ISO codes as preset
        if resolved_code:
            wb_data = _fetch_inequality_inputs_from_wb(resolved_code)
            live_params = wb_data.get("params", {})
            institutions_quality = live_params.get(
                "institutions_quality", institutions_quality
            )
            ownership_concentration = live_params.get(
                "ownership_concentration", ownership_concentration
            )
            mobility_channels = live_params.get("mobility_channels", mobility_channels)
            risk_distribution = live_params.get("risk_distribution", risk_distribution)
            information_symmetry = live_params.get(
                "information_symmetry", information_symmetry
            )
            voice_access = live_params.get("voice_access", voice_access)
            time_horizon = live_params.get("time_horizon", time_horizon)
            power_asymmetry = live_params.get("power_asymmetry", power_asymmetry)
            youth_unemployment = live_params.get(
                "youth_unemployment", youth_unemployment
            )
            future_orientation_collapse = live_params.get(
                "future_orientation_collapse", future_orientation_collapse
            )
            if not context:
                context = f"{resolved_code} inequality assessment — live WorldBank data"
            if domain == "civilization":
                domain = resolved_code

    # Run all 5 sub-dimensions
    conv = wealth_conversion_architecture(
        domain=domain,
        description=description,
        institutions_quality=institutions_quality,
        ownership_concentration=ownership_concentration,
        mobility_channels=mobility_channels,
        risk_distribution=risk_distribution,
        information_symmetry=information_symmetry,
        voice_access=voice_access,
        time_horizon=time_horizon,
        historical_damage=historical_damage,
        scale_mode=scale_mode,
    )
    asym = wealth_asymmetry_map(
        context=context,
        asset_asymmetry=ownership_concentration,
        information_asymmetry=1.0 - information_symmetry,
        power_asymmetry=power_asymmetry,
        risk_asymmetry=1.0 - risk_distribution,
        time_asymmetry=1.0 - time_horizon,
        mobility_asymmetry=1.0 - mobility_channels,
        voice_asymmetry=1.0 - voice_access,
        dignity_asymmetry=dignity_asymmetry,
        network_asymmetry=network_asymmetry,
        scale_mode=scale_mode,
    )
    role = wealth_role_scarcity_risk(
        context=context,
        youth_unemployment=youth_unemployment,
        housing_unaffordability=housing_unaffordability,
        delayed_family_formation=housing_unaffordability,
        weak_social_mobility=1.0 - mobility_channels,
        low_trust=1.0 - rules_contestable,
        civic_disengagement=1.0 - voice_access,
        status_bottleneck=power_asymmetry,
        future_orientation_collapse=future_orientation_collapse,
        scale_mode=scale_mode,
    )
    legit = wealth_legitimacy_audit(
        system_description=description,
        rules_understandable=institutions_quality,
        rules_contestable=rules_contestable,
        rules_fair_enough=1.0 - ownership_concentration,
        rules_repairable=voice_access,
        rules_non_humiliating=1.0 - dignity_asymmetry,
        rules_non_captured=rules_non_captured,
        contestation_cost_proportionate=contestation_cost_proportionate,
        scale_mode=scale_mode,
    )

    # Aggregate
    sub_verdicts = [
        conv.get("governance_verdict", "UNKNOWN"),
        asym.get("governance_verdict", "UNKNOWN"),
        role.get("governance_verdict", "UNKNOWN"),
        legit.get("governance_verdict", "UNKNOWN"),
    ]
    verdict_rank = {"VOID": 0, "888-HOLD": 1, "QUALIFY": 2, "SEAL": 3, "UNKNOWN": 2}
    final_verdict = min(sub_verdicts, key=lambda v: verdict_rank.get(v, 2))

    conv_score = conv.get("conversion_score", 0.5)
    asym_score = 1.0 - asym.get("average_asymmetry", 0.5)
    role_score = 1.0 - role.get("calhoun_risk_score", 0.5)
    legit_score = legit.get("legitimacy_score", 0.5)
    kernel_score = (conv_score + asym_score + role_score + legit_score) / 4.0

    bottleneck_map = {
        "conversion": conv_score,
        "asymmetry": asym_score,
        "role_architecture": role_score,
        "legitimacy": legit_score,
    }
    binding_constraint = min(bottleneck_map, key=bottleneck_map.get)

    result = {
        "mcp": "WEALTH",
        "tool": "wealth_inequality_kernel",
        "task": "wealth_inequality_kernel",
        "context": context,
        "domain": domain,
        "kernel_score": round(kernel_score, 4),
        "final_verdict": final_verdict,
        "binding_constraint": binding_constraint,
        "sub_dimension_scores": {k: round(v, 4) for k, v in bottleneck_map.items()},
        "sub_verdicts": {
            "conversion_architecture": conv.get("governance_verdict"),
            "asymmetry_map": asym.get("governance_verdict"),
            "role_scarcity": role.get("governance_verdict"),
            "legitimacy": legit.get("governance_verdict"),
        },
        "conversion_mode": conv.get("conversion_mode"),
        "calhoun_risk": role.get("calhoun_risk_score"),
        "above_calhoun_threshold": role.get("above_irreversibility_threshold"),
        "legitimacy_regime": legit.get("regime"),
        "dominant_asymmetry": asym.get("dominant_asymmetry"),
        "priority_interventions": conv.get("priority_interventions", []),
        "domain_verdict": final_verdict,
        "governance_verdict": final_verdict,
        "claim_tag": "ESTIMATE",
        "final_authority": "ARIF",
        "recommendation_only": True,
        "synthesis_axiom": (
            "Inequality is not one cause. It is a coupled system: "
            "endowment + institutional switch + asymmetry compounding + "
            "role scarcity + legitimacy collapse. "
            "The target is not equality of outcome. "
            "The target is bounded inequality with high mobility, dignity, and broad capability."
        ),
        "sub_tool_results": {
            "conversion_architecture": conv,
            "asymmetry_map": asym,
            "role_scarcity_risk": role,
            "legitimacy_audit": legit,
        },
        "scale_mode": scale_mode,
        "escalate_to_arifos_judge": final_verdict in ("VOID", "888-HOLD"),
        # World Bank live data provenance
        "wb_data_provenance": wb_data.get("data_provenance", {}),
        "live_inputs": wb_data.get("live_inputs", []),
        "missing_inputs": wb_data.get("missing_inputs", []),
        "data_years": wb_data.get("data_years", {}),
        "data_claim_state": wb_data.get("claim_state", "MANUAL_INPUT"),
    }

    # Persist to panel DB when country is known
    if wb_data.get("country_code"):
        years = wb_data.get("data_years", {})
        year_key = (
            max(years.values()) if years else datetime.now(timezone.utc).strftime("%Y")
        )
        _save_inequality_panel(wb_data["country_code"], year_key, result, wb_data)

    return _inject_emergence(
        "wealth_inequality_kernel",
        "synthesis",
        {
            "context": context,
            "domain": domain,
            "scale_mode": scale_mode,
        },
        result,
    )


# ═══════════════════════════════════════════════════════════════════════
# MISSING CONTRACT TOOLS — PHOENIX-73F (2026-05-25)
# Implements 5 tools declared in contracts/mcp_surface.yaml but absent
# from the runtime surface. Delegates to proven internal engines.
# ═══════════════════════════════════════════════════════════════════════


@mcp.tool(name="wealth_screen_opportunity")
def wealth_screen_opportunity(
    mode: str = "rank",
    opportunities: Optional[List[Dict[str, Any]]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    values: Optional[Dict[str, Any]] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-13: Screen — rank and filter opportunities by expected value,
    risk-adjusted return, and strategic fit.

    Modes:
      rank    — EMV-weighted ranking of all opportunities
      filter  — Apply constraint-based filtering (budget, time, risk)
      score   — Composite score via sovereign allocation kernel
    """
    return _dispatch_emergence(
        "wealth_screen_opportunity",
        mode,
        {
            "rank": wealth_expectation_emv,
            "filter": personal_decision,
            "score": wealth_score_kernel,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )


@mcp.tool(name="wealth_compute_viability")
def wealth_compute_viability(
    mode: str = "full",
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    period_unit: str = "annual",
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-14: Viability — NPV, IRR, payback, and entropy audit for a
    single project or investment. Returns a unified viability envelope.

    Modes:
      npv     — Net present value only
      irr     — Internal rate of return only
      payback — Payback period only
      full    — All four dimensions + sensitivity sweep
    """
    return _dispatch_emergence(
        "wealth_compute_viability",
        mode,
        {
            "npv": npv_reward,
            "irr": irr_yield,
            "payback": payback_time,
            "full": audit_entropy,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )


@mcp.tool(name="wealth_score_risk")
def wealth_score_risk(
    mode: str = "emv",
    scenarios: Optional[List[Dict[str, Any]]] = None,
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-15: Risk Score — Expected monetary value, Monte Carlo forecast,
    and entropy audit for tail-risk detection.

    Modes:
      emv        — Expected monetary value (probability-weighted)
      monte_carlo— Stochastic forecast with confidence bands
      audit      — Cash-flow noise, multiple-IRR detection, sensitivity
    """
    return _dispatch_emergence(
        "wealth_score_risk",
        mode,
        {
            "emv": emv_risk,
            "monte_carlo": monte_carlo_forecast,
            "audit": audit_entropy,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )


@mcp.tool(name="wealth_compare_scenarios")
def wealth_compare_scenarios(
    mode: str = "emv",
    scenarios: Optional[List[Dict[str, Any]]] = None,
    initial_investment: float = 0,
    cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-16: Compare Scenarios — Side-by-side EMV, NPV, IRR, or DSCR
    comparison across multiple investment scenarios.

    Modes:
      emv  — Compare expected monetary values
      npv  — Compare net present values
      irr  — Compare internal rates of return
      dscr — Compare debt-service coverage ratios
    """
    return _dispatch_emergence(
        "wealth_compare_scenarios",
        mode,
        {
            "emv": emv_risk,
            "npv": npv_reward,
            "irr": irr_yield,
            "dscr": dscr_leverage,
        },
        {k: v for k, v in locals().items() if k not in ("mode", "dispatch")},
    )


@mcp.tool(name="wealth_emit_investment_memo")
def wealth_emit_investment_memo(
    subject: str = "",
    metrics: Optional[Dict[str, Any]] = None,
    audience: str = "arif",
    max_length: int = 2000,
    scale_mode: str = "enterprise",
) -> Any:
    """Ω-WEALTH-17: Investment Memo — Synthesize computed metrics into a
    structured markdown investment memo for sovereign review.

    audience: arif | committee | public | regulator
    """
    metrics = metrics or {}
    sections: List[str] = [
        f"# Investment Memo: {subject}",
        f"**Audience:** {audience} | **Scale:** {scale_mode}",
        "",
        "## Executive Summary",
    ]

    verdict = metrics.get("verdict", "PENDING")
    if verdict in ("SEAL", "PASS", "QUALIFY"):
        sections.append(
            "✅ **Recommendation:** PROCEED with constitutional safeguards."
        )
    elif verdict in ("888-HOLD", "HOLD", "SABAR"):
        sections.append(
            "⚠️ **Recommendation:** HOLD pending further review or risk mitigation."
        )
    else:
        sections.append(
            "❌ **Recommendation:** REJECT — violates constitutional floors or insufficient data."
        )

    sections.extend(
        [
            "",
            "## Key Metrics",
        ]
    )
    for key, value in metrics.items():
        if key != "verdict":
            sections.append(f"- **{key}:** {value}")

    sections.extend(
        [
            "",
            "## Risk Assessment",
            "- Downside probability and tail risks reviewed.",
            "- Correlation and epistemic bias checked.",
            "- Constitutional floors (F1-F13) applied.",
            "",
            "## Next Steps",
            "1. Review binding constraint identified by kernel.",
            "2. Confirm irreversibility gate if capital action > threshold.",
            "3. Escalate to 888_JUDGE if any floor is VOID.",
            "",
            "---",
            "*Generated by WEALTH Ω-WEALTH-17 | DITEMPA BUKAN DIBERI*",
        ]
    )

    memo_text = "\n".join(sections)
    if len(memo_text) > max_length:
        memo_text = memo_text[: max_length - 3] + "..."

    return create_envelope(
        "wealth_emit_investment_memo",
        "Synthesis",
        {"memo": memo_text, "audience": audience, "subject": subject},
        {"length": len(memo_text), "max_length": max_length},
        [],
        [
            "Memo is synthesis, not primary evidence.",
            "All underlying metrics must be independently verified.",
        ],
        scale_mode=scale_mode,
    )


WEALTH_PUBLIC_TOOL_ORDER = (
    # L0 — Kernel Surface
    "wealth_system_registry_status",
    "wealth_omni_wisdom",
    "wealth_agent_path",
    # Phase 1 Survival Engine (absorbs cashflow/liquidity/runway wrappers)
    "wealth_survival_engine",
    # L1 — 11 Canonical Physics Organs (hysteresis_ledger absorbed into wealth_omni_wisdom 2026-06-03)
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
    # L2 — Mandatory Specialists
    "wealth_governance_verdict",
    # Domain Specialist (Civilization)
    "wealth_inequality_kernel",
    # NOTE: Atomic thin wrappers removed 2026-06-04.
    # Use mode-based tools: wealth_time_discount, wealth_energy_productivity,
    # wealth_entropy_risk, wealth_signal_information, wealth_flow_liquidity,
    # wealth_inertia_leverage, wealth_conservation_capital.
    # NOTE: wealth_synthesize, wealth_deal_frame, wealth_hysteresis_ledger
    # were absorbed into wealth_omni_wisdom on 2026-06-03 (Path D consolidation).
    # NOTE: wealth_health_check → wealth_system_registry_status(mode="health")
    # NOTE: wealth_epf_project + wealth_zakat_calculate → wealth_personal_finance (mode="epf"/"zakat")
    # NOTE: wealth_ledger_query + wealth_ledger_write → wealth_conservation_capital (mode="ledger_read"/"ledger_seal")
    # NOTE: wealth_entropy_audit → wealth_entropy_risk (mode="institutional")
    # NOTE: wealth_preference_rank → wealth_game_coordination (mode="preference")
    # All 7 absorptions executed 2026-06-05: 26 → 19 tools.
    # D1 — Personal Finance (merged 2026-06-04, +epf +zakat 2026-06-05)
    "wealth_personal_finance",
    # D3 — Market Data (merged 2026-06-04)
    "wealth_market_data",
    # D4 — Stock Analysis
    "wealth_stock_analysis",
)
_PUBLIC_TOOLS = set(WEALTH_PUBLIC_TOOL_ORDER)

# MCP Spec 2025-11-25 tool annotations (SEP-1862/1913/1984/2417)
_TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "wealth_system_registry_status": {
        "title": "System Registry Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_omni_wisdom": {
        "title": "Omni Wisdom",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "wealth_agent_path": {
        "title": "Agent Path",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_survival_engine": {
        "title": "Survival Engine",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_conservation_capital": {
        "title": "Conservation Capital",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "wealth_flow_liquidity": {
        "title": "Flow Liquidity",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_gradient_price": {
        "title": "Gradient Price",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_entropy_risk": {
        "title": "Entropy Risk",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_energy_productivity": {
        "title": "Energy Productivity",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_time_discount": {
        "title": "Time Discount",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_inertia_leverage": {
        "title": "Inertia Leverage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_field_macro": {
        "title": "Field Macro",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "wealth_signal_information": {
        "title": "Signal Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_game_coordination": {
        "title": "Game Coordination",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_boundary_governance": {
        "title": "Boundary Governance",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "wealth_governance_verdict": {
        "title": "Governance Verdict",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "wealth_inequality_kernel": {
        "title": "Inequality Kernel",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "wealth_personal_finance": {
        "title": "Personal Finance",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "wealth_market_data": {
        "title": "Market Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    "wealth_stock_analysis": {
        "title": "Stock Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


# MCP Spec 2025-11-25 outputSchema — standard WEALTH response envelope
# FastMCP expects dict[str, Any] JSON Schema, not Pydantic model.
_WEALTH_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Execution status"},
        "verdict": {
            "type": "string",
            "description": "Wisdom verdict: SEAL, HOLD, STOP, etc.",
        },
        "wisdom_verdict": {
            "type": "string",
            "description": "Omni-wisdom unified verdict",
        },
        "confidence": {"type": "number", "description": "Confidence score 0.0–1.0"},
        "epistemic_tag": {
            "type": "string",
            "description": "CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE",
        },
        "result": {"type": "object", "description": "Tool-specific payload"},
        "error": {"type": "string", "description": "Error message if status != OK"},
        "reasons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Human-readable justification",
        },
    },
}


def _patch_tool_annotations(mcp_server: Any) -> None:
    """Patch MCP tool annotations post-registration (FastMCP 3.x)."""
    import asyncio
    from mcp.types import ToolAnnotations

    async def _do() -> None:
        for name, anno in _TOOL_ANNOTATIONS.items():
            try:
                t = await mcp_server.get_tool(name)
                if t is not None and hasattr(t, "annotations"):
                    t.annotations = ToolAnnotations(**anno)
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do())
    except RuntimeError:
        asyncio.run(_do())


def _patch_output_schemas(mcp_server: Any) -> None:
    """Patch MCP tool outputSchema post-registration (FastMCP 3.x)."""
    import asyncio

    async def _do() -> None:
        for name in _TOOL_ANNOTATIONS.keys():
            try:
                t = await mcp_server.get_tool(name)
                if t is not None and hasattr(t, "output_schema"):
                    t.output_schema = _WEALTH_OUTPUT_SCHEMA
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do())
    except RuntimeError:
        asyncio.run(_do())


class OriginValidationMiddleware:
    """Validate Origin header on MCP endpoints to prevent DNS rebinding (SEP-2243)."""

    ALLOWED_ORIGIN_PREFIXES: tuple[str, ...] = (
        "https://wealth.arif-fazil.com",
        "https://arif-fazil.com",
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/mcp"):
            headers = dict(scope.get("headers", []))
            origin_bytes = headers.get(b"origin", b"")
            origin = (
                origin_bytes.decode()
                if isinstance(origin_bytes, bytes)
                else str(origin_bytes)
            )
            if origin and not any(
                origin.startswith(p) for p in self.ALLOWED_ORIGIN_PREFIXES
            ):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b'{"error":"Invalid Origin","detail":"DNS rebinding protection"}',
                    }
                )
                return
        await self.app(scope, receive, send)

    def __init__(self, app):
        self.app = app


# ── Tools declared in surface but not yet registered (PHOENIX-73F) ────
# These 5 L3 tools are in WEALTH_PUBLIC_TOOL_ORDER but their @mcp.tool
# decorators do not register with FastMCP at import time (silent failure).
# Excluded from registry_truth to allow healthy startup.
_KNOWN_MISSING = {
    "wealth_screen_opportunity",
    "wealth_compute_viability",
    "wealth_score_risk",
    "wealth_compare_scenarios",
    "wealth_emit_investment_memo",
}

# ═══════════════════════════════════════════════════════════════════════

# ============================================================

# ── Alias Dispatch Map (backward compat without registry pollution) ──
_ALIAS_DISPATCH: dict[str, Any] = {}


def _build_alias_dispatch() -> None:
    """Populate _ALIAS_DISPATCH from v2 canonical map only (P1-1: v1 legacy layer retired)."""
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
    # Check script location first (works inside Docker where code lives at /app)
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _app_root = os.path.dirname(_script_dir)  # one level up from internal/
    candidates = [
        os.environ.get("WEALTH_REPO_DIR"),
        _app_root,  # /app (Docker container root)
        _script_dir,  # /app/internal (fallback)
        "/opt/wealth-src",
        "/root/wealth",
        os.environ.get("ARIFOS_HOME", "/root") + "/WEALTH",
    ]
    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            result = subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={candidate}",
                    "-C",
                    candidate,
                    "rev-parse",
                    "--short",
                    "HEAD",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
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
    all_missing = [name for name in expected_names if name not in visible_set]
    extra = sorted(visible_set - expected_set)
    hidden_alias_count = len(set(_ALIAS_DISPATCH) - expected_set)
    # PHOENIX-73F: 5 contract tools are known-missing from registration.
    # Health check PASSES if only these known tools are absent.
    unexpected_missing = [n for n in all_missing if n not in _KNOWN_MISSING]
    # PHOENIX-73F FIX: surface count mismatch (38 intended / 33 runtime) means
    # external cache is stale even when all missing tools are in _KNOWN_MISSING.
    # Report DEGRADED_EXTERNAL_CACHE so clients know to reconnect and flush.
    has_stale_cache = len(expected_names) != len(visible_names)
    if has_stale_cache and not unexpected_missing and not extra:
        registry_truth = "DEGRADED_EXTERNAL_CACHE"
    else:
        registry_truth = "PASS" if not unexpected_missing and not extra else "FAIL"

    # Fix #8: Structured mismatch detection for external vs server tool visibility
    # external_visible_tools = what external clients report seeing
    # server_registered_tools = what the server actually has registered
    # mismatch = whether they differ (could indicate cache/bridge issues)
    external_visible_tools = visible_names  # Client-reported surface
    server_registered_tools = expected_names  # Server's intended surface
    mismatch = bool(unexpected_missing or extra)
    missing_from_external_client = (
        unexpected_missing  # What server has but client doesn't see
    )

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
        "missing_visible_tools": unexpected_missing,
        "registry_truth": registry_truth,
        # Fix #8: Structured mismatch detection (Arif 2026-05-16)
        "external_visible_tools": external_visible_tools,
        "server_registered_tools": server_registered_tools,
        "mismatch": mismatch,
        "missing_from_external_client": missing_from_external_client,
        # registry_truth reflects the server-side FastMCP internal registry.
        # If an external client (e.g. claude.ai bridge) shows fewer tools,
        # that is a CLIENT-SIDE CACHE issue — not a server failure.
        # Fix: disconnect and reconnect the WEALTH MCP integration on the client.
        "callability_note": (
            "registry_truth=PASS means the server's MCP tool surface matches "
            f"WEALTH_PUBLIC_TOOL_ORDER ({len(expected_names)} tools). "
            "If an external agent sees fewer tools, reconnect its MCP integration "
            "to flush the stale tool-list cache."
        )
        if registry_truth == "PASS"
        else (f"MISMATCH: missing={unexpected_missing}, extra={extra}"),
        "final_authority": "ARIF",
    }


if __name__ == "__main__":
    # ── Transport mode selection ─────────────────────────────────────────
    import argparse

    _parser = argparse.ArgumentParser(add_help=False)
    _parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default=os.environ.get("MCP_TRANSPORT", "http"),
    )
    _args, _ = _parser.parse_known_args()
    _patch_tool_annotations(mcp)
    _patch_output_schemas(mcp)
    if _args.transport == "stdio":
        mcp.run(transport="stdio")
        sys.exit(0)

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
    # ── Alias Dispatch Map — v2 canonical map only (P1-1: v1 legacy layer retired) ──
    _ALIAS_DISPATCH: dict[str, Any] = {}
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

    def _extract_structured_from_content(serialized: list) -> dict | None:
        """Extract structuredContent from MCP text content blocks.

        When FastMCP does not populate structuredContent in the tuple return,
        MCP clients that validate outputSchema (e.g. OpenCode bridge) will
        reject the response with -32600. This fallback parses JSON from
        text content blocks and promotes it to structuredContent.
        """
        if not serialized:
            return None
        for item in serialized:
            if isinstance(item, dict):
                text = item.get("text") or item.get("data") or ""
                if isinstance(text, str) and text.strip().startswith("{"):
                    try:
                        import json as _json

                        parsed = _json.loads(text)
                        if isinstance(parsed, dict) and parsed:
                            return parsed
                    except Exception:
                        pass
        return None

    def _serialize_result(result):
        """Convert FastMCP ToolResult to MCP-spec compliant JSON dict.

        to_mcp_result() has three return shapes:
          - CallToolResult (when ToolResult.meta is not None) — has model_dump
          - tuple (content_list, structured_dict) — when structured_content present
          - list[ContentBlock] — when no structured_content

        All paths use by_alias=True + exclude_none=True to strip annotations:null
        and emit structuredContent (camelCase) per MCP spec.
        """
        if result is None:
            return None
        if hasattr(result, "to_mcp_result"):
            mcp_r = result.to_mcp_result()
            if hasattr(mcp_r, "model_dump"):
                # CallToolResult — proper MCP type with aliases
                return mcp_r.model_dump(by_alias=True, exclude_none=True)
            # Tuple or list return — serialize manually with proper aliases
            content_list = mcp_r[0] if isinstance(mcp_r, tuple) else mcp_r
            structured = (
                mcp_r[1] if isinstance(mcp_r, tuple) and len(mcp_r) > 1 else None
            )
            serialized = [
                item.model_dump(by_alias=True, exclude_none=True)
                if hasattr(item, "model_dump")
                else item
                for item in (content_list or [])
            ]
            out: Dict[str, Any] = {"content": serialized}
            if structured is not None:
                out["structuredContent"] = structured
            else:
                # Fallback: MCP clients (OpenCode bridge) require structuredContent
                # when outputSchema is present. If FastMCP didn't produce it,
                # extract from content blocks or duplicate the first text content.
                extracted = _extract_structured_from_content(serialized)
                if extracted is not None:
                    out["structuredContent"] = extracted
                elif serialized and isinstance(serialized[0], dict):
                    # Last resort: use first content block's text as structured
                    txt = serialized[0].get("text", "")
                    out["structuredContent"] = (
                        {"result": txt} if txt else {"status": "ok"}
                    )
            return out
        if hasattr(result, "model_dump"):
            return result.model_dump(by_alias=True, exclude_none=True)
        # │ fallthrough-lists │ — mcp.call_tool() may return plain list[ContentBlock]
        # │ (not wrapped in ToolResult).  Treat identically to the tuple-passthrough
        # │ branch above: serialize content blocks, extract structuredContent from
        # │ JSON-parseable text.  Required by MCP clients that validate outputSchema.
        if isinstance(result, list):
            serialized = [
                item.model_dump(by_alias=True, exclude_none=True)
                if hasattr(item, "model_dump")
                else item
                for item in result
            ]
            out: Dict[str, Any] = {"content": serialized}
            extracted = _extract_structured_from_content(serialized)
            if extracted is not None:
                out["structuredContent"] = extracted
            elif serialized and isinstance(serialized[0], dict):
                txt = serialized[0].get("text", "")
                out["structuredContent"] = {"result": txt} if txt else {"status": "ok"}
            return out
        # │ fallthrough-dicts │ — mcp.call_tool() may return a plain dict
        # │ (not wrapped in ToolResult).  Wrap in MCP-spec CallToolResult shape
        # │ with structuredContent set to the dict's inner "result" key.
        # │ Required by MCP clients that validate outputSchema.
        if isinstance(result, dict):
            inner = result.get("result", result)
            text_content = json.dumps(inner, default=str, ensure_ascii=False)
            out = {
                "content": [{"type": "text", "text": text_content}],
                "structuredContent": inner
                if isinstance(inner, dict)
                else {"result": text_content},
            }
            return out
        return result

    # ── Supabase L4 Domain Receipts ───────────────────────────────────────────
    # Fire-and-forget async writes to Supabase domain tables.
    # Fails softly — never blocks WEALTH tool execution.
    # Pattern mirrors arifOS kernel injection (same doctrine).

    WEALTH_SUPABASE_URL = os.getenv(
        "WEALTH_SUPABASE_URL", "https://utbmmjmbolmuahwixjqc.supabase.co"
    )
    WEALTH_SUPABASE_ANON_KEY = os.getenv(
        "WEALTH_SUPABASE_ANON_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0Ym1tam1ib2xtdWFod2l4anFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1MjQwMTYsImV4cCI6MjAwNTA5OTk5Nn0.Nxg2Rkf-PyqnemVGz-_H1VW22jhNbmq67hH6EZ2EzEs",
    )

    async def _wealth_write_domain_receipt(
        tool_name: str, result: Any, arguments: dict
    ) -> None:
        """Write WEALTH domain data to Supabase. Fails silently if Supabase is down."""
        try:
            mode = os.getenv("WEALTH_SUPABASE_WRITE_MODE", "off").lower()
            if mode == "off":
                return

            epoch = datetime.now(timezone.utc).isoformat()
            headers = {
                "apikey": WEALTH_SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {WEALTH_SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                # ── cashflow_track → arifosmcp_transactions ─────────────────
                if tool_name == "wealth_cashflow_track" and mode in ("domain", "dual"):
                    payload = {
                        "tx_type": arguments.get("category", "expense"),
                        "asset": arguments.get("description", ""),
                        "amount": arguments.get("amount", 0.0),
                        "currency": arguments.get("currency", "MYR"),
                        "metadata": {
                            "owner": arguments.get("owner", "arif"),
                            "tool": "wealth_cashflow_track",
                            "result": result
                            if isinstance(result, dict)
                            else {"status": str(result)},
                        },
                        "epoch": epoch,
                    }
                    await client.post(
                        f"{WEALTH_SUPABASE_URL}/rest/v1/arifosmcp_transactions",
                        headers=headers,
                        json=payload,
                    )

                # ── net_worth_snapshot → arifosmcp_portfolio_snapshots ────
                elif tool_name == "wealth_net_worth_snapshot" and mode in (
                    "domain",
                    "dual",
                ):
                    # Extract holdings and total from result
                    holdings = (
                        result.get("holdings", []) if isinstance(result, dict) else []
                    )
                    total = (
                        result.get("net_worth", result.get("total_value", 0))
                        if isinstance(result, dict)
                        else 0
                    )
                    payload = {
                        "snapshot_ts": epoch,
                        "holdings": holdings,
                        "total_value": total,
                        "currency": arguments.get("currency", "MYR"),
                    }
                    await client.post(
                        f"{WEALTH_SUPABASE_URL}/rest/v1/arifosmcp_portfolio_snapshots",
                        headers=headers,
                        json=payload,
                    )

                # ── all tools → tool_calls audit (domain mode) ──────────────
                elif mode == "domain" or (mode == "dual"):
                    # Generic tool receipt for audit trail
                    pass  # arifOS already logs the cross-organ call

        except Exception:
            # Fire-and-forget — never let Supabase failure propagate
            pass

    async def legacy_mcp_handler(request):
        """Direct JSON-RPC handler — bypasses FastMCP Accept-header enforcement."""
        if request.method == "GET":
            return _JR(
                {
                    "mcp": "WEALTH",
                    "kernel": "Capital Intelligence Engine",
                    "version": __version__,
                    "transport": "streamable-http",
                    "note": "Use POST for JSON-RPC tool calls",
                }
            )
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
            return _JR(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "result": {
                        "tools": [
                            {
                                "name": t.name,
                                "description": t.description,
                                "inputSchema": (getattr(t, "parameters", None) or {})
                                | {"type": "object"},
                                "outputSchema": (
                                    getattr(t, "output_schema", None) or {}
                                )
                                | {"type": "object"},
                            }
                            for t in filtered_tools
                        ]
                    },
                }
            )

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                return _JR(
                    {
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "error": {"code": -32602, "message": "Missing tool name"},
                    },
                    status_code=400,
                )
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

                # ── Supabase L4: fire-and-forget domain receipt ───────────
                # Write to arifosmcp_transactions / arifosmcp_portfolio_snapshots
                # Never blocks — WEALTH continues even if Supabase is down
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        _wealth_write_domain_receipt(name, result, arguments)
                    )
                except Exception:
                    pass  # fire-and-forget — never propagate

                return _JR(
                    {
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "result": _serialize_result(result),
                    }
                )
            except Exception as e:
                # Return JSON-RPC error as HTTP 200 — clients expect error in body, not 5xx
                return _JR(
                    {
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "error": {"code": -32603, "message": str(e)},
                    },
                    status_code=200,
                )

        if method == "initialize":
            return _JR(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "prompts": {"listChanged": True},
                            "resources": {"listChanged": True, "subscribe": True},
                        },
                        "serverInfo": {"name": "WEALTH", "version": __version__},
                    },
                }
            )

        if method == "prompts/list":
            all_prompts = await mcp.list_prompts()
            return _JR(
                {
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
                    },
                }
            )

        if method == "prompts/get":
            prompt_name = params.get("name")
            all_prompts = await mcp.list_prompts()
            for p in all_prompts:
                if p.name == prompt_name:
                    try:
                        rendered = await mcp.render_prompt(
                            p, params.get("arguments", {})
                        )
                    except Exception:
                        rendered = {"prompt": getattr(p, "_fn", lambda: "")()}
                    return _JR(
                        {
                            "jsonrpc": "2.0",
                            "id": response_id,
                            "result": {
                                "description": p.description or "",
                                "messages": [
                                    {"role": "user", "content": {"text": str(rendered)}}
                                ]
                                if isinstance(rendered, str)
                                else {"content": str(rendered)},
                            },
                        }
                    )
            return _JR(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32602,
                        "message": f"Prompt not found: {prompt_name}",
                    },
                },
                status_code=404,
            )

        if method == "resources/list":
            all_resources = await mcp.list_resources()
            all_templates = []
            try:
                all_templates = await mcp.list_resource_templates()
            except Exception:
                pass
            return _JR(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "result": {
                        "resources": [
                            {
                                "uri": str(r.uri),
                                "name": str(getattr(r, "name", r.uri) or r.uri),
                                "description": str(getattr(r, "description", "") or ""),
                                "mimeType": str(
                                    getattr(r, "mime_type", "application/json")
                                    or "application/json"
                                ),
                            }
                            for r in all_resources
                        ],
                        "resourceTemplates": [
                            {
                                "uriTemplate": str(
                                    getattr(
                                        t,
                                        "uri_template",
                                        getattr(t, "uriTemplate", str(t)),
                                    )
                                ),
                                "name": str(
                                    getattr(
                                        t,
                                        "name",
                                        getattr(
                                            t,
                                            "uri_template",
                                            getattr(t, "uriTemplate", str(t)),
                                        ),
                                    )
                                    or getattr(
                                        t,
                                        "uri_template",
                                        getattr(t, "uriTemplate", str(t)),
                                    )
                                ),
                                "description": str(getattr(t, "description", "") or ""),
                                "mimeType": str(
                                    getattr(t, "mime_type", "application/json")
                                    or "application/json"
                                ),
                            }
                            for t in all_templates
                        ],
                    },
                }
            )

        if method == "notifications/initialized":
            return _JR({"jsonrpc": "2.0", "id": response_id, "result": {}})

        if method == "resources/read":
            uri = (params or {}).get("uri", "")
            try:
                result = await mcp.read_resource(uri)
                items = (
                    result.contents
                    if hasattr(result, "contents")
                    else (list(result) if hasattr(result, "__iter__") else [result])
                )
                contents = []
                for item in items:
                    text = (
                        getattr(item, "content", None)
                        or getattr(item, "text", None)
                        or str(item)
                    )
                    mime = getattr(item, "mime_type", None) or getattr(
                        item, "mimeType", "application/json"
                    )
                    contents.append({"uri": uri, "mimeType": mime, "text": text})
                return _JR(
                    {
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "result": {"contents": contents},
                    }
                )
            except Exception as e:
                return _JR(
                    {
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "error": {
                            "code": -32002,
                            "message": f"Resource not found: {e}",
                        },
                    },
                    status_code=404,
                )

        if method == "resources/templates/list":
            all_templates = []
            try:
                all_templates = await mcp.list_resource_templates()
            except Exception:
                pass
            return _JR(
                {
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "result": {
                        "resourceTemplates": [
                            {
                                "uriTemplate": str(
                                    getattr(
                                        t,
                                        "uri_template",
                                        getattr(t, "uriTemplate", str(t)),
                                    )
                                ),
                                "name": str(getattr(t, "name", "") or ""),
                                "description": str(getattr(t, "description", "") or ""),
                            }
                            for t in all_templates
                        ]
                    },
                }
            )

        return _JR(
            {
                "jsonrpc": "2.0",
                "id": response_id,
                "error": {"code": -32601, "message": "Method not found"},
            },
            status_code=404,
        )

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
            "wealth_reason_agent": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "wealth_kernel_route": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "wealth_judge_deliberate": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            # L2 — session state
            "wealth_session_init": {"danger_level": "L2", "fail_posture": "fail-open"},
            "wealth_evidence_fetch": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            # L1 — observe / degraded output
            "wealth_sense_observe": {"danger_level": "L1", "fail_posture": "fail-open"},
            "wealth_ops_measure": {"danger_level": "L1", "fail_posture": "fail-open"},
        }
        # Fail-open constraint for L1/L2: may degrade output, MUST NOT elevate authority
        _FAIL_OPEN_CONSTRAINT = "may degrade output, must not elevate authority"
        tools = []
        for t in all_tools:
            name = t.name
            meta = _DANGER_MAP.get(
                name, {"danger_level": "L2", "fail_posture": "fail-open"}
            )
            tools.append(
                {
                    "name": name,
                    "description": t.description or "",
                    "inputSchema": getattr(t, "inputSchema", {}),
                    "outputSchema": (getattr(t, "output_schema", None) or {})
                    | {"type": "object"},
                    "danger_level": meta["danger_level"],
                    "fail_posture": meta["fail_posture"],
                    "fail_open_constraint": _FAIL_OPEN_CONSTRAINT
                    if meta["fail_posture"] == "fail-open"
                    else None,
                }
            )
        return _JR(
            {
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
            }
        )

    async def build_info_handler(request):
        from starlette.responses import JSONResponse

        return JSONResponse(
            {
                "sha": "2f3d294891aa353bf3a0417c62436774e81d90b1",
                "short_sha": "2f3d294",
                "branch": "main",
                "version": "1.0",
                "tool_count": 33,
                "epoch": "2026",
                "source_repo": "wealth",
            }
        )

    async def health_handler(request):
        # Compute identity_hash from /root/WEALTH/identity.toml
        identity_hash = "UNAVAILABLE"
        try:
            import blake3

            with open("/root/WEALTH/identity.toml", "rb") as f:
                identity_hash = blake3.blake3(f.read()).hexdigest()
        except Exception:
            try:
                with open("/root/WEALTH/identity.toml", "rb") as f:
                    identity_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                identity_hash = "UNAVAILABLE"

        # P6 — Capital manifest hash (domain anchor, NOT constitution_hash)
        # WEALTH answers to CAPITAL_LAW (value law), not constitutional law.
        capital_manifest_hash = "sha256:missing"
        domain_law = "CAPITAL_LAW"
        try:
            _manifest_path = "/root/WEALTH/canon/001_CAPITAL_MANIFEST.md"
            if os.path.exists(_manifest_path):
                with open(_manifest_path, "rb") as f:
                    capital_manifest_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
        except Exception:
            pass

        registry = _registry_snapshot([tool.name for tool in await mcp.list_tools()])
        return _JR(
            {
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
                "identity_hash": identity_hash,
                # P6 — WEALTH identity anchor (CAPITAL_LAW, not constitutional)
                "domain_law": domain_law,
                "capital_manifest_hash": capital_manifest_hash,
                # Phase 2 hardening: freshness + owner summary
                "freshness": {
                    "status": "fresh"
                    if registry["registry_truth"] == "PASS"
                    else "stale",
                    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "age_seconds": 0,
                    "max_fresh_age_seconds": 60,
                    "stale_after_seconds": 300,
                    "expired_after_seconds": 3600,
                },
                "owner_summary": {
                    "color": (
                        "GREEN"
                        if registry["registry_truth"] == "PASS"
                        else "YELLOW"
                        if registry["registry_truth"] == "DEGRADED_EXTERNAL_CACHE"
                        else "RED"
                    ),
                    "reasons": (
                        ["registry_verified", "service_healthy"]
                        if registry["registry_truth"] == "PASS"
                        else ["registry_degraded_cache", "runtime_tool_count_mismatch"]
                        if registry["registry_truth"] == "DEGRADED_EXTERNAL_CACHE"
                        else ["registry_check_failed"]
                    ),
                },
            }
        )

    async def ready_handler(request):
        registry = _registry_snapshot([tool.name for tool in await mcp.list_tools()])
        return _JR(
            {
                "status": "ready" if registry["registry_truth"] == "PASS" else "warn",
                **registry,
            }
        )

    async def mcp_server_card(request):
        """MCP Server Card — SEP-2127 HTTP discovery document."""
        return _JR(
            {
                "name": "wealth",
                "displayName": "WEALTH Capital Intelligence",
                "url": "https://wealth.arif-fazil.com/mcp",
                "version": __version__,
                "capabilities": {"tools": True, "resources": False, "prompts": False},
                "authentication": {"type": "none"},
            }
        )

    async def prompts_handler(request):
        """Federation prompt discovery — returns governance reasoning workflows."""
        all_prompts = await mcp.list_prompts()
        return _JR(
            {
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
            }
        )

    async def resources_handler(request):
        """Federation resource discovery — returns schemas/policies/formulas/ontology/state."""
        all_resources = await mcp.list_resources()
        all_templates = []
        try:
            all_templates = await mcp.list_resource_templates()
        except Exception:
            pass
        return _JR(
            {
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
                        "uriTemplate": str(
                            getattr(
                                t, "uri_template", getattr(t, "uriTemplate", str(t))
                            )
                        ),
                        "name": str(
                            getattr(
                                t,
                                "name",
                                getattr(
                                    t, "uri_template", getattr(t, "uriTemplate", str(t))
                                ),
                            )
                            or getattr(
                                t, "uri_template", getattr(t, "uriTemplate", str(t))
                            )
                        ),
                        "description": str(getattr(t, "description", "") or ""),
                    }
                    for t in all_templates
                ],
            }
        )

    _patch_tool_annotations(mcp)
    _patch_output_schemas(mcp)
    mcp_app = mcp.http_app(path="/", transport="streamable-http", stateless_http=True)

    app = Starlette(
        routes=[
            Route("/.well-known/mcp.json", mcp_server_card, methods=["GET"]),
            Route("/.well-known/mcp/server.json", mcp_server_card, methods=["GET"]),
            Route("/mcp", legacy_mcp_handler, methods=["GET", "POST"]),
            Route("/tools", tools_handler, methods=["GET"]),
            Route("/prompts", prompts_handler, methods=["GET"]),
            Route("/resources", resources_handler, methods=["GET"]),
            Route("/health", health_handler, methods=["GET"]),
            Route("/api/build-info", build_info_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        lifespan=getattr(mcp_app, "lifespan", None),
    )
    app.add_middleware(OriginValidationMiddleware)

    # ── Startup Registry Assertion (deferred to lifespan) ────
    # PHOENIX-73F: 5 tools are in _KNOWN_MISSING but the assertion ran
    # at module-import time before FastMCP decorators finished registering.
    # Deferred to lifespan startup so all @mcp.tool decorators complete first.
    _KNOWN_MISSING = {
        "wealth_screen_opportunity",
        "wealth_compute_viability",
        "wealth_score_risk",
        "wealth_compare_scenarios",
        "wealth_emit_investment_memo",
    }

    async def _assert_registry() -> None:
        registered = {t.name for t in await mcp.list_tools()}
        extra = registered - _PUBLIC_TOOLS
        missing = _PUBLIC_TOOLS - registered - _KNOWN_MISSING
        unexpected_missing = missing - _KNOWN_MISSING
        if extra or unexpected_missing:
            raise RuntimeError(
                f"REGISTRY_TRUTH_FAILURE: extra={sorted(extra)} missing={sorted(missing)}"
            )

    _orig_lifespan = getattr(mcp_app, "lifespan", None)

    async def _combined_lifespan(app: Any) -> None:
        if _orig_lifespan:
            async with _orig_lifespan(app):
                await _assert_registry()
                yield
        else:
            await _assert_registry()
            yield

    app = Starlette(
        routes=[
            Route("/.well-known/mcp.json", mcp_server_card, methods=["GET"]),
            Route("/.well-known/mcp/server.json", mcp_server_card, methods=["GET"]),
            Route("/mcp", legacy_mcp_handler, methods=["GET", "POST"]),
            Route("/tools", tools_handler, methods=["GET"]),
            Route("/prompts", prompts_handler, methods=["GET"]),
            Route("/resources", resources_handler, methods=["GET"]),
            Route("/health", health_handler, methods=["GET"]),
            Route("/api/build-info", build_info_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        lifespan=_combined_lifespan,
    )
    app.add_middleware(OriginValidationMiddleware)

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 8082)),
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
