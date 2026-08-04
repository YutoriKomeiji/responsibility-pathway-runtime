# Language: Python
# Purpose: Provide a bounded, fail-closed Article 50 transparency assessment profile.
# Boundary: This module supports integrator controls and evidence; it does not provide legal advice or certify compliance.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class TerritorialScope(str, Enum):
    EU_IN_SCOPE = "eu_in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    UNRESOLVED = "unresolved"


class ActorRole(str, Enum):
    PROVIDER = "provider"
    DEPLOYER = "deployer"
    BOTH = "both"
    OTHER = "other"
    UNRESOLVED = "unresolved"


class SystemFunction(str, Enum):
    INTERACTIVE_AI = "interactive_ai"
    GENERATIVE_CONTENT = "generative_content"
    EMOTION_RECOGNITION = "emotion_recognition"
    BIOMETRIC_CATEGORISATION = "biometric_categorisation"
    OTHER = "other"
    UNRESOLVED = "unresolved"


class ContentModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"
    NONE = "none"
    UNRESOLVED = "unresolved"


class ContentContext(str, Enum):
    DEEPFAKE = "deepfake"
    PUBLIC_INTEREST_TEXT = "public_interest_text"
    ARTISTIC_OR_FICTIONAL = "artistic_or_fictional"
    ORDINARY_CONTENT = "ordinary_content"
    NONE = "none"
    UNRESOLVED = "unresolved"


class TransparencyOutcome(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    CONTROLS_REQUIRED = "controls_required"
    READY_FOR_HUMAN_GATE = "ready_for_human_gate"
    BLOCKED_UNRESOLVED = "blocked_unresolved"
    APPROVED_FOR_DECLARED_CONTEXT = "approved_for_declared_context"


@dataclass(frozen=True)
class Article50Assessment:
    assessment_id: str
    assessed_at: str
    legal_basis_version: str
    territorial_scope: TerritorialScope
    actor_role: ActorRole
    system_function: SystemFunction
    content_modality: ContentModality = ContentModality.NONE
    content_context: ContentContext = ContentContext.NONE
    human_review_completed: bool = False
    editorial_responsibility_owner: str | None = None
    interaction_disclosure_present: bool = False
    machine_readable_mark_present: bool = False
    visible_label_present: bool = False
    responsible_owner: str | None = None
    residual_uncertainty: str | None = None


@dataclass(frozen=True)
class Article50Decision:
    outcome: TransparencyOutcome
    interaction_disclosure_required: bool
    machine_readable_mark_required: bool
    visible_label_required: bool
    missing_evidence: tuple[str, ...]
    reasons: tuple[str, ...]
    human_gate_required: bool


def _is_provider(role: ActorRole) -> bool:
    return role in {ActorRole.PROVIDER, ActorRole.BOTH}


def _is_deployer(role: ActorRole) -> bool:
    return role in {ActorRole.DEPLOYER, ActorRole.BOTH}


def evaluate_article50(
    assessment: Article50Assessment,
    *,
    human_gate_approved: bool = False,
    human_gate_evidence: Iterable[str] = (),
) -> Article50Decision:
    """Evaluate declared Article 50 controls without making a legal determination."""

    reasons: list[str] = []
    missing: list[str] = []

    if not assessment.assessment_id.strip():
        raise ValueError("assessment_id must not be empty")
    if not assessment.assessed_at.strip():
        raise ValueError("assessed_at must not be empty")
    if not assessment.legal_basis_version.strip():
        raise ValueError("legal_basis_version must not be empty")

    unresolved = (
        assessment.territorial_scope is TerritorialScope.UNRESOLVED
        or assessment.actor_role is ActorRole.UNRESOLVED
        or assessment.system_function is SystemFunction.UNRESOLVED
        or assessment.content_modality is ContentModality.UNRESOLVED
        or assessment.content_context is ContentContext.UNRESOLVED
    )
    if unresolved:
        reasons.append("legal scope or classification is unresolved")
    if not assessment.responsible_owner:
        missing.append("responsible_owner")

    interaction_required = (
        assessment.territorial_scope is TerritorialScope.EU_IN_SCOPE
        and assessment.system_function is SystemFunction.INTERACTIVE_AI
    )
    machine_mark_required = (
        assessment.territorial_scope is TerritorialScope.EU_IN_SCOPE
        and _is_provider(assessment.actor_role)
        and assessment.system_function is SystemFunction.GENERATIVE_CONTENT
    )
    visible_label_required = False

    if (
        assessment.territorial_scope is TerritorialScope.EU_IN_SCOPE
        and _is_deployer(assessment.actor_role)
        and assessment.content_context in {ContentContext.DEEPFAKE, ContentContext.ARTISTIC_OR_FICTIONAL}
    ):
        visible_label_required = True

    if (
        assessment.territorial_scope is TerritorialScope.EU_IN_SCOPE
        and _is_deployer(assessment.actor_role)
        and assessment.content_context is ContentContext.PUBLIC_INTEREST_TEXT
    ):
        editorial_exception = bool(
            assessment.human_review_completed
            and assessment.editorial_responsibility_owner
            and assessment.editorial_responsibility_owner.strip()
        )
        visible_label_required = not editorial_exception
        if editorial_exception:
            reasons.append("public-interest text exception declared with human review and editorial responsibility")

    if interaction_required and not assessment.interaction_disclosure_present:
        missing.append("interaction_disclosure")
    if machine_mark_required and not assessment.machine_readable_mark_present:
        missing.append("machine_readable_mark")
    if visible_label_required and not assessment.visible_label_present:
        missing.append("visible_label")

    if assessment.territorial_scope is TerritorialScope.OUT_OF_SCOPE:
        outcome = TransparencyOutcome.NOT_APPLICABLE
        human_gate_required = False
    elif unresolved:
        outcome = TransparencyOutcome.BLOCKED_UNRESOLVED
        human_gate_required = True
    elif missing:
        outcome = TransparencyOutcome.CONTROLS_REQUIRED
        human_gate_required = True
    else:
        evidence = tuple(item for item in human_gate_evidence if item.strip())
        if human_gate_approved:
            if not evidence:
                raise ValueError("human_gate_evidence is required when human_gate_approved is true")
            outcome = TransparencyOutcome.APPROVED_FOR_DECLARED_CONTEXT
            human_gate_required = False
        else:
            outcome = TransparencyOutcome.READY_FOR_HUMAN_GATE
            human_gate_required = True

    return Article50Decision(
        outcome=outcome,
        interaction_disclosure_required=interaction_required,
        machine_readable_mark_required=machine_mark_required,
        visible_label_required=visible_label_required,
        missing_evidence=tuple(dict.fromkeys(missing)),
        reasons=tuple(reasons),
        human_gate_required=human_gate_required,
    )
