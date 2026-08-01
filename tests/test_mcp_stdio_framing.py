# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.mcp_stdio_framing import (
    McpStdioDiagnostics,
    McpStdioFramingError,
    McpStdioLineCodec,
)


def test_round_trip_strict_json_object() -> None:
    codec = McpStdioLineCodec()
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"name": "雪"}}

    encoded = codec.encode(message)

    assert encoded.endswith(b"\n")
    assert codec.feed(encoded) == (message,)
    codec.finish()


def test_partial_read_assembles_only_after_lf() -> None:
    codec = McpStdioLineCodec()

    assert codec.feed(b'{"jsonrpc":"2.0",') == ()
    assert codec.buffered_bytes > 0
    assert codec.feed(b'"id":1,"result":{}}\n') == (
        {"jsonrpc": "2.0", "id": 1, "result": {}},
    )
    assert codec.buffered_bytes == 0


def test_multiple_messages_in_one_chunk_preserve_order() -> None:
    codec = McpStdioLineCodec()

    assert codec.feed(b'{"id":1}\n{"id":2}\n') == ({"id": 1}, {"id": 2})


@pytest.mark.parametrize(
    "payload",
    [
        b"\n",
        b"\xef\xbb\xbf{}\n",
        b"\xff\n",
        b"not-json\n",
        b"[]\n",
        b'{"id":1} trailing\n',
        b'{"id":1,"id":2}\n',
        b'{"value":NaN}\n',
    ],
)
def test_invalid_line_poison_codec(payload: bytes) -> None:
    codec = McpStdioLineCodec()

    with pytest.raises(McpStdioFramingError):
        codec.feed(payload)

    assert codec.poisoned is True
    assert codec.buffered_bytes == 0
    with pytest.raises(McpStdioFramingError, match="poisoned"):
        codec.feed(b"{}\n")


def test_oversized_complete_message_is_rejected() -> None:
    codec = McpStdioLineCodec(max_message_bytes=4)

    with pytest.raises(McpStdioFramingError, match="exceeds"):
        codec.feed(b'{"a":1}\n')


def test_oversized_unterminated_message_is_rejected_before_unbounded_growth() -> None:
    codec = McpStdioLineCodec(max_message_bytes=4)

    with pytest.raises(McpStdioFramingError, match="unterminated"):
        codec.feed(b"12345")


def test_finish_rejects_partial_trailing_message() -> None:
    codec = McpStdioLineCodec()
    assert codec.feed(b'{"id":1}') == ()

    with pytest.raises(McpStdioFramingError, match="unterminated"):
        codec.finish()


def test_encode_rejects_nonfinite_and_oversized_messages() -> None:
    nonfinite = McpStdioLineCodec()
    with pytest.raises(McpStdioFramingError, match="strict JSON"):
        nonfinite.encode({"value": float("nan")})

    oversized = McpStdioLineCodec(max_message_bytes=2)
    with pytest.raises(McpStdioFramingError, match="exceeds"):
        oversized.encode({"a": 1})


def test_stderr_diagnostics_never_become_protocol_messages() -> None:
    diagnostics = McpStdioDiagnostics(max_bytes=8)

    diagnostics.feed(b'{"id":1}\nwarning')

    assert diagnostics.text() == '{"id":1}'
    assert diagnostics.truncated is True


def test_diagnostics_replace_invalid_utf8_without_poisoning_protocol_codec() -> None:
    diagnostics = McpStdioDiagnostics()
    protocol = McpStdioLineCodec()

    diagnostics.feed(b"bad:\xff")

    assert diagnostics.text() == "bad:\ufffd"
    assert protocol.feed(b"{}\n") == ({},)
