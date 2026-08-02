# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
# Language: Python
# Purpose: Run the same real-RPR demonstration under CPython CI and browser-hosted Pyodide.
# Boundary: The RPR runtime, SQLite stores, attempt ledger, evidence chain, and reconciliation are real.
#           Only the external payment provider is represented by a deterministic in-process adapter.
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rpr import (
    ActionClass,
    EnvironmentTrust,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    PathwayDefinition,
    PathwayState,
    ReconciliationResult,
    ReconciliationStatus,
    ResponsibilityPathwayRuntime,
    SQLiteExecutionAttemptLedger,
    SQLiteStore,
)
from rpr.rpe import AllowAllDevelopmentEvaluator

STATE_DIR = Path("/tmp/rpr-browser-demo")
PATHWAY_DB = STATE_DIR / "pathways.sqlite3"
ATTEMPT_DB = STATE_DIR / "attempts.sqlite3"
PATHWAY_ID = "browser-payment-timeout"
REQUEST = ExecutionRequest(
    operation_id="op-browser-payment",
    attempt_id="attempt-browser-payment-1",
    idempotency_key="idem-browser-payment-1",
    action="browser_payment_adapter",
    parameters={
        "payment_id": "pay-2026-0001",
        "amount": 125000,
        "currency": "JPY",
    },
)

_external_provider: dict[str, Any] = {
    "applied": False,
    "dispatch_count": 0,
    "payment_id": None,
}


def _definition() -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=PATHWAY_ID,
        action_name="browser_payment_adapter",
        action_class=ActionClass.HIGH_IMPACT,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="finance-owner",
        approval_authority="finance-approver",
        execution_actor="payment-agent",
        stop_authority="operations",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="finance-manager",
        human_return_point="before-payment-dispatch",
        residual_owner="finance-owner",
    )


def _runtime() -> ResponsibilityPathwayRuntime:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(PATHWAY_DB),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(ATTEMPT_DB),
    )


class TimeoutAfterAcceptanceExecutor:
    """Apply the external effect once, then return an ambiguous result."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        _external_provider["dispatch_count"] += 1
        _external_provider["applied"] = True
        _external_provider["payment_id"] = request.parameters["payment_id"]
        return ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            evidence={"adapter": "deterministic-browser-provider", "dispatch_accepted": True},
            reason="simulated_response_lost_after_provider_acceptance",
        )


class ProviderStateReconciliation:
    """Read provider state without redispatching the operation."""

    def reconcile(self, request: ExecutionRequest, attempt: object) -> ReconciliationResult:
        del attempt
        observed = {
            "payment_id": _external_provider["payment_id"],
            "applied": _external_provider["applied"],
            "dispatch_count": _external_provider["dispatch_count"],
        }
        if observed["applied"] and observed["payment_id"] == request.parameters["payment_id"]:
            return ReconciliationResult(
                ReconciliationStatus.VERIFIED_APPLIED,
                observed,
                "independent_provider_state_confirmed",
            )
        return ReconciliationResult(
            ReconciliationStatus.VERIFIED_NOT_APPLIED,
            observed,
            "provider_state_not_applied",
        )


def _remove_sqlite_family(path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        try:
            os.remove(candidate)
        except FileNotFoundError:
            pass


def reset_demo() -> dict[str, Any]:
    _remove_sqlite_family(PATHWAY_DB)
    _remove_sqlite_family(ATTEMPT_DB)
    _external_provider.update(applied=False, dispatch_count=0, payment_id=None)
    return {"step": "reset", "state": "not_registered", "provider": dict(_external_provider)}


def register_demo() -> dict[str, Any]:
    runtime = _runtime()
    registration = runtime.register(_definition(), idempotency_key="register-browser-payment")
    return {
        "step": "registered",
        "state": registration.state.value,
        "decision": registration.decision.value,
        "replayed": registration.replayed,
        "schema_version": runtime.store.schema_version,
        "evidence_valid": runtime.verify_evidence(PATHWAY_ID).valid,
        "events": runtime.store.events(PATHWAY_ID),
        "provider": dict(_external_provider),
    }


def approve_and_execute() -> dict[str, Any]:
    runtime = _runtime()
    if runtime.store.get_state(PATHWAY_ID) is not PathwayState.APPROVED:
        runtime.transition(
            PATHWAY_ID,
            PathwayState.APPROVED,
            actor="finance-approver",
            reason="invoice approved in browser demo",
        )
    result = runtime.execute(
        PATHWAY_ID,
        REQUEST,
        actor="payment-agent",
        executor=TimeoutAfterAcceptanceExecutor(),
    )
    return {
        "step": "ambiguous_write_persisted",
        "result_status": result.status.value,
        "state": runtime.store.get_state(PATHWAY_ID).value,
        "dispatch_count": _external_provider["dispatch_count"],
        "evidence_valid": runtime.verify_evidence(PATHWAY_ID).valid,
        "events": runtime.store.events(PATHWAY_ID),
        "provider": dict(_external_provider),
    }


def restart_and_reconcile() -> dict[str, Any]:
    restarted = _runtime()
    before = restarted.store.get_state(PATHWAY_ID).value
    reconciled = restarted.reconcile(
        PATHWAY_ID,
        REQUEST,
        actor="support",
        strategy=ProviderStateReconciliation(),
    )
    after = restarted.store.get_state(PATHWAY_ID).value
    return {
        "step": "restarted_and_reconciled",
        "state_before": before,
        "reconciliation_status": reconciled.status.value,
        "state": after,
        "dispatch_count": _external_provider["dispatch_count"],
        "duplicate_dispatch_prevented": _external_provider["dispatch_count"] == 1,
        "evidence_valid": restarted.verify_evidence(PATHWAY_ID).valid,
        "events": restarted.store.events(PATHWAY_ID),
        "provider": dict(_external_provider),
    }


def run_full_demo() -> dict[str, Any]:
    reset_demo()
    registered = register_demo()
    ambiguous = approve_and_execute()
    reconciled = restart_and_reconcile()
    return {"registered": registered, "ambiguous": ambiguous, "reconciled": reconciled}


def run_json(function_name: str) -> str:
    functions = {
        "reset_demo": reset_demo,
        "register_demo": register_demo,
        "approve_and_execute": approve_and_execute,
        "restart_and_reconcile": restart_and_reconcile,
        "run_full_demo": run_full_demo,
    }
    try:
        result = functions[function_name]()
        return json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True)
    except Exception as exc:  # demo boundary: return inspectable failure to the UI
        return json.dumps(
            {"ok": False, "error_type": type(exc).__name__, "error": str(exc)},
            ensure_ascii=False,
            sort_keys=True,
        )


if __name__ == "__main__":
    print(run_json("run_full_demo"))
