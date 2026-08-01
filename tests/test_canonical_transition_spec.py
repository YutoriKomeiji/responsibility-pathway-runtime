# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import json
from pathlib import Path

import pytest

from rpr.canonical_transition_spec import verify_canonical_spec


def _paths() -> tuple[Path, Path]:
    root = Path(__file__).parents[1]
    return root / "specs" / "pathway-state-machine.json", root / "formal" / "rprFormal" / "State.lean"


def test_canonical_spec_matches_python_and_lean() -> None:
    spec, lean = _paths()
    result = verify_canonical_spec(spec, lean)
    assert result.matched, result.to_dict()
    assert len(result.spec_sha256) == 64


def test_canonical_spec_detects_removed_transition(tmp_path: Path) -> None:
    spec, lean = _paths()
    value = json.loads(spec.read_text(encoding="utf-8"))
    value["transitions"]["running"].remove("completed")
    changed = tmp_path / "pathway-state-machine.json"
    changed.write_text(json.dumps(value), encoding="utf-8")
    result = verify_canonical_spec(changed, lean)
    assert not result.matched
    assert "running->completed" in result.runtime_only
    assert "running->completed" in result.lean_only


def test_canonical_spec_rejects_unknown_state(tmp_path: Path) -> None:
    spec, lean = _paths()
    value = json.loads(spec.read_text(encoding="utf-8"))
    value["states"].append("invented")
    changed = tmp_path / "pathway-state-machine.json"
    changed.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_canonical_spec(changed, lean)
