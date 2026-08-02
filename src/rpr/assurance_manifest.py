# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class AssuranceManifestError(ValueError):
    """The assurance manifest is malformed or exceeds its declared boundary."""


_ALLOWED_STATUSES = {
    "not_implemented",
    "implemented_unverified",
    "passing",
    "failing",
    "deferred",
    "out_of_scope",
}
_EVIDENCE_ORDER = {f"E{level}": level for level in range(6)}
_REQUIRED_HUMAN_GATES = {
    "repository_publicization",
    "pages_publication",
    "package_release",
    "tag_or_github_release",
    "external_or_live_mcp_connection",
    "credential_use",
    "license_change",
    "claim_escalation_to_e4_or_e5",
}
_REQUIRED_NOT_PERMITTED = {
    "full formal verification",
    "legal or regulatory compliance",
    "arbitrary third-party MCP compatibility",
    "live external MCP interoperability",
    "distributed correctness",
    "production readiness",
    "signed non-repudiation",
    "release-complete declaration without authorization",
}
_REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "status",
    "evidence_level",
    "statement",
    "implementation_anchors",
    "test_anchors",
    "retained_evidence",
    "residual_owner",
    "blocked_by",
    "residual_risks",
}


def load_assurance_manifest(path: str | Path, *, root: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssuranceManifestError(f"manifest_load_failed: {type(exc).__name__}: {exc}") from exc
    validate_assurance_manifest(payload, root=manifest_path.parent.parent if root is None else root)
    return payload


def validate_assurance_manifest(payload: Any, *, root: str | Path | None = None) -> None:
    if not isinstance(payload, Mapping):
        raise AssuranceManifestError("manifest_must_be_object")
    if payload.get("schema_version") != 1:
        raise AssuranceManifestError("unsupported_schema_version")
    if payload.get("product") != "Responsibility Pathway Runtime":
        raise AssuranceManifestError("unexpected_product")
    if payload.get("canonical_source") != "YutoriKomeiji/responsibility-pathway-runtime":
        raise AssuranceManifestError("unexpected_canonical_source")
    if payload.get("release_boundary") != "public_alpha_candidate":
        raise AssuranceManifestError("release_boundary_must_be_public_alpha_candidate")

    human_gates = _string_set(payload.get("human_gate_required_for"), "human_gate_required_for")
    missing_gates = _REQUIRED_HUMAN_GATES - human_gates
    if missing_gates:
        raise AssuranceManifestError(f"missing_human_gates: {sorted(missing_gates)!r}")

    maximum = payload.get("maximum_current_evidence_level")
    if maximum not in _EVIDENCE_ORDER:
        raise AssuranceManifestError("invalid_maximum_current_evidence_level")
    if _EVIDENCE_ORDER[maximum] > _EVIDENCE_ORDER["E3"]:
        raise AssuranceManifestError("evidence_level_escalation_requires_human_gate")

    boundary = payload.get("global_claim_boundary")
    if not isinstance(boundary, Mapping):
        raise AssuranceManifestError("global_claim_boundary_must_be_object")
    permitted = boundary.get("permitted")
    if not isinstance(permitted, str) or not permitted.strip():
        raise AssuranceManifestError("global_permitted_wording_required")
    not_permitted = _string_set(payload.get("global_claim_boundary", {}).get("not_permitted"), "global_claim_boundary.not_permitted")
    missing_prohibitions = _REQUIRED_NOT_PERMITTED - not_permitted
    if missing_prohibitions:
        raise AssuranceManifestError(f"missing_claim_prohibitions: {sorted(missing_prohibitions)!r}")

    source_documents = _string_list(payload.get("source_documents"), "source_documents", allow_empty=False)
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise AssuranceManifestError("claims_must_be_non_empty_list")

    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        _validate_claim(claim, index=index, maximum=maximum, claim_ids=claim_ids)

    if root is not None:
        root_path = Path(root)
        for relative in source_documents:
            _require_relative_file(root_path, relative, "source_document")
        for claim in claims:
            for relative in claim["implementation_anchors"]:
                _require_relative_file(root_path, relative, f"implementation_anchor:{claim['claim_id']}")
            for relative in claim["test_anchors"]:
                _require_relative_file(root_path, relative, f"test_anchor:{claim['claim_id']}")


def _validate_claim(claim: Any, *, index: int, maximum: str, claim_ids: set[str]) -> None:
    if not isinstance(claim, Mapping):
        raise AssuranceManifestError(f"claim_{index}_must_be_object")
    missing = _REQUIRED_CLAIM_FIELDS - set(claim)
    if missing:
        raise AssuranceManifestError(f"claim_{index}_missing_fields: {sorted(missing)!r}")

    claim_id = claim.get("claim_id")
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise AssuranceManifestError(f"claim_{index}_invalid_id")
    if claim_id in claim_ids:
        raise AssuranceManifestError(f"duplicate_claim_id: {claim_id}")
    claim_ids.add(claim_id)

    status = claim.get("status")
    if status not in _ALLOWED_STATUSES:
        raise AssuranceManifestError(f"claim_{claim_id}_invalid_status")
    evidence_level = claim.get("evidence_level")
    if evidence_level not in _EVIDENCE_ORDER:
        raise AssuranceManifestError(f"claim_{claim_id}_invalid_evidence_level")
    if _EVIDENCE_ORDER[evidence_level] > _EVIDENCE_ORDER[maximum]:
        raise AssuranceManifestError(f"claim_{claim_id}_exceeds_manifest_maximum")
    if status == "passing" and _EVIDENCE_ORDER[evidence_level] < _EVIDENCE_ORDER["E2"]:
        raise AssuranceManifestError(f"claim_{claim_id}_passing_without_sufficient_evidence")

    statement = claim.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise AssuranceManifestError(f"claim_{claim_id}_statement_required")
    owner = claim.get("residual_owner")
    if not isinstance(owner, str) or not owner.strip():
        raise AssuranceManifestError(f"claim_{claim_id}_residual_owner_required")

    implementation = _string_list(claim.get("implementation_anchors"), f"claim_{claim_id}.implementation_anchors", allow_empty=False)
    tests = _string_list(claim.get("test_anchors"), f"claim_{claim_id}.test_anchors", allow_empty=True)
    _string_list(claim.get("retained_evidence"), f"claim_{claim_id}.retained_evidence", allow_empty=True)
    blocked_by = _string_list(claim.get("blocked_by"), f"claim_{claim_id}.blocked_by", allow_empty=True)
    risks = _string_list(claim.get("residual_risks"), f"claim_{claim_id}.residual_risks", allow_empty=False)

    if status == "passing" and not tests:
        raise AssuranceManifestError(f"claim_{claim_id}_passing_without_test_anchor")
    if status == "implemented_unverified" and not blocked_by:
        raise AssuranceManifestError(f"claim_{claim_id}_unverified_without_blocker")
    if not implementation or not risks:
        raise AssuranceManifestError(f"claim_{claim_id}_missing_assurance_boundary")


def _string_list(value: Any, field: str, *, allow_empty: bool) -> list[str]:
    if not isinstance(value, list):
        raise AssuranceManifestError(f"{field}_must_be_list")
    if not allow_empty and not value:
        raise AssuranceManifestError(f"{field}_must_not_be_empty")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise AssuranceManifestError(f"{field}_contains_invalid_string")
        result.append(item)
    if len(result) != len(set(result)):
        raise AssuranceManifestError(f"{field}_contains_duplicates")
    return result


def _string_set(value: Any, field: str) -> set[str]:
    return set(_string_list(value, field, allow_empty=False))


def _require_relative_file(root: Path, relative: str, field: str) -> None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise AssuranceManifestError(f"{field}_must_be_relative")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        raise AssuranceManifestError(f"{field}_escapes_root")
    if not resolved.is_file():
        raise AssuranceManifestError(f"{field}_missing: {relative}")
