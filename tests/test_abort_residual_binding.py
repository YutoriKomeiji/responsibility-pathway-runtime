# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from copy import deepcopy

import pytest

from rpr.authority import AuthorityError
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.repair import RepairCoordinator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


def definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="external_mutation",
        action_class=ActionClass.REVERSIBLE_EXTERNAL,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority="reviewer",
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_dispatch",
        residual_owner="owner",
    )


def test_generic_abort_cannot_bypass_residual_closure(tmp_path) -> None:
    pathway_id = "p-abort-residual-binding"
    store_path = tmp_path / "pathways.sqlite3"
    runtime = ResponsibilityPathwayRuntime(store=SQLiteStore(store_path))
    registration = runtime.register(definition(pathway_id), idempotency_key="register-abort")
    assert registration.state is PathwayState.HUMAN_GATE
    before = deepcopy(runtime.evidence(pathway_id))

    with pytest.raises(AuthorityError, match="residual closure evidence"):
        runtime.transition(
            pathway_id,
            PathwayState.ABORTED,
            actor="owner",
            reason="must not abort without residual evidence",
        )

    assert runtime.store.get_state(pathway_id) is PathwayState.HUMAN_GATE
    assert runtime.evidence(pathway_id) == before
    assert runtime.verify_evidence(pathway_id).valid


def test_residual_owner_can_abort_with_durable_impact_evidence(tmp_path) -> None:
    pathway_id = "p-abort-residual-closure"
    store_path = tmp_path / "pathways.sqlite3"
    runtime = ResponsibilityPathwayRuntime(store=SQLiteStore(store_path))
    runtime.register(definition(pathway_id), idempotency_key="register-residual")
    coordinator = RepairCoordinator(runtime)
    before = deepcopy(runtime.evidence(pathway_id))

    with pytest.raises(AuthorityError, match="residual_owner"):
        coordinator.abort_with_residuals(
            pathway_id,
            actor="support",
            residuals={"external_record": "still_present"},
            reason="unauthorized residual closure",
        )

    assert runtime.store.get_state(pathway_id) is PathwayState.HUMAN_GATE
    assert runtime.evidence(pathway_id) == before

    coordinator.abort_with_residuals(
        pathway_id,
        actor="owner",
        residuals={
            "external_record": "still_present",
            "follow_up": "manual deletion ticket OPS-42",
            "impact_scope": "single test record",
        },
        reason="bounded operation abandoned with assigned residual work",
    )

    assert runtime.store.get_state(pathway_id) is PathwayState.ABORTED
    event = runtime.evidence(pathway_id)[-1]
    assert event["event_type"] == "residual_closure"
    assert event["actor"] == "owner"
    assert event["payload"]["residual_owner"] == "owner"
    assert event["payload"]["residuals"]["follow_up"] == "manual deletion ticket OPS-42"
    assert runtime.verify_evidence(pathway_id).valid

    restarted = ResponsibilityPathwayRuntime(store=SQLiteStore(store_path))
    assert restarted.store.get_state(pathway_id) is PathwayState.ABORTED
    assert restarted.evidence(pathway_id) == runtime.evidence(pathway_id)
    assert restarted.verify_evidence(pathway_id).valid
