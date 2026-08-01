# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.repair import RepairCoordinator
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class CountingExecutor:
    def __init__(self, result: ExecutionResult) -> None:
        self.result = result
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return self.result


def request(attempt_id: str) -> ExecutionRequest:
    return ExecutionRequest(
        f"op-{attempt_id}",
        attempt_id,
        f"idem-{attempt_id}",
        "external_mutation",
        {"attempt": attempt_id},
    )


def runtime(tmp_path) -> ResponsibilityPathwayRuntime:
    pathway_id = "p-retry-rotation"
    value = ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    value.register(
        PathwayDefinition(
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
        ),
        idempotency_key="register-retry-rotation",
    )
    value.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="approved for retry authorization rotation test",
    )
    return value


def test_latest_resume_authorization_replaces_earlier_retry_attempt(tmp_path) -> None:
    pathway_id = "p-retry-rotation"
    value = runtime(tmp_path)
    coordinator = RepairCoordinator(value)

    initial = request("attempt-initial")
    first = value.execute(
        pathway_id,
        initial,
        actor="agent",
        executor=CountingExecutor(
            ExecutionResult(ExecutionStatus.FAILED, reason="initial_failure")
        ),
    )
    assert first.status is ExecutionStatus.FAILED

    retry_one = request("attempt-retry-one")
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=initial.attempt_id,
        repair_evidence={"cycle": 1, "validation": "passed"},
        reason="first repair complete",
    )
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=initial.attempt_id,
        next_attempt_id=retry_one.attempt_id,
        reason="first retry authorized",
    )
    second = value.execute(
        pathway_id,
        retry_one,
        actor="agent",
        executor=CountingExecutor(
            ExecutionResult(ExecutionStatus.FAILED, reason="retry_one_failure")
        ),
    )
    assert second.status is ExecutionStatus.FAILED

    retry_two = request("attempt-retry-two")
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=retry_one.attempt_id,
        repair_evidence={"cycle": 2, "validation": "passed"},
        reason="second repair complete",
    )
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=retry_one.attempt_id,
        next_attempt_id=retry_two.attempt_id,
        reason="second retry authorized",
    )

    stale_executor = CountingExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            readback=ReadbackEvidence(True, {"applied": True}),
        )
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        value.execute(
            pathway_id,
            retry_one,
            actor="agent",
            executor=stale_executor,
        )
    assert stale_executor.calls == 0
    assert value.store.get_state(pathway_id) is PathwayState.RUNNING

    current_executor = CountingExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "retry-two"},
            ReadbackEvidence(True, {"applied": True}),
        )
    )
    result = value.execute(
        pathway_id,
        retry_two,
        actor="agent",
        executor=current_executor,
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert current_executor.calls == 1
    assert value.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert value.verify_evidence(pathway_id).valid
