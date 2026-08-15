# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json

from rpr.cli import main


def _pathway_payload() -> dict[str, object]:
    return {
        "pathway_id": "cli-bom-001",
        "action_name": "send_email",
        "action_class": "high_impact",
        "environment_trust": "trusted_internal",
        "decision_owner": "master",
        "approval_authority": "master",
        "execution_actor": "agent",
        "stop_authority": "operator",
        "evidence_owner": "audit",
        "repair_owner": "support",
        "resume_authority": "master",
        "human_return_point": "before_send",
        "residual_owner": "master",
    }


def test_check_accepts_plain_utf8_json(tmp_path, capsys) -> None:
    path = tmp_path / "plain.json"
    path.write_text(json.dumps(_pathway_payload()), encoding="utf-8")

    assert main(["check", str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["decision"] == "human_gate"


def test_check_accepts_utf8_bom_json(tmp_path, capsys) -> None:
    path = tmp_path / "bom.json"
    path.write_text(json.dumps(_pathway_payload()), encoding="utf-8-sig")

    assert main(["check", str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["decision"] == "human_gate"
