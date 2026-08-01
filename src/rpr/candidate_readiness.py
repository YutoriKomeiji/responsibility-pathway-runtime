# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping


_INTERNAL_CHECKS = (
    "pytest",
    "json_python_lean_parity",
    "lean_build",
    "wheel_install",
    "sdist_install",
    "release_audit",
    "rc_rehearsal",
    "clean_export",
)
_EXTERNAL_GATES = (
    "secret_scan",
    "vulnerability_review",
    "human_gate",
)


@dataclass(frozen=True)
class CandidateReadinessReport:
    source_commit: str
    internal_checks: Mapping[str, bool]
    external_gates: Mapping[str, bool]
    evidence_sha256: Mapping[str, str]
    residual_owner: str

    def validate(self) -> None:
        if not self.source_commit.strip():
            raise ValueError("source commit is required")
        if not self.residual_owner.strip():
            raise ValueError("residual owner is required")

        missing_internal = [name for name in _INTERNAL_CHECKS if name not in self.internal_checks]
        missing_external = [name for name in _EXTERNAL_GATES if name not in self.external_gates]
        if missing_internal:
            raise ValueError(f"missing internal checks: {', '.join(missing_internal)}")
        if missing_external:
            raise ValueError(f"missing external gates: {', '.join(missing_external)}")

        unknown_internal = sorted(set(self.internal_checks) - set(_INTERNAL_CHECKS))
        unknown_external = sorted(set(self.external_gates) - set(_EXTERNAL_GATES))
        if unknown_internal:
            raise ValueError(f"unknown internal checks: {', '.join(unknown_internal)}")
        if unknown_external:
            raise ValueError(f"unknown external gates: {', '.join(unknown_external)}")

        for name, digest in self.evidence_sha256.items():
            normalized = digest.lower()
            if len(normalized) != 64 or any(character not in "0123456789abcdef" for character in normalized):
                raise ValueError(f"invalid SHA-256 for {name}")

    @property
    def internal_ready(self) -> bool:
        self.validate()
        return all(self.internal_checks[name] for name in _INTERNAL_CHECKS)

    @property
    def external_ready(self) -> bool:
        self.validate()
        return all(self.external_gates[name] for name in _EXTERNAL_GATES)

    @property
    def decision(self) -> str:
        return "ready_for_human_release_decision" if self.internal_ready and self.external_ready else "hold"

    @property
    def blocking_items(self) -> tuple[str, ...]:
        self.validate()
        blocked = [name for name in _INTERNAL_CHECKS if not self.internal_checks[name]]
        blocked.extend(name for name in _EXTERNAL_GATES if not self.external_gates[name])
        return tuple(blocked)

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "source_commit": self.source_commit,
            "decision": self.decision,
            "internal_ready": self.internal_ready,
            "external_ready": self.external_ready,
            "blocking_items": list(self.blocking_items),
            "internal_checks": {name: self.internal_checks[name] for name in _INTERNAL_CHECKS},
            "external_gates": {name: self.external_gates[name] for name in _EXTERNAL_GATES},
            "evidence_sha256": dict(sorted(self.evidence_sha256.items())),
            "residual_owner": self.residual_owner,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
