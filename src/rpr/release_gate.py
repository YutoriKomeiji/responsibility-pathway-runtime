# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping


_ALLOWED_DECISIONS = {"approve", "approve_with_conditions", "hold"}
_REQUIRED_EVIDENCE = {
    "clean_export_manifest",
    "wheel",
    "sdist",
    "sbom",
    "clean_install_e2e",
    "secret_scan",
    "vulnerability_review",
    "known_limitations",
}


@dataclass(frozen=True)
class ReleaseDecisionPack:
    source_commit: str
    version: str
    decision: str
    evidence_sha256: Mapping[str, str]
    decision_owner: str
    release_authority: str
    evidence_owner: str
    residual_owner: str
    conditions: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.decision not in _ALLOWED_DECISIONS:
            raise ValueError("invalid release decision")
        if not self.source_commit.strip() or not self.version.strip():
            raise ValueError("source commit and version are required")
        missing = sorted(_REQUIRED_EVIDENCE - set(self.evidence_sha256))
        if missing:
            raise ValueError(f"missing release evidence: {', '.join(missing)}")
        for name, digest in self.evidence_sha256.items():
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.lower()):
                raise ValueError(f"invalid SHA-256 for {name}")
        for owner in (self.decision_owner, self.release_authority, self.evidence_owner, self.residual_owner):
            if not owner.strip():
                raise ValueError("all release owners are required")
        if self.decision == "approve_with_conditions" and not self.conditions:
            raise ValueError("conditional approval requires conditions")
        if self.decision == "approve" and self.conditions:
            raise ValueError("unconditional approval cannot retain conditions")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        value = asdict(self)
        value["evidence_sha256"] = dict(sorted(self.evidence_sha256.items()))
        return value

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
