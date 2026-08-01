# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .executor import ExecutionRequest, ExecutionResult
from .mcp_subprocess_lifecycle import McpProcessExit


class McpRetainedEvidenceError(ValueError):
    """Raised when retained evidence cannot be represented safely."""


_FORBIDDEN_KEY_FRAGMENTS = (
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
)


def _strict_json(value: Any, *, path: str = "$") -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise McpRetainedEvidenceError(f"non-finite number at {path}")
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise McpRetainedEvidenceError(f"non-string object key at {path}")
            normalized = key.casefold().replace("-", "_")
            if any(fragment in normalized for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                raise McpRetainedEvidenceError(
                    f"potential credential-bearing key is forbidden at {path}.{key}"
                )
            result[key] = _strict_json(item, path=f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_strict_json(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    raise McpRetainedEvidenceError(
        f"unsupported JSON value at {path}: {type(value).__name__}"
    )


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise McpRetainedEvidenceError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class McpDiagnosticsEvidence:
    bytes_retained: int
    truncated: bool

    def __post_init__(self) -> None:
        if isinstance(self.bytes_retained, bool) or not isinstance(self.bytes_retained, int):
            raise McpRetainedEvidenceError("bytes_retained must be an integer")
        if self.bytes_retained < 0:
            raise McpRetainedEvidenceError("bytes_retained must be non-negative")
        if not isinstance(self.truncated, bool):
            raise McpRetainedEvidenceError("truncated must be a boolean")


@dataclass(frozen=True)
class McpRetainedEvidence:
    payload: Mapping[str, Any]
    sha256: str

    def __post_init__(self) -> None:
        normalized = _strict_json(self.payload)
        expected = _hash_payload(normalized)
        if self.sha256 != expected:
            raise McpRetainedEvidenceError("retained evidence hash mismatch")
        object.__setattr__(self, "payload", normalized)

    def to_json(self) -> str:
        envelope = {"payload": self.payload, "sha256": self.sha256}
        return json.dumps(envelope, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "McpRetainedEvidence":
        try:
            envelope = json.loads(value, parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
        except (json.JSONDecodeError, ValueError) as exc:
            raise McpRetainedEvidenceError(f"invalid retained evidence JSON: {exc}") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "sha256"}:
            raise McpRetainedEvidenceError("retained evidence envelope shape mismatch")
        return cls(envelope["payload"], _required_text(envelope["sha256"], "sha256"))


def build_mcp_retained_evidence(
    request: ExecutionRequest,
    result: ExecutionResult,
    *,
    process_exit: McpProcessExit | None = None,
    diagnostics: McpDiagnosticsEvidence | None = None,
    residual_boundary: str,
) -> McpRetainedEvidence:
    if request.action != "mcp_tool_call":
        raise McpRetainedEvidenceError("request is not an MCP tool call")

    mcp = request.parameters.get("mcp")
    if not isinstance(mcp, Mapping):
        raise McpRetainedEvidenceError("missing MCP admission binding")

    admission_keys = (
        "protocol_version",
        "server_name",
        "server_version",
        "server_capabilities_sha256",
        "tool_name",
        "tool_schema_sha256",
    )
    admission: dict[str, str] = {}
    for key in admission_keys:
        admission[key] = _required_text(mcp.get(key), f"mcp.{key}")

    execution_evidence = _strict_json(result.evidence, path="$.execution.evidence")
    dispatch_state = execution_evidence.get("dispatch_state")
    if dispatch_state not in {"not_sent", "possibly_sent", "unknown", "sent"}:
        raise McpRetainedEvidenceError("execution evidence has invalid dispatch_state")

    readback: dict[str, Any] | None = None
    if result.readback is not None:
        readback = {
            "verified": result.readback.verified,
            "observed": _strict_json(result.readback.observed, path="$.execution.readback.observed"),
            "reason": result.readback.reason,
        }

    process: dict[str, Any] | None = None
    if process_exit is not None:
        process = {
            "exit_code": process_exit.exit_code,
            "graceful": process_exit.graceful,
            "terminated": process_exit.terminated,
            "killed": process_exit.killed,
        }

    diagnostic_value: dict[str, Any] | None = None
    if diagnostics is not None:
        diagnostic_value = {
            "bytes_retained": diagnostics.bytes_retained,
            "truncated": diagnostics.truncated,
        }

    payload = _strict_json(
        {
            "schema": "rpr.mcp.retained-evidence.v1",
            "operation": {
                "operation_id": request.operation_id,
                "attempt_id": request.attempt_id,
                "idempotency_key_sha256": hashlib.sha256(
                    request.idempotency_key.encode("utf-8")
                ).hexdigest(),
            },
            "admission": admission,
            "execution": {
                "status": str(result.status),
                "dispatch_state": dispatch_state,
                "reason": result.reason,
                "readback": readback,
            },
            "process_exit": process,
            "diagnostics": diagnostic_value,
            "residual_boundary": _required_text(residual_boundary, "residual_boundary"),
        }
    )
    return McpRetainedEvidence(payload, _hash_payload(payload))


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
