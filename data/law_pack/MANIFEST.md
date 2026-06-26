# Law Pack MANIFEST — v1 minimum binding

> **Source-of-truth for the law pack that ONTOLOGY.yaml validates against.**
>
> ⚠️ **DRAFT pending 888 ratification.** This manifest was reconciled on
> 2026-06-24 from the parallel 002 and 015 series. The 015 series is retired;
> its useful contents merged into `domains/law/ONTOLOGY.yaml`. The 888 seal is
> not yet alive.

| Field | Value |
|-------|-------|
| Pack id | `MY-LAW-PACK-V1` |
| Version | `1.1.0-DRAFT` |
| Issued | 2026-06-24 |
| Issuer | WEALTH_FORGE |
| Ratified by | **pending 888** |
| Witness | arifOS canon 002 (draft) |
| Jurisdiction coverage | MY-FED, MY-PG, MY-SBH, MY-SWK, MY-SYR |
| Source license | Open. Re-citation required (Act year + gazette version). |
| ACTS status | **Index only** — YAML files under `ACTS/` not yet populated |

## Acts in this pack (binding list)

| File | Act | Jurisdiction | Priority | Notes |
|------|-----|--------------|----------|-------|
| `ACTS/KANUN_TANAH_NEGARA_1965.yaml` | Kanun Tanah Negara 1965 | MY-FED | P0 | Land code — primary title spine |
| `ACTS/FEDERAL_CONSTITUTION_articles.yaml` | Federal Constitution — capital-affecting articles | MY-FED | P0 | Article 13, 89, 91, 136, 153 — bound to land and rights |
| `ACTS/MA63_constitution_articles.yaml` | Malaysia Agreement 1963 — constitutional protections | MY-SBH, MY-SWK | P0 | MA63 is first-class, not a footnote |
| `ACTS/SMA_PENANG_1957.yaml` | State land rules (Penang) | MY-PG | P0 | Penang-specific title and alienation |
| `ACTS/DISTRIBUTION_ACT_1958.yaml` | Distribution Act 1958 | MY-FED | P0 | Non-Muslim intestate |
| `ACTS/SMALL_ESTATES_1955.yaml` | Small Estates Act 1955 | MY-FED | P0 | Non-Muslim, simplified |
| `ACTS/FARAID_schedule.yaml` | Faraid schedule | MY-SYR | P0 | Muslim inheritance — fixed shares |
| `ACTS/PDPA_2010.yaml` | Personal Data Protection Act 2010 | MY-FED | P0 | Cross-cutting — every record involving a natural person |

## Refresh policy

- Federal Acts: revalidate on first session of each quarter.
- State rules: revalidate when the State gazette issues a new amendment.
- MA63: treat as constitutional; only revalidate on Federal Constitution amendment that touches MA63.
- Faraid: static unless Jabatan Kemajuan Islam Malaysia (JAKIM) issues a new edar.
- PDPA: revalidate when the Personal Data Protection Commissioner issues a new guideline.

A `data/law_pack/REFRESH_LOG.jsonl` will be appended each revalidation (T1 batched promotion — see SOUL.md §7.9.9).

## Rules

1. **No unsourced claims.** Every section text must be re-cited from a public gazette or authoritative republication.
2. **No paraphrasing.** Section text is verbatim. Paraphrase lives in the AdvisoryRecord's `detail`, not in `Section.text`.
3. **Append-only.** New acts are added; old acts are never deleted (they get `status: repealed`).
4. **Cross-jurisdiction synthesis lives downstream.** ONTOLOGY.yaml's `v1_law_pack` is the only index of this pack.

## Outstanding (deferred, not in v1)

- Customary law (Adat Perpatih, Adat Temenggung) — needs witness + ontology, not v1.
- Foreign law — v2 pack.
- Live case law — out of scope; not a law pack concern.
- Cross-border tax treaties — v2 pack.

---

DITEMPA BUKAN DIBERI — The pack is the spine. The canon is the law. 888 is the witness.