# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, LocalFileExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus, reconcile_started_attempt
from rpr.rpe import PythonRpeEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


def definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="replace_text_file",
        action_class=ActionClass.REVERSIBLE_EXTERNAL,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority="reviewer",
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_write",
        residual_owner="owner",
    )


def allow_action(action_request, packs):
    assert action_request["action"] == "replace_text_file"
    assert tuple(packs) == ({"pack_id": "rp-e2e"},)
    return {
        "decision": "allow",
        "reason_codes": ["requirements_satisfied"],
        "contract_version": "m1",
    }


def approve(runtime: ResponsibilityPathwayRuntime, pathway_id: str) -> None:
    runtime.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="bounded reversible change approved",
    )


def test_rpe_to_runtime_to_file_readback_completes(tmp_path):
    attempts_db = tmp_path / "attempts.sqlite3"
    evaluator = PythonRpeEvaluator(
        allow_action,
        [{"pack_id": "rp-e2e"}],
        expected_contract_version="m1",
    )
    runtime = ResponsibilityPathwayRuntime(
        rpe=evaluator,
        attempt_ledger=SQLiteExecutionAttemptLedger(attempts_db),
    )
    registered = runtime.register(definition("p-e2e-success"), idempotency_key="register-1")
    assert registered.state is PathwayState.AWAITING_APPROVAL
    assert registered.decision.value == "allow"
    assert "requirements_satisfied" in registered.reason_codes
    approve(runtime, "p-e2e-success")

    request = ExecutionRequest(
        operation_id="op-1",
        attempt_id="attempt-1",
        idempotency_key="write-1",
        action="replace_text_file",
        parameters={"path": "result.txt", "content": "governed output\n"},
    )
    result = runtime.execute(
        "p-e2e-success",
        request,
        actor="agent",
        executor=LocalFileExecutor(tmp_path / "workspace"),
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert runtime.store.get_state("p-e2e-success") is PathwayState.COMPLETED
    assert (tmp_path / "workspace" / "result.txt").read_text() == "governed output\n"
    assert runtime.verify_evidence("p-e2e-success").valid


class UnknownAfterDispatchExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            evidence={"operation_id": request.operation_id},
            reason="connection_lost_after_dispatch",
        )


def test_unknown_result_is_persisted_and_not_redispatched(tmp_path):
    ledger_path = tmp_path / "attempts.sqlite3"
    runtime = ResponsibilityPathwayRuntime(
        rpe=PythonRpeEvaluator(allow_action, [{"pack_id": "rp-e2e"}], expected_contract_version="m1"),
        attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
    )
    registered = runtime.register(definition("p-e2e-unknown"), idempotency_key="register-2")
    assert registered.state is PathwayState.AWAITING_APPROVAL
    approve(runtime, "p-e2e-unknown")
    request = ExecutionRequest(
        operation_id="op-unknown",
        attempt_id="attempt-unknown",
        idempotency_key="write-unknown",
        action="replace_text_file",
        parameters={"path": "unknown.txt", "content": "maybe written"},
    )
    executor = UnknownAfterDispatchExecutor()

    first = runtime.execute("p-e2e-unknown", request, actor="agent", executor=executor)
    second = runtime.execute("p-e2e-unknown", request, actor="agent", executor=executor)

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert second.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1
    assert runtime.store.get_state("p-e2e-unknown") is PathwayState.WRITE_STATUS_UNKNOWN


@dataclass
class AppliedObserver:
    calls: int = 0

    def reconcile(self, request, attempt):
        self.calls += 1
        assert request.attempt_id == attempt.attempt_id
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"resource_id": "item-42", "observer": "read_api"},
            "independent_readback_confirmed",
        )


def test_unresolved_started_attempt_can_be_reconciled_without_redispatch(tmp_path):
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    request = ExecutionRequest(
        operation_id="op-reconcile",
        attempt_id="attempt-reconcile",
        idempotency_key="write-reconcile",
        action="http_json_mutation",
        parameters={"url": "https://example.invalid/items", "id": "item-42"},
    )
    replayed, _ = ledger.begin("p-reconcile", request)
    assert not replayed

    observer = AppliedObserver()
    result = reconcile_started_attempt(
        pathway_id="p-reconcile",
        request=request,
        ledger=ledger,
        strategy=observer,
    )

    assert observer.calls == 1
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert result.evidence["reconciliation"]["resource_id"] == "item-42"
    assert ledger.get("attempt-reconcile").result_json is not None
