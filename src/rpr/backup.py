# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


class BackupError(RuntimeError):
    """Raised when a backup or restore cannot be verified safely."""


@dataclass(frozen=True)
class BackupArtifact:
    name: str
    source: str
    backup: str
    sha256: str
    integrity_check: str


@dataclass(frozen=True)
class BackupManifest:
    format_version: int
    created_at: str
    artifacts: tuple[BackupArtifact, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "format_version": self.format_version,
            "created_at": self.created_at,
            "artifacts": [asdict(item) for item in self.artifacts],
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integrity(path: Path) -> str:
    connection = sqlite3.connect(str(path))
    try:
        row = connection.execute("PRAGMA integrity_check").fetchone()
        return "" if row is None else str(row[0])
    finally:
        connection.close()


def backup_sqlite_set(
    databases: Iterable[tuple[str, str | Path]],
    destination: str | Path,
) -> BackupManifest:
    target = Path(destination).resolve()
    target.mkdir(parents=True, exist_ok=True)
    artifacts: list[BackupArtifact] = []
    names: set[str] = set()
    for name, source_value in databases:
        clean_name = name.strip()
        if not clean_name or clean_name in names or "/" in clean_name or "\\" in clean_name:
            raise BackupError("backup database names must be unique simple names")
        names.add(clean_name)
        source = Path(source_value).resolve()
        if not source.is_file():
            raise BackupError(f"database does not exist: {source}")
        backup = target / f"{clean_name}.sqlite3"
        if backup.exists():
            raise BackupError(f"backup target already exists: {backup}")
        source_connection = sqlite3.connect(str(source), timeout=30.0)
        backup_connection = sqlite3.connect(str(backup), timeout=30.0)
        try:
            source_connection.backup(backup_connection)
        finally:
            backup_connection.close()
            source_connection.close()
        integrity = _integrity(backup)
        if integrity != "ok":
            backup.unlink(missing_ok=True)
            raise BackupError(f"backup integrity check failed for {clean_name}: {integrity}")
        artifacts.append(BackupArtifact(clean_name, str(source), str(backup), _sha256(backup), integrity))
    manifest = BackupManifest(1, datetime.now(UTC).isoformat(), tuple(artifacts))
    manifest_path = target / "backup-manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def restore_sqlite_backup(
    backup: str | Path,
    destination: str | Path,
    *,
    expected_sha256: str,
    replace: bool = False,
) -> Path:
    source = Path(backup).resolve()
    target = Path(destination).resolve()
    if not source.is_file():
        raise BackupError("backup file does not exist")
    if _sha256(source) != expected_sha256:
        raise BackupError("backup digest does not match manifest")
    if _integrity(source) != "ok":
        raise BackupError("backup database failed integrity check")
    if target.exists() and not replace:
        raise BackupError("restore target already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.restore.tmp")
    temporary.unlink(missing_ok=True)
    source_connection = sqlite3.connect(str(source), timeout=30.0)
    target_connection = sqlite3.connect(str(temporary), timeout=30.0)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()
    if _integrity(temporary) != "ok":
        temporary.unlink(missing_ok=True)
        raise BackupError("restored database failed integrity check")
    temporary.replace(target)
    return target
