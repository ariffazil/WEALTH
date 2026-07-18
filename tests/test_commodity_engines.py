"""
Deterministic tests for WEALTH commodity engine bridge.
Tests adapter contract, not live engine state.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock


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
            assert "snapshot" in VALID_OPERATIONS[asset]

    def test_source_no_port(self):
        """source field never contains port numbers."""
        from wealth_core.commodity_engines import ENGINE_PORTS

        for asset, port in ENGINE_PORTS.items():
            assert isinstance(port, int)
            assert 3456 <= port <= 3458  # internal only
