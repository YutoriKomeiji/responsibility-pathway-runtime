# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .executor import ExecutionRequest
from .mcp_admission import McpAdmissionError, McpStableAdmissionAdapter
from .mcp_stable_snapshot import McpStableSnapshotValidator, STABLE_PROTOCOL_VERSION


class McpTransportError(RuntimeError):
    """A bounded MCP transport or JSON-RPC failure before tool dispatch."""


class McpPreDispatchError(RuntimeError):
    """Raised when stable MCP preparation fails before any tool mutation."""

    def __init__(self, phase: str, reason: str) -> None:
        super().__init__(f"MCP pre-dispatch failure during {phase}: {reason}")
        self.phase = phase
        self.reason = reason


class McpStableTransport(Protocol):
    """Minimal synchronous transport surface used by stable orchestration.

    Implementations own HTTP, stdio, authentication, framing, request IDs, and
    timeout behavior. They must return decoded JSON-RPC result objects and raise
    McpTransportError for protocol-level failures.
    """

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def notify(self, method: str, params: Mapping[str, Any]) -> None: ...


@dataclass(frozen=True)
class McpPreparedCall:
    request: ExecutionRequest
    server_identity: str
    protocol_version: str
    tool_name: str


class McpStableOrchestrator:
    """Prepare a stable MCP tool call without dispatching the tool.

    Connection, initialize, initialized notification, and tools/list all occur
    before an RPR execution attempt is created. Any failure here is therefore a
    pre-dispatch failure, never evidence of an uncertain external mutation.
    """

    def __init__(
        self,
        transport: McpStableTransport,
        admission: McpStableAdmissionAdapter,
        *,
        client_name: str = "responsibility-pathway-runtime",
        client_version: str = "0.1.0a2",
    ) -> None:
        if not client_name.strip() or not client_version.strip():
            raise ValueError("MCP client name and version are required")
        self.transport = transport
        self.admission = admission
        self.client_name = client_name
        self.client_version = client_version

    def prepare(
        self,
        *,
        tool_name: str,
        arguments: Mapping[str, Any],
        operation_id: str,
        attempt_id: str,
        idempotency_key: str,
    ) -> McpPreparedCall:
        initialize_params = {
            "protocolVersion": STABLE_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": self.client_name, "version": self.client_version},
        }
        initialize_result = self._request("initialize", initialize_params, phase="initialize")
        try:
            server = McpStableSnapshotValidator.validate_initialize(initialize_result)
        except McpAdmissionError as exc:
            raise McpPreDispatchError("initialize_validation", str(exc)) from exc

        self._notify("notifications/initialized", {}, phase="initialized_notification")
        tools_result = self._request("tools/list", {}, phase="tools_list")
        try:
            snapshot = McpStableSnapshotValidator.validate_tools_list(
                tools_result,
                server=server,
                tool_name=tool_name,
            )
            request = self.admission.admit(
                snapshot,
                operation_id=operation_id,
                attempt_id=attempt_id,
                idempotency_key=idempotency_key,
                arguments=arguments,
            )
        except McpAdmissionError as exc:
            raise McpPreDispatchError("admission", str(exc)) from exc

        return McpPreparedCall(
            request=request,
            server_identity=server.server_identity,
            protocol_version=server.protocol_version,
            tool_name=tool_name,
        )

    def _request(
        self,
        method: str,
        params: Mapping[str, Any],
        *,
        phase: str,
    ) -> Mapping[str, Any]:
        try:
            result = self.transport.request(method, params)
        except (McpTransportError, TimeoutError, ConnectionError, OSError) as exc:
            raise McpPreDispatchError(phase, f"{type(exc).__name__}: {exc}") from exc
        if not isinstance(result, Mapping):
            raise McpPreDispatchError(phase, "transport returned a non-object result")
        return result

    def _notify(self, method: str, params: Mapping[str, Any], *, phase: str) -> None:
        try:
            self.transport.notify(method, params)
        except (McpTransportError, TimeoutError, ConnectionError, OSError) as exc:
            raise McpPreDispatchError(phase, f"{type(exc).__name__}: {exc}") from exc
