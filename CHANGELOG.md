<!--
Language: English
Document-Type: Changelog
Status: Candidate
-->

# Changelog

All notable changes to Responsibility Pathway Runtime are recorded here.

## [0.1.0a3] - Unreleased

### Added

- local stdio read-only RPR MCP inspection server targeting stable MCP protocol `2025-11-25`;
- `rpr-mcp` command-line entry point;
- read-only MCP inspection tools for runtime status, pathways, evidence, and unresolved records;
- MCP protocol-abuse, notification, malformed-input, and database-byte-invariance tests;
- optional EU AI Act Article 50 transparency profile with structured, fail-closed assessment outcomes;
- executable Article 50 sample, English and Japanese documentation, public API exports, and ten focused tests;
- ER-1 first-wave executable hardening and enterprise-readiness planning.

### Changed

- candidate package identity advanced from `0.1.0a2` to `0.1.0a3` so materially different distributions do not reuse the published version number;
- MCP `serverInfo.version` is aligned with candidate version `0.1.0a3`;
- source preview and published-package claims are explicitly separated.

### Boundaries

- ER-1 has started but is not complete;
- this is release-candidate preparation, not a PyPI publication, GitHub Release, production authorization, EU-compliance claim, or enterprise-ready claim;
- mutating MCP tools, remote MCP transport, customer-equivalent environment validation, jurisdiction-specific legal classification, and ER-1 completion remain outside this candidate claim;
- no Git tag, GitHub Release, or PyPI publication is authorized by this entry.

## [0.1.0a2] - 2026-07-30

Published alpha baseline before the local read-only RPR MCP inspection server was included in distribution artifacts.
