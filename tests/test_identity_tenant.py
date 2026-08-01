# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from datetime import UTC, datetime

import pytest

from rpr.identity import ExternalTokenVerifierResolver, VerifiedClaimsPrincipalResolver, VerifiedTokenClaims
from rpr.models import ActionClass, EnvironmentTrust, PathwayDefinition
from rpr.principal import PrincipalError
from rpr.rpe import AllowAllDevelopmentEvaluator
from rpr.runtime import ResponsibilityPathwayRuntime
from rpr.tenant import SQLiteTenantRegistry, TenantBoundaryError, TenantContext, TenantScopedRuntime


def test_verified_claims_resolver_requires_allowed_issuer_audience_and_time():
    now = datetime(2026, 7, 30, 6, 0, tzinfo=UTC)
    resolver = VerifiedClaimsPrincipalResolver(
        allowed_issuers=["https://id.example.com/"],
        expected_audience="rpr-api",
        now=lambda: now,
    )
    claims = VerifiedTokenClaims(
        {
            "iss": "https://id.example.com",
            "sub": "alice",
            "aud": ["other", "rpr-api"],
            "exp": now.timestamp() + 300,
            "iat": now.timestamp() - 1,
            "tenant_id": "tenant-a",
        },
        "oidc:jwks:RS256",
    )
    principal = resolver.resolve(claims)
    assert principal.subject == "alice"
    assert principal.claims["tenant_id"] == "tenant-a"


def test_verified_claims_resolver_rejects_raw_token_and_expired_claims():
    now = datetime(2026, 7, 30, 6, 0, tzinfo=UTC)
    resolver = VerifiedClaimsPrincipalResolver(
        allowed_issuers=["https://id.example.com"], expected_audience="rpr-api", clock_skew_seconds=0, now=lambda: now
    )
    with pytest.raises(PrincipalError):
        resolver.resolve("header.payload.signature")
    with pytest.raises(PrincipalError):
        resolver.resolve(VerifiedTokenClaims({"iss": "https://id.example.com", "sub": "a", "aud": "rpr-api", "exp": now.timestamp()}, "verified"))


def test_external_verifier_must_return_verified_claims():
    claims_resolver = VerifiedClaimsPrincipalResolver(allowed_issuers=["issuer"], expected_audience="aud")
    resolver = ExternalTokenVerifierResolver(lambda credential: credential, claims_resolver)
    with pytest.raises(PrincipalError):
        resolver.resolve({"iss": "issuer"})


def definition(pathway_id: str, tenant_id: str) -> PathwayDefinition:
    return PathwayDefinition(
        pathway_id=pathway_id,
        action_name="observe",
        action_class=ActionClass.SUGGEST_ONLY,
        environment_trust=EnvironmentTrust.TRUSTED_INTERNAL,
        decision_owner="owner",
        approval_authority=None,
        execution_actor="agent",
        stop_authority="operator",
        evidence_owner="audit",
        repair_owner="support",
        resume_authority="manager",
        human_return_point="before_action",
        residual_owner="owner",
        metadata={"tenant_id": tenant_id},
    )


def test_tenant_scoped_runtime_blocks_cross_tenant_access():
    runtime = ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator())
    registry = SQLiteTenantRegistry()
    tenant_a = TenantScopedRuntime(runtime, registry, TenantContext("tenant-a"))
    tenant_b = TenantScopedRuntime(runtime, registry, TenantContext("tenant-b"))
    tenant_a.register(definition("p-tenant", "tenant-a"), idempotency_key="tenant-a-1")
    assert tenant_a.evidence("p-tenant")
    with pytest.raises(TenantBoundaryError):
        tenant_b.evidence("p-tenant")


def test_tenant_metadata_cannot_disagree_with_context():
    scoped = TenantScopedRuntime(
        ResponsibilityPathwayRuntime(rpe=AllowAllDevelopmentEvaluator()), SQLiteTenantRegistry(), TenantContext("tenant-a")
    )
    with pytest.raises(TenantBoundaryError):
        scoped.register(definition("p-wrong", "tenant-b"), idempotency_key="wrong-1")
