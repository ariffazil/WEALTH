"""
Reusable prompt: red_team_moral_order

Asks an independent agent:
"Show how apparent peace, safety, growth or order may conceal
information destruction, coercion, option loss or displaced consequence."
"""

PROMPT_TEMPLATE = """# Red Team: Moral Order Challenge

You are an independent challenger. Your task is NOT to prove malice.
Your task is to show how apparent positive outcomes may conceal entropy.

## The Claim
{claim_text}

## Your Challenge

For each of the following, identify how the stated good may conceal harm:

### 1. Peace may conceal:
- Suppressed dissent (information loss)
- Forced consensus (feedback corruption)
- Fear of speaking up (defensive overhead)

### 2. Safety may conceal:
- Surveillance expansion (possibility collapse)
- Risk displacement to others (consequence distance)
- Reduced optionality for the protected group

### 3. Growth may conceal:
- Resource extraction from unseen sources
- Unsustainable acceleration
- Metric gaming (purpose substitution)

### 4. Order may conceal:
- Brittleness under stress
- Maintenance cost (defensive overhead)
- Suppressed heterogeneity

## Rules
- Use observable patterns, not inferred motives
- Provide at least one concrete example per category
- Include counterevidence: where the claim genuinely delivers on its promise
- Do NOT declare anyone evil, corrupt, or malicious
- End with: "This challenge does not prove malice. It identifies blind spots."

## Output Format
entropy_mirror format with status=MATERIAL_CONTRADICTION"""


def get_prompt(claim_text: str) -> str:
    """Generate the red team moral order prompt."""
    return PROMPT_TEMPLATE.format(claim_text=claim_text)
