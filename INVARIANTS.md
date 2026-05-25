# INVARIANTS.md — WEALTH Capital Intelligence
> **DITEMPA BUKAN DIBERI** — Federated Source of Truth.
> **Owner:** WEALTH
> **Last verified:** 2026-05-25

## Owns
- Financial calculations (NPV, IRR, EMV, DSCR)
- Capital flow modeling and thermodynamic invariants
- 12 Ω-WEALTH substrate dimensions
- Capital intelligence verdicts (advisory only — arifOS judges, Arif decides)

## Does NOT Own
- Constitutional judgment (→ arifOS)
- Geoscience (→ GEOX)
- Execution (→ A-FORGE)

## Live State

| Item | Value | Verified |
|------|-------|----------|
| Port | **18082** | ✅ |
| Health | `https://wealth.arif-fazil.com/health` → `{"status":"healthy"}` | ✅ |
| Governance wrapper | ACTIVE — `[GOVERNANCE] WEALTH governance wrapper active` | ✅ |
| systemd service | `wealth-organ.service` | ✅ |
| Final authority | `ARIF` | ✅ |

## Port History

| Date | Port | Note |
|------|------|------|
| Pre-2026-05-25 | 8082 | Old default |
| 2026-05-25 | **18082** | Organ-standard (aligns with GEOX 18081) |

## Governance Import Invariant

WEALTH uses a package-relative import for its governance wrapper.
This is verified on every startup:

```bash
# internal/ must be a package (has __init__.py)
[ -f /root/WEALTH/internal/__init__.py ]

# monolith.py must use relative import
from .organ_governance import check_governance  # NOT: from organ_governance
```

## Required Health Check
```bash
curl http://127.0.0.1:18082/health
# Expected: {"status":"healthy","final_authority":"ARIF"}
```

## Forbidden Stale Assumptions
- ❌ WEALTH on port `8082` — correct is `18082`
- ❌ WEALTH governance disabled — it is ACTIVE
- ❌ WEALTH can execute without arifOS F1-F13 check
- ❌ "WEALTH is disabled" — it is LIVE
- ❌ Tool count "17 tools" or "50 tools" — use `curl https://wealth.arif-fazil.com/tools` to count

## Related Files
- `internal/monolith.py` — canonical kernel
- `internal/organ_governance.py` — governance wrapper
- `internal/__init__.py` — makes internal/ a Python package
- `wealth_import_smoke.py` — import validator
- `AGENT_KERNEL_START.md` — estate entry ritual
