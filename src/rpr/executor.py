# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    WRITE_STATUS_UNKNOWN = "write_status_unknown"


@dataclass(frozen=True)
class ExecutionRequest:
    operation_id: str
    attempt_id: str
    idempotency_key: str
    action: str
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("operation_id", "attempt_id", "idempotency_key", "action"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class ReadbackEvidence:
    verified: bool
    observed: Mapping[str, Any] = field(default_factory=dict)
    reason: str | None = None


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    evidence: Mapping[str, Any] = field(default_factory=dict)
    readback: ReadbackEvidence | None = None
    reason: str | None = None


class Executor(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...


class LocalFileExecutor:
    """Root-confined atomic UTF-8 file replacement with mandatory readback."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._results: dict[str, tuple[str, ExecutionResult]] = {}

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        fingerprint = self._fingerprint(request)
        replay = self._results.get(request.idempotency_key)
        if replay is not None:
            if replay[0] != fingerprint:
                return ExecutionResult(ExecutionStatus.FAILED, reason="idempotency_conflict")
            return replay[1]
        if request.action != "replace_text_file":
            return ExecutionResult(ExecutionStatus.FAILED, reason="unsupported_action")
        try:
            target = self._resolve(str(request.parameters["path"]))
            content = str(request.parameters["content"])
            expected_sha256 = request.parameters.get("expected_sha256")
            if expected_sha256 is not None and target.exists():
                current = hashlib.sha256(target.read_bytes()).hexdigest()
                if current != str(expected_sha256):
                    return ExecutionResult(ExecutionStatus.FAILED, {"current_sha256": current}, reason="precondition_failed")
            target.parent.mkdir(parents=True, exist_ok=True)
            encoded = content.encode("utf-8")
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                temp_name = handle.name
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
            observed = target.read_bytes()
            expected = hashlib.sha256(encoded).hexdigest()
            actual = hashlib.sha256(observed).hexdigest()
            readback = ReadbackEvidence(expected == actual, {"path": str(target.relative_to(self.root)), "sha256": actual, "size": len(observed)}, None if expected == actual else "readback_hash_mismatch")
            result = ExecutionResult(ExecutionStatus.SUCCEEDED if readback.verified else ExecutionStatus.WRITE_STATUS_UNKNOWN, {"expected_sha256": expected}, readback)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=f"{type(exc).__name__}: {exc}")
        self._results[request.idempotency_key] = (fingerprint, result)
        return result

    def _resolve(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("path escapes executor root")
        if candidate == self.root:
            raise ValueError("target must be a file below executor root")
        return candidate

    @staticmethod
    def _fingerprint(request: ExecutionRequest) -> str:
        canonical = repr((request.operation_id, request.action, sorted((str(k), repr(v)) for k, v in request.parameters.items())))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
