# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence

OUTBOX_SCHEMA_VERSION = 1


class OutboxSchemaVersionError(RuntimeError):
    """Raised when an outbox schema cannot be opened safely."""


class MessageTransport(Protocol):
    def send(self, *, recipient: str, subject: str, body: str, idempotency_key: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class DeliveryReceipt:
    message_id: str
    accepted: bool
    durable: bool


class SQLiteOutbox:
    """Durable outbox recording intent before transport dispatch."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(database), timeout=30.0, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def _migrate(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS rpy_outbox_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = self._connection.execute(
                "SELECT value FROM rpy_outbox_schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            version = 0 if row is None else int(row["value"])
            if version > OUTBOX_SCHEMA_VERSION:
                raise OutboxSchemaVersionError(
                    f"outbox schema {version} is newer than supported schema {OUTBOX_SCHEMA_VERSION}"
                )
            if version < 0:
                raise OutboxSchemaVersionError("outbox schema version cannot be negative")
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS message_outbox (
                    idempotency_key TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    receipt_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            self._connection.execute(
                "INSERT INTO rpy_outbox_schema_metadata(key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(OUTBOX_SCHEMA_VERSION),),
            )
            self._connection.execute("COMMIT")
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM rpy_outbox_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise OutboxSchemaVersionError("outbox schema metadata is missing")
        return int(row["value"])

    def begin(self, request: ExecutionRequest) -> tuple[bool, Mapping[str, Any] | None]:
        fingerprint = self._fingerprint(request)
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute("SELECT * FROM message_outbox WHERE idempotency_key = ?", (request.idempotency_key,)).fetchone()
            if row is not None:
                if row["fingerprint"] != fingerprint:
                    raise ValueError("outbox idempotency conflict")
                self._connection.execute("COMMIT")
                return True, None if row["receipt_json"] is None else json.loads(row["receipt_json"])
            self._connection.execute("INSERT INTO message_outbox(idempotency_key, fingerprint, status) VALUES (?, ?, 'prepared')", (request.idempotency_key, fingerprint))
            self._connection.execute("COMMIT")
            return False, None
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def finish(self, idempotency_key: str, status: str, receipt: Mapping[str, Any] | None) -> None:
        encoded = None if receipt is None else json.dumps(dict(receipt), sort_keys=True, ensure_ascii=False)
        with self._connection:
            self._connection.execute("UPDATE message_outbox SET status = ?, receipt_json = ?, updated_at = CURRENT_TIMESTAMP WHERE idempotency_key = ?", (status, encoded, idempotency_key))

    @staticmethod
    def _fingerprint(request: ExecutionRequest) -> str:
        canonical = json.dumps({"action": request.action, "parameters": dict(request.parameters)}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OutboundMessageExecutor:
    """Transport-neutral outbound-message executor requiring a durable receipt."""

    def __init__(self, transport: MessageTransport, outbox: SQLiteOutbox | None = None) -> None:
        self.transport = transport
        self.outbox = outbox or SQLiteOutbox()

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.action != "send_message":
            return ExecutionResult(ExecutionStatus.FAILED, reason="unsupported_action")
        try:
            replayed, receipt = self.outbox.begin(request)
            if replayed:
                if receipt is None:
                    return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="outbox_prepared_without_receipt")
                return self._from_receipt(receipt)
            recipient = str(request.parameters["recipient"]).strip()
            subject = str(request.parameters.get("subject", ""))
            body = str(request.parameters["body"])
            if not recipient or not body:
                self.outbox.finish(request.idempotency_key, "failed", None)
                return ExecutionResult(ExecutionStatus.FAILED, reason="recipient_and_body_required")
            raw = dict(self.transport.send(recipient=recipient, subject=subject, body=body, idempotency_key=request.idempotency_key))
            message_id = str(raw.get("message_id", "")).strip()
            accepted = bool(raw.get("accepted"))
            durable = bool(raw.get("durable"))
            receipt_value = {"message_id": message_id, "accepted": accepted, "durable": durable}
            self.outbox.finish(request.idempotency_key, "finished", receipt_value)
            return self._from_receipt(receipt_value)
        except (OSError, TimeoutError, ConnectionError) as exc:
            return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=f"message_transport_ambiguous:{type(exc).__name__}")
        except Exception as exc:
            return ExecutionResult(ExecutionStatus.FAILED, reason=f"message_executor_error:{type(exc).__name__}")

    @staticmethod
    def _from_receipt(receipt: Mapping[str, Any]) -> ExecutionResult:
        verified = bool(receipt.get("accepted")) and bool(receipt.get("durable")) and bool(str(receipt.get("message_id", "")).strip())
        readback = ReadbackEvidence(verified, dict(receipt), None if verified else "durable_delivery_receipt_missing")
        return ExecutionResult(ExecutionStatus.SUCCEEDED if verified else ExecutionStatus.WRITE_STATUS_UNKNOWN, {"delivery_receipt": dict(receipt)}, readback, readback.reason)
