# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import sqlite3
from pathlib import Path

import pytest

from rpr.attempts import ATTEMPT_SCHEMA_VERSION, AttemptSchemaVersionError, SQLiteExecutionAttemptLedger
from rpr.message_executor import OUTBOX_SCHEMA_VERSION, OutboxSchemaVersionError, SQLiteOutbox
from rpr.tenant import TENANT_SCHEMA_VERSION, SQLiteTenantRegistry, TenantSchemaVersionError


def _future_database(path: Path, table: str, version: int) -> None:
    connection = sqlite3.connect(path)
    connection.execute(f"CREATE TABLE {table} (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute(f"INSERT INTO {table}(key, value) VALUES ('schema_version', ?)", (str(version),))
    connection.commit()
    connection.close()


def test_legacy_attempt_ledger_gains_schema_metadata(tmp_path: Path) -> None:
    database = tmp_path / "attempts.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE execution_attempts (
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
    connection.commit()
    connection.close()
    ledger = SQLiteExecutionAttemptLedger(database)
    assert ledger.schema_version == ATTEMPT_SCHEMA_VERSION


def test_legacy_outbox_gains_schema_metadata(tmp_path: Path) -> None:
    database = tmp_path / "outbox.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE message_outbox (
            idempotency_key TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            receipt_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    connection.commit()
    connection.close()
    outbox = SQLiteOutbox(database)
    assert outbox.schema_version == OUTBOX_SCHEMA_VERSION


def test_legacy_tenant_registry_gains_schema_metadata(tmp_path: Path) -> None:
    database = tmp_path / "tenants.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE tenant_pathways (pathway_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    connection.commit()
    connection.close()
    registry = SQLiteTenantRegistry(database)
    assert registry.schema_version == TENANT_SCHEMA_VERSION


@pytest.mark.parametrize(
    ("filename", "table", "version", "factory", "error"),
    [
        ("future-attempt.sqlite3", "rpy_attempt_schema_metadata", ATTEMPT_SCHEMA_VERSION + 1, SQLiteExecutionAttemptLedger, AttemptSchemaVersionError),
        ("future-outbox.sqlite3", "rpy_outbox_schema_metadata", OUTBOX_SCHEMA_VERSION + 1, SQLiteOutbox, OutboxSchemaVersionError),
        ("future-tenant.sqlite3", "rpy_tenant_schema_metadata", TENANT_SCHEMA_VERSION + 1, SQLiteTenantRegistry, TenantSchemaVersionError),
    ],
)
def test_future_registry_schema_fails_closed(
    tmp_path: Path,
    filename: str,
    table: str,
    version: int,
    factory: object,
    error: type[Exception],
) -> None:
    database = tmp_path / filename
    _future_database(database, table, version)
    with pytest.raises(error, match="newer than supported"):
        factory(database)  # type: ignore[operator]
