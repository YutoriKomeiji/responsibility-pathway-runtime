# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class DependencyInventory:
    project_name: str
    project_version: str
    runtime: tuple[str, ...]
    optional: Mapping[str, tuple[str, ...]]
    build_system: tuple[str, ...]
    inventory_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "project_version": self.project_version,
            "runtime": list(self.runtime),
            "optional": {key: list(value) for key, value in sorted(self.optional.items())},
            "build_system": list(self.build_system),
            "inventory_sha256": self.inventory_sha256,
        }


def inventory_pyproject(path: str | Path) -> DependencyInventory:
    pyproject = Path(path)
    value = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = value.get("project", {})
    build = value.get("build-system", {})
    runtime = tuple(sorted(str(item) for item in project.get("dependencies", [])))
    optional = {
        str(group): tuple(sorted(str(item) for item in items))
        for group, items in dict(project.get("optional-dependencies", {})).items()
    }
    build_system = tuple(sorted(str(item) for item in build.get("requires", [])))
    canonical_value = {
        "project_name": str(project.get("name", "")),
        "project_version": str(project.get("version", "")),
        "runtime": runtime,
        "optional": {key: optional[key] for key in sorted(optional)},
        "build_system": build_system,
    }
    canonical = json.dumps(canonical_value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return DependencyInventory(
        canonical_value["project_name"],
        canonical_value["project_version"],
        runtime,
        optional,
        build_system,
        hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit the declared RPR dependency inventory.")
    parser.add_argument("pyproject", nargs="?", default="pyproject.toml")
    parser.add_argument("--output")
    args = parser.parse_args()
    inventory = inventory_pyproject(args.pyproject)
    encoded = json.dumps(inventory.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
