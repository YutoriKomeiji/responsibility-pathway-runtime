# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections import deque

import pytest

from rpr.mcp_stdio_channel import McpStdioChannel, McpStdioEvent
from rpr.mcp_stable_transport import McpTransportError


class ScriptedDuplex:
    def __init__(self, events=(), *, max_write: int | None = None, write_result=None):
        self.events = deque(events)
        self.max_write = max_write
        self.write_result = write_result
        self.writes: list[bytes] = []

    def write_stdin(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        if self.write_result is not None:
            return self.write_result
        if self.max_write is None:
            return len(data)
        return min(len(data), self.max_write)

    def read_event(self) -> McpStdioEvent:
        if not self.events:
            raise TimeoutError("script exhausted")
        return self.events.popleft()


def _response_line(request_id: int = 1) -> bytes:
    return (
        b'{"jsonrpc":"2.0","id":'
        + str(request_id).encode("ascii")
        + b',"result":{"ok":true}}\n'
    )


def test_exchange_supports_partial_write_partial_read_and_stderr() -> None:
    line = _response_line()
    duplex = ScriptedDuplex(
        [
            McpStdioEvent("stderr", b"starting\n"),
            McpStdioEvent("stdout", line[:11]),
            McpStdioEvent("stdout", line[11:]),
        ],
        max_write=5,
    )
    channel = McpStdioChannel(duplex)

    result = channel.exchange(
        {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
    )

    assert result == {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
    assert len(duplex.writes) > 1
    assert channel.diagnostics.text() == "starting\n"


def test_send_writes_notification_without_reading() -> None:
    duplex = ScriptedDuplex()
    channel = McpStdioChannel(duplex)

    channel.send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    assert b"".join(duplex.writes).endswith(b"\n")
    assert not duplex.events


def test_exchange_rejects_multiple_protocol_messages() -> None:
    duplex = ScriptedDuplex(
        [McpStdioEvent("stdout", _response_line(1) + _response_line(2))]
    )

    with pytest.raises(McpTransportError, match="multiple protocol messages"):
        McpStdioChannel(duplex).exchange(
            {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        )


def test_exchange_rejects_stdout_eof_before_response_and_stays_closed() -> None:
    duplex = ScriptedDuplex([McpStdioEvent("stdout", eof=True)])
    channel = McpStdioChannel(duplex)

    with pytest.raises(McpTransportError, match="closed before a response"):
        channel.exchange({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
    with pytest.raises(McpTransportError, match="already closed"):
        channel.send({"jsonrpc": "2.0", "method": "next", "params": {}})


def test_exchange_rejects_stderr_data_after_stderr_eof() -> None:
    duplex = ScriptedDuplex(
        [
            McpStdioEvent("stderr", eof=True),
            McpStdioEvent("stderr", b"late"),
        ]
    )

    with pytest.raises(McpTransportError, match="stderr data after EOF"):
        McpStdioChannel(duplex).exchange(
            {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        )


@pytest.mark.parametrize("write_result", [0, -1, True, "1", 10_000])
def test_write_rejects_invalid_progress(write_result) -> None:
    duplex = ScriptedDuplex(write_result=write_result)

    with pytest.raises(McpTransportError, match="writer returned"):
        McpStdioChannel(duplex).send(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        )


def test_exchange_rejects_invalid_event_object() -> None:
    class InvalidReader(ScriptedDuplex):
        def read_event(self):
            return {"stream": "stdout"}

    with pytest.raises(McpTransportError, match="invalid event"):
        McpStdioChannel(InvalidReader()).exchange(
            {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        )


def test_exchange_is_bounded_by_event_limit() -> None:
    duplex = ScriptedDuplex(
        [McpStdioEvent("stderr", b"noise") for _ in range(3)]
    )

    with pytest.raises(McpTransportError, match="exceeded max_events_per_exchange"):
        McpStdioChannel(duplex, max_events_per_exchange=3).exchange(
            {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        )


def test_event_validation_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="stdout or stderr"):
        McpStdioEvent("stdin", b"x")
    with pytest.raises(ValueError, match="must not contain data"):
        McpStdioEvent("stdout", b"x", eof=True)
    with pytest.raises(ValueError, match="must not be empty"):
        McpStdioEvent("stdout")
