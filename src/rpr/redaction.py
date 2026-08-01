# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


DEFAULT_SENSITIVE_KEYS = frozenset({
    "authorization", "cookie", "password", "secret", "token", "access_token",
    "refresh_token", "api_key", "private_key", "client_secret",
})


class EvidenceLimitError(ValueError):
    pass


@dataclass(frozen=True)
class RedactionPolicy:
    sensitive_keys: frozenset[str] = field(default_factory=lambda: DEFAULT_SENSITIVE_KEYS)
    replacement: str = "[REDACTED]"
    max_depth: int = 12
    max_items: int = 1000
    max_string_length: int = 16384

    def redact(self, value: Any) -> Any:
        budget = [self.max_items]
        return self._redact(value, depth=0, budget=budget)

    def _redact(self, value: Any, *, depth: int, budget: list[int]) -> Any:
        if depth > self.max_depth:
            raise EvidenceLimitError("evidence payload exceeds maximum depth")
        budget[0] -= 1
        if budget[0] < 0:
            raise EvidenceLimitError("evidence payload exceeds maximum item count")
        if isinstance(value, str):
            if len(value) > self.max_string_length:
                raise EvidenceLimitError("evidence string exceeds maximum length")
            return value
        if isinstance(value, Mapping):
            output: dict[str, Any] = {}
            for raw_key, item in value.items():
                key = str(raw_key)
                output[key] = self.replacement if key.casefold() in self.sensitive_keys else self._redact(item, depth=depth + 1, budget=budget)
            return output
        if isinstance(value, (list, tuple)):
            return [self._redact(item, depth=depth + 1, budget=budget) for item in value]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)
