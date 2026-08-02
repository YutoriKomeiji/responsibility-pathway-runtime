# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rpr.lifecycle_acceptance import (
    LifecycleAcceptanceError,
    LifecycleConfiguration,
    finalize_removal_evidence,
    load_configuration,
    run_lifecycle_acceptance,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_UPGRADE_FIXTURE = _REPOSITORY_ROOT / "fixtures/lifecycle/previous-candidate-v1.json"


def test_configuration_rejects_unknown_and_outside_workspace_paths(tmp_path: Path) -> None:
    with pytest.raises(LifecycleAcceptanceError, match="unknown configuration fields"):
        LifecycleConfiguration.from_mapping({
            "format_version": 1,
            "database_path": "data.sqlite3",
            "backup_directory": "backups",
            "retention_mode": "preserve_customer_data",
            "publish": True,
        })
    configuration = LifecycleConfiguration(
        format_version=1,
        database_path="../outside.sqlite3",
        backup_directory="backups",
        retention_mode="preserve_customer_data",
    )
    with pytest.raises(LifecycleAcceptanceError, match="inside workspace"):
        configuration.resolve(tmp_path)


def test_previous_candidate_configuration_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "format_version": 1,
        "database_path": "data/runtime.sqlite3",
        "backup_directory": "backup",
        "retention_mode": "preserve_customer_data",
    }), encoding="utf-8")
    configuration = load_configuration(path)
    assert configuration.format_version == 1
    assert configuration.retention_mode == "preserve_customer_data"


def test_lifecycle_acceptance_consumes_retained_fixture_and_restores_data(tmp_path: Path) -> None:
    output = tmp_path / "lifecycle-acceptance.json"
    document = run_lifecycle_acceptance(
        workspace=tmp_path / "workspace",
        output=output,
        source_commit="a" * 40,
        upgrade_fixture=_UPGRADE_FIXTURE,
    )
    assert document["configuration"]["compatible"] is True
    assert document["upgrade_fixture"]["accepted_by_candidate"] is True
    assert document["upgrade_fixture"]["schema"] == "lifecycle_events_v1"
    assert document["upgrade_fixture"]["row_count"] == 3
    assert len(document["upgrade_fixture"]["fixture_sha256"]) == 64
    assert document["backup_restore"]["content_equal"] is True
    assert document["backup_restore"]["source_digest"] == document["backup_restore"]["restored_digest"]
    assert document["removal"]["customer_data_preserved"] is True
    assert document["removal"]["backup_preserved"] is True
    assert document["decision"] == "awaiting_removal_verification"
    assert output.is_file()


def test_upgrade_fixture_rejects_unknown_schema_and_fields(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "format_version": 1,
        "schema": "unknown_schema",
        "rows": [{"event_id": 1, "payload": "data"}],
        "publish": True,
    }), encoding="utf-8")
    with pytest.raises(LifecycleAcceptanceError, match="unknown upgrade fixture fields"):
        run_lifecycle_acceptance(
            workspace=tmp_path / "workspace",
            output=tmp_path / "evidence.json",
            source_commit="b" * 40,
            upgrade_fixture=fixture,
        )


def test_removal_finalization_requires_no_package_residue(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    run_lifecycle_acceptance(
        workspace=tmp_path / "workspace",
        output=evidence,
        source_commit="c" * 40,
        upgrade_fixture=_UPGRADE_FIXTURE,
    )
    with pytest.raises(LifecycleAcceptanceError, match="did not pass"):
        finalize_removal_evidence(
            evidence=evidence,
            package_removed=True,
            cli_removed=True,
            residue_paths=("site-packages/rpr",),
        )
    document = finalize_removal_evidence(
        evidence=evidence,
        package_removed=True,
        cli_removed=True,
        residue_paths=(),
    )
    assert document["decision"] == "verified"
    assert document["removal"]["package_removed"] is True
    assert document["removal"]["customer_data_preserved"] is True
