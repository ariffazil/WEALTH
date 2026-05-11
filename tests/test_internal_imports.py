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
    _PUBLIC_TOOLS,
    wealth_energy_productivity,
    wealth_field_macro,
    wealth_flow_liquidity,
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
    assert {
        "g_score",
        "delta_s",
        "lyapunov_lambda",
        "omega_capacity",
        "entropy_s",
        "verdict",
        "regime",
    }.issubset(result)


def test_mcp_tool_surface_matches_public_registry():
    tool_names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert tool_names == _PUBLIC_TOOLS
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


def test_time_discount_requires_cash_flows():
    envelope = wealth_time_discount(mode="npv")
    assert envelope["status"] == "FAIL"
    assert envelope["engine_status"] == "INPUT_REQUIRED"
    assert "cash_flows" in envelope["required"]


def test_energy_productivity_requires_cash_flows():
    envelope = wealth_energy_productivity(mode="pi")
    assert envelope["status"] == "FAIL"
    assert envelope["engine_status"] == "INPUT_REQUIRED"
    assert envelope["allocation_signal"] == "INSUFFICIENT_DATA"


def test_field_macro_requires_fetch_coordinates():
    envelope = wealth_field_macro(mode="fetch")
    assert envelope["status"] == "FAIL"
    assert set(envelope["required"]) == {"source", "series_id", "entity_code"}


def test_flow_liquidity_default_payload_is_json_safe():
    envelope = wealth_flow_liquidity(mode="cashflow")
    assert envelope["primary_metrics"]["runway_months"] is None
    assert envelope["allocation_signal"] == "INSUFFICIENT_DATA"
    json.dumps(envelope, allow_nan=False)


def test_registry_status_matches_runtime_surface():
    payload = wealth_system_registry_status()
    assert payload["registry_truth"] == "PASS"
    assert payload["intended_public_tools"] == len(_PUBLIC_TOOLS)
    assert payload["registered_public_tools"] == len(_PUBLIC_TOOLS)


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
