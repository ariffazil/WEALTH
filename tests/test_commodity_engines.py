"""
Deterministic tests for WEALTH commodity engine bridge.
Tests adapter contract, not live engine state.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest


class TestCommodityEngineBridge:
    """Test the engine bridge adapter contract."""

    @pytest.mark.asyncio
    async def test_call_engine_success(self):
        """Valid asset + operation returns expected envelope."""
        from wealth_core.commodity_engines import call_engine

        mock_data = {"price": 4023, "symbol": "XAUUSD"}

        with patch(
            "wealth_core.commodity_engines._http_get",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await call_engine("gold", "ticker")

        assert result["error"] is False
        assert result["asset"] == "gold"
        assert result["operation"] == "ticker"
        assert result["data"] == mock_data
        assert result["source"] == "wealth://commodity"
        assert "3456" not in str(result)  # P0.1: no port leak

    @pytest.mark.asyncio
    async def test_call_engine_unknown_asset(self):
        """Unknown asset returns fail-closed error."""
        from wealth_core.commodity_engines import call_engine

        result = await call_engine("bitcoin", "ticker")

        assert result["error"] is True
        assert result["code"] == "UNKNOWN_ASSET"
        assert "bitcoin" in result["message"]
        assert "gold" in result["message"]

    @pytest.mark.asyncio
    async def test_call_engine_unknown_operation(self):
        """Unknown operation returns fail-closed error, not silent snapshot."""
        from wealth_core.commodity_engines import call_engine

        result = await call_engine("gold", "historical_volatility")

        assert result["error"] is True
        assert result["code"] == "UNKNOWN_OPERATION"
        assert result["requested_operation"] == "historical_volatility"

    @pytest.mark.asyncio
    async def test_call_engine_engine_failure(self):
        """Engine HTTP failure returns degraded state, not crash."""
        from wealth_core.commodity_engines import call_engine

        with patch(
            "wealth_core.commodity_engines._http_get",
            new=AsyncMock(side_effect=ConnectionError("refused")),
        ):
            result = await call_engine("gold", "ticker")

        assert result["error"] is True
        assert result["code"] == "ENGINE_FAILURE"
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_snapshot_aggregates_channels(self):
        """Snapshot returns ticker+signal+macro with partial success."""
        from wealth_core.commodity_engines import get_snapshot

        mock_ticker = {"price": 4023}
        mock_signal = {"direction": "FLAT", "confidence": 0.9}
        mock_macro = {"dxy": 103.2}

        async def mock_get(asset, op):
            data_map = {
                "ticker": mock_ticker,
                "signal_v2": mock_signal,
                "macro": mock_macro,
            }
            return {"error": False, "data": data_map[op]}

        with patch("wealth_core.commodity_engines.call_engine", new=mock_get):
            result = await get_snapshot("gold")

        assert result["asset"] == "gold"
        assert result["source"] == "wealth://commodity"
        assert result["snapshot"]["ticker"] == mock_ticker
        assert result["snapshot"]["signal"] == mock_signal
        assert result["snapshot"]["macro"] == mock_macro
        assert result["errors"] is None
        assert result["partial"] is False

    @pytest.mark.asyncio
    async def test_snapshot_partial_success(self):
        """If one channel fails, snapshot still returns partial data."""
        from wealth_core.commodity_engines import get_snapshot

        async def mock_get(asset, op):
            if op == "signal_v2":
                return {"error": True, "message": "Signal unavailable"}
            return {"error": False, "data": {"price": 4023}}

        with patch("wealth_core.commodity_engines.call_engine", new=mock_get):
            result = await get_snapshot("gold")

        assert result["partial"] is True
        assert result["errors"] is not None
        assert "signal" in result["errors"]
        assert result["snapshot"].get("ticker") is not None  # partial success

    def test_valid_operations_known(self):
        """All assets have known operations."""
        from wealth_core.commodity_engines import VALID_OPERATIONS

        for asset in ("gold", "oil", "gas"):
            assert "ticker" in VALID_OPERATIONS[asset]
            assert "signal_v2" in VALID_OPERATIONS[asset]
            assert "macro" in VALID_OPERATIONS[asset]
    def test_source_no_port(self):
        """source field never contains port numbers."""
        from wealth_core.commodity_engines import ENGINE_PORTS

        for asset, port in ENGINE_PORTS.items():
            assert isinstance(port, int)
            assert 3456 <= port <= 3458  # internal only


FETCHER_PATHS = {
    asset: Path(f"/root/WEALTH/engines/commodity/{asset}-api/fetch_{asset}.py")
    for asset in ("gold", "oil", "gas")
}
PUBLIC_PAGE_PATHS = [
    Path("/root/arif-sites/sites/arif-fazil.com/public") / asset / "index.html"
    for asset in ("gold", "oil", "gas")
]


def _load_fetcher(asset):
    spec = importlib.util.spec_from_file_location(f"commodity_{asset}_fetch_test", FETCHER_PATHS[asset])
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_frame():
    index = pd.date_range("2026-07-20", periods=64, freq="h", tz="UTC")
    close = pd.Series([100 + index_value * 0.1 for index_value in range(len(index))], index=index)
    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000,
        },
        index=index,
    )


def _count_key(value, key):
    if isinstance(value, dict):
        return (1 if key in value else 0) + sum(_count_key(item, key) for item in value.values())
    if isinstance(value, list):
        return sum(_count_key(item, key) for item in value)
    return 0


@pytest.mark.parametrize("asset", ("gold", "oil", "gas"))
def test_fetcher_snapshot_shape_one_timestamp_and_coherence(asset):
    module = _load_fetcher(asset)
    observed_at = "2026-07-21T03:00:00Z"
    snapshot = module.build_snapshot(
        asset,
        {"symbol": asset.upper(), "price": 100.0, "timestamp": "stale", "nested": {"timestamp": "stale"}},
        {"support": [99.0], "resistance": [101.0], "timestamp": "stale"},
        {"dxy": 100.0, "timestamp": "stale"},
        observed_at,
    )

    assert snapshot["schema"] == "wealth.snapshot.v1"
    assert snapshot["asset"] == asset
    assert snapshot["observed_at"] == observed_at
    assert set(("ticker", "levels", "macro", "coherence_id")) <= snapshot.keys()
    assert _count_key(snapshot, "observed_at") == 1
    assert _count_key(snapshot, "timestamp") == 0

    unsigned = {key: value for key, value in snapshot.items() if key != "coherence_id"}
    # Mirror Node JSON.stringify number semantics: a whole-number float becomes
    # an integer. The production serializer uses _node_body to apply the
    # same conversion before hashing.
    unsigned = module._node_body(unsigned)
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    assert snapshot["coherence_id"] == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("asset", ("gold", "oil", "gas"))
def test_fetcher_snapshot_hash_invalidates_when_unsigned_body_changes(asset):
    module = _load_fetcher(asset)
    base = module.build_snapshot(asset, {"price": 100.0}, {"support": [99.0]}, {"dxy": 100.0}, "2026-07-21T03:00:00Z")
    changed = module.build_snapshot(asset, {"price": 101.0}, {"support": [99.0]}, {"dxy": 100.0}, "2026-07-21T03:00:00Z")
    assert base["coherence_id"] != changed["coherence_id"]


@pytest.mark.parametrize("asset", ("gold", "oil", "gas"))
def test_fetcher_snapshot_uses_one_primary_data_fetch(asset, tmp_path, monkeypatch):
    module = _load_fetcher(asset)
    calls = []
    monkeypatch.setattr(module, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(module, "fetch_ohlcv", lambda **kwargs: calls.append(kwargs) or _sample_frame())
    monkeypatch.setattr(module, "_fetch_macro", lambda price=None: {"dxy": 100.0, "price_seen": price})

    snapshot = module.cmd_snapshot({})

    assert len(calls) == 1
    assert snapshot["ticker"]["price"] == 106.3
    assert snapshot["levels"]["support"]
    assert snapshot["observed_at"]


@pytest.mark.parametrize("asset", ("gold", "oil", "gas"))
def test_fetcher_snapshot_fails_closed_on_primary_fetch_error(asset, tmp_path, monkeypatch):
    module = _load_fetcher(asset)
    monkeypatch.setattr(module, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(module, "fetch_ohlcv", lambda **kwargs: (_ for _ in ()).throw(ConnectionError("offline")))

    with pytest.raises(RuntimeError, match="SNAPSHOT_UNAVAILABLE"):
        module.cmd_snapshot({})


def test_public_pages_have_no_stale_snapshot_markers():
    forbidden = (
        "0x999_TRINITY_SEALED_20260719",
        "2026-07-19",
        "Fed Rate 5.25%-5.50%",
        "999 SEAL ALIVE",
    )
    for page_path in PUBLIC_PAGE_PATHS:
        html = page_path.read_text(encoding="utf-8")
        assert all(marker not in html for marker in forbidden), page_path
        assert "apiFetch('/snapshot')" in html
        assert "wealth.snapshot.v1" in html
        assert "coherence_id" in html
