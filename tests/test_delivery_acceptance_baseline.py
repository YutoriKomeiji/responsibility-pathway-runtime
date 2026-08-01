# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from rpr.delivery_acceptance_baseline import build_delivery_acceptance_baseline


def test_baseline_preserves_verified_delivery_and_routes_to_documentation_review() -> None:
    matrix = build_delivery_acceptance_baseline(
        source_commit="a" * 40,
        residual_owner="Akihisa Ono",
    )

    assert matrix.items["traceability"].status == "verified"
    assert matrix.items["runtime_paths"].status == "verified"
    assert matrix.items["authority_and_escalation"].status == "verified"
    assert matrix.items["lifecycle_operations"].status == "verified"
    assert matrix.items["release_artifacts"].status == "verified"
    assert matrix.items["customer_handover"].status == "verified"
    assert matrix.items["bilingual_documents"].status == "pending"
    assert matrix.next_stage == "documentation_gap_review"
    assert matrix.blocking_dimensions == ("bilingual_documents",)


def test_every_baseline_evidence_reference_exists_in_repository() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    matrix = build_delivery_acceptance_baseline(
        source_commit="b" * 40,
        residual_owner="owner",
    )

    missing = [
        reference
        for item in matrix.items.values()
        for reference in item.evidence
        if not (repository_root / reference).is_file()
    ]

    assert missing == []


def test_baseline_serialization_keeps_documentation_and_human_boundary_visible() -> None:
    matrix = build_delivery_acceptance_baseline(
        source_commit="c" * 40,
        residual_owner="owner",
    )
    document = matrix.to_dict()

    assert document["next_stage"] == "documentation_gap_review"
    assert document["items"]["lifecycle_operations"]["status"] == "verified"
    assert document["items"]["customer_handover"]["status"] == "verified"
    assert document["items"]["customer_handover"]["blocker"] == ""
    assert "incubator/rpr/src/rpr/customer_handover.py" in document["items"]["customer_handover"]["evidence"]
    assert document["items"]["bilingual_documents"]["status"] == "pending"
    assert len(matrix.digest()) == 64
