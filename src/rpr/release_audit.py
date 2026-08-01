# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

_REQUIRED = {
    "README.md", "LICENSE", "SECURITY.md", "CHANGELOG.md", "CITATION.cff", "pyproject.toml"
}
_FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx", ".log"}
_FORBIDDEN_NAMES = {".env", "credentials.json", "secrets.json"}


@dataclass(frozen=True)
class AuditFinding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReleaseAuditReport:
    valid: bool
    files_checked: int
    archives_checked: int
    findings: tuple[AuditFinding, ...]
    manifest_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "files_checked": self.files_checked,
            "archives_checked": self.archives_checked,
            "findings": [asdict(item) for item in self.findings],
            "manifest_sha256": self.manifest_sha256,
        }


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _members(path: Path) -> Iterable[str]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            yield from archive.namelist()
    elif path.name.endswith(".tar.gz") or path.suffix in {".tar", ".tgz"}:
        with tarfile.open(path) as archive:
            yield from (member.name for member in archive.getmembers())


def audit_release_tree(root: str | Path, *, dist: str | Path | None = None) -> ReleaseAuditReport:
    base = Path(root).resolve()
    findings: list[AuditFinding] = []
    manifest: list[dict[str, object]] = []

    for required in sorted(_REQUIRED):
        if not (base / required).is_file():
            findings.append(AuditFinding("required_file_missing", required, "required release file is missing"))

    files = sorted(path for path in base.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(base).as_posix()
        if path.name in _FORBIDDEN_NAMES or path.suffix.lower() in _FORBIDDEN_SUFFIXES:
            findings.append(AuditFinding("forbidden_artifact", relative, "private or runtime artifact must not be exported"))
        manifest.append({"path": relative, "size": path.stat().st_size, "sha256": _digest(path)})

    archives_checked = 0
    if dist is not None:
        dist_path = Path(dist).resolve()
        archives = sorted(path for path in dist_path.glob("*") if path.is_file())
        for archive in archives:
            archives_checked += 1
            for member in _members(archive):
                normalized = Path(member)
                if normalized.name in _FORBIDDEN_NAMES or normalized.suffix.lower() in _FORBIDDEN_SUFFIXES:
                    findings.append(AuditFinding("forbidden_archive_member", f"{archive.name}:{member}", "forbidden artifact found in distribution archive"))
                if "incubator/" in member or "responsibility-pathway-program" in member:
                    findings.append(AuditFinding("private_path_leak", f"{archive.name}:{member}", "private incubator path leaked into distribution"))

    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return ReleaseAuditReport(not findings, len(files), archives_checked, tuple(findings), hashlib.sha256(canonical.encode("utf-8")).hexdigest())


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an RPR release rehearsal tree and optional distribution archives.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--dist")
    parser.add_argument("--output")
    args = parser.parse_args()
    report = audit_release_tree(args.root, dist=args.dist)
    encoded = json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
