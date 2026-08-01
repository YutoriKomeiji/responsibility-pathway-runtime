# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
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
        human_return_point="before_execution",
        residual_owner="owner",
    )


def test_unavailable_rpe_fails_closed_and_explicit_substitution_uses_new_pathway(tmp_path) -> None:
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    workspace = tmp_path / "workspace"

    blocked_runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
    )
    blocked_id = "p-product-e2e-rpe-unavailable"
    blocked = blocked_runtime.register(
        definition(blocked_id),
        idempotency_key="register-rpe-unavailable",
    )

    assert blocked.decision.value == "human_gate"
    assert blocked.state is PathwayState.HUMAN_GATE
    assert "rpe_unavailable" in blocked.reason_codes

    blocked_request = ExecutionRequest(
        "operation-rpe-unavailable",
        "attempt-rpe-unavailable",
        "idempotency-rpe-unavailable",
        "replace_text_file",
        {"path": "blocked.txt", "content": "must not be written\n"},
    )
    blocked_executor = CountingExecutor(LocalFileExecutor(workspace))
    with pytest.raises(ValueError, match="approved or running"):
        blocked_runtime.execute(
            blocked_id,
            blocked_request,
            actor="agent",
            executor=blocked_executor,
        )

    assert blocked_executor.calls == 0
    assert blocked_runtime.store.get_state(blocked_id) is PathwayState.HUMAN_GATE
    assert not (workspace / "blocked.txt").exists()
    with pytest.raises(KeyError):
        blocked_runtime.attempt_ledger.get(blocked_request.attempt_id)
    assert blocked_runtime.verify_evidence(blocked_id).valid

    captured: list[dict[str, object]] = []

    def authorized_substitute(action_request, requirement_packs):
        captured.append(action_request)
        assert tuple(requirement_packs) == ({"pack_id": "authorized-substitute-pack"},)
        return {
            "decision": "allow",
            "reason_codes": ["authorized_substitute_evaluator"],
            "contract_version": "rpe-rpr-v1",
        }

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            authorized_substitute,
            ({"pack_id": "authorized-substitute-pack"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    substitute_id = "p-product-e2e-rpe-substitute"
    substitute = restarted.register(
        definition(substitute_id),
        idempotency_key="register-rpe-substitute",
    )

    assert substitute.decision.value == "allow"
    assert substitute.state is PathwayState.AWAITING_APPROVAL
    assert substitute.reason_codes[-1] == "authorized_substitute_evaluator"
    assert captured[0]["responsibility_pathway"]["pathway_id"] == substitute_id
    assert restarted.store.get_state(blocked_id) is PathwayState.HUMAN_GATE

    with pytest.raises(AuthorityError, match="approval_authority"):
        restarted.transition(
            substitute_id,
            PathwayState.APPROVED,
            actor="agent",
            reason="execution actor cannot approve substitute pathway",
        )

    restarted.transition(
        substitute_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="approval authority accepts explicit substitute evaluation",
    )
    substitute_request = ExecutionRequest(
        "operation-rpe-substitute",
        "attempt-rpe-substitute",
        "idempotency-rpe-substitute",
        "replace_text_file",
        {
            "path": "accepted.txt",
            "content": "executed after explicit substitution and approval\n",
            "substitution_for": blocked_id,
        },
    )
    substitute_executor = CountingExecutor(LocalFileExecutor(workspace))
    result = restarted.execute(
        substitute_id,
        substitute_request,
        actor="agent",
        executor=substitute_executor,
    )

    assert result.status.value == "succeeded"
    assert result.readback is not None
    assert result.readback.verified
    assert substitute_executor.calls == 1
    assert (workspace / "accepted.txt").read_text(encoding="utf-8") == (
        "executed after explicit substitution and approval\n"
    )
    assert restarted.store.get_state(substitute_id) is PathwayState.COMPLETED
    assert restarted.store.get_state(blocked_id) is PathwayState.HUMAN_GATE
    assert restarted.verify_evidence(substitute_id).valid
    assert restarted.verify_evidence(blocked_id).valid
