# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass

import pytest

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.authority import AuthorityError
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


class CrashBeforePathwayCommitRuntime(ResponsibilityPathwayRuntime):
    """Fault-injection runtime that crashes after attempt classification persists."""

    def _finish_reconciliation_pathway(self, pathway_id, request, actor, result, *, replayed):
        del pathway_id, request, actor, result, replayed
        raise RuntimeError("injected_crash_before_pathway_commit")


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


def unresolved_runtime(tmp_path, pathway_id: str = "p-rec", runtime_class=ResponsibilityPathwayRuntime):
    store = SQLiteStore(tmp_path / "pathways.sqlite3")
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    runtime = runtime_class(store=store, attempt_ledger=ledger, rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    request = ExecutionRequest("op-rec", "attempt-rec", "idem-rec", "external_mutation", {"value": 1})
    replayed, _ = ledger.begin(pathway_id, request)
    assert replayed is False
    runtime._start_execution_pathway(pathway_id, request, "agent")
    runtime.mark_write_unknown(pathway_id, actor="agent", reason="dispatch outcome unknown")
    return runtime, request


def recreated_runtime(tmp_path):
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )


def test_verified_applied_closes_pathway_without_redispatch(tmp_path):
    runtime, request = unresolved_runtime(tmp_path)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, {"remote_id": "42"}, "observer confirmed"))

    result = runtime.reconcile("p-rec", request, actor="auditor", strategy=strategy)

    assert result.status is ExecutionStatus.SUCCEEDED
    assert strategy.calls == 1
    assert runtime.store.get_state("p-rec") is PathwayState.COMPLETED
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert runtime.evidence("p-rec")[-1]["event_type"] == "reconciliation_result"
    assert runtime.verify_evidence("p-rec").valid

    replay = runtime.reconcile("p-rec", request, actor="repairer", strategy=strategy)
    assert replay.status is ExecutionStatus.SUCCEEDED
    assert strategy.calls == 1


def test_verified_not_applied_enters_repair(tmp_path):
    runtime, request = unresolved_runtime(tmp_path)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_NOT_APPLIED, {"found": False}))

    result = runtime.reconcile("p-rec", request, actor="repairer", strategy=strategy)

    assert result.status is ExecutionStatus.FAILED
    assert runtime.store.get_state("p-rec") is PathwayState.REPAIR_REQUIRED
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.FAILED.value


def test_unresolved_observation_preserves_unknown_and_can_repeat(tmp_path):
    runtime, request = unresolved_runtime(tmp_path)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.UNRESOLVED, {"timeout": True}))

    first = runtime.reconcile("p-rec", request, actor="auditor", strategy=strategy)
    second = runtime.reconcile("p-rec", request, actor="repairer", strategy=strategy)

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert second.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert strategy.calls == 2
    assert runtime.store.get_state("p-rec") is PathwayState.WRITE_STATUS_UNKNOWN
    assert runtime.attempt_ledger.get(request.attempt_id).result_json is None
    assert [event["event_type"] for event in runtime.evidence("p-rec")].count("reconciliation_unresolved") == 2


def test_unauthorized_reconciliation_reads_no_attempt_and_writes_no_evidence(tmp_path):
    runtime, request = unresolved_runtime(tmp_path)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, {}))
    before = list(runtime.evidence("p-rec"))

    with pytest.raises(AuthorityError):
        runtime.reconcile("p-rec", request, actor="intruder", strategy=strategy)

    assert strategy.calls == 0
    assert runtime.evidence("p-rec") == before
    assert runtime.attempt_ledger.get(request.attempt_id).result_json is None


def test_restart_repairs_pathway_from_persisted_reconciliation_result(tmp_path):
    runtime, request = unresolved_runtime(tmp_path)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, {"remote_id": "42"}))
    result = strategy.reconcile(request, runtime.attempt_ledger.get(request.attempt_id))
    from rpr.executor import ExecutionResult, ReadbackEvidence

    persisted = ExecutionResult(ExecutionStatus.SUCCEEDED, {"reconciliation": dict(result.evidence)}, ReadbackEvidence(True, dict(result.evidence), result.reason), result.reason)
    runtime.attempt_ledger.finish(request.attempt_id, persisted)

    recreated = recreated_runtime(tmp_path)
    never_called = StaticStrategy(ReconciliationResult(ReconciliationStatus.UNRESOLVED, {}))
    replay = recreated.reconcile("p-rec", request, actor="repairer", strategy=never_called)

    assert replay.status is ExecutionStatus.SUCCEEDED
    assert never_called.calls == 0
    assert recreated.store.get_state("p-rec") is PathwayState.COMPLETED
    assert recreated.verify_evidence("p-rec").valid


def test_crash_after_verified_applied_classification_recovers_once_after_restart(tmp_path):
    runtime, request = unresolved_runtime(tmp_path, runtime_class=CrashBeforePathwayCommitRuntime)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, {"remote_id": "42"}, "observer confirmed"))
    events_before = list(runtime.evidence("p-rec"))

    with pytest.raises(RuntimeError, match="injected_crash_before_pathway_commit"):
        runtime.reconcile("p-rec", request, actor="auditor", strategy=strategy)

    assert strategy.calls == 1
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert runtime.store.get_state("p-rec") is PathwayState.WRITE_STATUS_UNKNOWN
    assert runtime.evidence("p-rec") == events_before

    recreated = recreated_runtime(tmp_path)
    never_called = StaticStrategy(ReconciliationResult(ReconciliationStatus.UNRESOLVED, {}))
    replay = recreated.reconcile("p-rec", request, actor="repairer", strategy=never_called)

    assert replay.status is ExecutionStatus.SUCCEEDED
    assert never_called.calls == 0
    assert recreated.store.get_state("p-rec") is PathwayState.COMPLETED
    assert [event["event_type"] for event in recreated.evidence("p-rec")].count("reconciliation_result") == 1
    assert recreated.verify_evidence("p-rec").valid

    event_count = len(recreated.evidence("p-rec"))
    second_replay = recreated.reconcile("p-rec", request, actor="auditor", strategy=never_called)
    assert second_replay.status is ExecutionStatus.SUCCEEDED
    assert never_called.calls == 0
    assert len(recreated.evidence("p-rec")) == event_count


def test_crash_after_verified_not_applied_classification_recovers_to_repair(tmp_path):
    runtime, request = unresolved_runtime(tmp_path, runtime_class=CrashBeforePathwayCommitRuntime)
    strategy = StaticStrategy(ReconciliationResult(ReconciliationStatus.VERIFIED_NOT_APPLIED, {"found": False}, "observer confirmed absent"))

    with pytest.raises(RuntimeError, match="injected_crash_before_pathway_commit"):
        runtime.reconcile("p-rec", request, actor="repairer", strategy=strategy)

    assert strategy.calls == 1
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.FAILED.value
    assert runtime.store.get_state("p-rec") is PathwayState.WRITE_STATUS_UNKNOWN

    recreated = recreated_runtime(tmp_path)
    never_called = StaticStrategy(ReconciliationResult(ReconciliationStatus.UNRESOLVED, {}))
    replay = recreated.reconcile("p-rec", request, actor="auditor", strategy=never_called)

    assert replay.status is ExecutionStatus.FAILED
    assert never_called.calls == 0
    assert recreated.store.get_state("p-rec") is PathwayState.REPAIR_REQUIRED
    assert [event["event_type"] for event in recreated.evidence("p-rec")].count("reconciliation_result") == 1
    assert recreated.verify_evidence("p-rec").valid
