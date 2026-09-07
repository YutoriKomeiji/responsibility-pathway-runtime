# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from rpr.inspection import inspect_pathway
from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
    RuntimeDecision,
)


def pathway(**overrides):
    values = dict(pathway_id="p-1", action_name="send_email", action_class=ActionClass.HIGH_IMPACT, environment_trust=EnvironmentTrust.TRUSTED_INTERNAL, decision_owner="owner", approval_authority="approver", execution_actor="agent", stop_authority="operator", evidence_owner="audit", repair_owner="support", resume_authority="manager", human_return_point="before_send", residual_owner="owner")
    values.update(overrides)
    return PathwayDefinition(**values)


def route(**overrides):
    values = dict(
        route_class=ResponsibilityRouteClass.AI_RESOLVE_WITHIN_DELEGATION,
        source_holder="agent-a",
        destination="agent-b",
        receiver_eligibility=ReceiverEligibility.ELIGIBLE,
        authority_class="delegated_runtime",
        delegation_scope="readback-only reconciliation",
        unresolved_payload=("external_effect",),
        allowed_next_actions=("readback", "reconcile"),
        closure_condition="effect state verified",
        reevaluation_condition="tool or authority context changes",
        residual_owner="owner",
    )
    values.update(overrides)
    return ResponsibilityRoute(**values)


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


def test_approval_required_without_authority_holds_for_definition_repair():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            approval_authority=None,
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "approval_authority_missing" in {item.code for item in result.findings}
    assert result.next_required_authority == "owner"
    assert result.next_required_action == "correct_pathway_definition"


def test_missing_repair_owner_is_invalid_and_does_not_create_human_gate():
    result = inspect_pathway(pathway(repair_owner=""))
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "repair_owner_missing" in {item.code for item in result.findings}
    assert result.next_required_authority == "owner"


def test_high_impact_requires_separate_stop_authority():
    result = inspect_pathway(pathway(stop_authority="agent"))
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "stop_execution_authority_not_separated" in {item.code for item in result.findings}


def test_high_impact_requires_concrete_human_return_point():
    result = inspect_pathway(pathway(human_return_point=""))
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "high_impact_human_return_point_missing" in {item.code for item in result.findings}


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
    assert "responsibility_route_available" not in value


def test_additive_responsibility_route_does_not_replace_human_gate_semantics():
    result = inspect_pathway(pathway(responsibility_route=route()))
    assert result.valid
    assert result.decision is RuntimeDecision.HUMAN_GATE


def test_responsibility_route_rejects_ineligible_receiver_without_false_escalation():
    result = inspect_pathway(
        pathway(
            responsibility_route=route(receiver_eligibility=ReceiverEligibility.INELIGIBLE),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "route_receiver_ineligible" in {item.code for item in result.findings}


def test_responsibility_route_preserves_residual_owner():
    result = inspect_pathway(
        pathway(
            responsibility_route=route(residual_owner="other-owner"),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "route_residual_owner_mismatch" in {item.code for item in result.findings}


def test_responsibility_route_requires_bounded_next_actions():
    result = inspect_pathway(
        pathway(
            responsibility_route=route(allowed_next_actions=()),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "route_allowed_next_actions_missing" in {item.code for item in result.findings}


def test_responsibility_route_rejects_blank_next_action():
    result = inspect_pathway(
        pathway(
            responsibility_route=route(allowed_next_actions=("readback", " ")),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "route_allowed_next_actions_blank" in {item.code for item in result.findings}


def test_responsibility_route_rejects_blank_required_field():
    result = inspect_pathway(
        pathway(
            responsibility_route=route(delegation_scope=""),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "route_delegation_scope_missing" in {item.code for item in result.findings}


def test_receiver_requiring_reevaluation_holds_without_invalidating_record():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            responsibility_route=route(receiver_eligibility=ReceiverEligibility.REQUIRES_REEVALUATION),
        )
    )
    assert result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert result.degradation_mode == "route_reevaluation_required"
    assert result.next_required_authority == "owner"
    assert result.next_required_action == "reevaluate_responsibility_route"
    assert "route_receiver_requires_reevaluation" in {item.code for item in result.findings}


def test_bounded_human_return_requires_concrete_return_point():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            human_return_point="",
            responsibility_route=route(route_class=ResponsibilityRouteClass.BOUNDED_HUMAN_RETURN),
        )
    )
    assert not result.valid
    assert result.decision is RuntimeDecision.HOLD
    assert "bounded_human_return_point_missing" in {item.code for item in result.findings}


def test_non_human_route_does_not_require_legacy_human_return_point():
    result = inspect_pathway(
        pathway(
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            human_return_point="",
            responsibility_route=route(),
        )
    )
    assert result.valid
    assert result.decision is RuntimeDecision.ALLOW
    assert result.human_return_available is False
