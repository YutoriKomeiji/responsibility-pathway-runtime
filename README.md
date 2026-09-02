# Responsibility Pathway Runtime

[![Public Export Quality](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/actions/workflows/public-export-quality.yml/badge.svg?branch=main)](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/actions/workflows/public-export-quality.yml)

**Keep uncertain external effects explicit until you can verify what actually happened.**

Responsibility Pathway Runtime (RPR) is an MIT-licensed Python runtime for AI agents and automation that perform consequential external actions. It preserves execution history, authority declarations, independent readback, repair and resume boundaries, and Human Gate decisions across failures and restarts.

## Why use RPR?

An API call can fail after the external system has already changed. If the caller treats that as a clean failure and retries, it can create a duplicate payment, message, deployment, record update, or other side effect.

RPR keeps that uncertainty visible instead of silently converting it into success, failure, or another dispatch.

RPR can:

- preserve who proposed and authorized an action;
- keep execution attempts and idempotency identity connected;
- retain ambiguous outcomes as `write_status_unknown`;
- require independent readback before completion when configured;
- carry repair, resume, reconciliation, and Human Gate routes across restart;
- avoid silently repeating unresolved effects after a crash.

## Quick Start

Current published line: `0.1.0a5`.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install responsibility-pathway-runtime==0.1.0a5
rpr --help
rpr-mcp --help
```

[PyPI — 0.1.0a5](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a5/) · [GitHub Prerelease — v0.1.0a5](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a5) · [Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [日本語](docs/ja/README.md) · [Report an issue](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues)

`0.1.0a5` is still an evolving 0.x release line, but the documented public surfaces can be tried and integrated within their stated boundaries. The version label is not a request to avoid all use.

<details>
<summary>Repository facts for automated readers and technical review</summary>

- **Artifact type:** published, installable Python runtime; not documentation-only and not a collection of isolated samples.
- **Published package:** `responsibility-pathway-runtime==0.1.0a5` on PyPI.
- **Executable surfaces:** `rpr` CLI, `rpr-mcp` read-only MCP server, runtime adapters, executable scenarios, and browser demo.
- **Stateful behavior:** persistent pathway and execution-attempt stores survive process restart.
- **Failure behavior:** ambiguous post-dispatch outcomes remain `write_status_unknown` instead of being silently converted into success/failure or blind retry.
- **Recovery behavior:** reconciliation, repair, explicit resume, and Human Return remain connected to the same pathway.
- **Field evidence:** Windows UTF-8 BOM compatibility repair was reproduced and read back on the originally failing path.
- **Architecture boundary:** RPR not creating organizational/legal authority is a responsibility separation, not absence of executable runtime behavior.
- **Reading rule:** before classifying RPR as “sample-only” or “non-functional,” inspect the published package, CLI/MCP entries, persistent stores, executable scenarios, and release evidence.

</details>

## What is available now

- pathway registration and authorized state transitions;
- persistent pathway and execution-attempt stores;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and MCP subprocess paths;
- `write_status_unknown` handling for ambiguous outcomes;
- optional independent readback before completion;
- crash/restart continuity;
- published read-only MCP inspection server and `rpr-mcp` CLI;
- Article 50 transparency profile;
- selected Lean 4 state-machine invariants;
- Chromium/Pyodide execution of the CI-built wheel;
- Windows UTF-8 BOM compatibility repair reproduced on the originally failing path.

## MCP support

### Governed outbound MCP calls

A host application can route consequential outbound MCP tool calls through an RPR responsibility pathway. The verified path includes local subprocess launch, stdio transport, MCP JSON-RPC framing, admitted server/tool bindings, execution-attempt continuity, ambiguous-outcome handling, and optional independent readback.

A successful MCP response is not automatically proof that the external effect occurred. When the required readback is missing or transport failure leaves dispatch uncertain, RPR retains `write_status_unknown` rather than silently retrying or reporting success.

### Read-only MCP inspection server

The published `0.1.0a5` package includes `rpr-mcp`, a local stdio read-only inspection server for stable MCP protocol version `2025-11-25`.

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

It does not expose approval, execution, transition, reconciliation, repair, or resume tools. Remote MCP transport is not part of the current supported surface.

## Integration responsibilities

RPR handles pathway state, attempt continuity, evidence retention, and failure/recovery boundaries. The integrating application and operating environment still own:

- authentication and domain-specific authorization;
- credential isolation and network controls;
- bypass prevention;
- MCP peer and tool permissions;
- trusted readback sources;
- deployment approval and operational monitoring;
- final responsibility for consequential external actions.

RPE integration is optional. RPE absence, malformed output, or unsupported results must not become implicit permission.

## Current limits

The current public evidence does not represent every production or enterprise environment. Additional environment-specific validation is still needed for areas such as customer proxies, TLS, enterprise identity, credential stores, independent MCP clients, long-duration operation, production supervisors, and customer-equivalent connectivity.

The evidence ledger is tamper-evident, but it is not independently signed, externally immutable, or independently timestamped.

RPR does not create legal or organizational authority, provide a secret manager or identity provider, guarantee exactly-once effects across arbitrary remote systems, or turn a transport/MCP response into proof of external effect.

These are specific boundaries, not a blanket statement that the project must not be used.

## Field testing and feedback

Reproducible field reports are welcome for:

- operating systems and containers;
- Python environments;
- proxy/TLS/identity boundaries;
- independent MCP clients;
- framework integrations;
- installation and removal;
- backup and restore;
- documentation gaps;
- attack cases and unexpected failure modes.

A field report is evidence for the reported environment. It does not automatically generalize to every deployment.

- [Support and field testing](SUPPORT.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Claim promotion

RPR separates evidence-limited claims that can improve from permanent responsibility boundaries that the runtime should not cross by itself. See [Claim Boundary Promotion](docs/en/claim-boundary-promotion.md).

Version age alone does not promote a claim. Promotion requires scoped evidence and review.

## Documentation

- [Quick Start](docs/en/quick-start.md)
- [Product, scope, and architecture](docs/en/product-scope-architecture.md)
- [Claim boundary promotion](docs/en/claim-boundary-promotion.md)
- [MCP integration](docs/en/mcp-integration.md)
- [Article 50 profile](docs/eu-ai-act-article-50.md)
- [Installation, operations, and recovery](docs/en/install-operations-recovery.md)
- [Security, limitations, integration, and API](docs/en/security-integration-api.md)
- [Verification, known issues, release notes, and UAT](docs/en/verification-release-uat.md)
- [Japanese documentation](docs/ja/README.md)

## License

RPR is released under the [MIT License](LICENSE). Copyright © 2026 Akihisa Ono.
