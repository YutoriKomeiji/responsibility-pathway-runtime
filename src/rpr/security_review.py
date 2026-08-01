# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ReviewRecord:
    review_type: str
    tool: str
    tool_version: str
    target: str
    status: str
    report_sha256: str
    notes: str = ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_review(*, review_type: str, tool: str, tool_version: str, target: str, status: str, report: str | Path, notes: str = "") -> ReviewRecord:
    allowed = {"passed", "failed", "needs_review"}
    if status not in allowed:
        raise ValueError(f"status must be one of {sorted(allowed)}")
    report_path = Path(report)
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    return ReviewRecord(review_type, tool, tool_version, target, status, _sha256(report_path), notes)


def bundle_reviews(records: Iterable[ReviewRecord]) -> dict[str, object]:
    ordered = sorted(records, key=lambda item: (item.review_type, item.tool, item.target))
    canonical = json.dumps([asdict(item) for item in ordered], sort_keys=True, separators=(",", ":"))
    return {
        "format_version": 1,
        "reviews": [asdict(item) for item in ordered],
        "bundle_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an independently generated release-security review report.")
    parser.add_argument("report")
    parser.add_argument("--review-type", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--tool-version", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--status", choices=("passed", "failed", "needs_review"), required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", default="security-review.json")
    args = parser.parse_args()
    record = record_review(review_type=args.review_type, tool=args.tool, tool_version=args.tool_version, target=args.target, status=args.status, report=args.report, notes=args.notes)
    Path(args.output).write_text(json.dumps(bundle_reviews((record,)), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
