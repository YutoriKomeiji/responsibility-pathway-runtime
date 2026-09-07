#!/usr/bin/env python3
"""Language: English comments; user-facing diagnostics are English/Japanese.

Validate the bounded public RPR repository before publicization or release.
Runtime tests, artifact reproducibility, and final release approval remain separate.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
PREVIOUS_FREEZE = "RPR-CF-2026-08-01-02"

REQUIRED_PATHS = (
    "README.md", "LICENSE", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "release-manifest.json", "product-status.json",
    "specs/pathway-state-machine.json", "specs/claim-traceability.json",
    "specs/test-id-registry.json", "specs/runtime-assurance-manifest-v1.json",
    "specs/integration-acceptance-inventory-v1.json",
    "formal/README.md", "formal/lean-toolchain", "formal/lakefile.toml",
    "formal/rprFormal/State.lean", "formal/rprFormal/Invariants.lean",
    "fixtures/lifecycle/previous-candidate-v1.json",
    "docs/en/README.md", "docs/ja/README.md",
    "docs/en/quick-start.md", "docs/ja/quick-start.md",
    "docs/en/install-operations-recovery.md", "docs/ja/install-operations-recovery.md",
    "docs/en/product-scope-architecture.md", "docs/ja/product-scope-architecture.md",
    "docs/en/security-integration-api.md", "docs/ja/security-integration-api.md",
    "docs/en/verification-release-uat.md", "docs/ja/verification-release-uat.md",
    "docs/en/mcp-integration.md", "docs/ja/mcp-integration.md",
    "docs/en/responsibility-routing-migration.md", "docs/ja/responsibility-routing-migration.md",
    "docs/en/support-maturity.md", "docs/ja/support-maturity.md",
    "site/index.html", "site/ja.html", "site/demo.html", "site/demo-en.html",
    "site/styles.css", "site/app.js",
    "examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md",
    ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/environment-report.yml", ".github/ISSUE_TEMPLATE/integration-request.yml",
    ".github/ISSUE_TEMPLATE/documentation.yml", ".github/pull_request_template.md",
    ".github/workflows/public-export-quality.yml", ".github/workflows/deploy-pages.yml",
)

BILINGUAL_PAIRS = (
    ("docs/en/README.md", "docs/ja/README.md"),
    ("docs/en/claim-boundary-promotion.md", "docs/ja/claim-boundary-promotion.md"),
    ("docs/en/eu-ai-act-article-50.md", "docs/ja/eu-ai-act-article-50.md"),
    ("docs/en/install-operations-recovery.md", "docs/ja/install-operations-recovery.md"),
    ("docs/en/mcp-integration.md", "docs/ja/mcp-integration.md"),
    ("docs/en/product-governance.md", "docs/ja/product-governance.md"),
    ("docs/en/product-scope-architecture.md", "docs/ja/product-scope-architecture.md"),
    ("docs/en/quick-start.md", "docs/ja/quick-start.md"),
    ("docs/en/responsibility-routing-migration.md", "docs/ja/responsibility-routing-migration.md"),
    ("docs/en/security-integration-api.md", "docs/ja/security-integration-api.md"),
    ("docs/en/support-maturity.md", "docs/ja/support-maturity.md"),
    ("docs/en/verification-release-uat.md", "docs/ja/verification-release-uat.md"),
    ("examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md"),
    ("site/index.html", "site/ja.html"),
    ("site/demo-en.html", "site/demo.html"),
)

ACTIVE_VERSIONED_DOCS = (
    "docs/en/README.md", "docs/ja/README.md",
    "docs/en/install-operations-recovery.md", "docs/ja/install-operations-recovery.md",
    "docs/en/mcp-integration.md", "docs/ja/mcp-integration.md",
    "docs/en/product-scope-architecture.md", "docs/ja/product-scope-architecture.md",
    "docs/en/security-integration-api.md", "docs/ja/security-integration-api.md",
    "docs/en/verification-release-uat.md", "docs/ja/verification-release-uat.md",
)

ROUTING_REQUIRED_FILES = (
    "README.md",
    "docs/en/README.md", "docs/ja/README.md",
    "docs/en/mcp-integration.md", "docs/ja/mcp-integration.md",
    "docs/en/responsibility-routing-migration.md", "docs/ja/responsibility-routing-migration.md",
    "site/index.html", "site/ja.html",
    "site/demo-en.html", "site/demo.html",
)

ROUTE_TOOL_REQUIRED_FILES = (
    "README.md",
    "docs/en/README.md", "docs/ja/README.md",
    "docs/en/mcp-integration.md", "docs/ja/mcp-integration.md",
    "site/demo-en.html", "site/demo.html",
)

TEXT_SUFFIXES = {".md", ".html", ".css", ".js", ".json", ".yml", ".yaml", ".toml", ".py", ".lean"}
PUBLIC_SURFACE_PREFIXES = (
    "README.md", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    "docs/", "site/", ".github/", "formal/", "specs/", "product-status.json", "release-manifest.json",
)
INTERNAL_PATTERNS = (
    re.compile(r"responsibility-pathway-program", re.IGNORECASE),
    re.compile(r"incubator/rpr", re.IGNORECASE),
    re.compile(r"private_rpp_development_only", re.IGNORECASE),
)
PRIVATE_PERSONA_PATTERNS = (
    re.compile(r"\bMaster approval\b", re.IGNORECASE),
    re.compile(r"マスター"),
)
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?([^\s\"']+)",
)
SAFE_SECRET_VALUES = {"", "none", "null", "redacted", "example", "placeholder", "test", "dummy", "changeme", "${secret}", "<secret>"}


def fail(message: str) -> None:
    print(f"ERROR / エラー: {message}")


def is_public_surface(relative: str) -> bool:
    return any(relative == prefix or relative.startswith(prefix) for prefix in PUBLIC_SURFACE_PREFIXES)


def has_likely_secret(text: str) -> bool:
    for match in SECRET_ASSIGNMENT.finditer(text):
        value = match.group(1).strip().lower()
        if value in SAFE_SECRET_VALUES or value.startswith(("test-", "dummy-", "example-", "placeholder-")):
            continue
        if len(value) >= 12:
            return True
    return False


def validate_status_files() -> int:
    errors = 0
    release = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    status = json.loads((ROOT / "product-status.json").read_text(encoding="utf-8"))
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    current_version = project.get("project", {}).get("version")
    published_version = status.get("version")
    release_version = release.get("version")
    candidate = status.get("candidate")

    if not isinstance(current_version, str) or not current_version:
        fail("pyproject project version is missing / pyprojectのproject versionがありません")
        errors += 1
    elif candidate is None:
        if published_version != current_version:
            fail("product status version differs from current package version / product-statusと現行package versionが不一致")
            errors += 1
    elif not isinstance(candidate, dict):
        fail("candidate release state must be an object / candidate release stateはobjectである必要があります")
        errors += 1
    else:
        candidate_version = candidate.get("version")
        candidate_state = candidate.get("state")
        if candidate_state not in {"release-candidate", "release-approved"}:
            fail("candidate state must be release-candidate or release-approved / candidate stateが不正です")
            errors += 1
        if candidate_version != current_version:
            fail("candidate version differs from current package version / candidateと現行package versionが不一致")
            errors += 1
        if candidate_state == "release-candidate":
            if candidate.get("release_approved") is not False or candidate.get("publication_blocked") is not True:
                fail("unapproved candidate must be unapproved and publication-blocked / 未承認candidateは未承認かつ公開停止である必要があります")
                errors += 1
        elif candidate_state == "release-approved":
            if candidate.get("release_approved") is not True or candidate.get("publication_blocked") is not False:
                fail("approved candidate must be approved and publication-enabled / 承認済candidateは承認済かつ公開可能である必要があります")
                errors += 1
        if not isinstance(published_version, str) or not published_version:
            fail("published product version is missing / 公開中product versionがありません")
            errors += 1

    if not isinstance(release_version, str) or not release_version:
        fail("release manifest version is missing / release-manifestのversionがありません")
        errors += 1
    else:
        artifacts = release.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            fail("release manifest artifact evidence is missing / release-manifestのartifact evidenceがありません")
            errors += 1
        else:
            for artifact in artifacts:
                name = artifact.get("name") if isinstance(artifact, dict) else None
                if not isinstance(name, str) or release_version not in name:
                    fail("release artifact version differs from frozen manifest / release artifactと凍結manifestのversionが不一致")
                    errors += 1
                    break

    if status.get("status") == "integrity-repair-candidate":
        if status.get("freeze_id") is not None or status.get("previous_freeze_id") != PREVIOUS_FREEZE:
            fail("repair candidate must invalidate the previous freeze / 修復候補は旧freezeを無効化する必要があります")
            errors += 1
        if status.get("publication_blocked") is not True:
            fail("repair candidate must block publication / 修復候補は公開停止が必要です")
            errors += 1
    elif status.get("freeze_id") != release.get("freeze_id"):
        fail("status and release freeze IDs differ / statusとreleaseのfreeze ID不一致")
        errors += 1

    if isinstance(published_version, str) and published_version:
        for relative in ACTIVE_VERSIONED_DOCS:
            path = ROOT / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            version_match = re.search(r"(?m)^Version:\s*([^\s]+)\s*$", text)
            if version_match and version_match.group(1) != published_version:
                fail(
                    f"active document version differs from published product / 公開中document version不一致: "
                    f"{relative}={version_match.group(1)} published={published_version}"
                )
                errors += 1
    return errors


def validate_bilingual_and_routing_surfaces() -> int:
    errors = 0
    for english, japanese in BILINGUAL_PAIRS:
        en_path, ja_path = ROOT / english, ROOT / japanese
        if not en_path.is_file() or not ja_path.is_file():
            fail(f"active bilingual pair incomplete / 日英active pair不足: {english} <-> {japanese}")
            errors += 1
            continue
        en_text = en_path.read_text(encoding="utf-8")
        ja_text = ja_path.read_text(encoding="utf-8")
        for anchor in ("Responsibility Routing", "rpr.get_route_visibility"):
            if (anchor in en_text) != (anchor in ja_text):
                fail(
                    f"bilingual semantic anchor differs / 日英semantic anchor不一致: "
                    f"{anchor}: {english} <-> {japanese}"
                )
                errors += 1

    for relative in ROUTING_REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file() and "Responsibility Routing" not in path.read_text(encoding="utf-8"):
            fail(f"Responsibility Routing missing from active product surface / active surfaceにRouting不足: {relative}")
            errors += 1

    for relative in ROUTE_TOOL_REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file() and "rpr.get_route_visibility" not in path.read_text(encoding="utf-8"):
            fail(f"route visibility tool missing from active product surface / route tool不足: {relative}")
            errors += 1

    for relative in ("site/demo-en.html", "site/demo.html"):
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for anchor in ("bounded_human_return", "hold_for_reconciliation", "authority_inferred"):
            if anchor not in text:
                fail(f"browser demo routing evidence anchor missing / demo route anchor不足: {relative}: {anchor}")
                errors += 1
    return errors


def main() -> int:
    errors = 0
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"missing required path / 必須path不足: {relative}")
            errors += 1
    if not errors:
        try:
            errors += validate_status_files()
            errors += validate_bilingual_and_routing_surfaces()
        except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            fail(f"invalid status metadata / status metadata不正: {exc}")
            errors += 1

    for path in ROOT.rglob("*"):
        if path.resolve() == SELF or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(f"non-UTF-8 text / UTF-8以外のtext: {relative}")
            errors += 1
            continue
        if is_public_surface(relative) and any(pattern.search(text) for pattern in INTERNAL_PATTERNS):
            fail(f"internal development reference on public surface / 公開面の内部開発参照: {relative}")
            errors += 1
        if is_public_surface(relative) and any(pattern.search(text) for pattern in PRIVATE_PERSONA_PATTERNS):
            fail(f"private persona term on public surface / 公開面の内部人格語: {relative}")
            errors += 1
        if has_likely_secret(text):
            fail(f"likely credential literal / credential実値らしき内容: {relative}")
            errors += 1

    if (ROOT / "site/index.html").is_file() and 'href="ja.html"' not in (ROOT / "site/index.html").read_text(encoding="utf-8"):
        fail("English site lacks Japanese navigation / 英語siteに日本語導線なし")
        errors += 1
    if (ROOT / "site/ja.html").is_file() and 'href="index.html"' not in (ROOT / "site/ja.html").read_text(encoding="utf-8"):
        fail("Japanese site lacks English navigation / 日本語siteに英語導線なし")
        errors += 1

    if errors:
        print(f"FAILED / 失敗: {errors} finding(s) / {errors}件")
        return 1
    print("PASS / 合格: public product structural validation completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
