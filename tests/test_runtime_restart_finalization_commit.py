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


class CrashAfterFinalizationCommitRuntime(ResponsibilityPathwayRuntime):
    """Commit the terminal/uncertain pathway state, then simulate process loss."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.crash_once = True

    def transition(self, pathway_id, target, *, actor, reason):
        state = super().transition(pathway_id, target, actor=actor, reason=reason)
        if self.crash_once and target in {
            PathwayState.COMPLETED,
            PathwayState.REPAIR_REQUIRED,
            PathwayState.WRITE_STATUS_UNKNOWN,
        }:
            self.crash_once = False
            raise RuntimeError("injected_crash_after_finalization_commit")
        return state


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


def request(pathway_id: str) -> ExecutionRequest:
    return ExecutionRequest(
        f"op-{pathway_id}",
        f"attempt-{pathway_id}",
        f"idem-{pathway_id}",
        "external_mutation",
        {"value": 1},
    )


@pytest.mark.parametrize(
    ("pathway_id", "result", "expected_state"),
    [
        (
            "p-success",
            ExecutionResult(
                ExecutionStatus.SUCCEEDED,
                {"write_id": "42"},
                ReadbackEvidence(True, {"applied": True}),
            ),
            PathwayState.COMPLETED,
        ),
        (
            "p-failure",
            ExecutionResult(
                ExecutionStatus.FAILED,
                {"error_code": "E42"},
                reason="remote_rejected",
            ),
            PathwayState.REPAIR_REQUIRED,
        ),
        (
            "p-unknown",
            ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                reason="timeout_after_send",
            ),
            PathwayState.WRITE_STATUS_UNKNOWN,
        ),
    ],
)
def test_restart_after_finalization_commit_is_idempotent_and_never_redispatches(
    tmp_path,
    pathway_id: str,
    result: ExecutionResult,
    expected_state: PathwayState,
) -> None:
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    crashing = CrashAfterFinalizationCommitRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    crashing.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    execution_request = request(pathway_id)
    first_executor = CountingExecutor(result)

    with pytest.raises(RuntimeError, match="injected_crash_after_finalization_commit"):
        crashing.execute(
            pathway_id,
            execution_request,
            actor="agent",
            executor=first_executor,
        )

    assert first_executor.calls == 1
    assert crashing.store.get_state(pathway_id) is expected_state
    assert crashing.attempt_ledger.get(execution_request.attempt_id).result_json is not None
    event_count_after_commit = len(crashing.evidence(pathway_id))
    assert crashing.verify_evidence(pathway_id).valid

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    forbidden_executor = CountingExecutor(ExecutionResult(ExecutionStatus.FAILED))

    first_replay = restarted.execute(
        pathway_id,
        execution_request,
        actor="agent",
        executor=forbidden_executor,
    )
    second_replay = restarted.execute(
        pathway_id,
        execution_request,
        actor="agent",
        executor=forbidden_executor,
    )

    assert first_replay.status is result.status
    assert second_replay.status is result.status
    assert forbidden_executor.calls == 0
    assert restarted.store.get_state(pathway_id) is expected_state
    assert len(restarted.evidence(pathway_id)) == event_count_after_commit
    assert restarted.verify_evidence(pathway_id).valid
