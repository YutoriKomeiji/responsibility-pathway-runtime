# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
# Generated from specs/pathway-state-machine.json. Do not edit manually.
from __future__ import annotations

from .models import PathwayState

ALLOWED_TRANSITIONS: dict[PathwayState, frozenset[PathwayState]] = {
    PathwayState.PROPOSED: frozenset({PathwayState.AWAITING_APPROVAL, PathwayState.APPROVED, PathwayState.DENIED}),
    PathwayState.AWAITING_APPROVAL: frozenset({PathwayState.APPROVED, PathwayState.DENIED, PathwayState.HUMAN_GATE}),
    PathwayState.APPROVED: frozenset({PathwayState.RUNNING, PathwayState.HELD, PathwayState.ABORTED}),
    PathwayState.RUNNING: frozenset({PathwayState.COMPLETED, PathwayState.STOPPED, PathwayState.PARTIALLY_COMPLETED, PathwayState.WRITE_STATUS_UNKNOWN, PathwayState.REPAIR_REQUIRED}),
    PathwayState.HELD: frozenset({PathwayState.HUMAN_GATE, PathwayState.APPROVED, PathwayState.ABORTED}),
    PathwayState.HUMAN_GATE: frozenset({PathwayState.APPROVED, PathwayState.DENIED, PathwayState.ABORTED}),
    PathwayState.STOPPED: frozenset({PathwayState.REPAIR_REQUIRED, PathwayState.ABORTED}),
    PathwayState.PARTIALLY_COMPLETED: frozenset({PathwayState.REPAIR_REQUIRED}),
    PathwayState.WRITE_STATUS_UNKNOWN: frozenset({PathwayState.COMPLETED, PathwayState.REPAIR_REQUIRED}),
    PathwayState.REPAIR_REQUIRED: frozenset({PathwayState.READY_TO_RESUME, PathwayState.ABORTED}),
    PathwayState.READY_TO_RESUME: frozenset({PathwayState.RUNNING, PathwayState.ABORTED}),
    PathwayState.COMPLETED: frozenset(),
    PathwayState.DENIED: frozenset(),
    PathwayState.ABORTED: frozenset(),
}

TERMINAL_STATES = frozenset({PathwayState.COMPLETED, PathwayState.DENIED, PathwayState.ABORTED})
