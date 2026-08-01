# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from pathlib import Path

from rpr.release_audit import audit_release_tree


REQUIRED = ("README.md", "LICENSE", "SECURITY.md", "CHANGELOG.md", "CITATION.cff", "pyproject.toml")


def _tree(tmp_path: Path) -> Path:
    for name in REQUIRED:
        (tmp_path / name).write_text(name, encoding="utf-8")
    package = tmp_path / "src" / "rpr"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    return tmp_path


def test_clean_tree_passes_and_manifest_is_deterministic(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    first = audit_release_tree(root)
    second = audit_release_tree(root)
    assert first.valid
    assert first.manifest_sha256 == second.manifest_sha256


def test_forbidden_runtime_artifact_blocks_release(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "attempts.sqlite3").write_bytes(b"private")
    report = audit_release_tree(root)
    assert not report.valid
    assert any(item.code == "forbidden_artifact" for item in report.findings)


def test_missing_release_document_blocks_release(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "SECURITY.md").unlink()
    report = audit_release_tree(root)
    assert not report.valid
    assert any(item.code == "required_file_missing" and item.path == "SECURITY.md" for item in report.findings)
