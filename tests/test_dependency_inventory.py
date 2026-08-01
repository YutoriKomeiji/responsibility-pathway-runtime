# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from pathlib import Path

from rpr.dependency_inventory import inventory_pyproject


def test_dependency_inventory_is_deterministic(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[build-system]\nrequires = [\"setuptools>=68\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"example\"\nversion = \"1.2.3\"\ndependencies = [\"beta>=2\", \"alpha==1\"]\n\n[project.optional-dependencies]\ndev = [\"pytest>=8\", \"build\"]\n""",
        encoding="utf-8",
    )
    first = inventory_pyproject(pyproject)
    second = inventory_pyproject(pyproject)
    assert first.inventory_sha256 == second.inventory_sha256
    assert first.runtime == ("alpha==1", "beta>=2")
    assert first.optional["dev"] == ("build", "pytest>=8")


def test_current_project_declares_no_runtime_dependency() -> None:
    inventory = inventory_pyproject(Path(__file__).parents[1] / "pyproject.toml")
    assert inventory.project_name == "responsibility-pathway-runtime"
    assert inventory.runtime == ()
    assert inventory.build_system
