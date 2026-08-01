# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from rpr import ExecutionRequest, ExecutionStatus, HttpMutationExecutor, JsonFieldReadback


class _FaultHandler(BaseHTTPRequestHandler):
    counters: dict[str, int] = {}

    def do_POST(self):  # noqa: N802
        type(self).counters[self.path] = type(self).counters.get(self.path, 0) + 1
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))

        if self.path == "/ok":
            self._send_json(200, {"id": payload["id"]})
            return
        if self.path == "/server-error":
            self._send_json(503, {"error": "unavailable"})
            return
        if self.path == "/malformed":
            body = b'{"id":'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/oversized":
            body = json.dumps({"id": payload["id"], "padding": "x" * 4096}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/timeout":
            time.sleep(0.25)
            try:
                self._send_json(200, {"id": payload["id"]})
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if self.path == "/disconnect":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        self._send_json(404, {"error": "not_found"})

    def _send_json(self, status: int, value: object) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        del format, args


@pytest.fixture
def fault_server():
    _FaultHandler.counters = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FaultHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def _executor(origin: str, **kwargs) -> HttpMutationExecutor:
    return HttpMutationExecutor(
        allowed_origins={origin},
        readback=JsonFieldReadback("id", "expected_id"),
        allow_insecure_http=True,
        **kwargs,
    )


def _request(origin: str, path: str, *, idem: str = "idem-1", value: str = "r-1") -> ExecutionRequest:
    return ExecutionRequest(
        operation_id=f"op-{path}",
        attempt_id=f"attempt-{path}",
        idempotency_key=idem,
        action="http_json_mutation",
        parameters={
            "url": origin + path,
            "json": {"id": value},
            "expected_id": value,
        },
    )


def test_normal_loopback_readback_and_replay_do_not_duplicate_dispatch(fault_server):
    origin = f"http://127.0.0.1:{fault_server.server_port}"
    executor = _executor(origin)
    request = _request(origin, "/ok")

    first = executor.execute(request)
    replay = executor.execute(request)

    assert first.status is ExecutionStatus.SUCCEEDED
    assert first.readback is not None and first.readback.verified
    assert replay == first
    assert _FaultHandler.counters["/ok"] == 1


def test_same_idempotency_key_with_different_request_is_rejected(fault_server):
    origin = f"http://127.0.0.1:{fault_server.server_port}"
    executor = _executor(origin)
    first = _request(origin, "/ok", idem="shared", value="a")
    conflicting = _request(origin, "/ok", idem="shared", value="b")

    assert executor.execute(first).status is ExecutionStatus.SUCCEEDED
    result = executor.execute(conflicting)

    assert result.status is ExecutionStatus.FAILED
    assert result.reason == "idempotency_conflict"
    assert _FaultHandler.counters["/ok"] == 1


@pytest.mark.parametrize(
    ("path", "executor_kwargs", "reason_fragment"),
    [
        ("/server-error", {}, "http_error_after_dispatch"),
        ("/malformed", {}, "invalid_readback"),
        ("/oversized", {"max_response_bytes": 128}, "response_too_large"),
        ("/timeout", {"timeout_seconds": 0.05}, "transport_ambiguous"),
        ("/disconnect", {}, "transport_ambiguous"),
    ],
)
def test_faults_never_become_false_success_or_automatic_replay(
    fault_server,
    path: str,
    executor_kwargs: dict[str, object],
    reason_fragment: str,
):
    origin = f"http://127.0.0.1:{fault_server.server_port}"
    executor = _executor(origin, **executor_kwargs)
    request = _request(origin, path, idem=f"idem-{path}")

    first = executor.execute(request)
    replay = executor.execute(request)

    assert first.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert reason_fragment in (first.reason or "")
    assert replay == first
    assert _FaultHandler.counters[path] == 1
