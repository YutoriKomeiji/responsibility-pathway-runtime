# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass

from .models import PathwayDefinition, PathwayState


class AuthorityError(PermissionError):
    """Raised when an actor lacks the declared authority for an operation."""


@dataclass(frozen=True)
class TransitionAuthority:
    required_role: str
    expected_actor: str


def _require_actor(actor: str) -> str:
    actor = actor.strip()
    if not actor:
        raise AuthorityError("actor is required")
    return actor


def authorize_execution_access(definition: PathwayDefinition, actor: str) -> None:
    """Authorize access to execution and replay results for a pathway."""

    actor = _require_actor(actor)
    if actor != definition.execution_actor:
        raise AuthorityError("actor lacks execution authority")


def authorize_reconciliation_access(definition: PathwayDefinition, actor: str) -> None:
    """Authorize observation-only reconciliation of an uncertain execution.

    Until a dedicated reconciliation authority is added to the pathway schema,
    either the declared repair owner or evidence owner may perform reconciliation.
    The runtime must never substitute the execution actor for this operation.
    """

    actor = _require_actor(actor)
    if actor not in {definition.repair_owner, definition.evidence_owner}:
        raise AuthorityError("actor lacks reconciliation authority")


def required_authority(definition: PathwayDefinition, target: PathwayState) -> TransitionAuthority | None:
    if target is PathwayState.APPROVED:
        return TransitionAuthority("approval_authority", definition.approval_authority or "")
    if target in {PathwayState.STOPPED, PathwayState.HELD, PathwayState.HUMAN_GATE}:
        return TransitionAuthority("stop_authority", definition.stop_authority)
    if target is PathwayState.REPAIR_REQUIRED:
        return TransitionAuthority("repair_owner", definition.repair_owner)
    if target is PathwayState.READY_TO_RESUME:
        return TransitionAuthority("repair_owner", definition.repair_owner)
    if target is PathwayState.RUNNING:
        return TransitionAuthority("execution_or_resume_authority", "")
    if target in {PathwayState.COMPLETED, PathwayState.PARTIALLY_COMPLETED, PathwayState.WRITE_STATUS_UNKNOWN}:
        return TransitionAuthority("execution_actor", definition.execution_actor)
    if target is PathwayState.ABORTED:
        return TransitionAuthority("residual_owner", definition.residual_owner)
    return None


def authorize_transition(definition: PathwayDefinition, current: PathwayState, target: PathwayState, actor: str) -> None:
    actor = _require_actor(actor)

    # This canonical edge exists only so authorized reconciliation can close an
    # uncertain write after observation. Generic transition calls must not use it.
    if current is PathwayState.WRITE_STATUS_UNKNOWN and target is PathwayState.COMPLETED:
        raise AuthorityError("unknown write completion requires reconciliation authority and evidence")

    # ABORTED is not a plain state change. It requires a residual owner and
    # durable residual-impact evidence through RepairCoordinator.abort_with_residuals().
    if target is PathwayState.ABORTED:
        raise AuthorityError("aborted transition requires residual closure evidence")

    if target is PathwayState.RUNNING:
        allowed = {definition.execution_actor}
        if current in {PathwayState.READY_TO_RESUME, PathwayState.STOPPED, PathwayState.HELD}:
            allowed.add(definition.resume_authority)
        if actor not in allowed:
            raise AuthorityError("actor lacks execution or resume authority")
        return

    rule = required_authority(definition, target)
    if rule is None:
        return
    if not rule.expected_actor or actor != rule.expected_actor:
        raise AuthorityError(f"actor lacks {rule.required_role}")
