# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from urllib import error

from rpr.models import (
    ActionClass,
    EnvironmentTrust,
    PathwayDefinition,
    PathwayState,
    ReceiverEligibility,
    ResponsibilityRoute,
    ResponsibilityRouteClass,
    RuntimeDecision,
)
from rpr.rpe import AllowAllDevelopmentEvaluator, PythonRpeEvaluator, RestRpeEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime


def definition(pathway_id: str, *, high_impact: bool = False, route=None) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="external_action",
        action_class=ActionClass.HIGH_IMPACT if high_impact else ActionClass.REVERSIBLE_EXTERNAL,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority="approver",
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_external_action",
        residual_owner="owner",
        responsibility_route=route,
    )


def route(*, eligibility: ReceiverEligibility) -> ResponsibilityRoute:
    return ResponsibilityRoute(
        route_class=ResponsibilityRouteClass.AI_RESOLVE_WITHIN_DELEGATION,
        source_holder="agent-a",
        destination="agent-b",
        receiver_eligibility=eligibility,
        authority_class="delegated_runtime",
        delegation_scope="readback-only",
        unresolved_payload=("effect_state",),
        allowed_next_actions=("readback",),
        closure_condition="effect state verified",
        reevaluation_condition="authority or environment changes",
        residual_owner="owner",
    )


def test_generic_rpe_unavailability_holds_without_assuming_human_receiver():
    result = ResponsibilityPathwayRuntime().register(
        definition("p-unavailable"),
        idempotency_key="register-unavailable",
    )
    assert result.decision is RuntimeDecision.HOLD
    assert result.state is PathwayState.HELD
    assert "rpe_unavailable" in result.reason_codes


def test_explicit_high_impact_human_gate_still_wins_over_rpe_hold():
    result = ResponsibilityPathwayRuntime().register(
        definition("p-high-impact", high_impact=True),
        idempotency_key="register-high-impact",
    )
    assert result.decision is RuntimeDecision.HUMAN_GATE
    assert result.state is PathwayState.HUMAN_GATE
    assert "rpe_unavailable" in result.reason_codes


def test_python_rpe_adapter_exception_holds():
    def broken_evaluator(action_request, packs):
        del action_request, packs
        raise RuntimeError("offline")

    evaluator = PythonRpeEvaluator(broken_evaluator, ())
    result = evaluator.evaluate({"action": "test"})
    assert result.decision is RuntimeDecision.HOLD
    assert result.reason_codes == ("rpe_python_error", "RuntimeError")


def test_rest_rpe_unavailability_holds(monkeypatch):
    def unavailable(*args, **kwargs):
        del args, kwargs
        raise error.URLError("offline")

    monkeypatch.setattr("rpr.rpe.request.urlopen", unavailable)
    evaluator = RestRpeEvaluator("http://127.0.0.1:9/evaluate")
    result = evaluator.evaluate({"action": "test"})
    assert result.decision is RuntimeDecision.HOLD
    assert result.reason_codes[0] == "rpe_rest_unavailable"


def test_rpe_contract_mismatch_holds_at_runtime_boundary():
    def old_contract(action_request, packs):
        del action_request, packs
        return {
            "decision": "allow",
            "reason_codes": ["old_contract"],
            "contract_version": "old",
        }

    runtime = ResponsibilityPathwayRuntime(
        rpe=PythonRpeEvaluator(old_contract, (), expected_contract_version="current")
    )
    result = runtime.register(
        definition("p-contract-mismatch"),
        idempotency_key="register-contract-mismatch",
    )
    assert result.decision is RuntimeDecision.HOLD
    assert result.state is PathwayState.HELD
    assert "rpe_contract_error" in result.reason_codes


def test_ineligible_non_human_route_holds_instead_of_false_human_escalation():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    result = runtime.register(
        definition("p-ineligible", route=route(eligibility=ReceiverEligibility.INELIGIBLE)),
        idempotency_key="register-ineligible",
    )
    assert result.decision is RuntimeDecision.HOLD
    assert result.state is PathwayState.HELD
    assert "route_receiver_ineligible" in result.reason_codes


def test_route_requiring_reevaluation_holds_until_rechecked():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    result = runtime.register(
        definition(
            "p-reevaluate",
            route=route(eligibility=ReceiverEligibility.REQUIRES_REEVALUATION),
        ),
        idempotency_key="register-reevaluate",
    )
    assert result.decision is RuntimeDecision.HOLD
    assert result.state is PathwayState.HELD
    assert "route_receiver_requires_reevaluation" in result.reason_codes
