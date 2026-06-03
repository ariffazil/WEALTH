"""
Tests for internal/federation_memory.py
Covers: empty_content guard, session_unavailable fallbacks,
network failure paths, remember/recall main flows, contract surface.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from urllib.error import URLError

import internal.federation_memory as fm


@pytest.fixture(autouse=True)
def reset_session():
    """Reset module-level session state between tests."""
    fm._session_id = None
    fm._session_ts = 0.0
    yield
    fm._session_id = None
    fm._session_ts = 0.0


# ── _ensure_session ───────────────────────────────────────────────────────

def test_ensure_session_cached():
    """Already-valid session is returned without network call."""
    import time
    fm._session_id = "cached-sid"
    fm._session_ts = time.time()
    result = fm._ensure_session()
    assert result == "cached-sid"


def test_ensure_session_network_success():
    """Session init returns header-provided sid."""
    mock_resp = MagicMock()
    mock_resp.headers.get.return_value = "new-sid-123"
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        sid = fm._ensure_session()
    assert sid == "new-sid-123"
    assert fm._session_id == "new-sid-123"


def test_ensure_session_network_fail():
    """URLError → returns None, session stays unset."""
    with patch("urllib.request.urlopen", side_effect=URLError("down")):
        sid = fm._ensure_session()
    assert sid is None
    assert fm._session_id is None


# ── remember ──────────────────────────────────────────────────────────────

def test_remember_empty_content():
    result = fm.remember("")
    assert result["stored"] is False
    assert result["error"] == "empty_content"


def test_remember_session_unavailable():
    with patch.object(fm, "_ensure_session", return_value=None):
        result = fm.remember("some content")
    assert result["stored"] is False
    assert result["error"] == "session_unavailable"


def test_remember_success():
    """Happy path: session available, arifOS returns SEAL verdict."""
    sc = {
        "verdict": "SEAL",
        "memory_id": "mem-001",
        "point_id": "pt-001",
        "pg_id": "pg-001",
        "pg_ok": True,
        "l5_status": "ok",
        "backends": ["qdrant", "postgres"],
    }
    body = f"data: {json.dumps({'result': {'structuredContent': sc}})}\n"
    mock_resp = MagicMock()
    mock_resp.read.return_value = body.encode()
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = fm.remember("test content", tags=["test"], tier="canon")

    assert result["stored"] is True
    assert result["memory_id"] == "mem-001"
    assert result["backends"] == ["qdrant", "postgres"]


def test_remember_hold_verdict():
    """arifOS returns HOLD → stored=False, _degraded set."""
    sc = {"verdict": "HOLD", "reasons": ["F7"], "failed_floors": ["F7"]}
    body = f"data: {json.dumps({'result': {'structuredContent': sc}})}\n"
    mock_resp = MagicMock()
    mock_resp.read.return_value = body.encode()
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = fm.remember("restricted content")

    assert result["stored"] is False
    assert result["verdict"] == "HOLD"


def test_remember_network_error():
    """Network failure → stored=False, _degraded set."""
    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", side_effect=URLError("timeout")):
        result = fm.remember("test")

    assert result["stored"] is False
    assert "_degraded" in result


def test_remember_no_data_in_response():
    """Response body with no 'data:' line → no_data_in_response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"event: ping\n"
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = fm.remember("test")

    assert result["stored"] is False
    assert result["error"] == "no_data_in_response"


# ── recall ────────────────────────────────────────────────────────────────

def test_recall_session_unavailable():
    with patch.object(fm, "_ensure_session", return_value=None):
        result = fm.recall("query")
    assert result["status"] == "session_unavailable"
    assert result["results"] == []


def test_recall_success():
    sc = {"results": [{"text": "memory entry 1"}, {"text": "memory entry 2"}]}
    body = f"data: {json.dumps({'result': {'structuredContent': sc}})}\n"
    mock_resp = MagicMock()
    mock_resp.read.return_value = body.encode()
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = fm.recall("wealth runway", limit=2)

    assert result["status"] == "ok"
    assert len(result["results"]) == 2


def test_recall_no_data():
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = fm.recall("query")

    assert result["status"] == "no_data"
    assert result["results"] == []


def test_recall_network_error():
    with patch.object(fm, "_ensure_session", return_value="sid-123"), \
         patch("urllib.request.urlopen", side_effect=URLError("refused")):
        result = fm.recall("query")

    assert result["status"] == "exception"
    assert result["results"] == []


# ── contract surface ──────────────────────────────────────────────────────

def test_get_contract_surface():
    surface = fm.get_contract_surface()
    assert surface["actor"] == "wealth"
    assert "mcpUrl" in surface
    assert "contract" in surface
