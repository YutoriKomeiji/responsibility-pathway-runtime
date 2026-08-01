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


class BlockingResultExecutor:
    def __init__(self, result: ExecutionResult) -> None:
        self.result = result
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return self.result


class CrashAfterBeginLedger(SQLiteExecutionAttemptLedger):
    """Persist a new attempt, then simulate process loss before dispatch."""

    def __init__(self, database) -> None:
        super().__init__(database)
        self.crash_once = True

    def begin(self, pathway_id, execution_request):
        result = super().begin(pathway_id, execution_request)
        if self.crash_once and not result[0]:
            self.crash_once = False
            raise RuntimeError("injected_crash_after_resumed_attempt_begin")
        return result


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
        human_return_point="before_retry",
        residual_owner="owner",
    )


def request(attempt_id: str) -> ExecutionRequest:
    return ExecutionRequest(
        f"op-{attempt_id}",
        attempt_id,
        f"idem-{attempt_id}",
        "external_mutation",
        {"attempt": attempt_id},
    )


def runtime(tmp_path, pathway_id: str) -> ResponsibilityPathwayRuntime:
    tmp_path.mkdir(parents=True, exist_ok=True)
    value = ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    value.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    value.transition(pathway_id, PathwayState.APPROVED, actor="reviewer", reason="approved for retry-policy test")
    return value


def test_running_pathway_rejects_different_attempt_before_ledger_creation(tmp_path) -> None:
    value = runtime(tmp_path, "p-running-bound")
    first_request = request("attempt-first")
    replay_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="timeout_after_send")
    )
    first = value.execute("p-running-bound", first_request, actor="agent", executor=replay_executor)

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert value.store.get_state("p-running-bound") is PathwayState.WRITE_STATUS_UNKNOWN

    # Rebuild a live RUNNING fixture with the durable execution-start binding.
    value = runtime(tmp_path / "live", "p-live-bound")
    value.attempt_ledger.begin("p-live-bound", first_request)
    value._start_execution_pathway("p-live-bound", first_request, "agent")

    second_request = request("attempt-second")
    second_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.SUCCEEDED, readback=ReadbackEvidence(True, {"applied": True}))
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        value.execute("p-live-bound", second_request, actor="agent", executor=second_executor)

    assert second_executor.calls == 0
    with pytest.raises(KeyError):
        value.attempt_ledger.get("attempt-second")
    assert value.store.get_state("p-live-bound") is PathwayState.RUNNING
    assert value.verify_evidence("p-live-bound").valid


def test_resume_allows_only_the_authorized_next_attempt(tmp_path) -> None:
    value = runtime(tmp_path, "p-resume-bound")
    failed_request = request("attempt-failed")
    failed = value.execute(
        "p-resume-bound",
        failed_request,
        actor="agent",
        executor=BlockingResultExecutor(
            ExecutionResult(ExecutionStatus.FAILED, reason="precondition_failed")
        ),
    )
    assert failed.status is ExecutionStatus.FAILED

    coordinator = RepairCoordinator(value)
    coordinator.complete_repair(
        "p-resume-bound",
        actor="support",
        prior_attempt_id="attempt-failed",
        repair_evidence={"validation": "passed"},
        reason="repair complete",
    )
    coordinator.resume(
        "p-resume-bound",
        actor="manager",
        prior_attempt_id="attempt-failed",
        next_attempt_id="attempt-authorized",
        reason="retry authorized",
    )

    wrong_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.SUCCEEDED, readback=ReadbackEvidence(True, {"applied": True}))
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        value.execute(
            "p-resume-bound",
            request("attempt-wrong"),
            actor="agent",
            executor=wrong_executor,
        )
    assert wrong_executor.calls == 0
    with pytest.raises(KeyError):
        value.attempt_ledger.get("attempt-wrong")

    correct_executor = BlockingResultExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "retry-1"},
            ReadbackEvidence(True, {"applied": True}),
        )
    )
    result = value.execute(
        "p-resume-bound",
        request("attempt-authorized"),
        actor="agent",
        executor=correct_executor,
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert correct_executor.calls == 1
    assert value.store.get_state("p-resume-bound") is PathwayState.COMPLETED
    assert value.verify_evidence("p-resume-bound").valid


def test_restart_after_resume_commit_preserves_authorized_attempt_binding(tmp_path) -> None:
    pathway_id = "p-resume-restart-bound"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    value = runtime(tmp_path, pathway_id)
    failed_request = request("attempt-failed-before-restart")
    failed = value.execute(
        pathway_id,
        failed_request,
        actor="agent",
        executor=BlockingResultExecutor(
            ExecutionResult(ExecutionStatus.FAILED, reason="precondition_failed")
        ),
    )
    assert failed.status is ExecutionStatus.FAILED

    coordinator = RepairCoordinator(value)
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=failed_request.attempt_id,
        repair_evidence={"validation": "passed"},
        reason="repair complete before restart",
    )
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=failed_request.attempt_id,
        next_attempt_id="attempt-authorized-after-restart",
        reason="retry authorized before restart",
    )
    assert value.store.get_state(pathway_id) is PathwayState.RUNNING

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    wrong_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.SUCCEEDED, readback=ReadbackEvidence(True, {"applied": True}))
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        restarted.execute(
            pathway_id,
            request("attempt-wrong-after-restart"),
            actor="agent",
            executor=wrong_executor,
        )
    assert wrong_executor.calls == 0
    with pytest.raises(KeyError):
        restarted.attempt_ledger.get("attempt-wrong-after-restart")

    correct_executor = BlockingResultExecutor(
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "retry-after-restart"},
            ReadbackEvidence(True, {"applied": True}),
        )
    )
    result = restarted.execute(
        pathway_id,
        request("attempt-authorized-after-restart"),
        actor="agent",
        executor=correct_executor,
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert correct_executor.calls == 1
    assert restarted.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert restarted.verify_evidence(pathway_id).valid


def test_resumed_attempt_crash_after_begin_never_redispatches(tmp_path) -> None:
    pathway_id = "p-resumed-attempt-begin-crash"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    value = runtime(tmp_path, pathway_id)
    prior_request = request("attempt-prior-failed")
    failed = value.execute(
        pathway_id,
        prior_request,
        actor="agent",
        executor=BlockingResultExecutor(
            ExecutionResult(ExecutionStatus.FAILED, reason="precondition_failed")
        ),
    )
    assert failed.status is ExecutionStatus.FAILED

    coordinator = RepairCoordinator(value)
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=prior_request.attempt_id,
        repair_evidence={"validation": "passed"},
        reason="repair complete before resumed attempt crash",
    )
    authorized_request = request("attempt-authorized-crash")
    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=prior_request.attempt_id,
        next_attempt_id=authorized_request.attempt_id,
        reason="retry authorized before resumed attempt crash",
    )

    crashing = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=CrashAfterBeginLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    with pytest.raises(RuntimeError, match="injected_crash_after_resumed_attempt_begin"):
        crashing.execute(
            pathway_id,
            authorized_request,
            actor="agent",
            executor=BlockingResultExecutor(
                ExecutionResult(
                    ExecutionStatus.SUCCEEDED,
                    readback=ReadbackEvidence(True, {"applied": True}),
                )
            ),
        )

    assert crashing.store.get_state(pathway_id) is PathwayState.RUNNING
    started = crashing.attempt_ledger.get(authorized_request.attempt_id)
    assert started.status == "started"
    assert started.result_json is None

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    wrong_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.SUCCEEDED, readback=ReadbackEvidence(True, {"applied": True}))
    )
    with pytest.raises(ValueError, match="bound to attempt"):
        restarted.execute(
            pathway_id,
            request("attempt-wrong-after-begin-crash"),
            actor="agent",
            executor=wrong_executor,
        )
    assert wrong_executor.calls == 0
    with pytest.raises(KeyError):
        restarted.attempt_ledger.get("attempt-wrong-after-begin-crash")

    replay_executor = BlockingResultExecutor(
        ExecutionResult(ExecutionStatus.SUCCEEDED, readback=ReadbackEvidence(True, {"applied": True}))
    )
    replay = restarted.execute(
        pathway_id,
        authorized_request,
        actor="agent",
        executor=replay_executor,
    )
    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert replay.reason == "prior_attempt_started_without_persisted_result"
    assert replay_executor.calls == 0
    assert restarted.store.get_state(pathway_id) is PathwayState.WRITE_STATUS_UNKNOWN

    repeated = restarted.execute(
        pathway_id,
        authorized_request,
        actor="agent",
        executor=replay_executor,
    )
    assert repeated.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert replay_executor.calls == 0
    assert restarted.verify_evidence(pathway_id).valid
