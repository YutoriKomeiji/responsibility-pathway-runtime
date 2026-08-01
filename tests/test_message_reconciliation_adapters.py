# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json

from rpr import (
    ActionClass,
    AgentToolCall,
    EnvironmentTrust,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    OutboundMessageExecutor,
    PathwayDefinition,
    PathwayState,
    ReadbackEvidence,
    ReconciliationResult,
    ReconciliationStatus,
    ResponsibilityPathwayRuntime,
    RprToolBoundary,
    SQLiteExecutionAttemptLedger,
    SQLiteOutbox,
    langgraph_tool_node,
    openai_function_tool_handler,
    reconcile_started_attempt,
)
from rpr.rpe import AllowAllDevelopmentEvaluator


class Transport:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, **kwargs):
        self.calls += 1
        return {"message_id": "m-1", "accepted": True, "durable": True}


class EchoExecutor:
    def execute(self, request):
        return ExecutionResult(ExecutionStatus.SUCCEEDED, {"action": request.action}, ReadbackEvidence(True, {"ok": True}))


class AppliedStrategy:
    def reconcile(self, request, attempt):
        return ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, {"remote_id": "r-1"})


def definition(pathway_id: str = "p-adapter"):
    return PathwayDefinition(pathway_id=pathway_id, action_name="send_message", action_class=ActionClass.SUGGEST_ONLY, environment_trust=EnvironmentTrust.TRUSTED_INTERNAL, decision_owner="owner", approval_authority=None, execution_actor="agent", stop_authority="operator", evidence_owner="audit", repair_owner="repair", resume_authority="manager", human_return_point="before_send", residual_owner="owner")


def test_message_executor_persists_receipt_and_replays_without_resend(tmp_path):
    transport = Transport()
    outbox_path = tmp_path / "outbox.sqlite3"
    request = ExecutionRequest("op-1", "attempt-1", "idem-1", "send_message", {"recipient": "a@example.com", "body": "hello"})
    first = OutboundMessageExecutor(transport, SQLiteOutbox(outbox_path)).execute(request)
    second = OutboundMessageExecutor(transport, SQLiteOutbox(outbox_path)).execute(request)
    assert first.status is ExecutionStatus.SUCCEEDED
    assert second.status is ExecutionStatus.SUCCEEDED
    assert transport.calls == 1


def test_reconcile_unresolved_attempt_without_redispatch(tmp_path):
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    request = ExecutionRequest("op-2", "attempt-2", "idem-2", "http_json_mutation", {"id": "x"})
    replayed, _ = ledger.begin("p-2", request)
    assert not replayed
    result = reconcile_started_attempt(pathway_id="p-2", request=request, ledger=ledger, strategy=AppliedStrategy())
    assert result.status is ExecutionStatus.SUCCEEDED
    replayed, record = ledger.begin("p-2", request)
    assert replayed and record.result_json is not None


def test_framework_neutral_and_wrapper_adapters():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(), idempotency_key="register-1")
    boundary = RprToolBoundary(runtime, lambda _: EchoExecutor())
    outcome = boundary.invoke(pathway_id="p-adapter", actor="agent", call=AgentToolCall("send_message", {"body": "hello"}, "call-1"))
    assert outcome.allowed
    assert outcome.state == PathwayState.COMPLETED.value

    runtime2 = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime2.register(definition("p-openai"), idempotency_key="register-2")
    handler = openai_function_tool_handler(RprToolBoundary(runtime2, lambda _: EchoExecutor()), pathway_id="p-openai", actor="agent", tool_name="send_message")
    value = json.loads(handler(json.dumps({"_rpr_call_id": "call-2", "body": "hello"})))
    assert value["state"] == PathwayState.COMPLETED.value

    runtime3 = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime3.register(definition("p-langgraph"), idempotency_key="register-3")
    node = langgraph_tool_node(RprToolBoundary(runtime3, lambda _: EchoExecutor()), pathway_id="p-langgraph", actor="agent", tool_name="send_message")
    state = node({"call_id": "call-3", "arguments": {"body": "hello"}})
    assert state["rpr"]["allowed"] is True
