# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .authority import AuthorityError, authorize_transition
from .evidence import build_event
from .executor import ExecutionStatus
from .models import PathwayState
from .runtime import ResponsibilityPathwayRuntime
from .state_machine import ensure_transition


@dataclass(frozen=True)
class CompensationRecord:
    action: str
    authority: str
    outcome: str
    evidence: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        if not self.action.strip() or not self.authority.strip() or not self.outcome.strip():
            raise ValueError("compensation action, authority, and outcome are required")
        return {
            "action": self.action,
            "authority": self.authority,
            "outcome": self.outcome,
            "evidence": dict(self.evidence),
        }


class RepairCoordinator:
    """Close repair evidence and authorize bounded pathway resumption."""

    def __init__(self, runtime: ResponsibilityPathwayRuntime) -> None:
        self.runtime = runtime

    def complete_repair(
        self,
        pathway_id: str,
        *,
        actor: str,
        prior_attempt_id: str,
        repair_evidence: Mapping[str, Any],
        reason: str,
        compensation: CompensationRecord | None = None,
    ) -> PathwayState:
        if not prior_attempt_id.strip():
            raise ValueError("prior_attempt_id is required")
        if not repair_evidence:
            raise ValueError("repair_evidence is required before ready_to_resume")
        prior_attempt = self.runtime.attempt_ledger.get(prior_attempt_id)
        if prior_attempt.pathway_id != pathway_id or prior_attempt.result_json is None:
            raise ValueError("prior attempt is not a finished attempt for this pathway")
        if prior_attempt.status != ExecutionStatus.FAILED.value:
            raise ValueError("repair requires a failed prior attempt")

        current = self.runtime.store.get_state(pathway_id)
        target = PathwayState.READY_TO_RESUME
        definition = self.runtime.store.get_definition(pathway_id)
        ensure_transition(current, target)
        authorize_transition(definition, current, target, actor)
        compensation_value = None if compensation is None else compensation.to_dict()
        event = build_event(
            pathway_id=pathway_id,
            event_type="repair_completed",
            actor=actor,
            payload={
                "from": current.value,
                "to": target.value,
                "prior_attempt_id": prior_attempt_id,
                "repair_evidence": dict(repair_evidence),
                "compensation": compensation_value,
                "reason": reason,
            },
            previous_hash=self.runtime.store.latest_event_hash(pathway_id),
            redaction_policy=self.runtime.redaction_policy,
        )
        self.runtime.store.transition_with_event(pathway_id, current, target, event)
        return target

    def resume(
        self,
        pathway_id: str,
        *,
        actor: str,
        prior_attempt_id: str,
        next_attempt_id: str,
        reason: str,
    ) -> PathwayState:
        if not prior_attempt_id.strip() or not next_attempt_id.strip():
            raise ValueError("prior_attempt_id and next_attempt_id are required")
        if prior_attempt_id == next_attempt_id:
            raise ValueError("resume requires a new attempt identity")
        prior_attempt = self.runtime.attempt_ledger.get(prior_attempt_id)
        if prior_attempt.pathway_id != pathway_id or prior_attempt.result_json is None:
            raise ValueError("prior attempt is not a finished attempt for this pathway")
        if prior_attempt.status != ExecutionStatus.FAILED.value:
            raise ValueError("resume requires a failed prior attempt")
        try:
            self.runtime.attempt_ledger.get(next_attempt_id)
        except KeyError:
            pass
        else:
            raise ValueError("next attempt identity already exists")

        repair_attempt_id = None
        for event in reversed(self.runtime.evidence(pathway_id)):
            if event.get("event_type") == "repair_completed":
                repair_attempt_id = event.get("payload", {}).get("prior_attempt_id")
                break
        if repair_attempt_id != prior_attempt_id:
            raise ValueError("resume prior_attempt_id must match the latest completed repair")

        current = self.runtime.store.get_state(pathway_id)
        target = PathwayState.RUNNING
        definition = self.runtime.store.get_definition(pathway_id)
        ensure_transition(current, target)
        authorize_transition(definition, current, target, actor)
        event = build_event(
            pathway_id=pathway_id,
            event_type="pathway_resumed",
            actor=actor,
            payload={
                "from": current.value,
                "to": target.value,
                "prior_attempt_id": prior_attempt_id,
                "next_attempt_id": next_attempt_id,
                "reason": reason,
            },
            previous_hash=self.runtime.store.latest_event_hash(pathway_id),
            redaction_policy=self.runtime.redaction_policy,
        )
        self.runtime.store.transition_with_event(pathway_id, current, target, event)
        return target

    def abort_with_residuals(
        self,
        pathway_id: str,
        *,
        actor: str,
        residuals: Mapping[str, Any],
        reason: str,
    ) -> PathwayState:
        if not residuals:
            raise ValueError("residuals are required for residual closure")
        current = self.runtime.store.get_state(pathway_id)
        target = PathwayState.ABORTED
        definition = self.runtime.store.get_definition(pathway_id)
        ensure_transition(current, target)
        if not actor.strip() or actor != definition.residual_owner:
            raise AuthorityError("actor lacks residual_owner")
        event = build_event(
            pathway_id=pathway_id,
            event_type="residual_closure",
            actor=actor,
            payload={
                "from": current.value,
                "to": target.value,
                "residual_owner": definition.residual_owner,
                "residuals": dict(residuals),
                "reason": reason,
            },
            previous_hash=self.runtime.store.latest_event_hash(pathway_id),
            redaction_policy=self.runtime.redaction_policy,
        )
        self.runtime.store.transition_with_event(pathway_id, current, target, event)
        return target
