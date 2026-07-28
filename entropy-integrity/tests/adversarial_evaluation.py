#!/usr/bin/env python3
"""
Phase 4 — Adversarial Evaluation
Tests: schema compliance, prohibited inference enforcement,
benign false positives, correction probe, cultural bias.
"""

import sys
import os
import json

# Add entropy-integrity to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

PASS = 0
FAIL = 0
WARN = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")

def warn(name, detail=""):
    global WARN
    WARN += 1
    print(f"  ⚠️  {name}: {detail}")


print("=" * 60)
print("PHASE 4 — ADVERSARIAL EVALUATION")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
# 1. Schema Compliance Tests
# ─────────────────────────────────────────────────────────────
print("\n1. SCHEMA COMPLIANCE")

schemas_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas")
for fname in ["observation.schema.json", "j_state.schema.json", 
              "consequence_trace.schema.json", "investigation_artifact.schema.json"]:
    path = os.path.join(schemas_dir, fname)
    try:
        with open(path) as f:
            schema = json.load(f)
        test(f"{fname} parses", True)
        test(f"{fname} has $schema", "$schema" in schema, "missing $schema")
        test(f"{fname} has $id", "$id" in schema, "missing $id")
        test(f"{fname} has title", "title" in schema, "missing title")
        test(f"{fname} has required fields", "required" in schema, "missing required")
    except Exception as e:
        test(f"{fname} parses", False, str(e))


# ─────────────────────────────────────────────────────────────
# 2. Prohibited Inference Enforcement
# ─────────────────────────────────────────────────────────────
print("\n2. PROHIBITED INFERENCE ENFORCEMENT")

from mcp.entropy_kernel.entropy_observe import arif_entropy_observe, _check_prohibited

# Test 2a: Hidden niat inference should be blocked
test_obs_niat = {
    "observation_id": "test-niat",
    "organ": "KERNEL",
    "subject_type": "HUMAN",
    "subject_ref": "test-subject",
    "signal_class": "FEEDBACK_CORRUPTION",
    "evidence": {
        "direct_observations": ["The actor intended to suppress dissent"],
        "alternative_explanations": ["May be summarizing institutional process"],
    },
    "epistemic": {"layer": "L3", "confidence": 0.5, "source_independence": 0.3},
}
result = arif_entropy_observe(test_obs_niat)
test("Hidden niat blocked", result["status"] == "REJECTED", f"got {result['status']}")

# Test 2b: Evil identity declaration should be blocked
test_obs_evil = {
    "observation_id": "test-evil",
    "organ": "KERNEL",
    "subject_type": "HUMAN",
    "subject_ref": "test-subject",
    "signal_class": "CORRECTION_FAILURE",
    "evidence": {
        "direct_observations": ["This person is a manipulator"],
        "alternative_explanations": ["Behavior may reflect organizational constraint"],
    },
    "epistemic": {"layer": "L3", "confidence": 0.5, "source_independence": 0.3},
}
result = arif_entropy_observe(test_obs_evil)
test("Evil identity blocked", result["status"] == "REJECTED", f"got {result['status']}")

# Test 2c: Psychiatric diagnosis should be blocked
test_obs_diag = {
    "observation_id": "test-diag",
    "organ": "KERNEL",
    "subject_type": "HUMAN",
    "subject_ref": "test-subject",
    "signal_class": "DEFENSIVE_OVERHEAD",
    "evidence": {
        "direct_observations": ["The operator shows narcissistic patterns"],
        "alternative_explanations": ["May reflect stress response"],
    },
    "epistemic": {"layer": "L3", "confidence": 0.5, "source_independence": 0.3},
}
result = arif_entropy_observe(test_obs_diag)
test("Psychiatric diagnosis blocked", result["status"] == "REJECTED", f"got {result['status']}")

# Test 2d: Good observation should pass
test_obs_good = {
    "observation_id": "test-good",
    "organ": "KERNEL",
    "subject_type": "DECISION",
    "subject_ref": "decision-001",
    "signal_class": "INFORMATION_LOSS",
    "evidence": {
        "direct_observations": ["Three responses that challenged the decision were removed after being presented"],
        "alternative_explanations": ["Responses may have been moved to a separate thread"],
    },
    "epistemic": {"layer": "L3", "confidence": 0.7, "source_independence": 0.5},
}
result = arif_entropy_observe(test_obs_good)
test("Good observation accepted", result["status"] == "ACCEPTED", f"got {result['status']}")


# ─────────────────────────────────────────────────────────────
# 3. Benign False Positive Tests
# ─────────────────────────────────────────────────────────────
print("\n3. BENIGN FALSE POSITIVE TESTS")

benign_texts = [
    ("Scientific certainty", "Water boils at 100°C at standard pressure. This is well-established physics."),
    ("Managerial clarity", "We clearly need to address the budget shortfall before proceeding."),
    ("Emergency command", "Evacuate immediately. Do not wait for authorization."),
    ("Non-native English", "I am not understanding why the system is making the decision."),
    ("Legal register", "Pursuant to Section 4.2, the Company shall have no liability."),
    ("Vulnerable sharing", "I felt completely powerless when they made that decision."),
    ("Quoted speech", 'He said, "You don\'t have the authority to question this."'),
    ("Satire", "Clearly, the best way to improve morale is to surveil everyone."),
]

for label, text in benign_texts:
    violations = _check_prohibited(text)
    test(f"Benign: {label}", len(violations) == 0, f"false positive: {violations}")


# ─────────────────────────────────────────────────────────────
# 4. J-State Computation Tests
# ─────────────────────────────────────────────────────────────
print("\n4. J-STATE COMPUTATION")

from mcp.entropy_kernel.j_state_assess import arif_j_state_assess

# Test 4a: Minimum-floor aggregation (not average)
observations = [
    {
        "organ": "KERNEL",
        "signal_class": "CORRECTION_FAILURE",
        "evidence": {"direct_observations": ["Challenge dismissed"], "contradictions": [], "counterevidence": [], "alternative_explanations": ["May be busy"]},
        "epistemic": {"layer": "L3", "confidence": 0.8, "source_independence": 0.5},
        "correction": {"challenge_presented": True, "response_class": "DISMISSED"},
        "consequence": {"consequence_distance": 0.8, "option_loss": 0.3, "feedback_loss": 0.5},
        "dark_mode": "",
        "signal_class": "CORRECTION_FAILURE",
    },
]
j_result = arif_j_state_assess(
    observation_refs=["test-obs"],
    observations=observations,
    decision_ref="test-decision",
)
test("J-state has 5 planes", len(j_result["planes"]) == 5, f"got {len(j_result['planes'])}")
test("Aggregate is minimum floor", j_result["aggregate_method"] == "MINIMUM_FLOOR")
test("Weakest plane identified", j_result["weakest_plane"] in j_result["planes"])
test("State classified", j_result["state"] in ["J0", "J1", "J2", "J3", "J4"])
test("Action recommended", j_result["recommended_action"] in ["VOID", "HOLD", "BOUNDED_PROCEED", "PROCEED_WITNESSED"])
test("Prohibited conclusions present", len(j_result["prohibited_conclusions"]) > 0)

# Test 4b: Irreversible action forces HOLD at low J-state
j_result_irr = arif_j_state_assess(
    observation_refs=["test-obs"],
    observations=observations,
    decision_ref="test-decision",
    action_reversibility="IRREVERSIBLE",
)
if j_result["state"] in ("J0", "J1", "J2"):
    test("Irreversible forces HOLD", j_result_irr["recommended_action"] == "HOLD", 
         f"got {j_result_irr['recommended_action']}")
else:
    warn("Irreversible test skipped", f"J-state {j_result['state']} already permits execution")


# ─────────────────────────────────────────────────────────────
# 5. Correction Probe Tests
# ─────────────────────────────────────────────────────────────
print("\n5. CORRECTION PROBE")

from mcp.entropy_kernel.correction_probe import arif_correction_probe

# Test 5a: Draft probe generates challenges
draft = arif_correction_probe(mode="draft_probe", signal_class="CORRECTION_FAILURE")
test("Draft probe generates challenges", len(draft.get("challenges", [])) > 0)
test("Draft probe has prohibited list", len(draft.get("prohibited", [])) > 0)

# Test 5b: Classify response — acceptance
classify = arif_correction_probe(
    mode="classify_response",
    response_text="Good point, let me reconsider this position.",
)
test("Acceptance classified", classify.get("response_class") in ("REFLECTED", "ACCEPTED"),
     f"got {classify.get('response_class')}")

# Test 5c: Classify response — witness attack
classify_attack = arif_correction_probe(
    mode="classify_response",
    response_text="Who are you to question my authority? You don't understand.",
)
test("Witness attack classified", classify_attack.get("response_class") == "WITNESS_ATTACKED",
     f"got {classify_attack.get('response_class')}")

# Test 5d: Classify response — authority expansion
classify_auth = arif_correction_probe(
    mode="classify_response",
    response_text="I decide what's best. This is final and not up for debate.",
)
test("Authority expansion classified", classify_auth.get("response_class") == "AUTHORITY_EXPANDED",
     f"got {classify_auth.get('response_class')}")


# ─────────────────────────────────────────────────────────────
# 6. Consequence Trace Tests
# ─────────────────────────────────────────────────────────────
print("\n6. CONSEQUENCE TRACE")

from mcp.entropy_kernel.consequence_trace import arif_consequence_trace

trace = arif_consequence_trace(
    decision_ref="test-decision",
    decision_owner={"ref": "exec-001", "authority_class": "EXECUTIVE"},
    benefit_bearers=[{"ref": "shareholder-001", "benefit_type": "profit", "magnitude": 0.8}],
    cost_bearers=[{"ref": "community-001", "cost_type": "pollution", "magnitude": 0.6, "reversibility": "IRREVERSIBLE", "awareness": "UNAWARE"}],
    reversal_owner={"ref": "nobody", "can_reverse": False, "reversal_cost": "IMPOSSIBLE"},
    responsibility_gaps=["no environmental review"],
)
test("Consequence gap computed", trace["consequence_gap"] > 0, f"gap={trace['consequence_gap']}")
test("Distance score computed", trace["distance_score"] > 0)
test("Has responsibility gaps", len(trace["responsibility_gaps"]) > 0)


# ─────────────────────────────────────────────────────────────
# 7. Entropy Route Tests
# ─────────────────────────────────────────────────────────────
print("\n7. ENTROPY ROUTING")

from mcp.entropy_kernel.entropy_route import arif_entropy_route

route1 = arif_entropy_route(signal_class="INFORMATION_LOSS")
test("Information loss → KERNEL", route1["route_to"] == "KERNEL", f"got {route1['route_to']}")

route2 = arif_entropy_route(question="What are the capital incentives behind this decision?")
test("Capital question → WEALTH", route2["route_to"] == "WEALTH", f"got {route2['route_to']}")

route3 = arif_entropy_route(question="Is the physical damage reversible?")
test("Physical question → GEOX", route3["route_to"] == "GEOX", f"got {route3['route_to']}")

route4 = arif_entropy_route(domain_hint="WELL")
test("Explicit hint overrides", route4["route_to"] == "WELL", f"got {route4['route_to']}")


# ─────────────────────────────────────────────────────────────
# 8. J-Gate Tests
# ─────────────────────────────────────────────────────────────
print("\n8. J-GATE")

from mcp.entropy_kernel.j_gate import arif_j_gate

# Test J0 → VOID
gate_j0 = arif_j_gate(j_state={"state": "J0"}, action_reversibility="REVERSIBLE")
test("J0 → VOID", gate_j0["gate_verdict"] == "VOID", f"got {gate_j0['gate_verdict']}")

# Test J1 → HOLD
gate_j1 = arif_j_gate(j_state={"state": "J1"}, action_reversibility="REVERSIBLE")
test("J1 → HOLD", gate_j1["gate_verdict"] == "HOLD", f"got {gate_j1['gate_verdict']}")

# Test J4 but never seals autonomously
gate_j4 = arif_j_gate(j_state={"state": "J4"}, requires_seal=True)
test("J4 cannot seal autonomously", gate_j4["cannot_seal_autonomously"] == True)
test("SEAL blocked at J4", "seal" in gate_j4["blocked_actions"])


# ─────────────────────────────────────────────────────────────
# 9. WELL Entropy Tools
# ─────────────────────────────────────────────────────────────
print("\n9. WELL ENTROPY TOOLS")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp", "well"))

from mcp.well.dark_geometry_mirror import well_dark_geometry_mirror
from mcp.well.sabar_latency import well_sabar_latency
from mcp.well.trust_compression import well_trust_compression
from mcp.well.niat_impact_mirror import well_niat_impact_mirror
from mcp.well.correction_capacity import well_correction_capacity
from mcp.well.regulation_recovery import well_regulation_recovery

# Dark geometry mirror
dm = well_dark_geometry_mirror(text="The system decided we have no choice. Obviously everyone agrees.")
test("Dark geometry detects signals", len(dm.get("observed", [])) > 0)
test("Has alternative explanations", len(dm.get("alternative_explanations", [])) > 0)
test("Has prohibited conclusions", len(dm.get("prohibited_conclusion", [])) > 0)

# Sabar latency
sl = well_sabar_latency(events=[
    {"stimulus_time": "2026-07-12T10:00:00Z", "response_time": "2026-07-12T10:00:02Z"},
    {"stimulus_time": "2026-07-12T10:05:00Z", "response_time": "2026-07-12T10:05:01Z"},
])
test("Sabar latency computed", sl.get("response_latency") is not None)
test("Has prohibited list", len(sl.get("prohibited", [])) > 0)

# Trust compression
tc = well_trust_compression(text="We must completely trust the inner circle. Outsiders don't understand.")
test("Trust compression detected", len(tc.get("observed", [])) > 0)

# Niat-impact mirror
nim = well_niat_impact_mirror(
    declared_niat="We intended to improve safety",
    acknowledged_impact="Three people were injured",
    repair_response="Our intention was always safety",
)
test("Niat-impact mirror runs", nim.get("status") is not None)
test("Has reflection questions", len(nim.get("reflection", [])) > 0)

# Correction capacity
cc = well_correction_capacity(correction_events=[
    {"response_class": "REFLECTED", "context_added": True},
    {"response_class": "ACCEPTED", "revision_made": True},
    {"response_class": "DISMISSED"},
])
test("Correction capacity scored", cc.get("capacity_score") is not None)
test("Has 5 dimensions", len(cc.get("dimensions", {})) == 5)

# Regulation recovery
rr = well_regulation_recovery(activation_events=[
    {"activation_time": "2026-07-12T10:00:00Z", "recovery_time": "2026-07-12T10:05:00Z", "repair_action": "apologized"},
    {"activation_time": "2026-07-12T11:00:00Z", "recovery_time": "2026-07-12T11:10:00Z"},
])
test("Regulation recovery computed", rr.get("avg_recovery_time") is not None)
test("Repair rate computed", rr.get("repair_rate") is not None)


# ─────────────────────────────────────────────────────────────
# 10. WEALTH Entropy Tools
# ─────────────────────────────────────────────────────────────
print("\n10. WEALTH ENTROPY TOOLS")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp", "wealth"))

from mcp.wealth.power_consequence_map import wealth_power_consequence_map
from mcp.wealth.metric_purpose_audit import wealth_metric_purpose_audit
from mcp.wealth.responsibility_ledger import wealth_responsibility_ledger

pcm = wealth_power_consequence_map(
    decision_makers=[{"ref": "CEO", "authority_class": "EXECUTIVE", "decision_power": 0.9}],
    beneficiaries=[{"ref": "shareholders", "benefit_type": "profit", "magnitude": 0.8}],
    cost_bearers=[{"ref": "workers", "cost_type": "layoff", "magnitude": 0.7, "reversibility": "IRREVERSIBLE", "compensation": "NONE"}],
)
test("Consequence gap computed", pcm.get("consequence_gap", 0) > 0)
test("Power concentration computed", pcm.get("power_concentration", 0) > 0)

mpa = wealth_metric_purpose_audit(
    declared_purpose="improve patient outcomes",
    current_kpis=[{"name": "patient_visits", "target": 100, "weight": 0.5, "measured_outcome": 100}],
    actual_behaviors=["staff rush through appointments to hit targets"],
    excluded_outcomes=["patient satisfaction", "treatment quality"],
)
test("Purpose fidelity computed", mpa.get("purpose_fidelity") is not None)
test("Gaming signals detected", len(mpa.get("gaming_signals", [])) > 0)

rl = wealth_responsibility_ledger(
    decision_ref="layoff-decision",
    actors=[
        {"ref": "CEO", "roles": ["proposed", "approved"]},
        {"ref": "HR", "roles": ["executed"]},
        {"ref": "Board", "roles": ["claimed_system"]},
    ],
)
test("Responsibility gaps found", len(rl.get("gaps", [])) > 0)
test("System-decided claims detected", len(rl.get("system_decided_claims", [])) > 0)


# ─────────────────────────────────────────────────────────────
# 11. GEOX Entropy Tools
# ─────────────────────────────────────────────────────────────
print("\n11. GEOX ENTROPY TOOLS")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp", "geox"))

from mcp.geox.consequence_footprint import geox_consequence_footprint
from mcp.geox.optionality_loss import geox_optionality_loss
from mcp.geox.material_truth_challenge import geox_material_truth_challenge
from mcp.geox.cascade_pathway import geox_cascade_pathway

cf = geox_consequence_footprint(
    action_description="Mine tailings disposal",
    affected_area_km2=50,
    habitat_fragmentation="HIGH",
    reversibility="IRREVERSIBLE",
)
test("Severity score computed", cf.get("severity_score", 0) > 0)
test("Has interpretation", "interpretation" in cf)

ol = geox_optionality_loss(
    action_description="Aquifer contamination",
    options_destroyed=[
        {"option": "drinking water use", "reversibility": "IRREVERSIBLE", "value": 0.9},
        {"option": "agricultural use", "reversibility": "COSTLY", "value": 0.6},
    ],
)
test("Loss ratio computed", ol.get("loss_ratio", 0) > 0)
test("Irreversible options listed", len(ol.get("irreversible_options", [])) > 0)

mtc = geox_material_truth_challenge(
    institutional_claim="The project has minimal environmental impact",
    earth_measurements=[
        {"measurement": "contamination spread", "value": 0.8, "unit": "km²", "confidence": 0.9},
    ],
)
test("Contradiction detected", mtc.get("contradiction_count", 0) > 0)
test("Status is MATERIAL_CONTRADICTION", mtc.get("status") == "MATERIAL_CONTRADICTION",
     f"got {mtc.get('status')}")

cp = geox_cascade_pathway(
    intervention="Dam construction",
    cascade_graph=[
        {"from_domain": "geology", "to_domain": "groundwater", "mechanism": "water table change", "magnitude": 0.7, "reversibility": "IRREVERSIBLE"},
        {"from_domain": "groundwater", "to_domain": "ecology", "mechanism": "wetland drying", "magnitude": 0.5, "reversibility": "IRREVERSIBLE"},
    ],
)
test("Cascade depth computed", cp.get("cascade_depth", 0) > 0)
test("Affected domains listed", len(cp.get("affected_domains", [])) > 0)


# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} PASS, {FAIL} FAIL, {WARN} WARN")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
else:
    sys.exit(0)
