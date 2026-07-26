# agent-cards/ — Draft persona cards (NOT public discovery)

> **DRAFT_ONLY** — none of the cards in this directory are part of the WEALTH
> organ's **public** discovery surface. They are **draft** personas living under
> the WEALTH organ, awaiting F13 SEAL before any deployment.

## What lives here

| File | Persona | Status | Public route? |
|------|---------|--------|---------------|
| `makcikgpt.json` | MakcikGPT Investigative Persona | `DRAFT_ONLY` (per `capabilities.draft_only: true` and `scopes: DRAFT_ONLY`) | **No** |

## What does NOT live here

The **organ public agent card** lives at `/.well-known/agent.json` and is the
sole canonical card advertised by:

- `public/sitemap.xml`
- `public/robots.txt`
- `/llms.txt` (the organ manifest)
- `/.well-known/mcp.json`

If you add a new persona card under `agent-cards/`, it MUST:

1. Set `capabilities.draft_only: true`.
2. Set `scopes` to include `DRAFT_ONLY`.
3. Reference this README in its `metadata.draft_only_under` field.
4. **Not** be referenced from any of the public discovery files above.

## Why this separation matters

The makcikgpt subagent addresses investigatory work with defamation risk
("kartel struktur" not "kartel") and must clear F13 sovereign seal before any
publication. Mixing it into the public organ sitemap would (a) advertise an
unsealed draft as if it were live, (b) pollute the capital-intelligence organ's
discovery surface with a Bahasa-Makcik persona scope, and (c) violate F1 AMANAH
by collapsing reversible draft state into irreversible public claims.

DITEMPA BUKAN DIBERI — Forged, Not Given.