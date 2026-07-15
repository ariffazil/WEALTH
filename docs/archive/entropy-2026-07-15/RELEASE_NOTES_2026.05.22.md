# RELEASE NOTES - WEALTH v2026.05.22-pre

> **Pre-release date:** 2026-05-22  
> **Evidence date:** 2026-05-21  
> **Status:** PRE-RELEASE / PR REVIEW  
> **Authority:** arifOS governance, Arif final judgment

## Purpose

This pre-release lowers repo entropy and makes WEALTH clearer as the capital evidence engine. WEALTH provides governed capital evidence; it does not move money or approve capital movement.

## Changed

- Existing tool metadata expansion preserved in trailer-compliant branch history.
- Shared federation layout contract repaired and normalized in `docs/AGENT_LAYOUT_CONTRACT.md`.
- Repo hygiene audit ledger added at `docs/REPO_HYGIENE_AUDIT_2026-05-21.md`.
- `server.py` made import-safe:
  - importing `server.py` exposes monolith tool functions for tests and scripts.
  - executing `server.py` still starts the runtime.
  - tests no longer collide with the live WEALTH service on port `8082`.
- Stale registry assertions updated to match the current public tool registry.

## Verification

```txt
git diff --check: PASS
npm test: PASS (52/52)
pytest tests/ -q: PASS (50/50)
```

## Boundary

WEALTH owns capital and resource evidence. It does not execute transactions, approve capital movement, adjudicate constitutional judgment, compute geoscience evidence, or serve as the UI cockpit.

## Release Note

This is a pre-release branch, not a direct push to `main`. No license fields were changed.

Ditempa Bukan Diberi.
