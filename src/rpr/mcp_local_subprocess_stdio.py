# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import selectors
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import BinaryIO

from .mcp_stdio_channel import McpStdioEvent
from .mcp_stable_transport import McpTransportError


class McpLocalSubprocessError(McpTransportError):
    """Raised when the bounded local subprocess stdio owner fails closed."""


class McpLocalSubprocessStdio:
    """Own a local, shell-free subprocess and its binary stdio pipes.

    The caller supplies an explicit argv and complete environment. Parent process
    environment variables are not inherited implicitly. This class provides no
    network, authentication, credential discovery, or remote process behavior.
    """

    def __init__(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str],
        cwd: str | Path | None = None,
        read_timeout_seconds: float = 5.0,
        read_size: int = 65536,
    ) -> None:
        self.argv = self._argv(argv)
        self.env = self._env(env)
        self.cwd = None if cwd is None else str(Path(cwd))
        self.read_timeout_seconds = self._positive_number(
            read_timeout_seconds, "read_timeout_seconds"
        )
        self.read_size = self._positive_int(read_size, "read_size")
        try:
            self.process = subprocess.Popen(
                self.argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
                env=self.env,
                shell=False,
                close_fds=True,
                bufsize=0,
            )
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"failed to spawn local MCP subprocess: {type(exc).__name__}: {exc}"
            ) from exc

        if self.process.stdin is None or self.process.stdout is None or self.process.stderr is None:
            self.process.kill()
            self.process.wait()
            raise McpLocalSubprocessError("local MCP subprocess did not expose all stdio pipes")

        self.stdin: BinaryIO = self.process.stdin
        self.stdout: BinaryIO = self.process.stdout
        self.stderr: BinaryIO = self.process.stderr
        self._selector = selectors.DefaultSelector()
        self._register(self.stdout, "stdout")
        self._register(self.stderr, "stderr")
        self._stdin_closed = False
        self._pipes_closed = False

    def write_stdin(self, data: bytes) -> int:
        if self._stdin_closed or self.stdin.closed:
            raise BrokenPipeError("local MCP subprocess stdin is closed")
        if not isinstance(data, bytes) or not data:
            raise McpLocalSubprocessError("stdin write requires non-empty bytes")
        try:
            written = self.stdin.write(data)
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"local MCP subprocess stdin write failed: {type(exc).__name__}: {exc}"
            ) from exc
        if written is None:
            raise McpLocalSubprocessError("local MCP subprocess stdin write returned no count")
        return written

    def read_event(self) -> McpStdioEvent:
        if self._pipes_closed:
            raise McpLocalSubprocessError("local MCP subprocess pipes are closed")
        events = self._selector.select(self.read_timeout_seconds)
        if not events:
            raise TimeoutError("local MCP subprocess stdio read timed out")
        key, _ = events[0]
        stream = str(key.data)
        pipe = key.fileobj
        try:
            data = os.read(pipe.fileno(), self.read_size)
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"local MCP subprocess {stream} read failed: {type(exc).__name__}: {exc}"
            ) from exc
        if data:
            return McpStdioEvent(stream=stream, data=data)
        self._selector.unregister(pipe)
        return McpStdioEvent(stream=stream, eof=True)

    def close_stdin(self) -> None:
        if self._stdin_closed:
            return
        self._stdin_closed = True
        try:
            self.stdin.close()
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"failed to close local MCP subprocess stdin: {type(exc).__name__}: {exc}"
            ) from exc

    def wait(self, timeout_seconds: float) -> int:
        timeout = self._positive_number(timeout_seconds, "timeout_seconds")
        try:
            return self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("local MCP subprocess wait timed out") from exc
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"local MCP subprocess wait failed: {type(exc).__name__}: {exc}"
            ) from exc

    def terminate(self) -> None:
        try:
            self.process.terminate()
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"local MCP subprocess terminate failed: {type(exc).__name__}: {exc}"
            ) from exc

    def kill(self) -> None:
        try:
            self.process.kill()
        except Exception as exc:
            raise McpLocalSubprocessError(
                f"local MCP subprocess kill failed: {type(exc).__name__}: {exc}"
            ) from exc

    def close_pipes(self) -> None:
        if self._pipes_closed:
            return
        self._pipes_closed = True
        errors: list[str] = []
        try:
            self._selector.close()
        except Exception as exc:
            errors.append(f"selector: {type(exc).__name__}: {exc}")
        for name, pipe in (("stdin", self.stdin), ("stdout", self.stdout), ("stderr", self.stderr)):
            if pipe.closed:
                continue
            try:
                pipe.close()
            except Exception as exc:
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
        if errors:
            raise McpLocalSubprocessError("failed to close local MCP subprocess pipes: " + "; ".join(errors))

    def _register(self, pipe: BinaryIO, stream: str) -> None:
        try:
            self._selector.register(pipe, selectors.EVENT_READ, stream)
        except Exception as exc:
            self.process.kill()
            self.process.wait()
            raise McpLocalSubprocessError(
                f"failed to register local MCP subprocess {stream}: {type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _argv(argv: Sequence[str]) -> tuple[str, ...]:
        if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence) or not argv:
            raise ValueError("argv must be a non-empty sequence of strings")
        result: list[str] = []
        for item in argv:
            if not isinstance(item, str) or not item or "\x00" in item:
                raise ValueError("argv entries must be non-empty strings without NUL")
            result.append(item)
        return tuple(result)

    @staticmethod
    def _env(env: Mapping[str, str]) -> dict[str, str]:
        if not isinstance(env, Mapping):
            raise ValueError("env must be a mapping of strings")
        result: dict[str, str] = {}
        for key, value in env.items():
            if not isinstance(key, str) or not key or "=" in key or "\x00" in key:
                raise ValueError("environment names must be non-empty strings without '=' or NUL")
            if not isinstance(value, str) or "\x00" in value:
                raise ValueError("environment values must be strings without NUL")
            result[key] = value
        return result

    @staticmethod
    def _positive_number(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        converted = float(value)
        if converted <= 0:
            raise ValueError(f"{name} must be positive")
        return converted

    @staticmethod
    def _positive_int(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value
