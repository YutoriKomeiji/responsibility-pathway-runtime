# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .executor import ExecutionRequest, ExecutionResult, Executor
from .models import PathwayDefinition, PathwayState
from .runtime import RegistrationResult, ResponsibilityPathwayRuntime

TENANT_SCHEMA_VERSION = 1


class TenantBoundaryError(PermissionError):
    """Raised when a pathway crosses an explicit tenant ownership boundary."""


class TenantSchemaVersionError(RuntimeError):
    """Raised when a tenant-registry schema cannot be opened safely."""


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise TenantBoundaryError("tenant_id is required")


class SQLiteTenantRegistry:
    """Persist pathway ownership separately from caller-provided metadata."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(database), timeout=30.0, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA busy_timeout = 30000")
        self._migrate()

    def _migrate(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS rpy_tenant_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = self._connection.execute(
                "SELECT value FROM rpy_tenant_schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            version = 0 if row is None else int(row["value"])
            if version > TENANT_SCHEMA_VERSION:
                raise TenantSchemaVersionError(
                    f"tenant schema {version} is newer than supported schema {TENANT_SCHEMA_VERSION}"
                )
            if version < 0:
                raise TenantSchemaVersionError("tenant schema version cannot be negative")
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS tenant_pathways (
                    pathway_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            self._connection.execute(
                "INSERT INTO rpy_tenant_schema_metadata(key, value) VALUES ('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(TENANT_SCHEMA_VERSION),),
            )
            self._connection.execute("COMMIT")
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    @property
    def schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT value FROM rpy_tenant_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            raise TenantSchemaVersionError("tenant schema metadata is missing")
        return int(row["value"])

    def claim(self, context: TenantContext, pathway_id: str) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute("SELECT tenant_id FROM tenant_pathways WHERE pathway_id = ?", (pathway_id,)).fetchone()
            if row is not None and str(row["tenant_id"]) != context.tenant_id:
                raise TenantBoundaryError("pathway is already owned by another tenant")
            if row is None:
                self._connection.execute(
                    "INSERT INTO tenant_pathways(pathway_id, tenant_id) VALUES (?, ?)",
                    (pathway_id, context.tenant_id),
                )
            self._connection.execute("COMMIT")
        except Exception:
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            raise

    def require(self, context: TenantContext, pathway_id: str) -> None:
        row = self._connection.execute("SELECT tenant_id FROM tenant_pathways WHERE pathway_id = ?", (pathway_id,)).fetchone()
        if row is None:
            raise TenantBoundaryError("pathway has no registered tenant owner")
        if str(row["tenant_id"]) != context.tenant_id:
            raise TenantBoundaryError("tenant does not own pathway")


class TenantScopedRuntime:
    """Tenant-enforcing façade over ResponsibilityPathwayRuntime.

    Applications should expose this façade rather than the unscoped runtime in multi-tenant
    services. Database credentials, filesystem roots, executor credentials, and network egress
    must still be isolated by deployment.
    """

    def __init__(self, runtime: ResponsibilityPathwayRuntime, registry: SQLiteTenantRegistry, context: TenantContext) -> None:
        self.runtime = runtime
        self.registry = registry
        self.context = context

    def register(self, definition: PathwayDefinition, *, idempotency_key: str) -> RegistrationResult:
        declared = str(definition.metadata.get("tenant_id", "")).strip()
        if declared and declared != self.context.tenant_id:
            raise TenantBoundaryError("definition tenant metadata does not match tenant context")
        self.registry.claim(self.context, definition.pathway_id)
        return self.runtime.register(definition, idempotency_key=idempotency_key)

    def transition(self, pathway_id: str, target: PathwayState, *, actor: str, reason: str) -> PathwayState:
        self.registry.require(self.context, pathway_id)
        return self.runtime.transition(pathway_id, target, actor=actor, reason=reason)

    def execute(self, pathway_id: str, request: ExecutionRequest, *, actor: str, executor: Executor) -> ExecutionResult:
        self.registry.require(self.context, pathway_id)
        return self.runtime.execute(pathway_id, request, actor=actor, executor=executor)

    def evidence(self, pathway_id: str) -> list[dict]:
        self.registry.require(self.context, pathway_id)
        return self.runtime.evidence(pathway_id)
