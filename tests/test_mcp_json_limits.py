# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from rpr.mcp_admission import (
    MAX_JSON_NESTING,
    MAX_JSON_NODES,
    MAX_JSON_PATH_COMPONENT,
    MAX_JSON_SERIALIZED_BYTES,
    MAX_JSON_STRING_BYTES,
    McpAdmissionError,
    McpServerToolSnapshot,
    McpStableAdmissionAdapter,
)


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs" / "mcp-compatibility.json"


def _nested_mapping(container_count: int) -> dict[str, Any]:
    value: Any = "leaf"
    for _ in range(container_count):
        value = {"next": value}
    return value


def _mixed_nesting(container_count: int) -> dict[str, Any]:
    value: Any = "leaf"
    for index in range(container_count - 1):
        value = {"next": value} if index % 2 == 0 else [value]
    return {"root": value}


def _snapshot(*, capabilities: dict[str, Any] | None = None) -> McpServerToolSnapshot:
    return McpServerToolSnapshot(
        protocol_version="2025-11-25",
        server_identity="server-a",
        server_capabilities=capabilities or {"tools": {}},
        tool_name="replace_record",
        tool_schema={"type": "object"},
    )


def _admit(arguments: dict[str, Any]):
    return McpStableAdmissionAdapter(CONTRACT).admit(
        _snapshot(),
        operation_id="op-limit",
        attempt_id="attempt-limit",
        idempotency_key="idem-limit",
        arguments=arguments,
    )


def test_arguments_accept_exact_maximum_container_depth() -> None:
    arguments = _nested_mapping(MAX_JSON_NESTING)
    request = _admit(arguments)
    assert request.parameters["arguments"] == arguments


def test_arguments_reject_one_container_beyond_maximum_depth() -> None:
    with pytest.raises(
        McpAdmissionError,
        match=rf"arguments.*maximum JSON nesting depth {MAX_JSON_NESTING}",
    ):
        _admit(_nested_mapping(MAX_JSON_NESTING + 1))


def test_snapshot_rejects_mixed_mapping_list_depth_with_domain_error() -> None:
    with pytest.raises(
        McpAdmissionError,
        match=rf"server_capabilities.*maximum JSON nesting depth {MAX_JSON_NESTING}",
    ):
        _snapshot(capabilities=_mixed_nesting(MAX_JSON_NESTING + 1))


def test_depth_tracking_is_per_branch_not_global_budget() -> None:
    branch = _nested_mapping(MAX_JSON_NESTING - 1)
    arguments = {"left": branch, "right": branch}
    request = _admit(arguments)
    assert request.parameters["arguments"]["left"] == branch
    assert request.parameters["arguments"]["right"] == branch


def test_arguments_accept_exact_expanded_node_budget() -> None:
    arguments = {"items": [None] * (MAX_JSON_NODES - 2)}
    request = _admit(arguments)
    assert len(request.parameters["arguments"]["items"]) == MAX_JSON_NODES - 2


def test_arguments_reject_one_node_beyond_expanded_budget() -> None:
    with pytest.raises(
        McpAdmissionError,
        match=rf"arguments.*maximum JSON node count {MAX_JSON_NODES}",
    ):
        _admit({"items": [None] * (MAX_JSON_NODES - 1)})


def test_arguments_accept_exact_ascii_utf8_budget() -> None:
    key = "value"
    value = "x" * (MAX_JSON_STRING_BYTES - len(key.encode("utf-8")))
    request = _admit({key: value})
    assert request.parameters["arguments"][key] == value


def test_arguments_reject_ascii_value_beyond_utf8_budget() -> None:
    key = "value"
    value = "x" * (MAX_JSON_STRING_BYTES - len(key.encode("utf-8")) + 1)
    with pytest.raises(
        McpAdmissionError,
        match=rf"arguments.*maximum JSON UTF-8 bytes {MAX_JSON_STRING_BYTES}",
    ):
        _admit({key: value})


def test_multibyte_values_are_charged_by_encoded_size() -> None:
    key = "値"
    remaining = MAX_JSON_STRING_BYTES - len(key.encode("utf-8"))
    value = "界" * (remaining // len("界".encode("utf-8")) + 1)
    assert len(value) < MAX_JSON_STRING_BYTES
    with pytest.raises(McpAdmissionError, match="maximum JSON UTF-8 bytes"):
        _admit({key: value})


def test_emoji_values_are_charged_by_encoded_size() -> None:
    key = "emoji"
    remaining = MAX_JSON_STRING_BYTES - len(key.encode("utf-8"))
    value = "😀" * (remaining // len("😀".encode("utf-8")) + 1)
    with pytest.raises(McpAdmissionError, match="maximum JSON UTF-8 bytes"):
        _admit({key: value})


def test_mapping_keys_are_charged_by_utf8_size() -> None:
    oversized_key = "鍵" * (MAX_JSON_STRING_BYTES // len("鍵".encode("utf-8")) + 1)
    with pytest.raises(
        McpAdmissionError,
        match=rf"arguments.*maximum JSON UTF-8 bytes {MAX_JSON_STRING_BYTES}",
    ):
        _admit({oversized_key: None})


def test_unpaired_surrogate_fails_as_domain_error() -> None:
    with pytest.raises(McpAdmissionError, match="valid UTF-8 text"):
        _admit({"value": "\ud800"})


def test_snapshot_and_arguments_use_independent_budgets() -> None:
    near_limit = "x" * (MAX_JSON_STRING_BYTES - len("payload".encode("utf-8")))
    snapshot = _snapshot(capabilities={"payload": near_limit})
    request = McpStableAdmissionAdapter(CONTRACT).admit(
        snapshot,
        operation_id="op-independent",
        attempt_id="attempt-independent",
        idempotency_key="idem-independent",
        arguments={"payload": near_limit},
    )
    assert request.parameters["arguments"]["payload"] == near_limit


def test_canonical_budget_accepts_bounded_escape_expansion() -> None:
    value = "\x00" * 100_000
    request = _admit({"value": value})
    assert request.parameters["arguments"]["value"] == value


def test_canonical_budget_rejects_control_character_expansion() -> None:
    value = "\x00" * 200_000
    assert len(value.encode("utf-8")) < MAX_JSON_STRING_BYTES
    with pytest.raises(
        McpAdmissionError,
        match=rf"arguments.*maximum canonical JSON bytes {MAX_JSON_SERIALIZED_BYTES}",
    ):
        _admit({"value": value})


def test_snapshot_uses_complete_canonical_byte_budget() -> None:
    with pytest.raises(
        McpAdmissionError,
        match=rf"server_capabilities.*maximum canonical JSON bytes {MAX_JSON_SERIALIZED_BYTES}",
    ):
        _snapshot(capabilities={"value": "\x00" * 200_000})


def test_unserializable_integer_fails_as_domain_error() -> None:
    huge_integer = 10**5_000
    with pytest.raises(McpAdmissionError, match="cannot be canonically serialized"):
        _admit({"value": huge_integer})


def test_repeated_shared_container_is_charged_per_serialized_occurrence() -> None:
    shared = [None] * (MAX_JSON_NODES // 2)
    with pytest.raises(McpAdmissionError, match="maximum JSON node count"):
        _admit({"left": shared, "right": shared})


def test_error_path_truncates_oversized_mapping_key() -> None:
    key = "k" * (MAX_JSON_PATH_COMPONENT + 20)
    with pytest.raises(McpAdmissionError) as captured:
        _admit({key: {"bad": {1, 2}}})

    message = str(captured.value)
    assert "…" in message
    assert len(message) < 256
