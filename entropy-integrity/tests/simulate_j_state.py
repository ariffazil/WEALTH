import sys
import os
import json

# Import fastmcp first to prevent name shadowing from the local 'mcp' directory
try:
    import fastmcp
except ImportError:
    print("Error: fastmcp is not installed in the current environment.")
    sys.exit(1)

# Append specific subdirectories to python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(project_root, "mcp"))
sys.path.append(os.path.join(project_root, "detectors"))

from kernel.server import arif_entropy_observe, arif_j_state_assess

def run_simulation():
    # 1. WELL registers observation of human pressure / responsibility shift
    obs_well = {
        "organ": "WELL",
        "subject_type": "DECISION",
        "subject_ref": "mine_closure_plan_v2",
        "signal_class": ["INFORMATION_LOSS", "CORRECTION_FAILURE"],
        "dark_mode": ["RESPONSIBILITY_LAUNDERING", "JUDGMENT_COLLAPSE"],
        "evidence": {
            "direct_observations": ["Three responses shifted responsibility to the automated closure SOP."],
            "pattern_window": {"time_window": "eval_1", "baseline_delta": 0.4, "recurrence": 2},
            "contradictions": ["Claimed zero risk but turned off downstream monitoring sensor."],
            "counterevidence": ["Company funded basic 1-year bond."],
            "alternative_explanations": ["SOP mandates formal step completion."]
        },
        "epistemic": {"layer": "L3", "confidence": 0.8, "source_independence": 0.75},
        "consequence": {
            "affected_parties": ["Farmers Cooperative B"],
            "reversibility": "IRREVERSIBLE",
            "option_loss": 0.7,
            "feedback_loss": 0.8,
            "consequence_distance": 0.9
        },
        "correction": {
            "challenge_presented": True,
            "response_class": ["DISMISSED", "AUTHORITY_EXPANDED"]
        },
        "prohibited_conclusions": ["hidden niat"]
    }

    obs_res = arif_entropy_observe(obs_well)
    print("1. Observation Registered Ref:", obs_res["observation_ref"])

    # 2. Kernel assesses overall J-State and action posture
    j_res = arif_j_state_assess(
        observation_refs=[obs_res["observation_ref"]],
        decision_ref="mine_closure_plan_v2",
        intended_purpose="Save corporate liability costs",
        claimed_authority="Board mandate",
        affected_parties=["Farmers Cooperative B"],
        action_reversibility="IRREVERSIBLE"
    )

    print("\n2. J-State Assessment Result:")
    print(json.dumps(j_res, indent=2))

if __name__ == "__main__":
    run_simulation()
