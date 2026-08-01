# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Iterable

from .redaction import RedactionPolicy


@dataclass(frozen=True)
class EvidenceEvent:
    pathway_id: str
    event_type: str
    actor: str
    payload: dict[str, Any]
    occurred_at: str
    previous_hash: str | None
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_payload(*, pathway_id: str, event_type: str, actor: str, payload: dict[str, Any], occurred_at: str, previous_hash: str | None) -> str:
    return json.dumps({"pathway_id": pathway_id, "event_type": event_type, "actor": actor, "payload": payload, "occurred_at": occurred_at, "previous_hash": previous_hash}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_event(*, pathway_id: str, event_type: str, actor: str, payload: dict[str, Any], previous_hash: str | None, redaction_policy: RedactionPolicy | None = None) -> EvidenceEvent:
    safe_payload = (redaction_policy or RedactionPolicy()).redact(payload)
    occurred_at = datetime.now(UTC).isoformat()
    canonical = _canonical_payload(pathway_id=pathway_id, event_type=event_type, actor=actor, payload=safe_payload, occurred_at=occurred_at, previous_hash=previous_hash)
    event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return EvidenceEvent(pathway_id, event_type, actor, safe_payload, occurred_at, previous_hash, event_hash)


def verify_event(event: dict[str, Any]) -> bool:
    canonical = _canonical_payload(pathway_id=str(event["pathway_id"]), event_type=str(event["event_type"]), actor=str(event["actor"]), payload=dict(event["payload"]), occurred_at=str(event["occurred_at"]), previous_hash=event.get("previous_hash"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest() == event.get("event_hash")


def verify_chain(events: Iterable[dict[str, Any]]) -> tuple[bool, int | None, str | None]:
    previous: str | None = None
    for index, event in enumerate(events):
        if event.get("previous_hash") != previous:
            return False, index, "previous_hash_mismatch"
        if not verify_event(event):
            return False, index, "event_hash_mismatch"
        previous = str(event["event_hash"])
    return True, None, None
