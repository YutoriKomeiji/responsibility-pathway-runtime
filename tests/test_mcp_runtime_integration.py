# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionStatus
from rpr.mcp_tool_executor import McpStableToolExecutor, McpToolCallOutcomeUnknownError
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.reconciliation import ReconciliationResult, ReconciliationStatus
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class OutcomeUnknownTransport:
    def __init__(self) -> None:
        self.tool_calls = 0

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        assert method == "tools/call"
        assert params["name"] == "records/update"
        self.tool_calls += 1
        raise McpToolCallOutcomeUnknownError("response lost after dispatch")

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        raise AssertionError(f"unexpected notification: {method} {params}")


class MustNotDispatchTransport:
    def __init__(self) -> None:
        self.tool_calls = 0

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.tool_calls += 1
        raise AssertionError(f"replay redispatched {method} {params}")

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        raise AssertionError(f"unexpected notification: {method} {params}")


@dataclass
class AppliedObserver:
    calls: int = 0

    def reconcile(self, request, attempt):
        assert request.attempt_id == "attempt-mcp-runtime"
        assert attempt.result_json is not None
        assert attempt.result_json["status"] == ExecutionStatus.WRITE_STATUS_UNKNOWN.value
        self.calls += 1
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_APPLIED,
            {"remote_record_id": "record-42", "version": 2},
            "independent observer confirmed the mutation",
        )


def definition() -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id="p-mcp-runtime",
        action_name="mcp_records_update",
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


def admitted_request() -> ExecutionRequest:
    return ExecutionRequest(
        operation_id="op-mcp-runtime",
        attempt_id="attempt-mcp-runtime",
        idempotency_key="idem-mcp-runtime",
        action="mcp_tool_call",
        parameters={
            "mcp": {
                "protocol_version": "2025-11-25",
                "server_identity": "records-server@1.0.0",
                "server_capabilities_hash": "a" * 64,
                "tool_name": "records/update",
                "tool_schema_hash": "b" * 64,
            },
            "arguments": {"record_id": "record-42", "value": "updated"},
        },
    )


def runtime_for(tmp_path) -> ResponsibilityPathwayRuntime:
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )


def test_mcp_unknown_result_replay_never_redispatches_and_reconciles_after_restart(tmp_path):
    runtime = runtime_for(tmp_path)
    runtime.register(definition(), idempotency_key="register-mcp-runtime")
    request = admitted_request()
    first_transport = OutcomeUnknownTransport()

    first = runtime.execute(
        "p-mcp-runtime",
        request,
        actor="agent",
        executor=McpStableToolExecutor(first_transport),
    )

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert first.evidence["dispatch_state"] == "possibly_sent"
    assert first_transport.tool_calls == 1
    assert runtime.store.get_state("p-mcp-runtime") is PathwayState.WRITE_STATUS_UNKNOWN
    persisted = runtime.attempt_ledger.get(request.attempt_id)
    assert persisted is not None
    assert persisted.status == ExecutionStatus.WRITE_STATUS_UNKNOWN.value

    recreated = runtime_for(tmp_path)
    replay_transport = MustNotDispatchTransport()
    replay = recreated.execute(
        "p-mcp-runtime",
        request,
        actor="agent",
        executor=McpStableToolExecutor(replay_transport),
    )

    assert replay.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert replay_transport.tool_calls == 0
    assert recreated.store.get_state("p-mcp-runtime") is PathwayState.WRITE_STATUS_UNKNOWN

    observer = AppliedObserver()
    reconciled = recreated.reconcile(
        "p-mcp-runtime",
        request,
        actor="auditor",
        strategy=observer,
    )

    assert reconciled.status is ExecutionStatus.SUCCEEDED
    assert observer.calls == 1
    assert recreated.store.get_state("p-mcp-runtime") is PathwayState.COMPLETED
    assert recreated.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert recreated.verify_evidence("p-mcp-runtime").valid

    event_count = len(recreated.evidence("p-mcp-runtime"))
    terminal_replay = recreated.reconcile(
        "p-mcp-runtime",
        request,
        actor="repairer",
        strategy=observer,
    )
    assert terminal_replay.status is ExecutionStatus.SUCCEEDED
    assert observer.calls == 1
    assert len(recreated.evidence("p-mcp-runtime")) == event_count
