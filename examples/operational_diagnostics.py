# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.diagnostics import diagnose_pathway
from rpr.executor import ExecutionRequest, ExecutionResult, ExecutionStatus
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.storage import SQLiteStore


class DemonstrationFailureExecutor:
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            ExecutionStatus.FAILED,
            evidence={"attempt_id": request.attempt_id, "diagnostic": "precondition_failed"},
            reason="target version changed before dispatch",
        )


def run_example(workdir: Path) -> list[dict[str, object]]:
    pathway_id = "example-operational-diagnostic"
    runtime = ResponsibilityPathwayRuntime(
        store=SQLiteStore(workdir / "pathways.sqlite3"),
        attempt_ledger=SQLiteExecutionAttemptLedger(workdir / "attempts.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
    )
    runtime.register(
        PathwayDefinition(
            pathway_id=pathway_id,
            action_name="external_mutation",
            action_class=ActionClass.REVERSIBLE_EXTERNAL,
            environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
            decision_owner="owner",
            approval_authority="reviewer",
            execution_actor="agent",
            stop_authority="operator",
            evidence_owner="audit",
            repair_owner="support",
            resume_authority="manager",
            human_return_point="before_retry",
            residual_owner="owner",
        ),
        idempotency_key="register-operational-diagnostic-example",
    )

    snapshots = [diagnose_pathway(runtime, pathway_id).to_dict()]

    runtime.transition(pathway_id, PathwayState.APPROVED, actor="reviewer", reason="approved for example")
    runtime.execute(
        pathway_id,
        ExecutionRequest(
            "op-example",
            "attempt-example",
            "idem-example",
            "external_mutation",
            {"target": "example-resource"},
        ),
        actor="agent",
        executor=DemonstrationFailureExecutor(),
    )
    snapshots.append(diagnose_pathway(runtime, pathway_id).to_dict())
    return snapshots


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rpr-diagnostic-") as directory:
        print(json.dumps(run_example(Path(directory)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
