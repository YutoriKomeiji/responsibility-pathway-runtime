# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import replace

from rpr.mcp_read_model import SQLiteReadModel
from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    PathwayState,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
)
from rpr.route_visibility import build_route_visibility
from rpr.storage import SQLiteStore


def _definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="inspect_record",
        action_class=ActionClass.OBSERVE_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="observer",
        stop_authority="operator",
        evidence_owner="auditor",
        repair_owner="repairer",
        resume_authority="resumer",
        human_return_point="operator_console",
        residual_owner="owner",
        metadata={"source": "test"},
    )


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


def test_visibility_classifies_human_gate_without_inferred_authority() -> None:
    definition = _definition("human-gate")
    value = build_route_visibility(
        state=PathwayState.HUMAN_GATE.value,
        definition=definition.to_dict(),
    )

    assert value["compatibility_route"] == ResponsibilityRouteClass.BOUNDED_HUMAN_RETURN.value
    assert value["declared_route"] is None
    assert value["authority_inferred"] is False
    assert value["human_return_point"] == "operator_console"
    assert value["residual_owner"] == "owner"


def test_visibility_classifies_unknown_write_as_reconciliation_hold() -> None:
    value = build_route_visibility(
        state=PathwayState.WRITE_STATUS_UNKNOWN.value,
        definition=_definition("unknown").to_dict(),
    )

    assert value["compatibility_route"] == ResponsibilityRouteClass.HOLD_FOR_RECONCILIATION.value
    assert value["authority_inferred"] is False


def test_visibility_preserves_declared_route_without_promoting_it_to_authority() -> None:
    definition = replace(_definition("declared"), responsibility_route=_route())
    value = build_route_visibility(
        state=PathwayState.RUNNING.value,
        definition=definition.to_dict(),
    )

    assert value["compatibility_route"] is None
    assert value["declared_route"] == _route().to_dict()
    assert value["authority_inferred"] is False


def test_read_model_exposes_internal_visibility_without_changing_pathway_shape(tmp_path) -> None:
    database = tmp_path / "rpr.sqlite3"
    store = SQLiteStore(database)
    definition = replace(_definition("p-1"), responsibility_route=_route())
    store.create_or_replay_pathway(definition, PathwayState.WRITE_STATUS_UNKNOWN, "idem-route")

    read_model = SQLiteReadModel(database)
    try:
        pathway = read_model.get_pathway("p-1")
        visibility = read_model.get_route_visibility("p-1")

        assert set(pathway) == {"pathway_id", "state", "definition", "created_at", "updated_at"}
        assert visibility["pathway_id"] == "p-1"
        assert visibility["compatibility_route"] == ResponsibilityRouteClass.HOLD_FOR_RECONCILIATION.value
        assert visibility["declared_route"] == _route().to_dict()
        assert visibility["authority_inferred"] is False
    finally:
        read_model.close()
