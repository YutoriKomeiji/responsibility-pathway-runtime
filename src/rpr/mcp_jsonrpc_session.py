# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .mcp_stable_transport import McpStableTransport, McpTransportError


class McpJsonRpcChannel(Protocol):
    """Decoded-message channel below the bounded JSON-RPC session.

    Concrete HTTP or stdio framing is intentionally outside this contract.
    """

    def exchange(self, message: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def send(self, message: Mapping[str, Any]) -> None: ...


@dataclass(frozen=True)
class McpJsonRpcRemoteError(McpTransportError):
    code: int
    message: str
    data: Any = None

    def __str__(self) -> str:
        return f"JSON-RPC error {self.code}: {self.message}"


class McpJsonRpcSession(McpStableTransport):
    """Fail-closed synchronous JSON-RPC 2.0 session for stable MCP.

    It owns request IDs and response correlation only. Authentication, byte
    framing, reconnect policy, and network I/O remain channel responsibilities.
    """

    def __init__(self, channel: McpJsonRpcChannel, *, first_request_id: int = 1) -> None:
        if isinstance(first_request_id, bool) or not isinstance(first_request_id, int):
            raise ValueError("first_request_id must be an integer")
        if first_request_id < 0:
            raise ValueError("first_request_id must be non-negative")
        self.channel = channel
        self._next_request_id = first_request_id

    def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        method_value = self._method(method)
        params_value = self._params(params)
        request_id = self._next_request_id
        self._next_request_id += 1
        envelope = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method_value,
            "params": params_value,
        }
        try:
            response = self.channel.exchange(envelope)
        except McpTransportError:
            raise
        except (TimeoutError, ConnectionError, OSError):
            raise
        except Exception as exc:
            raise McpTransportError(f"JSON-RPC channel exchange failed: {type(exc).__name__}: {exc}") from exc
        return self._validate_response(response, expected_id=request_id)

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        envelope = {
            "jsonrpc": "2.0",
            "method": self._method(method),
            "params": self._params(params),
        }
        try:
            self.channel.send(envelope)
        except McpTransportError:
            raise
        except (TimeoutError, ConnectionError, OSError):
            raise
        except Exception as exc:
            raise McpTransportError(f"JSON-RPC channel notification failed: {type(exc).__name__}: {exc}") from exc

    @staticmethod
    def _method(method: str) -> str:
        if not isinstance(method, str) or not method.strip():
            raise McpTransportError("JSON-RPC method must be a non-empty string")
        return method.strip()

    @staticmethod
    def _params(params: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(params, Mapping):
            raise McpTransportError("JSON-RPC params must be an object")
        return dict(params)

    @staticmethod
    def _validate_response(response: object, *, expected_id: int) -> Mapping[str, Any]:
        if not isinstance(response, Mapping):
            raise McpTransportError("JSON-RPC response must be an object")
        value = dict(response)
        if value.get("jsonrpc") != "2.0":
            raise McpTransportError("JSON-RPC response version mismatch")
        if "id" not in value:
            raise McpTransportError("JSON-RPC notification cannot satisfy a request")
        response_id = value["id"]
        if isinstance(response_id, bool) or response_id != expected_id:
            raise McpTransportError(
                f"JSON-RPC response id mismatch: expected {expected_id!r}, got {response_id!r}"
            )
        has_result = "result" in value
        has_error = "error" in value
        if has_result == has_error:
            raise McpTransportError("JSON-RPC response must contain exactly one of result or error")
        extras = set(value) - {"jsonrpc", "id", "result", "error"}
        if extras:
            raise McpTransportError(f"JSON-RPC response contains unsupported members: {sorted(extras)!r}")
        if has_error:
            error = value["error"]
            if not isinstance(error, Mapping):
                raise McpTransportError("JSON-RPC error must be an object")
            error_value = dict(error)
            code = error_value.get("code")
            message = error_value.get("message")
            if isinstance(code, bool) or not isinstance(code, int):
                raise McpTransportError("JSON-RPC error code must be an integer")
            if not isinstance(message, str) or not message.strip():
                raise McpTransportError("JSON-RPC error message must be a non-empty string")
            unsupported = set(error_value) - {"code", "message", "data"}
            if unsupported:
                raise McpTransportError(
                    f"JSON-RPC error contains unsupported members: {sorted(unsupported)!r}"
                )
            raise McpJsonRpcRemoteError(code, message.strip(), error_value.get("data"))
        result = value["result"]
        if not isinstance(result, Mapping):
            raise McpTransportError("MCP JSON-RPC result must be an object")
        return dict(result)
