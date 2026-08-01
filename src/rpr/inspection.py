# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from .models import ActionClass, EnvironmentTrust, InspectionResult, PathwayDefinition, RuntimeDecision, ValidationFinding


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
