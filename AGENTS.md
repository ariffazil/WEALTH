<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-13
valid_from: 2026-06-14
valid_until: 2026-08-12
confidence: high
scope: /root/WEALTH
-->

# AGENTS.md — WEALTH | arifOS Federation

> **MANDATORY BOOT SEQUENCE**
> 1. Read `/root/AGENTS.md` (Global Federation Rules & Identity)
> 2. Read `/root/CONTEXT.md` (Live Machine State & Ports)
> 3. Read this file (Repo-Specific Build/Test/Run rules)

> **DITEMPA BUKAN DIBERI** — Capital intelligence is forged, not given.

## Who You Serve

Arif. This is the **WEALTH** organ of the arifOS federation — Resource Intelligence / Capital Thermodynamics.

## What This Repo Is

The canonical capital engine. It models conservation, flow, gradient, entropy, energy, time, inertia, field, signal, game, boundary, and hysteresis as thermodynamic invariants over financial and resource systems.

**Canonical MCP tools** across kernel, physics organs, specialists, survival, personal finance, market data, and stock analysis. Dual runtime: Python (canonical) + Node.js (legacy). Tool count is a runtime fact — verify with `tools/list`.

## Authority & Autonomy

### Autonomous
- Modify Python/JS logic, add tools, refactor
- Run tests, fix bugs
- Update schemas and contracts

### Requires 888_HOLD
- Cross-repo API contract changes
- Production deployment without verified build + test pass

## Build & Test

```bash
cd /root/WEALTH

# Python side
pip install -e .
python internal/monolith.py   # Start canonical FastMCP server (default port 18082)
pytest tests/ -q              # Python tests

# Node.js side (legacy JS kernel)
npm install
npm test                      # node --test tests/*.test.js
npm run boot                  # node cli.js boot

# Docker
docker build -t wealth .
```

## Key Directories

| Path | Purpose |
|------|---------|
| `internal/monolith.py` | Historical monolith (~16k lines). **Live MCP exposes 7 tools** (`capital_*` surface via `tools/list` on :18082). Do not claim 37 without live verify. |
| `internal/stock/` | D4 Stock Analysis — 27-mode capital-risk governance (verify_math, pre_trade, fundamentals, TAC-9, contrast, confluence, kelly, nash_multi_factor) |
| `internal/market_data.py` | D3 Market Data — FX rates, commodities, macro indicators |
| `internal/personal_finance.py` | D1 Personal Finance — cashflow, net worth, EPF, zakat |
| `internal/db_schema.py` | PostgreSQL schema — transactions, assets, trades, positions, watchlist |
| `internal/engines/` | Advisory boundary, five seals, canonical tools |
| `mcp/server.py` | Cross-domain demo surface (6 tools) |
| `host/` | Modular Python libraries (coordination, epistemic, governance, ingest, kernel, wealth) |
| `src/` | Legacy JS/Node kernel |
| `capitalx/` | Constitutional capital pricing engine (Node.js) |
| `civilizational/` | JS boundary monitors |
| `canon/` | Constitutional specs |

## Known Anomalies

- ~~`pyproject.toml` license mismatch~~ — RESOLVED 2026-06-14. Both `pyproject.toml` and `package.json` declare `AGPL-3.0`.

## 🎭 Humour as Capture Signal (FORGED 2026-07-01)

> **Canonical skill:** `agent-humour-doctrine` (Hermes)

WEALTH detects humour as a potential **capture signal** in financial contexts:

- Jokes in financial advice may hide incentives
- Sarcasm in market commentary may mask uncertainty  
- "Trust me bro" humour may bypass verification
- Self-deprecating disclaimers may be false modesty

Use `wealth_capture_scan` to detect humour patterns that correlate with capture risk. Use `wealth_power_audit` when jokes appear in power-dynamic contexts.

---

## Federation Position

```
arifOS (Ω Law) → WEALTH (Capital) → A-FORGE (Ψ Execution) → VAULT999 (Seal)
```

WEALTH provides **evidence** — never execution. It computes NPV, IRR, EMV, DSCR, risk scores, and macro snapshots. It does not move capital.

> **APEX (port 3002)** is a legacy health probe; deliberation moved to the AAA a2a-server.  
> **MIND/MEMORY services** live under A-FORGE (ports 51001/51002) for cross-agent state and recall.

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*


---

## 🧠 CI ARCHITECTURE — Dual-Lane Agentic CI (FORGED 2026-07-01)

> **DITEMPA BUKAN DIBERI** — CI is forged, not given.
> **Architecture receipt:** `forge_work/AGENTIC-CI-FORGE-2026-07-01.md`

Every push to `main` triggers **two lanes**:

| Lane | Name | What It Does | Verdict |
|------|------|-------------|---------|
| **Lane 1** | Standard CI | Lint (Ruff) → Type check (MyPy) → Test (Pytest) → Build check | Pass/Fail |
| **Lane 2** | BIJAKSANA (Agentic CI) | ΔS (entropy) → Φ (clarity) → Ψ (truth/manifest) → Ω (governance) | SEAL_READY / SABAR / HOLD |

**The Report:** Both lanes feed into an `Agentic CI Report` — a structured JSON artifact posted as a GitHub Check Run with label `Agentic CI`. Federation cron picks up Check Run → `arif_judge` → AAA register → VAULT999 seal.

**Workflow file:** `.github/workflows/agentic-ci.yml`

**The Loop:**
```
git push → Lane 1 (Standard) + Lane 2 (BIJAKSANA)
       → Agentic CI Report (JSON + Check Run)
       → Federation cron → arif_judge → AAA → VAULT999
```

**Cross-organ:** This architecture is deployed identically across all 6 federation organs (arifOS, A-FORGE, AAA, GEOX, WEALTH, WELL). Each organ's `AGENTS.md` carries this section.

## 🛡️ STEEL SECURITY LAYER — Permanent Federation Context

> **This section is binding for every agent in the arifOS federation. Read it once. It simply IS.**

### What Actually Happened

Arif completed a one-time upgrade called the **Steel Security Layer**. Four free, best-in-class security tools (Trivy, Semgrep, Ruff, and Gitleaks) were added to the forge pipeline.

### How It Works

Every time any agent runs `make forge` or `make sot-check`, these tools scan the entire codebase and dependencies for:
- **Secrets** (Gitleaks — API keys, tokens, passwords committed to source)
- **Vulnerabilities** (Trivy — known CVEs in dependencies)
- **Risky code patterns** (Semgrep — injection, hardcoded credentials, unsafe deserialization)
- **Linting issues** (Ruff — Python code quality)

### The Iron Rule

**Everything is deliberately NON-BLOCKING.** No pre-commit hooks. No git blocks. No agent can ever be trapped in a loop by the security layer. The scanners watch and report — they never stop the metabolic cycle.

### How Problems Are Signalled

A tiny helper script (`audit_parser.py`) reads the scanner output. If it detects CRITICAL or HIGH severity findings, it fires an `888_HOLD` event into the NATS event bus. `888_HOLD` is **NOT an agent** — it is a dumb alarm bell that says "something needs human or senior-agent eyes right now." It does not think, decide, or fix anything.

### Your Unbreakable Rules

1. **Never** add blocking hooks, pre-commit, or anything that interrupts a metabolic cycle.
2. **Never** migrate to pnpm or change package managers unless Arif personally asks.
3. **Always** run the security audit as part of normal forge/sot-check — never skip it.
4. If you see a `888_HOLD` event, treat it as a real flag — but do not panic or stop other work.
5. Keep everything simple and low-friction for Arif at all times.

### How to Explain It to Arif

> "The machine now has its own quiet security watch that only rings the 888 bell when something is really wrong, while we agents stay completely free."

**DITEMPA BUKAN DIBERI — The forge has achieved full self-policing ascension.**


## Constitution

The 13 Constitutional Laws (L01–L13) live in **one canonical file**:

→ [arifOS/static/arifos/theory/000/000_CONSTITUTION.md](../../arifOS/static/arifos/theory/000/000_CONSTITUTION.md)

This organ emits the **Evidence Contract** (see Appendix B of the constitution) and does **not** self-judge. arifOS alone reads the envelope and applies L01–L13.

