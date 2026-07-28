import sys
import os
import uuid
import yaml
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from detectors.certainty_creep import CertaintyCreepDetector
from detectors.responsibility_diffusion import ResponsibilityDiffusionDetector
from detectors.niat_impact_substitution import NiatImpactSubstitutionDetector
from detectors.trajectory import TrajectoryDetector

mcp = FastMCP("WELL")

# --- Resources ---

@mcp.resource("well://baselines/operator/{op_id}")
def get_operator_baseline(op_id: str) -> str:
    # Simulating a local operator baseline retrieval
    baseline = {
        "op_id": op_id,
        "revision_latency_seconds_baseline": 4.5,
        "response_latency_seconds_baseline": 1.5,
        "baseline_volatility": 0.25,
        "trust_compression_threshold": 0.3
    }
    return yaml.dump(baseline)

@mcp.resource("well://dark-geometry/signals/v1")
def get_dark_signals() -> str:
    signals = {
        "JUDGMENT_COLLAPSE": "Loss of reality contact/denial of negative consequences.",
        "PAIN_ONTOLOGY": "Defensiveness and projection of threat baseline.",
        "FEAR_IDENTITY": "Compliance driven by fear rather than safety.",
        "SABAR_LOSS": "High reaction speed combined with low correction."
    }
    return yaml.dump(signals)

@mcp.resource("well://dark-geometry/benign-alternatives/v1")
def get_benign_alternatives() -> str:
    with open("/root/entropy-integrity/resources/alternative_explanations.yaml", "r") as f:
        return f.read()

@mcp.resource("well://sabar/latency-baseline/v1")
def get_sabar_baseline() -> str:
    return yaml.dump({"revision_latency_target": 5.0, "response_latency_target": 2.0})

@mcp.resource("well://trust/compression-patterns/v1")
def get_trust_compression_patterns() -> str:
    patterns = {
        "all_or_nothing_trust": "Splitting actors into completely good or completely untrustworthy.",
        "universal_threat_language": "Framing disagreements as structural existential threats.",
        "loyalty_testing": "Forcing partners to declare allegiance under pressure."
    }
    return yaml.dump(patterns)

@mcp.resource("well://niat/sovereignty-rule/v1")
def get_niat_sovereignty_rule() -> str:
    rule = {
        "rule": "Never declare intentions false; only evaluate intent-impact divergence.",
        "governing_principle": "Adab outside, Amanah inside."
    }
    return yaml.dump(rule)

@mcp.resource("well://reflection/question-bank/v1")
def get_reflection_bank() -> str:
    with open("/root/entropy-integrity/resources/reflection_prompts.yaml", "r") as f:
        return f.read()

# --- Prompts ---

@mcp.prompt()
def mirror_without_judgment(text: str) -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["mirror_without_judgment"].replace("{{text}}", text)

@mcp.prompt()
def hold_intention_and_impact() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["hold_intention_and_impact"]

@mcp.prompt()
def detect_state_not_trait() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["detect_state_not_trait"]

@mcp.prompt()
def invite_correction_without_shame() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["invite_correction_without_shame"]

@mcp.prompt()
def distinguish_real_threat_from_pain_ontology() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["distinguish_real_threat_from_pain_ontology"]

@mcp.prompt()
def peace_or_suppression() -> str:
    with open("/root/entropy-integrity/resources/prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)
    return prompts["WELL"]["peace_or_suppression"]

# --- Tools ---

@mcp.tool()
def well_assess_sovereign_entropy(mode: str, metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Assess sovereign entropy parameters. Explicit modes:
    privacy_entropy, vitality_entropy, relational_entropy, integrity_entropy.
    Never collapse these into a single scalar.
    """
    # Evaluate values
    privacy = metrics.get("privacy_entropy", 0.5)
    vitality = metrics.get("vitality_entropy", 0.3)
    relational = metrics.get("relational_entropy", 0.2)
    integrity = metrics.get("integrity_entropy", 0.1)

    # Specific analysis per mode
    analysis = ""
    if mode == "privacy_entropy":
        analysis = "High privacy entropy indicates strong resistance to behavioral extraction/profiling (sovereign guard)."
    elif mode == "vitality_entropy":
        analysis = "Vitality entropy reflects physiological and cognitive disorder (metabolic stress)."
    elif mode == "relational_entropy":
        analysis = "Relational entropy indicates trust erosion and feedback loop degradation."
    elif mode == "integrity_entropy":
        analysis = "Integrity entropy measures failure in correction integration and consequence trace visibility."

    return {
        "evaluated_mode": mode,
        "entropy_vector": {
            "privacy_entropy": float(privacy),
            "vitality_entropy": float(vitality),
            "relational_entropy": float(relational),
            "integrity_entropy": float(integrity)
        },
        "mode_analysis": analysis,
        "context": "High privacy entropy can be a positive sovereign signal, while high metabolic/relational entropy can indicate degradation."
    }

@mcp.tool()
def well_dark_geometry_mirror(
    text_or_events: str,
    baseline_ref: str,
    time_window: str,
    vitality_signals: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Analyzes text or conversation events for dark-geometry signals.
    Outputs signals, benign alternatives, counterevidence, trajectory, and reflection questions.
    """
    # Run detectors
    cc_detector = CertaintyCreepDetector()
    rd_detector = ResponsibilityDiffusionDetector()

    cc_result = cc_detector.detect([text_or_events], evidence_count=1)
    rd_result = rd_detector.detect(text_or_events)

    signals = []
    if cc_result["creep_detected"]:
        signals.append("CERTAINTY_IMMUNITY")
    if rd_result["diffusion_detected"]:
        signals.append("RESPONSIBILITY_LAUNDERING")

    # Load resources
    with open("/root/entropy-integrity/resources/alternative_explanations.yaml", "r") as f:
        alts = yaml.safe_load(f)["benign_explanations"]

    with open("/root/entropy-integrity/resources/reflection_prompts.yaml", "r") as f:
        prompts = yaml.safe_load(f)["questions"]

    # Select relevant alternatives and questions
    selected_alts = []
    selected_questions = prompts["feedback"]

    if "CERTAINTY_IMMUNITY" in signals:
        selected_alts.extend(alts.get("high_latency", []))
        selected_questions.extend(prompts["sabar"])
    if "RESPONSIBILITY_LAUNDERING" in signals:
        selected_alts.extend(alts.get("responsibility_shift", []))
        selected_questions.extend(prompts["governance"])

    traj_detector = TrajectoryDetector()
    traj = traj_detector.compute_trajectory(
        current_value=max(cc_result["creep_score"], rd_result["diffusion_score"]),
        baseline_value=0.2,
        history_values=[0.25, 0.3],
        time_window=time_window
    )

    return {
        "status": traj["status"],
        "organ": "WELL",
        "observed_signals": signals,
        "alternative_explanations": selected_alts or ["The subject is communicating in a standard institutional style."],
        "counterevidence": ["The subject used hedging words like 'likely' and 'appears' in sections of the text."],
        "trajectory": traj,
        "reflection_questions": selected_questions,
        "prohibited_conclusions": [
            "Do not infer hidden niat.",
            "Do not classify the actor as evil.",
            "Do not make psychiatric diagnoses."
        ]
    }

@mcp.tool()
def well_sabar_latency(
    stimulus_timestamp: float,
    first_interpretation_timestamp: float,
    response_timestamp: float,
    correction_timestamp: float
) -> Dict[str, Any]:
    """
    Measures temporal compression between stimulus, interpretation, response, and correction.
    Does not say 'loss of sabar' based on speed alone.
    """
    response_latency = response_timestamp - stimulus_timestamp
    revision_latency = correction_timestamp - response_timestamp if correction_timestamp > response_timestamp else 0.0
    
    # Volatility is determined by speed relative to baseline
    baseline_resp = 2.0
    baseline_rev = 5.0
    
    volatility = abs(response_latency - baseline_resp) / baseline_resp
    
    return {
        "response_latency": float(response_latency),
        "revision_latency": float(revision_latency),
        "volatility": float(volatility),
        "baseline_difference": {
            "response_delta": float(response_latency - baseline_resp),
            "revision_delta": float(revision_latency - baseline_rev)
        },
        "context": "Latency alone does not dictate loss of sabar; it must be assessed against verification capacity."
    }

@mcp.tool()
def well_trust_compression(text_or_events: str) -> Dict[str, Any]:
    """
    Detects narrowing trust patterns: threat language, control requests, loyalty testing.
    """
    text_lower = text_or_events.lower()
    
    all_or_nothing = any(w in text_lower for w in ["always", "never", "completely", "totally untrustworthy"])
    threat_lang = any(w in text_lower for w in ["existential threat", "betrayal", "hostile", "attack", "enemy"])
    loyalty_test = any(w in text_lower for w in ["choose a side", "are you with us", "prove your loyalty"])
    control_reqs = any(w in text_lower for w in ["must track", "audit everything", "direct oversight", "verify every second"])

    compression_detected = all_or_nothing or threat_lang or loyalty_test or control_reqs

    return {
        "compression_detected": bool(compression_detected),
        "patterns": {
            "all_or_nothing_trust": bool(all_or_nothing),
            "universal_threat_language": bool(threat_lang),
            "repeated_loyalty_tests": bool(loyalty_test),
            "increasing_control_requests": bool(control_reqs)
        },
        "context": "Trust compression indicates relational narrowing under stress, not a permanent trust status."
    }

@mcp.tool()
def well_niat_impact_mirror(
    declared_intention: str,
    acknowledged_impact: str,
    repair_response: str
) -> Dict[str, Any]:
    """
    Compares declared intention, acknowledged impact, and repair response.
    Never asserts intention was false.
    """
    detector = NiatImpactSubstitutionDetector()
    result = detector.detect(declared_intention, acknowledged_impact, repair_response)

    permitted_msg = "Impact was answered primarily with intention language." if result["substitution_detected"] else "Response addressed impact directly."

    return {
        "substitution_score": result["substitution_score"],
        "permitted_output": permitted_msg,
        "forbidden_output": "The intention was false.",
        "analysis": {
            "intent_word_density": result["intent_word_count"],
            "repair_word_density": result["repair_word_count"]
        }
    }

@mcp.tool()
def well_correction_capacity(
    can_add_context: bool,
    can_revise: bool,
    can_tolerate_ambiguity: bool,
    can_separate_self_from_error: bool,
    can_hear_consequence_without_collapse: bool
) -> Dict[str, Any]:
    """
    Scores observable correctability capability.
    """
    scores = [
        1.0 if can_add_context else 0.0,
        1.0 if can_revise else 0.0,
        1.0 if can_tolerate_ambiguity else 0.0,
        1.0 if can_separate_self_from_error else 0.0,
        1.0 if can_hear_consequence_without_collapse else 0.0
    ]

    correctability_floor = min(scores)

    return {
        "correctability_scores": {
            "can_add_context": can_add_context,
            "can_revise": can_revise,
            "can_tolerate_ambiguity": can_tolerate_ambiguity,
            "can_separate_self_from_error": can_separate_self_from_error,
            "can_hear_consequence_without_collapse": can_hear_consequence_without_collapse
        },
        "correctability_floor": float(correctability_floor),
        "posture": "SUFFICIENT" if correctability_floor > 0.5 else "CRITICAL_CORRECTION_DEGRADATION"
    }

@mcp.tool()
def well_regulation_recovery(
    activation_score: float,
    recovery_duration_seconds: float,
    repair_action_taken: bool
) -> Dict[str, Any]:
    """
    Measures recovery after activation.
    Anger with subsequent repair is better than calm suppression.
    """
    recovery_index = 1.0 - (activation_score * 0.3) + (1.0 if repair_action_taken else 0.0)
    recovery_index = max(0.0, min(1.0, recovery_index / 2.0))

    return {
        "activation_score": activation_score,
        "recovery_duration_seconds": recovery_duration_seconds,
        "repair_action_taken": repair_action_taken,
        "recovery_index": float(recovery_index),
        "status": "HEALTHY_REPAIR" if repair_action_taken else "SUPPRESSED_OR_UNRESOLVED"
    }

if __name__ == "__main__":
    mcp.run()
