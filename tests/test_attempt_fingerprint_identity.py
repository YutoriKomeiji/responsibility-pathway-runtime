# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import math

import pytest

from rpr.attempts import AttemptFingerprintError, SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest


def request(parameters: object) -> ExecutionRequest:
    return ExecutionRequest("op", "attempt", "idem", "test_action", parameters)  # type: ignore[arg-type]


def test_fingerprint_is_independent_of_mapping_key_order() -> None:
    left = request({"outer": {"a": 1, "b": [2, 3]}})
    right = request({"outer": {"b": [2, 3], "a": 1}})

    assert SQLiteExecutionAttemptLedger.fingerprint(left) == SQLiteExecutionAttemptLedger.fingerprint(right)


def test_tuple_and_list_share_json_array_identity() -> None:
    left = request({"items": (1, 2, 3)})
    right = request({"items": [1, 2, 3]})

    assert SQLiteExecutionAttemptLedger.fingerprint(left) == SQLiteExecutionAttemptLedger.fingerprint(right)


@pytest.mark.parametrize(
    "parameters",
    [
        {"value": object()},
        {1: "integer-key"},
        {"value": math.nan},
        {"value": math.inf},
        {"value": -math.inf},
    ],
)
def test_non_json_identity_is_rejected(parameters: object) -> None:
    with pytest.raises(AttemptFingerprintError):
        SQLiteExecutionAttemptLedger.fingerprint(request(parameters))


def test_cyclic_identity_is_rejected() -> None:
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    with pytest.raises(AttemptFingerprintError, match="cyclic"):
        SQLiteExecutionAttemptLedger.fingerprint(request(cyclic))


def test_shared_acyclic_value_is_allowed_and_deterministic() -> None:
    shared = {"value": [1, 2, 3]}
    first = request({"left": shared, "right": shared})
    second = request({"right": {"value": [1, 2, 3]}, "left": {"value": [1, 2, 3]}})

    assert SQLiteExecutionAttemptLedger.fingerprint(first) == SQLiteExecutionAttemptLedger.fingerprint(second)


def test_failed_fingerprint_leaves_no_attempt_row(tmp_path) -> None:
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    invalid = request({"value": object()})

    with pytest.raises(AttemptFingerprintError):
        ledger.begin("p", invalid)
    with pytest.raises(KeyError):
        ledger.get(invalid.attempt_id)
