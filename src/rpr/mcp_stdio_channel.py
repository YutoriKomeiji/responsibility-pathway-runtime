# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .mcp_stdio_framing import McpStdioDiagnostics, McpStdioLineCodec
from .mcp_stable_transport import McpTransportError


@dataclass(frozen=True)
class McpStdioEvent:
    """One bounded event produced by a future subprocess/pipe owner."""

    stream: str
    data: bytes = b""
    eof: bool = False

    def __post_init__(self) -> None:
        if self.stream not in {"stdout", "stderr"}:
            raise ValueError("stdio event stream must be stdout or stderr")
        if not isinstance(self.data, bytes):
            raise TypeError("stdio event data must be bytes")
        if not isinstance(self.eof, bool):
            raise TypeError("stdio event eof must be bool")
        if self.eof and self.data:
            raise ValueError("stdio EOF event must not contain data")
        if not self.eof and not self.data:
            raise ValueError("stdio data event must not be empty")


class McpStdioDuplex(Protocol):
    """Abstract stdin/stdout/stderr owner below the channel.

    A later implementation may own a subprocess and OS pipes. This increment
    intentionally provides no process spawn, shell, authentication, or live I/O.
    """

    def write_stdin(self, data: bytes) -> int: ...

    def read_event(self) -> McpStdioEvent: ...


class McpStdioChannel:
    """Single-flight decoded-message channel over bounded stdio events."""

    def __init__(
        self,
        duplex: McpStdioDuplex,
        *,
        codec: McpStdioLineCodec | None = None,
        diagnostics: McpStdioDiagnostics | None = None,
        max_events_per_exchange: int = 4096,
    ) -> None:
        if isinstance(max_events_per_exchange, bool) or not isinstance(
            max_events_per_exchange, int
        ):
            raise ValueError("max_events_per_exchange must be an integer")
        if max_events_per_exchange <= 0:
            raise ValueError("max_events_per_exchange must be positive")
        self.duplex = duplex
        self.codec = codec or McpStdioLineCodec()
        self.diagnostics = diagnostics or McpStdioDiagnostics()
        self.max_events_per_exchange = max_events_per_exchange
        self._stdout_eof = False
        self._stderr_eof = False

    def exchange(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        self._require_open_stdout()
        self._write_message(message)

        for _ in range(self.max_events_per_exchange):
            event = self._read_event()
            if event.stream == "stderr":
                self._handle_stderr(event)
                continue
            if event.eof:
                self._stdout_eof = True
                self.codec.finish()
                raise McpTransportError("MCP stdio stdout closed before a response")

            messages = self.codec.feed(event.data)
            if not messages:
                continue
            if len(messages) != 1:
                raise McpTransportError(
                    "MCP stdio exchange produced multiple protocol messages"
                )
            return messages[0]

        raise McpTransportError("MCP stdio exchange exceeded max_events_per_exchange")

    def send(self, message: Mapping[str, Any]) -> None:
        self._require_open_stdout()
        self._write_message(message)

    def _write_message(self, message: Mapping[str, Any]) -> None:
        payload = self.codec.encode(message)
        offset = 0
        while offset < len(payload):
            try:
                written = self.duplex.write_stdin(payload[offset:])
            except McpTransportError:
                raise
            except (BrokenPipeError, TimeoutError, ConnectionError, OSError):
                raise
            except Exception as exc:
                raise McpTransportError(
                    f"MCP stdio write failed: {type(exc).__name__}: {exc}"
                ) from exc
            if isinstance(written, bool) or not isinstance(written, int):
                raise McpTransportError("MCP stdio writer returned a non-integer count")
            remaining = len(payload) - offset
            if written <= 0 or written > remaining:
                raise McpTransportError("MCP stdio writer returned an invalid byte count")
            offset += written

    def _read_event(self) -> McpStdioEvent:
        try:
            event = self.duplex.read_event()
        except McpTransportError:
            raise
        except (TimeoutError, ConnectionError, OSError):
            raise
        except Exception as exc:
            raise McpTransportError(
                f"MCP stdio read failed: {type(exc).__name__}: {exc}"
            ) from exc
        if not isinstance(event, McpStdioEvent):
            raise McpTransportError("MCP stdio reader returned an invalid event")
        return event

    def _handle_stderr(self, event: McpStdioEvent) -> None:
        if event.eof:
            self._stderr_eof = True
            return
        if self._stderr_eof:
            raise McpTransportError("MCP stdio emitted stderr data after EOF")
        self.diagnostics.feed(event.data)

    def _require_open_stdout(self) -> None:
        if self._stdout_eof:
            raise McpTransportError("MCP stdio stdout is already closed")
