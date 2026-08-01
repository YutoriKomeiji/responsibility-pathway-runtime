# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import json
from pathlib import Path

import pytest

from rpr.security_review import bundle_reviews, record_review


def test_review_record_hashes_external_report(tmp_path: Path) -> None:
    report = tmp_path / "secret-scan.json"
    report.write_text(json.dumps({"findings": []}), encoding="utf-8")
    record = record_review(
        review_type="secret_scan",
        tool="example-scanner",
        tool_version="1.0",
        target="clean-export",
        status="passed",
        report=report,
    )
    assert len(record.report_sha256) == 64
    bundle = bundle_reviews((record,))
    assert bundle["reviews"][0]["status"] == "passed"


def test_review_bundle_is_order_independent(tmp_path: Path) -> None:
    first_report = tmp_path / "first.json"
    second_report = tmp_path / "second.json"
    first_report.write_text("{}", encoding="utf-8")
    second_report.write_text("{}", encoding="utf-8")
    first = record_review(review_type="secret_scan", tool="a", tool_version="1", target="export", status="passed", report=first_report)
    second = record_review(review_type="vulnerability_review", tool="b", tool_version="2", target="wheel", status="needs_review", report=second_report)
    assert bundle_reviews((first, second))["bundle_sha256"] == bundle_reviews((second, first))["bundle_sha256"]


def test_unknown_status_is_rejected(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        record_review(review_type="secret_scan", tool="scanner", tool_version="1", target="export", status="unknown", report=report)
