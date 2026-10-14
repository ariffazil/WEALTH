# Root-Cause Report — WEALTH Three-Defect Closure (2026-10-14)

Session: WEALTH_THREE_DEFECT_CLOSURE_20261014 · Repo: /root/WEALTH · HEAD before: dbf4d4b
All claims below are OBS (directly observed this session) unless marked DER/INT.

## D1 — capital_health sovereign_fiscal

**Where did the -32602 originate?** (OBS via git archaeology + live probes)
Historical. Pre-2026-08-06, `canonical.py` survival/sovereign_fiscal branch raised a bare
`ValueError("sovereign_fiscal survival mode requires …")` when fiscal params were missing.
An uncaught raise inside a FastMCP tool produces a transport-level tool error with no
structured content — the caller sees an error class, never a raw response. That was
recorded as `error:MCP_SCHEMA_VIOLATION (-32602)` in MODE_INVENTORY.md (2026-08-06).
Commit `52ff13c` (Loop 8, 2026-08-06) replaced the raise with a structured
MISSING_REQUIRED_PARAMS envelope. **Live reproduction today: NO -32602 under any tested
shape** (probe shape, full fiscal, direct mode, partial params, unknown extra arg,
string-typed number) — all return HTTP 200 with structured content.

**Was it request schema, dispatch schema, handler signature, mode registry, or response contract?**
Handler raise-path (dispatch layer), already healed at the tool layer. What conflicted with
the contract was the raise: no `wrap_result`, no envelope, misclassified by the governance
wrapper as INTERNAL_ERROR/FATAL.

**Why did the crash happen before raw response?** A raise bypasses `wrap_result()` — nothing
is materialized for capture; only an error class remains.

**What remains of D1 at product layer today (OBS):**
1. `scripts/baseline_probe.py` sends NO canonical fiscal payload for the sovereign_fiscal
   submode (representative payload = mode/session/actor only) and saves every submode call
   under the generic `capital_health__survival.json` (last-write-wins). Therefore a real raw
   sovereign_fiscal fixture cannot exist → verify_receipt --mode-inventory R6 REJECT
   (62/63, the audit's one surviving rejection).
2. End-of-chain unknown-mode handling in `capital_health` still `raise ValueError` (canonical.py,
   final lines of the tool) → classified INTERNAL_ERROR / FATAL / ESCALATE_TO_888_HOLD for what
   is a client input error. Sibling tools (capital_market, capital_registry, capital_diagnose)
   already follow "Zen Phase 2: unknown mode → structured error, never MCP -32602".
3. Stale claims: MODE_INVENTORY.md still asserts "crash -32602"; evidence_middleware
   `_KNOWN_CRASHING["capital_health"]={"survival:sovereign_fiscal"}` still asserts crashing.

**Minimum change that restores structured response + real fixture:** canonical fiscal payload
in the probe + per-submode fixture naming; structured UNKNOWN_MODE error replacing the raise;
refresh the two stale records; drop the stale middleware crashing entry. (The sovereign branch
itself already returns a full structured fiscal result — OBS D1b.)

## D2 — capital_health corporate_runway

**Where did the mode become personal_finance?** (DER from fixtures + code)
Historically the survival if-chain had no corporate branch; `_sm` fell through to
`_call_legacy_tool("wealth_survival_engine", {"mode": _sm or "personal_finance", …})` and the
legacy engine computed a personal-finance shape — the Aug-6 fixture
(`capital_health__survival__corporate_runway.json`) preserves it: `defect:
"SILENT_DOWNGRADE …"`, `assumptions: ['income=0, expenses=0']`. The current canonical.py has
an explicit corporate branch (541-593) — OBS D2a/D2b: corporate path live, materially
different outputs (12.0 vs 6.0 months), missing fields → explicit MISSING_REQUIRED_PARAMS.

**Default branch, alias map, parser, normalizer, or handler fallback?** Handler fallthrough
(no branch) + the `_sm or "personal_finance"` default in the legacy delegation. Both no longer
active for the corporate path.

**Which fields are dropped today?** (OBS D2d) Foreign material fields — `income`, `expenses`
(and `monthly_income_v`/`monthly_expenses_v` when liquid/burn present) — are silently ignored
by the corporate branch: neither consumed, reflected, nor rejected. Violates the field
disposition law (eat / reflect / reject).

**How will unsupported corporate input be rejected nyata?** Corporate branch gains an explicit
UNSUPPORTED_FIELDS structured error when personal-finance-only material fields accompany
`survival_submode="corporate_runway"`, plus resolved-mode reflection (`mode`,
`survival_submode` keys) in its output.

**Also stale:** INGESTION_MAP.md rows 50-52 (mark corporate fields DEGRADED/downgraded),
middleware `_KNOWN_DEAD_FIELDS["capital_health"]["survival:coporate_runway"]` — a key with a
typo ("coporate") that can never match a real call AND a claim that is now false.

## D3 — capital_diagnose collapse_signature.domain_scope

**Where is domain_scope accepted?** Tool signature: `capital_diagnose(mode, domain_scope="", payload=None, …)`
(canonical.py:774).

**Where should it enter computation/evidence-selection?** The engine
`compute_collapse_risk(scenario, capital_type="financial", historical_priors=None)` exposes
exactly those hooks; the tool's collapse branch (canonical.py:916-934) passes only
`p.get("scenario") or p.get("text") or p.get("source_text") or p.get("domain_scope") or ""`
— i.e., ONLY the payload-embedded copy. The top-level parameter is never merged into `p`
and never read. Sibling modes `cadence_monitor`/`crisis_reflex` DO consume top-level
domain_scope (`p.get("org_name", domain_scope)`) — the omission is specific to
collapse_signature.

**Why is _source_text empty?** With the probe's call shape (top-level domain_scope, no
payload), every term in the chain is falsy → `compute_collapse_risk("")` →
`profile["_source_text"] = ""`. (OBS D3a/D3b/D3d/D3e `_source_text=''`; D3c payload-embedded
→ `'enron_2000'`.)

**Hard dead-field proof (OBS):** after volatile-key strip, D3a(enron_2000) ≡ D3b(lehman_2008)
≡ D3e(planet_mars_2199) byte-identical; unknown scope silently accepted.

**What observable output should change with domain_scope?**
1. `_source_text` populated (top-level wired into the scenario chain, same as payload path);
2. scope → resolved corpus prior (disk registry `wealth_core/collapse_signature/corpus/*.txt`,
   via `list_available_corpora()`) → `historical_priors=[corpus_id]` → `priors_used` /
   `prior_comparison` differ per scope;
3. result reflects `domain_scope` (as supplied) + `domain_scope_resolved`;
4. unsupported scope → structured UNSUPPORTED_DOMAIN_SCOPE listing available corpora;
5. no material input at all (no scenario text, no scope) → structured MISSING_REQUIRED_INPUT
   (no confident-negative on zero evidence).

---

## PLAN (minimal, product layer, strictly bounded)

### FILES TO CHANGE
| File | Change |
|---|---|
| `wealth_mcp/tools/canonical.py` | (a) collapse_signature: wire top-level domain_scope into scenario chain + corpus resolution + priors + reflection + unsupported-scope rejection + empty-input gate. (b) corporate_runway: resolved-mode reflection + UNSUPPORTED_FIELDS for personal-only material fields. (c) sovereign_fiscal: resolved-mode reflection on fiscal result. (d) replace end-of-chain `raise ValueError(Unknown mode)` with structured UNKNOWN_MODE envelope (Zen Phase 2 pattern). |
| `wealth_mcp/middleware/evidence_middleware.py` | Remove the three stale entries that encode these defects (dead: collapse_signature.domain_scope; dead: survival:coporate_runway; crashing: survival:sovereign_fiscal). Structures remain as defense for future defects. |
| `scripts/baseline_probe.py` | Submode probes carry canonical payloads (personal/corporate/sovereign) and persist per-submode fixtures `capital_health__survival__<submode>.json` (plus the existing generic survival write). |
| `docs/INGESTION_MAP.md` | Update the three defect rows + counts to fixed state. |
| `docs/MODE_INVENTORY.md` | sovereign_fiscal ❌→✅ (real fixture), corporate_runway degraded→✅. |
| `tests/test_differential.py` | Clear the two stale known_red flags (corporate + collapse) whose defects are now fixed; update expected_difference prose. |
| `tests/test_defect_closure_20261014.py` | NEW — minimum regression contract for D1/D2/D3 (in-process `_tool_fn` harness). |
| `tests/fixtures/baseline/capital_health__survival__{personal_finance,corporate_runway,sovereign_fiscal}.json`, `capital_diagnose__collapse_signature.json`, `capital_health__survival.json`, `capital_health__garbage_mode_test.json` | refreshed by REAL probe calls after service reload (no hand-editing) |

### EXPECTED BEHAVIOR
- D1: canonical sovereign_fiscal payload → structured fiscal result reflecting all four
  inputs + resolved mode; invalid/unknown modes → structured UNKNOWN_MODE (isError-free
  envelope, correct classification); real fixture `capital_health__survival__sovereign_fiscal.json`
  exists → mode inventory 63/63 → R6 ACCEPT.
- D2: corporate_runway never resolves to personal_finance; resolved mode visible in output;
  A/B payloads materially different; missing liquid/burn → explicit error; personal-only
  fields alongside corporate → explicit UNSUPPORTED_FIELDS error.
- D3: top-level domain_scope consumed (source text + priors + reflection); A/B scopes differ
  explainably; unknown scope rejected explicitly; `_source_text` non-empty for valid material
  input; no-scope-no-text → MISSING_REQUIRED_INPUT (no silent confident negative).

### TESTS TO ADD (tests/test_defect_closure_20261014.py)
D1: (1) canonical sovereign_fiscal succeeds structurally; (2) result reflects 4 fiscal inputs;
(3) unknown mode → structured UNKNOWN_MODE (not raise); (4) partial fiscal → MISSING_REQUIRED_PARAMS.
D2: (5) corporate resolves corporate (mode keys present); (6) corporate fields survive;
(7) A/B materially different; (8) no personal_finance downgrade artifact; (9) missing required
→ explicit error; (10) income/expenses with corporate → UNSUPPORTED_FIELDS.
D3: (11) domain_scope A/B differential; (12) domain_scope reflected; (13) _source_text populated;
(14) unsupported scope → explicit error; (15) empty input → MISSING_REQUIRED_INPUT; (16) payload
text still drives analysis (back-compat).
Plus live-path: existing differential + ingestion suites must stay green.

### ROLLBACK METHOD
`git checkout HEAD -- <changed files>` for tracked files; delete the new test file; restart
wealth-organ.service. Fixtures: `git checkout` restores prior fixture content. Full receipt:
rollback_instructions.md.

### BLAST RADIUS
Touched tool branches: capital_health (survival submodes + unknown-mode tail), capital_diagnose
(collapse_signature only). No other tool, mode, engine signature, schema, or repo. Middleware
entries removed encode exactly these three defects (defense structure kept). Docs updated only
where they assert the three defects. Service restart required once (T2, announced). Existing
83-test baseline + calibration runner must remain green. Risk: collapse_signature empty-input
gate changes behavior for calls with NO material input — verified against existing suites
(ingestion/differential send text or scope).
