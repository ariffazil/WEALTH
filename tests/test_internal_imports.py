import asyncio
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import internal.monolith as monolith
from internal.invariants import get_g_score
from internal.monolith import (
    WEALTH_PUBLIC_TOOL_ORDER,
    wealth_boundary_governance,
    wealth_entropy_risk,
    wealth_gradient_price,
    wealth_hysteresis_ledger,
    mcp,
    wealth_system_registry_status,
    wealth_time_discount,
)
from host.ingest.health import HealthTracker
from host.ingest.registry import _cache_age_hours


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


def test_mcp_tool_surface_matches_public_registry():
    tool_names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert tool_names == set(WEALTH_PUBLIC_TOOL_ORDER)
    assert "wealth_future_value" not in tool_names
    assert "vault_write" not in tool_names


def test_invariant_tools_do_not_use_var_kwargs():
    for tool in (
        wealth_entropy_risk,
        wealth_time_discount,
        wealth_boundary_governance,
        wealth_hysteresis_ledger,
    ):
        assert all(
            parameter.kind is not inspect.Parameter.VAR_KEYWORD
            for parameter in inspect.signature(tool).parameters.values()
        )


def test_gradient_price_reports_supported_modes():
    envelope = wealth_gradient_price(mode="bad-mode")
    assert envelope["status"] == "FAIL"
    assert "spread" in envelope["allowed_modes"]


def test_time_discount_wraps_existing_engine():
    envelope = wealth_time_discount(
        mode="npv",
        initial_investment=1000.0,
        cash_flows=[1200.0],
        discount_rate=0.1,
    )
    assert envelope["tool"] == "wealth_time_discount"
    assert envelope["status"] in {"OK", "WARN", "HOLD"}
    assert envelope["provenance"]["source_tools"] == ["npv_reward"]


def test_hysteresis_ledger_query_wraps_existing_engine(monkeypatch):
    monkeypatch.setitem(
        monolith._INVARIANT_DISPATCH["wealth_hysteresis_ledger"],
        "query",
        lambda query, limit=10, session_id=None: {"task": "wealth_ledger_query", "count": 0, "query": query},
    )
    envelope = wealth_hysteresis_ledger(mode="query", query="nonexistent", limit=1)
    assert envelope["tool"] == "wealth_hysteresis_ledger"
    assert envelope["provenance"]["schema_version"] == "wealth.physics_economics.v1"


def test_registry_status_matches_runtime_surface():
    payload = wealth_system_registry_status()
    assert payload["registry_truth"] == "PASS"
    assert payload["public_surface_count"] == len(WEALTH_PUBLIC_TOOL_ORDER)
    assert payload["runtime_surface_count"] == len(WEALTH_PUBLIC_TOOL_ORDER)


def test_cache_age_is_unknown_when_no_cache_file_exists(tmp_path):
    missing = tmp_path / "missing-cache.json"
    assert _cache_age_hours(str(missing)) is None


def test_health_tracker_sanitizes_non_finite_cache_age(tmp_path):
    health_path = tmp_path / "ingest-health.json"
    tracker = HealthTracker(str(health_path))

    tracker.record_attempt("Ember", True, 0.0, cache_age_hours=float("inf"))

    payload = tracker.get_health()
    assert payload["Ember"]["cache_age_hours"] is None
    json.dumps(payload, allow_nan=False)


def test_health_tracker_sanitizes_legacy_non_finite_state(tmp_path):
    health_path = tmp_path / "legacy-ingest-health.json"
    health_path.write_text('{"Ember":{"cache_age_hours":Infinity}}', encoding="utf-8")

    tracker = HealthTracker(str(health_path))
    payload = tracker.get_health()

    assert payload["Ember"]["cache_age_hours"] is None
    json.dumps(payload, allow_nan=False)
