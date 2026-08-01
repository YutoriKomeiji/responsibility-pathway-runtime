# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from copy import deepcopy

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.repair import RepairCoordinator
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


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


def runtime_for(tmp_path, pathway_id: str) -> ResponsibilityPathwayRuntime:
    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / f"{pathway_id}-pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / f"{pathway_id}-attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    registration = runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    assert registration.state is PathwayState.AWAITING_APPROVAL
    runtime.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="fixture approval before bounded repair test",
    )
    return runtime


def request(attempt_id: str) -> ExecutionRequest:
    return ExecutionRequest(
        f"operation-{attempt_id}",
        attempt_id,
        f"idempotency-{attempt_id}",
        "external_mutation",
        {"value": attempt_id},
    )


class FailedExecutor:
    def execute(self, execution_request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            ExecutionStatus.FAILED,
            evidence={"attempt_id": execution_request.attempt_id},
            reason="fixture failure",
        )


def persist_result(
    runtime: ResponsibilityPathwayRuntime,
    pathway_id: str,
    attempt_id: str,
    status: ExecutionStatus,
) -> None:
    execution_request = request(attempt_id)
    replayed, _ = runtime.attempt_ledger.begin(pathway_id, execution_request)
    assert replayed is False
    runtime.attempt_ledger.finish(
        attempt_id,
        ExecutionResult(
            status,
            evidence={"attempt_id": attempt_id},
            readback=ReadbackEvidence(status is ExecutionStatus.SUCCEEDED, {"attempt_id": attempt_id}),
            reason="fixture result",
        ),
    )


def fail_pathway(runtime: ResponsibilityPathwayRuntime, pathway_id: str, attempt_id: str) -> None:
    result = runtime.execute(
        pathway_id,
        request(attempt_id),
        actor="agent",
        executor=FailedExecutor(),
    )
    assert result.status is ExecutionStatus.FAILED
    assert runtime.store.get_state(pathway_id) is PathwayState.REPAIR_REQUIRED


def test_complete_repair_rejects_nonfailed_attempt_without_mutation(tmp_path) -> None:
    pathway_id = "p-repair-success-rejected"
    runtime = runtime_for(tmp_path, pathway_id)
    persist_result(runtime, pathway_id, "attempt-succeeded", ExecutionStatus.SUCCEEDED)
    fail_pathway(runtime, pathway_id, "attempt-active-failure")
    before = deepcopy(runtime.evidence(pathway_id))

    with pytest.raises(ValueError, match="failed prior attempt"):
        RepairCoordinator(runtime).complete_repair(
            pathway_id,
            actor="support",
            prior_attempt_id="attempt-succeeded",
            repair_evidence={"validation": "passed"},
            reason="must not repair a successful attempt",
        )

    assert runtime.store.get_state(pathway_id) is PathwayState.REPAIR_REQUIRED
    assert runtime.evidence(pathway_id) == before
    assert runtime.verify_evidence(pathway_id).valid


def test_resume_must_match_latest_completed_repair_attempt(tmp_path) -> None:
    pathway_id = "p-repair-linkage"
    runtime = runtime_for(tmp_path, pathway_id)
    fail_pathway(runtime, pathway_id, "attempt-failed-a")
    coordinator = RepairCoordinator(runtime)
    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id="attempt-failed-a",
        repair_evidence={"validation": "passed", "repair_ticket": "R-1"},
        reason="attempt a repaired",
    )

    persist_result(runtime, pathway_id, "attempt-failed-b", ExecutionStatus.FAILED)
    before = deepcopy(runtime.evidence(pathway_id))

    with pytest.raises(ValueError, match="latest completed repair"):
        coordinator.resume(
            pathway_id,
            actor="manager",
            prior_attempt_id="attempt-failed-b",
            next_attempt_id="attempt-retry",
            reason="must not substitute an unrelated failed attempt",
        )

    assert runtime.store.get_state(pathway_id) is PathwayState.READY_TO_RESUME
    assert runtime.evidence(pathway_id) == before
    assert runtime.verify_evidence(pathway_id).valid

    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id="attempt-failed-a",
        next_attempt_id="attempt-retry",
        reason="resume the attempt that was actually repaired",
    )
    event = runtime.evidence(pathway_id)[-1]
    assert event["event_type"] == "pathway_resumed"
    assert event["payload"]["prior_attempt_id"] == "attempt-failed-a"
    assert event["payload"]["next_attempt_id"] == "attempt-retry"
    assert runtime.store.get_state(pathway_id) is PathwayState.RUNNING
    assert runtime.verify_evidence(pathway_id).valid
