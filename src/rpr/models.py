# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ActionClass(StrEnum):
    OBSERVE_ONLY = "observe_only"
    SUGGEST_ONLY = "suggest_only"
    APPROVAL_REQUIRED = "approval_required"
    REVERSIBLE_EXTERNAL = "reversible_external"
    HIGH_IMPACT = "high_impact"
    EMERGENCY_STOP = "emergency_stop"


class EnvironmentTrust(StrEnum):
    TRUSTED_INTERNAL = "trusted_internal"
    SEMI_TRUSTED = "semi_trusted"
    UNTRUSTED_PUBLIC = "untrusted_public"
    ADVERSARIAL = "adversarial"


class PathwayState(StrEnum):
    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    HELD = "held"
    HUMAN_GATE = "human_gate"
    STOPPED = "stopped"
    PARTIALLY_COMPLETED = "partially_completed"
    WRITE_STATUS_UNKNOWN = "write_status_unknown"
    REPAIR_REQUIRED = "repair_required"
    READY_TO_RESUME = "ready_to_resume"
    COMPLETED = "completed"
    DENIED = "denied"
    ABORTED = "aborted"


class RuntimeDecision(StrEnum):
    ALLOW = "allow"
    HOLD = "hold"
    HUMAN_GATE = "human_gate"
    DENY = "deny"


@dataclass(frozen=True)
class PathwayDefinition:
    pathway_id: str
    action_name: str
    action_class: ActionClass
    environment_trust: EnvironmentTrust
    decision_owner: str
    approval_authority: str | None
    execution_actor: str
    stop_authority: str
    evidence_owner: str
    repair_owner: str
    resume_authority: str
    human_return_point: str
    residual_owner: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PathwayDefinition":
        return cls(
            pathway_id=str(value["pathway_id"]),
            action_name=str(value["action_name"]),
            action_class=ActionClass(value["action_class"]),
            environment_trust=EnvironmentTrust(value["environment_trust"]),
            decision_owner=str(value["decision_owner"]),
            approval_authority=value.get("approval_authority"),
            execution_actor=str(value["execution_actor"]),
            stop_authority=str(value["stop_authority"]),
            evidence_owner=str(value["evidence_owner"]),
            repair_owner=str(value["repair_owner"]),
            resume_authority=str(value["resume_authority"]),
            human_return_point=str(value["human_return_point"]),
            residual_owner=str(value["residual_owner"]),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class InspectionResult:
    valid: bool
    decision: RuntimeDecision
    findings: tuple[ValidationFinding, ...]
    human_return_available: bool
    degradation_mode: str
    next_required_authority: str | None = None
    next_required_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "decision": self.decision.value,
            "findings": [asdict(item) for item in self.findings],
            "human_return_available": self.human_return_available,
            "degradation_mode": self.degradation_mode,
            "next_required_authority": self.next_required_authority,
            "next_required_action": self.next_required_action,
        }
