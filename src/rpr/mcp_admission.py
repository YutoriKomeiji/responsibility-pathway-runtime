# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .executor import ExecutionRequest


MAX_JSON_NESTING = 64
MAX_JSON_NODES = 10_000
MAX_JSON_STRING_BYTES = 1_000_000
MAX_JSON_SERIALIZED_BYTES = 1_100_000
MAX_JSON_PATH_COMPONENT = 64


class McpAdmissionError(ValueError):
    """Raised when an MCP call cannot be admitted under the configured contract."""


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise McpAdmissionError("JSON strings must be valid UTF-8 text") from exc


def _child_key_path(path: str, key: str) -> str:
    component = key
    if len(component) > MAX_JSON_PATH_COMPONENT:
        component = f"{component[:MAX_JSON_PATH_COMPONENT]}…"
    return f"{path}.{component}"


def _consume_json_budget(
    budget: dict[str, int],
    *,
    path: str,
    string_bytes: int = 0,
) -> None:
    budget["nodes"] += 1
    if budget["nodes"] > MAX_JSON_NODES:
        raise McpAdmissionError(
            f"{path} exceeds maximum JSON node count {MAX_JSON_NODES}"
        )
    budget["string_bytes"] += string_bytes
    if budget["string_bytes"] > MAX_JSON_STRING_BYTES:
        raise McpAdmissionError(
            f"{path} exceeds maximum JSON UTF-8 bytes {MAX_JSON_STRING_BYTES}"
        )


def _strict_json_plain(
    value: Any,
    *,
    path: str,
    active_containers: set[int] | None = None,
    depth: int = 0,
    budget: dict[str, int] | None = None,
) -> Any:
    """Validate strict JSON and return a detached plain snapshot.

    Containers on the active recursion path are tracked to reject cycles.
    Nesting, expanded node count, and aggregate UTF-8 string bytes are bounded
    before the input is detached or hashed. Reusing the same acyclic container
    in separate branches is valid and is charged once per serialized occurrence.
    """

    current_budget = budget if budget is not None else {"nodes": 0, "string_bytes": 0}
    _consume_json_budget(
        current_budget,
        path=path,
        string_bytes=_utf8_size(value) if isinstance(value, str) else 0,
    )

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise McpAdmissionError(f"{path} contains a non-finite JSON number")
        return value

    if isinstance(value, Mapping) or isinstance(value, (list, tuple)):
        if depth >= MAX_JSON_NESTING:
            raise McpAdmissionError(
                f"{path} exceeds maximum JSON nesting depth {MAX_JSON_NESTING}"
            )
        active = active_containers if active_containers is not None else set()
        container_id = id(value)
        if container_id in active:
            raise McpAdmissionError(f"{path} contains a cyclic JSON container")
        active.add(container_id)
        try:
            if isinstance(value, Mapping):
                result: dict[str, Any] = {}
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise McpAdmissionError(f"{path} contains a non-string object key")
                    current_budget["string_bytes"] += _utf8_size(key)
                    if current_budget["string_bytes"] > MAX_JSON_STRING_BYTES:
                        raise McpAdmissionError(
                            f"{path} exceeds maximum JSON UTF-8 bytes {MAX_JSON_STRING_BYTES}"
                        )
                    result[key] = _strict_json_plain(
                        item,
                        path=_child_key_path(path, key),
                        active_containers=active,
                        depth=depth + 1,
                        budget=current_budget,
                    )
                return result
            return [
                _strict_json_plain(
                    item,
                    path=f"{path}[{index}]",
                    active_containers=active,
                    depth=depth + 1,
                    budget=current_budget,
                )
                for index, item in enumerate(value)
            ]
        finally:
            active.remove(container_id)

    raise McpAdmissionError(
        f"{path} contains a non-JSON value of type {type(value).__name__}"
    )


def _canonical_json_bytes(value: Any, *, path: str) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise McpAdmissionError(f"{path} cannot be canonically serialized as JSON") from exc
    if len(encoded) > MAX_JSON_SERIALIZED_BYTES:
        raise McpAdmissionError(
            f"{path} exceeds maximum canonical JSON bytes {MAX_JSON_SERIALIZED_BYTES}"
        )
    return encoded


def _strict_json_document(value: Any, *, path: str) -> tuple[Any, bytes]:
    plain = _strict_json_plain(value, path=path)
    return plain, _canonical_json_bytes(plain, path=path)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _strict_json_snapshot(value: Any, *, path: str) -> tuple[Any, str]:
    plain, encoded = _strict_json_document(value, path=path)
    return _freeze_json(plain), hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class McpServerToolSnapshot:
    protocol_version: str
    server_identity: str
    server_capabilities: Mapping[str, Any]
    tool_name: str
    tool_schema: Mapping[str, Any]
    _server_capabilities_hash: str = field(init=False, repr=False, compare=False)
    _tool_schema_hash: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("protocol_version", "server_identity", "tool_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise McpAdmissionError(f"{name} is required")
        if not isinstance(self.server_capabilities, Mapping):
            raise McpAdmissionError("server_capabilities must be a JSON object")
        if not isinstance(self.tool_schema, Mapping):
            raise McpAdmissionError("tool_schema must be a JSON object")

        capabilities, capabilities_hash = _strict_json_snapshot(
            self.server_capabilities,
            path="server_capabilities",
        )
        schema, schema_hash = _strict_json_snapshot(
            self.tool_schema,
            path="tool_schema",
        )
        object.__setattr__(self, "server_capabilities", capabilities)
        object.__setattr__(self, "tool_schema", schema)
        object.__setattr__(self, "_server_capabilities_hash", capabilities_hash)
        object.__setattr__(self, "_tool_schema_hash", schema_hash)

    def admission_binding(self) -> dict[str, str]:
        return {
            "protocol_version": self.protocol_version,
            "server_identity": self.server_identity,
            "server_capabilities_hash": self._server_capabilities_hash,
            "tool_name": self.tool_name,
            "tool_schema_hash": self._tool_schema_hash,
        }


class McpStableAdmissionAdapter:
    """Build RPR execution requests for the stable MCP compatibility boundary.

    This class does not perform MCP transport. It binds a verified MCP server/tool
    snapshot to RPR business identity before an executor is allowed to dispatch.
    """

    def __init__(self, contract_path: str | Path, *, experimental: bool = False) -> None:
        self.contract_path = Path(contract_path)
        self.contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        self.experimental = experimental

    def admit(
        self,
        snapshot: McpServerToolSnapshot,
        *,
        operation_id: str,
        attempt_id: str,
        idempotency_key: str,
        arguments: Mapping[str, Any],
    ) -> ExecutionRequest:
        version = self._version(snapshot.protocol_version)
        if version["requires_experimental_flag"] and not self.experimental:
            raise McpAdmissionError("experimental MCP protocol version is disabled")
        if version["lifecycle"] != "stable" and not self.experimental:
            raise McpAdmissionError("non-stable MCP protocol version is disabled")
        if not isinstance(arguments, Mapping):
            raise McpAdmissionError("arguments must be a JSON object")

        binding = snapshot.admission_binding()
        detached_arguments, _ = _strict_json_document(arguments, path="arguments")
        parameters = {
            "mcp": binding,
            "arguments": detached_arguments,
        }
        return ExecutionRequest(
            operation_id=operation_id,
            attempt_id=attempt_id,
            idempotency_key=idempotency_key,
            action="mcp_tool_call",
            parameters=parameters,
        )

    @staticmethod
    def assert_transport_retry(original: ExecutionRequest, retry: ExecutionRequest) -> None:
        fields = ("operation_id", "attempt_id", "idempotency_key")
        if any(getattr(original, field) != getattr(retry, field) for field in fields):
            raise McpAdmissionError("transport retry changed RPR business identity")
        if original.action != retry.action or original.parameters != retry.parameters:
            raise McpAdmissionError("transport retry changed admitted MCP request")

    @staticmethod
    def assert_business_retry(previous: ExecutionRequest, retry: ExecutionRequest) -> None:
        if previous.attempt_id == retry.attempt_id:
            raise McpAdmissionError("business retry requires a new attempt identity")

    def _version(self, protocol_version: str) -> dict[str, Any]:
        for version in self.contract.get("versions", []):
            if version.get("protocol_version") == protocol_version:
                return version
        raise McpAdmissionError(f"unsupported MCP protocol version: {protocol_version}")
