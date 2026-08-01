# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from rpr.inspection import inspect_pathway
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, RuntimeDecision


def pathway(**overrides):
    values = dict(pathway_id="p-1", action_name="send_email", action_class=ActionClass.HIGH_IMPACT, environment_trust=EnvironmentTrust.TRUSTED_INTERNAL, decision_owner="owner", approval_authority="approver", execution_actor="agent", stop_authority="operator", evidence_owner="audit", repair_owner="support", resume_authority="manager", human_return_point="before_send", residual_owner="owner")
    values.update(overrides)
    return PathwayDefinition(**values)


def test_high_impact_pathway_routes_to_human_gate():
    result = inspect_pathway(pathway())
    assert result.valid
    assert result.decision is RuntimeDecision.HUMAN_GATE
    assert result.next_required_authority == "approver"
    assert result.next_required_action == "perform_explicit_human_review"


def test_reversible_external_with_approval_authority_is_admissible():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            action_name="replace_text_file",
        )
    )
    assert result.valid
    assert result.decision is RuntimeDecision.ALLOW
    assert result.degradation_mode == "approval_pending"
    assert result.next_required_authority == "approver"
    assert result.next_required_action == "approve_or_deny"


def test_observe_only_identifies_execution_actor_as_next_handler():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.OBSERVE_ONLY,
            action_name="read_status",
            approval_authority=None,
        )
    )
    assert result.valid
    assert result.next_required_authority == "agent"
    assert result.next_required_action == "execute_bounded_action"


def test_approval_required_without_authority_fails_closed():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            approval_authority=None,
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HUMAN_GATE
    assert "approval_authority_missing" in {item.code for item in result.findings}
    assert result.next_required_authority == "owner"
    assert result.next_required_action == "correct_pathway_definition"


def test_missing_repair_owner_is_invalid():
    result = inspect_pathway(pathway(repair_owner=""))
    assert not result.valid
    assert "repair_owner_missing" in {item.code for item in result.findings}
    assert result.next_required_authority == "owner"


def test_high_impact_requires_separate_stop_authority():
    result = inspect_pathway(pathway(stop_authority="agent"))
    assert not result.valid
    assert "stop_execution_authority_not_separated" in {item.code for item in result.findings}


def test_adversarial_environment_identifies_stop_authority_review():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.OBSERVE_ONLY,
            environment_trust=EnvironmentTrust.ADVERSARIAL,
            approval_authority=None,
        )
    )
    assert result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert result.next_required_authority == "operator"
    assert result.next_required_action == "review_adversarial_environment"


def test_inspection_serialization_includes_next_operational_step():
    value = inspect_pathway(pathway()).to_dict()
    assert value["next_required_authority"] == "approver"
    assert value["next_required_action"] == "perform_explicit_human_review"
