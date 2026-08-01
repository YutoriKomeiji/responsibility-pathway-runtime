# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rpr.claim_traceability import ClaimTraceabilityError, validate_manifest


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "specs" / "claim-traceability.json"
REGISTRY = ROOT / "specs" / "test-id-registry.json"


def test_canonical_claim_traceability_manifest_is_valid() -> None:
    data = validate_manifest(MANIFEST, root=ROOT, registry_path=REGISTRY)
    assert len(data["claims"]) == 12


def _write(tmp_path: Path, name: str, data: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_missing_claim_fails_closed(tmp_path: Path) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["claims"] = data["claims"][:-1]
    with pytest.raises(ClaimTraceabilityError, match="claim set mismatch"):
        validate_manifest(_write(tmp_path, "claim-traceability.json", data), root=ROOT, registry_path=REGISTRY)


def test_missing_anchor_fails_closed(tmp_path: Path) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["claims"][0]["implementation_anchors"] = ["src/rpr/does_not_exist.py"]
    with pytest.raises(ClaimTraceabilityError, match="anchor does not exist"):
        validate_manifest(_write(tmp_path, "claim-traceability.json", data), root=ROOT, registry_path=REGISTRY)


def test_passing_claim_cannot_use_weak_evidence(tmp_path: Path) -> None:
    data = copy.deepcopy(json.loads(MANIFEST.read_text(encoding="utf-8")))
    data["claims"][0]["evidence_level"] = "E1"
    with pytest.raises(ClaimTraceabilityError, match="passing requires at least E2"):
        validate_manifest(_write(tmp_path, "claim-traceability.json", data), root=ROOT, registry_path=REGISTRY)


def test_e4_requires_separate_promotion_record(tmp_path: Path) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["claims"][0]["evidence_level"] = "E4"
    with pytest.raises(ClaimTraceabilityError, match="separately approved promotion"):
        validate_manifest(_write(tmp_path, "claim-traceability.json", data), root=ROOT, registry_path=REGISTRY)


def test_unregistered_test_id_fails_closed(tmp_path: Path) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["claims"][0]["test_ids"] = ["RPR-NOT-REGISTERED"]
    with pytest.raises(ClaimTraceabilityError, match="unregistered test IDs"):
        validate_manifest(_write(tmp_path, "claim-traceability.json", data), root=ROOT, registry_path=REGISTRY)


def test_missing_registry_source_fails_closed(tmp_path: Path) -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["tests"][0]["source"] = "tests/does_not_exist.py"
    with pytest.raises(ClaimTraceabilityError, match="registry source does not exist"):
        validate_manifest(MANIFEST, root=ROOT, registry_path=_write(tmp_path, "test-id-registry.json", registry))


def test_passing_claim_requires_file_bound_test(tmp_path: Path) -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    claim = json.loads(MANIFEST.read_text(encoding="utf-8"))["claims"][0]
    referenced = set(claim["test_ids"])
    for entry in registry["tests"]:
        if entry["test_id"] in referenced:
            entry["binding"] = "specified_only"
            entry["source"] = "specs/runtime-product-test-specification.md"
    with pytest.raises(ClaimTraceabilityError, match="requires at least one file-bound"):
        validate_manifest(MANIFEST, root=ROOT, registry_path=_write(tmp_path, "test-id-registry.json", registry))


def test_unreferenced_registry_entry_fails_closed(tmp_path: Path) -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["tests"].append({"test_id": "RPR-EXTRA-001", "binding": "specified_only", "source": "specs/runtime-product-test-specification.md"})
    with pytest.raises(ClaimTraceabilityError, match="unreferenced entries"):
        validate_manifest(MANIFEST, root=ROOT, registry_path=_write(tmp_path, "test-id-registry.json", registry))
