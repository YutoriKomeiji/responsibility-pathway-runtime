# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class IntegrationInventoryError(RuntimeError):
    """Raised when the integration acceptance inventory is incomplete."""


def load_inventory(path: str | Path, *, repository_root: str | Path) -> dict[str, Any]:
    inventory_path = Path(path)
    root = Path(repository_root).resolve()
    document = json.loads(inventory_path.read_text(encoding="utf-8"))

    execution_classes = set(document.get("execution_classes", ()))
    statuses = set(document.get("statuses", ()))
    scenarios = document.get("scenarios")
    if not execution_classes or not statuses or not isinstance(scenarios, list) or not scenarios:
        raise IntegrationInventoryError("inventory registries and scenarios are required")

    seen: set[str] = set()
    for scenario in scenarios:
        scenario_id = str(scenario.get("id", "")).strip()
        if not scenario_id or scenario_id in seen:
            raise IntegrationInventoryError(f"missing or duplicate scenario id: {scenario_id!r}")
        seen.add(scenario_id)

        execution_class = scenario.get("execution_class")
        status = scenario.get("status")
        evidence = scenario.get("evidence")
        residual_risk = str(scenario.get("residual_risk", "")).strip()
        next_phase = str(scenario.get("next_phase", "")).strip()
        if execution_class not in execution_classes:
            raise IntegrationInventoryError(f"{scenario_id} has unknown execution class")
        if status not in statuses:
            raise IntegrationInventoryError(f"{scenario_id} has unknown status")
        if not isinstance(evidence, list):
            raise IntegrationInventoryError(f"{scenario_id} evidence must be a list")
        if not residual_risk or not next_phase:
            raise IntegrationInventoryError(f"{scenario_id} requires residual risk and next phase")
        if status in {"verified", "partial"} and not evidence:
            raise IntegrationInventoryError(f"{scenario_id} requires retained evidence")
        missing = [reference for reference in evidence if not (root / reference).is_file()]
        if missing:
            raise IntegrationInventoryError(
                f"{scenario_id} evidence does not exist: {', '.join(sorted(missing))}"
            )
        if execution_class == "external_environment_only" and status != "blocked":
            raise IntegrationInventoryError(
                f"{scenario_id} external-only scenario must remain blocked before Human Gate"
            )

    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    document["inventory_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    document["summary"] = {
        value: sum(1 for scenario in scenarios if scenario["status"] == value)
        for value in sorted(statuses)
    }
    document["candidate_freeze_allowed"] = not any(
        scenario["execution_class"] == "executable" and scenario["status"] != "verified"
        for scenario in scenarios
    )
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the RPR integration acceptance inventory")
    parser.add_argument("inventory")
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = load_inventory(args.inventory, repository_root=args.repository_root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
