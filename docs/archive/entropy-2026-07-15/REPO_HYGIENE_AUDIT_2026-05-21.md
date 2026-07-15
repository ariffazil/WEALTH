# Repo Hygiene Audit - 2026-05-21

## git status --short
```
 M docs/AGENT_LAYOUT_CONTRACT.md
 M server.py
 M tests/test_internal_imports.py
?? docs/REPO_HYGIENE_AUDIT_2026-05-21.md
```

## git branch --show-current
```
chore/repo-hygiene-wealth-20260521
```

## git log --oneline --decorate --graph --max-count=12
```
* ff49f2e (HEAD -> chore/repo-hygiene-wealth-20260521, main) registry: expand tools.yaml — 63 tools, uniform metadata, canonical source note
* 59076e7 (origin/main, origin/HEAD) REPO=ariffazil/wealth
* c7c903d registry: delete empty registry.json
* beab3b9 deps: sync package-lock.json with sdk ^1.29.0
* 6bfb453 deps: seal CVE-2026-25536 in Node MCP SDK
* c3b79d7 docs: forge boundary governance baseline
* b86c4e0 chore: advance next-horizon state and reduce chaos
* fb12191 ci(WEALTH): build-only validation — VPS handles GHCR push autonomously
* 99e00ab fix(WEALTH): remove broken GHCR_TOKEN fallback, use GITHUB_TOKEN only
* 6fffcca ci(WEALTH): fix GHCR push auth + add autonomous VPS deploy script
* 2211aba fix(WEALTH): claim-state discipline + advisory assessment mapping
* a829443 feat: fold arif_anti_sink_check into wealth_role_scarcity_risk as organism_context param
```

## git log --oneline origin/main..HEAD
```
ff49f2e registry: expand tools.yaml — 63 tools, uniform metadata, canonical source note
```

## git diff --stat
```
 docs/AGENT_LAYOUT_CONTRACT.md  | 155 +++++++++++++++++++++++++++++------------
 server.py                      |  15 +++-
 tests/test_internal_imports.py |   2 -
 3 files changed, 124 insertions(+), 48 deletions(-)
```

## git diff --check
```
PASS
```

## verification

```txt
npm test: PASS (52/52)
pytest tests/ -q: PASS (50/50)
```
