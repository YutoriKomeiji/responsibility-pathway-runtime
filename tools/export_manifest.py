# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_TOP_LEVEL = {
    "src", "tests", "examples", "docs", "README.md", "LICENSE", "SECURITY.md",
    "pyproject.toml", "CITATION.cff", "CHANGELOG.md",
}
FORBIDDEN_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".log", ".pem", ".key", ".p12", ".pfx"}
FORBIDDEN_NAMES = {".env", "credentials.json", "secrets.json"}


def build_manifest(root: Path, *, source_commit: str) -> dict:
    files: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if relative.parts[0] not in ALLOWED_TOP_LEVEL:
            continue
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"forbidden export artifact: {relative.as_posix()}")
        data = path.read_bytes()
        files.append({
            "path": relative.as_posix(),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    if not files:
        raise ValueError("no export files found")
    return {
        "format": "rpr-clean-export-manifest-v1",
        "source_commit": source_commit,
        "file_count": len(files),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic RPR clean-export manifest")
    parser.add_argument("root", type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = build_manifest(args.root.resolve(), source_commit=args.source_commit)
    encoded = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
