# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Language: English comments; assertions are language-neutral."""
from __future__ import annotations

import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO_DIR))

from run_demo import run  # noqa: E402


def test_authorized_completion_uses_one_dispatch(tmp_path):
    result = run("authorized-completion", tmp_path)
    assert result["result_status"] == "succeeded"
    assert result["final_state"] == "completed"
    assert result["dispatch_count"] == 1
    assert result["evidence_valid"] is True


def test_timeout_after_acceptance_restarts_without_duplicate_and_reconciles(tmp_path):
    result = run("timeout-after-acceptance", tmp_path)
    assert result["result_status"] == "write_status_unknown"
    assert result["replay_status"] == "write_status_unknown"
    assert result["reconciliation_status"] == "succeeded"
    assert result["final_state"] == "completed"
    assert result["dispatch_count"] == 1
    assert result["evidence_valid"] is True


def test_readback_unavailable_does_not_complete(tmp_path):
    result = run("readback-unavailable", tmp_path)
    assert result["result_status"] == "write_status_unknown"
    assert result["replay_status"] == "write_status_unknown"
    assert result["reconciliation_status"] == "write_status_unknown"
    assert result["final_state"] == "write_status_unknown"
    assert result["dispatch_count"] == 1


def test_human_rejection_has_zero_external_effects(tmp_path):
    result = run("human-rejection", tmp_path)
    assert result["final_state"] == "denied"
    assert result["dispatch_count"] == 0
    assert result["evidence_valid"] is True
