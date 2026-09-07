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


class ResponsibilityRouteClass(StrEnum):
    CONTINUE_AUTONOMOUSLY = "continue_autonomously"
    AI_RESOLVE_WITHIN_DELEGATION = "ai_resolve_within_delegation"
    HOLD_FOR_RECONCILIATION = "hold_for_reconciliation"
    BOUNDED_HUMAN_RETURN = "bounded_human_return"
    STOP_AND_PRESERVE_RESIDUE = "stop_and_preserve_residue"


class ReceiverEligibility(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    REQUIRES_REEVALUATION = "requires_reevaluation"


@dataclass(frozen=True)
class ResponsibilityRoute:
    route_class: ResponsibilityRouteClass
    source_holder: str
    destination: str
    receiver_eligibility: ReceiverEligibility
    authority_class: str
    delegation_scope: str
    unresolved_payload: tuple[str, ...]
    allowed_next_actions: tuple[str, ...]
    closure_condition: str
    reevaluation_condition: str
    residual_owner: str
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["route_class"] = self.route_class.value
        value["receiver_eligibility"] = self.receiver_eligibility.value
        value["unresolved_payload"] = list(self.unresolved_payload)
        value["allowed_next_actions"] = list(self.allowed_next_actions)
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ResponsibilityRoute":
        return cls(
            route_class=ResponsibilityRouteClass(value["route_class"]),
            source_holder=str(value["source_holder"]),
            destination=str(value["destination"]),
            receiver_eligibility=ReceiverEligibility(value["receiver_eligibility"]),
            authority_class=str(value["authority_class"]),
            delegation_scope=str(value["delegation_scope"]),
            unresolved_payload=tuple(str(item) for item in value.get("unresolved_payload", [])),
            allowed_next_actions=tuple(str(item) for item in value.get("allowed_next_actions", [])),
            closure_condition=str(value["closure_condition"]),
            reevaluation_condition=str(value["reevaluation_condition"]),
            residual_owner=str(value["residual_owner"]),
            expires_at=None if value.get("expires_at") is None else str(value["expires_at"]),
        )


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
    responsibility_route: ResponsibilityRoute | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["action_class"] = self.action_class.value
        value["environment_trust"] = self.environment_trust.value
        if self.responsibility_route is None:
            value.pop("responsibility_route", None)
        else:
            value["responsibility_route"] = self.responsibility_route.to_dict()
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PathwayDefinition":
        route_value = value.get("responsibility_route")
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
            responsibility_route=None if route_value is None else ResponsibilityRoute.from_dict(route_value),
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
