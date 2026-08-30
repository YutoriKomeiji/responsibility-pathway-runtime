<!--
Document Title: RPR Quick Start
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a5
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Quick Start

RPR is provided under the [MIT License](../../LICENSE), without warranty. Begin with a disposable, non-consequential rehearsal and decide independently whether the software is suitable for your environment.

GitHub prerelease/source and the PyPI package are aligned at public-alpha `0.1.0a5`.

- [PyPI package — 0.1.0a5](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a5/)
- [GitHub Prerelease — v0.1.0a5](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a5)
- [Live RPR browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html)
- [Public repository](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

## Rehearsal checklist

| Step | Action | Evidence to retain |
|---:|---|---|
| 1 | Record the package version and source | PyPI URL, version, repository URL, and tag |
| 2 | Create an isolated Python 3.11 environment | Python and pip versions |
| 3 | Install the pinned Public Alpha from PyPI | Installation log and resolved package version |
| 4 | Confirm the CLI surface | `rpr --help` output |
| 5 | Run a local synthetic pathway | Pathway, attempt, readback, and final state |
| 6 | Exercise restart or ambiguity handling | Proof that no unresolved effect was silently repeated |

## 1. Create an isolated environment and install

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility-pathway-runtime==0.1.0a5
```

Confirm the installed version and command surface:

```bash
python -m pip show responsibility-pathway-runtime
rpr --help
rpr-mcp --help
```

For source inspection or development against the matching GitHub prerelease:

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
git checkout v0.1.0a5
python -m pip install -e .
```

The Windows UTF-8 BOM repair is included in `0.1.0a5` and is verified for the reproduced environment and input path. That evidence does not imply universal Windows or customer-environment verification.

## 2. Run a non-consequential rehearsal

Use a disposable directory and synthetic data. Confirm that the host application can register a pathway and authority, reach a Human Gate, retain an execution attempt, attach independent readback evidence, restore unresolved state after restart, and expose repair or reconciliation when completion cannot be established.

Do not begin with production credentials, customer data, irreversible actions, or a remote write that cannot be independently read back.

## Environment record

| Category | Record |
|---|---|
| Runtime | OS, architecture, Python and pip versions |
| Distribution | PyPI URL, installed version, GitHub tag or commit |
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
