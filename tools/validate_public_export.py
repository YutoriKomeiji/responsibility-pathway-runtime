#!/usr/bin/env python3
"""Language: English comments; user-facing diagnostics are English/Japanese.

Validate the bounded public RPR repository assembly before promotion.
This checker validates export structure, public-surface residue, and likely
credential literals. Runtime tests and final release approval remain separate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

REQUIRED_PATHS = (
    "README.md", "LICENSE", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "release-manifest.json", "product-status.json",
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

TEXT_SUFFIXES = {".md", ".html", ".css", ".js", ".json", ".yml", ".yaml", ".toml", ".py"}
PUBLIC_SURFACE_PREFIXES = ("README.md", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/", "site/", ".github/")
INTERNAL_PATTERNS = (
    re.compile(r"responsibility-pathway-program", re.IGNORECASE),
    re.compile(r"incubator/rpr", re.IGNORECASE),
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


def main() -> int:
    errors = 0
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"missing required path / 必須path不足: {relative}")
            errors += 1

    for json_name in ("release-manifest.json", "product-status.json"):
        path = ROOT / json_name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid JSON / JSON不正: {json_name}: {exc}")
            errors += 1
            continue
        if data.get("version") != "0.1.0a2":
            fail(f"unexpected version / version不一致: {json_name}")
            errors += 1
        if data.get("freeze_id") != "RPR-CF-2026-08-01-02":
            fail(f"unexpected freeze_id / freeze_id不一致: {json_name}")
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
        if has_likely_secret(text):
            fail(f"likely credential literal / credential実値らしき内容: {relative}")
            errors += 1

    english_site = ROOT / "site/index.html"
    japanese_site = ROOT / "site/ja.html"
    if english_site.is_file() and 'href="ja.html"' not in english_site.read_text(encoding="utf-8"):
        fail("English site lacks Japanese navigation / 英語siteに日本語導線なし")
        errors += 1
    if japanese_site.is_file() and 'href="index.html"' not in japanese_site.read_text(encoding="utf-8"):
        fail("Japanese site lacks English navigation / 日本語siteに英語導線なし")
        errors += 1

    if errors:
        print(f"FAILED / 失敗: {errors} finding(s) / {errors}件")
        return 1
    print("PASS / 合格: public export structural validation completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
