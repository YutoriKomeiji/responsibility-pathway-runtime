# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from rpr.evidence import build_event
from rpr.mcp_read_model import ReadOnlyDatabaseError, SQLiteReadModel
from rpr.mcp_server import ReadOnlyRprMcpServer, run_stdio
from rpr.mcp_stable_snapshot import STABLE_PROTOCOL_VERSION
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.storage import SQLiteStore


def _definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="inspect-only-test",
        action_class=ActionClass.APPROVAL_REQUIRED,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority="approver",
        execution_actor="executor",
        stop_authority="stopper",
        evidence_owner="evidence",
        repair_owner="repair",
        resume_authority="resume",
        human_return_point="human",
        residual_owner="residual",
    )


def _database(tmp_path: Path) -> Path:
    database = tmp_path / "rpr.sqlite3"
    store = SQLiteStore(database)
    definition = _definition("path-1")
    store.create_or_replay_pathway(definition, PathwayState.HUMAN_GATE, "key-1")
    event = build_event(
        pathway_id="path-1",
        event_type="test_event",
        actor="tester",
        payload={"safe": True},
        previous_hash=None,
    )
    store.append_event(event)
    return database


def _initialized_server(database: Path) -> ReadOnlyRprMcpServer:
    server = ReadOnlyRprMcpServer(SQLiteReadModel(database))
    initialize = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": STABLE_PROTOCOL_VERSION},
        }
    )
    assert initialize is not None
    assert initialize["result"]["capabilities"] == {"tools": {"listChanged": False}}
    assert server.handle(
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    ) is None
    return server


def test_read_model_requires_existing_rpr_database(tmp_path: Path) -> None:
    with pytest.raises(ReadOnlyDatabaseError):
        SQLiteReadModel(tmp_path / "missing.sqlite3")


def test_status_and_read_only_tools(tmp_path: Path) -> None:
    server = _initialized_server(_database(tmp_path))

    status = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "rpr.get_status", "arguments": {}},
        }
    )
    assert status is not None
    assert status["result"]["structuredContent"]["mode"] == "read_only"
    assert status["result"]["structuredContent"]["pathway_count"] == 1
    assert status["result"]["structuredContent"]["unresolved_count"] == 1

    listed = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "rpr.list_pathways", "arguments": {}},
        }
    )
    assert listed is not None
    pathways = listed["result"]["structuredContent"]["pathways"]
    assert pathways[0]["pathway_id"] == "path-1"
    assert pathways[0]["state"] == PathwayState.HUMAN_GATE.value

    unresolved = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "rpr.list_unresolved", "arguments": {"limit": 10}},
        }
    )
    assert unresolved is not None
    assert [item["pathway_id"] for item in unresolved["result"]["structuredContent"]["pathways"]] == ["path-1"]


def test_pathway_and_evidence_tools(tmp_path: Path) -> None:
    server = _initialized_server(_database(tmp_path))
    pathway = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "rpr.get_pathway", "arguments": {"pathway_id": "path-1"}},
        }
    )
    assert pathway is not None
    assert pathway["result"]["structuredContent"]["definition"]["action_name"] == "inspect-only-test"

    evidence = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "rpr.get_evidence", "arguments": {"pathway_id": "path-1"}},
        }
    )
    assert evidence is not None
    events = evidence["result"]["structuredContent"]["events"]
    assert events[0]["event"]["event_type"] == "test_event"


def test_missing_pathway_is_a_tool_error(tmp_path: Path) -> None:
    server = _initialized_server(_database(tmp_path))
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "rpr.get_pathway", "arguments": {"pathway_id": "missing"}},
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    assert response["result"]["structuredContent"]["error"] == "pathway_not_found"


def test_tools_are_unavailable_before_initialized_notification(tmp_path: Path) -> None:
    server = ReadOnlyRprMcpServer(SQLiteReadModel(_database(tmp_path)))
    stdin = io.StringIO(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
        )
        + "\n"
    )
    stdout = io.StringIO()
    assert run_stdio(server, stdin=stdin, stdout=stdout) == 0
    response = json.loads(stdout.getvalue())
    assert response["error"]["code"] == -32002


def test_stdio_emits_only_json_rpc_lines(tmp_path: Path) -> None:
    server = ReadOnlyRprMcpServer(SQLiteReadModel(_database(tmp_path)))
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": STABLE_PROTOCOL_VERSION},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "rpr.get_status", "arguments": {}},
        },
    ]
    stdin = io.StringIO("\n".join(json.dumps(item) for item in requests) + "\n")
    stdout = io.StringIO()
    assert run_stdio(server, stdin=stdin, stdout=stdout) == 0
    lines = stdout.getvalue().splitlines()
    assert len(lines) == 3
    decoded = [json.loads(line) for line in lines]
    assert [item["id"] for item in decoded] == [1, 2, 3]
    assert decoded[1]["result"]["tools"][0]["name"] == "rpr.get_status"


def test_malformed_json_returns_parse_error(tmp_path: Path) -> None:
    server = ReadOnlyRprMcpServer(SQLiteReadModel(_database(tmp_path)))
    stdout = io.StringIO()
    run_stdio(server, stdin=io.StringIO("{not-json}\n"), stdout=stdout)
    response = json.loads(stdout.getvalue())
    assert response["error"]["code"] == -32700
