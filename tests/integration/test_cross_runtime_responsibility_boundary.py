# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import json

import pytest

from rpr import (
    ActionClass,
    AgentToolCall,
    EnvironmentTrust,
    ExecutionResult,
    ExecutionStatus,
    PathwayDefinition,
    PathwayState,
    ResponsibilityPathwayRuntime,
    RprToolBoundary,
    langgraph_tool_node,
    openai_function_tool_handler,
)
from rpr.rpe import AllowAllDevelopmentEvaluator


class UnknownAfterDispatchExecutor:
    """Model the dangerous window: dispatch may have happened, response was lost."""

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        return ExecutionResult(
            ExecutionStatus.WRITE_STATUS_UNKNOWN,
            {"operation_id": request.operation_id},
            reason="connection_lost_after_dispatch",
        )


def definition(pathway_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="external_write",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="repair",
        resume_authority="manager",
        human_return_point="before_external_write",
        residual_owner="owner",
    )


def make_boundary(pathway_id: str):
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    runtime.register(definition(pathway_id), idempotency_key=f"register-{pathway_id}")
    executor = UnknownAfterDispatchExecutor()
    boundary = RprToolBoundary(runtime, lambda _: executor)
    return runtime, executor, boundary


def assert_unknown_is_preserved(runtime, executor, pathway_id: str) -> None:
    assert runtime.store.get_state(pathway_id) is PathwayState.WRITE_STATUS_UNKNOWN
    assert executor.calls == 1


def test_plain_python_boundary_preserves_unknown_without_blind_redispatch():
    pathway_id = "cross-runtime-plain"
    runtime, executor, boundary = make_boundary(pathway_id)
    call = AgentToolCall("external_write", {"value": 1}, "same-call")

    first = boundary.invoke(pathway_id=pathway_id, actor="agent", call=call)
    second = boundary.invoke(pathway_id=pathway_id, actor="agent", call=call)

    assert first.state == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert second.state == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert_unknown_is_preserved(runtime, executor, pathway_id)


def test_real_langgraph_stategraph_preserves_same_rpr_boundary():
    langgraph_graph = pytest.importorskip("langgraph.graph")
    StateGraph = langgraph_graph.StateGraph
    START = langgraph_graph.START
    END = langgraph_graph.END

    pathway_id = "cross-runtime-langgraph"
    runtime, executor, boundary = make_boundary(pathway_id)
    rpr_node = langgraph_tool_node(
        boundary,
        pathway_id=pathway_id,
        actor="agent",
        tool_name="external_write",
    )

    graph = StateGraph(dict)
    graph.add_node("external_write", rpr_node)
    graph.add_edge(START, "external_write")
    graph.add_edge("external_write", END)
    app = graph.compile()

    first = app.invoke({"call_id": "same-call", "arguments": {"value": 1}})
    second = app.invoke({"call_id": "same-call", "arguments": {"value": 1}})

    assert first["rpr"]["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert second["rpr"]["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert_unknown_is_preserved(runtime, executor, pathway_id)


def test_real_openai_agents_functiontool_preserves_same_rpr_boundary():
    agents = pytest.importorskip("agents")
    FunctionTool = agents.FunctionTool

    pathway_id = "cross-runtime-openai-agents"
    runtime, executor, boundary = make_boundary(pathway_id)
    handler = openai_function_tool_handler(
        boundary,
        pathway_id=pathway_id,
        actor="agent",
        tool_name="external_write",
    )

    async def invoke(_ctx, arguments_json: str):
        return handler(arguments_json)

    tool = FunctionTool(
        name="external_write",
        description="Cross-runtime RPR compatibility probe",
        params_json_schema={
            "type": "object",
            "properties": {
                "_rpr_call_id": {"type": "string"},
                "value": {"type": "integer"},
            },
            "required": ["_rpr_call_id", "value"],
            "additionalProperties": False,
        },
        on_invoke_tool=invoke,
    )

    payload = json.dumps({"_rpr_call_id": "same-call", "value": 1})
    first = json.loads(asyncio.run(tool.on_invoke_tool(None, payload)))
    second = json.loads(asyncio.run(tool.on_invoke_tool(None, payload)))

    assert first["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert second["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert_unknown_is_preserved(runtime, executor, pathway_id)


def test_real_temporal_activity_environment_preserves_same_rpr_boundary():
    temporal_activity = pytest.importorskip("temporalio.activity")
    temporal_testing = pytest.importorskip("temporalio.testing")

    pathway_id = "cross-runtime-temporal-activity"
    runtime, executor, boundary = make_boundary(pathway_id)

    @temporal_activity.defn(name="rpr_external_write_probe")
    async def external_write_activity(payload: dict) -> dict:
        outcome = boundary.invoke(
            pathway_id=pathway_id,
            actor="agent",
            call=AgentToolCall(
                "external_write",
                {"value": payload["value"]},
                payload["call_id"],
            ),
        )
        return {
            "state": outcome.state,
            "allowed": outcome.allowed,
            "reason": outcome.reason,
        }

    async def run_probe():
        env = temporal_testing.ActivityEnvironment()
        payload = {"call_id": "same-call", "value": 1}
        first = await env.run(external_write_activity, payload)
        second = await env.run(external_write_activity, payload)
        return first, second

    first, second = asyncio.run(run_probe())

    assert first["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert second["state"] == PathwayState.WRITE_STATUS_UNKNOWN.value
    assert_unknown_is_preserved(runtime, executor, pathway_id)
