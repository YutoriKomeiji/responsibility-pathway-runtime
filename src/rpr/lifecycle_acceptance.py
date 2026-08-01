# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from rpr.backup import backup_sqlite_set, restore_sqlite_backup


_CONFIG_KEYS = {"format_version", "database_path", "backup_directory", "retention_mode"}
_FIXTURE_KEYS = {"format_version", "schema", "rows"}
_SUPPORTED_CONFIG_FORMATS = {1}
_SUPPORTED_FIXTURE_FORMATS = {1}
_SUPPORTED_FIXTURE_SCHEMAS = {"lifecycle_events_v1"}
_SUPPORTED_RETENTION_MODES = {"preserve_customer_data"}


class LifecycleAcceptanceError(RuntimeError):
    """Raised when lifecycle evidence cannot be produced safely."""


@dataclass(frozen=True)
class LifecycleConfiguration:
    format_version: int
    database_path: str
    backup_directory: str
    retention_mode: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "LifecycleConfiguration":
        missing = sorted(_CONFIG_KEYS - set(values))
        unknown = sorted(set(values) - _CONFIG_KEYS)
        if missing:
            raise LifecycleAcceptanceError(f"missing configuration fields: {', '.join(missing)}")
        if unknown:
            raise LifecycleAcceptanceError(f"unknown configuration fields: {', '.join(unknown)}")
        try:
            format_version = int(values["format_version"])
        except (TypeError, ValueError) as exc:
            raise LifecycleAcceptanceError("configuration format version must be an integer") from exc
        configuration = cls(
            format_version=format_version,
            database_path=str(values["database_path"]),
            backup_directory=str(values["backup_directory"]),
            retention_mode=str(values["retention_mode"]),
        )
        configuration.validate()
        return configuration

    def validate(self) -> None:
        if self.format_version not in _SUPPORTED_CONFIG_FORMATS:
            raise LifecycleAcceptanceError(
                f"unsupported configuration format: {self.format_version}"
            )
        if not self.database_path.strip() or not self.backup_directory.strip():
            raise LifecycleAcceptanceError("database and backup paths are required")
        if self.retention_mode not in _SUPPORTED_RETENTION_MODES:
            raise LifecycleAcceptanceError(
                f"unsupported retention mode: {self.retention_mode}"
            )

    def resolve(self, base: Path) -> tuple[Path, Path]:
        self.validate()
        database = (base / self.database_path).resolve()
        backup = (base / self.backup_directory).resolve()
        root = base.resolve()
        if root not in database.parents or root not in backup.parents:
            raise LifecycleAcceptanceError("configuration paths must remain inside workspace")
        if database == backup or database in backup.parents or backup in database.parents:
            raise LifecycleAcceptanceError("database and backup paths must be separate")
        return database, backup


def load_configuration(path: str | Path) -> LifecycleConfiguration:
    source = Path(path)
    try:
        values = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleAcceptanceError(f"configuration cannot be read: {source}") from exc
    if not isinstance(values, dict):
        raise LifecycleAcceptanceError("configuration root must be an object")
    return LifecycleConfiguration.from_mapping(values)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_upgrade_fixture(path: str | Path) -> tuple[int, str, tuple[tuple[int, str], ...], str]:
    source = Path(path).resolve()
    try:
        values = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleAcceptanceError(f"upgrade fixture cannot be read: {source}") from exc
    if not isinstance(values, dict):
        raise LifecycleAcceptanceError("upgrade fixture root must be an object")
    missing = sorted(_FIXTURE_KEYS - set(values))
    unknown = sorted(set(values) - _FIXTURE_KEYS)
    if missing:
        raise LifecycleAcceptanceError(f"missing upgrade fixture fields: {', '.join(missing)}")
    if unknown:
        raise LifecycleAcceptanceError(f"unknown upgrade fixture fields: {', '.join(unknown)}")
    try:
        format_version = int(values["format_version"])
    except (TypeError, ValueError) as exc:
        raise LifecycleAcceptanceError("upgrade fixture format version must be an integer") from exc
    schema = values["schema"]
    rows = values["rows"]
    if format_version not in _SUPPORTED_FIXTURE_FORMATS:
        raise LifecycleAcceptanceError(f"unsupported upgrade fixture format: {format_version}")
    if schema not in _SUPPORTED_FIXTURE_SCHEMAS:
        raise LifecycleAcceptanceError(f"unsupported upgrade fixture schema: {schema}")
    if not isinstance(rows, list) or not rows:
        raise LifecycleAcceptanceError("upgrade fixture rows must be a non-empty array")
    parsed: list[tuple[int, str]] = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"event_id", "payload"}:
            raise LifecycleAcceptanceError(f"upgrade fixture row {index} is malformed")
        event_id = row["event_id"]
        payload = row["payload"]
        if not isinstance(event_id, int) or event_id <= 0 or event_id in seen:
            raise LifecycleAcceptanceError(f"upgrade fixture row {index} has invalid event_id")
        if not isinstance(payload, str) or not payload:
            raise LifecycleAcceptanceError(f"upgrade fixture row {index} has invalid payload")
        seen.add(event_id)
        parsed.append((event_id, payload))
    return format_version, str(schema), tuple(parsed), _sha256(source)


def _database_digest(path: Path) -> str:
    connection = sqlite3.connect(str(path))
    try:
        rows = connection.execute(
            "SELECT event_id, payload FROM lifecycle_events ORDER BY event_id"
        ).fetchall()
    finally:
        connection.close()
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _materialize_upgrade_fixture(path: Path, rows: tuple[tuple[int, str], ...]) -> None:
    if path.exists():
        raise LifecycleAcceptanceError("upgrade fixture target already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(
            "CREATE TABLE lifecycle_events (event_id INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO lifecycle_events(event_id, payload) VALUES (?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def run_lifecycle_acceptance(
    *,
    workspace: str | Path,
    output: str | Path,
    source_commit: str,
    upgrade_fixture: str | Path,
) -> dict[str, object]:
    if not source_commit.strip():
        raise LifecycleAcceptanceError("source commit is required")
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "rpr-config-v1.json"
    config_path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "database_path": "customer-data/runtime.sqlite3",
                "backup_directory": "customer-backups",
                "retention_mode": "preserve_customer_data",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    configuration = load_configuration(config_path)
    database, backup_directory = configuration.resolve(root)
    fixture_format, fixture_schema, fixture_rows, fixture_sha256 = _load_upgrade_fixture(
        upgrade_fixture
    )
    _materialize_upgrade_fixture(database, fixture_rows)
    before_digest = _database_digest(database)

    manifest = backup_sqlite_set((("runtime", database),), backup_directory)
    artifact = manifest.artifacts[0]
    database.unlink()
    restored = restore_sqlite_backup(
        artifact.backup,
        database,
        expected_sha256=artifact.sha256,
    )
    after_digest = _database_digest(restored)
    if before_digest != after_digest:
        raise LifecycleAcceptanceError("restored customer data does not match source")

    document: dict[str, object] = {
        "source_commit": source_commit,
        "configuration": {
            "format_version": configuration.format_version,
            "compatible": True,
            "retention_mode": configuration.retention_mode,
        },
        "upgrade_fixture": {
            "previous_candidate_format": fixture_format,
            "schema": fixture_schema,
            "fixture_sha256": fixture_sha256,
            "row_count": len(fixture_rows),
            "accepted_by_candidate": True,
        },
        "backup_restore": {
            "manifest": manifest.to_dict(),
            "source_digest": before_digest,
            "restored_digest": after_digest,
            "content_equal": True,
        },
        "removal": {
            "package_removed": False,
            "customer_data_preserved": database.is_file(),
            "backup_preserved": Path(artifact.backup).is_file(),
        },
        "decision": "awaiting_removal_verification",
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def finalize_removal_evidence(
    *,
    evidence: str | Path,
    package_removed: bool,
    cli_removed: bool,
    residue_paths: tuple[str, ...],
) -> dict[str, object]:
    path = Path(evidence)
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleAcceptanceError("lifecycle evidence cannot be read") from exc
    if not isinstance(values, dict):
        raise LifecycleAcceptanceError("lifecycle evidence root is malformed")
    removal = values.get("removal")
    if not isinstance(removal, dict):
        raise LifecycleAcceptanceError("removal evidence is malformed")
    removal.update(
        {
            "package_removed": package_removed,
            "cli_removed": cli_removed,
            "residue_paths": list(residue_paths),
        }
    )
    complete = (
        package_removed
        and cli_removed
        and not residue_paths
        and removal.get("customer_data_preserved") is True
        and removal.get("backup_preserved") is True
    )
    values["decision"] = "verified" if complete else "hold"
    path.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not complete:
        raise LifecycleAcceptanceError("removal verification did not pass")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute RPR lifecycle acceptance evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)
    execute = subparsers.add_parser("execute")
    execute.add_argument("--workspace", required=True)
    execute.add_argument("--output", required=True)
    execute.add_argument("--source-commit", required=True)
    execute.add_argument("--upgrade-fixture", required=True)
    finalize = subparsers.add_parser("finalize-removal")
    finalize.add_argument("--evidence", required=True)
    finalize.add_argument("--package-removed", action="store_true")
    finalize.add_argument("--cli-removed", action="store_true")
    finalize.add_argument("--residue-path", action="append", default=[])
    args = parser.parse_args()
    if args.command == "execute":
        run_lifecycle_acceptance(
            workspace=args.workspace,
            output=args.output,
            source_commit=args.source_commit,
            upgrade_fixture=args.upgrade_fixture,
        )
    else:
        finalize_removal_evidence(
            evidence=args.evidence,
            package_removed=args.package_removed,
            cli_removed=args.cli_removed,
            residue_paths=tuple(args.residue_path),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
