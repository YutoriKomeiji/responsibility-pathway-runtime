# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rpr.assurance_manifest import AssuranceManifestError, load_assurance_manifest, validate_assurance_manifest


RPR_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = RPR_ROOT / "specs" / "runtime-assurance-manifest-v1.json"


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_repository_manifest_is_valid_and_anchored() -> None:
    loaded = load_assurance_manifest(MANIFEST_PATH)
    assert loaded["canonical_source"] == "YutoriKomeiji/responsibility-pathway-runtime"
    assert loaded["release_boundary"] == "public_alpha_candidate"
    assert loaded["maximum_current_evidence_level"] == "E3"
    assert {claim["claim_id"] for claim in loaded["claims"]} == {
        "MCP-CLM-01", "MCP-CLM-02", "MCP-CLM-03", "MCP-CLM-04", "MCP-CLM-05", "RPR-RC-01"
    }


def test_rejects_released_boundary_without_authorization() -> None:
    payload = _manifest()
    payload["release_boundary"] = "released"
    with pytest.raises(AssuranceManifestError, match="release_boundary_must_be_public_alpha_candidate"):
        validate_assurance_manifest(payload)


def test_rejects_missing_human_gate() -> None:
    payload = _manifest()
    payload["human_gate_required_for"].remove("tag_or_github_release")
    with pytest.raises(AssuranceManifestError, match="missing_human_gates"):
        validate_assurance_manifest(payload)


def test_rejects_e4_or_e5_escalation() -> None:
    payload = _manifest()
    payload["maximum_current_evidence_level"] = "E4"
    with pytest.raises(AssuranceManifestError, match="evidence_level_escalation_requires_human_gate"):
        validate_assurance_manifest(payload)


def test_rejects_claim_above_manifest_maximum() -> None:
    payload = _manifest()
    payload["claims"][0]["evidence_level"] = "E4"
    with pytest.raises(AssuranceManifestError, match="exceeds_manifest_maximum"):
        validate_assurance_manifest(payload)


def test_rejects_duplicate_claim_id() -> None:
    payload = _manifest()
    payload["claims"].append(copy.deepcopy(payload["claims"][0]))
    with pytest.raises(AssuranceManifestError, match="duplicate_claim_id"):
        validate_assurance_manifest(payload)


def test_rejects_passing_claim_without_tests() -> None:
    payload = _manifest()
    payload["claims"][0]["test_anchors"] = []
    with pytest.raises(AssuranceManifestError, match="passing_without_test_anchor"):
        validate_assurance_manifest(payload)


def test_rejects_unverified_claim_without_blocker() -> None:
    payload = _manifest()
    next(claim for claim in payload["claims"] if claim["claim_id"] == "RPR-RC-01")["blocked_by"] = []
    with pytest.raises(AssuranceManifestError, match="unverified_without_blocker"):
        validate_assurance_manifest(payload)


def test_rejects_missing_source_document(tmp_path: Path) -> None:
    with pytest.raises(AssuranceManifestError, match="source_document_missing"):
        validate_assurance_manifest(_manifest(), root=tmp_path)


def test_rejects_anchor_path_escape() -> None:
    payload = _manifest()
    payload["claims"][0]["implementation_anchors"] = ["../outside.py"]
    with pytest.raises(AssuranceManifestError, match="must_be_relative"):
        validate_assurance_manifest(payload, root=RPR_ROOT)
