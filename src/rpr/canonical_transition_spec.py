# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .formal_consistency import _parse_lean
from .models import PathwayState
from .state_machine import _ALLOWED


@dataclass(frozen=True)
class CanonicalSpecResult:
    matched: bool
    spec_sha256: str
    runtime_only: tuple[str, ...]
    spec_only: tuple[str, ...]
    lean_only: tuple[str, ...]
    spec_not_in_lean: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _edge(source: PathwayState, target: PathwayState) -> str:
    return f"{source.value}->{target.value}"


def verify_canonical_spec(spec_file: str | Path, lean_file: str | Path) -> CanonicalSpecResult:
    spec_path = Path(spec_file)
    raw = json.loads(spec_path.read_text(encoding="utf-8"))
    states = tuple(PathwayState(value) for value in raw["states"])
    if len(states) != len(set(states)) or set(states) != set(PathwayState):
        raise ValueError("canonical states must exactly match PathwayState")
    transitions = raw["transitions"]
    if set(transitions) != {state.value for state in PathwayState}:
        raise ValueError("canonical transition keys must exactly match states")
    spec_edges = {
        (PathwayState(source), PathwayState(target))
        for source, targets in transitions.items()
        for target in targets
    }
    runtime_edges = {(source, target) for source, targets in _ALLOWED.items() for target in targets}
    _, lean_edges = _parse_lean(Path(lean_file))
    runtime_only = tuple(sorted(_edge(*item) for item in runtime_edges - spec_edges))
    spec_only = tuple(sorted(_edge(*item) for item in spec_edges - runtime_edges))
    lean_only = tuple(sorted(_edge(*item) for item in lean_edges - spec_edges))
    spec_not_in_lean = tuple(sorted(_edge(*item) for item in spec_edges - lean_edges))
    return CanonicalSpecResult(
        matched=not (runtime_only or spec_only or lean_only or spec_not_in_lean),
        spec_sha256=hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        runtime_only=runtime_only,
        spec_only=spec_only,
        lean_only=lean_only,
        spec_not_in_lean=spec_not_in_lean,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify canonical RPR transition specification against Python and Lean.")
    parser.add_argument("spec", nargs="?", default="specs/pathway-state-machine.json")
    parser.add_argument("--lean", default="formal/rprFormal/State.lean")
    parser.add_argument("--output", default="canonical-transition-evidence.json")
    args = parser.parse_args()
    result = verify_canonical_spec(args.spec, args.lean)
    Path(args.output).write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
