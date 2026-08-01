# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from typing import Any, Mapping

from .mcp_stable_transport import McpTransportError


_UTF8_BOM = b"\xef\xbb\xbf"


class McpStdioFramingError(McpTransportError):
    """A fail-closed byte, line, UTF-8, or JSON framing failure."""


class McpStdioLineCodec:
    """Incremental one-JSON-object-per-LF codec for bounded MCP stdio.

    The codec owns bytes and line framing only. Process lifecycle, pipes,
    authentication, timeouts, and JSON-RPC correlation remain outside it.
    A framing error poisons the codec because stream synchronization can no
    longer be proven; callers must construct a new codec before continuing.
    """

    def __init__(self, *, max_message_bytes: int = 1_048_576) -> None:
        if isinstance(max_message_bytes, bool) or not isinstance(max_message_bytes, int):
            raise ValueError("max_message_bytes must be an integer")
        if max_message_bytes <= 0:
            raise ValueError("max_message_bytes must be positive")
        self.max_message_bytes = max_message_bytes
        self._buffer = bytearray()
        self._poisoned = False

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    @property
    def poisoned(self) -> bool:
        return self._poisoned

    def encode(self, message: Mapping[str, Any]) -> bytes:
        self._require_healthy()
        if not isinstance(message, Mapping):
            self._fail("stdio message must be an object")
        try:
            text = json.dumps(
                dict(message),
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            self._fail(f"stdio message is not strict JSON: {exc}", cause=exc)
        payload = text.encode("utf-8")
        if payload.startswith(_UTF8_BOM):
            self._fail("stdio message must not contain a UTF-8 BOM")
        if len(payload) > self.max_message_bytes:
            self._fail("stdio message exceeds max_message_bytes")
        return payload + b"\n"

    def feed(self, chunk: bytes | bytearray | memoryview) -> tuple[dict[str, Any], ...]:
        self._require_healthy()
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            self._fail("stdio chunk must be bytes-like")
        value = bytes(chunk)
        if not value:
            return ()
        self._buffer.extend(value)
        if b"\n" not in self._buffer and len(self._buffer) > self.max_message_bytes:
            self._fail("unterminated stdio message exceeds max_message_bytes")

        messages: list[dict[str, Any]] = []
        while True:
            newline = self._buffer.find(b"\n")
            if newline < 0:
                break
            line = bytes(self._buffer[:newline])
            del self._buffer[: newline + 1]
            messages.append(self._decode_line(line))

        if len(self._buffer) > self.max_message_bytes:
            self._fail("unterminated stdio message exceeds max_message_bytes")
        return tuple(messages)

    def finish(self) -> None:
        """Close a stream, rejecting any unterminated trailing bytes."""

        self._require_healthy()
        if self._buffer:
            self._fail("stdio stream ended with an unterminated message")

    def _decode_line(self, line: bytes) -> dict[str, Any]:
        if not line:
            self._fail("empty stdio lines are not allowed")
        if len(line) > self.max_message_bytes:
            self._fail("stdio message exceeds max_message_bytes")
        if line.startswith(_UTF8_BOM):
            self._fail("stdio message must not contain a UTF-8 BOM")
        try:
            text = line.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            self._fail("stdio message is not valid UTF-8", cause=exc)
        try:
            value = json.loads(
                text,
                object_pairs_hook=self._object_without_duplicates,
                parse_constant=self._reject_nonfinite,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            self._fail(f"stdio message is not strict JSON: {exc}", cause=exc)
        if not isinstance(value, dict):
            self._fail("stdio JSON message must be an object")
        return value

    @staticmethod
    def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON object member: {key!r}")
            value[key] = item
        return value

    @staticmethod
    def _reject_nonfinite(value: str) -> Any:
        raise ValueError(f"non-finite JSON number is not allowed: {value}")

    def _require_healthy(self) -> None:
        if self._poisoned:
            raise McpStdioFramingError("stdio codec is poisoned after a prior framing failure")

    def _fail(self, reason: str, *, cause: BaseException | None = None) -> None:
        self._poisoned = True
        self._buffer.clear()
        error = McpStdioFramingError(reason)
        if cause is None:
            raise error
        raise error from cause


class McpStdioDiagnostics:
    """Bounded stderr collector that can never produce protocol messages."""

    def __init__(self, *, max_bytes: int = 65_536) -> None:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
            raise ValueError("max_bytes must be an integer")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes
        self._buffer = bytearray()
        self.truncated = False

    def feed(self, chunk: bytes | bytearray | memoryview) -> None:
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise TypeError("diagnostic chunk must be bytes-like")
        value = bytes(chunk)
        remaining = self.max_bytes - len(self._buffer)
        if remaining <= 0:
            self.truncated = self.truncated or bool(value)
            return
        self._buffer.extend(value[:remaining])
        if len(value) > remaining:
            self.truncated = True

    def text(self) -> str:
        return bytes(self._buffer).decode("utf-8", errors="replace")
