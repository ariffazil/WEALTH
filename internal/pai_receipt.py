"""
PAI Receipt — Provenance + Authority + Intent
═══════════════════════════════════════════════════════════════════
WEALTH local mirror of the canonical PAI Receipt schema.

CANONICAL SOURCE: arifOS/arifosmcp/schemas/pai_receipt.py (Ratified 2026-06-06)
                 This file is the WEALTH-local copy. Same schema, same contract.

WEALTH-specific usage:
  - wealth_omni_wisdom (synthesis) — attaches T3+ PAI receipt to its output.
  - wealth_survival_engine — attaches T3+ PAI receipt to its output.
  - Any capital-moving decision path (spend, allocate, transfer, trade) — must
    produce a T4+ PAI receipt with requires_human_intent=True before any
    execution.
  - wealth_pai_attach — explicit tool for attaching PAI to any WEALTH output.

Rule: Any capital-moving or capital-signalling action requires fresh human intent.
      No API-key-style power. No permanent treasury token. No agent spending from vibes.

DITEMPA BUKAN DIBERI — the boundary object, forged.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class ProducerType(StrEnum):
    HUMAN = "human"
    AI = "ai"
    HUMAN_ASSISTED_AI = "human_assisted_ai"
    TOOL = "tool"
    UNKNOWN = "unknown"
    MIXED = "mixed"


class Organ(StrEnum):
    ARIFOS = "arifOS"
    GEOX = "GEOX"
    WEALTH = "WEALTH"
    WELL = "WELL"
    A_FORGE = "A-FORGE"
    APEX = "APEX"
    AAA = "AAA"
    EXTERNAL = "EXTERNAL"


class IntentAction(StrEnum):
    DRAFT = "draft"
    ANALYZE = "analyze"
    PUBLISH = "publish"
    SPEND = "spend"
    TRADE = "trade"
    ALLOCATE = "allocate"
    INVEST = "invest"
    PRICE = "price"
    TRANSFER = "transfer"
    DELETE = "delete"
    DEPLOY = "deploy"
    SEAL = "seal"
    MODIFY_TREASURY = "modify_treasury"
    ADVISORY = "advisory"


class RiskClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ATOMIC = "atomic"


class Reversibility(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class Tier(StrEnum):
    DRAFT = "draft"
    INTERNAL = "internal"
    EXTERNAL_CLAIM = "external_claim"
    CONSEQUENTIAL = "consequential"
    ATOMIC = "atomic"


PAI_RECEIPT_TYPE = "arifOS.PAI.v1"
CANONICAL_HUMAN_ROOT = "did:web:arif-fazil.com"

RISK_TO_TIER: dict[RiskClass, Tier] = {
    RiskClass.LOW: Tier.DRAFT,
    RiskClass.MEDIUM: Tier.EXTERNAL_CLAIM,
    RiskClass.HIGH: Tier.CONSEQUENTIAL,
    RiskClass.ATOMIC: Tier.ATOMIC,
}

INTENT_MIN_TIER: dict[IntentAction, Tier] = {
    IntentAction.DRAFT: Tier.DRAFT,
    IntentAction.ANALYZE: Tier.INTERNAL,
    IntentAction.ADVISORY: Tier.INTERNAL,
    IntentAction.PUBLISH: Tier.EXTERNAL_CLAIM,
    IntentAction.PRICE: Tier.EXTERNAL_CLAIM,
    IntentAction.SEAL: Tier.EXTERNAL_CLAIM,
    IntentAction.SPEND: Tier.CONSEQUENTIAL,
    IntentAction.TRADE: Tier.CONSEQUENTIAL,
    IntentAction.ALLOCATE: Tier.CONSEQUENTIAL,
    IntentAction.INVEST: Tier.CONSEQUENTIAL,
    IntentAction.TRANSFER: Tier.CONSEQUENTIAL,
    IntentAction.MODIFY_TREASURY: Tier.ATOMIC,
    IntentAction.DEPLOY: Tier.CONSEQUENTIAL,
    IntentAction.DELETE: Tier.ATOMIC,
}


class PAIOrigin(BaseModel):
    producer_type: ProducerType
    producer_id: str
    organ: Organ
    model_id: Optional[str] = None
    tool_id: Optional[str] = None


class PAIAuthority(BaseModel):
    human_root: str = CANONICAL_HUMAN_ROOT
    delegate: str
    authority_chain: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    subdelegation_allowed: bool = False


class PAIIntent(BaseModel):
    action: IntentAction
    scope: str
    risk_class: RiskClass
    external_effect: bool
    reversibility: Reversibility = Reversibility.FULL
    requires_human_intent: bool = False
    requires_888_hold: bool = False

    @model_validator(mode="after")
    def _enforce_intent_floor(self) -> "PAIIntent":
        tier = RISK_TO_TIER[self.risk_class]
        if tier in (Tier.CONSEQUENTIAL, Tier.ATOMIC) and not self.requires_human_intent:
            object.__setattr__(self, "requires_human_intent", True)
        if tier == Tier.ATOMIC and not self.requires_888_hold:
            object.__setattr__(self, "requires_888_hold", True)
        if self.requires_888_hold and self.reversibility == Reversibility.FULL:
            object.__setattr__(self, "reversibility", Reversibility.NONE)
        return self


class PAIEvidence(BaseModel):
    sources: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    confidence: str = "unknown"
    human_reviewed: bool = False
    reviewer_id: Optional[str] = None


class PAIAudit(BaseModel):
    destination: str = "VAULT999"
    previous_receipt: Optional[str] = None
    receipt_hash: Optional[str] = None
    signature: Optional[str] = None
    vault_ref: Optional[str] = None


class PAIReceipt(BaseModel):
    receipt_type: str = PAI_RECEIPT_TYPE
    object_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    origin: PAIOrigin
    authority: PAIAuthority
    intent: PAIIntent
    evidence: PAIEvidence = Field(default_factory=PAIEvidence)
    audit: PAIAudit = Field(default_factory=PAIAudit)

    @model_validator(mode="after")
    def _enforce_receipt_type(self) -> "PAIReceipt":
        if self.receipt_type != PAI_RECEIPT_TYPE:
            raise ValueError(
                f"receipt_type must be '{PAI_RECEIPT_TYPE}', got {self.receipt_type!r}"
            )
        return self


def tier_of(receipt: PAIReceipt | dict[str, Any]) -> Tier:
    if isinstance(receipt, dict):
        risk = receipt.get("intent", {}).get("risk_class", "low")
        action = receipt.get("intent", {}).get("action", "draft")
    else:
        risk = receipt.intent.risk_class
        action = receipt.intent.action
    declared_tier = RISK_TO_TIER[RiskClass(risk)]
    min_tier = INTENT_MIN_TIER[IntentAction(action)]
    tier_order = [Tier.DRAFT, Tier.INTERNAL, Tier.EXTERNAL_CLAIM, Tier.CONSEQUENTIAL, Tier.ATOMIC]
    if tier_order.index(min_tier) > tier_order.index(declared_tier):
        return min_tier
    return declared_tier


def content_hash(obj: Any) -> str:
    canonical = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mint_pai_receipt(
    *,
    object_id: str,
    producer_type: ProducerType,
    producer_id: str,
    organ: Organ,
    action: IntentAction,
    scope: str,
    risk_class: RiskClass,
    external_effect: bool = False,
    reversibility: Reversibility = Reversibility.FULL,
    delegate: str = "anonymous",
    authority_chain: Optional[list[str]] = None,
    expires_at: Optional[datetime] = None,
    subdelegation_allowed: bool = False,
    sources: Optional[list[str]] = None,
    tool_calls: Optional[list[str]] = None,
    confidence: str = "unknown",
    human_reviewed: bool = False,
    reviewer_id: Optional[str] = None,
    model_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    previous_receipt: Optional[str] = None,
    destination: str = "VAULT999",
    signature: Optional[str] = None,
) -> PAIReceipt:
    intent = PAIIntent(
        action=action, scope=scope, risk_class=risk_class,
        external_effect=external_effect, reversibility=reversibility,
    )
    authority = PAIAuthority(
        delegate=delegate,
        authority_chain=authority_chain or ["root"],
        expires_at=expires_at,
        subdelegation_allowed=subdelegation_allowed,
    )
    evidence = PAIEvidence(
        sources=sources or [], tool_calls=tool_calls or [],
        confidence=confidence, human_reviewed=human_reviewed, reviewer_id=reviewer_id,
    )
    audit = PAIAudit(destination=destination, previous_receipt=previous_receipt, signature=signature)
    origin = PAIOrigin(
        producer_type=producer_type, producer_id=producer_id, organ=organ,
        model_id=model_id, tool_id=tool_id,
    )
    receipt = PAIReceipt(
        object_id=object_id, origin=origin, authority=authority, intent=intent,
        evidence=evidence, audit=audit,
    )
    receipt.audit.receipt_hash = content_hash(receipt.model_dump(exclude={"audit"}))
    return receipt


def attach_pai_to_payload(
    payload: dict[str, Any], receipt: PAIReceipt
) -> dict[str, Any]:
    out = dict(payload)
    out["_pai_receipt"] = receipt.model_dump()
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  WEALTH-SPECIFIC HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def wealth_capital_receipt(
    *,
    verdict: str,  # SEAL | HOLD | STOP | SABAR
    scope: str,
    tool_id: str,
    sources: Optional[list[str]] = None,
    tool_calls: Optional[list[str]] = None,
    confidence: str = "ESTIMATE",
    human_reviewed: bool = False,
    reviewer_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> PAIReceipt:
    """Standard PAI receipt for a WEALTH capital-intelligence verdict.

    Mapping (wealth verdict → PAI tier):
      SEAL  (advisory)  → T3 EXTERNAL_CLAIM (MEDIUM, PUBLISH, full)
      HOLD  (caution)   → T3 EXTERNAL_CLAIM (MEDIUM, PUBLISH, full)
      SABAR (waiting)   → T2 INTERNAL        (LOW,    ANALYZE, full)
      STOP  (refused)   → T4 CONSEQUENTIAL   (HIGH,   ADVISORY, partial)
    """
    mapping = {
        "SEAL":  (RiskClass.MEDIUM, IntentAction.PUBLISH, Reversibility.FULL),
        "HOLD":  (RiskClass.MEDIUM, IntentAction.PUBLISH, Reversibility.FULL),
        "SABAR": (RiskClass.LOW, IntentAction.ANALYZE, Reversibility.FULL),
        "STOP":  (RiskClass.HIGH, IntentAction.ADVISORY, Reversibility.PARTIAL),
    }
    risk_class, action, reversibility = mapping.get(
        verdict.upper(), (RiskClass.MEDIUM, IntentAction.PUBLISH, Reversibility.FULL)
    )
    return mint_pai_receipt(
        object_id=f"wealth_{verdict.lower()}_{hash(scope) & 0xffffffff:#x}",
        producer_type=ProducerType.HUMAN_ASSISTED_AI if human_reviewed else ProducerType.AI,
        producer_id=f"tool:{tool_id}",
        organ=Organ.WEALTH,
        action=action,
        scope=scope,
        risk_class=risk_class,
        external_effect=True,
        reversibility=reversibility,
        delegate=f"tool:{tool_id}",
        sources=sources or [],
        tool_calls=tool_calls or [tool_id],
        confidence=confidence,
        human_reviewed=human_reviewed,
        reviewer_id=reviewer_id,
        model_id=model_id,
        tool_id=tool_id,
    )


__all__ = [
    "PAI_RECEIPT_TYPE", "CANONICAL_HUMAN_ROOT", "RISK_TO_TIER", "INTENT_MIN_TIER",
    "ProducerType", "Organ", "IntentAction", "RiskClass", "Reversibility", "Tier",
    "PAIOrigin", "PAIAuthority", "PAIIntent", "PAIEvidence", "PAIAudit", "PAIReceipt",
    "tier_of", "content_hash", "mint_pai_receipt", "attach_pai_to_payload",
    "wealth_capital_receipt",
]
