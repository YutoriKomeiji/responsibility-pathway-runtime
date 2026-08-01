# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Protocol

from .executor import ExecutionRequest, ExecutionResult


class CompensationStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    PROPOSED = "proposed"
    REQUIRES_HUMAN_GATE = "requires_human_gate"


@dataclass(frozen=True)
class CompensationPlan:
    status: CompensationStatus
    request: ExecutionRequest | None = None
    reason: str | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)


class CompensationPlanner(Protocol):
    def propose(self, *, original_request: ExecutionRequest, original_result: ExecutionResult) -> CompensationPlan: ...


class NoAutomaticCompensation:
    """Safe default: compensation is never inferred or executed automatically."""

    def propose(self, *, original_request: ExecutionRequest, original_result: ExecutionResult) -> CompensationPlan:
        del original_request, original_result
        return CompensationPlan(
            CompensationStatus.REQUIRES_HUMAN_GATE,
            reason="compensating action requires explicit design and approval",
        )
