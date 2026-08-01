# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from pathlib import Path

from rpr.formal_consistency import check_formal_consistency


def test_python_and_lean_transition_models_match() -> None:
    lean_state = Path(__file__).parents[1] / "formal" / "rprFormal" / "State.lean"
    result = check_formal_consistency(lean_state)
    assert result.matched, result.to_dict()
    assert not result.python_only
    assert not result.lean_only
    assert not result.python_states_only
    assert not result.lean_states_only
    assert len(result.lean_sha256) == 64


def test_consistency_checker_detects_missing_edge(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "formal" / "rprFormal" / "State.lean"
    modified = tmp_path / "State.lean"
    modified.write_text(
        source.read_text(encoding="utf-8").replace("  | running, completed => true\n", ""),
        encoding="utf-8",
    )
    result = check_formal_consistency(modified)
    assert not result.matched
    assert "running->completed" in result.python_only
