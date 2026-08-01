# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from pathlib import Path

import pytest

from rpr import (
    ActionClass, EnvironmentTrust, ExecutionRequest, ExecutionStatus, LocalFileExecutor,
    PathwayDefinition, PathwayState, Principal, RedactionPolicy, ResponsibilityPathwayRuntime,
    StaticActorBinding, TrustedPrincipalResolver,
)
from rpr.authority import AuthorityError
from rpr.redaction import EvidenceLimitError
from rpr.rpe import AllowAllDevelopmentEvaluator


def definition(pathway_id: str, action_class: ActionClass = ActionClass.SUGGEST_ONLY) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id, action_name="replace_text_file", action_class=action_class,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL, decision_owner="owner",
        approval_authority="approver" if action_class is not ActionClass.SUGGEST_ONLY else None,
        execution_actor="file-agent", stop_authority="operator", evidence_owner="audit",
        repair_owner="repair-team", resume_authority="manager", human_return_point="before-write",
        residual_owner="owner",
    )


def test_principal_binding_authorizes_declared_approval():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition("principal", ActionClass.APPROVAL_REQUIRED), idempotency_key="p-1")
    principal = Principal(subject="alice", issuer="corp-idp", authentication_method="oidc")
    binding = StaticActorBinding({("corp-idp", "alice"): "approver"})
    state = runtime.transition_as_principal("principal", PathwayState.APPROVED, credential=principal, resolver=TrustedPrincipalResolver(), binding=binding, reason="reviewed")
    assert state is PathwayState.APPROVED
    assert runtime.verify_evidence("principal").valid


def test_evidence_payload_redacts_nested_secrets():
    policy = RedactionPolicy()
    value = policy.redact({"headers": {"Authorization": "Bearer secret"}, "token": "abc", "safe": "ok"})
    assert value["headers"]["Authorization"] == "[REDACTED]"
    assert value["token"] == "[REDACTED]"
    assert value["safe"] == "ok"


def test_evidence_payload_limits_are_enforced():
    with pytest.raises(EvidenceLimitError):
        RedactionPolicy(max_string_length=3).redact({"value": "four"})


def test_local_file_executor_completes_only_after_readback(tmp_path: Path):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition("file-success"), idempotency_key="reg-success")
    request = ExecutionRequest(operation_id="op-1", attempt_id="attempt-1", idempotency_key="write-1", action="replace_text_file", parameters={"path": "docs/result.txt", "content": "hello"})
    result = runtime.execute("file-success", request, actor="file-agent", executor=LocalFileExecutor(tmp_path))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.readback and result.readback.verified
    assert runtime.store.get_state("file-success") is PathwayState.COMPLETED
    assert (tmp_path / "docs/result.txt").read_text() == "hello"


def test_unauthorized_actor_cannot_read_completed_replay(tmp_path: Path):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition("replay-completed"), idempotency_key="reg-replay-completed")
    request = ExecutionRequest(operation_id="op-replay", attempt_id="attempt-replay", idempotency_key="write-replay", action="replace_text_file", parameters={"path": "docs/replay.txt", "content": "done"})
    executor = LocalFileExecutor(tmp_path)

    result = runtime.execute("replay-completed", request, actor="file-agent", executor=executor)
    assert result.status is ExecutionStatus.SUCCEEDED
    evidence_before = runtime.evidence("replay-completed")

    with pytest.raises(AuthorityError, match="execution authority"):
        runtime.execute("replay-completed", request, actor="intruder", executor=executor)

    assert runtime.evidence("replay-completed") == evidence_before


def test_unauthorized_actor_cannot_observe_or_record_unresolved_replay(tmp_path: Path):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition("replay-unresolved"), idempotency_key="reg-replay-unresolved")
    request = ExecutionRequest(operation_id="op-unresolved", attempt_id="attempt-unresolved", idempotency_key="write-unresolved", action="replace_text_file", parameters={"path": "docs/unresolved.txt", "content": "unknown"})
    replayed, attempt = runtime.attempt_ledger.begin("replay-unresolved", request)
    assert replayed is False
    assert attempt.result_json is None
    evidence_before = runtime.evidence("replay-unresolved")

    with pytest.raises(AuthorityError, match="execution authority"):
        runtime.execute("replay-unresolved", request, actor="intruder", executor=LocalFileExecutor(tmp_path))

    assert runtime.evidence("replay-unresolved") == evidence_before
    assert runtime.attempt_ledger.get("attempt-unresolved").result_json is None


def test_path_escape_becomes_visible_unknown_write(tmp_path: Path):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition("file-escape"), idempotency_key="reg-escape")
    request = ExecutionRequest(operation_id="op-2", attempt_id="attempt-1", idempotency_key="write-2", action="replace_text_file", parameters={"path": "../escape.txt", "content": "no"})
    result = runtime.execute("file-escape", request, actor="file-agent", executor=LocalFileExecutor(tmp_path))
    assert result.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    assert runtime.store.get_state("file-escape") is PathwayState.WRITE_STATUS_UNKNOWN


def test_executor_idempotent_replay_and_conflict(tmp_path: Path):
    executor = LocalFileExecutor(tmp_path)
    first = ExecutionRequest(operation_id="op-3", attempt_id="a-1", idempotency_key="same", action="replace_text_file", parameters={"path": "x.txt", "content": "one"})
    assert executor.execute(first).status is ExecutionStatus.SUCCEEDED
    assert executor.execute(first).status is ExecutionStatus.SUCCEEDED
    conflict = ExecutionRequest(operation_id="op-3", attempt_id="a-2", idempotency_key="same", action="replace_text_file", parameters={"path": "x.txt", "content": "two"})
    assert executor.execute(conflict).reason == "idempotency_conflict"
