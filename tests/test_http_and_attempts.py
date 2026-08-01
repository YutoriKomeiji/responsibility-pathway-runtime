# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from rpr import (
    ActionClass,
    AttemptConflictError,
    EnvironmentTrust,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    HttpMutationExecutor,
    JsonFieldReadback,
    PathwayDefinition,
    PathwayState,
    ReadbackEvidence,
    ResponsibilityPathwayRuntime,
    SQLiteExecutionAttemptLedger,
    SQLiteStore,
)
from rpr.rpe import AllowAllDevelopmentEvaluator


class _Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_POST(self):  # noqa: N802
        type(self).counter += 1
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        body = json.dumps({"id": payload["id"]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        del format, args


class _BlockingExecutor:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self._lock = threading.Lock()
        self.calls = 0

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        with self._lock:
            self.calls += 1
        self.entered.set()
        if not self.release.wait(timeout=5):
            raise TimeoutError("test executor was not released")
        return ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"attempt_id": request.attempt_id},
            ReadbackEvidence(True, {"applied": True}, "test readback verified"),
            "completed",
        )


@pytest.fixture
def http_server():
    _Handler.counter = 0
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _definition(pathway_id: str = "p-http") -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="http_json_mutation",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_dispatch",
        residual_owner="owner",
    )


def test_http_executor_requires_allowlist_and_readback(http_server):
    origin = f"http://127.0.0.1:{http_server.server_port}"
    executor = HttpMutationExecutor(
        allowed_origins={origin},
        readback=JsonFieldReadback("id", "expected_id"),
        allow_insecure_http=True,
    )
    request = ExecutionRequest(
        operation_id="op-http-1",
        attempt_id="attempt-http-1",
        idempotency_key="idem-http-1",
        action="http_json_mutation",
        parameters={"url": origin + "/items", "json": {"id": "x-1"}, "expected_id": "x-1"},
    )
    result = executor.execute(request)
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback is not None and result.readback.verified
    assert _Handler.counter == 1
    assert executor.execute(request).status is ExecutionStatus.SUCCEEDED
    assert _Handler.counter == 1


def test_http_executor_rejects_non_allowlisted_origin():
    executor = HttpMutationExecutor(
        allowed_origins={"https://api.example.com"},
        readback=JsonFieldReadback("id", "expected_id"),
    )
    request = ExecutionRequest("op", "attempt", "idem", "http_json_mutation", {"url": "https://evil.example/items", "json": {}, "expected_id": "x"})
    result = executor.execute(request)
    assert result.status is ExecutionStatus.FAILED
    assert "origin" in (result.reason or "")


def test_attempt_and_pathway_survive_runtime_recreation(tmp_path, http_server):
    origin = f"http://127.0.0.1:{http_server.server_port}"
    pathway_path = tmp_path / "pathways.sqlite3"
    ledger_path = tmp_path / "attempts.sqlite3"
    executor = HttpMutationExecutor(allowed_origins={origin}, readback=JsonFieldReadback("id", "expected_id"), allow_insecure_http=True)
    request = ExecutionRequest("op-persist", "attempt-persist", "idem-persist", "http_json_mutation", {"url": origin + "/items", "json": {"id": "p-1"}, "expected_id": "p-1"})

    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(pathway_path),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
    )
    runtime.register(_definition("p-persist"), idempotency_key="pathway-persist")
    first = runtime.execute("p-persist", request, actor="agent", executor=executor)
    assert first.status is ExecutionStatus.SUCCEEDED
    assert runtime.store.get_state("p-persist") is PathwayState.COMPLETED
    assert runtime.verify_evidence("p-persist").valid
    event_count = len(runtime.evidence("p-persist"))
    assert _Handler.counter == 1

    recreated = ResponsibilityPathwayRuntime(
        store=SQLiteStore(pathway_path),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
    )
    replay = recreated.execute("p-persist", request, actor="agent", executor=executor)
    assert replay.status is ExecutionStatus.SUCCEEDED
    assert recreated.store.get_state("p-persist") is PathwayState.COMPLETED
    assert recreated.verify_evidence("p-persist").valid
    assert len(recreated.evidence("p-persist")) == event_count
    assert _Handler.counter == 1


def test_attempt_identifier_conflict_is_visible(tmp_path):
    ledger = SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3")
    first = ExecutionRequest("op-1", "attempt-1", "idem-1", "x", {"value": 1})
    second = ExecutionRequest("op-2", "attempt-1", "idem-2", "x", {"value": 2})
    ledger.begin("p", first)
    with pytest.raises(AttemptConflictError):
        ledger.begin("p", second)


def test_independent_sqlite_runtimes_dispatch_same_attempt_at_most_once(tmp_path):
    pathway_path = tmp_path / "pathways.sqlite3"
    ledger_path = tmp_path / "attempts.sqlite3"
    setup = ResponsibilityPathwayRuntime(
        store=SQLiteStore(pathway_path),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
    )
    setup.register(_definition("p-concurrent"), idempotency_key="pathway-concurrent")
    request = ExecutionRequest(
        "op-concurrent",
        "attempt-concurrent",
        "idem-concurrent",
        "http_json_mutation",
        {"value": 1},
    )
    executor = _BlockingExecutor()

    def execute_from_independent_runtime() -> ExecutionResult:
        runtime = ResponsibilityPathwayRuntime(
            store=SQLiteStore(pathway_path),
            rpe=AllowAllDevelopmentEvaluator(),
            attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
        )
        return runtime.execute("p-concurrent", request, actor="agent", executor=executor)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(execute_from_independent_runtime)
        assert executor.entered.wait(timeout=5)
        second_future = pool.submit(execute_from_independent_runtime)
        second = second_future.result(timeout=5)
        assert second.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
        assert second.reason == "prior_attempt_started_without_persisted_result"
        assert executor.calls == 1
        executor.release.set()
        first = first_future.result(timeout=5)

    assert first.status is ExecutionStatus.SUCCEEDED
    verifier = ResponsibilityPathwayRuntime(
        store=SQLiteStore(pathway_path),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(ledger_path),
    )
    assert verifier.store.get_state("p-concurrent") is PathwayState.COMPLETED
    assert verifier.attempt_ledger.get(request.attempt_id).status == ExecutionStatus.SUCCEEDED.value
    event_count = len(verifier.evidence("p-concurrent"))
    replay = verifier.execute("p-concurrent", request, actor="agent", executor=executor)
    assert replay.status is ExecutionStatus.SUCCEEDED
    assert executor.calls == 1
    assert len(verifier.evidence("p-concurrent")) == event_count
    assert verifier.verify_evidence("p-concurrent").valid
