# Rollback Instructions — WEALTH_THREE_DEFECT_CLOSURE_20261014

All changes are reversible. Two layers: code/docs (git) and runtime (service restart).

## 1. Full rollback (code + fixtures + service)

```bash
cd /root/WEALTH

# Code, docs, tests (tracked files touched by this mission)
git checkout HEAD -- \
  wealth_mcp/tools/canonical.py \
  wealth_mcp/middleware/evidence_middleware.py \
  scripts/baseline_probe.py \
  docs/INGESTION_MAP.md \
  docs/MODE_INVENTORY.md \
  tests/test_differential.py

# New test file (untracked) — remove
rm tests/test_defect_closure_20261014.py

# New fixture (untracked) — remove
rm tests/fixtures/baseline/capital_health__survival__sovereign_fiscal.json

# Probe-refreshed fixtures — restore pre-mission content
git checkout HEAD -- tests/fixtures/baseline/capital_health__*.json \
  tests/fixtures/baseline/capital_diagnose__collapse_signature.json \
  tests/fixtures/baseline/capital_diagnose__garbage_mode_test.json

# Receipts (untracked, forge_work) — optional removal or keep for audit
# rm -rf forge_work/wealth_defect_closure_20261014

# Reload the running organ with rolled-back code
systemctl restart wealth-organ.service
sleep 6 && curl -sf http://localhost:18082/health
```

## 2. Verify rollback

```bash
cd /root/WEALTH
sha256sum wealth_mcp/tools/canonical.py
# expect pre-mission hash: dfe1c7b2d53aa7b918042817c2978510337edb1b2e5654bd85132f9c9fe0bfb9

.venv/bin/python scripts/verify_receipt.py --mode-inventory
# expect REJECTED again on sovereign_fiscal (the defect state returns — that is correct)

.venv/bin/python -m pytest tests/test_defect_closure_20261014.py -q  # should now FAIL to collect (file removed)
```

## 3. Notes

- The commit made by this mission stages ONLY the files listed in
  mutation_manifest.json. `wealth_mcp/server.py` and `wealth_mcp/tools/backtest.py`
  carry PRE-EXISTING uncommitted WAVE6 work that is NOT part of this mission —
  `git checkout HEAD --` on those two files is NOT part of this rollback
  (doing so would destroy someone else's in-flight work).
- No vault entries, no identity surfaces, no other organs touched — nothing
  outside /root/WEALTH requires rollback.
- VAULT999 receipts written by probe calls during this session are append-only
  ledger records (call_status PASS/FAIL) and are not rolled back by design.
