# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import ipaddress
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Mapping


class ReadOnlyConnectionError(RuntimeError):
    """Raised when a read-only connection rehearsal fails closed."""


@dataclass(frozen=True)
class ReadOnlyConnectionEvidence:
    method: str
    origin: str
    status_code: int
    content_length: int
    body_sha256: str
    content_type: str | None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def rehearse_read_only_connection(
    url: str,
    *,
    allowed_origins: set[str],
    method: str = "GET",
    timeout_seconds: float = 3.0,
    maximum_response_bytes: int = 256 * 1024,
    headers: Mapping[str, str] | None = None,
    allow_public_network: bool = False,
) -> ReadOnlyConnectionEvidence:
    normalized_method = method.upper()
    if normalized_method not in {"GET", "HEAD"}:
        raise ReadOnlyConnectionError("method_not_read_only")
    if timeout_seconds <= 0 or maximum_response_bytes <= 0:
        raise ReadOnlyConnectionError("invalid_bound")

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ReadOnlyConnectionError("unsupported_url")
    if parsed.username is not None or parsed.password is not None:
        raise ReadOnlyConnectionError("url_userinfo_forbidden")
    if parsed.fragment:
        raise ReadOnlyConnectionError("url_fragment_forbidden")

    origin = _origin(parsed)
    if origin not in allowed_origins:
        raise ReadOnlyConnectionError("origin_not_allowed")
    loopback = _is_loopback_literal(parsed.hostname)
    if parsed.scheme == "http" and not loopback:
        raise ReadOnlyConnectionError("public_plain_http_forbidden")
    if not allow_public_network and not loopback:
        raise ReadOnlyConnectionError("public_network_not_enabled")

    request_headers = dict(headers or {})
    allowed_header_names = {"accept", "user-agent"}
    if any(name.lower() not in allowed_header_names for name in request_headers):
        raise ReadOnlyConnectionError("header_not_allowed")
    if any("\r" in value or "\n" in value for value in request_headers.values()):
        raise ReadOnlyConnectionError("invalid_header_value")

    request = urllib.request.Request(url, method=normalized_method, headers=request_headers)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            status = int(response.status)
            if not 200 <= status < 300:
                raise ReadOnlyConnectionError(f"unexpected_status:{status}")
            body = b"" if normalized_method == "HEAD" else response.read(maximum_response_bytes + 1)
            if len(body) > maximum_response_bytes:
                raise ReadOnlyConnectionError("response_too_large")
            return ReadOnlyConnectionEvidence(
                method=normalized_method,
                origin=origin,
                status_code=status,
                content_length=len(body),
                body_sha256=hashlib.sha256(body).hexdigest(),
                content_type=response.headers.get("Content-Type"),
            )
    except ReadOnlyConnectionError:
        raise
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ReadOnlyConnectionError("redirect_forbidden") from exc
        raise ReadOnlyConnectionError(f"http_error:{exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReadOnlyConnectionError("connection_failed") from exc


def _origin(parsed: urllib.parse.SplitResult) -> str:
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port or default_port
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    suffix = "" if port == default_port else f":{port}"
    return f"{parsed.scheme}://{host}{suffix}"


def _is_loopback_literal(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
