"""Tests for vault_supabase.py sync/async query separation.

Verifies sync callers use the sync bridge, async callers use the native
async path, and event-loop misuse fails loudly instead of blocking.
"""

import asyncio
from unittest.mock import patch, MagicMock
import httpx
import pytest

from host.governance.vault_supabase import (
    _run_select_async,
    _run_select_sync,
    _sync_supabase_select,
    _make_sync_client,
)


class TestSyncClientFactory:
    """P4: _make_sync_client creates configured httpx.Client."""

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    def test_creates_client_with_timeout(self):
        with _make_sync_client() as client:
            assert isinstance(client, httpx.Client)
            assert client.timeout.connect == 10.0

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    def test_prefer_header_when_set(self):
        with _make_sync_client(prefer="return=representation") as client:
            assert client.headers["Prefer"] == "return=representation"

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    def test_no_prefer_header_by_default(self):
        with _make_sync_client() as client:
            assert "Prefer" not in client.headers


class TestSyncSelect:
    """P3: _sync_supabase_select — basic behavior."""

    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", None)
    def test_returns_empty_when_no_key(self):
        result = _sync_supabase_select("any_table", {"order": "id.desc"})
        assert result == []

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    @patch("host.governance.vault_supabase.httpx.Client")
    def test_returns_rows_on_200(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "action": "seal"}]
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = _sync_supabase_select("test_table", {"order": "id.desc"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    @patch("host.governance.vault_supabase.httpx.Client")
    def test_returns_empty_on_non_200(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = _sync_supabase_select("test_table", {"order": "id.desc"})
        assert result == []

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    @patch("host.governance.vault_supabase.httpx.Client")
    def test_returns_empty_on_exception(self, mock_client_cls):
        mock_client_cls.side_effect = httpx.ConnectError("connection refused")
        result = _sync_supabase_select("test_table", {"order": "id.desc"})
        assert result == []


class TestRunSelectSeparated:
    """P3: sync and async Supabase reads stay on the correct path."""

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    @patch("host.governance.vault_supabase._supabase_select")
    def test_sync_path_uses_asyncio_run_without_active_loop(self, mock_async):
        mock_async.return_value = [{"id": 42}]
        result = _run_select_sync("test_table", {"order": "id.desc"})
        mock_async.assert_called_once()
        assert result == [{"id": 42}]

    @patch("host.governance.vault_supabase.SUPABASE_URL", "https://test.supabase.co")
    @patch("host.governance.vault_supabase.SUPABASE_ANON_KEY", "test-key-123")
    @pytest.mark.asyncio
    @patch("host.governance.vault_supabase._supabase_select")
    async def test_async_path_awaits_async_select(self, mock_async):
        mock_async.return_value = [{"id": 99}]
        result = await _run_select_async("test_table", {"order": "id.desc"})
        mock_async.assert_called_once()
        assert result == [{"id": 99}]

    @pytest.mark.asyncio
    async def test_sync_path_raises_inside_running_loop(self):
        with pytest.raises(RuntimeError, match="active event loop"):
            _run_select_sync("test_table", {"order": "id.desc"})
