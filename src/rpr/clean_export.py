# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


class ExportError(RuntimeError):
    """Raised when a clean export cannot be produced safely."""


_ALLOWED_ROOT_FILES = {
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "pyproject.toml",
}
_ALLOWED_DIRECTORIES = {"src", "tests", "examples", "docs"}
_FORBIDDEN_NAMES = {".env", "credentials.json", "secrets.json", "release-audit.json"}
_FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key", ".p12", ".pfx"}
_GENERATED_SUFFIXES = {".pyc"}
_GENERATED_PARTS = {"__pycache__", ".pytest_cache", "dist", "build"}
_PRIVATE_PARTS = {".git", ".github"}


@dataclass(frozen=True)
class ExportedFile:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ExportManifest:
    format_version: int
    source_root: str
    files: tuple[ExportedFile, ...]
    manifest_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "format_version": self.format_version,
            "source_root": self.source_root,
            "files": [asdict(item) for item in self.files],
            "manifest_sha256": self.manifest_sha256,
        }


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_generated(relative: Path) -> bool:
    return relative.suffix.lower() in _GENERATED_SUFFIXES or any(part in _GENERATED_PARTS for part in relative.parts)


def _candidate_files(source: Path) -> list[Path]:
    candidates: list[Path] = []
    for name in sorted(_ALLOWED_ROOT_FILES):
        path = source / name
        if path.is_file():
            candidates.append(path)
    for directory_name in sorted(_ALLOWED_DIRECTORIES):
        directory = source / directory_name
        if directory.is_dir():
            for path in directory.rglob("*"):
                if path.is_file() and not _is_generated(path.relative_to(source)):
                    candidates.append(path)
    return sorted(candidates, key=lambda item: item.relative_to(source).as_posix())


def _validate_relative(relative: Path) -> None:
    if relative.name in _FORBIDDEN_NAMES or relative.suffix.lower() in _FORBIDDEN_SUFFIXES:
        raise ExportError(f"forbidden artifact in export set: {relative.as_posix()}")
    if any(part in _PRIVATE_PARTS for part in relative.parts):
        raise ExportError(f"forbidden private path: {relative.as_posix()}")
    if relative.parts[0] not in _ALLOWED_DIRECTORIES and relative.as_posix() not in _ALLOWED_ROOT_FILES:
        raise ExportError(f"path is outside export allow-list: {relative.as_posix()}")


def rehearse_clean_export(source_root: str | Path, destination: str | Path) -> ExportManifest:
    source = Path(source_root).resolve()
    target = Path(destination).resolve()
    if not source.is_dir():
        raise ExportError("source root does not exist")
    try:
        target.relative_to(source)
    except ValueError:
        pass
    else:
        raise ExportError("export destination must not be inside the source tree")
    if target.exists() and any(target.iterdir()):
        raise ExportError("export destination must be absent or empty")
    target.mkdir(parents=True, exist_ok=True)
    files: list[ExportedFile] = []
    for path in _candidate_files(source):
        relative = path.relative_to(source)
        _validate_relative(relative)
        exported = target / relative
        exported.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, exported)
        if _digest(path) != _digest(exported):
            raise ExportError(f"copied file digest mismatch: {relative.as_posix()}")
        files.append(ExportedFile(relative.as_posix(), exported.stat().st_size, _digest(exported)))
    required_missing = sorted(name for name in _ALLOWED_ROOT_FILES if not (target / name).is_file())
    if required_missing:
        raise ExportError(f"required export files missing: {', '.join(required_missing)}")
    canonical = json.dumps([asdict(item) for item in files], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest = ExportManifest(1, str(source), tuple(files), hashlib.sha256(canonical.encode("utf-8")).hexdigest())
    (target / "EXPORT-MANIFEST.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
