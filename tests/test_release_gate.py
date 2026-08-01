# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

import pytest

from rpr.release_gate import ReleaseDecisionPack


EVIDENCE = {
    "clean_export_manifest": "1" * 64,
    "wheel": "2" * 64,
    "sdist": "3" * 64,
    "sbom": "4" * 64,
    "clean_install_e2e": "5" * 64,
    "secret_scan": "6" * 64,
    "vulnerability_review": "7" * 64,
    "known_limitations": "8" * 64,
}


def _pack(**overrides: object) -> ReleaseDecisionPack:
    values = {
        "source_commit": "abc123",
        "version": "0.1.0a2",
        "decision": "hold",
        "evidence_sha256": EVIDENCE,
        "decision_owner": "Master",
        "release_authority": "Master",
        "evidence_owner": "RPR release review",
        "residual_owner": "Master",
    }
    values.update(overrides)
    return ReleaseDecisionPack(**values)


def test_complete_hold_pack_is_deterministic() -> None:
    first = _pack()
    second = _pack(evidence_sha256=dict(reversed(list(EVIDENCE.items()))))
    assert first.digest() == second.digest()


def test_missing_evidence_blocks_decision() -> None:
    incomplete = dict(EVIDENCE)
    incomplete.pop("secret_scan")
    with pytest.raises(ValueError, match="missing release evidence"):
        _pack(evidence_sha256=incomplete).validate()


def test_conditional_approval_requires_conditions() -> None:
    with pytest.raises(ValueError, match="requires conditions"):
        _pack(decision="approve_with_conditions").validate()


def test_unconditional_approval_rejects_conditions() -> None:
    with pytest.raises(ValueError, match="cannot retain conditions"):
        _pack(decision="approve", conditions=("later",)).validate()
