# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .executor import ExecutionRequest, Executor
from .runtime import ResponsibilityPathwayRuntime


@dataclass(frozen=True)
class AgentToolCall:
    tool_name: str
    arguments: Mapping[str, Any]
    call_id: str


@dataclass(frozen=True)
class AgentToolOutcome:
    allowed: bool
    pathway_id: str
    state: str
    output: Mapping[str, Any]
    reason: str | None = None


class RprToolBoundary:
    """Framework-neutral boundary used by concrete agent-framework adapters."""

    def __init__(self, runtime: ResponsibilityPathwayRuntime, executor_for: Callable[[str], Executor]) -> None:
        self.runtime = runtime
        self.executor_for = executor_for

    def invoke(self, *, pathway_id: str, actor: str, call: AgentToolCall) -> AgentToolOutcome:
        request = ExecutionRequest(
            operation_id=call.call_id,
            attempt_id=call.call_id,
            idempotency_key=call.call_id,
            action=call.tool_name,
            parameters=dict(call.arguments),
        )
        result = self.runtime.execute(pathway_id, request, actor=actor, executor=self.executor_for(call.tool_name))
        state = self.runtime.store.get_state(pathway_id).value
        return AgentToolOutcome(
            allowed=result.status.value == "succeeded",
            pathway_id=pathway_id,
            state=state,
            output={
                "status": result.status.value,
                "evidence": dict(result.evidence),
                "readback": None if result.readback is None else {
                    "verified": result.readback.verified,
                    "observed": dict(result.readback.observed),
                    "reason": result.readback.reason,
                },
            },
            reason=result.reason,
        )


def openai_function_tool_handler(boundary: RprToolBoundary, *, pathway_id: str, actor: str, tool_name: str) -> Callable[[str], str]:
    """Return a dependency-free handler suitable for wrapping with Agents SDK `function_tool`.

    RPR does not import the SDK. The application wraps this callable and may attach SDK tool
    guardrails. Hosted and built-in tools require a different integration boundary.
    """

    def handler(arguments_json: str) -> str:
        arguments = json.loads(arguments_json)
        call_id = str(arguments.pop("_rpr_call_id"))
        outcome = boundary.invoke(pathway_id=pathway_id, actor=actor, call=AgentToolCall(tool_name, arguments, call_id))
        return json.dumps(outcome.output | {"pathway_id": outcome.pathway_id, "state": outcome.state, "reason": outcome.reason}, ensure_ascii=False)

    return handler


def langgraph_tool_node(boundary: RprToolBoundary, *, pathway_id: str, actor: str, tool_name: str) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Return a node callable usable from a LangGraph `StateGraph` or tool wrapper."""

    def node(state: Mapping[str, Any]) -> Mapping[str, Any]:
        call_id = str(state["call_id"])
        arguments = dict(state.get("arguments", {}))
        outcome = boundary.invoke(pathway_id=pathway_id, actor=actor, call=AgentToolCall(tool_name, arguments, call_id))
        return dict(state) | {"rpr": {"allowed": outcome.allowed, "state": outcome.state, "output": dict(outcome.output), "reason": outcome.reason}}

    return node
