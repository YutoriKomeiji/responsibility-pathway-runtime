# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.diagnostics import diagnose_pathway
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class FailedExecutor:
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            ExecutionStatus.FAILED,
            evidence={"attempt_id": request.attempt_id},
            reason="precondition_failed",
        )


def runtime_for(tmp_path) -> ResponsibilityPathwayRuntime:
    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(tmp_path / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(tmp_path / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    runtime.register(
        PathwayDefinition(
            pathway_id="p-diagnostic",
            action_name="external_mutation",
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
            decision_owner="owner",
            approval_authority="reviewer",
            execution_actor="agent",
            stop_authority="operator",
            evidence_owner="audit",
            repair_owner="support",
            resume_authority="manager",
            human_return_point="before_retry",
            residual_owner="owner",
        ),
        idempotency_key="register-diagnostic",
    )
    return runtime


def test_diagnostic_identifies_approval_handoff(tmp_path) -> None:
    runtime = runtime_for(tmp_path)

    diagnostic = diagnose_pathway(runtime, "p-diagnostic")

    assert diagnostic.state is PathwayState.AWAITING_APPROVAL
    assert diagnostic.next_required_authority == "reviewer"
    assert diagnostic.next_required_action == "approve_or_deny"
    assert diagnostic.active_attempt_id is None
    assert diagnostic.latest_event_type == "pathway_registered"
    assert diagnostic.evidence_valid
    assert diagnostic.to_dict()["state"] == "awaiting_approval"


def test_diagnostic_exposes_running_attempt_binding(tmp_path) -> None:
    runtime = runtime_for(tmp_path)
    runtime.transition("p-diagnostic", PathwayState.APPROVED, actor="reviewer", reason="approved")
    request = ExecutionRequest(
        "op-diagnostic",
        "attempt-diagnostic",
        "idem-diagnostic",
        "external_mutation",
        {"value": 1},
    )
    runtime.attempt_ledger.begin("p-diagnostic", request)
    runtime._start_execution_pathway("p-diagnostic", request, "agent")

    diagnostic = diagnose_pathway(runtime, "p-diagnostic")

    assert diagnostic.state is PathwayState.RUNNING
    assert diagnostic.next_required_authority == "agent"
    assert diagnostic.next_required_action == "monitor_active_attempt"
    assert diagnostic.active_attempt_id == "attempt-diagnostic"
    assert diagnostic.latest_event_type == "execution_started"
    assert diagnostic.evidence_valid


def test_diagnostic_routes_failed_attempt_to_repair_owner(tmp_path) -> None:
    runtime = runtime_for(tmp_path)
    runtime.transition("p-diagnostic", PathwayState.APPROVED, actor="reviewer", reason="approved")
    request = ExecutionRequest(
        "op-failed",
        "attempt-failed",
        "idem-failed",
        "external_mutation",
        {"value": 1},
    )
    runtime.execute("p-diagnostic", request, actor="agent", executor=FailedExecutor())

    diagnostic = diagnose_pathway(runtime, "p-diagnostic")

    assert diagnostic.state is PathwayState.REPAIR_REQUIRED
    assert diagnostic.next_required_authority == "support"
    assert diagnostic.next_required_action == "repair_failed_attempt"
    assert diagnostic.active_attempt_id is None
    assert diagnostic.evidence_valid
    assert diagnostic.evidence_event_count == len(runtime.evidence("p-diagnostic"))
