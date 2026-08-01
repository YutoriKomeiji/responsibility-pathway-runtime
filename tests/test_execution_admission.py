# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


def definition(pathway_id: str = "p-admission") -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="replace_text_file",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_write",
        residual_owner="owner",
    )


def request(attempt_id: str = "attempt-1") -> ExecutionRequest:
    return ExecutionRequest(
        operation_id="operation-1",
        attempt_id=attempt_id,
        idempotency_key="write-1",
        action="replace_text_file",
        parameters={"path": "result.txt", "content": "hello"},
    )


class CountingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, execution_request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"operation_id": execution_request.operation_id},
            ReadbackEvidence(True, {"sha256": "verified"}),
        )


def test_non_executable_pathway_does_not_leave_started_attempt() -> None:
    ledger = SQLiteExecutionAttemptLedger()
    runtime = ResponsibilityPathwayRuntime(attempt_ledger=ledger)
    registration = runtime.register(definition(), idempotency_key="pathway-1")
    assert registration.state is PathwayState.HUMAN_GATE

    executor = CountingExecutor()
    with pytest.raises(ValueError, match="pathway must be approved or running"):
        runtime.execute("p-admission", request(), actor="agent", executor=executor)

    assert executor.calls == 0
    with pytest.raises(KeyError):
        ledger.get("attempt-1")


def test_unauthorized_actor_does_not_leave_started_attempt() -> None:
    ledger = SQLiteExecutionAttemptLedger()
    runtime = ResponsibilityPathwayRuntime(
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=ledger,
    )
    registration = runtime.register(definition(), idempotency_key="pathway-2")
    assert registration.state is PathwayState.APPROVED

    executor = CountingExecutor()
    with pytest.raises(AuthorityError):
        runtime.execute("p-admission", request(), actor="intruder", executor=executor)

    assert executor.calls == 0
    assert runtime.store.get_state("p-admission") is PathwayState.APPROVED
    with pytest.raises(KeyError):
        ledger.get("attempt-1")


def test_completed_attempt_still_replays_without_redispatch() -> None:
    ledger = SQLiteExecutionAttemptLedger()
    runtime = ResponsibilityPathwayRuntime(
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=ledger,
    )
    runtime.register(definition(), idempotency_key="pathway-3")

    executor = CountingExecutor()
    first = runtime.execute("p-admission", request(), actor="agent", executor=executor)
    second = runtime.execute("p-admission", request(), actor="agent", executor=executor)

    assert first.status is ExecutionStatus.SUCCEEDED
    assert second == first
    assert executor.calls == 1
    assert runtime.store.get_state("p-admission") is PathwayState.COMPLETED
