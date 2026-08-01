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


class StaticExecutor:
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


def open_runtime(pathway_db, attempt_db) -> ResponsibilityPathwayRuntime:
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(pathway_db),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_db),
        rpe=AllowAllDevelopmentEvaluator(),
    )


def test_restart_preserves_latest_resume_authorization_and_rejects_stale_attempt(tmp_path) -> None:
    pathway_id = "p-resume-restart"
    pathway_db = tmp_path / "pathways.sqlite3"
    attempt_db = tmp_path / "attempts.sqlite3"
    runtime = open_runtime(pathway_db, attempt_db)
    runtime.register(
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
        idempotency_key="register-resume-restart",
    )
    runtime.transition(pathway_id, PathwayState.APPROVED, actor="reviewer", reason="approved")
    coordinator = RepairCoordinator(runtime)

    initial = request("attempt-initial")
    runtime.execute(
        pathway_id,
        initial,
        actor="agent",
        executor=StaticExecutor(ExecutionResult(ExecutionStatus.FAILED, reason="initial_failure")),
    )
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=initial.attempt_id,
        repair_evidence={"cycle": 1, "validation": "passed"},
        reason="first repair complete",
    )

    retry_one = request("attempt-retry-one")
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=initial.attempt_id,
        next_attempt_id=retry_one.attempt_id,
        reason="first retry authorized",
    )
    runtime.execute(
        pathway_id,
        retry_one,
        actor="agent",
        executor=StaticExecutor(ExecutionResult(ExecutionStatus.FAILED, reason="retry_one_failure")),
    )
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=retry_one.attempt_id,
        repair_evidence={"cycle": 2, "validation": "passed"},
        reason="second repair complete",
    )

    retry_two = request("attempt-retry-two")
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=retry_one.attempt_id,
        next_attempt_id=retry_two.attempt_id,
        reason="second retry authorized",
    )
    evidence_before_restart = runtime.evidence(pathway_id)
    assert runtime.store.get_state(pathway_id) is PathwayState.RUNNING

    restarted = open_runtime(pathway_db, attempt_db)
    assert restarted.store.get_state(pathway_id) is PathwayState.RUNNING
    assert restarted.evidence(pathway_id) == evidence_before_restart

    stale_executor = StaticExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            readback=ReadbackEvidence(True, {"applied": True}),
        )
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        restarted.execute(pathway_id, retry_one, actor="agent", executor=stale_executor)

    assert stale_executor.calls == 0
    assert restarted.store.get_state(pathway_id) is PathwayState.RUNNING
    assert restarted.evidence(pathway_id) == evidence_before_restart

    current_executor = StaticExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "retry-two"},
            ReadbackEvidence(True, {"applied": True}),
        )
    )
    result = restarted.execute(pathway_id, retry_two, actor="agent", executor=current_executor)

    assert result.status is ExecutionStatus.SUCCEEDED
    assert current_executor.calls == 1
    assert restarted.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert restarted.verify_evidence(pathway_id).valid
