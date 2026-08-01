# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rpr.mcp_compatibility import McpCompatibilityError, validate_mcp_compatibility


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "specs" / "mcp-compatibility.json"


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "mcp-compatibility.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _canonical() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_canonical_mcp_compatibility_contract_is_valid() -> None:
    data = validate_mcp_compatibility(CONTRACT)
    assert data["default_protocol_version"] == "2025-11-25"


def test_release_candidate_cannot_be_enabled_by_default(tmp_path: Path) -> None:
    data = copy.deepcopy(_canonical())
    rc = next(item for item in data["versions"] if item["protocol_version"] == "2026-07-28")
    rc["enabled_by_default"] = True
    with pytest.raises(McpCompatibilityError, match="non-stable versions"):
        validate_mcp_compatibility(_write(tmp_path, data))


def test_release_candidate_requires_experimental_flag(tmp_path: Path) -> None:
    data = copy.deepcopy(_canonical())
    rc = next(item for item in data["versions"] if item["protocol_version"] == "2026-07-28")
    rc["requires_experimental_flag"] = False
    with pytest.raises(McpCompatibilityError, match="non-stable versions"):
        validate_mcp_compatibility(_write(tmp_path, data))


def test_transport_retry_must_preserve_business_identity(tmp_path: Path) -> None:
    data = copy.deepcopy(_canonical())
    data["retry_contract"]["transport_retry_reuses_business_identity"] = False
    with pytest.raises(McpCompatibilityError, match="transport retry"):
        validate_mcp_compatibility(_write(tmp_path, data))


def test_mrtr_input_required_is_not_implicit_human_gate(tmp_path: Path) -> None:
    data = copy.deepcopy(_canonical())
    data["mrtr_contract"]["input_required_is_human_gate"] = True
    with pytest.raises(McpCompatibilityError, match="must not be equated"):
        validate_mcp_compatibility(_write(tmp_path, data))


def test_unknown_versions_fail_closed(tmp_path: Path) -> None:
    data = copy.deepcopy(_canonical())
    data["unknown_version_policy"] = "allow_latest"
    with pytest.raises(McpCompatibilityError, match="fail closed"):
        validate_mcp_compatibility(_write(tmp_path, data))
