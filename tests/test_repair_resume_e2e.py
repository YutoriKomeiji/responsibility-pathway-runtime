# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, LocalFileExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.repair import CompensationRecord, RepairCoordinator
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


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
        human_return_point="before_retry",
        residual_owner="owner",
    )


class FailedExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.FAILED,
            evidence={"attempt_id": request.attempt_id, "diagnostic": "precondition_failed"},
            reason="stale_target_version",
        )


def runtime_for(tmp_path, pathway_id: str) -> ResponsibilityPathwayRuntime:
    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / f"{pathway_id}-pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / f"{pathway_id}-attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    runtime.transition(pathway_id, PathwayState.APPROVED, actor="reviewer", reason="approved")
    return runtime


def test_failed_execution_repair_resume_and_new_attempt_complete(tmp_path) -> None:
    pathway_id = "p-repair-e2e"
    runtime = runtime_for(tmp_path, pathway_id)
    failed_request = ExecutionRequest(
        "op-failed",
        "attempt-failed",
        "idem-failed",
        "replace_text_file",
        {"path": "result.txt", "content": "old"},
    )
    failed_executor = FailedExecutor()

    failed = runtime.execute(pathway_id, failed_request, actor="agent", executor=failed_executor)

    assert failed.status is ExecutionStatus.FAILED
    assert failed_executor.calls == 1
    assert runtime.store.get_state(pathway_id) is PathwayState.REPAIR_REQUIRED

    coordinator = RepairCoordinator(runtime)
    with pytest.raises(ValueError, match="repair_evidence"):
        coordinator.complete_repair(
            pathway_id,
            actor="support",
            prior_attempt_id="attempt-failed",
            repair_evidence={},
            reason="missing evidence",
        )

    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id="attempt-failed",
        repair_evidence={"target_version": "v2", "validation": "passed"},
        compensation=CompensationRecord(
            action="restore_precondition_snapshot",
            authority="support",
            outcome="verified",
            evidence={"snapshot": "v2"},
        ),
        reason="precondition repaired and compensation verified",
    )
    assert runtime.store.get_state(pathway_id) is PathwayState.READY_TO_RESUME

    with pytest.raises(AuthorityError):
        coordinator.resume(
            pathway_id,
            actor="intruder",
            prior_attempt_id="attempt-failed",
            next_attempt_id="attempt-resumed",
            reason="unauthorized",
        )

    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id="attempt-failed",
        next_attempt_id="attempt-resumed",
        reason="repair evidence accepted",
    )
    assert runtime.store.get_state(pathway_id) is PathwayState.RUNNING

    resumed_request = ExecutionRequest(
        "op-resumed",
        "attempt-resumed",
        "idem-resumed",
        "replace_text_file",
        {"path": "result.txt", "content": "repaired output\n"},
    )
    result = runtime.execute(
        pathway_id,
        resumed_request,
        actor="agent",
        executor=LocalFileExecutor(tmp_path / "workspace"),
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert runtime.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert runtime.attempt_ledger.get("attempt-failed").status == ExecutionStatus.FAILED.value
    assert runtime.attempt_ledger.get("attempt-resumed").status == ExecutionStatus.SUCCEEDED.value
    events = runtime.evidence(pathway_id)
    repair_event = next(event for event in events if event["event_type"] == "repair_completed")
    resume_event = next(event for event in events if event["event_type"] == "pathway_resumed")
    assert repair_event["payload"]["prior_attempt_id"] == "attempt-failed"
    assert repair_event["payload"]["compensation"]["action"] == "restore_precondition_snapshot"
    assert resume_event["payload"]["next_attempt_id"] == "attempt-resumed"
    assert runtime.verify_evidence(pathway_id).valid


def test_residual_owner_closes_non_reversible_abort(tmp_path) -> None:
    pathway_id = "p-residual-close-active"
    runtime = runtime_for(tmp_path, pathway_id)
    request = ExecutionRequest("op-x", "attempt-x", "idem-x", "replace_text_file", {"path": "x", "content": "x"})
    runtime.execute(pathway_id, request, actor="agent", executor=FailedExecutor())
    coordinator = RepairCoordinator(runtime)

    with pytest.raises(AuthorityError):
        coordinator.abort_with_residuals(
            pathway_id,
            actor="support",
            residuals={"remote_effect": "cannot_be_reversed"},
            reason="repair not viable",
        )

    coordinator.abort_with_residuals(
        pathway_id,
        actor="owner",
        residuals={"remote_effect": "cannot_be_reversed", "accepted_by": "owner"},
        reason="residual impact accepted after failed repair",
    )

    assert runtime.store.get_state(pathway_id) is PathwayState.ABORTED
    event = runtime.evidence(pathway_id)[-1]
    assert event["event_type"] == "residual_closure"
    assert event["payload"]["residual_owner"] == "owner"
    assert runtime.verify_evidence(pathway_id).valid
