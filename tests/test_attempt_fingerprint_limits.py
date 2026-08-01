# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.attempts import (
    MAX_FINGERPRINT_CANONICAL_BYTES,
    MAX_FINGERPRINT_JSON_NESTING,
    MAX_FINGERPRINT_JSON_NODES,
    MAX_FINGERPRINT_JSON_STRING_BYTES,
    AttemptFingerprintError,
    SQLiteExecutionAttemptLedger,
    _strict_json_identity,
)
from rpr.executor import ExecutionRequest


def request(parameters: object) -> ExecutionRequest:
    return ExecutionRequest("op", "attempt", "idem", "test_action", parameters)  # type: ignore[arg-type]


def nested_list(depth: int) -> object:
    value: object = None
    for _ in range(depth):
        value = [value]
    return value


def test_exact_nesting_limit_is_accepted() -> None:
    _strict_json_identity(nested_list(MAX_FINGERPRINT_JSON_NESTING), path="value")


def test_one_container_beyond_nesting_limit_is_rejected() -> None:
    with pytest.raises(AttemptFingerprintError, match="nesting"):
        _strict_json_identity(nested_list(MAX_FINGERPRINT_JSON_NESTING + 1), path="value")


def test_exact_expanded_node_budget_is_accepted() -> None:
    value = [None] * (MAX_FINGERPRINT_JSON_NODES - 1)
    _strict_json_identity(value, path="value")


def test_one_node_beyond_expanded_budget_is_rejected() -> None:
    value = [None] * MAX_FINGERPRINT_JSON_NODES
    with pytest.raises(AttemptFingerprintError, match="node count"):
        _strict_json_identity(value, path="value")


def test_exact_aggregate_string_budget_is_accepted() -> None:
    value = {"k": "x" * (MAX_FINGERPRINT_JSON_STRING_BYTES - 1)}
    _strict_json_identity(value, path="value")


def test_mapping_keys_and_values_share_string_budget() -> None:
    value = {"k": "x" * MAX_FINGERPRINT_JSON_STRING_BYTES}
    with pytest.raises(AttemptFingerprintError, match="string bytes"):
        _strict_json_identity(value, path="value")


def test_multibyte_strings_are_charged_as_utf8_bytes() -> None:
    value = {"k": "界" * (MAX_FINGERPRINT_JSON_STRING_BYTES // 3 + 1)}
    with pytest.raises(AttemptFingerprintError, match="string bytes"):
        _strict_json_identity(value, path="value")


def test_shared_container_is_charged_per_expanded_occurrence() -> None:
    shared = [None] * (MAX_FINGERPRINT_JSON_NODES // 2)
    with pytest.raises(AttemptFingerprintError, match="node count"):
        _strict_json_identity({"left": shared, "right": shared}, path="value")


def test_canonical_escape_expansion_is_bounded() -> None:
    SQLiteExecutionAttemptLedger.fingerprint(request({"value": "\x00" * 180_000}))
    with pytest.raises(AttemptFingerprintError, match="canonical JSON bytes"):
        SQLiteExecutionAttemptLedger.fingerprint(request({"value": "\x00" * 190_000}))


def test_canonical_limit_constant_exceeds_payload_budget() -> None:
    assert MAX_FINGERPRINT_CANONICAL_BYTES > MAX_FINGERPRINT_JSON_STRING_BYTES


def test_oversized_mapping_key_does_not_amplify_error_path() -> None:
    value = {"k" * 10_000: object()}
    with pytest.raises(AttemptFingerprintError) as captured:
        _strict_json_identity(value, path="value")
    assert len(str(captured.value)) < 200


def test_invalid_unicode_is_rejected_as_domain_error() -> None:
    with pytest.raises(AttemptFingerprintError, match="invalid Unicode"):
        _strict_json_identity({"value": "\ud800"}, path="value")
