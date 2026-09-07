# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any, Mapping

from .models import PathwayState
from .routing import compatibility_route_for_state


def build_route_visibility(*, state: str, definition: Mapping[str, Any]) -> dict[str, Any]:
    """Build a read-only, non-authorizing view of current routing semantics.

    This helper does not select a receiver, grant Authority, mutate runtime state,
    or expand the MCP public contract. It only exposes already-persisted route
    metadata plus narrow compatibility classifications justified by DAN-96.
    """

    pathway_state = PathwayState(state)
    compatibility_route = compatibility_route_for_state(pathway_state)
    declared_route = definition.get("responsibility_route")
    if declared_route is not None and not isinstance(declared_route, Mapping):
        raise ValueError("responsibility_route must be an object when present")

    return {
        "state": pathway_state.value,
        "compatibility_route": None if compatibility_route is None else compatibility_route.value,
        "declared_route": None if declared_route is None else dict(declared_route),
        "human_return_point": definition.get("human_return_point"),
        "residual_owner": definition.get("residual_owner"),
        "authority_inferred": False,
    }
