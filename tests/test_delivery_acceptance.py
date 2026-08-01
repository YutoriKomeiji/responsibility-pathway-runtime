# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.delivery_acceptance import AcceptanceItem, DeliveryAcceptanceMatrix, build_matrix


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


def statuses(value: str = "verified") -> dict[str, str]:
    return {name: value for name in _DIMENSIONS}


def evidence() -> dict[str, tuple[str, ...]]:
    return {name: (f"evidence/{name}.json",) for name in _DIMENSIONS}


def test_runtime_gap_routes_back_to_implementation_review() -> None:
    values = statuses()
    values["runtime_paths"] = "partial"
    matrix = build_matrix(
        source_commit="a" * 40,
        statuses=values,
        evidence=evidence(),
        blockers={"runtime_paths": "failure-path evidence incomplete"},
        residual_owner="Akihisa Ono",
    )

    assert matrix.next_stage == "implementation_gap_review"
    assert matrix.blocking_dimensions == ("runtime_paths",)


def test_lifecycle_gap_routes_to_operational_acceptance() -> None:
    values = statuses()
    values["lifecycle_operations"] = "pending"
    matrix = build_matrix(
        source_commit="b" * 40,
        statuses=values,
        evidence=evidence(),
        blockers={},
        residual_owner="owner",
    )

    assert matrix.next_stage == "operational_acceptance_review"


def test_document_gap_does_not_reopen_implementation() -> None:
    values = statuses()
    values["bilingual_documents"] = "pending"
    matrix = build_matrix(
        source_commit="c" * 40,
        statuses=values,
        evidence=evidence(),
        blockers={},
        residual_owner="owner",
    )

    assert matrix.next_stage == "documentation_gap_review"
    assert matrix.blocking_dimensions == ("bilingual_documents",)


def test_all_dimensions_only_reach_candidate_freeze_boundary() -> None:
    matrix = build_matrix(
        source_commit="d" * 40,
        statuses=statuses(),
        evidence=evidence(),
        blockers={},
        residual_owner="owner",
    )

    assert matrix.next_stage == "ready_for_candidate_freeze"
    assert matrix.blocking_dimensions == ()
    assert len(matrix.digest()) == 64


def test_verified_without_evidence_and_partial_without_blocker_fail_closed() -> None:
    items = {name: AcceptanceItem("verified", (f"{name}.json",)) for name in _DIMENSIONS}
    items["traceability"] = AcceptanceItem("verified")
    with pytest.raises(ValueError, match="requires evidence"):
        DeliveryAcceptanceMatrix("a" * 40, items, "owner").validate()

    items["traceability"] = AcceptanceItem("partial", ("trace.json",))
    with pytest.raises(ValueError, match="requires blocker"):
        DeliveryAcceptanceMatrix("a" * 40, items, "owner").validate()


def test_missing_status_dimension_fails_with_domain_error() -> None:
    values = statuses()
    del values["traceability"]

    with pytest.raises(ValueError, match="missing status dimensions: traceability"):
        build_matrix(
            source_commit="e" * 40,
            statuses=values,
            evidence=evidence(),
            blockers={},
            residual_owner="owner",
        )


@pytest.mark.parametrize("input_name", ["status", "evidence", "blocker"])
def test_unknown_input_dimension_is_not_silently_ignored(input_name: str) -> None:
    values = statuses()
    references = evidence()
    blockers: dict[str, str] = {}

    if input_name == "status":
        values["marketing_launch"] = "verified"
    elif input_name == "evidence":
        references["marketing_launch"] = ("evidence/marketing.json",)
    else:
        blockers["marketing_launch"] = "not an acceptance dimension"

    with pytest.raises(ValueError, match=rf"unknown {input_name} dimensions: marketing_launch"):
        build_matrix(
            source_commit="f" * 40,
            statuses=values,
            evidence=references,
            blockers=blockers,
            residual_owner="owner",
        )
