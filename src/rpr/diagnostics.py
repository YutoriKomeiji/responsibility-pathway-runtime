# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from .models import PathwayDefinition, PathwayState

if TYPE_CHECKING:
    from .runtime import ResponsibilityPathwayRuntime


@dataclass(frozen=True)
class PathwayDiagnostic:
    pathway_id: str
    state: PathwayState
    next_required_authority: str | None
    next_required_action: str
    active_attempt_id: str | None
    latest_event_type: str | None
    evidence_valid: bool
    evidence_event_count: int

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


def diagnose_pathway(
    runtime: ResponsibilityPathwayRuntime,
    pathway_id: str,
) -> PathwayDiagnostic:
    """Return a read-only operational handoff for a persisted pathway."""

    state = runtime.store.get_state(pathway_id)
    definition = runtime.store.get_definition(pathway_id)
    events = runtime.evidence(pathway_id)
    verification = runtime.verify_evidence(pathway_id)
    authority, action = _next_step(definition, state)

    return PathwayDiagnostic(
        pathway_id=pathway_id,
        state=state,
        next_required_authority=authority,
        next_required_action=action,
        active_attempt_id=_active_attempt_id(events, state),
        latest_event_type=None if not events else str(events[-1].get("event_type")),
        evidence_valid=verification.valid,
        evidence_event_count=verification.event_count,
    )


def _active_attempt_id(events: list[dict[str, object]], state: PathwayState) -> str | None:
    if state is not PathwayState.RUNNING:
        return None
    for event in reversed(events):
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("to") != PathwayState.RUNNING.value:
            continue
        if event.get("event_type") == "execution_started":
            candidate = payload.get("attempt_id")
        elif event.get("event_type") == "pathway_resumed":
            candidate = payload.get("next_attempt_id")
        else:
            candidate = None
        if isinstance(candidate, str) and candidate.strip():
            return candidate
        return None
    return None


def _next_step(definition: PathwayDefinition, state: PathwayState) -> tuple[str | None, str]:
    if state is PathwayState.PROPOSED:
        return definition.decision_owner, "review_pathway_definition"
    if state is PathwayState.AWAITING_APPROVAL:
        return definition.approval_authority, "approve_or_deny"
    if state is PathwayState.APPROVED:
        return definition.execution_actor, "execute_bounded_action"
    if state is PathwayState.RUNNING:
        return definition.execution_actor, "monitor_active_attempt"
    if state is PathwayState.HELD:
        return definition.stop_authority, "review_hold_condition"
    if state is PathwayState.HUMAN_GATE:
        return definition.approval_authority or definition.decision_owner, "perform_human_review"
    if state is PathwayState.STOPPED:
        return definition.stop_authority, "assess_stopped_pathway"
    if state is PathwayState.PARTIALLY_COMPLETED:
        return definition.residual_owner, "assess_residual_impacts"
    if state is PathwayState.WRITE_STATUS_UNKNOWN:
        return definition.evidence_owner, "reconcile_write_status"
    if state is PathwayState.REPAIR_REQUIRED:
        return definition.repair_owner, "repair_failed_attempt"
    if state is PathwayState.READY_TO_RESUME:
        return definition.resume_authority, "authorize_resume"
    if state is PathwayState.COMPLETED:
        return definition.evidence_owner, "verify_completion_evidence"
    if state is PathwayState.DENIED:
        return definition.decision_owner, "review_denial"
    if state is PathwayState.ABORTED:
        return definition.residual_owner, "manage_residual_impacts"
    raise ValueError(f"unsupported pathway state: {state.value}")
