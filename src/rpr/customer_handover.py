# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


_REQUIRED_ROLES = ("operations", "audit", "maintenance")
_REQUIRED_BOUNDARIES = (
    "no_public_release_authority",
    "no_production_readiness_claim",
    "human_gate_required",
)


class CustomerHandoverError(RuntimeError):
    """Raised when a customer handover candidate is incomplete or unsafe."""


@dataclass(frozen=True)
class HandoverRole:
    responsibilities: tuple[str, ...]
    review_questions: tuple[str, ...]
    evidence: tuple[str, ...]

    def validate(self, *, name: str, repository_root: Path) -> None:
        if not self.responsibilities or any(not value.strip() for value in self.responsibilities):
            raise CustomerHandoverError(f"{name} responsibilities are incomplete")
        if not self.review_questions or any(not value.strip() for value in self.review_questions):
            raise CustomerHandoverError(f"{name} review questions are incomplete")
        if not self.evidence or any(not value.strip() for value in self.evidence):
            raise CustomerHandoverError(f"{name} evidence is incomplete")
        missing = [reference for reference in self.evidence if not (repository_root / reference).is_file()]
        if missing:
            raise CustomerHandoverError(
                f"{name} evidence references do not exist: {', '.join(sorted(missing))}"
            )


@dataclass(frozen=True)
class CustomerHandoverCandidate:
    source_commit: str
    roles: Mapping[str, HandoverRole]
    boundaries: Mapping[str, bool]
    residual_owner: str
    decision: str = "ready_for_customer_review"

    def validate(self, *, repository_root: Path) -> None:
        if not self.source_commit.strip():
            raise CustomerHandoverError("source commit is required")
        if not self.residual_owner.strip():
            raise CustomerHandoverError("residual owner is required")
        if self.decision != "ready_for_customer_review":
            raise CustomerHandoverError("handover candidate cannot self-approve")
        missing_roles = [name for name in _REQUIRED_ROLES if name not in self.roles]
        unknown_roles = sorted(set(self.roles) - set(_REQUIRED_ROLES))
        if missing_roles:
            raise CustomerHandoverError(f"missing handover roles: {', '.join(missing_roles)}")
        if unknown_roles:
            raise CustomerHandoverError(f"unknown handover roles: {', '.join(unknown_roles)}")
        for name in _REQUIRED_ROLES:
            self.roles[name].validate(name=name, repository_root=repository_root)
        missing_boundaries = [name for name in _REQUIRED_BOUNDARIES if name not in self.boundaries]
        unknown_boundaries = sorted(set(self.boundaries) - set(_REQUIRED_BOUNDARIES))
        if missing_boundaries:
            raise CustomerHandoverError(
                f"missing handover boundaries: {', '.join(missing_boundaries)}"
            )
        if unknown_boundaries:
            raise CustomerHandoverError(
                f"unknown handover boundaries: {', '.join(unknown_boundaries)}"
            )
        if not all(self.boundaries[name] is True for name in _REQUIRED_BOUNDARIES):
            raise CustomerHandoverError("all handover safety boundaries must remain active")

    def to_dict(self, *, repository_root: Path) -> dict[str, object]:
        self.validate(repository_root=repository_root)
        return {
            "source_commit": self.source_commit,
            "decision": self.decision,
            "roles": {name: asdict(self.roles[name]) for name in _REQUIRED_ROLES},
            "boundaries": {name: self.boundaries[name] for name in _REQUIRED_BOUNDARIES},
            "residual_owner": self.residual_owner,
        }

    def digest(self, *, repository_root: Path) -> str:
        canonical = json.dumps(
            self.to_dict(repository_root=repository_root),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _role(
    *,
    responsibilities: Sequence[str],
    review_questions: Sequence[str],
    evidence: Sequence[str],
) -> HandoverRole:
    return HandoverRole(tuple(responsibilities), tuple(review_questions), tuple(evidence))


def build_customer_handover_candidate(
    *,
    source_commit: str,
    residual_owner: str,
) -> CustomerHandoverCandidate:
    roles = {
        "operations": _role(
            responsibilities=(
                "operate only inside the configured responsibility and credential boundary",
                "monitor completed, held, unknown, and repair-required states separately",
                "execute tested backup, restore, upgrade, and removal procedures",
            ),
            review_questions=(
                "Are all governed mutations routed through RPR without an ungoverned bypass?",
                "Can operators diagnose and recover write-status-unknown without automatic replay?",
                "Can the lifecycle suite be reproduced in the customer environment?",
            ),
            evidence=(
                "incubator/rpr/docs/using-rpr.md",
                "incubator/rpr/src/rpr/diagnostics.py",
                "incubator/rpr/src/rpr/lifecycle_acceptance.py",
                "incubator/rpr/tests/test_operational_diagnostics.py",
                "incubator/rpr/tests/test_lifecycle_acceptance.py",
                ".github/workflows/rpr-lifecycle-acceptance.yml",
            ),
        ),
        "audit": _role(
            responsibilities=(
                "verify claim-to-evidence traceability and retained decision records",
                "confirm candidate evidence is reproducible and bound to the source commit",
                "retain unresolved external release gates as explicit blockers",
            ),
            review_questions=(
                "Does every verified delivery dimension point to retained evidence?",
                "Are Human Gate, secret scan, and vulnerability review still external decisions?",
                "Are known limitations visible and consistent with the candidate claims?",
            ),
            evidence=(
                "incubator/rpr/src/rpr/delivery_acceptance.py",
                "incubator/rpr/src/rpr/delivery_acceptance_baseline.py",
                "incubator/rpr/src/rpr/candidate_readiness.py",
                "incubator/rpr/src/rpr/claim_traceability.py",
                "incubator/rpr/docs/known-limitations.md",
                ".github/workflows/rpr-test.yml",
            ),
        ),
        "maintenance": _role(
            responsibilities=(
                "maintain supported Python, packaging, schema, and fixture compatibility boundaries",
                "treat restart, retry, repair, compensation, and residual ownership as tested paths",
                "update evidence and limitations when implementation or dependencies change",
            ),
            review_questions=(
                "Can a maintainer reproduce wheel and source installation checks?",
                "Are previous-candidate fixtures independent from the current candidate implementation?",
                "Do changes preserve fail-closed behavior and explicit residual ownership?",
            ),
            evidence=(
                "incubator/rpr/pyproject.toml",
                "incubator/rpr/fixtures/lifecycle/previous-candidate-v1.json",
                "incubator/rpr/tests/test_resume_authorization_restart.py",
                "incubator/rpr/tests/test_product_e2e_repair_resume_retry.py",
                "incubator/rpr/tests/test_product_e2e_explicit_compensation.py",
                "incubator/rpr/src/rpr/release_audit.py",
            ),
        ),
    }
    return CustomerHandoverCandidate(
        source_commit=source_commit,
        roles=roles,
        boundaries={name: True for name in _REQUIRED_BOUNDARIES},
        residual_owner=residual_owner,
    )


def write_customer_handover_candidate(
    *,
    repository_root: str | Path,
    output: str | Path,
    source_commit: str,
    residual_owner: str,
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    candidate = build_customer_handover_candidate(
        source_commit=source_commit,
        residual_owner=residual_owner,
    )
    document = candidate.to_dict(repository_root=root)
    document["candidate_sha256"] = candidate.digest(repository_root=root)
    serialized = json.dumps(document, indent=2, sort_keys=True) + "\n"
    normalized = json.loads(serialized)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialized, encoding="utf-8")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an RPR customer handover candidate")
    parser.add_argument("repository_root")
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--residual-owner", required=True)
    args = parser.parse_args()
    write_customer_handover_candidate(
        repository_root=args.repository_root,
        output=args.output,
        source_commit=args.source_commit,
        residual_owner=args.residual_owner,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
