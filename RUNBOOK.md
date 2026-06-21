# RUNBOOK.md — WEALTH (Capital Intelligence)

> **Organ:** WEALTH | **Port:** 18082
> **Last Updated:** 2026-06-21
> **Canonical FA:** 20 public + 34 hidden alias tools | **Monolith:** 657KB / ~16K lines

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
# Expected: {"status": "ALIVE", "version": "2026.06.15", "transport": "streamable-http", ...}
```

## Test
```bash
cd /root/WEALTH
uv sync --frozen
pytest tests/ -q --tb=short        # Python (153 pass)
npm test                             # Node.js legacy
npm run boot                         # node cli.js boot
```

## Logs
```bash
journalctl -u wealth-organ -n 50 --no-pager
journalctl -u wealth-organ -f       # Follow live
```

## Deploy
```bash
cd /root/WEALTH
git pull
systemctl restart wealth-organ
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
```

## Common Failure Modes
| Symptom | Likely Cause | Fix |
|---------|-------------|------|
| registry_truth FAIL | Tool surface drift | Check `monolith.py` for missing tool registration |
| /health unreachable | Service crashed | `systemctl restart wealth-organ` |
| Node tests failing | stdout pollution from Python | Known harness bug — filter `runPython` output |
| D4 stock analysis 888_HOLD | Missing trade data | Populate `wealth.trades` table |
| uv sync failing | Lock file mismatch | `uv sync` (not frozen) to regenerate |

## What NOT to Do
- Do NOT add buy/sell oracle tools (WEALTH computes, Arif decides — F13)
- Do NOT bind to 0.0.0.0 (localhost only per ADR-001)
- Do NOT modify FEDERATION_CONTRACT.md without cross-repo 888_HOLD
- Do NOT change license (AGPL-3.0)
