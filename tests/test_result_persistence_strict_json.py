# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import math

import pytest

from rpr.attempts import AttemptResultPersistenceError, SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


def request() -> ExecutionRequest:
    return ExecutionRequest("op-result", "attempt-result", "idem-result", "test_action", {})


def definition() -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id="p-result",
        action_name="test_action",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_dispatch",
        residual_owner="owner",
    )


class InvalidEvidenceExecutor:
    def __init__(self, evidence: object) -> None:
        self.evidence = evidence
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"value": self.evidence},
            ReadbackEvidence(True, {"applied": True}),
        )


def started_ledger(tmp_path) -> SQLiteExecutionAttemptLedger:
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    ledger.begin("p-result", request())
    return ledger


def test_valid_result_round_trips_as_strict_json(tmp_path) -> None:
    ledger = started_ledger(tmp_path)
    result = ExecutionResult(
        ExecutionStatus.SUCCEEDED,
        {"nested": {"items": [1, "二", True]}},
        ReadbackEvidence(True, {"sha256": "a" * 64}),
    )

    record = ledger.finish(request().attempt_id, result)

    assert record.status == ExecutionStatus.SUCCEEDED.value
    assert record.result_json is not None
    assert record.result_json["evidence"] == {"nested": {"items": [1, "二", True]}}


@pytest.mark.parametrize(
    "evidence",
    [
        object(),
        math.nan,
        math.inf,
        {1: "non-string-key"},
    ],
)
def test_invalid_result_evidence_is_rejected_without_overwriting_started_attempt(
    tmp_path, evidence: object
) -> None:
    ledger = started_ledger(tmp_path)

    with pytest.raises(AttemptResultPersistenceError):
        ledger.finish(
            request().attempt_id,
            ExecutionResult(ExecutionStatus.SUCCEEDED, {"value": evidence}),
        )

    record = ledger.get(request().attempt_id)
    assert record.status == "started"
    assert record.result_json is None


def test_cyclic_result_evidence_is_rejected(tmp_path) -> None:
    ledger = started_ledger(tmp_path)
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    with pytest.raises(AttemptResultPersistenceError, match="cyclic"):
        ledger.finish(
            request().attempt_id,
            ExecutionResult(ExecutionStatus.SUCCEEDED, cyclic),
        )


def test_runtime_marks_result_persistence_unknown_and_never_redispatches() -> None:
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(), idempotency_key="pathway-result")
    executor = InvalidEvidenceExecutor(object())

    first = runtime.execute("p-result", request(), actor="agent", executor=executor)

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert first.reason == "result_persistence_rejected:AttemptResultPersistenceError"
    assert runtime.store.get_state("p-result") is PathwayState.WRITE_STATUS_UNKNOWN
    attempt = runtime.attempt_ledger.get(request().attempt_id)
    assert attempt.status == ExecutionStatus.WRITE_STATUS_UNKNOWN.value
    assert attempt.result_json == {
        "status": ExecutionStatus.WRITE_STATUS_UNKNOWN.value,
        "evidence": {},
        "readback": None,
        "reason": "result_persistence_rejected:AttemptResultPersistenceError",
    }
    assert executor.calls == 1

    replay = runtime.execute("p-result", request(), actor="agent", executor=executor)

    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1
    assert runtime.verify_evidence("p-result").valid
