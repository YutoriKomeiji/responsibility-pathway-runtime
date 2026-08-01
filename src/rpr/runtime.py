# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .attempts import (
    AttemptResultPersistenceError,
    ExecutionAttemptRecord,
    SQLiteExecutionAttemptLedger,
)
from .authority import authorize_execution_access, authorize_reconciliation_access, authorize_transition
from .evidence import build_event, verify_chain
from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus, Executor, ReadbackEvidence
from .inspection import inspect_pathway
from .models import PathwayDefinition, PathwayState, RuntimeDecision
from .principal import ActorBinding, PrincipalResolver
from .reconciliation import ReconciliationStatus, ReconciliationStrategy
from .redaction import RedactionPolicy
from .rpe import RpeContractError, RpeEvaluator, UnavailableRpeEvaluator
from .state_machine import ensure_transition
from .storage import SQLiteStore


@dataclass(frozen=True)
class RegistrationResult:
    pathway_id: str
    state: PathwayState
    decision: RuntimeDecision
    reason_codes: tuple[str, ...]
    replayed: bool = False


@dataclass(frozen=True)
class EvidenceVerificationResult:
    valid: bool
    event_count: int
    failure_index: int | None = None
    reason: str | None = None


class ResponsibilityPathwayRuntime:
    def __init__(
        self,
        store: SQLiteStore | None = None,
        rpe: RpeEvaluator | None = None,
        redaction_policy: RedactionPolicy | None = None,
        attempt_ledger: SQLiteExecutionAttemptLedger | None = None,
    ) -> None:
        self.store = store or SQLiteStore()
        self.rpe = rpe or UnavailableRpeEvaluator()
        self.redaction_policy = redaction_policy or RedactionPolicy()
        self.attempt_ledger = attempt_ledger or SQLiteExecutionAttemptLedger()

    def register(self, definition: PathwayDefinition, *, idempotency_key: str) -> RegistrationResult:
        inspection = inspect_pathway(definition)
        action_request: dict[str, Any] = {"action": definition.action_name, "action_class": definition.action_class.value, "environment_trust": definition.environment_trust.value, "responsibility_pathway": definition.to_dict()}
        try:
            rpe_result = self.rpe.evaluate(action_request)
        except RpeContractError as exc:
            rpe_result_decision = RuntimeDecision.HUMAN_GATE
            rpe_reason_codes = ("rpe_contract_error", type(exc).__name__)
            rpe_raw: dict[str, Any] = {"error": str(exc)}
        else:
            rpe_result_decision = rpe_result.decision
            rpe_reason_codes = rpe_result.reason_codes
            rpe_raw = rpe_result.raw or {}
        combined = self._combine(inspection.decision, rpe_result_decision)
        state = self._initial_state(combined, definition.approval_authority is not None)
        replayed, persisted_state = self.store.create_or_replay_pathway(definition, state, idempotency_key)
        reason_codes = tuple(item.code for item in inspection.findings) + rpe_reason_codes
        if not replayed:
            self._record(definition.pathway_id, "pathway_registered", definition.decision_owner, {"inspection": inspection.to_dict(), "rpe": {"decision": rpe_result_decision.value, "reason_codes": list(rpe_reason_codes), "raw": rpe_raw}, "state": persisted_state.value, "idempotency_key": idempotency_key})
        return RegistrationResult(definition.pathway_id, persisted_state, combined, reason_codes, replayed)

    def transition(self, pathway_id: str, target: PathwayState, *, actor: str, reason: str) -> PathwayState:
        if target is PathwayState.RUNNING:
            raise ValueError(
                "RUNNING transitions require an execution or resume attempt binding; "
                "use execute() or RepairCoordinator.resume()"
            )
        current = self.store.get_state(pathway_id)
        definition = self.store.get_definition(pathway_id)
        ensure_transition(current, target)
        authorize_transition(definition, current, target, actor)
        event = build_event(pathway_id=pathway_id, event_type="state_transition", actor=actor, payload={"from": current.value, "to": target.value, "reason": reason}, previous_hash=self.store.latest_event_hash(pathway_id), redaction_policy=self.redaction_policy)
        self.store.transition_with_event(pathway_id, current, target, event)
        return target

    def transition_as_principal(self, pathway_id: str, target: PathwayState, *, credential: object, resolver: PrincipalResolver, binding: ActorBinding, reason: str) -> PathwayState:
        principal = resolver.resolve(credential)
        actor = binding.actor_for(principal)
        state = self.transition(pathway_id, target, actor=actor, reason=reason)
        self._record(pathway_id, "principal_authorized_transition", actor, {"issuer": principal.issuer, "subject": principal.subject, "authentication_method": principal.authentication_method, "target": target.value})
        return state

    def execute(self, pathway_id: str, request: ExecutionRequest, *, actor: str, executor: Executor) -> ExecutionResult:
        definition = self.store.get_definition(pathway_id)
        authorize_execution_access(definition, actor)

        current_before_begin = self.store.get_state(pathway_id)
        if current_before_begin is PathwayState.RUNNING:
            bound_attempt_id = self._active_running_attempt_id(pathway_id)
            if bound_attempt_id != request.attempt_id:
                raise ValueError(
                    f"running pathway is bound to attempt {bound_attempt_id!r}, got {request.attempt_id!r}"
                )

        replayed, attempt = self.attempt_ledger.begin(pathway_id, request)
        if replayed and attempt.result_json is not None:
            result = self._result_from_attempt(attempt)
            self._finish_execution_pathway(pathway_id, request, actor, result)
            return result
        if replayed:
            current = self.store.get_state(pathway_id)
            if current is PathwayState.APPROVED:
                if not self.attempt_ledger.discard_started(request.attempt_id):
                    raise RuntimeError("pre_dispatch_started_attempt_could_not_be_reset")
                replayed, attempt = self.attempt_ledger.begin(pathway_id, request)
                if replayed:
                    raise RuntimeError("pre_dispatch_started_attempt_reset_replayed")
                self._record(pathway_id, "execution_pre_dispatch_restart_recovered", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key})
            else:
                reason = "prior_attempt_started_without_persisted_result"
                if current is PathwayState.RUNNING:
                    self.transition(pathway_id, PathwayState.WRITE_STATUS_UNKNOWN, actor=actor, reason=reason)
                self._record(pathway_id, "execution_replay_unresolved", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "pathway_state": current.value})
                return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=reason)

        try:
            current = self.store.get_state(pathway_id)
            if current is PathwayState.APPROVED:
                self._start_execution_pathway(pathway_id, request, actor)
            elif current is not PathwayState.RUNNING:
                raise ValueError(f"pathway must be approved or running, got {current.value}")
        except Exception:
            try:
                persisted_state = self.store.get_state(pathway_id)
            except Exception:
                raise
            if persisted_state is not PathwayState.RUNNING:
                self.attempt_ledger.discard_started(request.attempt_id)
            raise

        try:
            result = executor.execute(request)
        except Exception as exc:
            result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=f"executor_exception:{type(exc).__name__}")

        try:
            self.attempt_ledger.finish(request.attempt_id, result)
        except AttemptResultPersistenceError as exc:
            reason = f"result_persistence_rejected:{type(exc).__name__}"
            fallback_persisted = True
            fallback_failure: str | None = None
            try:
                self.attempt_ledger.mark_result_persistence_unknown(request.attempt_id, reason=reason)
            except (sqlite3.Error, KeyError) as fallback_exc:
                fallback_persisted = False
                fallback_failure = type(fallback_exc).__name__
            uncertain_reason = reason
            if fallback_failure is not None:
                uncertain_reason = f"{reason}:fallback_persistence_failed:{fallback_failure}"
            uncertain = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason=uncertain_reason)
            self._record(pathway_id, "execution_result_persistence_unknown", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "reason": reason, "fallback_persisted": fallback_persisted, "fallback_failure": fallback_failure})
            self.transition(pathway_id, PathwayState.WRITE_STATUS_UNKNOWN, actor=actor, reason=uncertain_reason)
            return uncertain

        self._record(pathway_id, "execution_result", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "status": result.status.value, "evidence": dict(result.evidence), "readback": None if result.readback is None else {"verified": result.readback.verified, "observed": dict(result.readback.observed), "reason": result.readback.reason}, "reason": result.reason})
        self._finish_execution_pathway(pathway_id, request, actor, result)
        return result

    def _start_execution_pathway(self, pathway_id: str, request: ExecutionRequest, actor: str) -> None:
        current = self.store.get_state(pathway_id)
        target = PathwayState.RUNNING
        definition = self.store.get_definition(pathway_id)
        ensure_transition(current, target)
        authorize_transition(definition, current, target, actor)
        event = build_event(
            pathway_id=pathway_id,
            event_type="execution_started",
            actor=actor,
            payload={
                "from": current.value,
                "to": target.value,
                "operation_id": request.operation_id,
                "attempt_id": request.attempt_id,
                "idempotency_key": request.idempotency_key,
                "reason": "execution_started",
            },
            previous_hash=self.store.latest_event_hash(pathway_id),
            redaction_policy=self.redaction_policy,
        )
        self.store.transition_with_event(pathway_id, current, target, event)

    def _active_running_attempt_id(self, pathway_id: str) -> str:
        for event in reversed(self.store.events(pathway_id)):
            payload = event.get("payload", {})
            if payload.get("to") != PathwayState.RUNNING.value:
                continue
            if event.get("event_type") == "execution_started":
                attempt_id = payload.get("attempt_id")
            elif event.get("event_type") == "pathway_resumed":
                attempt_id = payload.get("next_attempt_id")
            else:
                attempt_id = None
            if isinstance(attempt_id, str) and attempt_id.strip():
                return attempt_id
            raise RuntimeError("running pathway has no durable attempt binding")
        raise RuntimeError("running pathway has no durable attempt binding")

    def _finish_execution_pathway(self, pathway_id: str, request: ExecutionRequest, actor: str, result: ExecutionResult) -> None:
        current = self.store.get_state(pathway_id)
        if result.status is ExecutionStatus.SUCCEEDED and result.readback is not None and result.readback.verified:
            target = PathwayState.COMPLETED
            reason = "executor_readback_verified"
            transition_actor = actor
        elif result.status is ExecutionStatus.FAILED:
            target = PathwayState.REPAIR_REQUIRED
            reason = result.reason or "executor_failed"
            transition_actor = self.store.get_definition(pathway_id).repair_owner
        else:
            if current is PathwayState.WRITE_STATUS_UNKNOWN:
                return
            self.transition(pathway_id, PathwayState.WRITE_STATUS_UNKNOWN, actor=actor, reason=result.reason or "executor_write_status_unknown")
            return

        if current is target:
            return
        if current is PathwayState.RUNNING:
            self.transition(pathway_id, target, actor=transition_actor, reason=reason)
            return
        if current is not PathwayState.WRITE_STATUS_UNKNOWN:
            raise ValueError(f"persisted execution result conflicts with pathway state {current.value}")

        ensure_transition(current, target)
        event = build_event(
            pathway_id=pathway_id,
            event_type="execution_result_after_concurrent_unknown",
            actor=actor,
            payload={
                "from": current.value,
                "to": target.value,
                "operation_id": request.operation_id,
                "attempt_id": request.attempt_id,
                "idempotency_key": request.idempotency_key,
                "status": result.status.value,
                "evidence": dict(result.evidence),
                "readback": None if result.readback is None else {"verified": result.readback.verified, "observed": dict(result.readback.observed), "reason": result.readback.reason},
                "reason": result.reason,
            },
            previous_hash=self.store.latest_event_hash(pathway_id),
            redaction_policy=self.redaction_policy,
        )
        self.store.transition_with_event(pathway_id, current, target, event)

    def reconcile(self, pathway_id: str, request: ExecutionRequest, *, actor: str, strategy: ReconciliationStrategy) -> ExecutionResult:
        """Observe and classify an uncertain persisted attempt without redispatch."""

        definition = self.store.get_definition(pathway_id)
        authorize_reconciliation_access(definition, actor)
        current = self.store.get_state(pathway_id)
        if current not in {PathwayState.WRITE_STATUS_UNKNOWN, PathwayState.COMPLETED, PathwayState.REPAIR_REQUIRED}:
            raise ValueError(f"pathway is not reconcilable, got {current.value}")

        replayed, attempt = self.attempt_ledger.begin(pathway_id, request)
        if not replayed:
            self.attempt_ledger.discard_started(request.attempt_id)
            raise ValueError("reconciliation requires an existing persisted attempt")

        if attempt.result_json is not None:
            persisted = self._result_from_attempt(attempt)
            if persisted.status is not ExecutionStatus.WRITE_STATUS_UNKNOWN:
                self._finish_reconciliation_pathway(pathway_id, request, actor, persisted, replayed=True)
                return persisted

        observed = strategy.reconcile(request, attempt)
        evidence = {"reconciliation": dict(observed.evidence)}
        if observed.status is ReconciliationStatus.VERIFIED_APPLIED:
            result = ExecutionResult(ExecutionStatus.SUCCEEDED, evidence, ReadbackEvidence(True, dict(observed.evidence), observed.reason), observed.reason)
            if not self._persist_reconciliation_result(pathway_id, request, actor, result):
                return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="reconciliation_result_persistence_rejected:AttemptResultPersistenceError")
            self._finish_reconciliation_pathway(pathway_id, request, actor, result, replayed=False)
            return result
        if observed.status is ReconciliationStatus.VERIFIED_NOT_APPLIED:
            result = ExecutionResult(ExecutionStatus.FAILED, evidence, ReadbackEvidence(True, dict(observed.evidence), observed.reason), observed.reason or "verified_not_applied")
            if not self._persist_reconciliation_result(pathway_id, request, actor, result):
                return ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, reason="reconciliation_result_persistence_rejected:AttemptResultPersistenceError")
            self._finish_reconciliation_pathway(pathway_id, request, actor, result, replayed=False)
            return result

        result = ExecutionResult(ExecutionStatus.WRITE_STATUS_UNKNOWN, evidence, ReadbackEvidence(False, dict(observed.evidence), observed.reason), observed.reason or "reconciliation_unresolved")
        self._record(pathway_id, "reconciliation_unresolved", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "evidence": dict(observed.evidence), "reason": result.reason})
        return result

    def _persist_reconciliation_result(self, pathway_id: str, request: ExecutionRequest, actor: str, result: ExecutionResult) -> bool:
        try:
            self.attempt_ledger.finish(request.attempt_id, result)
        except AttemptResultPersistenceError as exc:
            reason = f"reconciliation_result_persistence_rejected:{type(exc).__name__}"
            fallback_persisted = True
            fallback_failure: str | None = None
            try:
                self.attempt_ledger.mark_result_persistence_unknown(request.attempt_id, reason=reason)
            except (sqlite3.Error, KeyError) as fallback_exc:
                fallback_persisted = False
                fallback_failure = type(fallback_exc).__name__
            self._record(pathway_id, "reconciliation_result_persistence_unknown", actor, {"operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "reason": reason, "fallback_persisted": fallback_persisted, "fallback_failure": fallback_failure})
            return False
        return True

    def _finish_reconciliation_pathway(self, pathway_id: str, request: ExecutionRequest, actor: str, result: ExecutionResult, *, replayed: bool) -> None:
        current = self.store.get_state(pathway_id)
        target = PathwayState.COMPLETED if result.status is ExecutionStatus.SUCCEEDED else PathwayState.REPAIR_REQUIRED
        if current is target:
            return
        if current is not PathwayState.WRITE_STATUS_UNKNOWN:
            raise ValueError(f"persisted reconciliation result conflicts with pathway state {current.value}")
        ensure_transition(current, target)
        event = build_event(pathway_id=pathway_id, event_type="reconciliation_result", actor=actor, payload={"from": current.value, "to": target.value, "operation_id": request.operation_id, "attempt_id": request.attempt_id, "idempotency_key": request.idempotency_key, "status": result.status.value, "evidence": dict(result.evidence), "readback": None if result.readback is None else {"verified": result.readback.verified, "observed": dict(result.readback.observed), "reason": result.readback.reason}, "reason": result.reason, "replayed": replayed}, previous_hash=self.store.latest_event_hash(pathway_id), redaction_policy=self.redaction_policy)
        self.store.transition_with_event(pathway_id, current, target, event)

    def mark_write_unknown(self, pathway_id: str, *, actor: str, reason: str) -> PathwayState:
        return self.transition(pathway_id, PathwayState.WRITE_STATUS_UNKNOWN, actor=actor, reason=reason)

    def require_repair(self, pathway_id: str, *, actor: str, reason: str) -> PathwayState:
        return self.transition(pathway_id, PathwayState.REPAIR_REQUIRED, actor=actor, reason=reason)

    def evidence(self, pathway_id: str) -> list[dict[str, Any]]:
        return self.store.events(pathway_id)

    def verify_evidence(self, pathway_id: str) -> EvidenceVerificationResult:
        events = self.evidence(pathway_id)
        valid, index, reason = verify_chain(events)
        return EvidenceVerificationResult(valid, len(events), index, reason)

    def _record(self, pathway_id: str, event_type: str, actor: str, payload: dict[str, Any]) -> None:
        self.store.append_event(build_event(pathway_id=pathway_id, event_type=event_type, actor=actor, payload=payload, previous_hash=self.store.latest_event_hash(pathway_id), redaction_policy=self.redaction_policy))

    @staticmethod
    def _result_from_attempt(attempt: ExecutionAttemptRecord) -> ExecutionResult:
        assert attempt.result_json is not None
        value = attempt.result_json
        readback_value = value.get("readback")
        readback = None if readback_value is None else ReadbackEvidence(bool(readback_value.get("verified")), dict(readback_value.get("observed", {})), readback_value.get("reason"))
        return ExecutionResult(ExecutionStatus(str(value["status"])), dict(value.get("evidence", {})), readback, value.get("reason"))

    @staticmethod
    def _combine(left: RuntimeDecision, right: RuntimeDecision) -> RuntimeDecision:
        order = {RuntimeDecision.ALLOW: 0, RuntimeDecision.HOLD: 1, RuntimeDecision.HUMAN_GATE: 2, RuntimeDecision.DENY: 3}
        return left if order[left] >= order[right] else right

    @staticmethod
    def _initial_state(decision: RuntimeDecision, approval_configured: bool) -> PathwayState:
        if decision is RuntimeDecision.DENY:
            return PathwayState.DENIED
        if decision is RuntimeDecision.HUMAN_GATE:
            return PathwayState.HUMAN_GATE
        if decision is RuntimeDecision.HOLD:
            return PathwayState.HELD
        return PathwayState.AWAITING_APPROVAL if approval_configured else PathwayState.APPROVED
