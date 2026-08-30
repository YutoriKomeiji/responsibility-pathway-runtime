<!--
Language: English
Document-Type: Changelog
Status: Public Alpha
-->

# Changelog

All notable changes to Responsibility Pathway Runtime are recorded here.

## [0.1.0a5] - 2026-08-31

### Corrected

- `rpr check` now accepts both plain UTF-8 JSON and UTF-8 JSON with a byte-order mark by reading pathway input with `utf-8-sig`; this repairs a compatibility defect reproduced with PowerShell-generated JSON on Windows;
- public-export validation distinguishes published product status from staged next-release candidate state, preserving historical frozen artifact evidence instead of rewriting it merely to match a candidate package version.

### Added

- regression tests for plain UTF-8 and UTF-8 BOM CLI input;
- static-site release-synchronization regression coverage;
- English and Japanese evidence-driven claim-boundary promotion documentation;
- explicit candidate-state handling in `product-status.json` during pre-publication release preparation.

### Evidence

- the original Windows BOM failure was field-reproduced against public `0.1.0a4`;
- the repaired branch was rerun on Windows against the original BOM-bearing input and returned the expected `valid=true` / `decision=human_gate` result;
- final `0.1.0a5` release validation completed before publication;
- the GitHub `v0.1.0a5` prerelease was published;
- the PyPI publication workflow completed successfully and PyPI accepted both the `0.1.0a5` wheel and source distribution with `200 OK` responses through the Trusted Publisher path.

### Boundaries

- publication of `0.1.0a5` does not add a production-ready, enterprise-ready, legal/compliance certification, universal exactly-once, full-formal-verification, or customer-environment claim;
- later tags, GitHub Releases, and binary publication remain separately Human-Gated.

## [0.1.0a4] - 2026-08-04

### Corrected

- PyPI long-description source now identifies the current package instead of describing `0.1.0a2` as current;
- the local read-only `rpr-mcp` server is documented as included in the published package, not as an unreleased source preview;
- install commands, release links, package identity, and MCP `serverInfo.version` are aligned with `0.1.0a4`;
- release validation now treats rendered package metadata and stale predecessor-version wording as explicit release gates.

### Boundaries

- this correction does not add mutating MCP tools, remote MCP transport, production authorization, legal certification, EU-compliance claims, or enterprise-ready claims;
- publication of this alpha release does not imply production authorization, legal certification, EU-compliance, or enterprise readiness.

## [0.1.0a3] - 2026-08-04

### Added

- local stdio read-only RPR MCP inspection server targeting stable MCP protocol `2025-11-25`;
- `rpr-mcp` command-line entry point;
- read-only MCP inspection tools for runtime status, pathways, evidence, and unresolved records;
- MCP protocol-abuse, notification, malformed-input, and database-byte-invariance tests;
- optional EU AI Act Article 50 transparency profile with structured, fail-closed assessment outcomes;
- executable Article 50 sample, English and Japanese documentation, public API exports, and ten focused tests;
- ER-1 first-wave executable hardening and enterprise-readiness planning.

### Changed

- package identity advanced from `0.1.0a2` to `0.1.0a3`;
- MCP `serverInfo.version` was aligned with `0.1.0a3`;
- source preview and published-package claims were explicitly separated in release evidence, although the public README was not fully updated before publication.

### Boundaries

- ER-1 has started but is not complete;
- this is an alpha pre-release, not production authorization, an EU-compliance claim, or an enterprise-ready claim;
- mutating MCP tools, remote MCP transport, customer-equivalent environment validation, and jurisdiction-specific legal classification remain outside this release claim.

## [0.1.0a2] - 2026-07-30

Published alpha baseline before the local read-only RPR MCP inspection server was included in distribution artifacts.
