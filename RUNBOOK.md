> **Canonical RUNBOOK:** `/root/RUNBOOK.md` — this file is organ-specific overrides only.
> **SOT:** 2026-07-24 | **seal_seq:** fed-phase-7

# 📋 RUNBOOK — WEALTH Operations

> **SOT:** 2026-07-20

## Quick Health
```bash
curl -s http://localhost:18082/health | python3 -m json.tool
```

## Restart
```bash
sudo systemctl restart wealth-organ
```

## Logs
```bash
journalctl -u wealth-organ --since "5 min ago" --no-pager
```

## Deploy
```bash
cd /root/WEALTH
# Build + test, then:
sudo systemctl restart wealth-organ
curl -s http://localhost:18082/health
```

## Escalation
F13 SOVEREIGN: Muhammad Arif bin Fazil — 888_HOLD for irreversible actions.

