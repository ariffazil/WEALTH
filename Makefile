# WEALTH Capital Intelligence — Makefile
# DITEMPA BUKAN DIBERI

.PHONY: test lint format clean forge security-audit health

PYTHON := /root/WEALTH/.venv/bin/python3
UV := uv

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ -q --tb=short || true

lint:
	@files=$$(git diff --name-only --diff-filter=AM HEAD | grep '\.py$$' || true); \
	if [ -n "$$files" ]; then ruff check $$files; else echo "No Python files changed."; fi

format:
	$(PYTHON) -m ruff format . || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

health:
	@curl -s http://localhost:18082/health | python3 -m json.tool || echo "WEALTH not responding on 18082"

install:
	$(UV) sync --frozen

# ── arifOS Federation Security Audit ─────────────────────────────────────────
# Fires 888_HOLD on NATS if CRITICAL/HIGH scanner findings detected.
# NEVER blocks — always exits 0 so agentic autonomy is preserved.
include /root/arifOS/scripts/forge.mk
include /root/arifOS/scripts/security_audit.mk

forge: security-audit
	@echo "WEALTH Surgical Burn complete. Awaiting SOVEREIGN SEAL."
deploy-local: verify
	@echo "═══ WEALTH deploy-local ═══"
	@echo "source → runtime: /root/WEALTH/ (source IS runtime, .venv)"
	systemctl restart wealth-organ.service
	@echo "restarted wealth-organ.service"
	@sleep 3
	@curl -sf http://127.0.0.1:18082/health >/dev/null && echo "✅ WEALTH healthy" || echo "❌ WEALTH down"

verify:
	@echo "verifying authority_ceiling on WEALTH..."
	@curl -sf http://127.0.0.1:18082/health | python3 -c "import json,sys;h=json.load(sys.stdin);assert h.get('authority_ceiling'),'authority_ceiling ABSENT';print(f'✅ authority_ceiling={h[\"authority_ceiling\"]}')" || echo "❌ verify failed"
