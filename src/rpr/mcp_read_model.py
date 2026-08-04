# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import PathwayState


_TERMINAL_STATES = frozenset(
    {
        PathwayState.COMPLETED.value,
        PathwayState.DENIED.value,
        PathwayState.ABORTED.value,
    }
)


class ReadOnlyDatabaseError(RuntimeError):
    """Raised when an RPR database cannot be inspected safely in read-only mode."""


class SQLiteReadModel:
    """Read RPR pathway and evidence state without opening a write-capable connection."""

    def __init__(self, database: str | Path) -> None:
        path = Path(database).expanduser().resolve()
        if not path.is_file():
            raise ReadOnlyDatabaseError("database file does not exist")
        uri = f"file:{path.as_posix()}?mode=ro"
        try:
            self._connection = sqlite3.connect(uri, uri=True, timeout=5.0)
            self._connection.row_factory = sqlite3.Row
            self._validate_schema()
        except (sqlite3.Error, ValueError) as exc:
            raise ReadOnlyDatabaseError(f"cannot open RPR database read-only: {exc}") from exc

    def close(self) -> None:
        self._connection.close()

    def _validate_schema(self) -> None:
        required = {"rpy_schema_metadata", "pathways", "evidence_events"}
        rows = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        available = {str(row["name"]) for row in rows}
        missing = sorted(required - available)
        if missing:
            raise ReadOnlyDatabaseError(
                f"database is missing required RPR tables: {', '.join(missing)}"
            )

    def status(self) -> dict[str, Any]:
        schema_row = self._connection.execute(
            "SELECT value FROM rpy_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if schema_row is None:
            raise ReadOnlyDatabaseError("schema metadata is missing")
        pathway_count = int(
            self._connection.execute("SELECT COUNT(*) AS count FROM pathways").fetchone()["count"]
        )
        unresolved_count = int(
            self._connection.execute(
                "SELECT COUNT(*) AS count FROM pathways WHERE state NOT IN (?, ?, ?)",
                tuple(sorted(_TERMINAL_STATES)),
            ).fetchone()["count"]
        )
        return {
            "mode": "read_only",
            "schema_version": int(schema_row["value"]),
            "pathway_count": pathway_count,
            "unresolved_count": unresolved_count,
        }

    def list_pathways(self, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = _validated_limit(limit)
        rows = self._connection.execute(
            """SELECT pathway_id, definition_json, state, created_at, updated_at
               FROM pathways ORDER BY created_at, pathway_id LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._pathway_row(row) for row in rows]

    def list_unresolved(self, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = _validated_limit(limit)
        rows = self._connection.execute(
            """SELECT pathway_id, definition_json, state, created_at, updated_at
               FROM pathways WHERE state NOT IN (?, ?, ?)
               ORDER BY updated_at, pathway_id LIMIT ?""",
            (*tuple(sorted(_TERMINAL_STATES)), limit),
        ).fetchall()
        return [self._pathway_row(row) for row in rows]

    def get_pathway(self, pathway_id: str) -> dict[str, Any]:
        pathway_id = _required_id(pathway_id)
        row = self._connection.execute(
            """SELECT pathway_id, definition_json, state, created_at, updated_at
               FROM pathways WHERE pathway_id = ?""",
            (pathway_id,),
        ).fetchone()
        if row is None:
            raise KeyError(pathway_id)
        return self._pathway_row(row)

    def get_evidence(self, pathway_id: str, *, limit: int = 500) -> list[dict[str, Any]]:
        pathway_id = _required_id(pathway_id)
        limit = _validated_limit(limit, maximum=5000)
        if self._connection.execute(
            "SELECT 1 FROM pathways WHERE pathway_id = ?", (pathway_id,)
        ).fetchone() is None:
            raise KeyError(pathway_id)
        rows = self._connection.execute(
            """SELECT sequence, event_json, event_hash FROM evidence_events
               WHERE pathway_id = ? ORDER BY sequence LIMIT ?""",
            (pathway_id, limit),
        ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            event = json.loads(row["event_json"])
            result.append(
                {
                    "sequence": int(row["sequence"]),
                    "event_hash": str(row["event_hash"]),
                    "event": event,
                }
            )
        return result

    @staticmethod
    def _pathway_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "pathway_id": str(row["pathway_id"]),
            "state": str(row["state"]),
            "definition": json.loads(row["definition_json"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }


def _required_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("pathway_id must be a non-empty trimmed string")
    return value


def _validated_limit(value: object, *, maximum: int = 1000) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("limit must be an integer")
    if value < 1 or value > maximum:
        raise ValueError(f"limit must be between 1 and {maximum}")
    return value
