# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Mapping


class SourceAuthority(StrEnum):
    CANONICAL = "canonical"
    AUTHORIZED = "authorized"
    CORROBORATED = "corroborated"
    UNVERIFIED = "unverified"
    HOSTILE = "hostile"


class SourceContextError(ValueError):
    """Raised when action-driving source context is incomplete or stale."""


@dataclass(frozen=True)
class SourceContext:
    source_id: str
    authority: SourceAuthority
    provenance: str
    observed_at: datetime
    applicable_to: tuple[str, ...]
    content_digest: str | None = None
    attributes: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.provenance.strip():
            raise SourceContextError("source_id and provenance are required")
        if self.observed_at.tzinfo is None:
            raise SourceContextError("observed_at must be timezone-aware")
        if not self.applicable_to:
            raise SourceContextError("applicable_to must identify at least one action or domain")
        if self.content_digest is not None and not self.content_digest.strip():
            raise SourceContextError("content_digest must be non-empty when supplied")

    def validate_for(
        self,
        action_name: str,
        *,
        maximum_age: timedelta,
        now: datetime | None = None,
        minimum_authority: SourceAuthority = SourceAuthority.AUTHORIZED,
    ) -> None:
        if maximum_age.total_seconds() < 0:
            raise ValueError("maximum_age must be non-negative")
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if action_name not in self.applicable_to and "*" not in self.applicable_to:
            raise SourceContextError("source context is not applicable to this action")
        if self.observed_at > current:
            raise SourceContextError("source context is dated in the future")
        if current - self.observed_at > maximum_age:
            raise SourceContextError("source context is stale")
        order = {
            SourceAuthority.HOSTILE: 0,
            SourceAuthority.UNVERIFIED: 1,
            SourceAuthority.CORROBORATED: 2,
            SourceAuthority.AUTHORIZED: 3,
            SourceAuthority.CANONICAL: 4,
        }
        if order[self.authority] < order[minimum_authority]:
            raise SourceContextError("source authority is below the required threshold")

    def to_evidence(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "authority": self.authority.value,
            "provenance": self.provenance,
            "observed_at": self.observed_at.astimezone(UTC).isoformat(),
            "applicable_to": list(self.applicable_to),
            "content_digest": self.content_digest,
            "attributes": dict(self.attributes or {}),
        }
