<!--
Document Title: RPR Installation Operations and Recovery
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Installation, operation, and recovery

## Installation

Install only a manifest-matching wheel or source distribution in an isolated environment. Retain the artifact, digest, Python version, dependency resolution output, and installation log as deployment evidence.

## Configuration baseline

Before enabling an adapter, record the state-store location, permitted action types, endpoint allow-list, subprocess command allow-list, timeouts, retry policy, credential source, readback source, backup destination, retention policy, and responsible human owner.

Secrets must not be committed to repository files, examples, logs, pathway records, or Issue reports.

## Operating sequence

1. Validate the proposed action, actor, authority, and integration configuration.
2. Register or load the pathway.
3. Confirm the current state permits the requested transition.
4. Create one durable execution attempt before dispatch.
5. Dispatch through the bounded adapter.
6. Obtain independent readback.
7. Mark completion only when the required evidence matches.
8. Otherwise retain the unresolved state and enter repair, resume, reconciliation, or Human Gate.

## Restart

On restart, load persistent pathways and attempts before permitting new dispatch. An unresolved attempt must not be silently repeated. Reconstruct its operation identity, dispatch evidence, last known state, readback result, and required next decision.

## Backup and restore

Back up the persistent state and associated evidence using a method that preserves consistency. Test restoration into an isolated location. After restore, run diagnostics and reconcile unresolved attempts before enabling external actions.

## Ambiguous write recovery

When an adapter may have written but the result cannot be established:

- retain `write_status_unknown`;
- disable automatic redispatch;
- query an independent source using stable operation identity;
- attach the result and provenance;
- reconcile to complete, failed, repair-required, or Human Gate;
- preserve the decision and evidence trail.

## Removal and customer data

Uninstalling the Python package must not silently delete customer pathway data. Document the state-store and backup locations, retention owner, export format, deletion approval, and verification method separately from package removal.

## Operational stop conditions

Stop external execution when configuration, authority, credentials, persistence, readback, restore integrity, or operation identity cannot be established. Do not use retry as a substitute for reconciliation.
