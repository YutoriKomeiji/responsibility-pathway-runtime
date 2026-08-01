# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _component_name(requirement: str) -> str:
    for marker in ("[", "<", ">", "=", "!", "~", ";", " "):
        requirement = requirement.split(marker, 1)[0]
    return requirement.strip()


def generate_cyclonedx_sbom(pyproject: str | Path, *, source_commit: str = "UNKNOWN") -> dict[str, Any]:
    path = Path(pyproject)
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    name = str(project.get("name", "")).strip()
    version = str(project.get("version", "")).strip()
    if not name or not version:
        raise ValueError("project name and version are required")
    requirements = sorted(str(item) for item in project.get("dependencies", []))
    components = [
        {
            "type": "library",
            "name": _component_name(requirement),
            "version": requirement[len(_component_name(requirement)):].strip() or "UNSPECIFIED",
            "properties": [{"name": "rpr:declared-requirement", "value": requirement}],
        }
        for requirement in requirements
    ]
    serial_seed = f"{name}:{version}:{source_commit}:" + "|".join(requirements)
    serial = hashlib.sha256(serial_seed.encode("utf-8")).hexdigest()
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{serial[:8]}-{serial[8:12]}-{serial[12:16]}-{serial[16:20]}-{serial[20:32]}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "tools": {"components": [{"type": "application", "name": "rpr-sbom", "version": "1"}]},
            "component": {
                "type": "application",
                "name": name,
                "version": version,
                "properties": [{"name": "rpr:source-commit", "value": source_commit}],
            },
        },
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic-structure CycloneDX JSON SBOM from pyproject metadata.")
    parser.add_argument("pyproject", nargs="?", default="pyproject.toml")
    parser.add_argument("--source-commit", default="UNKNOWN")
    parser.add_argument("--output", default="sbom.cdx.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.write_text(json.dumps(generate_cyclonedx_sbom(args.pyproject, source_commit=args.source_commit), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
