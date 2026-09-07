# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from .models import PathwayState, ResponsibilityRouteClass


def compatibility_route_for_state(state: PathwayState) -> ResponsibilityRouteClass | None:
    """Return only route classifications already justified by current runtime semantics.

    This helper is intentionally narrow. It does not select a new receiver, grant
    Authority, or change runtime state. It only makes two existing compatibility
    relationships explicit for the DAN-96 migration:

    * WRITE_STATUS_UNKNOWN -> HOLD_FOR_RECONCILIATION
    * HUMAN_GATE -> BOUNDED_HUMAN_RETURN

    All other states remain unclassified until their routing semantics are
    explicitly designed and reviewed.
    """

    if state is PathwayState.WRITE_STATUS_UNKNOWN:
        return ResponsibilityRouteClass.HOLD_FOR_RECONCILIATION
    if state is PathwayState.HUMAN_GATE:
        return ResponsibilityRouteClass.BOUNDED_HUMAN_RETURN
    return None
