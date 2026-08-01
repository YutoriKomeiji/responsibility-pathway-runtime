# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Mapping, Sequence

from .principal import Principal, PrincipalError, PrincipalResolver


@dataclass(frozen=True)
class VerifiedTokenClaims:
    """Claims produced only after signature and algorithm verification by a trusted verifier."""

    values: Mapping[str, Any]
    verification_method: str


class VerifiedClaimsPrincipalResolver(PrincipalResolver):
    """Build a Principal from already-verified OIDC/JWT claims.

    This class does not parse or verify compact JWT strings. Signature, algorithm, key,
    certificate, nonce, and token-type verification belong to the supplied identity layer.
    """

    def __init__(
        self,
        *,
        allowed_issuers: Sequence[str],
        expected_audience: str,
        clock_skew_seconds: int = 60,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.allowed_issuers = frozenset(value.rstrip("/") for value in allowed_issuers if value.strip())
        self.expected_audience = expected_audience.strip()
        self.clock_skew_seconds = clock_skew_seconds
        self.now = now or (lambda: datetime.now(UTC))
        if not self.allowed_issuers or not self.expected_audience or clock_skew_seconds < 0:
            raise ValueError("allowed issuers, audience, and non-negative clock skew are required")

    def resolve(self, credential: object) -> Principal:
        if not isinstance(credential, VerifiedTokenClaims):
            raise PrincipalError("verified claims resolver requires VerifiedTokenClaims")
        claims = credential.values
        issuer = str(claims.get("iss", "")).rstrip("/")
        subject = str(claims.get("sub", "")).strip()
        if issuer not in self.allowed_issuers:
            raise PrincipalError("token issuer is not allowed")
        if not subject:
            raise PrincipalError("token subject is required")
        if not self._audience_matches(claims.get("aud")):
            raise PrincipalError("token audience does not match")
        now_ts = self.now().timestamp()
        skew = float(self.clock_skew_seconds)
        exp = self._numeric_claim(claims, "exp", required=True)
        nbf = self._numeric_claim(claims, "nbf", required=False)
        iat = self._numeric_claim(claims, "iat", required=False)
        if exp is not None and now_ts - skew >= exp:
            raise PrincipalError("token is expired")
        if nbf is not None and now_ts + skew < nbf:
            raise PrincipalError("token is not yet valid")
        if iat is not None and iat > now_ts + skew:
            raise PrincipalError("token issued-at is in the future")
        safe_claims = {
            key: str(value)
            for key, value in claims.items()
            if key in {"azp", "client_id", "tenant_id", "tid", "scope", "roles"}
        }
        return Principal(subject, issuer, credential.verification_method, safe_claims)

    def _audience_matches(self, value: Any) -> bool:
        if isinstance(value, str):
            return value == self.expected_audience
        if isinstance(value, (list, tuple)):
            return self.expected_audience in {str(item) for item in value}
        return False

    @staticmethod
    def _numeric_claim(claims: Mapping[str, Any], name: str, *, required: bool) -> float | None:
        value = claims.get(name)
        if value is None:
            if required:
                raise PrincipalError(f"token {name} claim is required")
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise PrincipalError(f"token {name} claim must be numeric") from exc


class ExternalTokenVerifierResolver(PrincipalResolver):
    """Compose a trusted external token verifier with strict claim validation."""

    def __init__(self, verifier: Callable[[object], VerifiedTokenClaims], claims_resolver: VerifiedClaimsPrincipalResolver) -> None:
        self.verifier = verifier
        self.claims_resolver = claims_resolver

    def resolve(self, credential: object) -> Principal:
        verified = self.verifier(credential)
        if not isinstance(verified, VerifiedTokenClaims):
            raise PrincipalError("external verifier did not return VerifiedTokenClaims")
        return self.claims_resolver.resolve(verified)
