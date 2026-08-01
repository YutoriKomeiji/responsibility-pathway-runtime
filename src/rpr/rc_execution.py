# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
from dataclasses import asdict, dataclass
from pathlib import Path

from .clean_export import rehearse_clean_export

_INSTALLED_PROBE = r'''
import json
import socket
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from rpr.attempts import SQLiteExecutionAttemptLedger
from rpr.executor import ExecutionRequest, ExecutionStatus, LocalFileExecutor
from rpr.http_executor import HttpMutationExecutor, JsonFieldReadback

results = {}
with tempfile.TemporaryDirectory(prefix="rpr-installed-e2e-") as directory:
    root = Path(directory)
    request = ExecutionRequest("file-op", "file-attempt", "file-key", "replace_text_file", {"path": "result.txt", "content": "verified"})
    executor = LocalFileExecutor(root / "files")
    first = executor.execute(request)
    second = executor.execute(request)
    assert first.status is ExecutionStatus.SUCCEEDED and first.readback and first.readback.verified
    assert second == first and (root / "files" / "result.txt").read_text() == "verified"
    results["file_readback_and_replay"] = "passed"

    class Handler(BaseHTTPRequestHandler):
        calls = 0
        def do_POST(self):
            type(self).calls += 1
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            body = json.dumps({"value": payload["value"]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    http = HttpMutationExecutor(allowed_origins={origin}, readback=JsonFieldReadback("value", "expected"), allow_insecure_http=True)
    http_request = ExecutionRequest("http-op", "http-attempt", "http-key", "http_json_mutation", {"url": origin + "/mutate", "json": {"value": "ok"}, "expected": "ok"})
    http_first = http.execute(http_request)
    http_second = http.execute(http_request)
    server.shutdown(); thread.join()
    assert http_first.status is ExecutionStatus.SUCCEEDED and http_first.readback and http_first.readback.verified
    assert http_second == http_first and Handler.calls == 1
    results["http_readback_and_no_redispatch"] = "passed"

    probe = socket.socket(); probe.bind(("127.0.0.1", 0)); unused_port = probe.getsockname()[1]; probe.close()
    bad_origin = f"http://127.0.0.1:{unused_port}"
    unknown_executor = HttpMutationExecutor(allowed_origins={bad_origin}, readback=JsonFieldReadback("value", "expected"), allow_insecure_http=True, timeout_seconds=0.2)
    unknown = unknown_executor.execute(ExecutionRequest("unknown-op", "unknown-attempt", "unknown-key", "http_json_mutation", {"url": bad_origin + "/mutate", "json": {"value": "x"}, "expected": "x"}))
    assert unknown.status is ExecutionStatus.WRITE_STATUS_UNKNOWN
    results["ambiguous_transport_preserved_unknown"] = "passed"

    ledger_path = root / "attempts.sqlite3"
    ledger = SQLiteExecutionAttemptLedger(ledger_path)
    replay_request = ExecutionRequest("persist-op", "persist-attempt", "persist-key", "replace_text_file", {"path": "x", "content": "y"})
    replayed, _ = ledger.begin("pathway", replay_request)
    assert not replayed
    restarted = SQLiteExecutionAttemptLedger(ledger_path)
    replayed_after_restart, record = restarted.begin("pathway", replay_request)
    assert replayed_after_restart and record.status == "started"
    results["persistent_restart_replay"] = "passed"

print(json.dumps(results, sort_keys=True))
'''


@dataclass(frozen=True)
class CommandEvidence:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout_sha256: str
    stderr_sha256: str


@dataclass(frozen=True)
class CandidateExecutionEvidence:
    format_version: int
    source_commit: str
    python_version: str
    export_manifest_sha256: str
    wheel_sha256: str
    sdist_sha256: str
    commands: tuple[CommandEvidence, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["commands"] = [asdict(item) for item in self.commands]
        return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(name: str, command: list[str], *, cwd: Path, env: dict[str, str]) -> CommandEvidence:
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True, check=False)
    evidence = CommandEvidence(name, tuple(command), completed.returncode, _sha256_bytes(completed.stdout), _sha256_bytes(completed.stderr))
    if completed.returncode != 0:
        sys.stdout.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        raise RuntimeError(f"release-candidate command failed: {name}")
    return evidence


def _venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _clean_environment() -> dict[str, str]:
    allowed = {"PATH", "HOME", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "WINDIR"}
    environment = {key: value for key, value in os.environ.items() if key in allowed}
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def execute_release_candidate(source_root: str | Path, output_directory: str | Path, *, source_commit: str) -> CandidateExecutionEvidence:
    source = Path(source_root).resolve()
    output = Path(output_directory).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    export = output / "clean-export"
    manifest = rehearse_clean_export(source, export)
    environment = _clean_environment()
    commands: list[CommandEvidence] = []
    commands.append(_run("build", [sys.executable, "-m", "build", "--outdir", str(output / "dist")], cwd=export, env=environment))
    wheels = sorted((output / "dist").glob("*.whl")); sdists = sorted((output / "dist").glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("candidate build must produce exactly one wheel and one sdist")
    probe = output / "installed_probe.py"; probe.write_text(_INSTALLED_PROBE, encoding="utf-8")
    for label, artifact in (("wheel", wheels[0]), ("sdist", sdists[0])):
        root = output / f"venv-{label}"; venv.EnvBuilder(with_pip=True, clear=True).create(root); python = _venv_python(root)
        commands.append(_run(f"{label}-tooling", [str(python), "-m", "pip", "install", "setuptools", "wheel"], cwd=output, env=environment))
        install = [str(python), "-m", "pip", "install", "--no-deps"]
        if label == "sdist": install.append("--no-build-isolation")
        install.append(str(artifact))
        commands.append(_run(f"{label}-install", install, cwd=output, env=environment))
        commands.append(_run(f"{label}-import", [str(python), "-c", "import importlib.metadata, rpr; print(importlib.metadata.version('responsibility-pathway-runtime'))"], cwd=output, env=environment))
        commands.append(_run(f"{label}-e2e", [str(python), str(probe)], cwd=output, env=environment))
    result = CandidateExecutionEvidence(1, source_commit, sys.version.split()[0], manifest.manifest_sha256, _sha256_file(wheels[0]), _sha256_file(sdists[0]), tuple(commands), True)
    (output / "candidate-execution-evidence.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a frozen RPR candidate in clean wheel and sdist environments.")
    parser.add_argument("source_root", nargs="?", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    execute_release_candidate(args.source_root, args.output, source_commit=args.source_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
