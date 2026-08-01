# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol
from urllib import error, request

from .models import RuntimeDecision


SUPPORTED_DECISION_VALUES = {item.value for item in RuntimeDecision}


@dataclass(frozen=True)
class RpeResult:
    decision: RuntimeDecision
    reason_codes: tuple[str, ...] = ()
    raw: dict[str, Any] | None = None
    contract_version: str | None = None


class RpeEvaluator(Protocol):
    def evaluate(self, action_request: dict[str, Any]) -> RpeResult: ...


class RpeContractError(RuntimeError):
    """Raised when an RPE response is structurally incompatible with RPR."""


class AllowAllDevelopmentEvaluator:
    """Explicit development-only evaluator; never use as an implicit fallback."""

    def evaluate(self, action_request: dict[str, Any]) -> RpeResult:
        del action_request
        return RpeResult(RuntimeDecision.ALLOW, ("development_evaluator",))


class UnavailableRpeEvaluator:
    def evaluate(self, action_request: dict[str, Any]) -> RpeResult:
        del action_request
        return RpeResult(RuntimeDecision.HUMAN_GATE, ("rpe_unavailable",))


def _normalize_result(value: Any, *, expected_contract_version: str | None = None) -> RpeResult:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    elif not isinstance(value, dict) and hasattr(value, "__dict__"):
        value = dict(value.__dict__)
    if not isinstance(value, dict):
        raise RpeContractError("RPE result must be a mapping")

    decision_value = value.get("decision") or value.get("outcome")
    if isinstance(decision_value, dict):
        decision_value = decision_value.get("decision") or decision_value.get("outcome")
    if decision_value not in SUPPORTED_DECISION_VALUES:
        raise RpeContractError(f"unsupported RPE decision: {decision_value!r}")

    contract_version = value.get("contract_version") or value.get("schema_version")
    if expected_contract_version and contract_version != expected_contract_version:
        raise RpeContractError(
            f"RPE contract version mismatch: expected {expected_contract_version}, got {contract_version}"
        )

    reasons = value.get("reason_codes") or value.get("reasons") or ()
    if isinstance(reasons, str):
        reasons = (reasons,)
    return RpeResult(
        decision=RuntimeDecision(str(decision_value)),
        reason_codes=tuple(str(item) for item in reasons),
        raw=value,
        contract_version=None if contract_version is None else str(contract_version),
    )


class PythonRpeEvaluator:
    """Adapter for the canonical RPE Python API without copying RPE semantics."""

    def __init__(
        self,
        evaluate_action: Callable[[dict[str, Any], Iterable[dict[str, Any]]], Any],
        requirement_packs: Iterable[dict[str, Any]] | Callable[[], Iterable[dict[str, Any]]],
        *,
        expected_contract_version: str | None = None,
    ) -> None:
        self._evaluate_action = evaluate_action
        self._requirement_packs = requirement_packs
        self._expected_contract_version = expected_contract_version

    def evaluate(self, action_request: dict[str, Any]) -> RpeResult:
        packs = self._requirement_packs() if callable(self._requirement_packs) else self._requirement_packs
        try:
            raw = self._evaluate_action(action_request, tuple(packs))
            return _normalize_result(raw, expected_contract_version=self._expected_contract_version)
        except RpeContractError:
            raise
        except Exception as exc:  # fail closed across the external boundary
            return RpeResult(RuntimeDecision.HUMAN_GATE, ("rpe_python_error", type(exc).__name__))


class RestRpeEvaluator:
    """Dependency-free local REST adapter for RPE's action-evaluation endpoint."""

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float = 5.0,
        expected_contract_version: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout_seconds
        self._expected_contract_version = expected_contract_version
        self._headers = {"Content-Type": "application/json", "Accept": "application/json", **(headers or {})}

    def evaluate(self, action_request: dict[str, Any]) -> RpeResult:
        payload = json.dumps(action_request, ensure_ascii=False).encode("utf-8")
        req = request.Request(self._endpoint, data=payload, headers=self._headers, method="POST")
        try:
            with request.urlopen(req, timeout=self._timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
            return _normalize_result(raw, expected_contract_version=self._expected_contract_version)
        except RpeContractError:
            raise
        except (error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return RpeResult(RuntimeDecision.HUMAN_GATE, ("rpe_rest_unavailable", type(exc).__name__))
