# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

import pytest

from rpr.authority import AuthorityError, authorize_execution_access, authorize_reconciliation_access
from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    PathwayState,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
)
from rpr.routing import compatibility_route_for_state


def _route() -> ResponsibilityRoute:
    return ResponsibilityRoute(
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


def _definition(*, responsibility_route: ResponsibilityRoute | None = None) -> PathwayDefinition:
    return PathwayDefinition(
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
        responsibility_route=responsibility_route,
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
    definition = _definition(responsibility_route=_route())
    restored = PathwayDefinition.from_dict(definition.to_dict())
    assert restored == definition


def test_route_destination_does_not_gain_execution_authority() -> None:
    definition = _definition(responsibility_route=_route())

    with pytest.raises(AuthorityError, match="execution authority"):
        authorize_execution_access(definition, "agent-b")

    authorize_execution_access(definition, "agent")


def test_route_destination_does_not_gain_reconciliation_authority() -> None:
    definition = _definition(responsibility_route=_route())

    with pytest.raises(AuthorityError, match="reconciliation authority"):
        authorize_reconciliation_access(definition, "agent-b")

    authorize_reconciliation_access(definition, "audit")
    authorize_reconciliation_access(definition, "repairer")


def test_unknown_write_is_classified_as_reconciliation_hold_not_human_return() -> None:
    assert (
        compatibility_route_for_state(PathwayState.WRITE_STATUS_UNKNOWN)
        is ResponsibilityRouteClass.HOLD_FOR_RECONCILIATION
    )


def test_human_gate_is_classified_only_as_bounded_human_return() -> None:
    assert (
        compatibility_route_for_state(PathwayState.HUMAN_GATE)
        is ResponsibilityRouteClass.BOUNDED_HUMAN_RETURN
    )


def test_unreviewed_states_do_not_receive_implicit_route_semantics() -> None:
    assert compatibility_route_for_state(PathwayState.RUNNING) is None
    assert compatibility_route_for_state(PathwayState.REPAIR_REQUIRED) is None
    assert compatibility_route_for_state(PathwayState.READY_TO_RESUME) is None
