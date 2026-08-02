<!--
Document Title: RPR Product Documentation
Document Type: Public Product Documentation Index
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Responsibility Pathway Runtime documentation

Responsibility Pathway Runtime (RPR) is an MIT-licensed runtime control and evidence component for governed external actions. The software is provided under the terms of the [MIT License](../../LICENSE), including its warranty and liability disclaimer.

The public repository, product site, and browser-hosted live demo are available now. A final tag, GitHub Release, and package-registry distribution have not yet been published.

[Product site](https://yutorikomeiji.github.io/responsibility-pathway-runtime/) · [Live browser demo](https://yutorikomeiji.github.io/responsibility-pathway-runtime/demo.html) · [Public repository](https://github.com/YutoriKomeiji/responsibility-pathway-runtime)

This documentation describes the verified public-alpha source `0.1.0a2`. It explains tested behavior and integration responsibilities; it does not create a warranty, certification, service commitment, or guarantee of fitness for a particular deployment.

## Start here

| Guide | Purpose |
|---|---|
| [Quick Start](quick-start.md) | Install from the public source and run a low-impact local rehearsal |
| [Product scope and architecture](product-scope-architecture.md) | Understand what RPR does, does not do, and where it sits |
| [Installation, operation, and recovery](install-operations-recovery.md) | Prepare, operate, stop, restore, and remove an integration |
| [Security, integration, and API boundary](security-integration-api.md) | Define trust boundaries and host-application obligations |
| [Verification, release notes, known issues, and UAT](verification-release-uat.md) | Review evidence, limitations, and a minimum acceptance plan |

## Product and integration boundary

| RPR provides | The integrator or operator provides |
|---|---|
| Pathway state and authorized transitions | Authentication and domain-specific authorization |
| Execution-attempt continuity | Credential isolation and network controls |
| Evidence attachment and readback workflow | An independent and authoritative readback source |
| Human Gate, repair, resume, and reconciliation states | Approval policy, bypass prevention, and operational ownership |
| Tested adapters and failure-state handling | Deployment suitability, monitoring, and final external action |

The frozen candidate was rehearsed on Linux with Python 3.11. Results for other operating systems, Python versions, proxies, TLS arrangements, identity systems, credential stores, remote MCP services, and host frameworks require environment-specific testing.

A field report is evidence for the reported configuration only. It is not a general warranty, legal opinion, safety certification, or proof of exactly-once behavior across arbitrary remote systems.

## Support routes

| Topic | Route |
|---|---|
| Product and integration questions | [`SUPPORT.md`](../../SUPPORT.md) |
| Security reports | [`SECURITY.md`](../../SECURITY.md) |
| Contributions | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |
| License terms | [`LICENSE`](../../LICENSE) |
