# WEALTH Phase 3 TODO — Epistemic Collapse Scanner

> **Filed:** 2026-07-03, from QQQ analysis (Kinabalu energy domain)
> **Priority:** HIGH — closes vocabulary gap exposed by WEALTH tool blind spots
> **Status:** BACKLOG (requires WEALTH server modification)

---

## Problem

Existing WEALTH scanners (`wealth_collapse_signature_scan`, `wealth_beautiful_mouse_scan`,
`wealth_power_audit`) are calibrated for:
- **Financial collapse** (Enron/1MDB/PDVSA/Pemex/WorldCom)
- **State-level institutional collapse**
- **Terminal-stage Calhoun Phase C** (perfect performance narratives)

They are **NOT** calibrated for:
- **Sub-function epistemic sink** (e.g., PETRONAS Exploration sub-function class)
- **Earlier-stage committee-density collapse** (before phrase-pool crystallizes)
- **Resource institution pattern** (50-year compound effect, not bankruptcy event)
- **Diplomatic-language extraction** (hard content written in polite grammar)

**Evidence:** QQQ analysis returned `INSUFFICIENT_SIGNAL` on all 6 wisdom dimensions
and `LOW` on all 6 power audit dimensions for a scenario structurally documented
in HAMPA cards (Laletha dossier pattern, Kak Su escalation email, 5 Graph patterns).

---

## Proposed Solution

### New Scanner: `wealth_epistemic_collapse_scan`

**Purpose:** Detect sub-function epistemic sink BEFORE Phase C crystallizes.

**Detection axis:** "Role saturation without truth metabolism"

**Calibration source:** Calhoun Universe 25 → institutional epistemology mapping
(from `kinabalu_institutional_pattern_2026-07-03.md`)

### Vocabulary to Add (20+ diplomatic-language phrases)

**Phase 1 — Committee language (career safety signals):**
- "highlighted the need for improvement"
- "informed to improve communication"
- "group alignment"
- "let's not reopen [X] at this stage"
- "personal guidance"
- "task reassignment"
- "matrix manager"
- "rotated recently"

**Phase 2 — Dossier language (extraction signals):**
- "5-point dossier"
- "diplomatic severity"
- "AI tools caused confusion"
- "underperformer"
- "presentation polisher"
- "citation chain"
- "inherited model"
- "personal guidance claimed"
- "task reassignment pattern"
- "1-on-1 surveillance"
- "dossier-builder"
- "competent middle manager"

**Phase 3 — Epistemic sink signals (systemic):**
- "we've always done it this way"
- "the model is established"
- "legacy framework"
- "stakeholder alignment required"
- "not the right time"
- "too early to challenge"
- "respect the existing body of work"

### Detection Logic

Density-based per signal (like `beautiful_mouse_scan`):
- Count diplomatic-language phrases per 1000 words
- Threshold: ≥3 phrases per 1000 words = EMERGING
- Threshold: ≥6 phrases per 1000 words = ACTIVE
- Threshold: ≥10 phrases per 1000 words = DOMINANT

Cross-reference with:
- `beautiful_mouse_scan` for Phase C indicators
- `collapse_signature_scan` for financial collapse overlap
- `power_audit` for incentive asymmetry

### Integration Points

1. **WEALTH server** (`internal/monolith.py`) — add new tool
2. **WEALTH AGENTS.md** — document new scanner
3. **GEOX bridge** — cross-reference with geological claim language
4. **arifOS judge** — feed epistemic collapse risk into constitutional verdicts

---

## Expected Impact

| Current | After Phase 3 |
|---------|---------------|
| `wealth_wisdom_evaluate`: NEUTRAL on institutional dynamics | Detects epistemic sink signals in proposal text |
| `wealth_power_audit`: LOW on capture risk | Detects diplomatic-language extraction patterns |
| `wealth_collapse_signature_scan`: MINIMAL on Calhoun pattern | Detects earlier-stage committee-density collapse |

---

## References

- `kinabalu_institutional_pattern_2026-07-03.md` — Calhoun Universe 25 → institutional epistemology
- `kinabalu_falsification_framework_2026-07-03.md` — GEOX-LC-001 acquisition law
- HAMPA cards (Laletha dossier, Kak Su escalation) — structural evidence
- `wealth_beautiful_mouse_scan` — existing Phase C detector (template for new scanner)

---

*Ditempa Bukan DiberI — The scanner gap is real. Close it.*
