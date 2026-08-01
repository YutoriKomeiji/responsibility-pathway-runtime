# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionStatus
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


@dataclass
class StaticStrategy:
    result: ReconciliationResult
    calls: int = 0

    def reconcile(self, request, attempt):
        del request, attempt
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


def unresolved_runtime(tmp_path, pathway_id: str):
    store = SQLiteStore(tmp_path / f"{pathway_id}-pathways.sqlite3")
    ledger = SQLiteExecutionAttemptLedger(tmp_path / f"{pathway_id}-attempts.sqlite3")
    runtime = ResponsibilityPathwayRuntime(
        store=store,
        attempt_ledger=ledger,
        rpe=AllowAllDevelopmentEvaluator(),
    )
    runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    request = ExecutionRequest("op-rec", "attempt-rec", "idem-rec", "external_mutation", {"value": 1})
    replayed, _ = ledger.begin(pathway_id, request)
    assert replayed is False
    runtime._start_execution_pathway(pathway_id, request, "agent")
    runtime.mark_write_unknown(pathway_id, actor="agent", reason="dispatch outcome unknown")
    return runtime, request


def test_verified_applied_invalid_evidence_stays_unknown(tmp_path):
    runtime, request = unresolved_runtime(tmp_path, "p-rec-invalid-applied")
    strategy = StaticStrategy(
        ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"remote": object()},
            "observer confirmed",
        )
    )

    result = runtime.reconcile(
        "p-rec-invalid-applied",
        request,
        actor="auditor",
        strategy=strategy,
    )

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "reconciliation_result_persistence_rejected:AttemptResultPersistenceError"
    assert strategy.calls == 1
    assert runtime.store.get_state("p-rec-invalid-applied") is PathwayState.WRITE_STATUS_UNKNOWN
    persisted = runtime.attempt_ledger.get(request.attempt_id)
    assert persisted.status == ExecutionStatus.WRITE_STATUS_UNKNOWN.value
    assert persisted.result_json is not None
    assert persisted.result_json["reason"] == result.reason
    assert runtime.evidence("p-rec-invalid-applied")[-1]["event_type"] == "reconciliation_result_persistence_unknown"
    assert runtime.verify_evidence("p-rec-invalid-applied").valid


def test_verified_not_applied_nonfinite_evidence_stays_unknown(tmp_path):
    runtime, request = unresolved_runtime(tmp_path, "p-rec-invalid-absent")
    strategy = StaticStrategy(
        ReconciliationResult(
            ReconciliationStatus.VERIFIED_NOT_APPLIED,
            {"confidence": float("nan")},
            "observer confirmed absent",
        )
    )

    result = runtime.reconcile(
        "p-rec-invalid-absent",
        request,
        actor="repairer",
        strategy=strategy,
    )

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert runtime.store.get_state("p-rec-invalid-absent") is PathwayState.WRITE_STATUS_UNKNOWN
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.WRITE_STATUS_UNKNOWN.value
    assert runtime.verify_evidence("p-rec-invalid-absent").valid


def test_reconciliation_can_reobserve_after_persistence_rejection(tmp_path):
    runtime, request = unresolved_runtime(tmp_path, "p-rec-reobserve")
    invalid = StaticStrategy(
        ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"remote": object()},
        )
    )
    first = runtime.reconcile("p-rec-reobserve", request, actor="auditor", strategy=invalid)
    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN

    valid = StaticStrategy(
        ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"remote_id": "42"},
            "observer confirmed",
        )
    )
    second = runtime.reconcile("p-rec-reobserve", request, actor="repairer", strategy=valid)

    assert invalid.calls == 1
    assert valid.calls == 1
    assert second.status is ExecutionStatus.SUCCEEDED
    assert runtime.store.get_state("p-rec-reobserve") is PathwayState.COMPLETED
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert runtime.verify_evidence("p-rec-reobserve").valid
