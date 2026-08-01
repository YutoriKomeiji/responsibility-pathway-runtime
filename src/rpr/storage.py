# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .evidence import EvidenceEvent
from .models import PathwayDefinition, PathwayState

CURRENT_SCHEMA_VERSION = 1


class IdempotencyConflictError(RuntimeError):
    """Raised when an idempotency key is reused for a different pathway definition."""


class SchemaVersionError(RuntimeError):
    """Raised when a database schema cannot be opened safely by this runtime."""


class SQLiteStore:
    def __init__(self, database: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(database), timeout=30.0, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA busy_timeout = 30000")
        self._migrate()

    def _migrate(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS rpy_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = self._connection.execute(
                "SELECT value FROM rpy_schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            version = 0 if row is None else int(row["value"])
            if version > CURRENT_SCHEMA_VERSION:
                raise SchemaVersionError(
                    f"database schema {version} is newer than supported schema {CURRENT_SCHEMA_VERSION}"
                )
            if version < 0:
                raise SchemaVersionError("database schema version cannot be negative")

            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS pathways (
                    pathway_id TEXT PRIMARY KEY,
                    definition_json TEXT NOT NULL,
                    definition_fingerprint TEXT,
                    state TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS evidence_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    pathway_id TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(pathway_id) REFERENCES pathways(pathway_id)
                )"""
            )
            columns = {str(item["name"]) for item in self._connection.execute("PRAGMA table_info(pathways)")}
            if "definition_fingerprint" not in columns:
                self._connection.execute("ALTER TABLE pathways ADD COLUMN definition_fingerprint TEXT")
            self._connection.execute(
                "INSERT INTO rpy_schema_metadata(key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(CURRENT_SCHEMA_VERSION),),
            )
            self._connection.execute("COMMIT")
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise
        self._backfill_fingerprints()

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM rpy_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise SchemaVersionError("schema metadata is missing")
        return int(row["value"])

    def _backfill_fingerprints(self) -> None:
        rows = self._connection.execute(
            "SELECT pathway_id, definition_json FROM pathways WHERE definition_fingerprint IS NULL OR definition_fingerprint = ''"
        ).fetchall()
        if not rows:
            return
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            for row in rows:
                canonical = self._canonical_json(json.loads(row["definition_json"]))
                fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                self._connection.execute(
                    "UPDATE pathways SET definition_json = ?, definition_fingerprint = ? WHERE pathway_id = ?",
                    (canonical, fingerprint, row["pathway_id"]),
                )
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    @staticmethod
    def _canonical_json(value: dict[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _canonical_definition(cls, definition: PathwayDefinition) -> str:
        return cls._canonical_json(definition.to_dict())

    @classmethod
    def _fingerprint(cls, definition: PathwayDefinition) -> str:
        return hashlib.sha256(cls._canonical_definition(definition).encode("utf-8")).hexdigest()

    def create_or_replay_pathway(self, definition: PathwayDefinition, state: PathwayState, idempotency_key: str) -> tuple[bool, PathwayState]:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        canonical = self._canonical_definition(definition)
        fingerprint = self._fingerprint(definition)
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT pathway_id, definition_fingerprint, state FROM pathways WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if row is not None:
                if row["pathway_id"] != definition.pathway_id or row["definition_fingerprint"] != fingerprint:
                    raise IdempotencyConflictError("idempotency key already belongs to a different pathway request")
                self._connection.execute("COMMIT")
                return True, PathwayState(row["state"])
            self._connection.execute(
                "INSERT INTO pathways(pathway_id, definition_json, definition_fingerprint, state, idempotency_key) VALUES (?, ?, ?, ?, ?)",
                (definition.pathway_id, canonical, fingerprint, state.value, idempotency_key),
            )
            self._connection.execute("COMMIT")
            return False, state
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    def get_definition(self, pathway_id: str) -> PathwayDefinition:
        row = self._connection.execute("SELECT definition_json FROM pathways WHERE pathway_id = ?", (pathway_id,)).fetchone()
        if row is None:
            raise KeyError(pathway_id)
        return PathwayDefinition.from_dict(json.loads(row["definition_json"]))

    def get_state(self, pathway_id: str) -> PathwayState:
        row = self._connection.execute("SELECT state FROM pathways WHERE pathway_id = ?", (pathway_id,)).fetchone()
        if row is None:
            raise KeyError(pathway_id)
        return PathwayState(row["state"])

    def transition_with_event(self, pathway_id: str, expected: PathwayState, target: PathwayState, event: EvidenceEvent) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            result = self._connection.execute(
                "UPDATE pathways SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE pathway_id = ? AND state = ?",
                (target.value, pathway_id, expected.value),
            )
            if result.rowcount != 1:
                row = self._connection.execute("SELECT state FROM pathways WHERE pathway_id = ?", (pathway_id,)).fetchone()
                if row is None:
                    raise KeyError(pathway_id)
                raise RuntimeError(f"concurrent state change: expected {expected.value}, found {row['state']}")
            self._connection.execute(
                "INSERT INTO evidence_events(pathway_id, event_json, event_hash) VALUES (?, ?, ?)",
                (event.pathway_id, json.dumps(event.to_dict(), sort_keys=True, ensure_ascii=False), event.event_hash),
            )
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    def append_event(self, event: EvidenceEvent) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                "INSERT INTO evidence_events(pathway_id, event_json, event_hash) VALUES (?, ?, ?)",
                (event.pathway_id, json.dumps(event.to_dict(), sort_keys=True, ensure_ascii=False), event.event_hash),
            )
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    def latest_event_hash(self, pathway_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT event_hash FROM evidence_events WHERE pathway_id = ? ORDER BY sequence DESC LIMIT 1",
            (pathway_id,),
        ).fetchone()
        return None if row is None else str(row["event_hash"])

    def events(self, pathway_id: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT event_json FROM evidence_events WHERE pathway_id = ? ORDER BY sequence",
            (pathway_id,),
        ).fetchall()
        return [json.loads(row["event_json"]) for row in rows]
