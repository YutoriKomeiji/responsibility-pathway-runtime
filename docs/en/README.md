<!--
Document Title: RPR Product Documentation
Document Type: Public Product Documentation Index
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Responsibility Pathway Runtime documentation

RPR is a runtime control and evidence layer for governed external actions. This documentation describes the frozen public-alpha candidate `0.1.0a2` without claiming universal production readiness.

## Start here

1. [Quick Start](quick-start.md)
2. [Product scope and architecture](product-scope-architecture.md)
3. [Installation, operation, and recovery](install-operations-recovery.md)
4. [Security, integration, and API boundary](security-integration-api.md)
5. [Verification, release notes, known issues, and UAT](verification-release-uat.md)

## Evidence boundary

The frozen candidate was rehearsed on Linux with Python 3.11. Other operating systems, Python versions, proxies, TLS arrangements, enterprise identity systems, credential stores, remote MCP services, and host-framework integrations require environment-specific evidence.

A successful field report demonstrates only the reported configuration. It does not establish general production readiness, legal compliance, safety certification, or exactly-once behavior across arbitrary remote systems.

## Responsibility boundary

RPR can retain declarations, pathway state, execution attempts, readback evidence, repair and reconciliation state, and Human Gate decisions. The integrating application and its operators remain responsible for authentication, authorization, credential isolation, network controls, domain-specific policy, bypass prevention, independent readback, deployment approval, and final external action.

## Support routes

- Product and integration questions: see [`SUPPORT.md`](../../SUPPORT.md)
- Security reports: see [`SECURITY.md`](../../SECURITY.md)
- Contributions: see [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- Public issue forms: use the repository Issue tab after production promotion
