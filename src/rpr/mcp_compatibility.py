# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class McpCompatibilityError(ValueError):
    """Raised when the MCP compatibility contract is unsafe or inconsistent."""


def _require_unique_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise McpCompatibilityError(f"{field} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise McpCompatibilityError(f"{field} contains duplicates")
    return value


def validate_mcp_compatibility(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise McpCompatibilityError("unsupported schema_version")

    versions = data.get("versions")
    if not isinstance(versions, list) or not versions:
        raise McpCompatibilityError("versions must be a non-empty list")
    ids = [entry.get("protocol_version") for entry in versions if isinstance(entry, dict)]
    if len(ids) != len(set(ids)):
        raise McpCompatibilityError("protocol versions contain duplicates")

    default = data.get("default_protocol_version")
    by_id = {entry.get("protocol_version"): entry for entry in versions if isinstance(entry, dict)}
    if default not in by_id:
        raise McpCompatibilityError("default protocol version is not registered")
    default_entry = by_id[default]
    if default_entry.get("lifecycle") != "stable" or default_entry.get("enabled_by_default") is not True:
        raise McpCompatibilityError("default protocol version must be stable and enabled")
    if default_entry.get("requires_experimental_flag") is not False:
        raise McpCompatibilityError("stable default cannot require an experimental flag")

    allowed_lifecycles = {"stable", "release_candidate", "draft", "deprecated"}
    for protocol_version, entry in by_id.items():
        if entry.get("lifecycle") not in allowed_lifecycles:
            raise McpCompatibilityError(f"{protocol_version}: invalid lifecycle")
        _require_unique_strings(entry.get("accepted_discovery_modes"), f"{protocol_version}.accepted_discovery_modes")
        if not isinstance(entry.get("session_model"), str) or not entry["session_model"].strip():
            raise McpCompatibilityError(f"{protocol_version}: session_model is required")
        if entry.get("lifecycle") in {"release_candidate", "draft"}:
            if entry.get("enabled_by_default") is not False or entry.get("requires_experimental_flag") is not True:
                raise McpCompatibilityError(f"{protocol_version}: non-stable versions must be experimental and disabled by default")

    required_bindings = {"protocol_version", "server_identity", "server_capabilities_hash", "tool_name", "tool_schema_hash"}
    if set(_require_unique_strings(data.get("admission_bindings"), "admission_bindings")) != required_bindings:
        raise McpCompatibilityError("admission_bindings must match the required MCP admission identity")

    retry = data.get("retry_contract")
    if not isinstance(retry, dict):
        raise McpCompatibilityError("retry_contract is required")
    if retry.get("transport_retry_reuses_business_identity") is not True:
        raise McpCompatibilityError("transport retry must preserve business identity")
    if retry.get("business_retry_requires_new_attempt_identity") is not True:
        raise McpCompatibilityError("business retry must require a new attempt identity")
    required_identity = {"operation_id", "attempt_id", "idempotency_key", "request_fingerprint"}
    if set(_require_unique_strings(retry.get("required_business_identity_fields"), "required_business_identity_fields")) != required_identity:
        raise McpCompatibilityError("business identity fields are incomplete")

    mrtr = data.get("mrtr_contract")
    if not isinstance(mrtr, dict):
        raise McpCompatibilityError("mrtr_contract is required")
    if mrtr.get("input_required_is_human_gate") is not False or mrtr.get("requires_explicit_mapping") is not True:
        raise McpCompatibilityError("MRTR input_required must not be equated automatically with Human Gate")
    _require_unique_strings(mrtr.get("allowed_mappings"), "allowed_mappings")

    if data.get("unknown_version_policy") != "reject":
        raise McpCompatibilityError("unknown MCP versions must fail closed")
    if data.get("release_boundary") != "public_alpha_candidate":
        raise McpCompatibilityError("release boundary must remain a public-alpha candidate")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the RPR MCP compatibility contract")
    parser.add_argument("contract", nargs="?", default="specs/mcp-compatibility.json")
    args = parser.parse_args()
    data = validate_mcp_compatibility(args.contract)
    print(json.dumps({"valid": True, "versions": len(data["versions"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
