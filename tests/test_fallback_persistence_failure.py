# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


class FailingFallbackLedger(SQLiteExecutionAttemptLedger):
    def mark_result_persistence_unknown(self, attempt_id: str, *, reason: str):
        del attempt_id, reason
        raise sqlite3.OperationalError("injected fallback persistence failure")


class InvalidEvidenceExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"invalid": object()},
            ReadbackEvidence(True, {"applied": True}),
        )


@dataclass
class InvalidReconciliationStrategy:
    calls: int = 0

    def reconcile(self, request, attempt) -> ReconciliationResult:
        del request, attempt
        self.calls += 1
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"invalid": object()},
            "observer returned non-json evidence",
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


def request(prefix: str) -> ExecutionRequest:
    return ExecutionRequest(
        f"op-{prefix}",
        f"attempt-{prefix}",
        f"idem-{prefix}",
        "external_mutation",
        {"value": 1},
    )


def test_execution_fallback_db_failure_preserves_unknown_and_never_redispatches(tmp_path) -> None:
    ledger = FailingFallbackLedger(tmp_path / "attempts.sqlite3")
    runtime = ResponsibilityPathwayRuntime(
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=ledger,
    )
    runtime.register(definition("p-exec-fallback"), idempotency_key="register-exec")
    executor = InvalidEvidenceExecutor()
    execution_request = request("exec")

    first = runtime.execute(
        "p-exec-fallback",
        execution_request,
        actor="agent",
        executor=executor,
    )

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert first.reason == (
        "result_persistence_rejected:AttemptResultPersistenceError:"
        "fallback_persistence_failed:OperationalError"
    )
    assert runtime.store.get_state("p-exec-fallback") is PathwayState.WRITE_STATUS_UNKNOWN
    attempt = ledger.get(execution_request.attempt_id)
    assert attempt.status == "started"
    assert attempt.result_json is None
    event = next(
        item
        for item in runtime.evidence("p-exec-fallback")
        if item["event_type"] == "execution_result_persistence_unknown"
    )
    assert event["payload"]["fallback_persisted"] is False
    assert event["payload"]["fallback_failure"] == "OperationalError"
    assert runtime.verify_evidence("p-exec-fallback").valid
    assert executor.calls == 1

    replay = runtime.execute(
        "p-exec-fallback",
        execution_request,
        actor="agent",
        executor=executor,
    )

    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert replay.reason == "prior_attempt_started_without_persisted_result"
    assert executor.calls == 1


def test_reconciliation_fallback_db_failure_keeps_pathway_unknown(tmp_path) -> None:
    ledger = FailingFallbackLedger(tmp_path / "attempts.sqlite3")
    runtime = ResponsibilityPathwayRuntime(
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=ledger,
    )
    pathway_id = "p-rec-fallback"
    reconciliation_request = request("rec")
    runtime.register(definition(pathway_id), idempotency_key="register-rec")
    replayed, _ = ledger.begin(pathway_id, reconciliation_request)
    assert replayed is False
    runtime._start_execution_pathway(pathway_id, reconciliation_request, "agent")
    runtime.mark_write_unknown(pathway_id, actor="agent", reason="dispatch outcome unknown")
    strategy = InvalidReconciliationStrategy()

    result = runtime.reconcile(
        pathway_id,
        reconciliation_request,
        actor="auditor",
        strategy=strategy,
    )

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert runtime.store.get_state(pathway_id) is PathwayState.WRITE_STATUS_UNKNOWN
    attempt = ledger.get(reconciliation_request.attempt_id)
    assert attempt.status == "started"
    assert attempt.result_json is None
    event = next(
        item
        for item in runtime.evidence(pathway_id)
        if item["event_type"] == "reconciliation_result_persistence_unknown"
    )
    assert event["payload"]["fallback_persisted"] is False
    assert event["payload"]["fallback_failure"] == "OperationalError"
    assert runtime.verify_evidence(pathway_id).valid
    assert strategy.calls == 1
