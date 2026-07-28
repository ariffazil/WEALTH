import re
from typing import List, Dict, Any

class CertaintyCreepDetector:
    """
    Detects certainty creep: when confidence values or certainty phrasing
    increases over a chronological sequence of statements without an increase
    in underlying evidence or witness count.
    """

    CERTAINTY_KEYWORDS = [
        r"\bdefinitely\b", r"\babsolutely\b", r"\bproven\b", r"\bwithout\b a\b doubt\b",
        r"\bcertainly\b", r"\b100%\b", r"\balways\b", r"\bnever\b", r"\bclear fact\b",
        r"\bobvious\b", r"\bundeniable\b", r"\bindisputable\b"
    ]

    HEDGING_KEYWORDS = [
        r"\bpossibly\b", r"\bmaybe\b", r"\bperhaps\b", r"\bprobably\b", r"\bmight\b",
        r"\bcould\b", r"\bsuggests\b", r"\bindicates\b", r"\bappears\b", r"\blikely\b",
        r"\bconditional\b"
    ]

    def __init__(self):
        self.certainty_patterns = [re.compile(p, re.IGNORECASE) for p in self.CERTAINTY_KEYWORDS]
        self.hedging_patterns = [re.compile(p, re.IGNORECASE) for p in self.HEDGING_KEYWORDS]

    def analyze_statement(self, text: str) -> Dict[str, Any]:
        certainty_count = sum(1 for p in self.certainty_patterns if p.search(text))
        hedging_count = sum(1 for p in self.hedging_patterns if p.search(text))
        
        words = text.split()
        word_count = len(words) if words else 1
        
        # Simple ratio
        certainty_ratio = certainty_count / word_count
        hedging_ratio = hedging_count / word_count
        
        # Raw score between 0.0 and 1.0 representing certainty intensity
        raw_certainty = 0.5 + (certainty_ratio * 5) - (hedging_ratio * 3)
        raw_certainty = max(0.0, min(1.0, raw_certainty))
        
        return {
            "text": text,
            "certainty_count": certainty_count,
            "hedging_count": hedging_count,
            "certainty_ratio": certainty_ratio,
            "raw_certainty": raw_certainty
        }

    def detect(self, statements: List[str], evidence_count: int = 1) -> Dict[str, Any]:
        """
        Analyzes a sequence of statements.
        certainty_creep is flagged if certainty increases while evidence_count remains low.
        """
        if not statements:
            return {"creep_detected": False, "score": 0.0, "trajectory": []}
            
        analyses = [self.analyze_statement(s) for s in statements]
        certainties = [a["raw_certainty"] for a in analyses]
        
        # Check if trend is increasing
        if len(certainties) > 1:
            creep_slope = certainties[-1] - certainties[0]
        else:
            creep_slope = 0.0
            
        # Creep score: slope scaled by low evidence
        evidence_penalty = 1.0 / (evidence_count if evidence_count > 0 else 1)
        creep_score = max(0.0, creep_slope) * evidence_penalty
        
        # Flag if certainty becomes high (e.g. > 0.8) without substantial evidence
        creep_detected = (creep_score > 0.2) or (certainties[-1] >= 0.9 and evidence_count < 3)
        
        return {
            "creep_detected": bool(creep_detected),
            "creep_score": float(creep_score),
            "slope": float(creep_slope),
            "certainties": certainties,
            "prohibited_conclusions": [
                "Do not infer hidden intention or bad faith based on certainty markers."
            ]
        }
