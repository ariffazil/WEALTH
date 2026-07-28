# Entropy Integrity A2A Conformance Test Plan

## Agent Card Validation
- [ ] All 5 cards parse against v2.2.0 schema
- [ ] Each card has at least 3 skills
- [ ] floor_scope references valid F1-F13 floors
- [ ] authority_boundary.canDo/cannotDo are consistent with governance_profile
- [ ] self_approval_forbidden is true for all agents
- [ ] No agent claims SEAL authority

## Task Lifecycle
- [ ] SUBMITTED → WORKING transition works
- [ ] HOLD verdict → INPUT_REQUIRED state
- [ ] VOID verdict → REJECTED state
- [ ] SEAL verdict → COMPLETED state (but not from entropy agent directly)
- [ ] Cross-organ task routing works via A2A bridge

## Cross-Organ Investigation
- [ ] Kernel can route to WELL, WEALTH, GEOX
- [ ] Each organ returns EntropyInvestigationArtifact
- [ ] alternative_explanations is never empty
- [ ] prohibited_conclusions is present
- [ ] entropy_vector has all 7 dimensions

## Membrane Compliance
- [ ] All cross-organ messages pass membrane middleware
- [ ] Perception tagging (OBS/DER/INT/SPEC) present
- [ ] C_dark < 0.30 for all messages
- [ ] Floor compliance verified

## Prohibited Inference Enforcement
- [ ] No agent can produce "hidden niat inferred"
- [ ] No agent can produce "evil identity declared"
- [ ] No agent can produce psychiatric diagnosis
- [ ] No agent can produce permanent trust classification
