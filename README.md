# Responsibility Pathway Runtime

**Govern external actions without losing evidence, recovery, or the human decision point.**

Responsibility Pathway Runtime (RPR) is an MIT-licensed Python runtime for applications that need to place an explicit responsibility pathway in front of consequential external actions. It helps a host application preserve actor and authority declarations, execution-attempt continuity, readback evidence, fail-closed ambiguity handling, repair routes, and Human Gate decisions.

> **Public Alpha — 0.1.0a2**  
> Tag: `v0.1.0a2`  
> Freeze ID: `RPR-CF-2026-08-02-01`  
> Tested final rehearsal profile: Linux, Python 3.11  
> The source repository, product site, browser demo, GitHub Prerelease, and PyPI package are public.  
> RPR is not a legal-responsibility engine, identity provider, secret manager, production gateway, or guarantee of exactly-once effects across arbitrary remote systems.

[PyPI](https://pypi.org/project/responsibility-pathway-runtime/) · [GitHub Prerelease](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a2) · [Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [MCP integration](docs/en/mcp-integration.md) · [日本語の入口](docs/ja/README.md) · [Quick Start](docs/en/quick-start.md) · [Product documentation](docs/en/README.md) · [Report an issue](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues)

## Why RPR

AI agents and automation can execute faster than people can reconstruct what happened. RPR provides a bounded runtime layer where an integrating application can:

- declare actors, authority, and the proposed action;
- evaluate and retain an explicit pathway state;
- bind operations, attempts, and idempotency identity;
- require independent readback before completion;
- stop ambiguous writes as `write_status_unknown` instead of false success;
- retain Human Gate, repair, resume, reconciliation, and evidence continuity;
- survive restart without silently repeating unresolved effects.

## Current MCP support

RPR `0.1.0a2` can govern outbound MCP tool calls made by a host application. The verified public-alpha path includes local subprocess launch, stdio transport, MCP JSON-RPC framing, admitted server and tool bindings, execution-attempt continuity, fail-closed ambiguous outcomes, and optional independent readback.

```text
host application or agent
  -> proposed MCP tool call
  -> actor, authority, Human Gate, and pathway state
  -> admitted MCP server and tool binding
  -> tools/call
  -> tool result
  -> independent readback when required
  -> completed | write_status_unknown | repair | reconcile | human gate
```

A successful MCP response is not automatically proof of a consequential external effect. When required readback is missing or a transport failure leaves dispatch uncertain, RPR keeps the pathway as `write_status_unknown` rather than silently retrying or reporting success.

> **Boundary:** RPR currently governs calls to an MCP server. It is not yet distributed as an MCP server exposing RPR pathway operations as MCP tools. Remote MCP services and customer-specific transports require environment-specific evaluation.

See the [MCP integration guide](docs/en/mcp-integration.md) or the [Japanese guide](docs/ja/mcp-integration.md).

## Verified in the public alpha

- pathway registration and authorized state transitions;
- persistent pathway and execution-attempt stores;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and real MCP subprocess paths;
- MCP server/tool admission binding, stdio execution, fault injection, and ambiguous-call handling;
- HTTP fault injection;
- crash/restart continuity and duplicate-dispatch prevention;
- backup, restore, diagnostics, uninstall, package/CLI residue checks, and customer-data retention;
- wheel and source-distribution build and installation checks;
- GitHub Actions OIDC Trusted Publishing to PyPI;
- English-primary and Japanese-parallel product documentation;
- Lean 4 verification of selected published state-machine invariants;
- Chromium and Pyodide execution of the CI-built RPR wheel in the public browser demo.

## We need field-test reports for

RPR is public so real users can report reproducible environment and integration findings. Please open an Issue for:

- Windows, macOS, other Linux distributions, containers, and Python environments beyond the final Linux/Python 3.11 rehearsal;
- proxy, TLS, enterprise identity, credential handling, remote MCP, and service-specific connectivity;
- framework, agent, CI/CD, RPA, batch, and application integrations;
- installation, upgrade, backup/restore, removal, and operational usability;
- confusing states, missing examples, documentation gaps, and unsupported assumptions.

A user report is field evidence for that environment. It does not imply universal production readiness.

## Quick Start

Install the Public Alpha from PyPI in an isolated, disposable environment:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility-pathway-runtime==0.1.0a2
rpr --help
```

For development or source inspection, clone the public repository and use an editable install:

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
python -m pip install -e .
```

To inspect the runtime without installing it locally, use the [live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html). The demo runs the CI-built RPR wheel in Pyodide with SQLite; only the external payment provider is simulated.

The pre-release verification hashes remain recorded in [`release-evidence/replacement-freeze-2026-08-02.json`](release-evidence/replacement-freeze-2026-08-02.json). They are evidence for the frozen candidate that preceded the PyPI publication, not a substitute for reading the published package metadata and release state.

## Integration boundary

The host application remains responsible for authentication, credential isolation, network controls, bypass prevention, domain-specific authorization, MCP server selection, tool permissions, and the independent readback source. RPE integration is optional; RPE absence, malformed output, or unsupported results must not become implicit permission.

## Documentation

- [Product, scope, and architecture](docs/en/product-scope-architecture.md)
- [MCP integration](docs/en/mcp-integration.md)
- [Installation, operations, and recovery](docs/en/install-operations-recovery.md)
- [Security, limitations, integration, and API](docs/en/security-integration-api.md)
- [Verification, known issues, release notes, and UAT](docs/en/verification-release-uat.md)
- [Support and field testing](SUPPORT.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

RPR is released under the [MIT License](LICENSE). Copyright © 2026 Akihisa Ono.
