# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any, Mapping

from rpr.executor import ExecutionRequest, ExecutionStatus
from rpr.mcp_tool_executor import McpStableToolExecutor
from rpr.mcp_stable_snapshot import STABLE_PROTOCOL_VERSION


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append((method, params))
        return {"content": []}

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        raise AssertionError("executor must not send notifications")


def request_for(protocol_version: str) -> ExecutionRequest:
    return ExecutionRequest(
        operation_id="op-protocol",
        attempt_id="attempt-protocol",
        idempotency_key="idem-protocol",
        action="mcp_tool_call",
        parameters={
            "mcp": {
                "protocol_version": protocol_version,
                "server_identity": "example@1.0",
                "server_capabilities_hash": "a" * 64,
                "tool_name": "records/update",
                "tool_schema_hash": "b" * 64,
            },
            "arguments": {"record_id": "42"},
        },
    )


def test_stable_protocol_is_dispatched() -> None:
    transport = RecordingTransport()

    result = McpStableToolExecutor(transport, require_readback=False).execute(
        request_for(STABLE_PROTOCOL_VERSION)
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert transport.calls == [
        ("tools/call", {"name": "records/update", "arguments": {"record_id": "42"}})
    ]


def test_release_candidate_protocol_is_rejected_without_dispatch() -> None:
    transport = RecordingTransport()

    result = McpStableToolExecutor(transport).execute(request_for("2026-07-28"))

    assert result.status is ExecutionStatus.FAILED
    assert result.evidence["dispatch_state"] == "not_sent"
    assert result.reason == (
        "invalid_mcp_admission_envelope: "
        f"stable MCP executor requires protocol {STABLE_PROTOCOL_VERSION}"
    )
    assert transport.calls == []


def test_unknown_protocol_is_rejected_without_dispatch() -> None:
    transport = RecordingTransport()

    result = McpStableToolExecutor(transport).execute(request_for("2099-01-01"))

    assert result.status is ExecutionStatus.FAILED
    assert result.evidence["dispatch_state"] == "not_sent"
    assert transport.calls == []
