# WEALTH MCP — Mode Inventory

**Generated:** 2026-08-06 · Session SEAL-9132be9f7d264bc9 · Actor ARIF (SOVEREIGN)
**Source:** Live probe evidence + source-code audit (`canonical.py`, 1886 lines)
**Method:** `capital_registry(mode="schema")` + source analysis + live tool calls

---

## Discrepancy Summary

| Tool | Advertised (registry) | Actual (code) | Gap |
|------|----------------------|---------------|-----|
| capital_diagnose | 12 | **15** | +3 undocumented: petronas_vitals, sovereign_pulse, petronas_phi |
| capital_health | 7 | 7 | — |
| capital_entropy | 6 | 6 | — |
| capital_primitive | 10 (+8 aliases) | 10 | — |
| All others | — | — | — |

**Gap severity:** `capital_diagnose` error message (line 829) and `capital_registry(mode="schema")` (line 1228-1243) both omit 3 valid runtime modes. This is the CLASS of defect Arif identified: "the agent asserted six modes; my call crashed before returning a list."

---

## 1. capital_primitive (10 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `npv` | Not yet probed | — |
| `irr` | Not yet probed | — |
| `emv` | Not yet probed | — |
| `evoi` | Not yet probed | — |
| `mc` | Not yet probed | — |
| `kelly` | Not yet probed | — |
| `markowitz` | Not yet probed | — |
| `robust` | Not yet probed | — |
| `chance_constrained` | Not yet probed | — |
| `two_stage` | Not yet probed | — |

**Aliases:** monte_carlo→mc, kelly_criterion→kelly, etc. (8 total)

---

## 2. capital_health (7 modes + 3 submodes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `conservation` | Not yet probed | — |
| `flow` | Not yet probed | — |
| `runway` | Not yet probed | — |
| `survival` | ✅ reachable | See submodes below |
| `fiscal_breakeven` | Not yet probed | — |
| `confluence` | Not yet probed | — |
| `asymmetry` | Not yet probed | — |

**survival_submode variants:**
| Submode | Reachable | Probe Result |
|---------|-----------|-------------|
| `personal_finance` | ✅ | Valid response |
| `corporate_runway` | ✅ (degraded) | Silently downgraded to personal_finance. `assumptions: ["income=0, expenses=0"]` despite supplied arrays. COVERAGE: 0.33. Verdict contradiction: domain_verdict=SEAL, apex.verdict=HOLD(G=0.0), risk.verdict=GO. C11 witness: inner earth=true, envelope earth=false. |
| `sovereign_fiscal` | ❌ | **error:MCP_SCHEMA_VIOLATION** (-32602). Tool crashes at output schema layer before returning. |

**Known identity bug (Arif session):** Previously returned `tool_name: "capital_market"` — routing/labelling mismatch. This probe returned correct `tool_name: "capital_health"`. Intermittent.

---

## 3. capital_diagnose (15 modes — 12 advertised + 3 undocumented)

| Mode | Advertised? | Reachable | Probe Result |
|------|------------|-----------|-------------|
| `stress_index` | ✅ | Not yet probed | — |
| `governance_capacity` | ✅ | Not yet probed | — |
| `cascade_model` | ✅ | Not yet probed | — |
| `exploitation_detect` | ✅ | Not yet probed | — |
| `collapse_signature` | ✅ | ✅ | Returns 6-axis profile, all `signal_count=0`. `_source_text: ""` — no text ingestion path. `risk.score=0.0, risk_level=MINIMAL`. The Enron pipeline feeds nothing in. |
| `beautiful_mouse` | ✅ | Not yet probed | — |
| `capture_scan` | ✅ | Not yet probed | — |
| `power_audit` | ✅ | Not yet probed | — |
| `bid_surface` | ✅ | Not yet probed | — |
| `optimize_mwc` | ✅ | Not yet probed | — |
| `cadence_monitor` | ✅ | Not yet probed | — |
| `crisis_reflex` | ✅ | Not yet probed | — |
| **`petronas_vitals`** | ❌ | ✅ | **UNDOCUMENTED.** Returns full PETRONAS Φ vitals (9 tripwires, BODY/SPINE/SOUL layers, IFR anchors, F2 audit). Working. |
| **`sovereign_pulse`** | ❌ | ✅ | **UNDOCUMENTED.** Alias for petronas_vitals — returns identical result. |
| **`petronas_phi`** | ❌ | ✅ | **UNDOCUMENTED.** Alias for petronas_vitals — returns identical result. |

**Registry gap:** `capital_registry(mode="schema")` lists 12 modes. Error message on invalid mode also lists 12. All 3 petronas_* modes are valid at runtime (line 714: `if m in ("petronas_vitals", "sovereign_pulse", "petronas_phi")`) but invisible to discovery.

---

## 4. capital_market (7 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `fx` | Not yet probed | — |
| `commodity` | Not yet probed | — |
| `indicator` | Not yet probed | — |
| `stock` | Not yet probed | — |
| `gold` | Not yet probed | — |
| `oil` | Not yet probed | — |
| `gas` | Not yet probed | — |

---

## 5. capital_ledger (2 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `query` | Not yet probed | — |
| `write` | Not yet probed | — (requires ack_irreversible) |

---

## 6. capital_registry (4 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `status` | ✅ | Valid. 8 canonical tools, registry_truth=PASS |
| `schema` | ✅ | Valid. Full mode listing. **Note:** capital_diagnose modes listed as 12 (missing 3). |
| `domains` | ✅ | Valid. 6-domain classification. |
| `health` | ✅ | Valid. ALIVE, 8 public tools. |

---

## 7. capital_entropy (6 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `power_consequence_map` | ✅ (degraded) | Known from prior session: byte-identical output across semantically-different payloads. Confirmed: only map_id/timestamp differ. |
| `metric_purpose_audit` | Not yet probed | — |
| `responsibility_ledger` | Not yet probed | — |
| `trust_capital_decay` | Not yet probed | — |
| `coercive_order_cost` | Not yet probed | — |
| `entropy_externality` | Not yet probed | — |

---

## 8. wealth_judge_handoff (2 modes)

| Mode | Reachable | Probe Result |
|------|-----------|-------------|
| `prepare` | Not yet probed | — |
| `submit` | Not yet probed | — |

**Silent default:** Unknown modes silently fall through to `prepare`-like behavior. This is a defect — `wealth_judge_handoff` does not raise on invalid mode.

---

## TOTALS

| Category | Count |
|----------|-------|
| Total modes (canonical) | 53 |
| Modes probed | 10 |
| Modes reachable ✅ | 8 |
| Modes reachable (degraded) ⚠️ | 1 (corporate_runway) |
| Modes crashed ❌ | 1 (sovereign_fiscal) |
| Modes not yet probed | 43 |
| Undocumented modes | 3 (capital_diagnose: petronas_vitals, sovereign_pulse, petronas_phi) |
| Silent-default defect | 1 (wealth_judge_handoff) |

---

*Issued from live probe evidence, session SEAL-9132be9f7d264bc9. Final authority: Arif. DITEMPA BUKAN DIBERI.*
