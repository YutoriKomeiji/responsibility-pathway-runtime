<!--
Document Title: RPR Verification Release and UAT
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Verification, release notes, known issues, and UAT

## Release identity

| Field | Value |
|---|---|
| Version | `0.1.0a2` |
| Channel | Public Alpha on PyPI and GitHub Prerelease |
| Tag | `v0.1.0a2` |
| Freeze ID | `RPR-CF-2026-08-02-01` |
| Product commit | Recorded in `release-manifest.json` |
| Final rehearsal profile | Linux / Python 3.11 |
| License | [MIT License](../../LICENSE) |

## What the retained evidence supports

The frozen evidence set covers pathway transitions, persistent state, execution-attempt continuity, Human Gate and repair routes, supported adapter paths, fault injection, restart behavior, backup and restore, diagnostics, removal, package installation, and reproducible artifacts.

For MCP, the retained verification covers the tested local subprocess and stdio path, JSON-RPC framing, admitted server/tool binding, fault injection, ambiguous-call preservation, restart continuity, and duplicate-dispatch prevention. It does not establish general compatibility with remote or hosted MCP services.

| Evidence statement | It does mean | It does not mean |
|---|---|---|
| A test passed | The recorded case passed in the recorded environment | Every environment or integration will pass |
| A build is reproducible | The tested build process produced matching artifacts | The artifact is free of all defects or vulnerabilities |
| A pathway completed | Required evidence matched for that case | The remote system provides universal exactly-once semantics |
| A local MCP test passed | The recorded subprocess/stdio case met its stated checks | Every MCP server, transport, tool, or remote service is compatible |
| A UAT report passed | The reported configuration met its stated checks | General production fitness or certification |

Verification documentation records observations and test results. It does not modify the MIT License or create a warranty, support obligation, certification, or legal assurance.

## Known limitations

| Area | Current boundary |
|---|---|
| Environments | Customer environments are not pre-verified |
| Platforms | Windows, macOS, additional Linux, containers, and other Python profiles need field evidence |
| MCP | Local subprocess/stdio is tested; remote MCP, hosted services, enterprise identity, and service-specific readback need integration-specific tests |
| Enterprise integration | Proxy, TLS, identity, credentials, and remote services require integration-specific tests |
| Remote effects | Exactly-once behavior is not guaranteed across arbitrary systems |
| Legal and security | RPR does not provide legal interpretation, authorization, or security certification |
| Compatibility | Alpha interfaces and migration behavior may change |
| MCP server role | RPR `0.1.0a2` does not expose its own pathway operations as MCP tools |

## Minimum UAT plan

Use synthetic or non-consequential actions first.

| Step | Acceptance check |
|---:|---|
| 1 | Record environment, artifact digest, configuration, and responsible owner |
| 2 | Unauthorized transitions fail closed |
| 3 | A required Human Gate cannot be bypassed |
| 4 | One dispatch completes with independent readback |
| 5 | An ambiguous result does not become false completion |
| 6 | Restart does not duplicate an unresolved dispatch |
| 7 | Repair or reconciliation reaches a documented end state |
| 8 | State backup and restore succeed in isolation |
| 9 | Diagnostic output contains no secrets |
| 10 | Package removal preserves or deletes data according to the declared policy |

For an MCP integration, also verify:

| Step | MCP acceptance check |
|---:|---|
| M1 | The expected protocol version, server identity, capabilities, tool name, and tool schema are bound before dispatch |
| M2 | A pre-dispatch rejection is distinguishable from an outcome that may have been sent |
| M3 | A transport timeout or uncertain result becomes `write_status_unknown` rather than an automatic retry |
| M4 | A consequential tool requires authoritative independent readback before completion |
| M5 | Restart restores the unresolved attempt without silently repeating `tools/call` |
| M6 | Remote or hosted MCP claims are limited to the exact environment that was tested |

## Reporting results

Report expected and actual behavior, reproduction steps, sanitized logs, environment, RPR version, Freeze ID, artifact digest, adapter, readback source, and whether a real external effect occurred.

For MCP, also report the transport, server implementation and version, protocol version, tool name, schema digest, authentication arrangement, and whether dispatch could be ruled out when a failure occurred.

Classify each result as `pass`, `fail`, `blocked`, `not applicable`, or `not executed`. Do not convert blocked or unexecuted cases into passing evidence.

## Release promotion gate

Repository visibility changes, tags, GitHub Releases, binary publication, and release declarations require the designated human approval after the prepared export passes the applicable secret, internal-reference, license, manifest, digest, documentation, and claim/evidence checks.
