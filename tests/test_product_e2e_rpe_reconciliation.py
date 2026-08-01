# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus
from rpr.rpe import PythonRpeEvaluator
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
            "idempotency_key": request.idempotency_key,
            "applied": True,
        }
        return ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            reason="transport_lost_after_write",
        )


class ExternalStateReconciler:
    def __init__(self, external_state: dict[str, object]) -> None:
        self.external_state = external_state
        self.calls = 0

    def reconcile(self, request, attempt):
        self.calls += 1
        observed = self.external_state.get(request.operation_id)
        assert attempt.attempt_id == request.attempt_id
        assert observed == {
            "attempt_id": request.attempt_id,
            "idempotency_key": request.idempotency_key,
            "applied": True,
        }
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {
                "operation_id": request.operation_id,
                "attempt_id": request.attempt_id,
                "idempotency_key": request.idempotency_key,
                "applied": True,
            },
            "independent_readback_verified",
        )


def test_rpe_to_reconciliation_product_e2e_survives_restart(tmp_path) -> None:
    pathway_id = "p-product-e2e-reconciliation"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    captured: list[dict[str, object]] = []

    def evaluate_action(action_request, requirement_packs):
        captured.append(action_request)
        assert tuple(requirement_packs) == ({"pack_id": "pack-e2e-1"},)
        return {
            "decision": "allow",
            "reason_codes": ["requirements_satisfied"],
            "contract_version": "rpe-rpr-v1",
        }

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-e2e-1"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    definition = PathwayDefinition(
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
        human_return_point="before_retry",
        residual_owner="owner",
    )
    registration = runtime.register(definition, idempotency_key="register-product-e2e")
    assert registration.decision.value == "allow"
    assert registration.state is PathwayState.AWAITING_APPROVAL
    assert registration.reason_codes[-1] == "requirements_satisfied"
    assert captured[0]["action"] == definition.action_name
    assert captured[0]["responsibility_pathway"]["pathway_id"] == pathway_id

    runtime.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="customer-authorized execution",
    )
    request = ExecutionRequest(
        "operation-product-e2e",
        "attempt-product-e2e",
        "idempotency-product-e2e",
        "external_mutation",
        {"resource_id": "resource-1"},
    )
    external_state: dict[str, object] = {}
    executor = AmbiguousExecutor(external_state)
    result = runtime.execute(pathway_id, request, actor="agent", executor=executor)

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1
    assert runtime.store.get_state(pathway_id) is PathwayState.WRITE_STATUS_UNKNOWN

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-e2e-1"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    reconciler = ExternalStateReconciler(external_state)
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
    persisted = restarted.attempt_ledger.get(request.attempt_id)
    assert persisted.result_json is not None
    assert persisted.result_json["status"] == ExecutionStatus.SUCCEEDED.value
    assert restarted.verify_evidence(pathway_id).valid
