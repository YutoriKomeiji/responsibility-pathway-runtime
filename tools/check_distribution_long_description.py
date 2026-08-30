# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
import re
import tomllib
import zipfile
from pathlib import Path


class MetadataValidationError(RuntimeError):
    pass


def _project_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _product_status(root: Path) -> dict[str, object]:
    return json.loads((root / "product-status.json").read_text(encoding="utf-8"))


def _wheel_metadata(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise MetadataValidationError(f"expected one METADATA file in {wheel}, found {len(names)}")
        return archive.read(names[0]).decode("utf-8")


def validate(root: Path, dist: Path) -> dict[str, str]:
    version = _project_version(root)
    status = _product_status(root)
    candidate = status.get("candidate")
    is_candidate = isinstance(candidate, dict) and candidate.get("version") == version

    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise MetadataValidationError(f"expected one wheel in {dist}, found {len(wheels)}")

    metadata = _wheel_metadata(wheels[0])
    header, separator, description = metadata.partition("\n\n")
    if not separator:
        raise MetadataValidationError("wheel METADATA has no long-description body")

    if f"Version: {version}\n" not in header + "\n":
        raise MetadataValidationError(f"METADATA Version does not match pyproject version {version}")

    if is_candidate:
        expected_markers = (
            f"Release Candidate — {version}",
            "Unpublished candidate",
            "Published read-only MCP inspection server",
            "2025-11-25",
        )
        forbidden_candidate_phrases = (
            f"python -m pip install responsibility-pathway-runtime=={version}",
            f"releases/tag/v{version}",
        )
        for phrase in forbidden_candidate_phrases:
            if phrase in description:
                raise MetadataValidationError(f"candidate long description advertises an unpublished surface: {phrase}")
    else:
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

    public_alphas = set(re.findall(r"Public Alpha — ([0-9]+\.[0-9]+\.[0-9]+a[0-9]+)", description))
    release_candidates = set(re.findall(r"Release Candidate — ([0-9]+\.[0-9]+\.[0-9]+a[0-9]+)", description))
    if is_candidate:
        if release_candidates != {version}:
            raise MetadataValidationError(
                f"candidate long description advertises unexpected candidate versions: {sorted(release_candidates)}; expected {version}"
            )
    elif public_alphas != {version}:
        raise MetadataValidationError(
            f"long description advertises unexpected alpha versions: {sorted(public_alphas)}; expected {version}"
        )

    return {
        "version": version,
        "wheel": wheels[0].name,
        "status": "candidate-validated" if is_candidate else "validated",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    result = validate(args.root.resolve(), args.dist.resolve())
    print(f"distribution long description validated: {result['wheel']} ({result['version']}, {result['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
