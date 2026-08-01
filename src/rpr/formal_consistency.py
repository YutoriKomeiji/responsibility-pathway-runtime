# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .models import PathwayState
from .state_machine import _ALLOWED

_LEAN_TO_PYTHON = {
    "proposed": PathwayState.PROPOSED,
    "awaitingApproval": PathwayState.AWAITING_APPROVAL,
    "approved": PathwayState.APPROVED,
    "running": PathwayState.RUNNING,
    "held": PathwayState.HELD,
    "humanGate": PathwayState.HUMAN_GATE,
    "stopped": PathwayState.STOPPED,
    "partiallyCompleted": PathwayState.PARTIALLY_COMPLETED,
    "writeStatusUnknown": PathwayState.WRITE_STATUS_UNKNOWN,
    "repairRequired": PathwayState.REPAIR_REQUIRED,
    "readyToResume": PathwayState.READY_TO_RESUME,
    "completed": PathwayState.COMPLETED,
    "denied": PathwayState.DENIED,
    "aborted": PathwayState.ABORTED,
}
_STATE_PATTERN = re.compile(r"^\s*\|\s+([A-Za-z][A-Za-z0-9]*)\s*$")
_EDGE_PATTERN = re.compile(
    r"^\s*\|\s+([A-Za-z][A-Za-z0-9]*),\s*([A-Za-z][A-Za-z0-9]*)\s*=>\s*true\s*$"
)


@dataclass(frozen=True)
class FormalConsistencyResult:
    matched: bool
    python_only: tuple[str, ...]
    lean_only: tuple[str, ...]
    python_states_only: tuple[str, ...]
    lean_states_only: tuple[str, ...]
    lean_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "matched": self.matched,
            "python_only": list(self.python_only),
            "lean_only": list(self.lean_only),
            "python_states_only": list(self.python_states_only),
            "lean_states_only": list(self.lean_states_only),
            "lean_sha256": self.lean_sha256,
        }


def _edge_name(source: PathwayState, target: PathwayState) -> str:
    return f"{source.value}->{target.value}"


def _parse_lean(path: Path) -> tuple[set[PathwayState], set[tuple[PathwayState, PathwayState]]]:
    text = path.read_text(encoding="utf-8")
    states: set[PathwayState] = set()
    edges: set[tuple[PathwayState, PathwayState]] = set()
    in_state_declaration = False
    for line in text.splitlines():
        if line.startswith("inductive PathwayState where"):
            in_state_declaration = True
            continue
        if in_state_declaration and "deriving" in line:
            in_state_declaration = False
            continue
        if in_state_declaration:
            match = _STATE_PATTERN.match(line)
            if match:
                name = match.group(1)
                if name not in _LEAN_TO_PYTHON:
                    raise ValueError(f"unknown Lean pathway state: {name}")
                states.add(_LEAN_TO_PYTHON[name])
        edge = _EDGE_PATTERN.match(line)
        if edge:
            source_name, target_name = edge.groups()
            try:
                source = _LEAN_TO_PYTHON[source_name]
                target = _LEAN_TO_PYTHON[target_name]
            except KeyError as exc:
                raise ValueError(f"unknown Lean pathway state in transition: {exc.args[0]}") from exc
            edges.add((source, target))
    return states, edges


def check_formal_consistency(lean_state_file: str | Path) -> FormalConsistencyResult:
    path = Path(lean_state_file)
    lean_states, lean_edges = _parse_lean(path)
    python_states = set(PathwayState)
    python_edges = {(source, target) for source, targets in _ALLOWED.items() for target in targets}
    python_only = tuple(sorted(_edge_name(*edge) for edge in python_edges - lean_edges))
    lean_only = tuple(sorted(_edge_name(*edge) for edge in lean_edges - python_edges))
    python_states_only = tuple(sorted(state.value for state in python_states - lean_states))
    lean_states_only = tuple(sorted(state.value for state in lean_states - python_states))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return FormalConsistencyResult(
        matched=not (python_only or lean_only or python_states_only or lean_states_only),
        python_only=python_only,
        lean_only=lean_only,
        python_states_only=python_states_only,
        lean_states_only=lean_states_only,
        lean_sha256=digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare the Python and Lean RPR transition models.")
    parser.add_argument("lean_state_file", nargs="?", default="formal/rprFormal/State.lean")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = check_formal_consistency(args.lean_state_file)
    payload = json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
