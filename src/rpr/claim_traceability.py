# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_CLAIMS = {f"CLM-{index:02d}" for index in range(1, 13)}
ALLOWED_STATUSES = {
    "not_implemented",
    "implemented_unverified",
    "passing",
    "failing",
    "deferred",
    "out_of_scope",
}
ALLOWED_LEVELS = {f"E{index}" for index in range(6)}
ALLOWED_BINDINGS = {"file_bound", "specified_only"}


class ClaimTraceabilityError(ValueError):
    """Raised when the claim traceability basis is incomplete or inconsistent."""


def _non_empty_strings(value: Any, field: str, claim_id: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise ClaimTraceabilityError(f"{claim_id}: {field} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise ClaimTraceabilityError(f"{claim_id}: {field} contains duplicates")
    return value


def _load_registry(registry_path: Path, product_root: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ClaimTraceabilityError("unsupported test ID registry schema_version")
    entries = data.get("tests")
    if not isinstance(entries, list):
        raise ClaimTraceabilityError("test ID registry tests must be a list")
    registry: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ClaimTraceabilityError("test ID registry entry must be an object")
        test_id = entry.get("test_id")
        binding = entry.get("binding")
        source = entry.get("source")
        if not isinstance(test_id, str) or not test_id.strip():
            raise ClaimTraceabilityError("test ID registry entry requires test_id")
        if test_id in registry:
            raise ClaimTraceabilityError(f"duplicate test ID registry entry: {test_id}")
        if binding not in ALLOWED_BINDINGS:
            raise ClaimTraceabilityError(f"{test_id}: invalid binding {binding!r}")
        if not isinstance(source, str) or not source.strip():
            raise ClaimTraceabilityError(f"{test_id}: source is required")
        if not (product_root / source).exists():
            raise ClaimTraceabilityError(f"{test_id}: registry source does not exist: {source}")
        registry[test_id] = entry
    return registry


def validate_manifest(
    manifest_path: str | Path,
    *,
    root: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    product_root = Path(root) if root is not None else manifest_path.parent.parent
    registry_file = Path(registry_path) if registry_path is not None else product_root / "specs" / "test-id-registry.json"
    registry = _load_registry(registry_file, product_root)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ClaimTraceabilityError("unsupported claim traceability schema_version")
    claims = data.get("claims")
    if not isinstance(claims, list):
        raise ClaimTraceabilityError("claims must be a list")

    ids = [claim.get("claim_id") for claim in claims if isinstance(claim, dict)]
    if set(ids) != EXPECTED_CLAIMS or len(ids) != len(EXPECTED_CLAIMS):
        missing = sorted(EXPECTED_CLAIMS - set(ids))
        extra = sorted(set(ids) - EXPECTED_CLAIMS)
        raise ClaimTraceabilityError(f"claim set mismatch: missing={missing}, extra={extra}")

    referenced_test_ids: set[str] = set()
    for claim in claims:
        claim_id = claim["claim_id"]
        status = claim.get("status")
        level = claim.get("evidence_level")
        if status not in ALLOWED_STATUSES:
            raise ClaimTraceabilityError(f"{claim_id}: invalid status {status!r}")
        if level not in ALLOWED_LEVELS:
            raise ClaimTraceabilityError(f"{claim_id}: invalid evidence_level {level!r}")
        if level in {"E4", "E5"}:
            raise ClaimTraceabilityError(f"{claim_id}: E4/E5 requires a separately approved promotion record")
        anchors = _non_empty_strings(claim.get("implementation_anchors"), "implementation_anchors", claim_id)
        test_ids = _non_empty_strings(claim.get("test_ids"), "test_ids", claim_id)
        _non_empty_strings(claim.get("evidence_ids"), "evidence_ids", claim_id)
        if not isinstance(claim.get("residual_owner"), str) or not claim["residual_owner"].strip():
            raise ClaimTraceabilityError(f"{claim_id}: residual_owner is required")
        if not isinstance(claim.get("permitted_wording"), str) or not claim["permitted_wording"].strip():
            raise ClaimTraceabilityError(f"{claim_id}: permitted_wording is required")
        blocked_by = claim.get("blocked_by")
        if not isinstance(blocked_by, list) or not all(isinstance(item, str) and item.strip() for item in blocked_by):
            raise ClaimTraceabilityError(f"{claim_id}: blocked_by must be a string list")
        if status == "passing" and level in {"E0", "E1"}:
            raise ClaimTraceabilityError(f"{claim_id}: passing requires at least E2")
        for anchor in anchors:
            if not (product_root / anchor).exists():
                raise ClaimTraceabilityError(f"{claim_id}: implementation anchor does not exist: {anchor}")
        missing_tests = sorted(set(test_ids) - registry.keys())
        if missing_tests:
            raise ClaimTraceabilityError(f"{claim_id}: unregistered test IDs: {missing_tests}")
        bindings = {registry[test_id]["binding"] for test_id in test_ids}
        if status == "passing" and "file_bound" not in bindings:
            raise ClaimTraceabilityError(f"{claim_id}: passing claim requires at least one file-bound test ID")
        referenced_test_ids.update(test_ids)

    unused = sorted(set(registry) - referenced_test_ids)
    if unused:
        raise ClaimTraceabilityError(f"test ID registry contains unreferenced entries: {unused}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the RPR claim traceability manifest")
    parser.add_argument("manifest", nargs="?", default="specs/claim-traceability.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry", default="specs/test-id-registry.json")
    args = parser.parse_args()
    data = validate_manifest(args.manifest, root=args.root, registry_path=args.registry)
    print(json.dumps({"valid": True, "claims": len(data["claims"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
