# STATUS.md — WEALTH Capital Intelligence

> **Authority:** F13 SOVEREIGN (Muhammad Arif bin Fazil)
> **Scope:** WEALTH organ only — for federation-wide status see `FEDERATION_STATUS.md`
> **Last probe:** 2026-06-20T12:53 UTC
> **Update:** Run `curl -s http://localhost:18082/health | python3 -m json.tool` and update below.

---

## 1. Current Health

| Metric | Value | Source |
|--------|-------|--------|
| **Status** | OPERATIONAL | `/health` |
| **Port** | 18082 | systemd `wealth-organ.service` |
| **Version** | 2026.06.06 | `pyproject.toml` |
| **Public tools** | 20 + 34 hidden aliases | `internal/monolith.py` |
| **Test pass** | 153/153 | `pytest tests/ -q` |
| **Canonical entrypoint** | `internal/monolith.py` (655KB) | systemd |
| **Git HEAD** | `d5047b7` | `git log -1` |
| **License** | AGPL-3.0 | `LICENSE` |

## 2. Financial Snapshot

| Item | Value | Source |
|------|-------|--------|
| **Current state** | Uninitialized | `WEALTH_SNAPSHOT.yaml` |
| **Base currency** | MYR | `WEALTH_SNAPSHOT.yaml` |
| **Active holds** | 0 | `888_ACTIVE.md` |

## 3. Federation Position

```
arifOS (Constitutional Kernel) → WEALTH (Capital Compute) → AAA (Cockpit Display)
                                          ↑
                                     Evidence from market data
```

WEALTH is **compute-only**. It never allocates capital, authorizes trades, or adjudicates constitution.

## 4. Quick Commands

```bash
systemctl status wealth-organ
curl -s http://127.0.0.1:18082/health | python3 -m json.tool
cd /root/WEALTH && pytest tests/ -q --tb=short
journalctl -u wealth-organ -n 20 --no-pager
```
