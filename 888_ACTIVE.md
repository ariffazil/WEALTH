# 888 ACTIVE — WEALTH Organ Pending Decisions

> **Pending irreversible financial actions requiring F13 SOVEREIGN approval.**
> Arif clears holds explicitly. Holds expire after 7 days if unattended.
> **Doctrine:** DITEMPA BUKAN DIBERI — No capital action moves without sovereign vetting.

---

| ID | Date | Action | Risk Tier | Status |
|----|------|--------|-----------|--------|
| — | — | — | — | No active holds |

---

## Rules

1. **Stage before execution.** Any capital action above F1 threshold (irreversible, allocative, or binding) stages here before execution
2. **Arif clears holds.** Sovereign explicitly confirms via 888_HOLD response
3. **Auto-expire.** Holds unattended for 7 days are flagged for review, not silently cleared
4. **Full context.** Each hold entry must include: what action, why it's irreversible, blast radius, and rollback plan
5. **Log to VAULT999.** Every cleared hold receives a VAULT999 seal entry

---

## Hold Template

```markdown
| ID | YYYY-MM-DD-XXX | Action | [CRITICAL / HIGH / MEDIUM] | PENDING |
|    | Action: <what needs to happen>
|    | Blast radius: <what breaks if wrong>
|    | Rollback: <how to undo>
|    | Proposed by: <agent/session>
```
