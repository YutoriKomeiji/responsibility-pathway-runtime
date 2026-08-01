# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Write a stable CI report for human and agent catch-up."""

from __future__ import annotations

import json
import os
from pathlib import Path


STEP_KEYS = (
    ("install", "Install test and build tools"),
    ("tests", "Test suite"),
    ("formal_consistency", "Formal consistency"),
    ("transition_parity", "Canonical transition parity"),
    ("build", "Build wheel and source distribution"),
    ("wheel_install", "Isolated wheel install and CLI"),
    ("sdist_install", "Isolated source install and CLI"),
    ("release_audit", "Release audit"),
    ("residue_scan", "Legacy identifier residue scan"),
)


def main() -> int:
    output_dir = Path(os.environ.get("RPR_CI_REPORT_DIR", ".ci-report"))
    output_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        {
            "id": key,
            "name": name,
            "outcome": os.environ.get(f"RPR_STEP_{key.upper()}", "unknown"),
        }
        for key, name in STEP_KEYS
    ]
    failed = [item for item in steps if item["outcome"] != "success"]
    report = {
        "schema_version": 1,
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "workflow": os.environ.get("GITHUB_WORKFLOW"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_number": os.environ.get("GITHUB_RUN_NUMBER"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "commit_sha": os.environ.get("GITHUB_SHA"),
        "ref": os.environ.get("GITHUB_REF"),
        "event_name": os.environ.get("GITHUB_EVENT_NAME"),
        "overall": "failure" if failed else "success",
        "steps": steps,
        "failed_step_ids": [item["id"] for item in failed],
        "next_action": (
            "Inspect the named failed step logs and attached diagnostic files; do not treat the run as passed."
            if failed
            else "All required test-build-install steps passed."
        ),
    }

    json_path = output_dir / "rpr-ci-report.json"
    md_path = output_dir / "rpr-ci-report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    run_url = (
        f"https://github.com/{report['repository']}/actions/runs/{report['run_id']}"
        if report["repository"] and report["run_id"]
        else "unavailable"
    )
    lines = [
        "<!-- rpr-ci-catch-up -->",
        "## RPR CI catch-up report",
        "",
        f"- Overall: **{report['overall']}**",
        f"- Commit: `{report['commit_sha']}`",
        f"- Run: {run_url}",
        f"- Attempt: `{report['run_attempt']}`",
        "",
        "| Check | Outcome |",
        "|---|---|",
    ]
    lines.extend(f"| {item['name']} | `{item['outcome']}` |" for item in steps)
    lines.extend(
        [
            "",
            f"**Next action:** {report['next_action']}",
            "",
            "Detailed command output is retained in the workflow logs and the `rpr-ci-catch-up` artifact.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
