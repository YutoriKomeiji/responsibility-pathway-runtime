# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Fail when active pre-release RPY identifiers remain after the RPR migration.

Only the naming history, this scanner, and explicitly bounded negative references are
excluded. Broad directory exclusions are intentionally avoided so active source, tests,
workflows, documentation, packaging, and release evidence remain auditable.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

LEGACY_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:RPY|Rpy|rpy)(?![A-Za-z0-9_])")
TEXT_SUFFIXES = {
    ".c",
    ".cfg",
    ".cff",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".lean",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist", "__pycache__"}
APPROVED_FILES = {
    Path("incubator/rpr/docs/rpr-naming-migration.md"),
    Path("incubator/rpr/tools/check_rpr_rename.py"),
}
APPROVED_NEGATIVE_REFERENCES = {
    Path("incubator/rpr/specs/runtime-product-test-specification.md"): {
        "No legacy `rpy` package name, incubator-only path, stale repository URL, or unintended private path may remain in exported product artifacts."
    },
    Path("incubator/rpr/specs/development-production-environment-model.md"): {
        "- stale `rpy` naming or migration residue;"
    },
}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE", "Makefile"}:
            yield path


def find_legacy_references(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(root):
        relative = path.relative_to(root)
        if relative in APPROVED_FILES:
            continue
        approved_lines = APPROVED_NEGATIVE_REFERENCES.get(relative, set())
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if line.strip() in approved_lines:
                continue
            if LEGACY_PATTERN.search(line):
                findings.append(f"{relative}:{line_number}:{line.strip()}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    findings = find_legacy_references(root)
    if findings:
        print("Active legacy RPY identifiers remain:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("No unapproved active RPY identifiers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
