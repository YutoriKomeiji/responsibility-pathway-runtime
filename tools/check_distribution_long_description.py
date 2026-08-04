# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import re
import tomllib
import zipfile
from pathlib import Path


class MetadataValidationError(RuntimeError):
    pass


def _project_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _wheel_metadata(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise MetadataValidationError(f"expected one METADATA file in {wheel}, found {len(names)}")
        return archive.read(names[0]).decode("utf-8")


def validate(root: Path, dist: Path) -> dict[str, str]:
    version = _project_version(root)
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise MetadataValidationError(f"expected one wheel in {dist}, found {len(wheels)}")

    metadata = _wheel_metadata(wheels[0])
    header, separator, description = metadata.partition("\n\n")
    if not separator:
        raise MetadataValidationError("wheel METADATA has no long-description body")

    if f"Version: {version}\n" not in header + "\n":
        raise MetadataValidationError(f"METADATA Version does not match pyproject version {version}")

    expected_markers = (
        f"Public Alpha — {version}",
        f"responsibility-pathway-runtime=={version}",
        "Published read-only MCP inspection server",
        "2025-11-25",
    )
    for marker in expected_markers:
        if marker not in description:
            raise MetadataValidationError(f"long description is missing required marker: {marker}")

    forbidden_phrases = (
        "Unreleased read-only server preview",
        "This read-only MCP server is an unreleased source preview",
        "Published PyPI `0.1.0a2`",
        "Public Alpha — 0.1.0a2",
    )
    for phrase in forbidden_phrases:
        if phrase in description:
            raise MetadataValidationError(f"long description retains stale phrase: {phrase}")

    advertised = set(re.findall(r"Public Alpha — ([0-9]+\.[0-9]+\.[0-9]+a[0-9]+)", description))
    if advertised != {version}:
        raise MetadataValidationError(
            f"long description advertises unexpected alpha versions: {sorted(advertised)}; expected {version}"
        )

    return {"version": version, "wheel": wheels[0].name, "status": "validated"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    result = validate(args.root.resolve(), args.dist.resolve())
    print(f"distribution long description validated: {result['wheel']} ({result['version']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
