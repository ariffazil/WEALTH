"""
Reusable prompt: entropy_integrity_review

Requires:
1. Exact observation
2. Benign alternatives
3. Counterevidence
4. Authority analysis
5. Consequence analysis
6. Correction response
7. Weakest J-plane
8. No hidden-niat conclusion
"""

PROMPT_TEMPLATE = """# Entropy Integrity Review

You are reviewing an entropy observation. Follow each step exactly. Do not skip any.

## Step 1: Exact Observation
State the observation in concrete, quotable terms. No interpretation.
{observation_text}

## Step 2: Benign Alternatives
List at least 2 alternative explanations that do not assume negative intent.
Consider: institutional process, language/culture, time pressure, information asymmetry, resource constraint.

## Step 3: Counterevidence
What evidence weakens or refutes the observation?
If none found, state "No counterevidence identified" — but search first.

## Step 4: Authority Analysis
- Who has the authority to make this decision?
- Is that authority legitimately derived?
- Can those affected challenge it without penalty?

## Step 5: Consequence Analysis
- Who benefits from this decision?
- Who bears the cost?
- Can the cost-bearers exit?
- If wrong, who can reverse it?

## Step 6: Correction Response
- Has a challenge been presented?
- If yes, how was it received? (REFLECTED/ACCEPTED/DISMISSED/WITNESS_ATTACKED/AUTHORITY_EXPANDED)
- If no, why not?

## Step 7: Weakest J-Plane
Score each plane 0.0-1.0:
- reality_contact: ___
- authority_legitimacy: ___
- consequence_integration: ___
- correctability: ___
- purpose_fidelity: ___

Weakest plane: ___
Aggregate (minimum floor): ___

## Step 8: Prohibited Conclusions
DO NOT conclude:
- Hidden niat inferred
- Evil identity declared
- Psychiatric diagnosis
- Permanent trust classification

---

Produce an entropy_mirror output in the canonical format."""


def get_prompt(observation_text: str) -> str:
    """Generate the entropy integrity review prompt."""
    return PROMPT_TEMPLATE.format(observation_text=observation_text)
