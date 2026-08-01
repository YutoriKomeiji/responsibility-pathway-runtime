# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus

ATTEMPT_SCHEMA_VERSION = 1
MAX_FINGERPRINT_JSON_NESTING = 64
MAX_FINGERPRINT_JSON_NODES = 10_000
MAX_FINGERPRINT_JSON_STRING_BYTES = 1_000_000
MAX_FINGERPRINT_CANONICAL_BYTES = 1_100_000
MAX_FINGERPRINT_PATH_COMPONENT = 64
MAX_RESULT_CANONICAL_BYTES = 1_100_000


class AttemptConflictError(RuntimeError):
    """Raised when an attempt identifier is reused for different execution data."""


class AttemptFingerprintError(ValueError):
    """Raised when execution data cannot form a strict JSON request identity."""


class AttemptResultPersistenceError(ValueError):
    """Raised when an execution result cannot be persisted as strict JSON."""


class AttemptSchemaVersionError(RuntimeError):
    """Raised when an attempt-ledger schema cannot be opened safely."""


@dataclass(frozen=True)
class ExecutionAttemptRecord:
    pathway_id: str
    operation_id: str
    attempt_id: str
    idempotency_key: str
    request_fingerprint: str
    status: str
    result_json: Mapping[str, Any] | None


@dataclass
class _FingerprintBudget:
    nodes: int = 0
    string_bytes: int = 0

    def consume(self, *, path: str, node: bool = True, string_bytes: int = 0) -> None:
        if node:
            self.nodes += 1
            if self.nodes > MAX_FINGERPRINT_JSON_NODES:
                raise AttemptFingerprintError(
                    f"{path} exceeds maximum expanded JSON node count "
                    f"{MAX_FINGERPRINT_JSON_NODES}"
                )
        self.string_bytes += string_bytes
        if self.string_bytes > MAX_FINGERPRINT_JSON_STRING_BYTES:
            raise AttemptFingerprintError(
                f"{path} exceeds maximum aggregate JSON string bytes "
                f"{MAX_FINGERPRINT_JSON_STRING_BYTES}"
            )


def _utf8_size(value: str, *, path: str) -> int:
    try:
        return len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise AttemptFingerprintError(f"{path} contains invalid Unicode") from exc


def _mapping_child_path(path: str, key: str) -> str:
    component = key
    if len(component) > MAX_FINGERPRINT_PATH_COMPONENT:
        component = component[: MAX_FINGERPRINT_PATH_COMPONENT - 1] + "…"
    return f"{path}.{component}"


def _strict_json_identity(
    value: Any,
    *,
    path: str,
    active_containers: set[int] | None = None,
    budget: _FingerprintBudget | None = None,
    depth: int = 0,
) -> Any:
    """Validate bounded strict JSON identity and return a detached plain value."""

    active = active_containers if active_containers is not None else set()
    current_budget = budget if budget is not None else _FingerprintBudget()
    current_budget.consume(path=path)

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        current_budget.consume(path=path, node=False, string_bytes=_utf8_size(value, path=path))
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AttemptFingerprintError(f"{path} contains a non-finite JSON number")
        return value

    if isinstance(value, Mapping) or isinstance(value, (list, tuple)):
        if depth >= MAX_FINGERPRINT_JSON_NESTING:
            raise AttemptFingerprintError(
                f"{path} exceeds maximum JSON nesting {MAX_FINGERPRINT_JSON_NESTING}"
            )
        container_id = id(value)
        if container_id in active:
            raise AttemptFingerprintError(f"{path} contains a cyclic JSON container")
        active.add(container_id)
        try:
            if isinstance(value, Mapping):
                result: dict[str, Any] = {}
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise AttemptFingerprintError(f"{path} contains a non-string object key")
                    current_budget.consume(
                        path=path,
                        node=False,
                        string_bytes=_utf8_size(key, path=path),
                    )
                    child_path = _mapping_child_path(path, key)
                    result[key] = _strict_json_identity(
                        item,
                        path=child_path,
                        active_containers=active,
                        budget=current_budget,
                        depth=depth + 1,
                    )
                return result
            return [
                _strict_json_identity(
                    item,
                    path=f"{path}[{index}]",
                    active_containers=active,
                    budget=current_budget,
                    depth=depth + 1,
                )
                for index, item in enumerate(value)
            ]
        finally:
            active.remove(container_id)

    raise AttemptFingerprintError(
        f"{path} contains a non-JSON value of type {type(value).__name__}"
    )


def _strict_result_json(result: ExecutionResult) -> bytes:
    value = {
        "status": result.status.value,
        "evidence": result.evidence,
        "readback": None
        if result.readback is None
        else {
            "verified": result.readback.verified,
            "observed": result.readback.observed,
            "reason": result.readback.reason,
        },
        "reason": result.reason,
    }
    try:
        detached = _strict_json_identity(value, path="result")
        encoded = json.dumps(
            detached,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except AttemptFingerprintError as exc:
        raise AttemptResultPersistenceError(str(exc)) from exc
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise AttemptResultPersistenceError(
            "execution result cannot be canonically serialized as JSON"
        ) from exc
    if len(encoded) > MAX_RESULT_CANONICAL_BYTES:
        raise AttemptResultPersistenceError(
            f"execution result exceeds maximum canonical JSON bytes {MAX_RESULT_CANONICAL_BYTES}"
        )
    return encoded


class SQLiteExecutionAttemptLedger:
    """Persistent execution-attempt ledger with replay conflict detection."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(database), timeout=30.0, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA busy_timeout = 30000")
        self._migrate()

    def _migrate(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS rpy_attempt_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = self._connection.execute(
                "SELECT value FROM rpy_attempt_schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            version = 0 if row is None else int(row["value"])
            if version > ATTEMPT_SCHEMA_VERSION:
                raise AttemptSchemaVersionError(
                    f"attempt schema {version} is newer than supported schema {ATTEMPT_SCHEMA_VERSION}"
                )
            if version < 0:
                raise AttemptSchemaVersionError("attempt schema version cannot be negative")
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS execution_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    pathway_id TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            self._connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS execution_attempt_idempotency ON execution_attempts(pathway_id, idempotency_key)"
            )
            self._connection.execute(
                "INSERT INTO rpy_attempt_schema_metadata(key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(ATTEMPT_SCHEMA_VERSION),),
            )
            self._connection.execute("COMMIT")
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM rpy_attempt_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise AttemptSchemaVersionError("attempt schema metadata is missing")
        return int(row["value"])

    @staticmethod
    def fingerprint(request: ExecutionRequest) -> str:
        identity = _strict_json_identity(
            {
                "operation_id": request.operation_id,
                "action": request.action,
                "parameters": request.parameters,
            },
            path="request",
        )
        try:
            canonical_bytes = json.dumps(
                identity,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
            raise AttemptFingerprintError("request cannot be canonically serialized as JSON") from exc
        if len(canonical_bytes) > MAX_FINGERPRINT_CANONICAL_BYTES:
            raise AttemptFingerprintError(
                "request exceeds maximum canonical JSON bytes "
                f"{MAX_FINGERPRINT_CANONICAL_BYTES}"
            )
        return hashlib.sha256(canonical_bytes).hexdigest()

    def begin(self, pathway_id: str, request: ExecutionRequest) -> tuple[bool, ExecutionAttemptRecord]:
        fingerprint = self.fingerprint(request)
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT * FROM execution_attempts WHERE attempt_id = ? OR (pathway_id = ? AND idempotency_key = ?)",
                (request.attempt_id, pathway_id, request.idempotency_key),
            ).fetchone()
            if row is not None:
                record = self._record(row)
                if (
                    record.pathway_id != pathway_id
                    or record.operation_id != request.operation_id
                    or record.request_fingerprint != fingerprint
                ):
                    raise AttemptConflictError("attempt or idempotency key belongs to different execution data")
                self._connection.execute("COMMIT")
                return True, record
            self._connection.execute(
                "INSERT INTO execution_attempts(pathway_id, operation_id, attempt_id, idempotency_key, request_fingerprint, status) VALUES (?, ?, ?, ?, ?, ?)",
                (pathway_id, request.operation_id, request.attempt_id, request.idempotency_key, fingerprint, "started"),
            )
            self._connection.execute("COMMIT")
            return False, ExecutionAttemptRecord(pathway_id, request.operation_id, request.attempt_id, request.idempotency_key, fingerprint, "started", None)
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def finish(self, attempt_id: str, result: ExecutionResult) -> ExecutionAttemptRecord:
        encoded = _strict_result_json(result).decode("utf-8")
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            changed = self._connection.execute(
                "UPDATE execution_attempts SET status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP WHERE attempt_id = ?",
                (result.status.value, encoded, attempt_id),
            )
            if changed.rowcount != 1:
                raise KeyError(attempt_id)
            row = self._connection.execute("SELECT * FROM execution_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
            self._connection.execute("COMMIT")
            return self._record(row)
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def mark_result_persistence_unknown(
        self,
        attempt_id: str,
        *,
        reason: str,
    ) -> ExecutionAttemptRecord:
        fallback = json.dumps(
            {
                "status": ExecutionStatus.WRITE_STATUS_UNKNOWN.value,
                "evidence": {},
                "readback": None,
                "reason": reason,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            changed = self._connection.execute(
                "UPDATE execution_attempts SET status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP WHERE attempt_id = ?",
                (ExecutionStatus.WRITE_STATUS_UNKNOWN.value, fallback, attempt_id),
            )
            if changed.rowcount != 1:
                raise KeyError(attempt_id)
            row = self._connection.execute(
                "SELECT * FROM execution_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            self._connection.execute("COMMIT")
            return self._record(row)
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def discard_started(self, attempt_id: str) -> bool:
        """Remove a pre-dispatch attempt that never reached an external executor.

        Only a row still marked ``started`` with no persisted result is eligible.
        Finished or otherwise classified attempts are retained for replay safety.
        """
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            changed = self._connection.execute(
                "DELETE FROM execution_attempts WHERE attempt_id = ? AND status = 'started' AND result_json IS NULL",
                (attempt_id,),
            )
            self._connection.execute("COMMIT")
            return changed.rowcount == 1
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def get(self, attempt_id: str) -> ExecutionAttemptRecord:
        row = self._connection.execute("SELECT * FROM execution_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
        if row is None:
            raise KeyError(attempt_id)
        return self._record(row)

    @staticmethod
    def _record(row: sqlite3.Row) -> ExecutionAttemptRecord:
        return ExecutionAttemptRecord(
            pathway_id=str(row["pathway_id"]),
            operation_id=str(row["operation_id"]),
            attempt_id=str(row["attempt_id"]),
            idempotency_key=str(row["idempotency_key"]),
            request_fingerprint=str(row["request_fingerprint"]),
            status=str(row["status"]),
            result_json=None if row["result_json"] is None else json.loads(row["result_json"]),
        )
