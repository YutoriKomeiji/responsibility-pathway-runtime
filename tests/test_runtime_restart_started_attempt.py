# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class CrashAfterBeginLedger(SQLiteExecutionAttemptLedger):
    """Persist the started attempt, then simulate process loss before state transition."""

    def __init__(self, database) -> None:
        super().__init__(database)
        self.crash_once = True

    def begin(self, pathway_id, request):
        result = super().begin(pathway_id, request)
        if self.crash_once and not result[0]:
            self.crash_once = False
            raise RuntimeError("injected_crash_after_attempt_begin")
        return result


class CrashAfterRunningCommitRuntime(ResponsibilityPathwayRuntime):
    """Commit the bound RUNNING state, then simulate loss before executor dispatch."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.crash_once = True

    def _start_execution_pathway(self, pathway_id, request, actor):
        super()._start_execution_pathway(pathway_id, request, actor)
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("injected_crash_after_running_commit")


class CountingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "42"},
            ReadbackEvidence(True, {"applied": True}),
        )


def definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="external_mutation",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="auditor",
        repair_owner="repairer",
        resume_authority="resumer",
        human_return_point="before_retry",
        residual_owner="owner",
    )


def request(attempt_id: str) -> ExecutionRequest:
    return ExecutionRequest(
        "op-restart",
        attempt_id,
        f"idem-{attempt_id}",
        "external_mutation",
        {"value": 1},
    )


def runtime_paths(tmp_path):
    return tmp_path / "pathways.sqlite3", tmp_path / "attempts.sqlite3"


def test_restart_safely_retries_started_attempt_while_pathway_is_still_approved(tmp_path) -> None:
    store_path, attempt_path = runtime_paths(tmp_path)
    crashing = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=CrashAfterBeginLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    crashing.register(definition("p-pre-dispatch"), idempotency_key="register-pre")
    execution_request = request("attempt-pre")

    with pytest.raises(RuntimeError, match="injected_crash_after_attempt_begin"):
        crashing.execute(
            "p-pre-dispatch",
            execution_request,
            actor="agent",
            executor=CountingExecutor(),
        )

    assert crashing.store.get_state("p-pre-dispatch") is PathwayState.APPROVED
    assert crashing.attempt_ledger.get(execution_request.attempt_id).status == "started"

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    executor = CountingExecutor()
    result = restarted.execute(
        "p-pre-dispatch",
        execution_request,
        actor="agent",
        executor=executor,
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert executor.calls == 1
    assert restarted.store.get_state("p-pre-dispatch") is PathwayState.COMPLETED
    assert restarted.attempt_ledger.get(execution_request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert [event["event_type"] for event in restarted.evidence("p-pre-dispatch")].count(
        "execution_pre_dispatch_restart_recovered"
    ) == 1
    assert restarted.verify_evidence("p-pre-dispatch").valid


def test_restart_never_redispatches_started_attempt_after_running_commit(tmp_path) -> None:
    store_path, attempt_path = runtime_paths(tmp_path)
    crashing = CrashAfterRunningCommitRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    crashing.register(definition("p-running"), idempotency_key="register-running")
    execution_request = request("attempt-running")

    with pytest.raises(RuntimeError, match="injected_crash_after_running_commit"):
        crashing.execute(
            "p-running",
            execution_request,
            actor="agent",
            executor=CountingExecutor(),
        )

    assert crashing.store.get_state("p-running") is PathwayState.RUNNING
    attempt = crashing.attempt_ledger.get(execution_request.attempt_id)
    assert attempt.status == "started"
    assert attempt.result_json is None

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    executor = CountingExecutor()
    result = restarted.execute(
        "p-running",
        execution_request,
        actor="agent",
        executor=executor,
    )

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "prior_attempt_started_without_persisted_result"
    assert executor.calls == 0
    assert restarted.store.get_state("p-running") is PathwayState.WRITE_STATUS_UNKNOWN
    assert restarted.attempt_ledger.get(execution_request.attempt_id).result_json is None
    assert restarted.verify_evidence("p-running").valid

    replay = restarted.execute(
        "p-running",
        execution_request,
        actor="agent",
        executor=executor,
    )
    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 0
