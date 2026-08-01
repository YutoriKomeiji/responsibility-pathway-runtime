# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy

import pytest

from rpr.mcp_admission import McpAdmissionError
from rpr.mcp_stable_snapshot import McpStableSnapshotValidator


def initialize_result() -> dict:
    return {
        "protocolVersion": "2025-11-25",
        "capabilities": {"tools": {"listChanged": True}, "modes": ["read", "write"]},
        "serverInfo": {"name": "example-server", "version": "1.2.3"},
    }


def tools_result() -> dict:
    return {
        "tools": [
            {
                "name": "replace_text_file",
                "description": "Replace a bounded text file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "read_text_file",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        ]
    }


def test_stable_initialize_and_tools_list_build_admission_snapshot() -> None:
    server = McpStableSnapshotValidator.validate_initialize(initialize_result())
    snapshot = McpStableSnapshotValidator.validate_tools_list(
        tools_result(), server=server, tool_name="replace_text_file"
    )

    assert snapshot.protocol_version == "2025-11-25"
    assert snapshot.server_identity == "example-server@1.2.3"
    assert snapshot.tool_name == "replace_text_file"
    assert snapshot.tool_schema["required"] == ("path", "content")
    binding = snapshot.admission_binding()
    assert binding["server_identity"] == "example-server@1.2.3"
    assert binding["server_capabilities_hash"]
    assert binding["tool_schema_hash"]


def test_initialize_snapshot_is_detached_and_deeply_immutable() -> None:
    result = initialize_result()
    server = McpStableSnapshotValidator.validate_initialize(result)

    result["capabilities"]["tools"]["listChanged"] = False
    result["capabilities"]["modes"].append("admin")

    assert server.server_capabilities["tools"]["listChanged"] is True
    assert server.server_capabilities["modes"] == ("read", "write")
    with pytest.raises(TypeError):
        server.server_capabilities["tools"]["listChanged"] = False


def test_initialize_snapshot_rejects_nested_non_json_values() -> None:
    result = initialize_result()
    result["capabilities"]["tools"]["bad"] = {"not-json"}
    with pytest.raises(McpAdmissionError, match="non-JSON"):
        McpStableSnapshotValidator.validate_initialize(result)


def test_initialize_protocol_mismatch_fails_closed() -> None:
    result = initialize_result()
    result["protocolVersion"] = "2026-07-28"
    with pytest.raises(McpAdmissionError, match="stable initialize requires protocol"):
        McpStableSnapshotValidator.validate_initialize(result)


def test_initialize_without_tools_capability_fails_closed() -> None:
    result = initialize_result()
    result["capabilities"] = {}
    with pytest.raises(McpAdmissionError, match="tools capability"):
        McpStableSnapshotValidator.validate_initialize(result)


def test_duplicate_tool_name_fails_closed() -> None:
    server = McpStableSnapshotValidator.validate_initialize(initialize_result())
    result = tools_result()
    result["tools"].append(copy.deepcopy(result["tools"][0]))
    with pytest.raises(McpAdmissionError, match="duplicate MCP tool name"):
        McpStableSnapshotValidator.validate_tools_list(
            result, server=server, tool_name="replace_text_file"
        )


def test_missing_requested_tool_fails_closed() -> None:
    server = McpStableSnapshotValidator.validate_initialize(initialize_result())
    with pytest.raises(McpAdmissionError, match="requested MCP tool not found"):
        McpStableSnapshotValidator.validate_tools_list(
            tools_result(), server=server, tool_name="delete_everything"
        )


def test_non_object_input_schema_fails_closed() -> None:
    server = McpStableSnapshotValidator.validate_initialize(initialize_result())
    result = tools_result()
    result["tools"][0]["inputSchema"]["type"] = "array"
    with pytest.raises(McpAdmissionError, match="must declare object type"):
        McpStableSnapshotValidator.validate_tools_list(
            result, server=server, tool_name="replace_text_file"
        )


def test_initialize_identity_or_capability_drift_fails_closed() -> None:
    original = McpStableSnapshotValidator.validate_initialize(initialize_result())
    changed_result = initialize_result()
    changed_result["serverInfo"]["version"] = "1.2.4"
    changed = McpStableSnapshotValidator.validate_initialize(changed_result)
    with pytest.raises(McpAdmissionError, match="snapshot changed before dispatch"):
        McpStableSnapshotValidator.assert_same_server(original, changed)


def test_caller_mutation_cannot_hide_initialize_drift() -> None:
    original_result = initialize_result()
    original = McpStableSnapshotValidator.validate_initialize(original_result)
    original_result["capabilities"]["tools"]["listChanged"] = False

    refreshed_result = initialize_result()
    refreshed_result["capabilities"]["tools"]["listChanged"] = False
    refreshed = McpStableSnapshotValidator.validate_initialize(refreshed_result)

    with pytest.raises(McpAdmissionError, match="snapshot changed before dispatch"):
        McpStableSnapshotValidator.assert_same_server(original, refreshed)


def test_tool_schema_drift_changes_admission_binding() -> None:
    server = McpStableSnapshotValidator.validate_initialize(initialize_result())
    first = McpStableSnapshotValidator.validate_tools_list(
        tools_result(), server=server, tool_name="replace_text_file"
    )
    changed_result = tools_result()
    changed_result["tools"][0]["inputSchema"]["properties"]["mode"] = {"type": "string"}
    second = McpStableSnapshotValidator.validate_tools_list(
        changed_result, server=server, tool_name="replace_text_file"
    )
    assert first.admission_binding()["tool_schema_hash"] != second.admission_binding()["tool_schema_hash"]
