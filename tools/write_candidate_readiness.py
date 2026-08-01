# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rpr.candidate_readiness import CandidateReadinessReport


_INTERNAL_NAMES = (
    "pytest",
    "json_python_lean_parity",
    "lean_build",
    "wheel_install",
    "sdist_install",
    "release_audit",
    "rc_rehearsal",
    "clean_export",
)


def _outcome(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"success", "failure", "cancelled", "skipped"}:
        raise ValueError(f"unsupported CI outcome: {value}")
    return normalized == "success"


def _evidence(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def build_document(
    *,
    source_commit: str,
    outcomes: dict[str, str],
    evidence_root: Path,
    residual_owner: str,
) -> dict[str, object]:
    missing = sorted(set(_INTERNAL_NAMES) - set(outcomes))
    unknown = sorted(set(outcomes) - set(_INTERNAL_NAMES))
    if missing:
        raise ValueError(f"missing CI outcomes: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"unknown CI outcomes: {', '.join(unknown)}")

    evidence = _evidence(evidence_root)
    if not evidence:
        raise ValueError("candidate readiness requires retained evidence files")

    report = CandidateReadinessReport(
        source_commit=source_commit,
        internal_checks={name: _outcome(outcomes[name]) for name in _INTERNAL_NAMES},
        external_gates={
            "secret_scan": False,
            "vulnerability_review": False,
            "human_gate": False,
        },
        evidence_sha256=evidence,
        residual_owner=residual_owner,
    )
    document = report.to_dict()
    document["report_sha256"] = report.digest()
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the retained RPR candidate-readiness report.")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--residual-owner", required=True)
    for name in _INTERNAL_NAMES:
        parser.add_argument(f"--{name.replace('_', '-')}", required=True)
    args = parser.parse_args()

    outcomes = {
        name: getattr(args, name)
        for name in _INTERNAL_NAMES
    }
    document = build_document(
        source_commit=args.source_commit,
        outcomes=outcomes,
        evidence_root=args.evidence_root,
        residual_owner=args.residual_owner,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
