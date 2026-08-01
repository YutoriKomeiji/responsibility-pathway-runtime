# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Iterable


class ClaimClass(StrEnum):
    CREATIVE = "creative"
    INFERENCE = "inference"
    FACTUAL = "factual"
    STATISTIC_OR_QUOTATION = "statistic_or_quotation"
    HIGH_IMPACT = "high_impact"


class VerificationState(StrEnum):
    PROPOSED = "proposed"
    SOURCE_ATTACHED = "source_attached"
    SOURCE_RETRIEVED = "source_retrieved"
    SOURCE_SUPPORTS_CLAIM = "source_supports_claim"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    UNVERIFIED = "unverified"
    HUMAN_REVIEWED = "human_reviewed"
    APPROVED_FOR_USE = "approved_for_use"


class UseContext(StrEnum):
    INTERNAL_DRAFT = "internal_draft"
    EXTERNAL_MESSAGE = "external_message"
    PUBLICATION = "publication"
    HIGH_IMPACT_ACTION = "high_impact_action"


class ClaimDecision(StrEnum):
    ALLOW = "allow"
    HOLD = "hold"
    HUMAN_GATE = "human_gate"
    DENY = "deny"


def _validate_sha256(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("evidence reference must be SHA-256")


@dataclass(frozen=True)
class ClaimEvidence:
    evidence_id: str
    artifact_sha256: str
    source_locator: str
    verifier: str
    independent: bool = False
    supports_claim: bool | None = None

    def validate(self) -> None:
        if not self.evidence_id.strip() or not self.source_locator.strip() or not self.verifier.strip():
            raise ValueError("evidence id, source locator, and verifier are required")
        _validate_sha256(self.artifact_sha256)


@dataclass(frozen=True)
class EpistemicClaim:
    claim_id: str
    text: str
    claim_class: ClaimClass
    verification_state: VerificationState
    evidence: tuple[ClaimEvidence, ...] = ()
    assumptions: tuple[str, ...] = ()
    conflict_notes: tuple[str, ...] = ()
    review_owner: str | None = None
    approval_authority: str | None = None
    residual_owner: str | None = None

    def validate(self) -> None:
        if not self.claim_id.strip() or not self.text.strip():
            raise ValueError("claim id and text are required")
        for item in self.evidence:
            item.validate()
        if len({item.evidence_id for item in self.evidence}) != len(self.evidence):
            raise ValueError("duplicate evidence id")
        if self.verification_state in {
            VerificationState.SOURCE_ATTACHED,
            VerificationState.SOURCE_RETRIEVED,
            VerificationState.SOURCE_SUPPORTS_CLAIM,
            VerificationState.HUMAN_REVIEWED,
            VerificationState.APPROVED_FOR_USE,
        } and not self.evidence:
            raise ValueError("verification state requires evidence")
        if self.verification_state is VerificationState.SOURCE_SUPPORTS_CLAIM and not any(
            item.supports_claim is True for item in self.evidence
        ):
            raise ValueError("supported state requires supporting evidence")
        if self.verification_state is VerificationState.CONFLICTING_EVIDENCE and not self.conflict_notes:
            raise ValueError("conflicting evidence requires conflict notes")
        if self.verification_state in {VerificationState.HUMAN_REVIEWED, VerificationState.APPROVED_FOR_USE}:
            if not self.review_owner or not self.review_owner.strip():
                raise ValueError("reviewed claims require a review owner")
        if self.verification_state is VerificationState.APPROVED_FOR_USE:
            if not self.approval_authority or not self.approval_authority.strip():
                raise ValueError("approved claims require approval authority")
            if not self.residual_owner or not self.residual_owner.strip():
                raise ValueError("approved claims require residual owner")


@dataclass(frozen=True)
class ClaimGateResult:
    claim_id: str
    use_context: UseContext
    decision: ClaimDecision
    reason_codes: tuple[str, ...]


def evaluate_claim_use(claim: EpistemicClaim, context: UseContext) -> ClaimGateResult:
    claim.validate()
    reasons: list[str] = []

    if claim.verification_state is VerificationState.CONFLICTING_EVIDENCE:
        return ClaimGateResult(claim.claim_id, context, ClaimDecision.HUMAN_GATE, ("conflicting_evidence",))

    if context is UseContext.INTERNAL_DRAFT:
        if claim.verification_state in {VerificationState.PROPOSED, VerificationState.UNVERIFIED}:
            reasons.append("draft_must_display_unverified_status")
        if claim.claim_class is ClaimClass.INFERENCE and not claim.assumptions:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HOLD, ("inference_assumptions_missing",))
        return ClaimGateResult(claim.claim_id, context, ClaimDecision.ALLOW, tuple(reasons))

    if claim.claim_class is ClaimClass.CREATIVE:
        if claim.verification_state in {VerificationState.PROPOSED, VerificationState.UNVERIFIED}:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.ALLOW, ("creative_content_must_be_labelled",))

    if claim.claim_class is ClaimClass.INFERENCE:
        if not claim.assumptions:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HOLD, ("inference_assumptions_missing",))
        if claim.verification_state not in {
            VerificationState.SOURCE_SUPPORTS_CLAIM,
            VerificationState.HUMAN_REVIEWED,
            VerificationState.APPROVED_FOR_USE,
        }:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HOLD, ("inference_basis_not_verified",))

    if claim.claim_class in {ClaimClass.FACTUAL, ClaimClass.STATISTIC_OR_QUOTATION}:
        if claim.verification_state not in {
            VerificationState.SOURCE_SUPPORTS_CLAIM,
            VerificationState.HUMAN_REVIEWED,
            VerificationState.APPROVED_FOR_USE,
        }:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HOLD, ("factual_claim_not_supported",))
        if not any(item.supports_claim is True for item in claim.evidence):
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HOLD, ("supporting_evidence_missing",))

    if claim.claim_class is ClaimClass.HIGH_IMPACT or context is UseContext.HIGH_IMPACT_ACTION:
        if claim.verification_state is not VerificationState.APPROVED_FOR_USE:
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HUMAN_GATE, ("high_impact_claim_not_approved",))
        if not any(item.independent and item.supports_claim is True for item in claim.evidence):
            return ClaimGateResult(claim.claim_id, context, ClaimDecision.HUMAN_GATE, ("independent_verification_missing",))

    if context in {UseContext.EXTERNAL_MESSAGE, UseContext.PUBLICATION} and claim.verification_state is not VerificationState.APPROVED_FOR_USE:
        return ClaimGateResult(claim.claim_id, context, ClaimDecision.HUMAN_GATE, ("external_use_not_approved",))

    return ClaimGateResult(claim.claim_id, context, ClaimDecision.ALLOW, ())


def build_claim_bundle(claims: Iterable[EpistemicClaim]) -> dict[str, object]:
    ordered = sorted(claims, key=lambda item: item.claim_id)
    identifiers: set[str] = set()
    for claim in ordered:
        claim.validate()
        if claim.claim_id in identifiers:
            raise ValueError("duplicate claim id")
        identifiers.add(claim.claim_id)
    values = [asdict(item) for item in ordered]
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "format_version": 1,
        "claims": values,
        "bundle_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
