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

## 1. Verify the release artifact

Compare the file name, byte size, and SHA-256 digest with [`release-manifest.json`](../../release-manifest.json).

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

## 4. Start with a non-consequential local rehearsal

Use a disposable directory and synthetic data. Confirm that the host application can:

1. register a pathway and declared authority;
2. reach a Human Gate rather than bypassing it;
3. create and retain an execution attempt;
4. attach independent readback evidence;
5. resume after restart without repeating an unresolved effect;
6. expose repair or reconciliation when completion cannot be established.

Do not begin with production credentials, customer data, irreversible actions, or a remote service whose write result cannot be independently read back.

## 5. Record the environment

Retain at least:

- operating system and architecture;
- Python and pip versions;
- installation source and artifact digest;
- RPR version and Freeze ID;
- host framework and adapter path;
- network, proxy, TLS, identity, and credential arrangement;
- exact command, expected result, actual result, and relevant logs with secrets removed.

## 6. Report field evidence

Use the environment-report Issue form for successful or failed reproducible tests. Use the bug form for product defects, the integration form for framework or service requests, and the private route in `SECURITY.md` for vulnerabilities.

## Stop conditions

Stop the rehearsal when authority is absent, the independent readback source is unavailable, a credential may be exposed, an external effect is ambiguous, the pathway cannot be restored, or the next action would be irreversible without explicit human approval.
