# WEALTH Law Tools — Roadmap

> **This is a roadmap only. No code tools are implemented yet.**
>
> The canonical proposed-tool registry lives in `domains/law/ONTOLOGY.yaml`
> under the `proposed_tools:` key. Every tool here maps to an entry there.
>
> Implementation cycle requires 888_HOLD and test harnesses.

---

## Tool philosophy

WEALTH law tools compute the **shadow** of law:
- What the text appears to say.
- Which institution handles it.
- What forms, delays, and costs exist.
- What risks and dignity gaps arise.

They **never** issue binding verdicts. They never self-seal.

---

## Tool map

| Blueprint name | Canonical proposed name | Capacity band | What it computes |
|----------------|-------------------------|---------------|------------------|
| `law_lookup` | `wealth_law_lookup_act` + `wealth_law_lookup_section` | OBSERVE | Act metadata and section text by citation |
| `law_classify_case` | `wealth_law_classify_case` | OBSERVE | Pusaka kecil/besar, Muslim/non-Muslim, route |
| `law_route_institution` | `wealth_law_route_institution` | OBSERVE | Recommend PTG / Mahkamah / Syariah / Amanah Raya |
| `law_flag_risk` | `wealth_law_flag_risk` | OBSERVE | Detect 888_HOLD triggers, conflict markers, dignity risk |
| `law_generate_checklist` | `wealth_law_generate_checklist` | DRAFT | Human-facing docs, forms, timeline |

Additional proposed tools already in `ONTOLOGY.yaml`:
- `wealth_law_draft_form`
- `wealth_law_parse_document`
- `wealth_law_faraid_calculate`
- `wealth_law_distribution_calculate`
- `wealth_law_jurisdiction_resolve`
- `wealth_law_drift_detect`
- `wealth_law_human_ack`

---

## Where tools should live

When implemented, the canonical surface should be:
- Python FastMCP tools inside `internal/monolith.py` (canonical WEALTH organ).
- Or a dedicated `internal/law/` module if `monolith.py` grows too large.

The blueprint suggested `WEALTH/api/` or `WEALTH/mcp/` — those paths exist but are
not the canonical organ surface. Use `internal/` for production tools.

---

## Implementation gates

Before any tool goes live:

1. Law pack YAMLs under `data/law_pack/ACTS/` must be populated.
2. Every section text must be verified against official gazette.
3. `domains/law/ONTOLOGY.yaml` must be ratified by 888.
4. Each tool must have adversarial tests for:
   - Verdict-language refusal
   - Missing-source refusal
   - Silent jurisdiction refusal
   - HIGH/CRITICAL → 888_HOLD
5. A-FORGE lease + human sign-off wrapper must exist.

---

## Anti-patterns

- Implementing a tool before the ontology is ratified.
- Letting a tool return "this is illegal" / "you must".
- Letting a tool proceed without jurisdiction tag.
- Letting a tool self-seal or self-judge.

---

*DITEMPA BUKAN DIBERI — Tools are hands; doctrine is the spine.*
