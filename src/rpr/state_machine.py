# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from ._generated_transitions import ALLOWED_TRANSITIONS
from .models import PathwayState

_ALLOWED = ALLOWED_TRANSITIONS


class InvalidTransition(ValueError):
    pass


def ensure_transition(current: PathwayState, target: PathwayState) -> None:
    if target not in _ALLOWED[current]:
        raise InvalidTransition(f"Transition {current.value} -> {target.value} is not allowed")
