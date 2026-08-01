# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any, Mapping

from rpr.executor import ExecutionRequest, ExecutionStatus, ReadbackEvidence
from rpr.mcp_tool_executor import (
    McpStableToolExecutor,
    McpToolCallNotSentError,
    McpToolCallOutcomeUnknownError,
)
from rpr.mcp_stable_transport import McpTransportError


CAPABILITIES_HASH = "a" * 64
SCHEMA_HASH = "b" * 64


class ScriptedTransport:
    def __init__(self, outcome: object) -> None:
        self.outcome = outcome
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append((method, params))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome  # type: ignore[return-value]

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        raise AssertionError("tool executor must not send notifications")


class Observer:
    def __init__(self, evidence: object) -> None:
        self.evidence = evidence
        self.calls = 0

    def observe(
        self,
        request: ExecutionRequest,
        tool_result: Mapping[str, Any],
    ) -> ReadbackEvidence:
        self.calls += 1
        if isinstance(self.evidence, BaseException):
            raise self.evidence
        return self.evidence  # type: ignore[return-value]


def admitted_request() -> ExecutionRequest:
    return ExecutionRequest(
        operation_id="op-1",
        attempt_id="attempt-1",
        idempotency_key="idem-1",
        action="mcp_tool_call",
        parameters={
            "mcp": {
                "protocol_version": "2025-11-25",
                "server_identity": "example@1.0",
                "server_capabilities_hash": CAPABILITIES_HASH,
                "tool_name": "replace_record",
                "tool_schema_hash": SCHEMA_HASH,
            },
            "arguments": {"record_id": "42", "value": "updated"},
        },
    )


def malformed_request(*, mcp: object, arguments: object, extra: object | None = None) -> ExecutionRequest:
    parameters: dict[str, object] = {"mcp": mcp, "arguments": arguments}
    if extra is not None:
        parameters["unexpected"] = extra
    return ExecutionRequest("op", "attempt", "idem", "mcp_tool_call", parameters)


def assert_rejected_without_dispatch(request: ExecutionRequest) -> None:
    transport = ScriptedTransport({"content": []})
    result = McpStableToolExecutor(transport).execute(request)
    assert result.status is ExecutionStatus.FAILED
    assert result.reason is not None and result.reason.startswith("invalid_mcp_admission_envelope:")
    assert result.evidence["dispatch_state"] == "not_sent"
    assert transport.calls == []


def test_verified_readback_is_required_for_success() -> None:
    transport = ScriptedTransport({"content": [{"type": "text", "text": "ok"}]})
    observer = Observer(ReadbackEvidence(True, {"record_id": "42", "value": "updated"}))

    result = McpStableToolExecutor(transport, readback_observer=observer).execute(admitted_request())

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert observer.calls == 1
    assert transport.calls == [
        ("tools/call", {"name": "replace_record", "arguments": {"record_id": "42", "value": "updated"}})
    ]


def test_success_response_without_readback_is_unknown() -> None:
    result = McpStableToolExecutor(ScriptedTransport({"content": []})).execute(admitted_request())

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "independent_readback_required"


def test_failed_readback_is_unknown() -> None:
    observer = Observer(ReadbackEvidence(False, {"record_id": "42"}, "value_mismatch"))

    result = McpStableToolExecutor(
        ScriptedTransport({"content": []}),
        readback_observer=observer,
    ).execute(admitted_request())

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "value_mismatch"


def test_tool_error_is_failed_without_readback() -> None:
    observer = Observer(ReadbackEvidence(True))

    result = McpStableToolExecutor(
        ScriptedTransport({"isError": True, "content": [{"type": "text", "text": "denied"}]}),
        readback_observer=observer,
    ).execute(admitted_request())

    assert result.status is ExecutionStatus.FAILED
    assert result.reason == "mcp_tool_error"
    assert observer.calls == 0


def test_proven_not_sent_failure_is_failed() -> None:
    result = McpStableToolExecutor(
        ScriptedTransport(McpToolCallNotSentError("connection refused before write"))
    ).execute(admitted_request())

    assert result.status is ExecutionStatus.FAILED
    assert result.evidence["dispatch_state"] == "not_sent"


def test_possible_send_without_response_is_unknown() -> None:
    result = McpStableToolExecutor(
        ScriptedTransport(McpToolCallOutcomeUnknownError("response stream lost"))
    ).execute(admitted_request())

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.evidence["dispatch_state"] == "possibly_sent"


def test_generic_transport_error_during_call_is_unknown() -> None:
    result = McpStableToolExecutor(
        ScriptedTransport(McpTransportError("transport failed"))
    ).execute(admitted_request())

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.evidence["dispatch_state"] == "unknown"


def test_non_object_response_is_unknown() -> None:
    result = McpStableToolExecutor(ScriptedTransport(["unexpected"])).execute(admitted_request())

    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert result.reason == "tools_call_returned_non_object_result"


def test_non_mcp_request_is_rejected_without_dispatch() -> None:
    transport = ScriptedTransport({"content": []})
    request = ExecutionRequest("op", "attempt", "idem", "replace_text_file", {})

    result = McpStableToolExecutor(transport).execute(request)

    assert result.status is ExecutionStatus.FAILED
    assert result.reason == "unsupported_action"
    assert transport.calls == []


def test_missing_binding_fields_are_rejected_without_dispatch() -> None:
    assert_rejected_without_dispatch(malformed_request(mcp={}, arguments={}))


def test_unexpected_binding_or_parameter_fields_are_rejected_without_dispatch() -> None:
    binding = dict(admitted_request().parameters["mcp"])
    binding["unexpected"] = "value"
    assert_rejected_without_dispatch(malformed_request(mcp=binding, arguments={}))
    assert_rejected_without_dispatch(
        malformed_request(mcp=admitted_request().parameters["mcp"], arguments={}, extra=True)
    )


def test_invalid_identity_and_hashes_are_rejected_without_dispatch() -> None:
    binding = dict(admitted_request().parameters["mcp"])
    binding["server_identity"] = " example@1.0 "
    assert_rejected_without_dispatch(malformed_request(mcp=binding, arguments={}))

    binding = dict(admitted_request().parameters["mcp"])
    binding["tool_schema_hash"] = "ABCDEF"
    assert_rejected_without_dispatch(malformed_request(mcp=binding, arguments={}))


def test_non_json_and_cyclic_arguments_are_rejected_without_dispatch() -> None:
    assert_rejected_without_dispatch(
        malformed_request(mcp=admitted_request().parameters["mcp"], arguments={"value": object()})
    )

    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic
    assert_rejected_without_dispatch(
        malformed_request(mcp=admitted_request().parameters["mcp"], arguments=cyclic)
    )


def test_arguments_are_detached_before_transport_dispatch() -> None:
    transport = ScriptedTransport({"content": []})
    request = admitted_request()
    original_arguments = request.parameters["arguments"]

    result = McpStableToolExecutor(transport, require_readback=False).execute(request)

    assert result.status is ExecutionStatus.SUCCEEDED
    assert transport.calls[0][1]["arguments"] == original_arguments
    assert transport.calls[0][1]["arguments"] is not original_arguments
