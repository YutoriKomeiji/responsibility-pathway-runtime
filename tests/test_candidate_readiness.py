# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import pytest

from rpr.candidate_readiness import CandidateReadinessReport


def checks(value: bool = True) -> dict[str, bool]:
    return {
        "pytest": value,
        "json_python_lean_parity": value,
        "lean_build": value,
        "wheel_install": value,
        "sdist_install": value,
        "release_audit": value,
        "rc_rehearsal": value,
        "clean_export": value,
    }


def gates(value: bool = True) -> dict[str, bool]:
    return {
        "secret_scan": value,
        "vulnerability_review": value,
        "human_gate": value,
    }


def report(*, internal: dict[str, bool] | None = None, external: dict[str, bool] | None = None) -> CandidateReadinessReport:
    return CandidateReadinessReport(
        source_commit="a" * 40,
        internal_checks=checks() if internal is None else internal,
        external_gates=gates() if external is None else external,
        evidence_sha256={"ci_bundle": "b" * 64},
        residual_owner="Akihisa Ono",
    )


def test_internal_success_without_external_review_remains_hold() -> None:
    external = gates()
    external["secret_scan"] = False
    external["vulnerability_review"] = False
    external["human_gate"] = False

    candidate = report(external=external)

    assert candidate.internal_ready
    assert not candidate.external_ready
    assert candidate.decision == "hold"
    assert candidate.blocking_items == ("secret_scan", "vulnerability_review", "human_gate")


def test_failed_internal_check_remains_visible_even_when_external_gates_pass() -> None:
    internal = checks()
    internal["clean_export"] = False

    candidate = report(internal=internal)

    assert not candidate.internal_ready
    assert candidate.external_ready
    assert candidate.decision == "hold"
    assert candidate.blocking_items == ("clean_export",)


def test_all_checks_only_reach_human_release_decision_boundary() -> None:
    candidate = report()

    assert candidate.decision == "ready_for_human_release_decision"
    assert candidate.blocking_items == ()
    assert candidate.to_dict()["decision"] == "ready_for_human_release_decision"
    assert len(candidate.digest()) == 64


def test_missing_or_unknown_check_is_rejected() -> None:
    missing = checks()
    del missing["pytest"]
    with pytest.raises(ValueError, match="missing internal checks"):
        report(internal=missing).validate()

    unknown = checks()
    unknown["marketing_launch"] = True
    with pytest.raises(ValueError, match="unknown internal checks"):
        report(internal=unknown).validate()


def test_invalid_evidence_digest_is_rejected() -> None:
    candidate = CandidateReadinessReport(
        source_commit="a" * 40,
        internal_checks=checks(),
        external_gates=gates(),
        evidence_sha256={"ci_bundle": "not-a-digest"},
        residual_owner="Akihisa Ono",
    )

    with pytest.raises(ValueError, match="invalid SHA-256"):
        candidate.validate()
