# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence


class ReadbackStrategy(Protocol):
    def verify(self, *, request: ExecutionRequest, status_code: int, headers: Mapping[str, str], body: bytes) -> ReadbackEvidence: ...


@dataclass(frozen=True)
class JsonFieldReadback:
    """Verify one JSON response field against an expected request parameter."""

    response_field: str
    expected_parameter: str

    def verify(self, *, request: ExecutionRequest, status_code: int, headers: Mapping[str, str], body: bytes) -> ReadbackEvidence:
        del headers
        if not 200 <= status_code < 300:
            return ReadbackEvidence(False, {"status_code": status_code}, "unexpected_status")
        try:
            value = json.loads(body.decode("utf-8"))
            observed = value[self.response_field]
            expected = request.parameters[self.expected_parameter]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            return ReadbackEvidence(False, {"status_code": status_code}, f"invalid_readback: {type(exc).__name__}")
        verified = observed == expected
        return ReadbackEvidence(
            verified,
            {"status_code": status_code, "field": self.response_field, "value": observed},
            None if verified else "readback_value_mismatch",
        )


class HttpMutationExecutor:
    """Bounded JSON HTTP mutation executor with strict origin allow-list and readback."""

    def __init__(
        self,
        *,
        allowed_origins: set[str],
        readback: ReadbackStrategy,
        timeout_seconds: float = 10.0,
        allow_insecure_http: bool = False,
        max_response_bytes: int = 1_000_000,
    ) -> None:
        if not allowed_origins:
            raise ValueError("allowed_origins is required")
        self.allowed_origins = {self._normalize_origin(value) for value in allowed_origins}
        self.readback = readback
        self.timeout_seconds = timeout_seconds
        self.allow_insecure_http = allow_insecure_http
        self.max_response_bytes = max_response_bytes
        self._results: dict[str, tuple[str, ExecutionResult]] = {}

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        fingerprint = self._fingerprint(request)
        replay = self._results.get(request.idempotency_key)
        if replay is not None:
            if replay[0] != fingerprint:
                return ExecutionResult(ExecutionStatus.FAILED, reason="idempotency_conflict")
            return replay[1]
        if request.action != "http_json_mutation":
            return ExecutionResult(ExecutionStatus.FAILED, reason="unsupported_action")
        try:
            url = str(request.parameters["url"])
            method = str(request.parameters.get("method", "POST")).upper()
            if method not in {"POST", "PUT", "PATCH", "DELETE"}:
                return ExecutionResult(ExecutionStatus.FAILED, reason="unsupported_method")
            self._validate_url(url)
            payload = json.dumps(request.parameters.get("json", {}), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers = {"Content-Type": "application/json", "Accept": "application/json", "Idempotency-Key": request.idempotency_key}
            supplied_headers = request.parameters.get("headers", {})
            if not isinstance(supplied_headers, Mapping):
                return ExecutionResult(ExecutionStatus.FAILED, reason="headers_must_be_mapping")
            for key, value in supplied_headers.items():
                lower = str(key).lower()
                if lower in {"host", "content-length", "transfer-encoding", "connection"}:
                    return ExecutionResult(ExecutionStatus.FAILED, reason=f"forbidden_header:{lower}")
                headers[str(key)] = str(value)
            response = urlopen(Request(url, data=payload, headers=headers, method=method), timeout=self.timeout_seconds)
            body = response.read(self.max_response_bytes + 1)
            if len(body) > self.max_response_bytes:
                result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="response_too_large")
            else:
                response_headers = {str(k): str(v) for k, v in response.headers.items()}
                readback = self.readback.verify(request=request, status_code=response.status, headers=response_headers, body=body)
                result = ExecutionResult(
                    ExecutionStatus.SUCCEEDED if readback.verified else ExecutionStatus.WRITE_STATUS_UNKNOWN,
                    {"status_code": response.status, "response_bytes": len(body)},
                    readback,
                    None if readback.verified else readback.reason,
                )
        except HTTPError as exc:
            # A server response proves the request reached the endpoint, but not whether a mutation occurred.
            result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, {"status_code": exc.code}, reason="http_error_after_dispatch")
        except (URLError, socket.timeout, TimeoutError, OSError) as exc:
            result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=f"transport_ambiguous:{type(exc).__name__}")
        except (KeyError, TypeError, ValueError) as exc:
            result = ExecutionResult(ExecutionStatus.FAILED, reason=f"invalid_request:{type(exc).__name__}:{exc}")
        self._results[request.idempotency_key] = (fingerprint, result)
        return result

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.username or parsed.password or parsed.fragment:
            raise ValueError("userinfo and fragments are prohibited")
        if parsed.scheme not in ({"https", "http"} if self.allow_insecure_http else {"https"}):
            raise ValueError("insecure or unsupported scheme")
        origin = self._normalize_origin(url)
        if origin not in self.allowed_origins:
            raise ValueError("origin is not allow-listed")

    @staticmethod
    def _normalize_origin(value: str) -> str:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("origin must include scheme and host")
        default_port = 443 if parsed.scheme == "https" else 80
        port = parsed.port or default_port
        return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}:{port}"

    @staticmethod
    def _fingerprint(request: ExecutionRequest) -> str:
        import hashlib

        canonical = json.dumps(
            {"operation_id": request.operation_id, "action": request.action, "parameters": dict(request.parameters)},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
