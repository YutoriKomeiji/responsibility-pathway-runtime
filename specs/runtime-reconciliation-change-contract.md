# RPR Runtime-Integrated Reconciliation Change Contract

Status: Draft / Implementation Basis
Owner: Akihisa Ono
Repository role: RPP development environment
Release boundary: Private development only

## 1. Purpose

This contract defines the required semantics before the standalone attempt-ledger reconciliation helper may be integrated into `ResponsibilityPathwayRuntime`.

Reconciliation MUST update the execution attempt, pathway state, and evidence trail coherently. Updating only the attempt ledger is insufficient.

## 2. Preconditions

Runtime reconciliation MUST require all of the following:

- the pathway exists;
- the pathway is in `write_status_unknown`;
- the persisted attempt exists and has no classified result;
- the request identity and fingerprint match the persisted attempt;
- the caller has declared reconciliation authority;
- the strategy performs observation only and does not redispatch the mutation.

Until a dedicated field is added, reconciliation authority is bounded to the declared `repair_owner` or `evidence_owner`. The acting identity MUST be recorded as supplied; the runtime MUST NOT substitute the execution actor.

## 3. Result mapping

### 3.1 Verified applied

A verified observation that proves the external effect was applied MUST:

- classify the attempt as `succeeded` with verified readback;
- transition the pathway from `write_status_unknown` to `completed`;
- append reconciliation evidence containing the observation, actor, attempt identity, and reason;
- perform no external mutation dispatch.

The canonical transition model MUST explicitly permit this transition. Authority rules MUST explicitly permit the reconciliation authority for this transition only when the current state is `write_status_unknown` and the transition is produced through the reconciliation API.

### 3.2 Verified not applied

A verified observation that proves the effect was not applied MUST:

- classify the attempt as `failed` with verified observation evidence;
- transition the pathway from `write_status_unknown` to `repair_required`;
- append reconciliation evidence;
- identify the repair owner;
- perform no automatic retry or redispatch.

### 3.3 Unresolved

An insufficient observation MUST:

- preserve the attempt as unresolved;
- preserve the pathway as `write_status_unknown`;
- append bounded observation evidence;
- perform no mutation dispatch.

The attempt ledger MUST NOT be finalized with a `write_status_unknown` result merely because one observation was inconclusive; repeated authorized observations must remain possible.

## 4. Atomicity and crash behavior

The implementation MUST define and test the crash boundaries between:

1. observation completion;
2. attempt classification;
3. pathway transition;
4. evidence append.

A crash MUST NOT leave a classified attempt with an unrelated pathway state without a deterministic detection and repair route.

Where a single database transaction is not currently possible across the pathway store and attempt ledger, the runtime MUST persist enough reconciliation identity and phase information to detect and repair an interrupted reconciliation. A green happy-path test alone is insufficient.

## 5. Required tests

The implementation increment MUST include at minimum:

- `RPR-REC-001` verified applied closes attempt, pathway, and evidence coherently;
- `RPR-REC-002` verified not applied enters repair without redispatch;
- `RPR-REC-003` unresolved observation preserves unknown state and permits later observation;
- `RPR-REC-004` unauthorized actor cannot observe or classify the attempt;
- `RPR-REC-005` repeated identical reconciliation is idempotent;
- `RPR-REC-006` attempt, pathway, and latest evidence describe the same classification;
- `RPR-REC-007` reconciliation strategy never invokes the mutation executor;
- restart test using durable pathway and attempt stores;
- crash test after attempt classification but before pathway transition;
- JSON/Python/Lean parity after canonical transition changes.

## 6. Non-claims

This change does not prove that an external observer is truthful, complete, fresh, or legally authoritative. It proves only that RPR processes a bounded observation through declared authority and maintains internal state/evidence coherence within the tested runtime and storage boundary.

## 7. Implementation order

1. Add reconciliation-specific authority enforcement.
2. Amend the canonical transition model.
3. Regenerate Python transition data and update the Lean model.
4. Add runtime reconciliation API without removing the standalone helper yet.
5. Add component and runtime tests.
6. Add restart and interruption-repair tests.
7. Deprecate direct product use of ledger-only reconciliation after runtime integration is verified.
