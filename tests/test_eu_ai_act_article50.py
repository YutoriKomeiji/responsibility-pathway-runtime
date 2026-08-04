# Language: Python
# Purpose: Verify fail-closed Article 50 transparency decisions.
# Boundary: Tests cover the reference profile, not legal compliance.

import pytest

from rpr.eu_ai_act_article50 import (
    ActorRole,
    Article50Assessment,
    ContentContext,
    ContentModality,
    SystemFunction,
    TerritorialScope,
    TransparencyOutcome,
    evaluate_article50,
)


def assessment(**overrides):
    values = {
        "assessment_id": "a50-001",
        "assessed_at": "2026-08-04T16:30:00+09:00",
        "legal_basis_version": "EU-AI-ACT-ARTICLE-50-2026-08-02",
        "territorial_scope": TerritorialScope.EU_IN_SCOPE,
        "actor_role": ActorRole.DEPLOYER,
        "system_function": SystemFunction.GENERATIVE_CONTENT,
        "content_modality": ContentModality.TEXT,
        "content_context": ContentContext.ORDINARY_CONTENT,
        "responsible_owner": "release-owner",
    }
    values.update(overrides)
    return Article50Assessment(**values)


def test_interactive_ai_requires_disclosure():
    decision = evaluate_article50(
        assessment(system_function=SystemFunction.INTERACTIVE_AI, content_modality=ContentModality.NONE)
    )
    assert decision.outcome is TransparencyOutcome.CONTROLS_REQUIRED
    assert decision.interaction_disclosure_required is True
    assert decision.missing_evidence == ("interaction_disclosure",)


def test_provider_generated_content_requires_machine_readable_mark():
    decision = evaluate_article50(
        assessment(actor_role=ActorRole.PROVIDER, machine_readable_mark_present=False)
    )
    assert decision.machine_readable_mark_required is True
    assert "machine_readable_mark" in decision.missing_evidence


def test_deepfake_requires_visible_label():
    decision = evaluate_article50(
        assessment(
            content_modality=ContentModality.VIDEO,
            content_context=ContentContext.DEEPFAKE,
            visible_label_present=False,
        )
    )
    assert decision.visible_label_required is True
    assert decision.outcome is TransparencyOutcome.CONTROLS_REQUIRED


def test_artistic_content_keeps_proportionate_disclosure_requirement():
    decision = evaluate_article50(
        assessment(
            content_modality=ContentModality.VIDEO,
            content_context=ContentContext.ARTISTIC_OR_FICTIONAL,
            visible_label_present=True,
        )
    )
    assert decision.visible_label_required is True
    assert decision.outcome is TransparencyOutcome.READY_FOR_HUMAN_GATE


def test_public_interest_text_exception_requires_review_and_editorial_owner():
    decision = evaluate_article50(
        assessment(
            content_context=ContentContext.PUBLIC_INTEREST_TEXT,
            human_review_completed=True,
            editorial_responsibility_owner="Akihisa Ono",
        )
    )
    assert decision.visible_label_required is False
    assert decision.outcome is TransparencyOutcome.READY_FOR_HUMAN_GATE


def test_public_interest_text_without_editorial_responsibility_blocks():
    decision = evaluate_article50(
        assessment(
            content_context=ContentContext.PUBLIC_INTEREST_TEXT,
            human_review_completed=True,
            editorial_responsibility_owner=None,
        )
    )
    assert decision.visible_label_required is True
    assert decision.outcome is TransparencyOutcome.CONTROLS_REQUIRED


def test_unresolved_scope_is_fail_closed():
    decision = evaluate_article50(assessment(territorial_scope=TerritorialScope.UNRESOLVED))
    assert decision.outcome is TransparencyOutcome.BLOCKED_UNRESOLVED
    assert decision.human_gate_required is True


def test_human_gate_approval_requires_evidence():
    with pytest.raises(ValueError, match="human_gate_evidence"):
        evaluate_article50(assessment(), human_gate_approved=True)


def test_human_gate_approval_is_bounded_to_declared_context():
    decision = evaluate_article50(
        assessment(),
        human_gate_approved=True,
        human_gate_evidence=("review:123", "owner:release-owner"),
    )
    assert decision.outcome is TransparencyOutcome.APPROVED_FOR_DECLARED_CONTEXT
    assert decision.human_gate_required is False


def test_out_of_scope_record_is_not_named_compliant():
    decision = evaluate_article50(assessment(territorial_scope=TerritorialScope.OUT_OF_SCOPE))
    assert decision.outcome is TransparencyOutcome.NOT_APPLICABLE
    assert "compliant" not in decision.outcome.value
