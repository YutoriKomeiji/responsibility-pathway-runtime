# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Mapping

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionStatus, ReadbackEvidence
from rpr.mcp_admission import McpStableAdmissionAdapter
from rpr.mcp_jsonrpc_session import McpJsonRpcSession
from rpr.mcp_stable_transport import McpStableOrchestrator
from rpr.mcp_stdio_channel import McpStdioChannel, McpStdioEvent
from rpr.mcp_tool_executor import McpStableToolExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


CONTRACT = Path(__file__).parents[1] / "specs" / "mcp-compatibility.json"


def _line(request_id: int, result: Mapping[str, Any]) -> bytes:
    import json

    return (
        json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "result": dict(result)},
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": "2025-11-25",
        "serverInfo": {"name": "bounded-tools", "version": "1.2.3"},
        "capabilities": {"tools": {"listChanged": False}},
    }


def _tools_result() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "replace_record",
                "description": "replace one bounded record",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["record_id", "value"],
                },
            }
        ]
    }


class ScriptedDuplex:
    """Deterministic byte/event double for the complete bounded stdio stack."""

    def __init__(self, events: list[McpStdioEvent], *, max_write: int = 7) -> None:
        self.events = deque(events)
        self.max_write = max_write
        self.writes: list[bytes] = []

    def write_stdin(self, data: bytes) -> int:
        value = bytes(data)
        self.writes.append(value)
        return min(len(value), self.max_write)

    def read_event(self) -> McpStdioEvent:
        if not self.events:
            raise TimeoutError("script exhausted")
        return self.events.popleft()


class VerifiedObserver:
    def __init__(self) -> None:
        self.calls = 0

    def observe(
        self,
        request: ExecutionRequest,
        tool_result: Mapping[str, Any],
    ) -> ReadbackEvidence:
        self.calls += 1
        assert request.parameters["mcp"]["server_identity"] == "bounded-tools@1.2.3"
        assert request.parameters["mcp"]["tool_name"] == "replace_record"
        assert tool_result["content"][0]["text"] == "updated"
        return ReadbackEvidence(
            True,
            {"record_id": "r-42", "value": "updated", "version": 2},
        )


def _definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="mcp_replace_record",
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


def _runtime(tmp_path) -> ResponsibilityPathwayRuntime:
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )


def _prepare(session: McpJsonRpcSession, *, suffix: str) -> ExecutionRequest:
    orchestrator = McpStableOrchestrator(
        session,
        McpStableAdmissionAdapter(CONTRACT),
    )
    prepared = orchestrator.prepare(
        tool_name="replace_record",
        arguments={"record_id": "r-42", "value": "updated"},
        operation_id=f"op-{suffix}",
        attempt_id=f"attempt-{suffix}",
        idempotency_key=f"idem-{suffix}",
    )
    return prepared.request


def _events() -> list[McpStdioEvent]:
    initialize = _line(1, _initialize_result())
    tools = _line(2, _tools_result())
    call = _line(
        3,
        {"content": [{"type": "text", "text": "updated"}]},
    )
    return [
        McpStdioEvent("stderr", b"server starting\n"),
        McpStdioEvent("stdout", initialize[:13]),
        McpStdioEvent("stdout", initialize[13:]),
        McpStdioEvent("stdout", tools),
        McpStdioEvent("stderr", b"tool dispatch\n"),
        McpStdioEvent("stdout", call[:9]),
        McpStdioEvent("stdout", call[9:]),
    ]


def test_stable_stdio_stack_reaches_runtime_completion_only_after_verified_readback(tmp_path):
    duplex = ScriptedDuplex(_events())
    channel = McpStdioChannel(duplex)
    session = McpJsonRpcSession(channel)
    request = _prepare(session, suffix="stdio-success")
    runtime = _runtime(tmp_path)
    runtime.register(_definition("p-stdio-success"), idempotency_key="register-stdio-success")
    observer = VerifiedObserver()

    result = runtime.execute(
        "p-stdio-success",
        request,
        actor="agent",
        executor=McpStableToolExecutor(session, readback_observer=observer),
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert observer.calls == 1
    assert runtime.store.get_state("p-stdio-success") is PathwayState.COMPLETED
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    assert runtime.verify_evidence("p-stdio-success").valid
    assert channel.diagnostics.text() == "server starting\ntool dispatch\n"
    written = b"".join(duplex.writes)
    assert b'"method":"initialize"' in written
    assert b'"method":"notifications/initialized"' in written
    assert b'"method":"tools/list"' in written
    assert b'"method":"tools/call"' in written


def test_stable_stdio_stack_keeps_success_response_unknown_without_readback(tmp_path):
    duplex = ScriptedDuplex(_events())
    session = McpJsonRpcSession(McpStdioChannel(duplex))
    request = _prepare(session, suffix="stdio-unknown")
    runtime = _runtime(tmp_path)
    runtime.register(_definition("p-stdio-unknown"), idempotency_key="register-stdio-unknown")

    result = runtime.execute(
        "p-stdio-unknown",
        request,
        actor="agent",
        executor=McpStableToolExecutor(session),
    )

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "independent_readback_required"
    assert runtime.store.get_state("p-stdio-unknown") is PathwayState.WRITE_STATUS_UNKNOWN
    assert runtime.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.WRITE_STATUS_UNKNOWN.value
    assert runtime.verify_evidence("p-stdio-unknown").valid
