# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus
from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    PathwayState,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
)
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus
from rpr.route_visibility import build_route_visibility
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class AmbiguousExecutor:
    def __init__(self, external_state: dict[str, object]) -> None:
        self.external_state = external_state
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        self.external_state[request.operation_id] = {
            "attempt_id": request.attempt_id,
            "applied": True,
        }
        return ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            reason="transport_lost_after_write",
        )


class ReadbackReconciler:
    def __init__(self, external_state: dict[str, object]) -> None:
        self.external_state = external_state
        self.calls = 0

    def reconcile(self, request, attempt):
        self.calls += 1
        observed = self.external_state.get(request.operation_id)
        assert attempt.attempt_id == request.attempt_id
        assert observed == {"attempt_id": request.attempt_id, "applied": True}
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"operation_id": request.operation_id, "applied": True},
            "independent_readback_verified",
        )


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
        human_return_point="before_exceptional_manual_decision",
        residual_owner="owner",
        responsibility_route=ResponsibilityRoute(
            route_class=ResponsibilityRouteClass.HOLD_FOR_RECONCILIATION,
            source_holder="agent",
            destination="audit",
            receiver_eligibility=ReceiverEligibility.ELIGIBLE,
            authority_class="evidence_authority",
            delegation_scope="readback-only reconciliation",
            unresolved_payload=("external_effect",),
            allowed_next_actions=("readback", "reconcile"),
            closure_condition="effect state verified",
            reevaluation_condition="authority, receiver, or environment changes",
            residual_owner="owner",
        ),
    )


def route_visibility(runtime: ResponsibilityPathwayRuntime, pathway_id: str):
    return build_route_visibility(
        state=runtime.store.get_state(pathway_id).value,
        definition=runtime.store.get_definition(pathway_id).to_dict(),
    )


def test_responsibility_routing_survives_ambiguous_write_restart_and_reconciliation(tmp_path) -> None:
    pathway_id = "p-routing-product-e2e"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    registered = runtime.register(definition(pathway_id), idempotency_key="register-routing-e2e")
    assert registered.state is PathwayState.AWAITING_APPROVAL

    runtime.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="bounded execution approved",
    )

    request = ExecutionRequest(
        operation_id="operation-routing-e2e",
        attempt_id="attempt-routing-e2e",
        idempotency_key="idempotency-routing-e2e",
        action="external_mutation",
        parameters={"resource_id": "resource-1"},
    )
    external_state: dict[str, object] = {}
    executor = AmbiguousExecutor(external_state)
    result = runtime.execute(pathway_id, request, actor="agent", executor=executor)

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1
    assert runtime.store.get_state(pathway_id) is PathwayState.WRITE_STATUS_UNKNOWN

    unresolved_route = route_visibility(runtime, pathway_id)
    assert unresolved_route["compatibility_route"] == "hold_for_reconciliation"
    assert unresolved_route["declared_route"]["route_class"] == "hold_for_reconciliation"
    assert unresolved_route["declared_route"]["receiver_eligibility"] == "eligible"
    assert unresolved_route["declared_route"]["allowed_next_actions"] == ["readback", "reconcile"]
    assert unresolved_route["residual_owner"] == "owner"
    assert unresolved_route["authority_inferred"] is False

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    restarted_route = route_visibility(restarted, pathway_id)
    assert restarted_route == unresolved_route

    replay = restarted.execute(pathway_id, request, actor="agent", executor=executor)
    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1

    reconciler = ReadbackReconciler(external_state)
    reconciled = restarted.reconcile(
        pathway_id,
        request,
        actor="audit",
        strategy=reconciler,
    )
    assert reconciled.status is ExecutionStatus.SUCCEEDED
    assert reconciler.calls == 1
    assert executor.calls == 1
    assert restarted.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert restarted.verify_evidence(pathway_id).valid

    completed_route = route_visibility(restarted, pathway_id)
    assert completed_route["compatibility_route"] is None
    assert completed_route["declared_route"]["route_class"] == "hold_for_reconciliation"
    assert completed_route["authority_inferred"] is False
    assert completed_route["residual_owner"] == "owner"
