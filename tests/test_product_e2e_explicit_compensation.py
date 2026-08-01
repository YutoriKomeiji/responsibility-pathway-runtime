# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
from rpr.compensation import CompensationStatus, NoAutomaticCompensation
from rpr.executor import ExecutionRequest, ExecutionResult, LocalFileExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import PythonRpeEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class CountingExecutor:
    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.calls += 1
        return self.delegate.execute(request)


def definition(pathway_id: str, *, action_name: str = "replace_text_file") -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name=action_name,
        action_class=ActionClass.REVERSIBLE_EXTERNAL,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority="reviewer",
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_execution",
        residual_owner="owner",
    )


def evaluator(reason_code: str) -> PythonRpeEvaluator:
    def evaluate_action(action_request, requirement_packs):
        assert tuple(requirement_packs) == ({"pack_id": "pack-explicit-compensation"},)
        return {
            "decision": "allow",
            "reason_codes": [reason_code],
            "contract_version": "rpe-rpr-v1",
            "pathway_id": action_request["responsibility_pathway"]["pathway_id"],
        }

    return PythonRpeEvaluator(
        evaluate_action,
        ({"pack_id": "pack-explicit-compensation"},),
        expected_contract_version="rpe-rpr-v1",
    )


def test_compensation_requires_separate_authorized_pathway_and_never_runs_automatically(tmp_path) -> None:
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    workspace = tmp_path / "workspace"
    target = workspace / "customer-config.txt"
    workspace.mkdir()
    target.write_text("baseline\n", encoding="utf-8")

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=evaluator("original_action_allowed"),
    )
    original_id = "p-product-e2e-original-action"
    original_registration = runtime.register(
        definition(original_id),
        idempotency_key="register-original-action",
    )
    assert original_registration.state is PathwayState.AWAITING_APPROVAL
    runtime.transition(
        original_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="original mutation approved",
    )

    original_request = ExecutionRequest(
        "operation-original-action",
        "attempt-original-action",
        "idempotency-original-action",
        "replace_text_file",
        {"path": target.name, "content": "changed\n"},
    )
    original_executor = CountingExecutor(LocalFileExecutor(workspace))
    original_result = runtime.execute(
        original_id,
        original_request,
        actor="agent",
        executor=original_executor,
    )

    assert original_result.status.value == "succeeded"
    assert original_result.readback is not None and original_result.readback.verified
    assert original_executor.calls == 1
    assert target.read_text(encoding="utf-8") == "changed\n"
    assert runtime.store.get_state(original_id) is PathwayState.COMPLETED

    plan = NoAutomaticCompensation().propose(
        original_request=original_request,
        original_result=original_result,
    )
    assert plan.status is CompensationStatus.REQUIRES_HUMAN_GATE
    assert plan.request is None
    assert "explicit design and approval" in (plan.reason or "")
    assert target.read_text(encoding="utf-8") == "changed\n"
    assert original_executor.calls == 1
    assert runtime.store.get_state(original_id) is PathwayState.COMPLETED

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=evaluator("compensating_action_allowed"),
    )
    assert restarted.store.get_state(original_id) is PathwayState.COMPLETED
    assert target.read_text(encoding="utf-8") == "changed\n"

    compensation_id = "p-product-e2e-compensating-action"
    compensation_registration = restarted.register(
        definition(compensation_id),
        idempotency_key="register-compensating-action",
    )
    assert compensation_registration.state is PathwayState.AWAITING_APPROVAL
    assert compensation_registration.reason_codes[-1] == "compensating_action_allowed"

    compensation_request = ExecutionRequest(
        "operation-compensating-action",
        "attempt-compensating-action",
        "idempotency-compensating-action",
        "replace_text_file",
        {
            "path": target.name,
            "content": "baseline\n",
            "compensation_for_pathway_id": original_id,
            "compensation_for_operation_id": original_request.operation_id,
            "compensation_for_attempt_id": original_request.attempt_id,
        },
    )
    compensation_executor = CountingExecutor(LocalFileExecutor(workspace))

    with pytest.raises(ValueError, match="approved or running"):
        restarted.execute(
            compensation_id,
            compensation_request,
            actor="agent",
            executor=compensation_executor,
        )
    assert compensation_executor.calls == 0
    assert target.read_text(encoding="utf-8") == "changed\n"
    with pytest.raises(KeyError):
        restarted.attempt_ledger.get(compensation_request.attempt_id)

    with pytest.raises(AuthorityError, match="approval_authority"):
        restarted.transition(
            compensation_id,
            PathwayState.APPROVED,
            actor="agent",
            reason="execution actor cannot approve compensation",
        )

    restarted.transition(
        compensation_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="separate compensating action approved",
    )
    compensation_result = restarted.execute(
        compensation_id,
        compensation_request,
        actor="agent",
        executor=compensation_executor,
    )

    assert compensation_result.status.value == "succeeded"
    assert compensation_result.readback is not None and compensation_result.readback.verified
    assert compensation_executor.calls == 1
    assert target.read_text(encoding="utf-8") == "baseline\n"
    assert restarted.store.get_state(compensation_id) is PathwayState.COMPLETED
    assert restarted.store.get_state(original_id) is PathwayState.COMPLETED

    compensation_events = restarted.evidence(compensation_id)
    result_event = next(event for event in compensation_events if event["event_type"] == "execution_result")
    assert result_event["payload"]["operation_id"] == compensation_request.operation_id
    assert result_event["payload"]["attempt_id"] == compensation_request.attempt_id
    assert result_event["payload"]["idempotency_key"] == compensation_request.idempotency_key
    assert restarted.verify_evidence(original_id).valid
    assert restarted.verify_evidence(compensation_id).valid
