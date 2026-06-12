# RUNBOOK.md — WEALTH (Capital Intelligence)

> **Organ:** WEALTH | **Port:** 18082
> **Last Updated:** 2026-06-12

## Start / Stop
```bash
systemctl start wealth-organ
systemctl stop wealth-organ
systemctl restart wealth-organ
systemctl status wealth-organ
```

## Health Check
```bash
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
```

## Test
```bash
cd /root/WEALTH
pip install -e ".[dev]"
pytest tests/ -q --tb=short        # Python (153 pass)
npm test                             # Node.js legacy
```

## Logs
```bash
journalctl -u wealth-organ -n 50 --no-pager
```

## Common Failure Modes
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| registry_truth FAIL | Tool surface drift | Check `monolith.py` for missing tool registration |
| /health unreachable | Service crashed | `systemctl restart wealth-organ` |
| Node tests failing | stdout pollution from Python | Known harness bug — filter `runPython` output |
| D4 stock analysis 888_HOLD | Missing trade data | Populate `wealth.trades` table |

## What NOT to Do
- Do NOT change license field in pyproject.toml without 888_HOLD
- Do NOT add buy/sell oracle tools (WEALTH computes, Arif decides)
- Do NOT bind to 0.0.0.0
