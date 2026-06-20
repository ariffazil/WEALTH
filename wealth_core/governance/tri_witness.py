"""
WEALTH Core — Tri-Witness Validation.

F3 WITNESS: Tri-witness validation: Human, AI, Earth.
Every capital seal must carry witness attestation from all three.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriWitness:
    """
    Tri-witness validation for capital seals.
    
    Three witnesses must attest:
    - human: Human confirmed the action (F13 SOVEREIGN)
    - ai: AI system processed and validated (F2 TRUTH)
    - earth: Data source/earth evidence grounded (F3 WITNESS)
    """
    human: bool = False
    ai: bool = False
    earth: bool = False
    human_id: str = ""
    ai_id: str = ""
    earth_source: str = ""
    notes: str = ""

    def is_complete(self) -> bool:
        """All three witnesses must be present for a valid seal."""
        return self.human and self.ai and self.earth

    def missing_witnesses(self) -> list[str]:
        """Which witnesses are missing?"""
        missing = []
        if not self.human:
            missing.append("human")
        if not self.ai:
            missing.append("ai")
        if not self.earth:
            missing.append("earth")
        return missing

    def to_dict(self) -> dict:
        """Serialize to dict for envelope."""
        return {
            "human": self.human,
            "ai": self.ai,
            "earth": self.earth,
            "human_id": self.human_id,
            "ai_id": self.ai_id,
            "earth_source": self.earth_source,
            "notes": self.notes,
            "is_complete": self.is_complete(),
            "missing": self.missing_witnesses(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TriWitness":
        """Deserialize from dict."""
        return cls(
            human=d.get("human", False),
            ai=d.get("ai", False),
            earth=d.get("earth", False),
            human_id=d.get("human_id", ""),
            ai_id=d.get("ai_id", ""),
            earth_source=d.get("earth_source", ""),
            notes=d.get("notes", ""),
        )

    @classmethod
    def ai_only(cls, ai_id: str = "WEALTH") -> "TriWitness":
        """Create a witness with only AI attestation (for OBSERVE/COMPUTE)."""
        return cls(human=False, ai=True, earth=False, ai_id=ai_id)

    @classmethod
    def full(cls, human_id: str = "Arif", ai_id: str = "WEALTH", earth_source: str = "") -> "TriWitness":
        """Create a fully-attested witness (for SEAL)."""
        return cls(
            human=True, ai=True, earth=True,
            human_id=human_id, ai_id=ai_id, earth_source=earth_source,
        )
