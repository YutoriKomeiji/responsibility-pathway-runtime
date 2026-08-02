#!/usr/bin/env python3
"""Language: English comments; user-facing diagnostics are English/Japanese.

Validate the bounded public RPR repository before publicization or release.
Runtime tests, artifact reproducibility, and final release approval remain separate.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
EXPECTED_VERSION = "0.1.0a2"
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
    "site/index.html", "site/ja.html", "site/styles.css", "site/app.js",
    "examples/production-grade-demo/README.md", "examples/production-grade-demo/README.ja.md",
    ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/environment-report.yml", ".github/ISSUE_TEMPLATE/integration-request.yml",
    ".github/ISSUE_TEMPLATE/documentation.yml", ".github/pull_request_template.md",
    ".github/workflows/public-export-quality.yml", ".github/workflows/deploy-pages.yml",
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
    for name, data in (("release-manifest.json", release), ("product-status.json", status)):
        if data.get("version") != EXPECTED_VERSION:
            fail(f"unexpected version / version不一致: {name}")
            errors += 1
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
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid status JSON / status JSON不正: {exc}")
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
