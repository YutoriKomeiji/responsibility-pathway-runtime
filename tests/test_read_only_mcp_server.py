# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import io
import json
import sqlite3

import pytest

from rpr.evidence import build_event
from rpr.mcp_read_model import ReadOnlyDatabaseError, SQLiteReadModel
from rpr.mcp_server import JsonRpcError, ReadOnlyRprMcpServer, run_stdio
from rpr.mcp_stable_snapshot import STABLE_PROTOCOL_VERSION
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.storage import SQLiteStore


def _definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="inspect_record",
        action_class=ActionClass.OBSERVE_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="observer",
        stop_authority="operator",
        evidence_owner="auditor",
        repair_owner="repairer",
        resume_authority="resumer",
        human_return_point="operator_console",
        residual_owner="owner",
        metadata={"source": "test"},
    )


def _database(tmp_path):
    database = tmp_path / "rpr.sqlite3"
    store = SQLiteStore(database)
    pending = _definition("p-pending")
    completed = _definition("p-completed")
    store.create_or_replay_pathway(pending, PathwayState.HUMAN_GATE, "idem-pending")
    store.create_or_replay_pathway(completed, PathwayState.COMPLETED, "idem-completed")
    event = build_event(
        pathway_id=pending.pathway_id,
        event_type="pathway_registered",
        actor="owner",
        payload={"state": PathwayState.HUMAN_GATE.value},
        previous_hash=None,
    )
    store.append_event(event)
    return database


def _server(tmp_path):
    read_model = SQLiteReadModel(_database(tmp_path))
    return read_model, ReadOnlyRprMcpServer(read_model)


def _initialize(server: ReadOnlyRprMcpServer) -> None:
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": STABLE_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1"},
            },
        }
    )
    assert response is not None
    assert response["result"]["protocolVersion"] == STABLE_PROTOCOL_VERSION
    assert server.handle(
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    ) is None


def test_read_model_is_read_only_and_does_not_disclose_database_path(tmp_path):
    database = _database(tmp_path)
    read_model = SQLiteReadModel(database)
    try:
        status = read_model.status()
        assert status == {
            "mode": "read_only",
            "schema_version": 1,
            "pathway_count": 2,
            "unresolved_count": 1,
        }
        assert str(database) not in json.dumps(status)
        with pytest.raises(sqlite3.OperationalError):
            read_model._connection.execute(
                "UPDATE pathways SET state = 'completed' WHERE pathway_id = 'p-pending'"
            )
    finally:
        read_model.close()


def test_read_model_lists_pathways_unresolved_and_evidence(tmp_path):
    read_model = SQLiteReadModel(_database(tmp_path))
    try:
        pathways = read_model.list_pathways()
        assert [item["pathway_id"] for item in pathways] == ["p-completed", "p-pending"]
        unresolved = read_model.list_unresolved()
        assert [item["pathway_id"] for item in unresolved] == ["p-pending"]
        pathway = read_model.get_pathway("p-pending")
        assert pathway["state"] == PathwayState.HUMAN_GATE.value
        assert pathway["definition"]["metadata"] == {"source": "test"}
        events = read_model.get_evidence("p-pending")
        assert len(events) == 1
        assert events[0]["event"]["event_type"] == "pathway_registered"
    finally:
        read_model.close()


def test_server_requires_initialize_before_initialized_notification(tmp_path):
    read_model, server = _server(tmp_path)
    try:
        with pytest.raises(JsonRpcError) as captured:
            server.handle(
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            )
        assert captured.value.code == -32002
        assert server.initialized is False
    finally:
        read_model.close()


def test_server_exposes_only_read_only_tools(tmp_path):
    read_model, server = _server(tmp_path)
    try:
        _initialize(server)
        response = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        assert response is not None
        names = [tool["name"] for tool in response["result"]["tools"]]
        assert names == [
            "rpr.get_status",
            "rpr.list_pathways",
            "rpr.get_pathway",
            "rpr.get_evidence",
            "rpr.list_unresolved",
        ]
        assert not any(
            fragment in name
            for name in names
            for fragment in ("approve", "execute", "reconcile", "resume", "transition", "write")
        )
    finally:
        read_model.close()


def test_server_returns_structured_results_and_tool_errors(tmp_path):
    read_model, server = _server(tmp_path)
    try:
        _initialize(server)
        status = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "rpr.get_status"},
            }
        )
        assert status is not None
        assert status["result"]["structuredContent"]["mode"] == "read_only"

        missing = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "rpr.get_pathway",
                    "arguments": {"pathway_id": "missing"},
                },
            }
        )
        assert missing is not None
        assert missing["result"]["isError"] is True
        assert missing["result"]["structuredContent"]["error"] == "pathway_not_found"

        invalid = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "rpr.list_pathways",
                    "arguments": {"limit": True},
                },
            }
        )
        assert invalid is not None
        assert invalid["result"]["isError"] is True
        assert invalid["result"]["structuredContent"]["error"] == "invalid_request"
    finally:
        read_model.close()


def test_stdio_emits_only_json_rpc_messages_and_suppresses_notification_errors(tmp_path):
    read_model, server = _server(tmp_path)
    stdin = io.StringIO(
        "not-json\n"
        + json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/unknown", "params": {}}
        )
        + "\n"
        + json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": STABLE_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1"},
                },
            }
        )
        + "\n"
        + json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        )
        + "\n"
        + json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "rpr.list_unresolved", "arguments": {}},
            }
        )
        + "\n"
    )
    stdout = io.StringIO()
    try:
        assert run_stdio(server, stdin=stdin, stdout=stdout) == 0
        messages = [json.loads(line) for line in stdout.getvalue().splitlines()]
        assert len(messages) == 3
        assert messages[0]["error"]["code"] == -32700
        assert messages[1]["result"]["serverInfo"]["name"] == "responsibility-pathway-runtime"
        assert messages[2]["result"]["structuredContent"]["pathways"][0]["pathway_id"] == "p-pending"
    finally:
        read_model.close()


def test_read_model_rejects_missing_or_non_rpr_database(tmp_path):
    with pytest.raises(ReadOnlyDatabaseError, match="database file does not exist"):
        SQLiteReadModel(tmp_path / "missing.sqlite3")

    empty = tmp_path / "empty.sqlite3"
    sqlite3.connect(empty).close()
    with pytest.raises(ReadOnlyDatabaseError, match="missing required RPR tables"):
        SQLiteReadModel(empty)
