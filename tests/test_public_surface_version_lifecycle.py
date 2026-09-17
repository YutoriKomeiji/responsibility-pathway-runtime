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

# Release preparation is future-version-first: once pyproject.toml is moved to
# the next candidate version, every active/current-facing version-bearing
# surface must move with it before GitHub/PyPI publication.
ACTIVE_VERSION_SURFACES = (
    "README.md",
    "README_PYPI.md",
    "docs/en/README.md",
    "docs/ja/README.md",
    "docs/en/verification-release-uat.md",
    "docs/ja/verification-release-uat.md",
    "site/index.html",
    "site/ja.html",
)


def test_active_version_bearing_surfaces_match_project_release_identity() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, flags=re.MULTILINE)
    assert match, "pyproject.toml project version not found"
    project_version = match.group(1)

    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    candidate = status.get("candidate")
    if isinstance(candidate, dict) and candidate.get("state") in {"release-candidate", "release-approved"}:
        assert candidate.get("version") == project_version
    else:
        assert status["version"] == project_version

    findings: list[str] = []
    for relative in ACTIVE_VERSION_SURFACES:
        path = ROOT / relative
        assert path.is_file(), f"missing active version surface: {relative}"
        text = path.read_text(encoding="utf-8")
        if project_version not in text:
            findings.append(relative)

    assert not findings, (
        "release identity drift: active/current-facing version-bearing surfaces "
        f"must move to {project_version} before external publication: {findings}"
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


def test_current_repository_metadata_tracks_current_published_identity() -> None:
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    published = status["version"]

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{published}"' in pyproject

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{published}]" in changelog


def test_frozen_release_manifest_remains_historical_evidence_not_current_identity() -> None:
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    published = status["version"]
    release_manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))

    frozen_version = release_manifest["version"]
    assert frozen_version != published
    assert release_manifest["freeze_id"]
    assert release_manifest["artifact_source_commit"]
    assert release_manifest["verification_run_id"]

    artifacts = release_manifest.get("artifacts")
    assert isinstance(artifacts, list) and artifacts
    for artifact in artifacts:
        assert frozen_version in artifact["name"]
        assert artifact["sha256"]

    # Lifecycle boundary: this manifest is retained evidence for its own frozen
    # release lineage. It must not be rewritten merely to mirror current state.
    assert release_manifest["status"]["public_release_approved"] is False
