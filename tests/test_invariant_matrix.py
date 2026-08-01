# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
import pytest

from rpr.models import PathwayState
from rpr.state_machine import InvalidTransition, _ALLOWED, ensure_transition


TERMINAL = {PathwayState.COMPLETED, PathwayState.DENIED, PathwayState.ABORTED}


def test_all_state_pairs_match_declared_transition_relation() -> None:
    for current in PathwayState:
        for target in PathwayState:
            if target in _ALLOWED[current]:
                ensure_transition(current, target)
            else:
                with pytest.raises(InvalidTransition):
                    ensure_transition(current, target)


def test_terminal_states_have_no_outgoing_transition() -> None:
    for state in TERMINAL:
        assert _ALLOWED[state] == set()


def test_unknown_write_has_only_repair_or_reconciliation_completion_edges() -> None:
    forbidden = {
        PathwayState.APPROVED,
        PathwayState.RUNNING,
        PathwayState.READY_TO_RESUME,
    }
    assert forbidden.isdisjoint(_ALLOWED[PathwayState.WRITE_STATUS_UNKNOWN])
    assert _ALLOWED[PathwayState.WRITE_STATUS_UNKNOWN] == {
        PathwayState.REPAIR_REQUIRED,
        PathwayState.COMPLETED,
    }


def test_human_gate_never_transitions_directly_to_execution_or_completion() -> None:
    assert PathwayState.RUNNING not in _ALLOWED[PathwayState.HUMAN_GATE]
    assert PathwayState.COMPLETED not in _ALLOWED[PathwayState.HUMAN_GATE]


def test_repair_and_resume_are_separate_authority_steps() -> None:
    assert PathwayState.RUNNING not in _ALLOWED[PathwayState.REPAIR_REQUIRED]
    assert PathwayState.READY_TO_RESUME in _ALLOWED[PathwayState.REPAIR_REQUIRED]
    assert PathwayState.RUNNING in _ALLOWED[PathwayState.READY_TO_RESUME]


def test_completion_predecessors_are_running_or_reconciled_unknown() -> None:
    predecessors = {state for state, targets in _ALLOWED.items() if PathwayState.COMPLETED in targets}
    assert predecessors == {PathwayState.RUNNING, PathwayState.WRITE_STATUS_UNKNOWN}
