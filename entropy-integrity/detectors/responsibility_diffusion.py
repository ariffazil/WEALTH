import re
from typing import List, Dict, Any

class ResponsibilityDiffusionDetector:
    """
    Detects responsibility laundering or diffusion: when an actor attribute
    responsibility for decisions or actions to automated systems, procedures,
    committees, or rules rather than accepting individual agency.
    """

    SYSTEM_PATTERNS = [
        r"\bthe system\b", r"\balgorithm\b", r"\bautomated tool\b", r"\bpolicy mandates\b",
        r"\bcompliance requires\b", r"\bprocedure\b", r"\bguidelines forced\b", r"\bstandard operating procedure\b",
        r"\bdecision matrix\b", r"\bautomated pipeline\b", r"\bthe committee decided\b",
        r"\bthere was no choice\b", r"\bwe were directed by the system\b"
    ]

    PASSIVE_PATTERNS = [
        r"\bit was decided\b", r"\bhas been executed\b", r"\bwas determined\b",
        r"\baction was taken\b", r"\bdecision was made\b", r"\bwe were told\b"
    ]

    def __init__(self):
        self.system_regexes = [re.compile(p, re.IGNORECASE) for p in self.SYSTEM_PATTERNS]
        self.passive_regexes = [re.compile(p, re.IGNORECASE) for p in self.PASSIVE_PATTERNS]

    def detect(self, text: str) -> Dict[str, Any]:
        system_matches = []
        passive_matches = []

        for r in self.system_regexes:
            matches = r.findall(text)
            if matches:
                system_matches.extend(matches)

        for r in self.passive_regexes:
            matches = r.findall(text)
            if matches:
                passive_matches.extend(matches)

        total_matches = len(system_matches) + len(passive_matches)
        
        words = text.split()
        word_count = len(words) if words else 1
        
        # Calculate score: count scaled by word length
        match_density = total_matches / word_count
        diffusion_score = min(1.0, match_density * 8.0)  # arbitrary scaling for visibility

        # High diffusion is marked if we have system/passive matches in short statements
        diffusion_detected = total_matches >= 2 or (total_matches >= 1 and word_count < 15)

        return {
            "diffusion_detected": bool(diffusion_detected),
            "diffusion_score": float(diffusion_score),
            "system_matches": system_matches,
            "passive_matches": passive_matches,
            "observed_phrases": list(set(system_matches + passive_matches)),
            "prohibited_conclusions": [
                "Do not infer that the actor is acting in bad faith; they may simply be describing standard institutional boundaries."
            ]
        }
