# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import json
import sqlite3
from pathlib import Path

from rpr.backup import backup_sqlite_set, restore_sqlite_backup
from rpr.hash_bundle import create_hash_bundle
from rpr.sbom import generate_cyclonedx_sbom


def _db(path: Path, table: str, value: str) -> Path:
    connection = sqlite3.connect(path)
    connection.execute(f"CREATE TABLE {table} (value TEXT NOT NULL)")
    connection.execute(f"INSERT INTO {table}(value) VALUES (?)", (value,))
    connection.commit()
    connection.close()
    return path


def test_four_registry_backup_restore_drill(tmp_path: Path) -> None:
    sources = (
        ("pathways", _db(tmp_path / "pathways.sqlite3", "pathway_record", "p")),
        ("attempts", _db(tmp_path / "attempts.sqlite3", "attempt_record", "a")),
        ("outbox", _db(tmp_path / "outbox.sqlite3", "outbox_record", "o")),
        ("tenants", _db(tmp_path / "tenants.sqlite3", "tenant_record", "t")),
    )
    manifest = backup_sqlite_set(sources, tmp_path / "backup")
    assert {item.name for item in manifest.artifacts} == {"pathways", "attempts", "outbox", "tenants"}
    for item in manifest.artifacts:
        restored = restore_sqlite_backup(item.backup, tmp_path / "restored" / Path(item.backup).name, expected_sha256=item.sha256)
        connection = sqlite3.connect(restored)
        try:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            connection.close()


def test_cyclonedx_sbom_has_project_and_declared_dependencies(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname="demo-runtime"\nversion="1.2.3"\ndependencies=["example-lib>=2"]\n',
        encoding="utf-8",
    )
    sbom = generate_cyclonedx_sbom(pyproject, source_commit="abc123")
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert sbom["metadata"]["component"]["name"] == "demo-runtime"
    assert sbom["components"][0]["name"] == "example-lib"


def test_hash_bundle_is_content_deterministic(tmp_path: Path) -> None:
    wheel = tmp_path / "demo.whl"
    sdist = tmp_path / "demo.tar.gz"
    sbom = tmp_path / "sbom.cdx.json"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    sbom.write_text(json.dumps({"bomFormat": "CycloneDX"}), encoding="utf-8")
    first = create_hash_bundle((wheel, sdist, sbom), source_commit="abc123")
    second = create_hash_bundle((sbom, wheel, sdist), source_commit="abc123")
    assert first["bundle_sha256"] == second["bundle_sha256"]
    assert [item["name"] for item in first["artifacts"]] == ["demo.tar.gz", "demo.whl", "sbom.cdx.json"]
