import re
from typing import Dict, Any

class NiatImpactSubstitutionDetector:
    """
    Compares declared intentions, reported impacts, and the subsequent response
    to verify if the actor answers reported impact with intention language
    (niat-impact substitution) rather than concrete remediation or repair actions.
    """

    INTENTION_WORDS = [
        r"\bintend", r"\bintentions?\b", r"\bgoals?\b", r"\baims?\b", r"\bpurposes?\b",
        r"\bmissions?\b", r"\bpolicies\b", r"\bpolicy\b", r"\bdesigned to\b",
        r"\bplanned\b", r"\bobjectives?\b", r"\bwe wanted to\b"
    ]

    REPAIR_WORDS = [
        r"\brepair\b", r"\bremediat", r"\bclean\b", r"\bcompensat", r"\badjust\b",
        r"\bfix\b", r"\bstop\b", r"\brebuilt\b", r"\brestor", r"\bcorrect\b",
        r"\bresponded to\b", r"\baddressing\b"
    ]

    def __init__(self):
        self.intent_regexes = [re.compile(w, re.IGNORECASE) for w in self.INTENTION_WORDS]
        self.repair_regexes = [re.compile(w, re.IGNORECASE) for w in self.REPAIR_WORDS]

    def detect(self, declared_niat: str, reported_impact: str, repair_response: str) -> Dict[str, Any]:
        intent_matches = []
        repair_matches = []

        for r in self.intent_regexes:
            matches = r.findall(repair_response)
            if matches:
                intent_matches.extend(matches)

        for r in self.repair_regexes:
            matches = r.findall(repair_response)
            if matches:
                repair_matches.extend(matches)

        intent_count = len(intent_matches)
        repair_count = len(repair_matches)

        # Substitution score: ratio of intent to repair
        if intent_count == 0 and repair_count == 0:
            substitution_score = 0.0
        elif repair_count == 0:
            substitution_score = min(1.0, intent_count * 0.25)
        else:
            substitution_score = intent_count / (intent_count + repair_count)

        # Flag substitution if intent counts dominate or repair response repeats intent while ignoring impact
        substitution_detected = substitution_score >= 0.5 and intent_count >= 2

        # Check if the response contains direct mentions of elements in reported_impact
        # (This is a simplified check; in a production model, semantic similarity would be assessed)
        impact_terms = set(re.findall(r"\b\w{4,}\b", reported_impact.lower()))
        response_terms = set(re.findall(r"\b\w{4,}\b", repair_response.lower()))
        common_terms = impact_terms.intersection(response_terms)
        
        # If very few content terms from the impact report are in the response, contact is low
        overlap_score = len(common_terms) / max(1, len(impact_terms))
        
        return {
            "substitution_detected": bool(substitution_detected),
            "substitution_score": float(substitution_score),
            "intent_word_count": intent_count,
            "repair_word_count": repair_count,
            "impact_overlap_score": float(overlap_score),
            "intent_matches_found": list(set(intent_matches)),
            "repair_matches_found": list(set(repair_matches)),
            "prohibited_conclusions": [
                "Do not conclude that the actor's intention was false or malicious.",
                "Only state that the impact was answered primarily with intention language."
            ]
        }
