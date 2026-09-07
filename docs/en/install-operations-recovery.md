<!--
Document Title: RPR Installation Operations and Recovery
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Installation, operation, and recovery

This guide describes recommended integration practices for published `0.1.0a6` and the current repository source boundary. It is not a hosted service commitment, managed-operations agreement, or warranty. RPR is provided under the [MIT License](../../LICENSE).

## Deployment baseline

| Area | Integrator decision and evidence |
|---|---|
| Artifact | Verified wheel or source distribution, digest, source |
| Runtime | Python version, dependency resolution, isolated environment |
| Persistence | State-store location, access control, backup and retention |
| Authority | Permitted actions, authorized actors, delegation source-of-truth, configured bounded Human Gate owners |
| Responsibility Routing | Receiver eligibility, route scope, unresolved payload, allowed next actions, closure/reevaluation conditions, Residual Owner |
| Execution | Adapter allow-lists, timeout, cancellation, retry policy |
| Credentials | External secret source and least-privilege scope |
| Evidence | Independent readback source and matching rule |
| Recovery | Repair, reconciliation, resume, and incident owners |

Secrets must not be committed to repository files, examples, logs, pathway records, diagnostic bundles, or Issues.

## Operating sequence

| Order | Operation | Completion condition |
|---:|---|---|
| 1 | Validate action, actor, declared Authority, route eligibility, and integration configuration | Required declarations are present |
| 2 | Register or load the pathway | Persistent state is available |
| 3 | Check the requested transition and route | Current state, actor, and receiver conditions permit it |
| 4 | Create a durable execution attempt | Attempt identity is stored before dispatch |
| 5 | Dispatch through the bounded adapter | Dispatch evidence is retained |
| 6 | Obtain independent readback | External source is queried |
| 7 | Reconcile evidence | Required evidence matches or preserves the unresolved effect |
| 8 | Complete, repair, resume, hold, reconcile, or enter an explicitly configured bounded Human Gate | State and Responsibility Route remain coherent |

## Restart and ambiguous writes

| Situation | Required handling |
|---|---|
| Process restart | Load persistent pathways and attempts before new dispatch |
| Unresolved attempt | Do not silently redispatch |
| Possible write with unknown result | Retain `write_status_unknown` |
| Readback available | Query using stable operation identity and retain provenance |
| Readback unavailable or inconclusive | Preserve a reconciliation hold or another explicitly eligible and authorized Responsibility Route |
| Receiver eligibility or Authority unknown | Hold; do not invent a human receiver |

Retry is not a substitute for reconciliation. `Fail closed` is not synonymous with `Human Gate`.

Evidence transfer, receiver capability, successful transport, recovered state, or route selection do not create Authority.

## Backup and restore

Back up persistent state and associated evidence consistently. Test restoration in an isolated location. After restoration, run diagnostics, re-check route-relevant material state, and reconcile unresolved attempts before enabling external actions. Restoring state does not automatically restore approval or resume Authority.

## Removal and retained data

Uninstalling the Python package and deleting pathway data are separate operations.

| Item | Record before removal |
|---|---|
| Package | Installed version and uninstall result |
| State | Store and backup locations |
| Retention | Owner, period, and export format |
| Deletion | Approver, method, and verification evidence |

## Operational stop conditions

Stop external execution when configuration, Authority, receiver eligibility, credentials, persistence, readback, restore integrity, stable operation identity, or Residual Owner cannot be established. The integrator remains responsible for deciding whether and how the software may be used in its environment.
