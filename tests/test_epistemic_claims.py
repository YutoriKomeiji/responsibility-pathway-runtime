# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

import pytest

from rpr.epistemic_claims import (
    ClaimClass,
    ClaimDecision,
    ClaimEvidence,
    EpistemicClaim,
    UseContext,
    VerificationState,
    build_claim_bundle,
    evaluate_claim_use,
)


DIGEST = "a" * 64


def evidence(*, independent: bool = False, supports: bool | None = True) -> ClaimEvidence:
    return ClaimEvidence("ev-1", DIGEST, "https://example.invalid/source", "validator", independent, supports)


def approved_claim(claim_class: ClaimClass = ClaimClass.FACTUAL, *, independent: bool = False) -> EpistemicClaim:
    return EpistemicClaim(
        "claim-1",
        "A bounded factual claim",
        claim_class,
        VerificationState.APPROVED_FOR_USE,
        (evidence(independent=independent),),
        assumptions=("declared assumption",) if claim_class is ClaimClass.INFERENCE else (),
        review_owner="reviewer",
        approval_authority="authority",
        residual_owner="owner",
    )


def test_approved_factual_claim_can_be_published() -> None:
    result = evaluate_claim_use(approved_claim(), UseContext.PUBLICATION)
    assert result.decision is ClaimDecision.ALLOW


def test_unverified_factual_claim_is_held() -> None:
    claim = EpistemicClaim("claim-1", "Unverified fact", ClaimClass.FACTUAL, VerificationState.UNVERIFIED)
    result = evaluate_claim_use(claim, UseContext.EXTERNAL_MESSAGE)
    assert result.decision is ClaimDecision.HOLD
    assert "factual_claim_not_supported" in result.reason_codes


def test_conflicting_evidence_returns_to_human_gate() -> None:
    claim = EpistemicClaim(
        "claim-1",
        "Contested fact",
        ClaimClass.FACTUAL,
        VerificationState.CONFLICTING_EVIDENCE,
        (evidence(supports=True), ClaimEvidence("ev-2", "b" * 64, "source-2", "validator-2", True, False)),
        conflict_notes=("sources disagree",),
    )
    result = evaluate_claim_use(claim, UseContext.PUBLICATION)
    assert result.decision is ClaimDecision.HUMAN_GATE


def test_high_impact_claim_requires_independent_verification() -> None:
    claim = approved_claim(ClaimClass.HIGH_IMPACT, independent=False)
    result = evaluate_claim_use(claim, UseContext.HIGH_IMPACT_ACTION)
    assert result.decision is ClaimDecision.HUMAN_GATE
    assert result.reason_codes == ("independent_verification_missing",)


def test_high_impact_claim_with_independent_evidence_can_pass_gate() -> None:
    claim = approved_claim(ClaimClass.HIGH_IMPACT, independent=True)
    result = evaluate_claim_use(claim, UseContext.HIGH_IMPACT_ACTION)
    assert result.decision is ClaimDecision.ALLOW


def test_inference_requires_declared_assumptions() -> None:
    claim = EpistemicClaim(
        "claim-1",
        "An inference",
        ClaimClass.INFERENCE,
        VerificationState.SOURCE_SUPPORTS_CLAIM,
        (evidence(),),
    )
    result = evaluate_claim_use(claim, UseContext.INTERNAL_DRAFT)
    assert result.decision is ClaimDecision.HOLD


def test_creative_content_can_proceed_with_label() -> None:
    claim = EpistemicClaim("claim-1", "A fictional concept", ClaimClass.CREATIVE, VerificationState.PROPOSED)
    result = evaluate_claim_use(claim, UseContext.PUBLICATION)
    assert result.decision is ClaimDecision.ALLOW
    assert result.reason_codes == ("creative_content_must_be_labelled",)


def test_approved_state_requires_responsibility_owners() -> None:
    claim = EpistemicClaim(
        "claim-1",
        "Fact",
        ClaimClass.FACTUAL,
        VerificationState.APPROVED_FOR_USE,
        (evidence(),),
        review_owner="reviewer",
        approval_authority="authority",
    )
    with pytest.raises(ValueError, match="residual owner"):
        claim.validate()


def test_bundle_is_deterministic() -> None:
    first = approved_claim()
    second = EpistemicClaim(
        "claim-2",
        "Second claim",
        ClaimClass.FACTUAL,
        VerificationState.APPROVED_FOR_USE,
        (ClaimEvidence("ev-2", "b" * 64, "source-2", "validator-2", False, True),),
        review_owner="reviewer",
        approval_authority="authority",
        residual_owner="owner",
    )
    assert build_claim_bundle((first, second))["bundle_sha256"] == build_claim_bundle((second, first))["bundle_sha256"]
