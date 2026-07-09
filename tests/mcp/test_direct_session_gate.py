from wealth_mcp.server import _validate_direct_session_binding


def test_direct_session_gate_requires_session(monkeypatch):
    def fake_validate_session(session_id, actor_id):
        assert session_id is None
        assert actor_id is None
        return {"valid": False, "reason": "L11 AUTH: session_id missing", "actor_id": None}

    monkeypatch.setattr(
        "arifosmcp.runtime.session_auth.validate_session",
        fake_validate_session,
    )

    result = _validate_direct_session_binding("wealth_compute_irr", None, None)

    assert result["ok"] is False
    assert result["code"] == "SESSION_REQUIRED"


def test_direct_session_gate_accepts_verified_session(monkeypatch):
    def fake_validate_session(session_id, actor_id):
        return {
            "valid": True,
            "reason": "L11 AUTH: session valid",
            "actor_id": "arif",
            "session": {
                "actor_id": "arif",
                "actor_verified": True,
                "signature_verified": True,
            },
        }

    monkeypatch.setattr(
        "arifosmcp.runtime.session_auth.validate_session",
        fake_validate_session,
    )

    result = _validate_direct_session_binding("wealth_compute_irr", "arif", "SEAL-test1234abcd5678")

    assert result["ok"] is True
    assert result["actor_id"] == "arif"
    assert result["actor_verified"] is True
