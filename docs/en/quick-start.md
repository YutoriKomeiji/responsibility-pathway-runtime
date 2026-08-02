<!--
Document Title: RPR Quick Start
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Quick Start

RPR is provided under the [MIT License](../../LICENSE), without warranty. Begin with a disposable, non-consequential rehearsal and decide independently whether the software is suitable for your environment.

## Rehearsal checklist

| Step | Action | Evidence to retain |
|---|---|---|
| 1 | Verify the artifact against [`release-manifest.json`](../../release-manifest.json) | File name, byte size, SHA-256 digest |
| 2 | Create an isolated Python 3.11 environment | Python and pip versions |
| 3 | Install the verified wheel | Installation log and dependency resolution |
| 4 | Confirm the CLI surface | `rpr --help` output |
| 5 | Run a local synthetic pathway | Pathway, attempt, readback, and final state |
| 6 | Exercise restart or ambiguity handling | Proof that no unresolved effect was silently repeated |

## 1. Verify the artifact

```bash
sha256sum responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
sha256sum responsibility_pathway_runtime-0.1.0a2.tar.gz
```

Do not install an artifact whose digest or size differs from the manifest.

## 2. Create an isolated environment

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
```

## 3. Confirm the command surface

```bash
rpr --help
python -m responsibility_pathway_runtime --help
```

## 4. Run a non-consequential rehearsal

Use a disposable directory and synthetic data. Confirm that the host application can register a pathway and authority, reach a Human Gate, retain an execution attempt, attach independent readback evidence, restore unresolved state after restart, and expose repair or reconciliation when completion cannot be established.

Do not begin with production credentials, customer data, irreversible actions, or a remote write that cannot be independently read back.

## Environment record

| Category | Record |
|---|---|
| Runtime | OS, architecture, Python and pip versions |
| Artifact | Source, version, Freeze ID, digest |
| Integration | Host framework, adapter, network, proxy, TLS, identity, credentials |
| Test | Exact command, expected result, actual result |
| Evidence | Sanitized logs, readback source, final pathway state |

## Reporting routes

| Finding | Route |
|---|---|
| Reproducible environment result | Environment-report Issue form |
| Product defect | Bug Issue form |
| Framework or service request | Integration Issue form |
| Potential vulnerability | Private route in [`SECURITY.md`](../../SECURITY.md) |

## Stop conditions

Stop the rehearsal when authority is absent, independent readback is unavailable, credentials may be exposed, an external effect is ambiguous, the pathway cannot be restored, or the next action would be irreversible without explicit human approval.
