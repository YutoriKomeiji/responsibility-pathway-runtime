# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import pytest

from rpr.mcp_admission import McpStableAdmissionAdapter
from rpr.mcp_stable_transport import (
    McpPreDispatchError,
    McpStableOrchestrator,
    McpTransportError,
)


CONTRACT = Path(__file__).parents[1] / "specs" / "mcp-compatibility.json"


def initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": "2025-11-25",
        "serverInfo": {"name": "bounded-tools", "version": "1.2.3"},
        "capabilities": {"tools": {"listChanged": False}},
    }


def tools_result() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "replace_record",
                "description": "replace one bounded record",
                "inputSchema": {
                    "type": "object",
                    "properties": {"record_id": {"type": "string"}},
                    "required": ["record_id"],
                },
            }
        ]
    }


@dataclass
class FakeTransport:
    initialize: Mapping[str, Any] = field(default_factory=initialize_result)
    tools: Mapping[str, Any] = field(default_factory=tools_result)
    fail_phase: str | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("request", method))
        if self.fail_phase == method:
            raise McpTransportError(f"forced {method} failure")
        if method == "initialize":
            assert params["protocolVersion"] == "2025-11-25"
            return self.initialize
        if method == "tools/list":
            return self.tools
        raise AssertionError(f"unexpected request method: {method}")

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        self.calls.append(("notify", method))
        if self.fail_phase == method:
            raise ConnectionError(f"forced {method} failure")
        assert method == "notifications/initialized"
        assert params == {}


def orchestrator(transport: FakeTransport) -> McpStableOrchestrator:
    return McpStableOrchestrator(
        transport,
        McpStableAdmissionAdapter(CONTRACT),
    )


def test_stable_orchestration_prepares_admitted_request_without_tool_dispatch():
    transport = FakeTransport()

    prepared = orchestrator(transport).prepare(
        tool_name="replace_record",
        arguments={"record_id": "r-42"},
        operation_id="op-mcp-1",
        attempt_id="attempt-mcp-1",
        idempotency_key="mcp-1",
    )

    assert transport.calls == [
        ("request", "initialize"),
        ("notify", "notifications/initialized"),
        ("request", "tools/list"),
    ]
    assert prepared.server_identity == "bounded-tools@1.2.3"
    assert prepared.protocol_version == "2025-11-25"
    assert prepared.request.action == "mcp_tool_call"
    assert prepared.request.parameters["arguments"] == {"record_id": "r-42"}
    assert prepared.request.parameters["mcp"]["tool_name"] == "replace_record"


@pytest.mark.parametrize(
    ("phase", "expected_phase"),
    [
        ("initialize", "initialize"),
        ("notifications/initialized", "initialized_notification"),
        ("tools/list", "tools_list"),
    ],
)
def test_transport_failures_remain_pre_dispatch(phase: str, expected_phase: str):
    transport = FakeTransport(fail_phase=phase)

    with pytest.raises(McpPreDispatchError) as error:
        orchestrator(transport).prepare(
            tool_name="replace_record",
            arguments={"record_id": "r-42"},
            operation_id="op-mcp-fail",
            attempt_id="attempt-mcp-fail",
            idempotency_key="mcp-fail",
        )

    assert error.value.phase == expected_phase
    assert "write_status_unknown" not in str(error.value)


def test_invalid_initialize_result_stops_before_initialized_notification():
    transport = FakeTransport(
        initialize={
            **initialize_result(),
            "protocolVersion": "2026-07-28",
        }
    )

    with pytest.raises(McpPreDispatchError) as error:
        orchestrator(transport).prepare(
            tool_name="replace_record",
            arguments={"record_id": "r-42"},
            operation_id="op-version",
            attempt_id="attempt-version",
            idempotency_key="mcp-version",
        )

    assert error.value.phase == "initialize_validation"
    assert transport.calls == [("request", "initialize")]


def test_missing_tool_stops_before_admission_request_is_created():
    transport = FakeTransport(tools={"tools": []})

    with pytest.raises(McpPreDispatchError) as error:
        orchestrator(transport).prepare(
            tool_name="replace_record",
            arguments={"record_id": "r-42"},
            operation_id="op-tool",
            attempt_id="attempt-tool",
            idempotency_key="mcp-tool",
        )

    assert error.value.phase == "admission"
    assert "requested MCP tool not found" in error.value.reason


def test_non_object_transport_result_fails_closed():
    class InvalidTransport(FakeTransport):
        def request(self, method: str, params: Mapping[str, Any]):
            if method == "initialize":
                return []
            return super().request(method, params)

    with pytest.raises(McpPreDispatchError) as error:
        orchestrator(InvalidTransport()).prepare(
            tool_name="replace_record",
            arguments={"record_id": "r-42"},
            operation_id="op-shape",
            attempt_id="attempt-shape",
            idempotency_key="mcp-shape",
        )

    assert error.value.phase == "initialize"
    assert "non-object" in error.value.reason
