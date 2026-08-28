# Responsibility Pathway Runtime

**Govern external actions without losing evidence, recovery, or the human decision point.**

Responsibility Pathway Runtime (RPR) is an MIT-licensed Python runtime for applications that need to place an explicit responsibility pathway in front of consequential external actions. It preserves actor and authority declarations, execution-attempt continuity, readback evidence, fail-closed ambiguity handling, repair routes, and Human Gate decisions.

> **Public Alpha — 0.1.0a4**  
> Tag: `v0.1.0a4`  
> Correction scope: package-description and release-metadata alignment after `0.1.0a3`  
> RPR is not a legal-responsibility engine, identity provider, secret manager, production gateway, or guarantee of exactly-once effects across arbitrary remote systems.

[PyPI](https://pypi.org/project/responsibility-pathway-runtime/) · [GitHub Prerelease](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a4) · [Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [MCP integration](docs/en/mcp-integration.md) · [Article 50 profile](docs/eu-ai-act-article-50.md) · [日本語の入口](docs/ja/README.md) · [Quick Start](docs/en/quick-start.md) · [Report an issue](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues)

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

The published package includes two distinct MCP-related boundaries.

### Governed outbound MCP calls

A host application can route consequential outbound MCP tool calls through an RPR responsibility pathway. The verified path includes local subprocess launch, stdio transport, MCP JSON-RPC framing, admitted server and tool bindings, execution-attempt continuity, fail-closed ambiguous outcomes, and optional independent readback.

A successful MCP response is not automatically proof of a consequential external effect. When required readback is missing or transport failure leaves dispatch uncertain, RPR retains `write_status_unknown` rather than silently retrying or reporting success.

### Published read-only MCP inspection server

The package includes `rpr-mcp`, a local stdio read-only inspection server targeting stable MCP protocol version `2025-11-25`.

```bash
rpr-mcp --database ./rpr.sqlite3
```

It exposes only:

```text
rpr.get_status
rpr.list_pathways
rpr.get_pathway
rpr.get_evidence
rpr.list_unresolved
```

It has no approval, execution, transition, reconciliation, repair, or resume tool. The SQLite database is opened in read-only mode. Access is intended only for a trusted local MCP client that already has operating-system permission to read the database.

Support for mutating MCP tools, remote MCP transport, and later draft or release-candidate MCP protocol versions is not claimed.

## EU AI Act Article 50 transparency profile

RPR includes an optional Article 50 profile that records and evaluates integrator-declared disclosure, marking, labelling, editorial-review, and Human Gate evidence through structured fail-closed outcomes.

This profile does not provide legal classification, legal advice, certification, or a declaration of compliance with the EU AI Act. Jurisdiction-specific interpretation and deployment decisions remain with the responsible operator and legal advisers.

## Verified public-alpha scope

- pathway registration and authorized state transitions;
- persistent pathway and execution-attempt stores;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and real MCP subprocess paths;
- published read-only MCP inspection server and `rpr-mcp` CLI;
- MCP protocol-abuse, malformed-input, notification, subprocess, and database-byte-invariance tests;
- Article 50 profile, executable sample, public API exports, and focused tests;
- crash/restart continuity and duplicate-dispatch prevention;
- wheel and source-distribution build and clean-install checks;
- English-primary and Japanese-parallel documentation;
- selected Lean 4 state-machine invariants;
- Chromium and Pyodide execution of the CI-built wheel.

ER-1 hardening has started but is not complete. Customer proxy, TLS, identity, credentials, independent MCP clients, operating-system permission profiles, long-duration operation, production supervisors, and customer-equivalent connectivity remain external-environment validation items.

The evidence ledger is tamper-evident, but it is not independently signed, externally immutable, or independently timestamped. No production-ready or enterprise-ready claim is made.

## Claim boundary and promotion path

RPR does not treat every current non-claim as a permanent disclaimer. Public boundaries are separated into **evidence-limited boundaries that can move** and **permanent responsibility boundaries that RPR should not cross by itself**. See [Claim Boundary Promotion](docs/en/claim-boundary-promotion.md).

Current evidence-limited boundaries include production/enterprise readiness, customer-environment validation, broad exactly-once claims, independently anchored ledger integrity, and implementation-wide formal conformance. Each has an explicit evidence route: sustained workload and deployment evidence; reproducible customer-profile field evidence; target-side transaction/idempotency plus authoritative readback; signing/attestation or external immutability where claimed; and model-to-runtime conformance evidence, respectively.

These claims move only after scoped evidence is reviewed and explicitly admitted. Version age alone does not promote them.

Permanent responsibility boundaries remain even as RPR matures: the runtime does not create legal or organizational authority, make credentials/networks/external systems correct, treat a transport or MCP response as automatic proof of external effect, transfer final responsibility to software, promise universal exactly-once behavior for arbitrary remote systems without the required contract, or turn an abstract formal proof into automatic proof of the complete runtime/deployment.

Where practical, evidence-limited boundaries are tracked as `evidence_collecting`, `review_ready`, or `promoted`; permanent boundaries are `permanently_out_of_scope`.

## Quick Start

Install the public alpha in an isolated environment:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility-pathway-runtime==0.1.0a4
rpr --help
rpr-mcp --help
```

For development or source inspection:

```bash
git clone https://github.com/YutoriKomeiji/responsibility-pathway-runtime.git
cd responsibility-pathway-runtime
python -m pip install -e .
```

## Integration boundary

The host application remains responsible for authentication, credential isolation, network controls, bypass prevention, domain-specific authorization, MCP peer selection, tool permissions, trusted-client access to stored pathway data, and independent readback sources. RPE integration is optional; RPE absence, malformed output, or unsupported results must not become implicit permission.

## Field-test reports

Please report reproducible findings for operating systems, containers, Python environments, proxy/TLS/identity boundaries, independent MCP clients, framework integrations, installation and removal, backup and restore, and documentation gaps. A user report is evidence for that environment; it does not imply universal production readiness.

## Documentation

- [Product, scope, and architecture](docs/en/product-scope-architecture.md)
- [Claim boundary promotion](docs/en/claim-boundary-promotion.md)
- [MCP integration](docs/en/mcp-integration.md)
- [Article 50 profile](docs/eu-ai-act-article-50.md)
- [Installation, operations, and recovery](docs/en/install-operations-recovery.md)
- [Security, limitations, integration, and API](docs/en/security-integration-api.md)
- [Verification, known issues, release notes, and UAT](docs/en/verification-release-uat.md)
- [Support and field testing](SUPPORT.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

RPR is released under the [MIT License](LICENSE). Copyright © 2026 Akihisa Ono.
