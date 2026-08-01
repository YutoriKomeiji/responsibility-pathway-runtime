# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections import deque

import pytest

from rpr.mcp_subprocess_lifecycle import (
    McpProcessLifecycleError,
    McpSubprocessLifecycle,
)


class FakeProcess:
    def __init__(self, waits: list[object]) -> None:
        self.waits = deque(waits)
        self.calls: list[object] = []
        self.close_pipes_error: Exception | None = None

    def close_stdin(self) -> None:
        self.calls.append("close_stdin")

    def wait(self, timeout_seconds: float) -> int:
        self.calls.append(("wait", timeout_seconds))
        outcome = self.waits.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome  # type: ignore[return-value]

    def terminate(self) -> None:
        self.calls.append("terminate")

    def kill(self) -> None:
        self.calls.append("kill")

    def close_pipes(self) -> None:
        self.calls.append("close_pipes")
        if self.close_pipes_error is not None:
            raise self.close_pipes_error


def test_graceful_shutdown_closes_stdin_waits_and_closes_pipes() -> None:
    process = FakeProcess([0])
    lifecycle = McpSubprocessLifecycle(process)

    result = lifecycle.shutdown()

    assert result.exit_code == 0
    assert result.successful is True
    assert result.graceful is True
    assert result.terminated is False
    assert result.killed is False
    assert process.calls == ["close_stdin", ("wait", 5.0), "close_pipes"]


def test_timeout_escalates_to_terminate() -> None:
    process = FakeProcess([TimeoutError(), 143])
    lifecycle = McpSubprocessLifecycle(process)

    result = lifecycle.shutdown()

    assert result.exit_code == 143
    assert result.graceful is False
    assert result.terminated is True
    assert result.killed is False
    assert process.calls == [
        "close_stdin",
        ("wait", 5.0),
        "terminate",
        ("wait", 2.0),
        "close_pipes",
    ]


def test_second_timeout_escalates_to_kill() -> None:
    process = FakeProcess([TimeoutError(), TimeoutError(), -9])
    lifecycle = McpSubprocessLifecycle(process)

    result = lifecycle.shutdown()

    assert result.exit_code == -9
    assert result.graceful is False
    assert result.terminated is True
    assert result.killed is True
    assert process.calls == [
        "close_stdin",
        ("wait", 5.0),
        "terminate",
        ("wait", 2.0),
        "kill",
        ("wait", 2.0),
        "close_pipes",
    ]


def test_process_that_survives_kill_fails_closed_and_still_closes_pipes() -> None:
    process = FakeProcess([TimeoutError(), TimeoutError(), TimeoutError()])
    lifecycle = McpSubprocessLifecycle(process)

    with pytest.raises(McpProcessLifecycleError, match="did not exit after kill"):
        lifecycle.shutdown()

    assert process.calls[-1] == "close_pipes"


def test_cleanup_failure_prevents_success_result() -> None:
    process = FakeProcess([0])
    process.close_pipes_error = OSError("close failed")
    lifecycle = McpSubprocessLifecycle(process)

    with pytest.raises(McpProcessLifecycleError, match="failed to close process pipes"):
        lifecycle.shutdown()


def test_shutdown_result_is_idempotent_after_success() -> None:
    process = FakeProcess([7])
    lifecycle = McpSubprocessLifecycle(process)

    first = lifecycle.shutdown()
    second = lifecycle.shutdown()

    assert first is second
    assert first.successful is False
    assert process.calls == ["close_stdin", ("wait", 5.0), "close_pipes"]


def test_invalid_exit_code_fails_closed() -> None:
    process = FakeProcess([True])
    lifecycle = McpSubprocessLifecycle(process)

    with pytest.raises(McpProcessLifecycleError, match="non-integer exit code"):
        lifecycle.shutdown()
    assert process.calls[-1] == "close_pipes"


@pytest.mark.parametrize("value", [0, -1, True, "5"])
def test_timeout_configuration_must_be_positive_number(value: object) -> None:
    process = FakeProcess([0])
    with pytest.raises(ValueError):
        McpSubprocessLifecycle(process, graceful_timeout_seconds=value)  # type: ignore[arg-type]
