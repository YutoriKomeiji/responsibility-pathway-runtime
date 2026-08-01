# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_writer() -> ModuleType:
    path = Path(__file__).parents[1] / "tools" / "write_candidate_readiness.py"
    spec = importlib.util.spec_from_file_location("rpr_write_candidate_readiness", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load candidate readiness writer from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_document = _load_writer().build_document

_NAMES = (
    "pytest",
    "json_python_lean_parity",
    "lean_build",
    "wheel_install",
    "sdist_install",
    "release_audit",
    "rc_rehearsal",
    "clean_export",
)


def outcomes(value: str = "success") -> dict[str, str]:
    return {name: value for name in _NAMES}


def test_green_internal_ci_remains_hold_for_external_gates(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "workflow-context.json").write_text("{}\n", encoding="utf-8")

    document = build_document(
        source_commit="a" * 40,
        outcomes=outcomes(),
        evidence_root=evidence,
        residual_owner="Akihisa Ono",
    )

    assert document["internal_ready"] is True
    assert document["external_ready"] is False
    assert document["decision"] == "hold"
    assert document["blocking_items"] == [
        "secret_scan",
        "vulnerability_review",
        "human_gate",
    ]
    assert len(document["evidence_sha256"]["workflow-context.json"]) == 64
    assert len(document["report_sha256"]) == 64


def test_failed_ci_step_is_preserved_as_blocker(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "context.json").write_text("{}", encoding="utf-8")
    values = outcomes()
    values["pytest"] = "failure"

    document = build_document(
        source_commit="b" * 40,
        outcomes=values,
        evidence_root=evidence,
        residual_owner="owner",
    )

    assert document["internal_ready"] is False
    assert document["blocking_items"][0] == "pytest"


def test_unknown_outcome_and_empty_evidence_fail_closed(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    values = outcomes()
    values["pytest"] = "unknown"

    with pytest.raises(ValueError, match="retained evidence"):
        build_document(
            source_commit="c" * 40,
            outcomes=values,
            evidence_root=evidence,
            residual_owner="owner",
        )

    (evidence / "context.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported CI outcome"):
        build_document(
            source_commit="c" * 40,
            outcomes=values,
            evidence_root=evidence,
            residual_owner="owner",
        )
