<!--
Document Title: RPR Verification Release and UAT
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Verification, release notes, known issues, and UAT

## Release identity

- Version: `0.1.0a2`
- Channel: public alpha
- Freeze ID: `RPR-CF-2026-08-01-02`
- Canonical product commit recorded in `release-manifest.json`
- Final rehearsal profile: Linux and Python 3.11

## Verified locally executable scope

The frozen candidate retained evidence for pathway transitions, persistent state, execution-attempt continuity, Human Gate and repair routes, local file, allow-listed HTTP, durable outbound-message, MCP subprocess execution, fault injection, restart behavior, backup and restore, diagnostics, removal, package installation, and reproducible artifacts.

This statement is bounded to the frozen evidence set. It does not claim every environment, remote system, credential arrangement, framework, or operating condition was executed.

## Known limitations and non-claims

- Customer environments are not pre-verified.
- Windows, macOS, additional Linux distributions, containers, and Python profiles require field evidence.
- Enterprise proxy, TLS, identity, credentials, and remote MCP routes require integration-specific tests.
- Exactly-once effects are not guaranteed across arbitrary remote systems.
- RPR does not supply legal interpretation, production authorization, security certification, or universal deployment fitness.
- Alpha interfaces and migration behavior may change before a stable release.

## Minimum UAT plan

Use synthetic or non-consequential actions first.

1. Record environment, artifact digest, configuration, and responsible owner.
2. Confirm unauthorized transitions fail closed.
3. Confirm a required Human Gate cannot be bypassed.
4. Exercise one successful dispatch with independent readback.
5. Inject or simulate an ambiguous result and confirm no false completion.
6. Restart with an unresolved attempt and confirm no duplicate dispatch.
7. Exercise repair or reconciliation to a documented end state.
8. Back up and restore the state store in isolation.
9. Run diagnostics and verify secrets are absent from outputs.
10. Remove the package and confirm retained customer data follows the declared policy.

## Reporting result

A report should include expected and actual behavior, reproducible steps, sanitized logs, environment details, RPR version, Freeze ID, artifact digest, adapter type, readback source, and whether any real external effect occurred.

Classify the result as pass, fail, blocked, not applicable, or not executed. Do not convert blocked or not-executed scenarios into passing evidence.

## Release promotion gate

Public repository creation or update, tag creation, GitHub Release, binary upload, and publication occur only after the prepared export passes secret, internal-file, internal-link, license, manifest, digest, documentation, and claim/evidence audits and receives explicit human approval.
