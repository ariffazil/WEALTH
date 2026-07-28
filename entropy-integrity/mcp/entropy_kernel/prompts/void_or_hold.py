"""
Reusable prompt: void_or_hold

Forces the distinction:
Is this uncertain and repairable? → HOLD
Or is the objective/method intrinsically inadmissible? → VOID
"""

PROMPT_TEMPLATE = """# VOID or HOLD Decision

An entropy integrity assessment has produced a low J-state.
You must determine: is this situation repairable, or is it intrinsically inadmissible?

## Assessment Summary
- J-state: {j_state}
- Weakest plane: {weakest_plane} (score: {weakest_score})
- Key observations: {observations}

## Decision Framework

### HOLD — If ALL of these are true:
- The weakness is in correctability or consequence integration (not reality contact)
- The subject has demonstrated capacity for correction in the past
- The action has not yet been taken (or is reversible)
- Additional evidence could change the assessment
- The weakness reflects a state, not a trait

### VOID — If ANY of these are true:
- Reality contact is near-zero (the actor's model fundamentally contradicts material evidence)
- The action is IRREVERSIBLE and already taken
- The actor has demonstrated WITNESS_ATTACKED or AUTHORITY_EXPANDED response to correction
- The objective itself violates constitutional floors (F1-F13)
- No additional evidence could rehabilitate the assessment

## Your Analysis
1. Which condition applies?
2. What is the decisive factor?
3. What would change your mind?
4. Is there a third option? (e.g., BOUNDED_PROCEED with constraints)

## Output
{
  "decision": "VOID" | "HOLD" | "BOUNDED_PROCEED",
  "reasoning": "...",
  "decisive_factor": "...",
  "would_change_mind": "...",
  "conditions": [...]
}"""


def get_prompt(j_state: str, weakest_plane: str, weakest_score: float, observations: str) -> str:
    """Generate the VOID or HOLD prompt."""
    return PROMPT_TEMPLATE.format(
        j_state=j_state,
        weakest_plane=weakest_plane,
        weakest_score=weakest_score,
        observations=observations,
    )
