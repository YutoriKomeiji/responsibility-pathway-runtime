# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
)


def test_legacy_pathway_definition_wire_shape_is_unchanged_when_route_absent() -> None:
    definition = PathwayDefinition(
        "legacy-1",
        "read_status",
        ActionClass.OBSERVE_ONLY,
        EnvironmentTrust.TRUSTED_INTERNAL,
        "owner",
        None,
        "agent",
        "operator",
        "audit",
        "repairer",
        "resumer",
        "on-error",
        "owner",
        {"target": "status"},
    )

    value = definition.to_dict()
    assert value["metadata"] == {"target": "status"}
    assert "responsibility_route" not in value


def test_additive_route_serialization_is_round_trip_stable() -> None:
    route = ResponsibilityRoute(
        route_class=ResponsibilityRouteClass.AI_RESOLVE_WITHIN_DELEGATION,
        source_holder="agent-a",
        destination="agent-b",
        receiver_eligibility=ReceiverEligibility.ELIGIBLE,
        authority_class="delegated-runtime",
        delegation_scope="readback-only",
        unresolved_payload=("external_effect",),
        allowed_next_actions=("readback", "reconcile"),
        closure_condition="effect verified",
        reevaluation_condition="authority or tool context changes",
        residual_owner="owner",
    )
    definition = PathwayDefinition(
        pathway_id="route-1",
        action_name="read_status",
        action_class=ActionClass.OBSERVE_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="repairer",
        resume_authority="resumer",
        human_return_point="on-error",
        residual_owner="owner",
        metadata={"target": "status"},
        responsibility_route=route,
    )

    restored = PathwayDefinition.from_dict(definition.to_dict())
    assert restored == definition
