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


class CrashAfterFinishLedger(SQLiteExecutionAttemptLedger):
    """Persist the execution result, then simulate process loss before pathway finalization."""

    def __init__(self, database) -> None:
        super().__init__(database)
        self.crash_once = True

    def finish(self, attempt_id, result):
        record = super().finish(attempt_id, result)
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("injected_crash_after_attempt_finish")
        return record


class CountingExecutor:
    def __init__(self, result: ExecutionResult) -> None:
        self.result = result
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return self.result


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
        "op-finished-restart",
        attempt_id,
        f"idem-{attempt_id}",
        "external_mutation",
        {"value": 1},
    )


def runtime_paths(tmp_path):
    return tmp_path / "pathways.sqlite3", tmp_path / "attempts.sqlite3"


def crash_after_persisting_result(tmp_path, pathway_id: str, execution_result: ExecutionResult):
    store_path, attempt_path = runtime_paths(tmp_path)
    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=CrashAfterFinishLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    execution_request = request(f"attempt-{pathway_id}")
    executor = CountingExecutor(execution_result)

    with pytest.raises(RuntimeError, match="injected_crash_after_attempt_finish"):
        runtime.execute(pathway_id, execution_request, actor="agent", executor=executor)

    assert executor.calls == 1
    assert runtime.store.get_state(pathway_id) is PathwayState.RUNNING
    assert runtime.attempt_ledger.get(execution_request.attempt_id).result_json is not None
    return store_path, attempt_path, execution_request


def test_restart_finalizes_persisted_verified_success_without_redispatch(tmp_path) -> None:
    store_path, attempt_path, execution_request = crash_after_persisting_result(
        tmp_path,
        "p-success",
        ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"write_id": "42"},
            ReadbackEvidence(True, {"applied": True}),
        ),
    )
    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    executor = CountingExecutor(ExecutionResult(ExecutionStatus.FAILED))

    replay = restarted.execute("p-success", execution_request, actor="agent", executor=executor)

    assert replay.status is ExecutionStatus.SUCCEEDED
    assert executor.calls == 0
    assert restarted.store.get_state("p-success") is PathwayState.COMPLETED
    assert restarted.verify_evidence("p-success").valid


def test_restart_finalizes_persisted_failure_without_redispatch(tmp_path) -> None:
    store_path, attempt_path, execution_request = crash_after_persisting_result(
        tmp_path,
        "p-failure",
        ExecutionResult(ExecutionStatus.FAILED, {"error_code": "E42"}, reason="remote_rejected"),
    )
    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    executor = CountingExecutor(ExecutionResult(ExecutionStatus.SUCCEEDED))

    replay = restarted.execute("p-failure", execution_request, actor="agent", executor=executor)

    assert replay.status is ExecutionStatus.FAILED
    assert executor.calls == 0
    assert restarted.store.get_state("p-failure") is PathwayState.REPAIR_REQUIRED
    assert restarted.verify_evidence("p-failure").valid


def test_restart_finalizes_persisted_unknown_without_redispatch(tmp_path) -> None:
    store_path, attempt_path, execution_request = crash_after_persisting_result(
        tmp_path,
        "p-unknown",
        ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="timeout_after_send"),
    )
    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    executor = CountingExecutor(ExecutionResult(ExecutionStatus.SUCCEEDED))

    replay = restarted.execute("p-unknown", execution_request, actor="agent", executor=executor)

    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 0
    assert restarted.store.get_state("p-unknown") is PathwayState.WRITE_STATUS_UNKNOWN
    assert restarted.verify_evidence("p-unknown").valid
