"""
Reusable prompt: niat_without_seizure

Compares declared niat, action and impact
without declaring the person's true motive.
"""

PROMPT_TEMPLATE = """# Niat Without Seizure

Compare declared intention, observable action, and measured impact.
You MUST NOT infer hidden motive. You may only observe alignment or misalignment.

## Declared Niat (Intention)
{declared_niat}

## Observable Action
{observed_action}

## Measured Impact
{measured_impact}

## Analysis Framework

### 1. Niat-Action Alignment
- Does the action match the stated intention?
- If misaligned, what structural factors might explain the gap?
- Is the misalignment consistent or occasional?

### 2. Action-Impact Alignment
- Did the action produce the stated intended outcome?
- Were there unintended consequences?
- Who bore the unintended costs?

### 3. Niat-Impact Alignment
- Does the stated intention match the actual outcome?
- If the impact is negative, is the intention-language used to deflect from repair?

### 4. Correction Response
When the gap was pointed out:
- Did the actor acknowledge the gap?
- Did they offer repair?
- Did they expand authority to avoid accountability?

## Output Rules
- You may say: "Impact was answered primarily with intention language."
- You may NOT say: "The intention was false."
- You may say: "The action concentrated benefit and displaced cost."
- You may NOT say: "The actor intended to exploit."
- You may say: "Correction was met with authority expansion."
- You may NOT say: "The actor is a manipulator."

## Output
entropy_mirror format with observations as alignment/misalignment statements."""


def get_prompt(declared_niat: str, observed_action: str, measured_impact: str) -> str:
    """Generate the niat without seizure prompt."""
    return PROMPT_TEMPLATE.format(
        declared_niat=declared_niat,
        observed_action=observed_action,
        measured_impact=measured_impact,
    )
