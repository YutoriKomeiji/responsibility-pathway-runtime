# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Protocol

from .attempts import ExecutionAttemptRecord, SQLiteExecutionAttemptLedger
from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus, ReadbackEvidence


class ReconciliationStatus(StrEnum):
    VERIFIED_APPLIED = "verified_applied"
    VERIFIED_NOT_APPLIED = "verified_not_applied"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class ReconciliationResult:
    status: ReconciliationStatus
    evidence: Mapping[str, object]
    reason: str | None = None


class ReconciliationStrategy(Protocol):
    def reconcile(self, request: ExecutionRequest, attempt: ExecutionAttemptRecord) -> ReconciliationResult: ...


def reconcile_started_attempt(
    *,
    pathway_id: str,
    request: ExecutionRequest,
    ledger: SQLiteExecutionAttemptLedger,
    strategy: ReconciliationStrategy,
) -> ExecutionResult:
    replayed, attempt = ledger.begin(pathway_id, request)
    if not replayed or attempt.result_json is not None:
        raise ValueError("reconciliation requires an unresolved persisted attempt")
    observed = strategy.reconcile(request, attempt)
    if observed.status is ReconciliationStatus.VERIFIED_APPLIED:
        result = ExecutionResult(
            ExecutionStatus.SUCCEEDED,
            {"reconciliation": dict(observed.evidence)},
            ReadbackEvidence(True, dict(observed.evidence), observed.reason),
            observed.reason,
        )
    elif observed.status is ReconciliationStatus.VERIFIED_NOT_APPLIED:
        result = ExecutionResult(
            ExecutionStatus.FAILED,
            {"reconciliation": dict(observed.evidence)},
            ReadbackEvidence(True, dict(observed.evidence), observed.reason),
            observed.reason or "verified_not_applied",
        )
    else:
        result = ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            {"reconciliation": dict(observed.evidence)},
            ReadbackEvidence(False, dict(observed.evidence), observed.reason),
            observed.reason or "reconciliation_unresolved",
        )
    ledger.finish(request.attempt_id, result)
    return result
