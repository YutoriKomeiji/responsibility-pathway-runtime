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

This guide describes recommended integration practices. It is not a hosted service commitment, managed-operations agreement, or warranty. RPR is provided under the [MIT License](../../LICENSE).

## Deployment baseline

| Area | Integrator decision and evidence |
|---|---|
| Artifact | Verified wheel or source distribution, digest, source |
| Runtime | Python version, dependency resolution, isolated environment |
| Persistence | State-store location, access control, backup and retention |
| Authority | Permitted actions, authorized actors, Human Gate owners |
| Execution | Adapter allow-lists, timeout, cancellation, retry policy |
| Credentials | External secret source and least-privilege scope |
| Evidence | Independent readback source and matching rule |
| Recovery | Repair, reconciliation, resume, and incident owners |

Secrets must not be committed to repository files, examples, logs, pathway records, diagnostic bundles, or Issues.

## Operating sequence

| Order | Operation | Completion condition |
|---:|---|---|
| 1 | Validate action, actor, authority, and integration configuration | Required declarations are present |
| 2 | Register or load the pathway | Persistent state is available |
| 3 | Check the requested transition | Current state and actor permit it |
| 4 | Create a durable execution attempt | Attempt identity is stored before dispatch |
| 5 | Dispatch through the bounded adapter | Dispatch evidence is retained |
| 6 | Obtain independent readback | External source is queried |
| 7 | Reconcile evidence | Required evidence matches the expected effect |
| 8 | Complete or stop | Enter completed, repair, resume, reconciliation, or Human Gate |

## Restart and ambiguous writes

| Situation | Required handling |
|---|---|
| Process restart | Load persistent pathways and attempts before new dispatch |
| Unresolved attempt | Do not silently redispatch |
| Possible write with unknown result | Retain `write_status_unknown` |
| Readback available | Query using stable operation identity and retain provenance |
| Readback unavailable or inconclusive | Stop and route to reconciliation or Human Gate |

Retry is not a substitute for reconciliation.

## Backup and restore

Back up persistent state and associated evidence consistently. Test restoration in an isolated location. After restoration, run diagnostics and reconcile unresolved attempts before enabling external actions.

## Removal and retained data

Uninstalling the Python package and deleting pathway data are separate operations.

| Item | Record before removal |
|---|---|
| Package | Installed version and uninstall result |
| State | Store and backup locations |
| Retention | Owner, period, and export format |
| Deletion | Approver, method, and verification evidence |

## Operational stop conditions

Stop external execution when configuration, authority, credentials, persistence, readback, restore integrity, or stable operation identity cannot be established. The integrator remains responsible for deciding whether and how the software may be used in its environment.
