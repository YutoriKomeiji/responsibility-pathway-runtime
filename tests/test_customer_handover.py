# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rpr.customer_handover import (
    CustomerHandoverError,
    build_customer_handover_candidate,
    write_customer_handover_candidate,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_handover_candidate_covers_operations_audit_and_maintenance() -> None:
    candidate = build_customer_handover_candidate(
        source_commit="a" * 40,
        residual_owner="Akihisa Ono",
    )

    document = candidate.to_dict(repository_root=_repository_root())

    assert tuple(document["roles"]) == ("operations", "audit", "maintenance")
    for role in document["roles"].values():
        assert role["responsibilities"]
        assert role["review_questions"]
        assert role["evidence"]
    assert document["decision"] == "ready_for_customer_review"
    assert document["boundaries"] == {
        "no_public_release_authority": True,
        "no_production_readiness_claim": True,
        "human_gate_required": True,
    }


def test_handover_candidate_rejects_missing_evidence_reference(tmp_path: Path) -> None:
    candidate = build_customer_handover_candidate(
        source_commit="b" * 40,
        residual_owner="owner",
    )
    operations = replace(
        candidate.roles["operations"],
        evidence=("missing/customer-runbook.md",),
    )
    invalid = replace(candidate, roles={**candidate.roles, "operations": operations})

    with pytest.raises(CustomerHandoverError, match="evidence references do not exist"):
        invalid.to_dict(repository_root=tmp_path)


def test_handover_candidate_cannot_self_approve() -> None:
    candidate = build_customer_handover_candidate(
        source_commit="c" * 40,
        residual_owner="owner",
    )

    with pytest.raises(CustomerHandoverError, match="cannot self-approve"):
        replace(candidate, decision="accepted").to_dict(repository_root=_repository_root())


def test_handover_candidate_requires_all_safety_boundaries() -> None:
    candidate = build_customer_handover_candidate(
        source_commit="d" * 40,
        residual_owner="owner",
    )

    with pytest.raises(CustomerHandoverError, match="must remain active"):
        replace(
            candidate,
            boundaries={**candidate.boundaries, "human_gate_required": False},
        ).to_dict(repository_root=_repository_root())


def test_write_handover_candidate_retains_digest_and_source_commit(tmp_path: Path) -> None:
    output = tmp_path / "customer-handover.json"

    document = write_customer_handover_candidate(
        repository_root=_repository_root(),
        output=output,
        source_commit="e" * 40,
        residual_owner="Akihisa Ono",
    )

    retained = json.loads(output.read_text(encoding="utf-8"))
    assert retained == document
    assert retained["source_commit"] == "e" * 40
    assert retained["decision"] == "ready_for_customer_review"
    assert len(retained["candidate_sha256"]) == 64
