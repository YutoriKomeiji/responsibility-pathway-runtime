# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
from rpr.executor import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    LocalFileExecutor,
)
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.repair import RepairCoordinator
from rpr.rpe import PythonRpeEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class FailedExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.FAILED,
            {"validation": "precondition_failed"},
            reason="precondition_failed",
        )


class CountingExecutor:
    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        return self.delegate.execute(request)


def test_rpe_failure_repair_resume_retry_product_e2e_survives_restart(tmp_path) -> None:
    pathway_id = "p-product-e2e-repair-resume"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    workspace = tmp_path / "workspace"
    captured: list[dict[str, object]] = []

    def evaluate_action(action_request, requirement_packs):
        captured.append(action_request)
        assert tuple(requirement_packs) == ({"pack_id": "pack-repair-e2e"},)
        return {
            "decision": "allow",
            "reason_codes": ["requirements_satisfied"],
            "contract_version": "rpe-rpr-v1",
        }

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-repair-e2e"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    definition = PathwayDefinition(
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
    registration = runtime.register(definition, idempotency_key="register-repair-e2e")
    assert registration.decision.value == "allow"
    assert registration.state is PathwayState.AWAITING_APPROVAL
    assert registration.reason_codes[-1] == "requirements_satisfied"
    assert captured[0]["action"] == "replace_text_file"

    runtime.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="approved for initial execution",
    )
    first_request = ExecutionRequest(
        "operation-repair-e2e",
        "attempt-repair-e2e-1",
        "idempotency-repair-e2e-1",
        "replace_text_file",
        {"path": "result.txt", "content": "accepted after repair\n"},
    )
    failed_executor = FailedExecutor()
    first_result = runtime.execute(
        pathway_id,
        first_request,
        actor="agent",
        executor=failed_executor,
    )

    assert first_result.status is ExecutionStatus.FAILED
    assert failed_executor.calls == 1
    assert runtime.store.get_state(pathway_id) is PathwayState.REPAIR_REQUIRED
    assert runtime.attempt_ledger.get(first_request.attempt_id).result_json is not None

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-repair-e2e"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    coordinator = RepairCoordinator(restarted)

    with pytest.raises(AuthorityError, match="repair_owner"):
        coordinator.complete_repair(
            pathway_id,
            actor="agent",
            prior_attempt_id=first_request.attempt_id,
            repair_evidence={"validation": "passed"},
            reason="unauthorized repair closure",
        )

    coordinator.complete_repair(
        pathway_id,
        actor="support",
        prior_attempt_id=first_request.attempt_id,
        repair_evidence={
            "validation": "passed",
            "cause": "stale precondition",
            "corrective_action": "refreshed expected state",
        },
        reason="repair evidence accepted",
    )
    assert restarted.store.get_state(pathway_id) is PathwayState.READY_TO_RESUME

    second_request = ExecutionRequest(
        first_request.operation_id,
        "attempt-repair-e2e-2",
        "idempotency-repair-e2e-2",
        first_request.action,
        first_request.parameters,
    )
    with pytest.raises(AuthorityError, match="execution or resume authority"):
        coordinator.resume(
            pathway_id,
            actor="reviewer",
            prior_attempt_id=first_request.attempt_id,
            next_attempt_id=second_request.attempt_id,
            reason="unauthorized resume",
        )

    coordinator.resume(
        pathway_id,
        actor="manager",
        prior_attempt_id=first_request.attempt_id,
        next_attempt_id=second_request.attempt_id,
        reason="authorized retry after repair",
    )
    assert restarted.store.get_state(pathway_id) is PathwayState.RUNNING

    stale_executor = CountingExecutor(LocalFileExecutor(workspace))
    with pytest.raises(ValueError, match="bound to attempt"):
        restarted.execute(
            pathway_id,
            first_request,
            actor="agent",
            executor=stale_executor,
        )
    assert stale_executor.calls == 0

    retry_executor = CountingExecutor(LocalFileExecutor(workspace))
    retry_result = restarted.execute(
        pathway_id,
        second_request,
        actor="agent",
        executor=retry_executor,
    )

    assert retry_result.status is ExecutionStatus.SUCCEEDED
    assert retry_result.readback is not None
    assert retry_result.readback.verified
    assert retry_executor.calls == 1
    assert (workspace / "result.txt").read_text(encoding="utf-8") == "accepted after repair\n"
    assert restarted.store.get_state(pathway_id) is PathwayState.COMPLETED
    assert restarted.attempt_ledger.get(second_request.attempt_id).result_json is not None
    assert restarted.verify_evidence(pathway_id).valid
