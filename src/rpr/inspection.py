# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from .models import (
    ActionClass,
    EnvironmentTrust,
    InspectionResult,
    PathwayDefinition,
    ReceiverEligibility,
    ResponsibilityRouteClass,
    RuntimeDecision,
    ValidationFinding,
)


def _inspect_responsibility_route(pathway: PathwayDefinition) -> list[ValidationFinding]:
    route = pathway.responsibility_route
    if route is None:
        return []

    findings: list[ValidationFinding] = []
    required = {
        "route_source_holder": route.source_holder,
        "route_destination": route.destination,
        "route_authority_class": route.authority_class,
        "route_delegation_scope": route.delegation_scope,
        "route_closure_condition": route.closure_condition,
        "route_reevaluation_condition": route.reevaluation_condition,
        "route_residual_owner": route.residual_owner,
    }
    for name, value in required.items():
        if not value.strip():
            findings.append(ValidationFinding(f"{name}_missing", f"{name} is required", "error"))

    if not route.allowed_next_actions:
        findings.append(
            ValidationFinding(
                "route_allowed_next_actions_missing",
                "A responsibility route must bound at least one allowed next action",
                "error",
            )
        )
    elif any(not action.strip() for action in route.allowed_next_actions):
        findings.append(
            ValidationFinding(
                "route_allowed_next_actions_blank",
                "Responsibility route actions must be non-empty",
                "error",
            )
        )

    if route.residual_owner != pathway.residual_owner:
        findings.append(
            ValidationFinding(
                "route_residual_owner_mismatch",
                "Responsibility routing must preserve the pathway residual owner unless ownership is explicitly redesigned",
                "error",
            )
        )

    if route.receiver_eligibility is ReceiverEligibility.INELIGIBLE:
        findings.append(
            ValidationFinding(
                "route_receiver_ineligible",
                "An ineligible receiver cannot be selected as the active responsibility route destination",
                "error",
            )
        )
    elif route.receiver_eligibility is ReceiverEligibility.REQUIRES_REEVALUATION:
        findings.append(
            ValidationFinding(
                "route_receiver_requires_reevaluation",
                "Receiver eligibility must be reevaluated before the route is relied on",
                "warning",
            )
        )

    if (
        route.route_class is ResponsibilityRouteClass.BOUNDED_HUMAN_RETURN
        and not pathway.human_return_point.strip()
    ):
        findings.append(
            ValidationFinding(
                "bounded_human_return_point_missing",
                "A bounded human-return route requires a concrete human return point",
                "error",
            )
        )

    return findings


def inspect_pathway(pathway: PathwayDefinition) -> InspectionResult:
    findings: list[ValidationFinding] = []
    required = {
        "pathway_id": pathway.pathway_id,
        "action_name": pathway.action_name,
        "decision_owner": pathway.decision_owner,
        "execution_actor": pathway.execution_actor,
        "stop_authority": pathway.stop_authority,
        "evidence_owner": pathway.evidence_owner,
        "repair_owner": pathway.repair_owner,
        "resume_authority": pathway.resume_authority,
        "human_return_point": pathway.human_return_point,
        "residual_owner": pathway.residual_owner,
    }
    for name, value in required.items():
        if not value.strip():
            findings.append(ValidationFinding(f"{name}_missing", f"{name} is required", "error"))

    findings.extend(_inspect_responsibility_route(pathway))

    approval_needed = pathway.action_class in {
        ActionClass.APPROVAL_REQUIRED,
        ActionClass.REVERSIBLE_EXTERNAL,
        ActionClass.HIGH_IMPACT,
    }
    if approval_needed and not (pathway.approval_authority or "").strip():
        findings.append(ValidationFinding("approval_authority_missing", "This action class requires an approval authority", "error"))

    if pathway.action_class is ActionClass.HIGH_IMPACT and pathway.stop_authority == pathway.execution_actor:
        findings.append(ValidationFinding("stop_execution_authority_not_separated", "High-impact actions should separate stop authority from execution actor", "error"))

    if pathway.environment_trust in {EnvironmentTrust.UNTRUSTED_PUBLIC, EnvironmentTrust.ADVERSARIAL}:
        findings.append(ValidationFinding("untrusted_environment", "Untrusted environments require an explicit human gate before external mutation", "warning"))

    errors = [item for item in findings if item.severity == "error"]
    next_authority: str | None
    next_action: str | None
    if errors:
        decision, degradation = RuntimeDecision.HUMAN_GATE, "stop_and_await"
        next_authority, next_action = pathway.decision_owner or None, "correct_pathway_definition"
    elif pathway.environment_trust is EnvironmentTrust.ADVERSARIAL:
        decision, degradation = RuntimeDecision.HOLD, "safe_only"
        next_authority, next_action = pathway.stop_authority, "review_adversarial_environment"
    elif pathway.action_class is ActionClass.HIGH_IMPACT:
        decision, degradation = RuntimeDecision.HUMAN_GATE, "limited"
        next_authority, next_action = pathway.approval_authority, "perform_explicit_human_review"
    elif approval_needed:
        decision, degradation = RuntimeDecision.ALLOW, "approval_pending"
        next_authority, next_action = pathway.approval_authority, "approve_or_deny"
    else:
        decision, degradation = RuntimeDecision.ALLOW, "full"
        next_authority, next_action = pathway.execution_actor, "execute_bounded_action"

    return InspectionResult(
        valid=not errors,
        decision=decision,
        findings=tuple(findings),
        human_return_available=bool(pathway.human_return_point.strip()),
        degradation_mode=degradation,
        next_required_authority=next_authority,
        next_required_action=next_action,
    )
