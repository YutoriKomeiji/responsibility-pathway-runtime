# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json

import pytest

from rpr.executor import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ReadbackEvidence,
)
from rpr.mcp_retained_evidence import (
    McpDiagnosticsEvidence,
    McpRetainedEvidence,
    McpRetainedEvidenceError,
    build_mcp_retained_evidence,
)
from rpr.mcp_subprocess_lifecycle import McpProcessExit


def request(*, parameters: dict[str, object] | None = None) -> ExecutionRequest:
    return ExecutionRequest(
        operation_id="op-1",
        attempt_id="attempt-1",
        idempotency_key="private-idempotency-value",
        action="mcp_tool_call",
        parameters=parameters
        or {
            "mcp": {
                "protocol_version": "2025-11-25",
                "server_name": "local-helper",
                "server_version": "1.0.0",
                "server_capabilities_sha256": "a" * 64,
                "tool_name": "replace_record",
                "tool_schema_sha256": "b" * 64,
            },
            "arguments": {"record_id": "r-1"},
        },
    )


def test_build_round_trip_and_hash_verification() -> None:
    result = ExecutionResult(
        ExecutionStatus.SUCCEEDED,
        {"dispatch_state": "sent", "tool_result": {"content_count": 1}},
        ReadbackEvidence(True, {"record_id": "r-1", "version": 2}),
    )

    evidence = build_mcp_retained_evidence(
        request(),
        result,
        process_exit=McpProcessExit(0, True, False, False),
        diagnostics=McpDiagnosticsEvidence(bytes_retained=18, truncated=False),
        residual_boundary="single-node local stdio helper; no external server claim",
    )

    restored = McpRetainedEvidence.from_json(evidence.to_json())
    assert restored == evidence
    assert restored.payload["schema"] == "rpr.mcp.retained-evidence.v1"
    assert restored.payload["execution"] == {
        "status": "succeeded",
        "dispatch_state": "sent",
        "reason": None,
        "readback": {
            "verified": True,
            "observed": {"record_id": "r-1", "version": 2},
            "reason": None,
        },
    }
    operation = restored.payload["operation"]
    assert operation["operation_id"] == "op-1"
    assert operation["attempt_id"] == "attempt-1"
    assert operation["idempotency_key_sha256"] != "private-idempotency-value"
    assert "private-idempotency-value" not in restored.to_json()


def test_hash_changes_when_payload_is_tampered() -> None:
    evidence = build_mcp_retained_evidence(
        request(),
        ExecutionResult(ExecutionStatus.FAILED, {"dispatch_state": "not_sent"}),
        residual_boundary="request proved not sent",
    )
    envelope = json.loads(evidence.to_json())
    envelope["payload"]["execution"]["dispatch_state"] = "sent"

    with pytest.raises(McpRetainedEvidenceError, match="hash mismatch"):
        McpRetainedEvidence.from_json(json.dumps(envelope))


def test_unknown_outcome_is_retained_without_claiming_success() -> None:
    evidence = build_mcp_retained_evidence(
        request(),
        ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            {"dispatch_state": "possibly_sent"},
            reason="TimeoutError: response deadline exceeded",
        ),
        process_exit=McpProcessExit(-15, False, True, False),
        diagnostics=McpDiagnosticsEvidence(bytes_retained=65536, truncated=True),
        residual_boundary="write may have occurred; reconciliation required",
    )

    assert evidence.payload["execution"]["status"] == "write_status_unknown"
    assert evidence.payload["execution"]["dispatch_state"] == "possibly_sent"
    assert evidence.payload["diagnostics"] == {
        "bytes_retained": 65536,
        "truncated": True,
    }
    assert evidence.payload["process_exit"]["terminated"] is True


@pytest.mark.parametrize("dispatch_state", [None, "", "queued", 1, True])
def test_invalid_dispatch_state_is_rejected(dispatch_state: object) -> None:
    with pytest.raises(McpRetainedEvidenceError, match="dispatch_state"):
        build_mcp_retained_evidence(
            request(),
            ExecutionResult(ExecutionStatus.FAILED, {"dispatch_state": dispatch_state}),
            residual_boundary="invalid test input",
        )


def test_missing_admission_binding_is_rejected() -> None:
    with pytest.raises(McpRetainedEvidenceError, match="admission binding"):
        build_mcp_retained_evidence(
            request(parameters={"arguments": {}}),
            ExecutionResult(ExecutionStatus.FAILED, {"dispatch_state": "not_sent"}),
            residual_boundary="missing admission",
        )


@pytest.mark.parametrize(
    "observed",
    [
        {"api_token": "must-not-be-retained"},
        {"nested": {"password": "must-not-be-retained"}},
        {"value": float("nan")},
        {1: "non-string-key"},
        {"value": {1, 2}},
    ],
)
def test_unsafe_or_non_json_readback_is_rejected(observed: object) -> None:
    with pytest.raises(McpRetainedEvidenceError):
        build_mcp_retained_evidence(
            request(),
            ExecutionResult(
                ExecutionStatus.SUCCEEDED,
                {"dispatch_state": "sent"},
                ReadbackEvidence(True, observed),  # type: ignore[arg-type]
            ),
            residual_boundary="unsafe input must fail closed",
        )


def test_raw_diagnostics_text_has_no_field_in_schema() -> None:
    evidence = build_mcp_retained_evidence(
        request(),
        ExecutionResult(ExecutionStatus.FAILED, {"dispatch_state": "sent"}),
        diagnostics=McpDiagnosticsEvidence(12, False),
        residual_boundary="diagnostics content intentionally excluded",
    )

    serialized = evidence.to_json()
    assert "stderr" not in serialized
    assert "diagnostic body" not in serialized


def test_wrong_action_and_empty_boundary_are_rejected() -> None:
    non_mcp = ExecutionRequest("op", "attempt", "key", "replace_text_file", {})
    result = ExecutionResult(ExecutionStatus.FAILED, {"dispatch_state": "not_sent"})

    with pytest.raises(McpRetainedEvidenceError, match="not an MCP tool call"):
        build_mcp_retained_evidence(non_mcp, result, residual_boundary="local")
    with pytest.raises(McpRetainedEvidenceError, match="residual_boundary"):
        build_mcp_retained_evidence(request(), result, residual_boundary="  ")
