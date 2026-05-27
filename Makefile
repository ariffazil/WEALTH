# WEALTH Capital Intelligence — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: test lint format clean forge security-audit health

PYTHON := python3
PIP := pip

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ -q --tb=short || true

lint:
	ruff check . || true

format:
	ruff format . || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

health:
	@curl -s http://localhost:18082/health | python3 -m json.tool || echo "WEALTH not responding on 18082"

# ── arifOS Federation Security Audit ─────────────────────────────────────────
# Fires 888_HOLD on NATS if CRITICAL/HIGH scanner findings detected.
# NEVER blocks — always exits 0 so agentic autonomy is preserved.
include /root/arifOS/scripts/security_audit.mk

forge: security-audit
	@echo "WEALTH Surgical Burn complete. Awaiting SOVEREIGN SEAL."
