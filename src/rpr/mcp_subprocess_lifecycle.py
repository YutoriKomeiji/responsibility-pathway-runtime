# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .mcp_stable_transport import McpTransportError


class McpProcessLifecycleError(McpTransportError):
    """Raised when a bounded process lifecycle cannot be completed safely."""


class McpProcessHandle(Protocol):
    """Owned process resources below a future concrete subprocess adapter."""

    def close_stdin(self) -> None: ...

    def wait(self, timeout_seconds: float) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def close_pipes(self) -> None: ...


@dataclass(frozen=True)
class McpProcessExit:
    exit_code: int
    graceful: bool
    terminated: bool
    killed: bool

    @property
    def successful(self) -> bool:
        return self.exit_code == 0


class McpSubprocessLifecycle:
    """Single-owner, bounded shutdown contract for a future MCP subprocess.

    This class owns no OS process itself. A concrete adapter must provide the
    handle and remains responsible for platform-specific spawn and pipe I/O.
    """

    def __init__(
        self,
        handle: McpProcessHandle,
        *,
        graceful_timeout_seconds: float = 5.0,
        terminate_timeout_seconds: float = 2.0,
        kill_timeout_seconds: float = 2.0,
    ) -> None:
        self.handle = handle
        self.graceful_timeout_seconds = self._timeout(
            graceful_timeout_seconds, "graceful_timeout_seconds"
        )
        self.terminate_timeout_seconds = self._timeout(
            terminate_timeout_seconds, "terminate_timeout_seconds"
        )
        self.kill_timeout_seconds = self._timeout(
            kill_timeout_seconds, "kill_timeout_seconds"
        )
        self._result: McpProcessExit | None = None
        self._closing = False

    def shutdown(self) -> McpProcessExit:
        if self._result is not None:
            return self._result
        if self._closing:
            raise McpProcessLifecycleError("MCP process shutdown is already in progress")
        self._closing = True

        primary_error: BaseException | None = None
        result: McpProcessExit | None = None
        try:
            self._call("close stdin", self.handle.close_stdin)
            try:
                exit_code = self._wait(self.graceful_timeout_seconds)
                result = McpProcessExit(exit_code, True, False, False)
            except TimeoutError:
                self._call("terminate process", self.handle.terminate)
                try:
                    exit_code = self._wait(self.terminate_timeout_seconds)
                    result = McpProcessExit(exit_code, False, True, False)
                except TimeoutError:
                    self._call("kill process", self.handle.kill)
                    try:
                        exit_code = self._wait(self.kill_timeout_seconds)
                    except TimeoutError as exc:
                        raise McpProcessLifecycleError(
                            "MCP process did not exit after kill"
                        ) from exc
                    result = McpProcessExit(exit_code, False, True, True)
        except BaseException as exc:
            primary_error = exc
        finally:
            try:
                self._call("close process pipes", self.handle.close_pipes)
            except BaseException as cleanup_error:
                if primary_error is None:
                    primary_error = cleanup_error
            self._closing = False

        if primary_error is not None:
            if isinstance(primary_error, McpProcessLifecycleError):
                raise primary_error
            raise McpProcessLifecycleError(
                f"MCP process shutdown failed: {type(primary_error).__name__}: {primary_error}"
            ) from primary_error
        if result is None:
            raise McpProcessLifecycleError("MCP process shutdown produced no exit result")
        self._result = result
        return result

    def _wait(self, timeout_seconds: float) -> int:
        try:
            exit_code = self.handle.wait(timeout_seconds)
        except TimeoutError:
            raise
        except Exception as exc:
            raise McpProcessLifecycleError(
                f"MCP process wait failed: {type(exc).__name__}: {exc}"
            ) from exc
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            raise McpProcessLifecycleError("MCP process wait returned a non-integer exit code")
        return exit_code

    @staticmethod
    def _call(label: str, operation: object) -> None:
        try:
            operation()  # type: ignore[operator]
        except Exception as exc:
            raise McpProcessLifecycleError(
                f"failed to {label}: {type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _timeout(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        converted = float(value)
        if converted <= 0:
            raise ValueError(f"{name} must be positive")
        return converted
