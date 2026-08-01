# Responsibility Pathway Runtime

**Govern external actions without losing evidence, recovery, or the human decision point.**

Responsibility Pathway Runtime (RPR) is an MIT-licensed Python runtime for applications that need to place an explicit responsibility pathway in front of consequential external actions. It helps a host application preserve actor and authority declarations, execution-attempt continuity, readback evidence, fail-closed ambiguity handling, repair routes, and Human Gate decisions.

> **Public alpha — 0.1.0a2**  
> Freeze ID: `RPR-CF-2026-08-01-02`  
> Tested final rehearsal profile: Linux, Python 3.11  
> RPR is not a legal-responsibility engine, identity provider, secret manager, production gateway, or guarantee of exactly-once effects across arbitrary remote systems.

[日本語の入口](docs/ja/README.md) · [Quick Start](docs/en/quick-start.md) · [Product documentation](docs/en/README.md) · [Report an issue](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues)

## Why RPR

AI agents and automation can execute faster than people can reconstruct what happened. RPR provides a bounded runtime layer where an integrating application can:

- declare actors, authority, and the proposed action;
- evaluate and retain an explicit pathway state;
- bind operations, attempts, and idempotency identity;
- require independent readback before completion;
- stop ambiguous writes as `write_status_unknown` instead of false success;
- retain Human Gate, repair, resume, reconciliation, and evidence continuity;
- survive restart without silently repeating unresolved effects.

## Verified in the frozen alpha candidate

- pathway registration and authorized state transitions;
- persistent pathway and execution-attempt stores;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and real MCP subprocess paths;
- HTTP and MCP fault injection;
- crash/restart continuity and duplicate-dispatch prevention;
- backup, restore, diagnostics, uninstall, package/CLI residue checks, and customer-data retention;
- clean wheel and source-distribution installation;
- two independent byte-for-byte reproducible builds;
- English-primary and Japanese-parallel product documentation;
- final RC audit with no retained findings for locally executable scope.

## We need field-test reports for

RPR is being published so real users can report reproducible environment and integration findings. Please open an Issue for:

- Windows, macOS, other Linux distributions, containers, and Python environments beyond the final Linux/Python 3.11 rehearsal;
- proxy, TLS, enterprise identity, credential handling, remote MCP, and service-specific connectivity;
- framework, agent, CI/CD, RPA, batch, and application integrations;
- installation, upgrade, backup/restore, removal, and operational usability;
- confusing states, missing examples, documentation gaps, and unsupported assumptions.

A user report is field evidence for that environment. It does not imply universal production readiness.

## Quick Start

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
rpr --help
```

Verify the received artifact before installation:

```text
responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
SHA-256 33f1f9255ee93b4f8be28abf3d547a038eea463e7d0965dada843d8724af3790
size 107214 bytes

responsibility_pathway_runtime-0.1.0a2.tar.gz
SHA-256 7a82e586d44954ed3c3ead0b7d89dba27cb3d308f0fe721cbe8b37d55e1541dd
size 129479 bytes
```

## Integration boundary

The host application remains responsible for authentication, credential isolation, network controls, bypass prevention, domain-specific authorization, and the independent readback source. RPE integration is optional; RPE absence, malformed output, or unsupported results must not become implicit permission.

## Documentation

- [Product, scope, and architecture](docs/en/product-scope-architecture.md)
- [Installation, operations, and recovery](docs/en/install-operations-recovery.md)
- [Security, limitations, integration, and API](docs/en/security-integration-api.md)
- [Verification, known issues, release notes, and UAT](docs/en/verification-release-uat.md)
- [Support and field testing](SUPPORT.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

RPR is released under the [MIT License](LICENSE). Copyright © 2026 Akihisa Ono.