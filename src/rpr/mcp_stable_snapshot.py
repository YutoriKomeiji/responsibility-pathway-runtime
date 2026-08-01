# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .mcp_admission import (
    McpAdmissionError,
    McpServerToolSnapshot,
    _strict_json_snapshot,
)


STABLE_PROTOCOL_VERSION = "2025-11-25"


def _required_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise McpAdmissionError(f"{field} must be an object")
    return value


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise McpAdmissionError(f"{field} is required")
    return value.strip()


def _strict_frozen_json(value: Mapping[str, Any], *, path: str) -> Mapping[str, Any]:
    """Return only the immutable document from admission snapshot validation."""

    frozen, _canonical_hash = _strict_json_snapshot(value, path=path)
    if not isinstance(frozen, Mapping):
        raise McpAdmissionError(f"{path} must be a JSON object")
    return frozen


@dataclass(frozen=True)
class McpStableServerSnapshot:
    protocol_version: str
    server_identity: str
    server_capabilities: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "server_capabilities",
            _strict_frozen_json(self.server_capabilities, path="server_capabilities"),
        )


class McpStableSnapshotValidator:
    """Validate stable MCP initialize and tools/list results before admission.

    This validator consumes already-decoded MCP result objects. It performs no
    transport and never invokes a tool. Its output is suitable for the stable
    admission adapter only after the initialize and tools snapshots agree.
    """

    @staticmethod
    def validate_initialize(result: Mapping[str, Any]) -> McpStableServerSnapshot:
        result = _required_mapping(result, "initialize result")
        protocol_version = _required_text(result.get("protocolVersion"), "protocolVersion")
        if protocol_version != STABLE_PROTOCOL_VERSION:
            raise McpAdmissionError(
                f"stable initialize requires protocol {STABLE_PROTOCOL_VERSION}, got {protocol_version}"
            )

        server_info = _required_mapping(result.get("serverInfo"), "serverInfo")
        name = _required_text(server_info.get("name"), "serverInfo.name")
        version = _required_text(server_info.get("version"), "serverInfo.version")
        capabilities = _required_mapping(result.get("capabilities"), "capabilities")
        if "tools" not in capabilities:
            raise McpAdmissionError("server does not declare tools capability")
        _required_mapping(capabilities.get("tools"), "capabilities.tools")

        return McpStableServerSnapshot(
            protocol_version=protocol_version,
            server_identity=f"{name}@{version}",
            server_capabilities=capabilities,
        )

    @staticmethod
    def validate_tools_list(
        result: Mapping[str, Any],
        *,
        server: McpStableServerSnapshot,
        tool_name: str,
    ) -> McpServerToolSnapshot:
        result = _required_mapping(result, "tools/list result")
        requested_name = _required_text(tool_name, "tool_name")
        tools = result.get("tools")
        if not isinstance(tools, Sequence) or isinstance(tools, (str, bytes)):
            raise McpAdmissionError("tools must be a list")

        selected: Mapping[str, Any] | None = None
        names: set[str] = set()
        for index, raw_tool in enumerate(tools):
            tool = _required_mapping(raw_tool, f"tools[{index}]")
            name = _required_text(tool.get("name"), f"tools[{index}].name")
            if name in names:
                raise McpAdmissionError(f"duplicate MCP tool name: {name}")
            names.add(name)
            schema = _required_mapping(tool.get("inputSchema"), f"tools[{index}].inputSchema")
            if schema.get("type") != "object":
                raise McpAdmissionError(f"tool {name} inputSchema must declare object type")
            properties = schema.get("properties", {})
            _required_mapping(properties, f"tool {name} inputSchema.properties")
            required = schema.get("required", [])
            if not isinstance(required, Sequence) or isinstance(required, (str, bytes)):
                raise McpAdmissionError(f"tool {name} inputSchema.required must be a list")
            if len(required) != len(set(required)) or not all(isinstance(item, str) and item for item in required):
                raise McpAdmissionError(f"tool {name} inputSchema.required is invalid")
            if name == requested_name:
                selected = tool

        if selected is None:
            raise McpAdmissionError(f"requested MCP tool not found: {requested_name}")

        return McpServerToolSnapshot(
            protocol_version=server.protocol_version,
            server_identity=server.server_identity,
            server_capabilities=server.server_capabilities,
            tool_name=requested_name,
            tool_schema=dict(_required_mapping(selected.get("inputSchema"), "selected tool inputSchema")),
        )

    @staticmethod
    def assert_same_server(
        original: McpStableServerSnapshot,
        refreshed: McpStableServerSnapshot,
    ) -> None:
        if original != refreshed:
            raise McpAdmissionError("MCP initialize snapshot changed before dispatch")
