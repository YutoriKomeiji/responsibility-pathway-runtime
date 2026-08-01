# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import os
import sys

import pytest

from rpr.mcp_jsonrpc_session import McpJsonRpcSession
from rpr.mcp_local_subprocess_stdio import McpLocalSubprocessStdio
from rpr.mcp_stdio_channel import McpStdioChannel
from rpr.mcp_subprocess_lifecycle import McpSubprocessLifecycle


HELPER = r'''
import json
import os
import sys
import time

for raw in sys.stdin.buffer:
    message = json.loads(raw)
    sys.stderr.buffer.write(b"helper-diagnostic\n")
    sys.stderr.buffer.flush()
    time.sleep(0.01)
    if "id" not in message:
        continue
    response = {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "method": message["method"],
            "params": message.get("params", {}),
            "secret_inherited": "RPR_TEST_PARENT_SECRET" in os.environ,
            "allowed": os.environ.get("RPR_TEST_ALLOWED"),
        },
    }
    encoded = json.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n"
    midpoint = max(1, len(encoded) // 2)
    sys.stdout.buffer.write(encoded[:midpoint])
    sys.stdout.buffer.flush()
    sys.stdout.buffer.write(encoded[midpoint:])
    sys.stdout.buffer.flush()
'''

SLEEP_HELPER = "import time; time.sleep(30)"


def owner(code: str = HELPER, *, read_timeout_seconds: float = 2.0) -> McpLocalSubprocessStdio:
    return McpLocalSubprocessStdio(
        [sys.executable, "-u", "-c", code],
        env={"RPR_TEST_ALLOWED": "yes"},
        read_timeout_seconds=read_timeout_seconds,
        read_size=7,
    )


def test_real_local_pipe_round_trip_and_environment_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RPR_TEST_PARENT_SECRET", "must-not-cross-boundary")
    transport = owner()
    channel = McpStdioChannel(transport, max_events_per_exchange=4096)
    session = McpJsonRpcSession(channel)

    result = session.request("tools/call", {"name": "echo", "arguments": {"value": 7}})

    assert result == {
        "method": "tools/call",
        "params": {"name": "echo", "arguments": {"value": 7}},
        "secret_inherited": False,
        "allowed": "yes",
    }
    assert "helper-diagnostic" in channel.diagnostics.text()

    exit_result = McpSubprocessLifecycle(
        transport,
        graceful_timeout_seconds=2.0,
        terminate_timeout_seconds=1.0,
        kill_timeout_seconds=1.0,
    ).shutdown()
    assert exit_result.exit_code == 0
    assert exit_result.graceful is True
    assert transport.stdin.closed
    assert transport.stdout.closed
    assert transport.stderr.closed


def test_notification_is_written_without_response_and_shutdown_is_clean() -> None:
    transport = owner()
    session = McpJsonRpcSession(McpStdioChannel(transport))
    session.notify("notifications/initialized", {})

    result = McpSubprocessLifecycle(
        transport,
        graceful_timeout_seconds=2.0,
        terminate_timeout_seconds=1.0,
        kill_timeout_seconds=1.0,
    ).shutdown()

    assert result.exit_code == 0
    assert result.graceful is True


def test_read_timeout_fails_closed_and_lifecycle_terminates_sleeping_helper() -> None:
    transport = owner(SLEEP_HELPER, read_timeout_seconds=0.05)
    channel = McpStdioChannel(transport, max_events_per_exchange=4)
    session = McpJsonRpcSession(channel)

    with pytest.raises(TimeoutError, match="stdio read timed out"):
        session.request("ping", {})

    result = McpSubprocessLifecycle(
        transport,
        graceful_timeout_seconds=0.05,
        terminate_timeout_seconds=1.0,
        kill_timeout_seconds=1.0,
    ).shutdown()
    assert result.exit_code != 0
    assert result.terminated is True


def test_explicit_environment_does_not_copy_parent_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/parent/path/that/must/not/be/copied")
    transport = owner()
    try:
        assert transport.env == {"RPR_TEST_ALLOWED": "yes"}
        assert "PATH" not in transport.env
    finally:
        McpSubprocessLifecycle(
            transport,
            graceful_timeout_seconds=2.0,
            terminate_timeout_seconds=1.0,
            kill_timeout_seconds=1.0,
        ).shutdown()


@pytest.mark.parametrize(
    "argv",
    [[], [""], ["python", "bad\x00arg"], "python"],
)
def test_invalid_argv_is_rejected_before_spawn(argv: object) -> None:
    with pytest.raises(ValueError, match="argv"):
        McpLocalSubprocessStdio(argv, env={})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "environment",
    [
        {"BAD=NAME": "value"},
        {"BAD\x00NAME": "value"},
        {"GOOD": "bad\x00value"},
        {1: "value"},
    ],
)
def test_invalid_environment_is_rejected_before_spawn(environment: object) -> None:
    with pytest.raises(ValueError, match="environment"):
        McpLocalSubprocessStdio(
            [sys.executable, "-c", "pass"],
            env=environment,  # type: ignore[arg-type]
        )


def test_missing_executable_is_wrapped_fail_closed() -> None:
    missing = os.path.join(os.sep, "definitely", "missing", "rpr-mcp-helper")
    with pytest.raises(Exception, match="failed to spawn local MCP subprocess"):
        McpLocalSubprocessStdio([missing], env={})
