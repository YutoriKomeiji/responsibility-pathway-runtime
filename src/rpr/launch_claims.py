# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable

_ALLOWED_STATUS = {"proposed", "supported", "blocked", "retired"}


@dataclass(frozen=True)
class LaunchClaim:
    claim_id: str
    text: str
    status: str
    evidence_sha256: tuple[str, ...] = ()
    limitation_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.claim_id.strip() or not self.text.strip():
            raise ValueError("claim id and text are required")
        if self.status not in _ALLOWED_STATUS:
            raise ValueError("invalid claim status")
        for digest in self.evidence_sha256:
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.lower()):
                raise ValueError("claim evidence must be SHA-256")
        if self.status == "supported" and not self.evidence_sha256:
            raise ValueError("supported claims require evidence")
        if self.status in {"proposed", "blocked"} and self.evidence_sha256:
            raise ValueError("unapproved claims cannot carry release evidence")


def build_launch_claim_registry(claims: Iterable[LaunchClaim]) -> dict[str, object]:
    ordered = sorted(claims, key=lambda item: item.claim_id)
    identifiers: set[str] = set()
    for claim in ordered:
        claim.validate()
        if claim.claim_id in identifiers:
            raise ValueError("duplicate claim id")
        identifiers.add(claim.claim_id)
    values = [asdict(item) for item in ordered]
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "format_version": 1,
        "claims": values,
        "registry_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
