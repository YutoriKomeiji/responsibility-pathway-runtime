from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_TOKEN = re.compile(r"\b0\.\d+\.\d+a\d+\b")
CURRENT_MARKERS = (
    "current published",
    "currently published",
    "current package baseline",
    "published package baseline",
    "current public alpha",
    "現在の公開",
    "現在pypiで公開中",
    "公開package baseline",
    "公開版は",
)

# These are deliberately broader than tools/validate_public_export.py's primary
# documentation path. The regression exists because a green intended-surface
# validator can still miss a second current-facing reader path.
ALTERNATE_CURRENT_SURFACES = (
    "README_PYPI.md",
    "SUPPORT.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    ".github/ISSUE_TEMPLATE/documentation.yml",
    ".github/ISSUE_TEMPLATE/integration-request.yml",
)


def test_alternate_current_surfaces_do_not_claim_a_superseded_published_version() -> None:
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    published = status["version"]

    findings: list[str] = []
    for relative in ALTERNATE_CURRENT_SURFACES:
        path = ROOT / relative
        assert path.is_file(), f"missing alternate current surface: {relative}"
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if not any(marker in lower for marker in CURRENT_MARKERS):
                continue
            wrong = sorted({v for v in VERSION_TOKEN.findall(line) if v != published})
            if wrong:
                findings.append(f"{relative}:{line_number}: {wrong} expected={published}")

    assert not findings, "stale current/published version claims: " + "; ".join(findings)


def test_pypi_readme_tracks_current_published_package_and_routing_boundary() -> None:
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    published = status["version"]
    text = (ROOT / "README_PYPI.md").read_text(encoding="utf-8")

    assert f"responsibility-pathway-runtime=={published}" in text
    assert "Responsibility Routing" in text
    assert "read-only route visibility" in text
    assert "do not create Authority" in text


def test_retired_doc_paths_are_not_reintroduced_by_alternate_current_surfaces() -> None:
    retired = (
        "responsibility-routing-migration.md",
        "release-candidate-0.1.0a3.md",
        "pre-public-audit-0.1.0a2.md",
        "docs/ja/writing-standard.md",
    )
    findings: list[str] = []
    for relative in ALTERNATE_CURRENT_SURFACES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for target in retired:
            if target in text:
                findings.append(f"{relative} -> {target}")
    assert not findings, "retired current-surface references: " + "; ".join(findings)


def test_repository_metadata_files_do_not_regress_current_release_identity() -> None:
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    published = status["version"]

    release_manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    assert release_manifest["version"] == published

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{published}"' in pyproject

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{published}]" in changelog
