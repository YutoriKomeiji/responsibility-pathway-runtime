# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import sys

import pytest

from rpr.mcp_jsonrpc_session import McpJsonRpcSession
from rpr.mcp_local_subprocess_stdio import McpLocalSubprocessError, McpLocalSubprocessStdio
from rpr.mcp_stable_transport import McpTransportError
from rpr.mcp_stdio_channel import McpStdioChannel
from rpr.mcp_subprocess_lifecycle import McpSubprocessLifecycle


NORMAL_HELPER = r'''
import json
import sys

for raw in sys.stdin.buffer:
    request = json.loads(raw)
    sys.stderr.buffer.write(b"diagnostic-before-response\n")
    sys.stderr.buffer.flush()
    if "id" not in request:
        continue
    response = {
        "jsonrpc": "2.0",
        "id": request["id"],
        "result": {"method": request["method"], "ok": True},
    }
    encoded = json.dumps(response, separators=(",", ":")).encode() + b"\n"
    midpoint = max(1, len(encoded) // 2)
    sys.stdout.buffer.write(encoded[:midpoint])
    sys.stdout.buffer.flush()
    sys.stdout.buffer.write(encoded[midpoint:])
    sys.stdout.buffer.flush()
'''

MALFORMED_HELPER = r'''
import sys
sys.stdin.buffer.readline()
sys.stdout.buffer.write(b"{not-json}\n")
sys.stdout.buffer.flush()
'''

WRONG_ID_HELPER = r'''
import json
import sys
request = json.loads(sys.stdin.buffer.readline())
response = {"jsonrpc": "2.0", "id": request["id"] + 1, "result": {"ok": True}}
sys.stdout.buffer.write(json.dumps(response).encode() + b"\n")
sys.stdout.buffer.flush()
'''

ABRUPT_EXIT_HELPER = r'''
import os
import sys
sys.stdin.buffer.readline()
os._exit(17)
'''

SLEEP_HELPER = "import time; time.sleep(30)"
IGNORE_TERM_HELPER = r'''
import signal
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
time.sleep(30)
'''


def owner(code: str, *, timeout: float = 0.2) -> McpLocalSubprocessStdio:
    return McpLocalSubprocessStdio(
        [sys.executable, "-u", "-c", code],
        env={},
        read_timeout_seconds=timeout,
        read_size=5,
    )


def shutdown(transport: McpLocalSubprocessStdio, *, graceful: float = 0.2):
    return McpSubprocessLifecycle(
        transport,
        graceful_timeout_seconds=graceful,
        terminate_timeout_seconds=0.5,
        kill_timeout_seconds=0.5,
    ).shutdown()


def test_real_subprocess_round_trip_fragmented_stdout_and_stderr() -> None:
    transport = owner(NORMAL_HELPER)
    channel = McpStdioChannel(transport, max_events_per_exchange=4096)
    session = McpJsonRpcSession(channel)

    assert session.request("tools/call", {}) == {"method": "tools/call", "ok": True}
    assert "diagnostic-before-response" in channel.diagnostics.text()

    result = shutdown(transport)
    assert result.exit_code == 0
    assert result.graceful is True


def test_malformed_json_fails_closed() -> None:
    transport = owner(MALFORMED_HELPER)
    session = McpJsonRpcSession(McpStdioChannel(transport))
    try:
        with pytest.raises(McpTransportError):
            session.request("ping", {})
    finally:
        shutdown(transport)


def test_response_id_mismatch_fails_closed() -> None:
    transport = owner(WRONG_ID_HELPER)
    session = McpJsonRpcSession(McpStdioChannel(transport))
    try:
        with pytest.raises(McpTransportError, match="response id mismatch"):
            session.request("ping", {})
    finally:
        shutdown(transport)


def test_response_timeout_terminates_child() -> None:
    transport = owner(SLEEP_HELPER, timeout=0.05)
    session = McpJsonRpcSession(McpStdioChannel(transport))

    with pytest.raises(TimeoutError, match="stdio read timed out"):
        session.request("ping", {})

    result = shutdown(transport, graceful=0.05)
    assert result.exit_code != 0
    assert result.terminated is True


def test_abrupt_exit_is_not_misreported_as_success() -> None:
    transport = owner(ABRUPT_EXIT_HELPER)
    session = McpJsonRpcSession(McpStdioChannel(transport))
    try:
        with pytest.raises(McpTransportError):
            session.request("tools/call", {})
        assert transport.wait(1.0) == 17
    finally:
        transport.close_pipes()


def test_lifecycle_escalates_to_kill_when_sigterm_is_ignored() -> None:
    transport = owner(IGNORE_TERM_HELPER)
    result = shutdown(transport, graceful=0.05)

    assert result.exit_code != 0
    assert result.killed is True


def test_restart_after_failed_child_uses_fresh_process_and_request_sequence() -> None:
    failed = owner(ABRUPT_EXIT_HELPER)
    try:
        with pytest.raises(McpTransportError):
            McpJsonRpcSession(McpStdioChannel(failed)).request("ping", {})
        assert failed.wait(1.0) == 17
    finally:
        failed.close_pipes()

    replacement = owner(NORMAL_HELPER)
    try:
        session = McpJsonRpcSession(McpStdioChannel(replacement), first_request_id=1)
        assert session.request("ping", {}) == {"method": "ping", "ok": True}
    finally:
        shutdown(replacement)


def test_missing_executable_spawn_failure_is_wrapped() -> None:
    missing = os.path.join(os.sep, "definitely", "missing", "rpr-mcp-acceptance-helper")
    with pytest.raises(McpLocalSubprocessError, match="failed to spawn"):
        McpLocalSubprocessStdio([missing], env={})


def test_write_after_child_exit_fails_closed() -> None:
    transport = owner("pass")
    assert transport.wait(1.0) == 0
    try:
        with pytest.raises((McpLocalSubprocessError, BrokenPipeError)):
            transport.write_stdin(b"{}\n")
    finally:
        transport.close_pipes()
