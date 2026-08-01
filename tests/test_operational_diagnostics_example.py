# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_operational_diagnostics_example_is_executable() -> None:
    example = Path(__file__).parents[1] / "examples" / "operational_diagnostics.py"

    completed = subprocess.run(
        [sys.executable, str(example)],
        check=True,
        capture_output=True,
        text=True,
    )
    snapshots = json.loads(completed.stdout)

    assert snapshots[0]["state"] == "awaiting_approval"
    assert snapshots[0]["next_required_authority"] == "reviewer"
    assert snapshots[0]["next_required_action"] == "approve_or_deny"
    assert snapshots[0]["evidence_valid"] is True

    assert snapshots[1]["state"] == "repair_required"
    assert snapshots[1]["next_required_authority"] == "support"
    assert snapshots[1]["next_required_action"] == "repair_failed_attempt"
    # The failed execution result is followed by the durable transition into
    # REPAIR_REQUIRED, so the transition is the latest evidence event.
    assert snapshots[1]["latest_event_type"] == "state_transition"
    assert snapshots[1]["evidence_valid"] is True
