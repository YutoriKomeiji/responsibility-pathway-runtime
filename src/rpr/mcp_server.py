# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, IO, Mapping

from .mcp_read_model import ReadOnlyDatabaseError, SQLiteReadModel
from .mcp_stable_snapshot import STABLE_PROTOCOL_VERSION

_SERVER_NAME = "responsibility-pathway-runtime"
_SERVER_VERSION = "0.1.0a3"

@dataclass(frozen=True)
class JsonRpcError(Exception):
    code: int
    message: str
    data: Mapping[str, Any] | None = None

_TOOLS: tuple[dict[str, Any], ...] = (
    {"name": "rpr.get_status", "description": "Return read-only RPR database status and pathway counts.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "rpr.list_pathways", "description": "List RPR pathways without changing runtime state.", "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}, "additionalProperties": False}},
    {"name": "rpr.get_pathway", "description": "Return one RPR pathway definition and current state.", "inputSchema": {"type": "object", "properties": {"pathway_id": {"type": "string", "minLength": 1}}, "required": ["pathway_id"], "additionalProperties": False}},
    {"name": "rpr.get_evidence", "description": "Return retained evidence events for one RPR pathway.", "inputSchema": {"type": "object", "properties": {"pathway_id": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 5000}}, "required": ["pathway_id"], "additionalProperties": False}},
    {"name": "rpr.list_unresolved", "description": "List pathways that are not completed, denied, or aborted.", "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}, "additionalProperties": False}},
)

class ReadOnlyRprMcpServer:
    """Minimal MCP server exposing only read-only RPR inspection tools."""
    def __init__(self, read_model: SQLiteReadModel) -> None:
        self.read_model = read_model
        self.initialize_seen = False
        self.initialized = False
    def handle(self, request: object) -> dict[str, Any] | None:
        if not isinstance(request, Mapping): raise JsonRpcError(-32600, "request must be a JSON object")
        if request.get("jsonrpc") != "2.0": raise JsonRpcError(-32600, "jsonrpc must be '2.0'")
        method = request.get("method")
        if not isinstance(method, str) or not method: raise JsonRpcError(-32600, "method must be a non-empty string")
        request_id = request.get("id")
        if method == "notifications/initialized":
            _empty_params(request.get("params"))
            if not self.initialize_seen: raise JsonRpcError(-32002, "initialize request has not completed")
            self.initialized = True
            return None
        if method == "initialize":
            result = self._initialize(request.get("params")); self.initialize_seen = True
            return self._response(request_id, result)
        if not self.initialized: raise JsonRpcError(-32002, "server has not received notifications/initialized")
        if method == "ping": _empty_params(request.get("params")); return self._response(request_id, {})
        if method == "tools/list": _empty_params(request.get("params")); return self._response(request_id, {"tools": list(_TOOLS)})
        if method == "tools/call": return self._response(request_id, self._call_tool(request.get("params")))
        raise JsonRpcError(-32601, f"method not found: {method}")
    @staticmethod
    def _initialize(params: object) -> dict[str, Any]:
        if not isinstance(params, Mapping): raise JsonRpcError(-32602, "initialize params must be an object")
        requested = params.get("protocolVersion")
        if requested != STABLE_PROTOCOL_VERSION: raise JsonRpcError(-32602, f"unsupported protocolVersion; expected {STABLE_PROTOCOL_VERSION}")
        return {"protocolVersion": STABLE_PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": _SERVER_NAME, "version": _SERVER_VERSION}, "instructions": "Read-only RPR inspection server for a trusted local MCP client. It cannot approve, execute, reconcile, resume, or mutate responsibility pathways."}
    def _call_tool(self, params: object) -> dict[str, Any]:
        if not isinstance(params, Mapping): raise JsonRpcError(-32602, "tools/call params must be an object")
        keys = set(params)
        if "name" not in keys or not keys <= {"name", "arguments"}: raise JsonRpcError(-32602, "tools/call params require name and may contain arguments")
        name, arguments = params.get("name"), params.get("arguments", {})
        if not isinstance(name, str) or not name: raise JsonRpcError(-32602, "tool name must be a non-empty string")
        if not isinstance(arguments, Mapping): raise JsonRpcError(-32602, "tool arguments must be an object")
        try: value = self._invoke(name, arguments)
        except KeyError as exc: return self._tool_result({"error": "pathway_not_found", "pathway_id": str(exc.args[0])}, is_error=True)
        except (ValueError, ReadOnlyDatabaseError) as exc: return self._tool_result({"error": "invalid_request", "message": str(exc)}, is_error=True)
        return self._tool_result(value)
    def _invoke(self, name: str, arguments: Mapping[str, Any]) -> Any:
        if name == "rpr.get_status": _require_keys(arguments, allowed=set()); return self.read_model.status()
        if name == "rpr.list_pathways": _require_keys(arguments, allowed={"limit"}); return {"pathways": self.read_model.list_pathways(limit=arguments.get("limit", 100))}
        if name == "rpr.get_pathway": _require_keys(arguments, allowed={"pathway_id"}, required={"pathway_id"}); return self.read_model.get_pathway(arguments["pathway_id"])
        if name == "rpr.get_evidence":
            _require_keys(arguments, allowed={"pathway_id", "limit"}, required={"pathway_id"})
            return {"pathway_id": arguments["pathway_id"], "events": self.read_model.get_evidence(arguments["pathway_id"], limit=arguments.get("limit", 500))}
        if name == "rpr.list_unresolved": _require_keys(arguments, allowed={"limit"}); return {"pathways": self.read_model.list_unresolved(limit=arguments.get("limit", 100))}
        raise ValueError(f"unknown tool: {name}")
    @staticmethod
    def _tool_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, sort_keys=True)}], "structuredContent": value}
        if is_error: result["isError"] = True
        return result
    @staticmethod
    def _response(request_id: object, result: Mapping[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": dict(result)}

def _empty_params(value: object) -> None:
    if value is None: return
    if not isinstance(value, Mapping) or value: raise JsonRpcError(-32602, "params must be an empty object when provided")

def _require_keys(arguments: Mapping[str, Any], *, allowed: set[str], required: set[str] | None = None) -> None:
    required = required or set(); keys = set(arguments); unexpected = sorted(keys - allowed); missing = sorted(required - keys)
    if unexpected or missing:
        details = []
        if unexpected: details.append(f"unexpected arguments: {', '.join(unexpected)}")
        if missing: details.append(f"missing arguments: {', '.join(missing)}")
        raise ValueError("; ".join(details))

def run_stdio(server: ReadOnlyRprMcpServer, *, stdin: IO[str] = sys.stdin, stdout: IO[str] = sys.stdout) -> int:
    for raw_line in stdin:
        if not raw_line.strip(): continue
        request_id: object = None; is_notification = False
        try:
            request = json.loads(raw_line)
            if isinstance(request, Mapping): request_id = request.get("id"); is_notification = "id" not in request
            response = server.handle(request)
        except json.JSONDecodeError as exc: response = _error_response(None, JsonRpcError(-32700, "parse error", {"detail": str(exc)}))
        except JsonRpcError as exc: response = None if is_notification else _error_response(request_id, exc)
        except Exception as exc: response = None if is_notification else _error_response(request_id, JsonRpcError(-32603, "internal error", {"type": type(exc).__name__}))
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"); stdout.flush()
    return 0

def _error_response(request_id: object, error: JsonRpcError) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": error.code, "message": error.message}
    if error.data is not None: payload["data"] = dict(error.data)
    return {"jsonrpc": "2.0", "id": request_id, "error": payload}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rpr-mcp"); parser.add_argument("--database", type=Path, required=True, help="Existing RPR SQLite database"); args = parser.parse_args(argv)
    try: read_model = SQLiteReadModel(args.database)
    except ReadOnlyDatabaseError as exc: print(f"rpr-mcp: {exc}", file=sys.stderr); return 2
    try: return run_stdio(ReadOnlyRprMcpServer(read_model))
    finally: read_model.close()

if __name__ == "__main__": raise SystemExit(main())
