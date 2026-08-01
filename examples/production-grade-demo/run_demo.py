# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Language: English comments; CLI summaries support English/Japanese labels."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from payment_service import PaymentServer, PaymentState
from rpr import (
    ActionClass,
    EnvironmentTrust,
    ExecutionRequest,
    HttpMutationExecutor,
    PathwayDefinition,
    PathwayState,
    ReadbackEvidence,
    ReconciliationResult,
    ReconciliationStatus,
    ResponsibilityPathwayRuntime,
    SQLiteExecutionAttemptLedger,
    SQLiteStore,
)
from rpr.rpe import AllowAllDevelopmentEvaluator


class IndependentPaymentReadback:
    """Verify the mutation by querying the payment-status endpoint."""

    def __init__(self, status_base_url: str):
        self.status_base_url = status_base_url.rstrip("/")

    def verify(self, *, request, status_code, headers, body):
        del status_code, headers, body
        payment_id = str(request.parameters["expected_payment_id"])
        try:
            with urlopen(f"{self.status_base_url}/{payment_id}", timeout=2) as response:
                observed = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return ReadbackEvidence(False, {"payment_id": payment_id}, f"independent_readback_unavailable:{type(exc).__name__}")
        verified = observed.get("payment_id") == payment_id and observed.get("status") == "accepted"
        return ReadbackEvidence(verified, observed, None if verified else "payment_state_not_verified")


class PaymentReconciliation:
    def __init__(self, status_base_url: str):
        self.status_base_url = status_base_url.rstrip("/")

    def reconcile(self, request, attempt):
        del attempt
        payment_id = str(request.parameters["expected_payment_id"])
        try:
            with urlopen(f"{self.status_base_url}/{payment_id}", timeout=2) as response:
                observed = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return ReconciliationResult(ReconciliationStatus.UNRESOLVED, {"payment_id": payment_id}, f"readback_unavailable:{type(exc).__name__}")
        if observed.get("payment_id") == payment_id and observed.get("status") == "accepted":
            return ReconciliationResult(ReconciliationStatus.VERIFIED_APPLIED, observed, "independent_payment_status_confirmed")
        return ReconciliationResult(ReconciliationStatus.VERIFIED_NOT_APPLIED, observed, "payment_not_applied")


def definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="http_json_mutation",
        action_class=ActionClass.HIGH_IMPACT,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="finance-owner",
        approval_authority="finance-approver",
        execution_actor="payment-agent",
        stop_authority="operations",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="finance-manager",
        human_return_point="before-payment-dispatch",
        residual_owner="finance-owner",
    )


def make_runtime(state_dir: Path) -> ResponsibilityPathwayRuntime:
    return ResponsibilityPathwayRuntime(
        store=SQLiteStore(state_dir / "pathways.sqlite3"),
        rpe=AllowAllDevelopmentEvaluator(),
        attempt_ledger=SQLiteExecutionAttemptLedger(state_dir / "attempts.sqlite3"),
    )


def run(scenario: str, state_dir: Path) -> dict:
    payment_state = PaymentState(
        timeout_after_acceptance=scenario == "timeout-after-acceptance",
        readback_available=scenario != "readback-unavailable",
    )
    pathway_id = f"payment-{scenario}"
    runtime = make_runtime(state_dir)
    registered = runtime.register(definition(pathway_id), idempotency_key=f"register-{scenario}")

    if scenario == "human-rejection":
        runtime.transition(pathway_id, PathwayState.DENIED, actor="finance-approver", reason="payment rejected")
        return {
            "scenario": scenario,
            "registered_state": registered.state.value,
            "final_state": runtime.store.get_state(pathway_id).value,
            "dispatch_count": 0,
            "evidence_valid": runtime.verify_evidence(pathway_id).valid,
        }

    runtime.transition(pathway_id, PathwayState.APPROVED, actor="finance-approver", reason="invoice approved")
    with PaymentServer(payment_state) as service:
        request = ExecutionRequest(
            operation_id=f"op-{scenario}",
            attempt_id=f"attempt-{scenario}",
            idempotency_key=f"idem-{scenario}",
            action="http_json_mutation",
            parameters={
                "url": service.origin + "/payments",
                "json": {"payment_id": "pay-2026-0001", "amount": 125000, "currency": "JPY"},
                "expected_payment_id": "pay-2026-0001",
            },
        )
        executor = HttpMutationExecutor(
            allowed_origins={service.origin},
            readback=IndependentPaymentReadback(service.origin + "/status"),
            allow_insecure_http=True,
        )
        result = runtime.execute(pathway_id, request, actor="payment-agent", executor=executor)

        restarted = make_runtime(state_dir)
        replay = restarted.execute(pathway_id, request, actor="payment-agent", executor=executor)
        reconciliation = None
        if result.status.value == "write_status_unknown":
            reconciled = restarted.reconcile(
                pathway_id,
                request,
                actor="support",
                strategy=PaymentReconciliation(service.origin + "/status"),
            )
            reconciliation = reconciled.status.value

    return {
        "scenario": scenario,
        "registered_state": registered.state.value,
        "result_status": result.status.value,
        "replay_status": replay.status.value,
        "reconciliation_status": reconciliation,
        "final_state": restarted.store.get_state(pathway_id).value,
        "dispatch_count": payment_state.dispatch_count,
        "evidence_valid": restarted.verify_evidence(pathway_id).valid,
        "reason": result.reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=("authorized-completion", "timeout-after-acceptance", "readback-unavailable", "human-rejection"))
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--language", choices=("en", "ja"), default="en")
    args = parser.parse_args()
    if args.state_dir:
        args.state_dir.mkdir(parents=True, exist_ok=True)
        output = run(args.scenario, args.state_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="rpr-demo-") as temp:
            output = run(args.scenario, Path(temp))
    label = "Result" if args.language == "en" else "結果"
    print(f"{label}: {json.dumps(output, ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
