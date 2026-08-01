# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


class PrincipalError(PermissionError):
    """Raised when a principal cannot be authenticated or bound to an actor."""


@dataclass(frozen=True)
class Principal:
    subject: str
    issuer: str
    authentication_method: str
    claims: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.subject.strip() or not self.issuer.strip() or not self.authentication_method.strip():
            raise PrincipalError("subject, issuer, and authentication_method are required")


class PrincipalResolver(Protocol):
    def resolve(self, credential: object) -> Principal: ...


class ActorBinding(Protocol):
    def actor_for(self, principal: Principal) -> str: ...


@dataclass(frozen=True)
class StaticActorBinding:
    bindings: Mapping[tuple[str, str], str]

    def actor_for(self, principal: Principal) -> str:
        actor = self.bindings.get((principal.issuer, principal.subject), "").strip()
        if not actor:
            raise PrincipalError("principal is not bound to an RPR actor")
        return actor


@dataclass(frozen=True)
class TrustedPrincipalResolver:
    """Accepts an already authenticated Principal from a trusted application boundary."""

    def resolve(self, credential: object) -> Principal:
        if not isinstance(credential, Principal):
            raise PrincipalError("trusted resolver requires a Principal instance")
        return credential
