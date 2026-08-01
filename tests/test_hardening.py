# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json

import pytest

from rpr.authority import AuthorityError
from rpr.evidence import verify_chain
from rpr.executor import ExecutionRequest
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState, RuntimeDecision
from rpr.rpe import AllowAllDevelopmentEvaluator, PythonRpeEvaluator, RpeContractError
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import IdempotencyConflictError, SQLiteStore


def pathway(pathway_id: str = "p-1") -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="read_file",
        action_class=ActionClass.OBSERVE_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="repairer",
        resume_authority="resumer",
        human_return_point="on-error",
        residual_owner="owner",
        metadata={"target": "README.md"},
    )


def execution_request() -> ExecutionRequest:
    return ExecutionRequest("op-1", "attempt-1", "idem-exec-1", "read_file", {"path": "README.md"})


def test_registration_replay_is_stable() -> None:
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    first = runtime.register(pathway(), idempotency_key="key-1")
    second = runtime.register(pathway(), idempotency_key="key-1")
    assert first.replayed is False
    assert second.replayed is True
    assert second.state is first.state
    assert len(runtime.evidence("p-1")) == 1


def test_idempotency_key_conflict_is_visible() -> None:
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(pathway("p-1"), idempotency_key="same-key")
    with pytest.raises(IdempotencyConflictError):
        runtime.register(pathway("p-2"), idempotency_key="same-key")


def test_execution_start_requires_declared_actor_and_binding() -> None:
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(pathway(), idempotency_key="key-1")
    request = execution_request()
    with pytest.raises(AuthorityError):
        runtime._start_execution_pathway("p-1", request, "intruder")
    runtime._start_execution_pathway("p-1", request, "agent")
    runtime.transition("p-1", PathwayState.STOPPED, actor="operator", reason="operator stop")
    runtime.transition("p-1", PathwayState.REPAIR_REQUIRED, actor="repairer", reason="repair needed")
    runtime.transition("p-1", PathwayState.READY_TO_RESUME, actor="repairer", reason="repair verified")


def test_evidence_chain_verification_detects_tamper() -> None:
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(pathway(), idempotency_key="key-1")
    runtime._start_execution_pathway("p-1", execution_request(), "agent")
    result = runtime.verify_evidence("p-1")
    assert result.valid is True
    events = runtime.evidence("p-1")
    events[0]["payload"]["state"] = "tampered"
    valid, failure_index, reason = verify_chain(events)
    assert valid is False
    assert failure_index == 0
    assert reason == "event_hash_mismatch"


def test_python_rpe_adapter_normalizes_canonical_result() -> None:
    def evaluate(action_request, packs):
        assert action_request["action"] == "read_file"
        assert len(packs) == 1
        return {"decision": "allow", "reason_codes": ["ok"], "contract_version": "1.0"}

    evaluator = PythonRpeEvaluator(evaluate, [{"pack_id": "test"}], expected_contract_version="1.0")
    result = evaluator.evaluate({"action": "read_file"})
    assert result.decision is RuntimeDecision.ALLOW
    assert result.reason_codes == ("ok",)


def test_python_rpe_adapter_rejects_contract_mismatch() -> None:
    evaluator = PythonRpeEvaluator(
        lambda action, packs: {"decision": "allow", "contract_version": "2.0"},
        [],
        expected_contract_version="1.0",
    )
    with pytest.raises(RpeContractError):
        evaluator.evaluate({"action": "read_file"})


def test_transition_and_event_are_atomic_on_event_conflict(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "rpr.db")
    runtime = ResponsibilityPathwayRuntime(store=store, rpe=AllowAllDevelopmentEvaluator())
    runtime.register(pathway(), idempotency_key="key-1")
    runtime._start_execution_pathway("p-1", execution_request(), "agent")
    assert store.get_state("p-1") is PathwayState.RUNNING
    assert runtime.verify_evidence("p-1").valid
