# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import pytest

from rpr.mcp_jsonrpc_session import McpJsonRpcRemoteError, McpJsonRpcSession
from rpr.mcp_stable_transport import McpTransportError


@dataclass
class ScriptedChannel:
    responses: list[object] = field(default_factory=list)
    exchanges: list[dict[str, Any]] = field(default_factory=list)
    notifications: list[dict[str, Any]] = field(default_factory=list)

    def exchange(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        self.exchanges.append(dict(message))
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value  # type: ignore[return-value]

    def send(self, message: Mapping[str, Any]) -> None:
        self.notifications.append(dict(message))


def test_request_ids_are_monotonic_and_results_are_unwrapped():
    channel = ScriptedChannel(
        responses=[
            {"jsonrpc": "2.0", "id": 7, "result": {"first": True}},
            {"jsonrpc": "2.0", "id": 8, "result": {"second": True}},
        ]
    )
    session = McpJsonRpcSession(channel, first_request_id=7)

    assert session.request("initialize", {"value": 1}) == {"first": True}
    assert session.request("tools/list", {}) == {"second": True}
    assert [item["id"] for item in channel.exchanges] == [7, 8]
    assert all(item["jsonrpc"] == "2.0" for item in channel.exchanges)


def test_notification_has_no_id_and_never_consumes_response():
    channel = ScriptedChannel()
    session = McpJsonRpcSession(channel, first_request_id=3)

    session.notify("notifications/initialized", {})

    assert channel.notifications == [
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    ]
    assert channel.exchanges == []


@pytest.mark.parametrize(
    "response, reason",
    [
        ({"id": 1, "result": {}}, "version mismatch"),
        ({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}, "notification"),
        ({"jsonrpc": "2.0", "id": 2, "result": {}}, "id mismatch"),
        ({"jsonrpc": "2.0", "id": True, "result": {}}, "id mismatch"),
        ({"jsonrpc": "2.0", "id": 1}, "exactly one"),
        ({"jsonrpc": "2.0", "id": 1, "result": {}, "error": {}}, "exactly one"),
        ({"jsonrpc": "2.0", "id": 1, "result": [], "extra": 1}, "unsupported members"),
        ({"jsonrpc": "2.0", "id": 1, "result": []}, "result must be an object"),
    ],
)
def test_malformed_or_uncorrelated_responses_fail_closed(response, reason):
    session = McpJsonRpcSession(ScriptedChannel([response]))

    with pytest.raises(McpTransportError, match=reason):
        session.request("tools/list", {})


@pytest.mark.parametrize(
    "error, reason",
    [
        ([], "error must be an object"),
        ({"code": True, "message": "bad"}, "code must be an integer"),
        ({"code": -32603, "message": ""}, "message must be a non-empty string"),
        ({"code": -32603, "message": "bad", "unexpected": 1}, "unsupported members"),
    ],
)
def test_malformed_remote_errors_fail_closed(error, reason):
    session = McpJsonRpcSession(
        ScriptedChannel([{"jsonrpc": "2.0", "id": 1, "error": error}])
    )

    with pytest.raises(McpTransportError, match=reason):
        session.request("tools/list", {})


def test_valid_remote_error_preserves_code_message_and_data():
    session = McpJsonRpcSession(
        ScriptedChannel(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {"code": -32602, "message": "Invalid params", "data": {"field": "name"}},
                }
            ]
        )
    )

    with pytest.raises(McpJsonRpcRemoteError) as caught:
        session.request("tools/call", {"name": "replace_text"})

    assert caught.value.code == -32602
    assert caught.value.message == "Invalid params"
    assert caught.value.data == {"field": "name"}


def test_channel_programming_error_is_wrapped_but_transport_failures_keep_type():
    programming = McpJsonRpcSession(ScriptedChannel([RuntimeError("boom")]))
    with pytest.raises(McpTransportError, match="channel exchange failed"):
        programming.request("tools/list", {})

    timeout = McpJsonRpcSession(ScriptedChannel([TimeoutError("late")]))
    with pytest.raises(TimeoutError, match="late"):
        timeout.request("tools/list", {})


def test_invalid_outbound_method_and_params_are_rejected_before_channel_use():
    channel = ScriptedChannel()
    session = McpJsonRpcSession(channel)

    with pytest.raises(McpTransportError, match="method"):
        session.request(" ", {})
    with pytest.raises(McpTransportError, match="params"):
        session.request("tools/list", [])  # type: ignore[arg-type]

    assert channel.exchanges == []
