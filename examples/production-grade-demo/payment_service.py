# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
"""Language: English comments; JSON responses are language-neutral.

Deterministic localhost payment fixture for the RPR production-grade demo.
This is the only test double in the scenario; RPR runtime behavior is real.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class PaymentState:
    payments: dict[str, dict] = field(default_factory=dict)
    dispatch_count: int = 0
    timeout_after_acceptance: bool = False
    readback_available: bool = True


class PaymentServer:
    def __init__(self, state: PaymentState):
        self.state = state
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, status: int, payload: dict) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                payment_id = payload["payment_id"]
                outer.state.dispatch_count += 1
                outer.state.payments.setdefault(payment_id, {**payload, "status": "accepted"})
                if outer.state.timeout_after_acceptance:
                    self.close_connection = True
                    return
                self._json(200, {"payment_id": payment_id, "status": "accepted"})

            def do_GET(self):  # noqa: N802
                if not outer.state.readback_available:
                    self._json(503, {"error": "readback_unavailable"})
                    return
                payment_id = self.path.rsplit("/", 1)[-1]
                payment = outer.state.payments.get(payment_id)
                self._json(200 if payment else 404, payment or {"error": "not_found"})

            def log_message(self, format, *args):  # noqa: A002
                del format, args

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.thread.join(timeout=3)
        self.server.server_close()
