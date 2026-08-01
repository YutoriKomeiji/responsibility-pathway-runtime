<!--
Document Title: RPR Security Integration and API Boundary
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Security, integration, and API boundary

## Security model

RPR is a control and evidence component, not a complete security perimeter. Deploy it inside a host architecture that supplies authenticated users and services, least-privilege credentials, network policy, endpoint allow-lists, protected persistence, log redaction, software-supply-chain controls, and operational monitoring.

## Trust boundaries

Treat these as separate trust domains:

- the human or institutional authority;
- the host application;
- RPR state and evidence stores;
- adapter processes;
- credentials and secret stores;
- remote systems;
- independent readback sources;
- optional RPE decision services.

A result from one domain must not be silently substituted for evidence owned by another. In particular, adapter return values are not automatically independent readback.

## Integration contract

Each integration must define:

- accepted action and actor schemas;
- authority and Human Gate requirements;
- stable operation and idempotency identity;
- permitted state transitions;
- dispatch timeout and cancellation behavior;
- authoritative readback source and matching rules;
- ambiguous-write handling;
- repair, resume, and reconciliation ownership;
- data classification, retention, and deletion rules;
- observability and incident routes.

## API stability

The `0.1.0a2` surface is public alpha. Integrators should pin the version and validate serialized state, CLI behavior, adapter configuration, and migration procedures before upgrading. Alpha releases may make incompatible corrections when required to preserve safety or evidence semantics.

## Credentials

RPR documentation and examples must use placeholders. Credentials must be supplied through an external secret mechanism and scoped to the smallest permitted operation set. Never place secrets in pathway evidence, exception messages, diagnostic bundles, public Issues, or release artifacts.

## Bypass prevention

A host application must not expose a second execution path that skips the pathway controls for the same consequential operation. Tests should demonstrate that direct adapter invocation, alternate endpoints, debug modes, and restart paths cannot silently bypass required admission and evidence handling.

## Vulnerability reporting

Do not disclose exploitable security details in a public Issue. Follow the private reporting route in [`SECURITY.md`](../../SECURITY.md).
