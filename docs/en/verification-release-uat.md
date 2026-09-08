<!--
Document Title: RPR Verification Release and UAT
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Verification, release notes, known issues, and UAT

## Release identity

| Field | Value |
|---|---|
| Version | `0.1.0a6` |
| Channel | Public Alpha on PyPI and GitHub Prerelease |
| Tag | `v0.1.0a6` |
| Release commit | `9f71a34f5d7eb0e25359ccf31d0c6d85570203d8` |
| Publish workflow | `34087946734` — success |
| Final rehearsal profile | Linux / Python 3.11, plus bounded Windows field evidence for the BOM repair |
| License | [MIT License](../../LICENSE) |

Repository source may contain later work. That work is not promoted to a package release merely by existing on `main`; a later release requires a fresh candidate, exact-head validation, and explicit Human Gate approval.

## What the retained `0.1.0a6` evidence supports

The published evidence set covers pathway transitions, persistent state, execution-attempt continuity, configured Human Gate and repair routes, Responsibility Routing, supported adapter paths, fault injection, restart behavior, backup and restore, diagnostics, removal, package installation, and reproducible artifacts.

For MCP, retained verification covers tested local subprocess and stdio paths, JSON-RPC framing, admitted server/tool binding, read-only MCP inspection, read-only route visibility, fault injection, ambiguous-call preservation, restart continuity, and duplicate-dispatch prevention. It does not establish general compatibility with remote or hosted MCP services.

| Evidence statement | It does mean | It does not mean |
|---|---|---|
| A test passed | The recorded case passed in the recorded environment | Every environment or integration will pass |
| A build is reproducible | The tested build process produced matching artifacts | The artifact is free of all defects or vulnerabilities |
| A pathway completed | Required evidence matched for that case | The remote system provides universal exactly-once semantics |
| A local MCP test passed | The recorded subprocess/stdio case met its stated checks | Every MCP server, transport, tool, or remote service is compatible |
| A UAT report passed | The reported configuration met its stated checks | General production fitness or certification |

Verification documentation records observations and test results. It does not modify the MIT License or create a warranty, support obligation, certification, or legal assurance.

## Responsibility Routing verification included in `0.1.0a6`

Release-level routing evidence includes:

- route serialization and legacy compatibility;
- receiver eligibility validation;
- no false human escalation from generic fail-closed conditions;
- `REQUIRES_REEVALUATION` hold behavior;
- Authority non-propagation through evidence, capability, route selection, or transport success;
- Residual Owner preservation;
- persistence/runtime-recreation route visibility;
- ambiguous-write -> `hold_for_reconciliation` visibility;
- reconciliation without duplicate dispatch;
- read-only MCP route visibility with `authority_inferred: false`;
- English and Japanese browser/demo assertions;
- claim/test registry binding and exact-head CI.

The release candidate passed the complete standalone suite with 477 tests, production-grade demo tests, clean wheel installation and CLI checks, Lean/JSON/Python parity checks, reproducible artifact verification, and EN/JA browser/Pyodide E2E before publication.

## Published artifact evidence

| Artifact | SHA256 |
|---|---|
| `responsibility_pathway_runtime-0.1.0a6-py3-none-any.whl` | `3db42d6d1289e2a1f1a20afc8d181a7bc433dcbb8e7ea87416415192a6ca6cb2` |
| `responsibility_pathway_runtime-0.1.0a6.tar.gz` | `0690b9ea23831ea5dc24578accecb68fccc7a0737bbf71facdd09be629f0874f` |

PyPI accepted both artifacts through Trusted Publishing, and public readback confirmed the `0.1.0a6` page and file metadata. Digital attestations were generated during publication.

## Known limitations

| Area | Current boundary |
|---|---|
| Environments | Customer environments are not pre-verified |
| Platforms | Windows beyond the bounded field case, macOS, additional Linux, containers, and other Python profiles need field evidence |
| MCP | Local subprocess/stdio, local read-only inspection, and read-only route visibility are tested; remote MCP, hosted services, enterprise identity, and service-specific readback need integration-specific tests |
| Responsibility Routing | Bounded route metadata/visibility is published; receiver eligibility and organizational delegation source-of-truth remain integrator-owned |
| Enterprise integration | Proxy, TLS, identity, credentials, and remote services require integration-specific tests |
| Remote effects | Exactly-once behavior is not guaranteed across arbitrary systems |
| Legal and security | RPR does not provide legal interpretation, create organizational Authority, or provide security certification |
| Formal evidence | Lean checks selected state-transition invariants; it does not formally prove receiver eligibility or Responsibility Routing delegation semantics |
| Compatibility | Alpha interfaces and migration behavior may change |
| MCP server role | Published `0.1.0a6` includes read-only `rpr-mcp` and `rpr.get_route_visibility`; it exposes no mutating pathway operations. |

## Minimum UAT plan

Use synthetic or non-consequential actions first.

| Step | Acceptance check |
|---:|---|
| 1 | Record environment, artifact digest, configuration, and responsible owner |
| 2 | Unauthorized transitions fail closed |
| 3 | A required configured Human Gate cannot be bypassed |
| 4 | Generic evaluator/route failure does not invent a human destination |
| 5 | Receiver eligibility and delegation scope are explicit for any Responsibility Route used |
| 6 | One dispatch completes with independent readback |
| 7 | An ambiguous result does not become false completion |
| 8 | Restart does not duplicate an unresolved dispatch |
| 9 | `write_status_unknown` exposes reconciliation hold without inferring Authority |
| 10 | Repair or reconciliation reaches a documented end state while preserving Residual Owner |
| 11 | State backup and restore succeed in isolation and route-relevant material state is reevaluated |
| 12 | Diagnostic output contains no secrets |
| 13 | Package removal preserves or deletes data according to the declared policy |

For an MCP integration, also verify:

| Step | MCP acceptance check |
|---:|---|
| M1 | The expected protocol version, server identity, capabilities, tool name, and tool schema are bound before dispatch |
| M2 | A pre-dispatch rejection is distinguishable from an outcome that may have been sent |
| M3 | A transport timeout or uncertain result becomes `write_status_unknown` rather than an automatic retry |
| M4 | A consequential tool requires authoritative independent readback before completion |
| M5 | Restart restores the unresolved attempt without silently repeating `tools/call` |
| M6 | Read-only route visibility cannot approve, execute, reconcile, resume, or grant Authority |
| M7 | Remote or hosted MCP claims are limited to the exact environment that was tested |

## Reporting results

Report expected and actual behavior, reproduction steps, sanitized logs, environment, RPR version, release/tag identity, artifact digest, adapter, readback source, route classification/receiver eligibility when relevant, and whether a real external effect occurred.

For MCP, also report the transport, server implementation and version, protocol version, tool name, schema digest, authentication arrangement, and whether dispatch could be ruled out when a failure occurred.

Classify each result as `pass`, `fail`, `blocked`, `not applicable`, or `not executed`. Do not convert blocked or unexecuted cases into passing evidence.

## Release promotion gate

Tags, GitHub Releases, binary publication, claim promotion, and release declarations require designated human approval after the exact candidate head passes applicable source, unit, component, integration, system/E2E, persistence/restart, package-install, formal-scope, secret/internal-reference, bilingual documentation, manifest/digest, and claim/evidence checks.

If a frozen candidate changes after validation, rebuild a fresh candidate from repaired `main` rather than carrying old evidence forward.
