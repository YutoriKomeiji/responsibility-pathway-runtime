# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import pytest

from rpr.authority import AuthorityError
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus, LocalFileExecutor
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


def definition():
    return PathwayDefinition(pathway_id="p-runtime", action_name="replace_text_file", action_class=ActionClass.SUGGEST_ONLY, environment_trust=EnvironmentTrust.TRUSTED_INTERNAL, decision_owner="owner", approval_authority=None, execution_actor="agent", stop_authority="operator", evidence_owner="audit", repair_owner="support", resume_authority="manager", human_return_point="before_write", residual_owner="owner")


class UnknownExecutor:
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        del request
        return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="timeout")


def test_runtime_persists_state_and_hash_chained_evidence(tmp_path):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    result = runtime.register(definition(), idempotency_key="idem-1")
    assert result.state is PathwayState.APPROVED
    request = ExecutionRequest(
        "operation-runtime",
        "attempt-runtime",
        "execution-idem-runtime",
        "replace_text_file",
        {"path": "result.txt", "content": "verified\n"},
    )
    execution = runtime.execute(
        "p-runtime",
        request,
        actor="agent",
        executor=LocalFileExecutor(tmp_path),
    )
    assert execution.status is ExecutionStatus.SUCCEEDED
    assert runtime.store.get_state("p-runtime") is PathwayState.COMPLETED
    events = runtime.evidence("p-runtime")
    assert any(event["event_type"] == "execution_started" for event in events)
    assert all(
        event["previous_hash"] == events[index - 1]["event_hash"]
        for index, event in enumerate(events[1:], start=1)
    )


def test_generic_transition_cannot_create_unbound_running_state():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(), idempotency_key="idem-running-boundary")
    before = runtime.evidence("p-runtime")

    with pytest.raises(ValueError, match="execution or resume attempt binding"):
        runtime.transition("p-runtime", PathwayState.RUNNING, actor="agent", reason="manual start")

    assert runtime.store.get_state("p-runtime") is PathwayState.APPROVED
    assert runtime.evidence("p-runtime") == before
    assert runtime.verify_evidence("p-runtime").valid


def test_unknown_write_cannot_be_marked_completed_by_generic_transition():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(), idempotency_key="idem-2")
    request = ExecutionRequest(
        "operation-unknown",
        "attempt-unknown",
        "execution-idem-unknown",
        "replace_text_file",
        {"path": "unknown.txt", "content": "unknown\n"},
    )
    result = runtime.execute("p-runtime", request, actor="agent", executor=UnknownExecutor())
    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert runtime.store.get_state("p-runtime") is PathwayState.WRITE_STATUS_UNKNOWN
    with pytest.raises(AuthorityError, match="requires reconciliation authority and evidence"):
        runtime.transition("p-runtime", PathwayState.COMPLETED, actor="agent", reason="guess")


def test_default_rpe_unavailable_fails_to_human_gate():
    runtime = ResponsibilityPathwayRuntime()
    result = runtime.register(definition(), idempotency_key="idem-3")
    assert result.state is PathwayState.HUMAN_GATE
    assert "rpe_unavailable" in result.reason_codes
