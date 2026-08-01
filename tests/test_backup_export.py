# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import json
import sqlite3
from pathlib import Path

import pytest

from rpr.backup import BackupError, backup_sqlite_set, restore_sqlite_backup
from rpr.clean_export import ExportError, rehearse_clean_export


REQUIRED = ("README.md", "LICENSE", "SECURITY.md", "CHANGELOG.md", "CITATION.cff", "pyproject.toml")


def _database(path: Path, value: str = "preserved") -> Path:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE records (value TEXT NOT NULL)")
    connection.execute("INSERT INTO records(value) VALUES (?)", (value,))
    connection.commit()
    connection.close()
    return path


def test_backup_restore_preserves_database_and_manifest(tmp_path: Path) -> None:
    source = _database(tmp_path / "source.sqlite3")
    backup_dir = tmp_path / "backup"
    manifest = backup_sqlite_set((("pathways", source),), backup_dir)
    artifact = manifest.artifacts[0]
    assert artifact.integrity_check == "ok"
    manifest_json = json.loads((backup_dir / "backup-manifest.json").read_text(encoding="utf-8"))
    assert manifest_json["format_version"] == 1

    restored = restore_sqlite_backup(
        artifact.backup,
        tmp_path / "restored.sqlite3",
        expected_sha256=artifact.sha256,
    )
    connection = sqlite3.connect(restored)
    try:
        assert connection.execute("SELECT value FROM records").fetchone()[0] == "preserved"
    finally:
        connection.close()


def test_restore_rejects_digest_mismatch_and_existing_target(tmp_path: Path) -> None:
    source = _database(tmp_path / "source.sqlite3")
    artifact = backup_sqlite_set((("store", source),), tmp_path / "backup").artifacts[0]
    with pytest.raises(BackupError, match="digest"):
        restore_sqlite_backup(artifact.backup, tmp_path / "restore.sqlite3", expected_sha256="0" * 64)
    target = _database(tmp_path / "existing.sqlite3", "existing")
    with pytest.raises(BackupError, match="already exists"):
        restore_sqlite_backup(artifact.backup, target, expected_sha256=artifact.sha256)


def _release_tree(root: Path) -> Path:
    root.mkdir(parents=True)
    for name in REQUIRED:
        (root / name).write_text(name, encoding="utf-8")
    package = root / "src" / "rpr"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_smoke.py").write_text("def test_smoke(): assert True\n", encoding="utf-8")
    return root


def test_clean_export_copies_only_allowlisted_product_tree(tmp_path: Path) -> None:
    source = _release_tree(tmp_path / "source")
    (source / "private-review.md").write_text("private", encoding="utf-8")
    target = tmp_path / "export"
    first = rehearse_clean_export(source, target)
    assert (target / "src" / "rpr" / "__init__.py").is_file()
    assert not (target / "private-review.md").exists()
    assert (target / "EXPORT-MANIFEST.json").is_file()

    second_target = tmp_path / "export-second"
    second = rehearse_clean_export(source, second_target)
    assert first.manifest_sha256 == second.manifest_sha256


def test_clean_export_rejects_forbidden_artifact_inside_allowlist(tmp_path: Path) -> None:
    source = _release_tree(tmp_path / "source")
    (source / "tests" / "runtime.sqlite3").write_bytes(b"private")
    with pytest.raises(ExportError, match="forbidden"):
        rehearse_clean_export(source, tmp_path / "export")
