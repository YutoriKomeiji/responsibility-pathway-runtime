# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import json
import sqlite3
from pathlib import Path

import pytest

from rpr.models import PathwayState
from rpr.storage import CURRENT_SCHEMA_VERSION, SQLiteStore, SchemaVersionError


def _legacy_definition() -> dict[str, object]:
    return {
        "pathway_id": "legacy-path",
        "action_name": "replace_text_file",
        "action_class": "approval_required",
        "environment_trust": "trusted_internal",
        "decision_owner": "owner",
        "approval_authority": "approver",
        "execution_actor": "executor",
        "stop_authority": "stopper",
        "evidence_owner": "evidence",
        "repair_owner": "repair",
        "resume_authority": "resume",
        "human_return_point": "human",
        "residual_owner": "residual",
        "metadata": {},
    }


def test_legacy_database_without_metadata_is_migrated_and_preserved(tmp_path: Path) -> None:
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE pathways (
            pathway_id TEXT PRIMARY KEY,
            definition_json TEXT NOT NULL,
            state TEXT NOT NULL,
            idempotency_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE evidence_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            pathway_id TEXT NOT NULL,
            event_json TEXT NOT NULL,
            event_hash TEXT NOT NULL UNIQUE
        );
        """
    )
    connection.execute(
        "INSERT INTO pathways(pathway_id, definition_json, state, idempotency_key) VALUES (?, ?, ?, ?)",
        ("legacy-path", json.dumps(_legacy_definition()), PathwayState.AWAITING_APPROVAL.value, "legacy-key"),
    )
    connection.commit()
    connection.close()

    store = SQLiteStore(database)

    assert store.schema_version == CURRENT_SCHEMA_VERSION
    assert store.get_state("legacy-path") is PathwayState.AWAITING_APPROVAL
    assert store.get_definition("legacy-path").residual_owner == "residual"


def test_unknown_future_schema_fails_closed(tmp_path: Path) -> None:
    database = tmp_path / "future.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE rpy_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute(
        "INSERT INTO rpy_schema_metadata(key, value) VALUES ('schema_version', ?)",
        (str(CURRENT_SCHEMA_VERSION + 1),),
    )
    connection.commit()
    connection.close()

    with pytest.raises(SchemaVersionError, match="newer than supported"):
        SQLiteStore(database)
