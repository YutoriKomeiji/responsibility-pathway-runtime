# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from copy import deepcopy

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
from rpr.executor import ExecutionRequest, ExecutionStatus, LocalFileExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import PythonRpeEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


def test_rpe_hold_to_human_gate_requires_authorized_return_before_dispatch(tmp_path) -> None:
    pathway_id = "p-product-e2e-human-gate"
    store_path = tmp_path / "pathways.sqlite3"
    attempt_path = tmp_path / "attempts.sqlite3"
    workspace = tmp_path / "workspace"
    captured: list[dict[str, object]] = []

    def evaluate_action(action_request, requirement_packs):
        captured.append(action_request)
        assert tuple(requirement_packs) == ({"pack_id": "pack-human-gate-1"},)
        return {
            "decision": "hold",
            "reason_codes": ["human_review_required"],
            "contract_version": "rpe-rpr-v1",
        }

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-human-gate-1"},),
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
        human_return_point="approval_review",
        residual_owner="owner",
    )
    registration = runtime.register(definition, idempotency_key="register-human-gate-e2e")

    assert registration.decision.value == "hold"
    assert registration.state is PathwayState.HELD
    assert registration.reason_codes[-1] == "human_review_required"
    assert captured[0]["action"] == "replace_text_file"
    registration_evidence = deepcopy(runtime.evidence(pathway_id))

    request = ExecutionRequest(
        "operation-human-gate-e2e",
        "attempt-human-gate-e2e",
        "idempotency-human-gate-e2e",
        "replace_text_file",
        {"path": "result.txt", "content": "approved delivery"},
    )
    executor = LocalFileExecutor(workspace)

    with pytest.raises(ValueError, match="pathway must be approved or running"):
        runtime.execute(pathway_id, request, actor="agent", executor=executor)
    with pytest.raises(KeyError):
        runtime.attempt_ledger.get(request.attempt_id)
    assert not (workspace / "result.txt").exists()
    assert runtime.store.get_state(pathway_id) is PathwayState.HELD
    assert runtime.evidence(pathway_id) == registration_evidence

    runtime.transition(
        pathway_id,
        PathwayState.HUMAN_GATE,
        actor="operator",
        reason="explicit human decision required",
    )
    gate_evidence = deepcopy(runtime.evidence(pathway_id))
    assert gate_evidence[:-1] == registration_evidence
    assert gate_evidence[-1]["event_type"] == "state_transition"
    assert gate_evidence[-1]["actor"] == "operator"
    assert gate_evidence[-1]["payload"]["from"] == PathwayState.HELD.value
    assert gate_evidence[-1]["payload"]["to"] == PathwayState.HUMAN_GATE.value
    assert runtime.verify_evidence(pathway_id).valid

    restarted = ResponsibilityPathwayRuntime(
        store=SQLiteStore(store_path),
        attempt_ledger=SQLiteExecutionAttemptLedger(attempt_path),
        rpe=PythonRpeEvaluator(
            evaluate_action,
            ({"pack_id": "pack-human-gate-1"},),
            expected_contract_version="rpe-rpr-v1",
        ),
    )
    assert restarted.store.get_state(pathway_id) is PathwayState.HUMAN_GATE
    assert restarted.evidence(pathway_id) == gate_evidence

    with pytest.raises(AuthorityError, match="approval_authority"):
        restarted.transition(
            pathway_id,
            PathwayState.APPROVED,
            actor="agent",
            reason="unauthorized return attempt",
        )
    assert restarted.store.get_state(pathway_id) is PathwayState.HUMAN_GATE
    assert restarted.evidence(pathway_id) == gate_evidence
    assert restarted.verify_evidence(pathway_id).valid

    restarted.transition(
        pathway_id,
        PathwayState.APPROVED,
        actor="reviewer",
        reason="human review approved bounded execution",
    )
    approved_evidence = deepcopy(restarted.evidence(pathway_id))
    assert approved_evidence[:-1] == gate_evidence
    assert approved_evidence[-1]["actor"] == "reviewer"
    assert approved_evidence[-1]["payload"]["from"] == PathwayState.HUMAN_GATE.value
    assert approved_evidence[-1]["payload"]["to"] == PathwayState.APPROVED.value

    result = restarted.execute(pathway_id, request, actor="agent", executor=executor)

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert (workspace / "result.txt").read_text(encoding="utf-8") == "approved delivery"
    assert restarted.store.get_state(pathway_id) is PathwayState.COMPLETED
    persisted = restarted.attempt_ledger.get(request.attempt_id)
    assert persisted.result_json is not None
    assert persisted.result_json["status"] == ExecutionStatus.SUCCEEDED.value
    final_evidence = restarted.evidence(pathway_id)
    assert final_evidence[: len(approved_evidence)] == approved_evidence
    assert restarted.verify_evidence(pathway_id).valid
