# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from rpr.read_only_connection import (
    ReadOnlyConnectionError,
    rehearse_read_only_connection,
)


class _Handler(BaseHTTPRequestHandler):
    body = b'{"status":"ok"}'

    def do_GET(self) -> None:
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        body = self.body if self.path != "/large" else b"x" * 65
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:
        self.send_response(204)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def log_message(self, *_args: object) -> None:
        pass


@pytest.fixture()
def loopback_origin() -> str:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_loopback_get_retains_hash_not_body(loopback_origin: str) -> None:
    evidence = rehearse_read_only_connection(
        loopback_origin + "/ok",
        allowed_origins={loopback_origin},
        headers={"Accept": "application/json", "User-Agent": "rpr-rehearsal"},
    )
    assert evidence.method == "GET"
    assert evidence.origin == loopback_origin
    assert evidence.status_code == 200
    assert evidence.content_length == len(_Handler.body)
    assert evidence.body_sha256 == hashlib.sha256(_Handler.body).hexdigest()
    assert not hasattr(evidence, "body")


def test_head_is_read_only_and_retains_no_body(loopback_origin: str) -> None:
    evidence = rehearse_read_only_connection(
        loopback_origin + "/ok",
        method="HEAD",
        allowed_origins={loopback_origin},
    )
    assert evidence.status_code == 204
    assert evidence.content_length == 0
    assert evidence.body_sha256 == hashlib.sha256(b"").hexdigest()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_mutating_methods_fail_closed(loopback_origin: str, method: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="method_not_read_only"):
        rehearse_read_only_connection(
            loopback_origin + "/ok",
            method=method,
            allowed_origins={loopback_origin},
        )


def test_origin_must_be_explicitly_allowed(loopback_origin: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="origin_not_allowed"):
        rehearse_read_only_connection(loopback_origin + "/ok", allowed_origins=set())


def test_url_userinfo_is_forbidden(loopback_origin: str) -> None:
    authority = loopback_origin.removeprefix("http://")
    with pytest.raises(ReadOnlyConnectionError, match="url_userinfo_forbidden"):
        rehearse_read_only_connection(
            f"http://user:secret@{authority}/ok",
            allowed_origins={loopback_origin},
        )


@pytest.mark.parametrize("header", ["Authorization", "Cookie", "X-API-Key", "X-Auth-Token"])
def test_non_allowlisted_headers_are_forbidden(loopback_origin: str, header: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="header_not_allowed"):
        rehearse_read_only_connection(
            loopback_origin + "/ok",
            allowed_origins={loopback_origin},
            headers={header: "secret"},
        )


def test_header_newlines_are_forbidden(loopback_origin: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="invalid_header_value"):
        rehearse_read_only_connection(
            loopback_origin + "/ok",
            allowed_origins={loopback_origin},
            headers={"User-Agent": "safe\r\ninjected"},
        )


def test_redirects_are_not_followed(loopback_origin: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="redirect_forbidden"):
        rehearse_read_only_connection(
            loopback_origin + "/redirect",
            allowed_origins={loopback_origin},
        )


def test_response_size_is_bounded(loopback_origin: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="response_too_large"):
        rehearse_read_only_connection(
            loopback_origin + "/large",
            allowed_origins={loopback_origin},
            maximum_response_bytes=64,
        )


def test_public_network_requires_https_and_explicit_enablement() -> None:
    with pytest.raises(ReadOnlyConnectionError, match="public_plain_http_forbidden"):
        rehearse_read_only_connection(
            "http://example.com/",
            allowed_origins={"http://example.com"},
            allow_public_network=True,
        )
    with pytest.raises(ReadOnlyConnectionError, match="public_network_not_enabled"):
        rehearse_read_only_connection(
            "https://example.com/",
            allowed_origins={"https://example.com"},
        )


def test_invalid_bounds_fail_before_connection(loopback_origin: str) -> None:
    with pytest.raises(ReadOnlyConnectionError, match="invalid_bound"):
        rehearse_read_only_connection(
            loopback_origin + "/ok",
            allowed_origins={loopback_origin},
            timeout_seconds=0,
        )
