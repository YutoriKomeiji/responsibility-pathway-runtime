# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Responsibility Pathway Runtime public API."""

from .agent_adapters import AgentToolCall, AgentToolOutcome, RprToolBoundary, langgraph_tool_node, openai_function_tool_handler
from .attempts import AttemptConflictError, ExecutionAttemptRecord, SQLiteExecutionAttemptLedger
from .authority import AuthorityError
from .compensation import CompensationPlan, CompensationStatus, NoAutomaticCompensation
from .eu_ai_act_article50 import (
    ActorRole,
    Article50Assessment,
    Article50Decision,
    ContentContext,
    ContentModality,
    SystemFunction,
    TerritorialScope,
    TransparencyOutcome,
    evaluate_article50,
)
from .executor import ExecutionRequest, ExecutionResult, ExecutionStatus, LocalFileExecutor, ReadbackEvidence
from .http_executor import HttpMutationExecutor, JsonFieldReadback, ReadbackStrategy
from .identity import ExternalTokenVerifierResolver, VerifiedClaimsPrincipalResolver, VerifiedTokenClaims
from .message_executor import DeliveryReceipt, MessageTransport, OutboundMessageExecutor, SQLiteOutbox
from .models import ActionClass, EnvironmentTrust, PathwayDefinition, PathwayState, RuntimeDecision
from .principal import Principal, PrincipalError, StaticActorBinding, TrustedPrincipalResolver
from .reconciliation import ReconciliationResult, ReconciliationStatus, ReconciliationStrategy, reconcile_started_attempt
from .redaction import EvidenceLimitError, RedactionPolicy
from .rpe import PythonRpeEvaluator, RestRpeEvaluator, RpeContractError
from .runtime import EvidenceVerificationResult, RegistrationResult, ResponsibilityPathwayRuntime
from .source_context import SourceAuthority, SourceContext, SourceContextError
from .storage import IdempotencyConflictError, SQLiteStore
from .tenant import SQLiteTenantRegistry, TenantBoundaryError, TenantContext, TenantScopedRuntime

__all__ = [
    "ActionClass", "ActorRole", "AgentToolCall", "AgentToolOutcome", "Article50Assessment", "Article50Decision",
    "AttemptConflictError", "AuthorityError", "CompensationPlan", "CompensationStatus", "ContentContext",
    "ContentModality", "DeliveryReceipt", "EnvironmentTrust", "EvidenceLimitError", "EvidenceVerificationResult",
    "ExecutionAttemptRecord", "ExecutionRequest", "ExecutionResult", "ExecutionStatus", "ExternalTokenVerifierResolver",
    "HttpMutationExecutor", "IdempotencyConflictError", "JsonFieldReadback", "LocalFileExecutor", "MessageTransport",
    "NoAutomaticCompensation", "OutboundMessageExecutor", "PathwayDefinition", "PathwayState", "Principal",
    "PrincipalError", "PythonRpeEvaluator", "ReadbackEvidence", "ReadbackStrategy", "ReconciliationResult",
    "ReconciliationStatus", "ReconciliationStrategy", "RedactionPolicy", "RegistrationResult",
    "ResponsibilityPathwayRuntime", "RestRpeEvaluator", "RpeContractError", "RprToolBoundary", "RuntimeDecision",
    "SQLiteExecutionAttemptLedger", "SQLiteOutbox", "SQLiteStore", "SQLiteTenantRegistry", "SourceAuthority",
    "SourceContext", "SourceContextError", "StaticActorBinding", "SystemFunction", "TenantBoundaryError",
    "TenantContext", "TenantScopedRuntime", "TerritorialScope", "TransparencyOutcome", "TrustedPrincipalResolver",
    "VerifiedClaimsPrincipalResolver", "VerifiedTokenClaims", "evaluate_article50", "langgraph_tool_node",
    "openai_function_tool_handler", "reconcile_started_attempt",
]
