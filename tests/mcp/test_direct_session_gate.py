"""Direct session gate — organ-local, no arifosmcp import."""

from wealth_mcp.server import _validate_direct_session_binding


def test_direct_session_gate_requires_session_for_non_capital():
    result = _validate_direct_session_binding("wealth_compute_irr", None, None)
    assert result["ok"] is False
    assert result["code"] == "SESSION_REQUIRED"


def test_direct_session_gate_allows_unbound_capital_surface():
    result = _validate_direct_session_binding(
        "capital_primitive", "wealth-mcp", "_default"
    )
    assert result["ok"] is False
    assert result["code"] == "SESSION_REQUIRED"


def test_direct_session_gate_bridge_path_does_not_import_arifosmcp(monkeypatch):
    def fake_bridge(session_id, actor_id):
        return {
            "ok": True,
            "code": "BRIDGE_OBSERVE",
            "reason": "bridged",
            "actor_id": actor_id or "arif",
            "session_id": session_id,
            "actor_verified": False,
        }

    monkeypatch.setattr(
        "wealth_mcp.server._validate_session_via_http_bridge", fake_bridge
    )
    result = _validate_direct_session_binding(
        "capital_primitive", "arif", "SEAL-test1234abcd5678"
    )
    assert result["ok"] is True
    assert result["code"] == "BRIDGE_OBSERVE"
