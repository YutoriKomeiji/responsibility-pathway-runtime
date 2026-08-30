<!--
Document Title: RPR Product Documentation
Document Type: Public Product Documentation Index
Status: Public Alpha
Version: split-state: GitHub 0.1.0a5 / PyPI 0.1.0a4
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Responsibility Pathway Runtime documentation

Responsibility Pathway Runtime (RPR) is an MIT-licensed runtime control and evidence component for governed external actions. The software is provided under the terms of the [MIT License](../../LICENSE), including its warranty and liability disclaimer.

Current distribution state is temporarily split: GitHub prerelease/source is `0.1.0a5`, while the independently read-back PyPI package remains `0.1.0a4`. Do not treat PyPI `0.1.0a5` as public until its publication is directly verified.

[PyPI — 0.1.0a4 current](https://pypi.org/project/responsibility-pathway-runtime/0.1.0a4/) · [GitHub Prerelease — v0.1.0a5](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/releases/tag/v0.1.0a5) · [Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [Public repository](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

The documentation tracks the current public source and verified distribution state separately. It explains tested behavior and integration responsibilities; it does not create a warranty, certification, service commitment, or guarantee of fitness for a particular deployment.

## Start here

| Guide | Purpose |
|---|---|
| [Quick Start](quick-start.md) | Install the currently verified PyPI version and run a low-impact local rehearsal |
| [Product scope and architecture](product-scope-architecture.md) | Understand what RPR does, does not do, and where it sits |
| [Claim Boundary Promotion](claim-boundary-promotion.md) | Review evidence-limited and permanent responsibility boundaries |
| [MCP integration](mcp-integration.md) | Understand the current outbound MCP tool-call and read-only inspection boundaries |
| [Installation, operation, and recovery](install-operations-recovery.md) | Prepare, operate, stop, restore, and remove an integration |
| [Security, integration, and API boundary](security-integration-api.md) | Define trust boundaries and host-application obligations |
| [Verification, release notes, known issues, and UAT](verification-release-uat.md) | Review evidence, limitations, and a minimum acceptance plan |

## Current MCP boundary

The current RPR public line can govern outbound calls from a host application to an MCP server, including local subprocess/stdio transport, admitted server and tool bindings, fail-closed ambiguous outcomes, and optional independent readback. The published PyPI `0.1.0a4` package also includes `rpr-mcp`, a local stdio read-only inspection server. The GitHub `v0.1.0a5` prerelease retains these boundaries and adds the field-reproduced Windows UTF-8 BOM CLI compatibility repair; that repair is not yet a PyPI `0.1.0a5` distribution claim until PyPI readback succeeds.

## Product and integration boundary

| RPR provides | The integrator or operator provides |
|---|---|
| Pathway state and authorized transitions | Authentication and domain-specific authorization |
| Execution-attempt continuity | Credential isolation and network controls |
| Evidence attachment and readback workflow | An independent and authoritative readback source |
| Human Gate, repair, resume, and reconciliation states | Approval policy, bypass prevention, and operational ownership |
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
