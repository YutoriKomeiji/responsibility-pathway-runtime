# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rpr.integration_acceptance_inventory import IntegrationInventoryError, load_inventory


ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "incubator/rpr/specs/integration-acceptance-inventory-v1.json"


def test_inventory_retains_verified_evidence_and_allows_candidate_freeze_review() -> None:
    document = load_inventory(INVENTORY, repository_root=ROOT)

    assert document["summary"] == {
        "blocked": 1,
        "partial": 0,
        "planned": 0,
        "verified": 8,
    }
    assert document["candidate_freeze_allowed"] is True
    assert len(document["inventory_sha256"]) == 64
    assert {scenario["next_phase"] for scenario in document["scenarios"]} == {"C", "E"}


def test_every_verified_or_partial_scenario_has_existing_evidence() -> None:
    document = load_inventory(INVENTORY, repository_root=ROOT)

    for scenario in document["scenarios"]:
        if scenario["status"] in {"verified", "partial"}:
            assert scenario["evidence"]
            assert all((ROOT / reference).is_file() for reference in scenario["evidence"])


def test_inventory_rejects_unretained_verified_claim(tmp_path: Path) -> None:
    document = json.loads(INVENTORY.read_text(encoding="utf-8"))
    scenario = next(item for item in document["scenarios"] if item["status"] == "blocked")
    scenario["execution_class"] = "executable"
    scenario["status"] = "verified"
    scenario["evidence"] = []
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(IntegrationInventoryError, match="requires retained evidence"):
        load_inventory(path, repository_root=ROOT)


def test_external_environment_scenarios_remain_blocked(tmp_path: Path) -> None:
    document = json.loads(INVENTORY.read_text(encoding="utf-8"))
    scenario = next(
        item for item in document["scenarios"]
        if item["execution_class"] == "external_environment_only"
    )
    scenario["status"] = "planned"
    path = tmp_path / "invalid-external.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(IntegrationInventoryError, match="must remain blocked"):
        load_inventory(path, repository_root=ROOT)
