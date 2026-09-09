<!--
Document Title: RPR Product Documentation
Document Type: Public Product Documentation Index
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Responsibility Pathway Runtime documentation

Responsibility Pathway Runtime (RPR) is an MIT-licensed runtime control and evidence component for governed external actions. The software is provided under the terms of the [MIT License](../../LICENSE), including its warranty and liability disclaimer.

The current published package is public-alpha `0.1.0a6`. Repository `main` may contain later source work that is not part of the published package until a later release passes exact-head validation and Human Gate.

[PyPI — 0.1.0a6](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a6/) · [GitHub Prerelease — v0.1.0a6](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a6) · [Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [Public repository](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

The documentation explains tested behavior and integration responsibilities; it does not create a warranty, certification, service commitment, or guarantee of fitness for a particular deployment.

## Start here

| Guide | Purpose |
|---|---|
| [Quick Start](quick-start.md) | Install the current PyPI public alpha and run a low-impact local rehearsal |
| [Product scope and architecture](product-scope-architecture.md) | Understand what RPR does, does not do, and where it sits |
| [Support and maturity](support-maturity.md) | See per-surface maturity and evidence boundaries |
| [Claim Boundary Promotion](claim-boundary-promotion.md) | Review evidence-limited and permanent responsibility boundaries |
| [MCP integration](mcp-integration.md) | Understand the current outbound MCP tool-call and read-only inspection boundaries |
| [Installation, operation, and recovery](install-operations-recovery.md) | Prepare, operate, stop, restore, and remove an integration |
| [Security, integration, and API boundary](security-integration-api.md) | Define trust boundaries and host-application obligations |
| [Verification, release notes, known issues, and UAT](verification-release-uat.md) | Review evidence, limitations, and a minimum acceptance plan |

Release-candidate, migration, and pre-public audit records are preserved separately under [`release-history/`](../../release-history/README.md). They are historical evidence, not current product guidance.

## Responsibility Routing boundary

Published `0.1.0a6` contains the additive Responsibility Routing model. Human Return remains valid as a bounded route, but generic fail-closed behavior is not synonymous with Human Gate.

The route model preserves receiver eligibility, delegation scope, unresolved payload, bounded next actions, closure/reevaluation conditions, and Residual Owner. Evidence transfer, receiver capability, successful transport, recovered state, or route selection do not create Authority.

A later package release still requires a fresh candidate, exact-head validation, claim/test/document parity, and an explicit release Human Gate.

## Current MCP boundary

The published RPR `0.1.0a6` line can govern outbound calls from a host application to an MCP server, including local subprocess/stdio transport, admitted server and tool bindings, fail-closed ambiguous outcomes, and optional independent readback. The published package also includes `rpr-mcp`, a local stdio read-only inspection server, the field-reproduced Windows UTF-8 BOM CLI compatibility repair, and read-only Responsibility Routing visibility.

Published `0.1.0a6` read-only tools are:

```text
rpr.get_status
rpr.list_pathways
rpr.get_pathway
rpr.get_evidence
rpr.list_unresolved
rpr.get_route_visibility
```

`rpr.get_route_visibility` is inspection-only and explicitly reports that Authority was not inferred.

## Product and integration boundary

| RPR provides | The integrator or operator provides |
|---|---|
| Pathway state and authorized transitions | Authentication and domain-specific authorization |
| Execution-attempt continuity | Credential isolation and network controls |
| Evidence attachment and readback workflow | An independent and authoritative readback source |
| Responsibility Routing metadata and bounded Human Gate / repair / resume / reconciliation states | Receiver eligibility, delegation source-of-truth, approval policy, bypass prevention, and operational ownership |
| Tested adapters and failure-state handling | Deployment suitability, monitoring, and final external action |

Current evidence includes Linux validation plus bounded Windows field evidence for the reproduced BOM-bearing input path. Results for other operating systems, Python versions, proxies, TLS arrangements, identity systems, credential stores, remote MCP services, and host frameworks require environment-specific testing.

A field report is evidence for the reported configuration only. It is not a general warranty, legal opinion, safety certification, or proof of exactly-once behavior across arbitrary remote systems.

## Support routes

| Topic | Route |
|---|---|
| Product and integration questions | [`SUPPORT.md`](../../SUPPORT.md) |
| Security reports | [`SECURITY.md`](../../SECURITY.md) |
| Contributions | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| License terms | [`LICENSE`](../../LICENSE) |
