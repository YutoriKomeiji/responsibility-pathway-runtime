# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import re
from typing import Any, Mapping, Protocol

from .executor import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ReadbackEvidence,
)
from .mcp_admission import McpAdmissionError, _strict_json_document
from .mcp_stable_snapshot import STABLE_PROTOCOL_VERSION
from .mcp_stable_transport import McpStableTransport, McpTransportError


_MCP_BINDING_FIELDS = frozenset(
    {
        "protocol_version",
        "server_identity",
        "server_capabilities_hash",
        "tool_name",
        "tool_schema_hash",
    }
)
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")


class McpToolCallNotSentError(McpTransportError):
    """The transport failed before the tools/call request could be sent."""


class McpToolCallOutcomeUnknownError(McpTransportError):
    """The tools/call request may have been sent, but no reliable result exists."""


class McpReadbackObserver(Protocol):
    """Independently observe the external state affected by a tool call."""

    def observe(
        self,
        request: ExecutionRequest,
        tool_result: Mapping[str, Any],
    ) -> ReadbackEvidence: ...


def _validated_dispatch_parameters(request: ExecutionRequest) -> tuple[str, dict[str, Any]]:
    if set(request.parameters) != {"mcp", "arguments"}:
        raise McpAdmissionError("MCP request parameters must contain only mcp and arguments")

    mcp = request.parameters.get("mcp")
    arguments = request.parameters.get("arguments")
    if not isinstance(mcp, Mapping) or not isinstance(arguments, Mapping):
        raise McpAdmissionError("MCP admission envelope must contain object values")
    if set(mcp) != _MCP_BINDING_FIELDS:
        raise McpAdmissionError("MCP admission binding fields are incomplete or unexpected")

    for field in ("protocol_version", "server_identity", "tool_name"):
        value = mcp.get(field)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise McpAdmissionError(f"MCP admission field {field} is invalid")

    if mcp["protocol_version"] != STABLE_PROTOCOL_VERSION:
        raise McpAdmissionError(
            f"stable MCP executor requires protocol {STABLE_PROTOCOL_VERSION}"
        )

    for field in ("server_capabilities_hash", "tool_schema_hash"):
        value = mcp.get(field)
        if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
            raise McpAdmissionError(
                f"MCP admission field {field} must be a lowercase SHA-256 hex digest"
            )

    detached_arguments, _ = _strict_json_document(arguments, path="arguments")
    if not isinstance(detached_arguments, dict):
        raise McpAdmissionError("arguments must be a JSON object")
    return mcp["tool_name"], detached_arguments


class McpStableToolExecutor:
    """Execute an admitted stable MCP tool call with explicit uncertainty handling.

    The executor accepts only requests produced by the stable MCP admission path.
    A successful MCP response is not sufficient for a mutating operation: an
    independent readback observer must verify the resulting external state.
    """

    def __init__(
        self,
        transport: McpStableTransport,
        *,
        readback_observer: McpReadbackObserver | None = None,
        require_readback: bool = True,
    ) -> None:
        self.transport = transport
        self.readback_observer = readback_observer
        self.require_readback = require_readback

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.action != "mcp_tool_call":
            return ExecutionResult(ExecutionStatus.FAILED, reason="unsupported_action")

        try:
            tool_name, arguments = _validated_dispatch_parameters(request)
        except McpAdmissionError as exc:
            return ExecutionResult(
                ExecutionStatus.FAILED,
                {"dispatch_state": "not_sent"},
                reason=f"invalid_mcp_admission_envelope: {exc}",
            )

        params = {"name": tool_name, "arguments": arguments}
        try:
            raw_result = self.transport.request("tools/call", params)
        except McpToolCallNotSentError as exc:
            return ExecutionResult(
                ExecutionStatus.FAILED,
                {"dispatch_state": "not_sent"},
                reason=f"{type(exc).__name__}: {exc}",
            )
        except (McpToolCallOutcomeUnknownError, TimeoutError, ConnectionError, OSError) as exc:
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "possibly_sent"},
                reason=f"{type(exc).__name__}: {exc}",
            )
        except McpTransportError as exc:
            # A generic transport failure during tools/call cannot prove that the
            # server did not receive the request, so fail closed as unknown.
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "unknown"},
                reason=f"{type(exc).__name__}: {exc}",
            )

        if not isinstance(raw_result, Mapping):
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "sent", "response_shape": type(raw_result).__name__},
                reason="tools_call_returned_non_object_result",
            )

        tool_result = dict(raw_result)
        if tool_result.get("isError") is True:
            return ExecutionResult(
                ExecutionStatus.FAILED,
                {"dispatch_state": "sent", "tool_result": tool_result},
                reason="mcp_tool_error",
            )

        if not self.require_readback:
            return ExecutionResult(
                ExecutionStatus.SUCCEEDED,
                {"dispatch_state": "sent", "tool_result": tool_result},
            )

        if self.readback_observer is None:
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "sent", "tool_result": tool_result},
                reason="independent_readback_required",
            )

        try:
            readback = self.readback_observer.observe(request, tool_result)
        except (TimeoutError, ConnectionError, OSError, ValueError, TypeError) as exc:
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "sent", "tool_result": tool_result},
                reason=f"readback_failed: {type(exc).__name__}: {exc}",
            )

        if not isinstance(readback, ReadbackEvidence):
            return ExecutionResult(
                ExecutionStatus.WRITE_STATUS_UNKNOWN,
                {"dispatch_state": "sent", "tool_result": tool_result},
                reason="readback_observer_returned_invalid_evidence",
            )

        return ExecutionResult(
            ExecutionStatus.SUCCEEDED if readback.verified else ExecutionStatus.WRITE_STATUS_UNKNOWN,
            {"dispatch_state": "sent", "tool_result": tool_result},
            readback,
            None if readback.verified else (readback.reason or "readback_not_verified"),
        )
