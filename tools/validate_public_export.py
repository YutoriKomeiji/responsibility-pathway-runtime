#!/usr/bin/env python3
"""Validate bounded public RPR structure, lifecycle, and current-state claims.

Runtime tests, artifact reproducibility, release approval, publication, and public
readback remain separate. This validator turns known public-surface version and
lifecycle drift into reproducible failures without treating document-spec version
numbers or historical counterexample text as product-version claims.
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

ACTIVE_DOC_BASENAMES = (
    "README.md", "claim-boundary-promotion.md", "eu-ai-act-article-50.md",
    "install-operations-recovery.md", "mcp-integration.md", "product-governance.md",
    "product-scope-architecture.md", "quick-start.md", "security-integration-api.md",
    "support-maturity.md", "verification-release-uat.md",
)

REQUIRED_PATHS = (
    "README.md", "LICENSE", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "release-manifest.json", "product-status.json",
    "specs/pathway-state-machine.json", "specs/claim-traceability.json",
    "specs/test-id-registry.json", "specs/runtime-assurance-manifest-v1.json",
    "specs/integration-acceptance-inventory-v1.json",
    "specs/runtime-claim-assurance-case.md", "specs/runtime-product-test-specification.md",
    "formal/README.md", "formal/lean-toolchain", "formal/lakefile.toml",
    "formal/rprFormal/State.lean", "formal/rprFormal/Invariants.lean",
    "fixtures/lifecycle/previous-candidate-v1.json",
    *(f"docs/en/{name}" for name in ACTIVE_DOC_BASENAMES),
    *(f"docs/ja/{name}" for name in ACTIVE_DOC_BASENAMES),
    "examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md",
    "release-history/README.md", ".github/authoring/rpr-japanese-writing-standard.md",
    "site/index.html", "site/ja.html", "site/demo.html", "site/demo-en.html",
    "site/styles.css", "site/app.js",
    ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/environment-report.yml", ".github/ISSUE_TEMPLATE/integration-request.yml",
    ".github/ISSUE_TEMPLATE/documentation.yml", ".github/pull_request_template.md",
    ".github/workflows/public-export-quality.yml", ".github/workflows/deploy-pages.yml",
)

BILINGUAL_PAIRS = tuple(
    (f"docs/en/{name}", f"docs/ja/{name}") for name in ACTIVE_DOC_BASENAMES
) + (
    ("examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md"),
    ("site/index.html", "site/ja.html"),
    ("site/demo-en.html", "site/demo.html"),
)

USER_CURRENT_SURFACES = (
    "README.md",
    *(f"docs/en/{name}" for name in ACTIVE_DOC_BASENAMES),
    *(f"docs/ja/{name}" for name in ACTIVE_DOC_BASENAMES),
    "examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md",
    "site/index.html", "site/ja.html", "site/demo-en.html", "site/demo.html",
)
CURRENT_CONTROL_SPECS = (
    "specs/runtime-claim-assurance-case.md",
    "specs/runtime-product-test-specification.md",
)
ROUTING_REQUIRED_FILES = (
    "README.md", "docs/en/README.md", "docs/ja/README.md",
    "docs/en/mcp-integration.md", "docs/ja/mcp-integration.md",
    "docs/en/support-maturity.md", "docs/ja/support-maturity.md",
    "examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md",
    "site/index.html", "site/ja.html", "site/demo-en.html", "site/demo.html",
)
ROUTE_TOOL_REQUIRED_FILES = (
    "README.md", "docs/en/README.md", "docs/ja/README.md",
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
PRIVATE_PERSONA_PATTERNS = (re.compile(r"\bMaster approval\b", re.IGNORECASE), re.compile(r"マスター"))
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?([^\s\"']+)"
)
SAFE_SECRET_VALUES = {"", "none", "null", "redacted", "example", "placeholder", "test", "dummy", "changeme", "${secret}", "<secret>"}
VERSION_TOKEN = re.compile(r"\b0\.\d+\.\d+a\d+\b")
CURRENT_VERSION_MARKERS = (
    "current published", "currently published", "current package baseline",
    "published package baseline", "current public alpha", "current published line",
    "current published package", "現在の公開", "現在pypiで公開中", "公開package baseline",
    "公開版は", "公開中の版",
)
RETIRED_ACTIVE_REFERENCES = (
    "responsibility-routing-migration.md", "writing-standard.md",
    "release-candidate-0.1.0a3.md", "pre-public-audit-0.1.0a2.md",
)


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


def validate_active_doc_inventory() -> int:
    errors = 0
    expected = set(ACTIVE_DOC_BASENAMES)
    for language in ("en", "ja"):
        actual = {p.name for p in (ROOT / "docs" / language).glob("*.md") if p.is_file()}
        missing, extra = sorted(expected - actual), sorted(actual - expected)
        if missing:
            fail(f"active {language} docs missing / active docs不足: {missing}")
            errors += 1
        if extra:
            fail(f"historical/control/unknown docs remain active / active docsに余分な文書: {language}: {extra}")
            errors += 1
    return errors


def validate_status_files() -> tuple[int, str | None]:
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
    elif candidate is None and published_version != current_version:
        fail("product status version differs from current package version / product-statusと現行package versionが不一致")
        errors += 1
    elif candidate is not None:
        if not isinstance(candidate, dict) or candidate.get("state") not in {"release-candidate", "release-approved"}:
            fail("candidate release state is invalid / candidate release stateが不正です")
            errors += 1
        elif candidate.get("version") != current_version:
            fail("candidate version differs from current package version / candidateと現行package versionが不一致")
            errors += 1
        elif candidate.get("state") == "release-candidate" and (candidate.get("release_approved") is not False or candidate.get("publication_blocked") is not True):
            fail("unapproved candidate must be publication-blocked / 未承認candidateは公開停止が必要です")
            errors += 1
        elif candidate.get("state") == "release-approved" and (candidate.get("release_approved") is not True or candidate.get("publication_blocked") is not False):
            fail("approved candidate state is inconsistent / 承認済candidate stateが不整合です")
            errors += 1

    if not isinstance(published_version, str) or not published_version:
        fail("published product version is missing / 公開中product versionがありません")
        errors += 1
        published_version = None

    if not isinstance(release_version, str) or not release_version:
        fail("release manifest version is missing / release-manifestのversionがありません")
        errors += 1
    else:
        artifacts = release.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            fail("release manifest artifact evidence is missing / release-manifestのartifact evidenceがありません")
            errors += 1
        elif any(not isinstance(a, dict) or release_version not in str(a.get("name", "")) for a in artifacts):
            fail("release artifact version differs from frozen manifest / release artifactと凍結manifestのversionが不一致")
            errors += 1

    if status.get("status") == "integrity-repair-candidate":
        if status.get("freeze_id") is not None or status.get("previous_freeze_id") != PREVIOUS_FREEZE or status.get("publication_blocked") is not True:
            fail("repair candidate lifecycle is inconsistent / 修復候補lifecycleが不整合です")
            errors += 1
    elif status.get("freeze_id") != release.get("freeze_id"):
        fail("status and release freeze IDs differ / statusとreleaseのfreeze ID不一致")
        errors += 1

    return errors, published_version


def validate_user_current_surfaces(published_version: str | None) -> int:
    if not published_version:
        return 0
    errors = 0
    for relative in USER_CURRENT_SURFACES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()

        if relative.startswith("docs/"):
            header = re.search(r"(?m)^Version:\s*([^\s]+)\s*$", text)
            if header and header.group(1) != published_version:
                fail(f"active doc product Version mismatch / active doc Version不一致: {relative}={header.group(1)} expected={published_version}")
                errors += 1

        for line_number, line in enumerate(text.splitlines(), start=1):
            line_lower = line.lower()
            if any(marker in line_lower for marker in CURRENT_VERSION_MARKERS):
                wrong = sorted({v for v in VERSION_TOKEN.findall(line) if v != published_version})
                if wrong:
                    fail(f"stale current/published version claim / stale current version: {relative}:{line_number} {wrong} expected={published_version}")
                    errors += 1

        for retired in RETIRED_ACTIVE_REFERENCES:
            if retired in text:
                fail(f"retired/historical path remains on current surface / retired参照がcurrent surfaceに残存: {relative}: {retired}")
                errors += 1

        if published_version == "0.1.0a6":
            stale_routing = (
                r"Responsibility Routing.{0,180}(?:source preview|0\.1\.0a5)",
                r"(?:source preview|0\.1\.0a5).{0,180}Responsibility Routing",
            )
            if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in stale_routing):
                fail(f"released Responsibility Routing described with stale a5/source-preview semantics / Routing release状態drift: {relative}")
                errors += 1
    return errors


def validate_current_control_specs(published_version: str | None) -> int:
    if not published_version:
        return 0
    errors = 0
    for relative in CURRENT_CONTROL_SPECS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        baseline = re.search(r"(?m)^Published baseline:\s*`?([^`\s]+)`?\s*$", text)
        if not baseline or baseline.group(1) != published_version:
            fail(f"current control Published baseline mismatch / control baseline不一致: {relative} expected={published_version}")
            errors += 1
        if "Lifecycle: `CURRENT`" not in text:
            fail(f"current control missing CURRENT lifecycle / control lifecycle不足: {relative}")
            errors += 1
    return errors


def validate_bilingual_and_routing() -> int:
    errors = 0
    for english, japanese in BILINGUAL_PAIRS:
        en_path, ja_path = ROOT / english, ROOT / japanese
        if not en_path.is_file() or not ja_path.is_file():
            fail(f"active bilingual pair incomplete / 日英active pair不足: {english} <-> {japanese}")
            errors += 1
            continue
        en_text, ja_text = en_path.read_text(encoding="utf-8"), ja_path.read_text(encoding="utf-8")
        for anchor in ("Responsibility Routing", "rpr.get_route_visibility"):
            if (anchor in en_text) != (anchor in ja_text):
                fail(f"bilingual semantic anchor differs / 日英semantic anchor不一致: {anchor}: {english} <-> {japanese}")
                errors += 1

    for relative in ROUTING_REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file() and "Responsibility Routing" not in path.read_text(encoding="utf-8"):
            fail(f"Responsibility Routing missing / active surfaceにRouting不足: {relative}")
            errors += 1
    for relative in ROUTE_TOOL_REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file() and "rpr.get_route_visibility" not in path.read_text(encoding="utf-8"):
            fail(f"route visibility tool missing / route tool不足: {relative}")
            errors += 1
    for relative in ("site/demo-en.html", "site/demo.html"):
        path = ROOT / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for anchor in ("bounded_human_return", "hold_for_reconciliation", "authority_inferred"):
                if anchor not in text:
                    fail(f"browser demo routing evidence anchor missing / demo route anchor不足: {relative}: {anchor}")
                    errors += 1
    return errors


def validate_historical_and_authoring_boundaries() -> int:
    errors = 0
    history = ROOT / "release-history"
    if not history.is_dir() or not any(p.is_file() for p in history.rglob("*.md")):
        fail("release-history must preserve historical records / release-history履歴がありません")
        errors += 1
    authoring = ROOT / ".github" / "authoring" / "rpr-japanese-writing-standard.md"
    if authoring.is_file() and "AUTHORING_CONTROL" not in authoring.read_text(encoding="utf-8"):
        fail("writing standard must be AUTHORING_CONTROL / writing standard lifecycle不足")
        errors += 1
    snapshot = json.loads((ROOT / "tests/public-test-scope.json").read_text(encoding="utf-8"))
    if snapshot.get("record_type") != "historical_test_scope_snapshot" or snapshot.get("status") != "historical_keep":
        fail("public-test-scope historical lifecycle classification is invalid / historical snapshot分類不正")
        errors += 1
    if "current_published_version" in snapshot:
        fail("historical snapshot retains misleading current_published_version / historical snapshotにcurrent field残存")
        errors += 1
    return errors


def main() -> int:
    errors = 0
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"missing required path / 必須path不足: {relative}")
            errors += 1
    errors += validate_active_doc_inventory()

    published_version = None
    if not errors:
        try:
            status_errors, published_version = validate_status_files()
            errors += status_errors
            errors += validate_user_current_surfaces(published_version)
            errors += validate_current_control_specs(published_version)
            errors += validate_bilingual_and_routing()
            errors += validate_historical_and_authoring_boundaries()
        except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
            fail(f"invalid status/lifecycle metadata / status・lifecycle metadata不正: {exc}")
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
        if is_public_surface(relative) and any(p.search(text) for p in INTERNAL_PATTERNS):
            fail(f"internal development reference on public surface / 公開面の内部開発参照: {relative}")
            errors += 1
        if is_public_surface(relative) and any(p.search(text) for p in PRIVATE_PERSONA_PATTERNS):
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
    print("PASS / 合格: public product structural, lifecycle, and current-state validation completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
