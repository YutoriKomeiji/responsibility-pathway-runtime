# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

import pytest

import rpr.mcp_admission as mcp_admission
from rpr.mcp_admission import McpAdmissionError, McpServerToolSnapshot, McpStableAdmissionAdapter


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs" / "mcp-compatibility.json"


def snapshot(*, protocol_version: str = "2025-11-25", server_identity: str = "server-a", schema_type: str = "string") -> McpServerToolSnapshot:
    return McpServerToolSnapshot(
        protocol_version=protocol_version,
        server_identity=server_identity,
        server_capabilities={"tools": {"listChanged": True}},
        tool_name="replace_record",
        tool_schema={"type": "object", "properties": {"value": {"type": schema_type}}},
    )


def test_stable_snapshot_is_bound_into_execution_request() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    request = adapter.admit(
        snapshot(),
        operation_id="op-1",
        attempt_id="attempt-1",
        idempotency_key="idem-1",
        arguments={"value": "approved"},
    )

    assert request.action == "mcp_tool_call"
    assert request.parameters["mcp"]["protocol_version"] == "2025-11-25"
    assert request.parameters["mcp"]["server_identity"] == "server-a"
    assert len(request.parameters["mcp"]["server_capabilities_hash"]) == 64
    assert len(request.parameters["mcp"]["tool_schema_hash"]) == 64


def test_snapshot_is_detached_deeply_immutable_and_hash_stable() -> None:
    capabilities = {"tools": {"listChanged": True}, "modes": ["read", "write"]}
    schema = {"type": "object", "properties": {"value": {"type": "string"}}}
    captured = McpServerToolSnapshot(
        protocol_version="2025-11-25",
        server_identity="server-a",
        server_capabilities=capabilities,
        tool_name="replace_record",
        tool_schema=schema,
    )
    original_binding = captured.admission_binding()

    capabilities["tools"]["listChanged"] = False
    capabilities["modes"].append("admin")
    schema["properties"]["value"]["type"] = "integer"

    assert captured.admission_binding() == original_binding
    assert captured.server_capabilities["tools"]["listChanged"] is True
    assert captured.server_capabilities["modes"] == ("read", "write")
    with pytest.raises(TypeError):
        captured.server_capabilities["tools"]["listChanged"] = False


def test_snapshot_binding_reuses_construction_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = snapshot()
    expected = captured.admission_binding()

    def fail_if_serialized_again(value, *, path):
        raise AssertionError(f"unexpected reserialization at {path}")

    monkeypatch.setattr(mcp_admission, "_canonical_json_bytes", fail_if_serialized_again)

    assert captured.admission_binding() == expected
    assert captured.admission_binding() == expected


def test_snapshot_hashes_are_canonical_and_not_cross_wired() -> None:
    first = McpServerToolSnapshot(
        protocol_version="2025-11-25",
        server_identity="server-a",
        server_capabilities={"z": 1, "a": {"b": 2}},
        tool_name="replace_record",
        tool_schema={"type": "object", "required": ["value"]},
    )
    reordered = McpServerToolSnapshot(
        protocol_version="2025-11-25",
        server_identity="server-a",
        server_capabilities={"a": {"b": 2}, "z": 1},
        tool_name="replace_record",
        tool_schema={"required": ["value"], "type": "object"},
    )
    swapped_content = McpServerToolSnapshot(
        protocol_version="2025-11-25",
        server_identity="server-a",
        server_capabilities={"type": "object", "required": ["value"]},
        tool_name="replace_record",
        tool_schema={"z": 1, "a": {"b": 2}},
    )

    first_binding = first.admission_binding()
    reordered_binding = reordered.admission_binding()
    swapped_binding = swapped_content.admission_binding()

    assert first_binding == reordered_binding
    assert first_binding["server_capabilities_hash"] == swapped_binding["tool_schema_hash"]
    assert first_binding["tool_schema_hash"] == swapped_binding["server_capabilities_hash"]
    assert first_binding["server_capabilities_hash"] != first_binding["tool_schema_hash"]


def test_snapshot_private_hashes_do_not_leak_into_repr() -> None:
    captured = snapshot()
    rendered = repr(captured)

    assert "_server_capabilities_hash" not in rendered
    assert "_tool_schema_hash" not in rendered
    assert captured._server_capabilities_hash not in rendered
    assert captured._tool_schema_hash not in rendered


@pytest.mark.parametrize(
    "invalid",
    [
        {"bad": {1, 2}},
        {1: "non-string-key"},
        {"bad": float("nan")},
        {"bad": float("inf")},
    ],
)
def test_snapshot_rejects_non_strict_json(invalid) -> None:
    with pytest.raises(McpAdmissionError, match="JSON|non-string|non-finite"):
        McpServerToolSnapshot(
            protocol_version="2025-11-25",
            server_identity="server-a",
            server_capabilities=invalid,
            tool_name="replace_record",
            tool_schema={"type": "object"},
        )


def test_snapshot_rejects_cyclic_json_with_domain_error() -> None:
    cyclic_capabilities: dict[str, object] = {"tools": {}}
    cyclic_capabilities["self"] = cyclic_capabilities

    with pytest.raises(McpAdmissionError, match="cyclic JSON container"):
        McpServerToolSnapshot(
            protocol_version="2025-11-25",
            server_identity="server-a",
            server_capabilities=cyclic_capabilities,
            tool_name="replace_record",
            tool_schema={"type": "object"},
        )


def test_arguments_reject_indirect_list_mapping_cycle() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    arguments: dict[str, object] = {}
    nested: list[object] = [arguments]
    arguments["nested"] = nested

    with pytest.raises(McpAdmissionError, match="arguments.*cyclic JSON container"):
        adapter.admit(
            snapshot(),
            operation_id="op-cycle",
            attempt_id="a-cycle",
            idempotency_key="i-cycle",
            arguments=arguments,
        )


def test_shared_acyclic_container_is_detached_at_each_location() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    shared = {"value": ["x"]}
    arguments = {"left": shared, "right": shared}

    request = adapter.admit(
        snapshot(),
        operation_id="op-shared",
        attempt_id="a-shared",
        idempotency_key="i-shared",
        arguments=arguments,
    )

    assert request.parameters["arguments"] == {
        "left": {"value": ["x"]},
        "right": {"value": ["x"]},
    }
    assert request.parameters["arguments"]["left"] is not request.parameters["arguments"]["right"]


def test_arguments_are_strict_json_and_detached_from_caller_mutation() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    arguments = {"record": {"tags": ["a"]}}
    request = adapter.admit(
        snapshot(),
        operation_id="op",
        attempt_id="a",
        idempotency_key="i",
        arguments=arguments,
    )

    arguments["record"]["tags"].append("b")
    assert request.parameters["arguments"] == {"record": {"tags": ["a"]}}

    with pytest.raises(McpAdmissionError, match="non-finite"):
        adapter.admit(
            snapshot(),
            operation_id="op-2",
            attempt_id="a-2",
            idempotency_key="i-2",
            arguments={"value": float("nan")},
        )


def test_unknown_version_fails_closed() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    with pytest.raises(McpAdmissionError, match="unsupported MCP protocol version"):
        adapter.admit(snapshot(protocol_version="2099-01-01"), operation_id="op", attempt_id="a", idempotency_key="i", arguments={})


def test_release_candidate_is_disabled_without_explicit_flag() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    with pytest.raises(McpAdmissionError, match="experimental MCP protocol version is disabled"):
        adapter.admit(snapshot(protocol_version="2026-07-28"), operation_id="op", attempt_id="a", idempotency_key="i", arguments={})


def test_identity_or_schema_change_changes_admitted_request() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    original = adapter.admit(snapshot(), operation_id="op", attempt_id="a", idempotency_key="i", arguments={"value": "x"})
    changed_server = adapter.admit(snapshot(server_identity="server-b"), operation_id="op", attempt_id="a", idempotency_key="i", arguments={"value": "x"})
    changed_schema = adapter.admit(snapshot(schema_type="integer"), operation_id="op", attempt_id="a", idempotency_key="i", arguments={"value": "x"})

    with pytest.raises(McpAdmissionError, match="changed admitted MCP request"):
        adapter.assert_transport_retry(original, changed_server)
    with pytest.raises(McpAdmissionError, match="changed admitted MCP request"):
        adapter.assert_transport_retry(original, changed_schema)


def test_transport_retry_preserves_complete_business_identity() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    original = adapter.admit(snapshot(), operation_id="op", attempt_id="a", idempotency_key="i", arguments={"value": "x"})
    same = adapter.admit(snapshot(), operation_id="op", attempt_id="a", idempotency_key="i", arguments={"value": "x"})
    adapter.assert_transport_retry(original, same)

    changed_attempt = adapter.admit(snapshot(), operation_id="op", attempt_id="b", idempotency_key="i", arguments={"value": "x"})
    with pytest.raises(McpAdmissionError, match="changed RPR business identity"):
        adapter.assert_transport_retry(original, changed_attempt)


def test_business_retry_requires_new_attempt_identity() -> None:
    adapter = McpStableAdmissionAdapter(CONTRACT)
    previous = adapter.admit(snapshot(), operation_id="op", attempt_id="a", idempotency_key="i", arguments={})
    invalid = adapter.admit(snapshot(), operation_id="op", attempt_id="a", idempotency_key="i-2", arguments={})
    valid = adapter.admit(snapshot(), operation_id="op", attempt_id="b", idempotency_key="i-2", arguments={})

    with pytest.raises(McpAdmissionError, match="new attempt identity"):
        adapter.assert_business_retry(previous, invalid)
    adapter.assert_business_retry(previous, valid)
