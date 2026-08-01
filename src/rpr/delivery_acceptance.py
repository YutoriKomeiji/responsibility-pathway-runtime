# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Sequence


_DIMENSIONS = (
    "traceability",
    "runtime_paths",
    "authority_and_escalation",
    "lifecycle_operations",
    "supported_scope",
    "release_artifacts",
    "customer_handover",
    "bilingual_documents",
)
_ALLOWED_STATUSES = {"verified", "partial", "pending", "blocked"}


@dataclass(frozen=True)
class AcceptanceItem:
    status: str
    evidence: tuple[str, ...] = ()
    blocker: str = ""

    def validate(self, *, name: str) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported acceptance status for {name}: {self.status}")
        if self.status == "verified" and not self.evidence:
            raise ValueError(f"verified acceptance item requires evidence: {name}")
        if self.status in {"blocked", "partial"} and not self.blocker.strip():
            raise ValueError(f"{self.status} acceptance item requires blocker: {name}")
        if any(not value.strip() for value in self.evidence):
            raise ValueError(f"blank evidence reference for {name}")


@dataclass(frozen=True)
class DeliveryAcceptanceMatrix:
    source_commit: str
    items: Mapping[str, AcceptanceItem]
    residual_owner: str

    def validate(self) -> None:
        if not self.source_commit.strip():
            raise ValueError("source commit is required")
        if not self.residual_owner.strip():
            raise ValueError("residual owner is required")

        missing = [name for name in _DIMENSIONS if name not in self.items]
        unknown = sorted(set(self.items) - set(_DIMENSIONS))
        if missing:
            raise ValueError(f"missing acceptance dimensions: {', '.join(missing)}")
        if unknown:
            raise ValueError(f"unknown acceptance dimensions: {', '.join(unknown)}")
        for name in _DIMENSIONS:
            self.items[name].validate(name=name)

    @property
    def blocking_dimensions(self) -> tuple[str, ...]:
        self.validate()
        return tuple(name for name in _DIMENSIONS if self.items[name].status != "verified")

    @property
    def next_stage(self) -> str:
        self.validate()
        statuses = {name: self.items[name].status for name in _DIMENSIONS}
        if statuses["traceability"] != "verified" or statuses["runtime_paths"] != "verified":
            return "implementation_gap_review"
        if statuses["lifecycle_operations"] != "verified" or statuses["release_artifacts"] != "verified":
            return "operational_acceptance_review"
        if statuses["supported_scope"] != "verified" or statuses["customer_handover"] != "verified":
            return "handover_gap_review"
        if statuses["bilingual_documents"] != "verified":
            return "documentation_gap_review"
        if statuses["authority_and_escalation"] != "verified":
            return "governance_gap_review"
        return "ready_for_candidate_freeze"

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "source_commit": self.source_commit,
            "next_stage": self.next_stage,
            "blocking_dimensions": list(self.blocking_dimensions),
            "items": {
                name: {
                    "status": self.items[name].status,
                    "evidence": list(self.items[name].evidence),
                    "blocker": self.items[name].blocker,
                }
                for name in _DIMENSIONS
            },
            "residual_owner": self.residual_owner,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_input_keys(*, name: str, values: Mapping[str, object], require_all: bool) -> None:
    missing = [dimension for dimension in _DIMENSIONS if require_all and dimension not in values]
    unknown = sorted(set(values) - set(_DIMENSIONS))
    if missing:
        raise ValueError(f"missing {name} dimensions: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"unknown {name} dimensions: {', '.join(unknown)}")


def build_matrix(
    *,
    source_commit: str,
    statuses: Mapping[str, str],
    evidence: Mapping[str, Sequence[str]],
    blockers: Mapping[str, str],
    residual_owner: str,
) -> DeliveryAcceptanceMatrix:
    _validate_input_keys(name="status", values=statuses, require_all=True)
    _validate_input_keys(name="evidence", values=evidence, require_all=False)
    _validate_input_keys(name="blocker", values=blockers, require_all=False)

    items = {
        name: AcceptanceItem(
            status=statuses[name],
            evidence=tuple(evidence.get(name, ())),
            blocker=blockers.get(name, ""),
        )
        for name in _DIMENSIONS
    }
    matrix = DeliveryAcceptanceMatrix(
        source_commit=source_commit,
        items=items,
        residual_owner=residual_owner,
    )
    matrix.validate()
    return matrix
