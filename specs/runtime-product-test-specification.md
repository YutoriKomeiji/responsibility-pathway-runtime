# RPR Runtime Product Test Specification

Status: Draft / Active Test Basis
Version: 0.1
Owner: Akihisa Ono
Repository role: RPP development canonical source
Product target: Responsibility Pathway Runtime (RPR)
Release boundary: Private development only. This document does not authorize public release or a production-ready claim.

## 1. Purpose

This specification defines the tests required before RPR may be treated as a runtime product candidate rather than only a research implementation or component library.

The test suite MUST demonstrate not only that individual functions return expected values, but that the complete responsibility pathway remains coherent across authorization, execution, persistence, failure, restart, readback, reconciliation, repair, resume, evidence, and residual ownership.

A green unit-test suite alone is insufficient. Product readiness requires evidence across the layers defined in this document.

## 2. Product claims under test

RPR is intended to support the following bounded claims:

1. External actions are admitted only through declared pathway state and authority.
2. Human Gate and explicit approval prevent unauthorized dispatch.
3. Dispatch attempts are durably recorded without creating false evidence for actions that were never dispatched.
4. Completed or unresolved attempts are not silently re-dispatched.
5. Callback success is not treated as proof of external completion without readback.
6. Unknown external state remains unknown until verified.
7. Restart does not erase pathway, attempt, or evidence state.
8. Reconciliation updates the pathway and evidence consistently, not only the attempt ledger.
9. Repair and resume require declared authority.
10. Evidence remains ordered, hash-linked, inspectable, and redacted according to policy.
11. JSON, Python, and Lean 4 representations agree on the selected canonical transition model.
12. Built artifacts can be installed and exercised in a clean environment.

The suite MUST NOT be presented as proof of legal compliance, full system safety, complete formal verification, production identity assurance, distributed-system correctness, or external-provider delivery guarantees.

## 3. System under test

The product test boundary includes:

- `ResponsibilityPathwayRuntime`;
- `SQLiteStore`;
- `SQLiteExecutionAttemptLedger`;
- state transition and authority enforcement;
- RPE adapters and contract handling;
- executors supplied with RPR;
- readback and reconciliation;
- evidence generation, redaction, persistence, and verification;
- repair, resume, stop, abort, and residual-owner transitions;
- CLI and package installation surfaces;
- canonical JSON model, generated Python transition table, and selected Lean 4 model.

External identity providers, distributed databases, cloud gateways, hosted tool interception, and third-party delivery systems are outside the current product test boundary unless represented by explicit test doubles or bounded adapters.

## 4. Test principles

### 4.1 Fail closed

Missing authority, unavailable RPE, contract mismatch, unsupported state, invalid evidence, and ambiguous execution outcome MUST NOT become implicit allow or completed states.

### 4.2 No false dispatch evidence

A request rejected before the executor is called MUST NOT leave a durable attempt that implies possible external mutation.

### 4.3 No unverified completion

A successful executor return without verified readback MUST NOT move the pathway to `completed`.

### 4.4 Unknown remains unknown

Timeout, disconnect, crash, or incomplete persistence after possible dispatch MUST result in an explicit unresolved state until reconciliation establishes otherwise.

### 4.5 Replay is authorized

Replay safety MUST NOT bypass pathway access or actor authorization. Preventing duplicate dispatch does not authorize arbitrary actors to read prior results or append replay events.

### 4.6 State, attempt, and evidence coherence

Any operation that classifies or repairs an attempt MUST leave the pathway state, attempt record, and evidence trail mutually consistent.

### 4.7 Real restart testing

Restart tests MUST close the original runtime and database connections, instantiate new objects, reopen persisted stores, and continue from durable state. Calling the same object twice is not a restart test.

### 4.8 Deterministic acceptance

Every required test MUST have explicit preconditions, operation, expected state, expected durable records, expected evidence, and forbidden outcomes.

## 5. Test levels

- **L1 Unit**: pure validation, transition, authority, fingerprint, and serialization behavior.
- **L2 Component**: SQLite store, attempt ledger, evidence chain, executor, RPE adapter.
- **L3 Runtime integration**: runtime with real stores and bounded executors.
- **L4 Product E2E**: RPE decision through approval, dispatch, readback, persistence, restart, and closure.
- **L5 Release verification**: build, clean install, CLI, parity, Lean build, audit, and RC rehearsal.

A Public Alpha candidate MUST pass all required L1-L5 tests. Tests marked `Future Production` are not release blockers for the current private-alpha hardening cycle but define the production gap.

## 6. Required test catalogue

### A. Registration and admission

#### RPR-ADM-001 Valid low-risk registration

Given a valid pathway and explicit development evaluator returning `allow`, registration MUST persist the pathway and produce the expected initial state.

#### RPR-ADM-002 Approval-required registration

A pathway with approval authority MUST start at `awaiting_approval` even when RPE returns `allow`.

#### RPR-ADM-003 Missing approval authority

An action class requiring approval but lacking an approval authority MUST fail closed to `human_gate` or a stricter state and MUST expose the reason code.

#### RPR-ADM-004 RPE unavailable

Unavailable RPE MUST result in `human_gate`; no implicit development allow is permitted.

#### RPR-ADM-005 RPE contract mismatch

Unsupported decision values, malformed payloads, or incompatible contract versions MUST fail closed and record a bounded reason.

#### RPR-ADM-006 Registration replay

Reusing the same registration idempotency key with the identical pathway MUST replay the persisted state without duplicate registration evidence.

#### RPR-ADM-007 Registration conflict

Reusing a registration idempotency key with different pathway data MUST raise a conflict and MUST NOT alter the original pathway.

### B. Authority and Human Gate

#### RPR-AUT-001 Approval authority

Only the declared approval authority may transition `awaiting_approval` to `approved`.

#### RPR-AUT-002 Execution authority

Only the execution actor may begin execution from `approved`.

#### RPR-AUT-003 Stop authority

Only the declared stop authority may enter stop, hold, or human-gate states where required.

#### RPR-AUT-004 Repair authority

Only the repair owner may classify repair and mark readiness to resume where specified.

#### RPR-AUT-005 Resume authority

Only the declared resume authority or explicitly permitted actor may restart from a resumable state.

#### RPR-AUT-006 Residual-owner abort

Only the residual owner may perform an abort transition requiring residual-impact acceptance.

#### RPR-AUT-007 Replay authorization

An actor lacking access or execution authority MUST NOT retrieve a completed replay result, observe unresolved-attempt details, or append replay evidence through `execute()`.

#### RPR-AUT-008 Principal binding

Authenticated principal resolution and actor binding MUST reject issuer, subject, or binding mismatches.

### C. Pre-dispatch durability

#### RPR-PRE-001 Invalid state rejection

Calling `execute()` in a non-executable state MUST call the executor zero times and leave no started attempt.

#### RPR-PRE-002 Unauthorized actor rejection

Calling `execute()` as an unauthorized actor MUST call the executor zero times, preserve the pathway state, and leave no started attempt.

#### RPR-PRE-003 Missing pathway

Calling `execute()` for an unknown pathway MUST not retain a started attempt.

#### RPR-PRE-004 Safe discard scope

Pre-dispatch cleanup MUST match pathway ID, attempt ID, idempotency key, and request fingerprint, or otherwise be proven internal and unambiguous.

#### RPR-PRE-005 Finished attempt retention

Cleanup MUST NOT delete a finished, classified, or reconciled attempt.

### D. Dispatch and readback

#### RPR-EXE-001 Successful verified execution

A permitted executor action with verified readback MUST move `approved -> running -> completed`, persist the attempt result, and append valid evidence.

#### RPR-EXE-002 Success without readback

An executor status of success without verified readback MUST NOT complete the pathway. The outcome MUST become unknown or repair-required according to the declared contract.

#### RPR-EXE-003 Verified readback mismatch

A readback mismatch MUST NOT complete the pathway and MUST preserve diagnostic evidence.

#### RPR-EXE-004 Executor-declared failure

A declared failure MUST move the pathway to `repair_required` through the correct authority route and persist the result.

#### RPR-EXE-005 Executor exception

An exception after dispatch begins MUST be treated as `write_status_unknown`, not automatically failed or retried.

#### RPR-EXE-006 Unsupported executor action

An unsupported action MUST be classified deterministically and MUST NOT be reported as completed.

#### RPR-EXE-007 File confinement

The local file executor MUST reject root escape, root-as-target, and invalid path forms.

#### RPR-EXE-008 File precondition

A stale expected hash MUST fail without modifying the target.

#### RPR-EXE-009 Allow-listed HTTP boundary

HTTP execution MUST reject non-allow-listed destinations, unsupported schemes, redirect escape, or otherwise out-of-contract targets.

### E. Idempotency and replay

#### RPR-IDM-001 Completed replay

Repeating an identical completed request MUST return the persisted result and call the executor zero additional times.

#### RPR-IDM-002 Unresolved replay

Repeating a started attempt with no result MUST return `write_status_unknown` and MUST NOT re-dispatch.

#### RPR-IDM-003 Attempt-ID conflict

Reusing an attempt ID with different execution data MUST raise a conflict.

#### RPR-IDM-004 Idempotency-key conflict

Reusing a pathway-scoped execution idempotency key with different execution data MUST raise a conflict.

#### RPR-IDM-005 Replay after pathway closure

Replay behavior after `completed`, `aborted`, or other terminal state MUST be explicitly defined and authorized.

#### RPR-IDM-006 Concurrent begin

Two database connections attempting the same request concurrently MUST produce one durable attempt and one replay, without duplicate dispatch authorization.

### F. Crash and restart matrix

Each crash test MUST use durable pathway and attempt databases and a newly constructed runtime after the simulated crash.

#### RPR-CRS-001 Crash before attempt insert

No attempt and no external action may exist after restart.

#### RPR-CRS-002 Crash after attempt insert, before state transition

The attempt MUST be distinguishable as pre-dispatch or safely removable; it MUST NOT become false external uncertainty.

#### RPR-CRS-003 Crash after `running`, before executor call

The product MUST provide a deterministic recovery rule that does not assume dispatch occurred.

#### RPR-CRS-004 Crash during executor call

After restart, the pathway MUST remain unresolved and must not re-dispatch automatically.

#### RPR-CRS-005 Crash after external effect, before executor return

The pathway MUST remain unresolved until independent readback or reconciliation.

#### RPR-CRS-006 Crash after executor result, before attempt finish

The attempt MUST replay as unresolved; no duplicate dispatch is allowed.

#### RPR-CRS-007 Crash after attempt finish, before pathway transition

Restart MUST detect and repair the mismatch between durable attempt result and pathway state.

#### RPR-CRS-008 Crash after pathway transition, before evidence append

State and evidence MUST be atomic or the inconsistency MUST be detected and repairable.

#### RPR-CRS-009 Crash after evidence append

Restart MUST preserve the final state and a valid evidence chain.

#### RPR-CRS-010 Repeated restart

Multiple restarts during unresolved handling MUST not weaken uncertainty or trigger duplicate dispatch.

### G. Reconciliation

#### RPR-REC-001 Verified applied

Independent observation that proves the effect was applied MUST persist a succeeded attempt result, transition the pathway to the contractually correct state, and append reconciliation evidence.

#### RPR-REC-002 Verified not applied

Independent observation that proves no effect occurred MUST preserve evidence and transition to a safe retry, repair, or aborted state according to policy. It MUST NOT retry automatically unless explicitly authorized.

#### RPR-REC-003 Unresolved observation

Insufficient observation MUST leave both attempt and pathway unresolved.

#### RPR-REC-004 Reconciliation authorization

Only a declared reconciliation, repair, or evidence authority may reconcile an attempt.

#### RPR-REC-005 Reconciliation replay

Repeating the same reconciliation MUST be idempotent and MUST NOT duplicate pathway transitions or evidence.

#### RPR-REC-006 Attempt/pathway coherence

After reconciliation, the attempt result, pathway state, and latest evidence event MUST describe the same classification.

#### RPR-REC-007 No mutation redispatch

A reconciliation strategy MUST observe only and MUST not reissue the original external mutation.

### H. Repair, compensation, resume, and residual ownership

#### RPR-RPR-001 Failed execution enters repair

A failed result MUST identify the repair owner and required next action.

#### RPR-RPR-002 Repair completion

Repair evidence MUST be persisted before entering `ready_to_resume`.

#### RPR-RPR-003 Unauthorized resume

An unauthorized actor MUST not resume a stopped or repaired pathway.

#### RPR-RPR-004 Authorized resume

An authorized resume MUST create a new execution attempt identity while preserving linkage to the prior attempt and repair evidence.

#### RPR-RPR-005 Compensation is explicit

Compensation MUST never be inferred solely from a failed operation. The compensating action, authority, and evidence requirements MUST be declared.

#### RPR-RPR-006 Partial completion

Partial completion MUST preserve completed effects, unresolved effects, and residual owner without collapsing to generic failure.

#### RPR-RPR-007 Residual closure

A terminal closure with non-reversible impact MUST retain the residual owner and closure reason.

### I. Persistence and concurrency

#### RPR-PER-001 Pathway restart persistence

A new runtime using the same SQLite pathway database MUST recover the exact pathway definition and state.

#### RPR-PER-002 Attempt restart persistence

A new ledger using the same SQLite attempt database MUST recover result, status, and fingerprint.

#### RPR-PER-003 Evidence restart persistence

A new runtime MUST recover all evidence in sequence and verify the chain.

#### RPR-PER-004 Atomic state and evidence

A state transition and its evidence event MUST commit atomically.

#### RPR-PER-005 Concurrent state transition

Two connections attempting conflicting transitions MUST allow one and reject the stale transition.

#### RPR-PER-006 Concurrent attempt completion

Competing finishes of the same attempt MUST not silently overwrite incompatible results.

#### RPR-PER-007 Busy and retry behavior

SQLite busy handling MUST fail predictably within bounded time and MUST not corrupt state.

#### RPR-PER-008 Schema forward safety

A database with a newer schema version MUST be rejected without modification.

#### RPR-PER-009 Migration repeatability

Running migrations repeatedly MUST be safe and deterministic.

### J. Evidence and inspection

#### RPR-EVD-001 Hash-chain validity

All normal transitions MUST produce a valid ordered chain.

#### RPR-EVD-002 Tamper detection

Modified, removed, reordered, or substituted evidence MUST fail verification.

#### RPR-EVD-003 Redaction

Configured sensitive fields MUST not appear in persisted evidence.

#### RPR-EVD-004 Operational sufficiency

Evidence MUST include pathway, actor, event type, relevant operation and attempt identifiers, state classification, reason, and readback or reconciliation summary where applicable.

#### RPR-EVD-005 No secret leakage

Credentials, authorization headers, raw secrets, and prohibited payload fields MUST not be persisted or emitted by diagnostics.

#### RPR-EVD-006 Inspection coherence

Inspection output MUST reflect the durable state and identify missing next authority or unresolved conditions.

### K. RPE integration

#### RPR-RPE-001 Python adapter allow

A valid `allow` response MUST be normalized without copying RPE semantics into RPR.

#### RPR-RPE-002 Restrictive combination

Combining local inspection and RPE decisions MUST select the more restrictive outcome.

#### RPR-RPE-003 Adapter exception

Python or REST adapter failure MUST fail closed to Human Gate.

#### RPR-RPE-004 Contract version

Expected version mismatch MUST be visible and fail closed.

#### RPR-RPE-005 Reason preservation

RPE reason codes and bounded raw metadata MUST be available in registration evidence without leaking prohibited data.

#### RPR-RPE-006 Pack lifecycle boundary

When governance eligibility is connected, suspended, expired, ownerless, ambiguous, or incompatible packs MUST prevent execution.

### L. State-model and formal parity

#### RPR-FRM-001 JSON/Python state parity

All canonical states and transitions in JSON MUST match generated Python values.

#### RPR-FRM-002 Python/Lean state parity

Selected canonical states and transitions represented in Lean 4 MUST match Python.

#### RPR-FRM-003 Generated artifact freshness

CI MUST fail when generated transition files are stale relative to the canonical model.

#### RPR-FRM-004 Selected invariants

Lean build MUST machine-check the selected invariants claimed by the project.

#### RPR-FRM-005 Claim boundary

Documentation and release audit MUST state that Lean checks selected model invariants, not the entire Python runtime, external world, legal compliance, or full system safety.

### M. Package, CLI, and clean-environment operation

#### RPR-PKG-001 Unit and integration suite

The full required pytest suite MUST pass on supported Python versions.

#### RPR-PKG-002 Build artifacts

Wheel and source distribution MUST build without untracked source dependencies.

#### RPR-PKG-003 Clean install

The wheel MUST install into a fresh virtual environment.

#### RPR-PKG-004 Import

`import rpr` MUST succeed after clean installation.

#### RPR-PKG-005 CLI help

`rpr --help` MUST succeed after clean installation.

#### RPR-PKG-006 Minimal product scenario

A documented quick-start scenario MUST run using only installed package contents.

#### RPR-PKG-007 Artifact contents

The wheel and sdist MUST contain required runtime, generated model, schemas, notices, and documentation, and MUST exclude development-only residue.

#### RPR-PKG-008 Residue scan

No legacy `rpy` package name, incubator-only path, stale repository URL, or unintended private path may remain in exported product artifacts.

#### RPR-PKG-009 Release audit

Automated release audit MUST validate metadata, license, version, URLs, claims, file set, and clean installation.

#### RPR-PKG-010 RC rehearsal

A release-candidate rehearsal MUST produce reproducible evidence without publishing to a public registry.

### N. Security and misuse resistance

#### RPR-SEC-001 Invalid input boundaries

Empty identifiers, malformed paths, unsupported states, and invalid enum values MUST be rejected.

#### RPR-SEC-002 Path traversal

File operations MUST not escape their configured root through relative paths, symlinks, or normalization tricks.

#### RPR-SEC-003 HTTP target validation

Host, scheme, port, redirects, and DNS or resolution assumptions MUST be bounded and documented.

#### RPR-SEC-004 Evidence injection

Untrusted payload content MUST not forge event structure, actor identity, hashes, or reason codes.

#### RPR-SEC-005 Resource bounds

Oversized evidence, payload, or response handling MUST have defined behavior.

#### RPR-SEC-006 Database corruption

Corrupt or structurally incompatible storage MUST fail safely without silently resetting governance state.

#### RPR-SEC-007 Development bypass visibility

Development-only evaluators or bypasses MUST be explicit, opt-in, and visibly identified in evidence and documentation.

### O. Operational diagnostics

#### RPR-OPS-001 Actionable exception

Operator-visible failures MUST identify the pathway, operation or attempt where safe, failure class, and next safe action.

#### RPR-OPS-002 Unknown-state diagnostics

Unknown status MUST expose why it is unknown, what may have happened, what must not be retried, and how to reconcile.

#### RPR-OPS-003 Human Gate context

Human Gate output MUST provide the decision needed, applicable authority, evidence available, and safe continuation options.

#### RPR-OPS-004 Repair context

Repair-required output MUST identify the repair owner, failed condition, and resume prerequisites.

#### RPR-OPS-005 Inspection after restart

Operators MUST be able to inspect a restarted pathway without mutating it.

## 7. Product E2E scenarios

The following named E2E scenarios are mandatory and MUST be separately identifiable in CI.

### E2E-01 Governed reversible file change

RPE allow -> awaiting approval -> authorized approval -> execution -> atomic file replacement -> SHA-256 readback -> completed -> valid evidence -> restart readback.

### E2E-02 Human Gate blocks external action

RPE unavailable or restrictive decision -> Human Gate -> attempted execution rejected -> executor zero calls -> no attempt poison -> diagnostic next action.

### E2E-03 Unknown after possible dispatch

Authorized execution -> executor loses connection after possible mutation -> unknown persisted -> restart -> no redispatch -> independent observation -> reconciled state and evidence.

### E2E-04 Verified not applied

Possible dispatch -> unknown -> independent readback proves no effect -> no automatic retry -> explicit authorized retry or closure path.

### E2E-05 Failure, repair, and resume

Execution failure -> repair required -> repair evidence -> authorized ready-to-resume -> new attempt -> verified completion -> prior history preserved.

### E2E-06 Concurrent duplicate request

Two runtime instances submit the same request concurrently -> one dispatch maximum -> one durable outcome -> authorized replay for the other caller.

### E2E-07 Crash boundary sweep

Inject a crash at every boundary listed in section F and verify the documented recovery classification after constructing a new runtime.

### E2E-08 RPE contract failure

Malformed or incompatible RPE response -> Human Gate -> no executor call -> bounded evidence and diagnostic.

## 8. Acceptance evidence

Every required CI run MUST retain or report:

- commit SHA;
- Python version and platform;
- test count and result;
- failed test IDs, if any;
- build artifact names and SHA-256 values;
- clean-install result;
- CLI result;
- JSON/Python/Lean parity result;
- Lean build result;
- release-audit result;
- RC rehearsal result;
- known skips with justification.

A test is not considered passed solely because the workflow job is green if the relevant step was skipped, marked continue-on-error, or did not execute the specified product boundary.

## 9. Severity and release rules

- **Blocker**: duplicate external effect, unauthorized execution or replay, false completion, loss of unknown state, corrupt evidence, unsafe implicit allow, or unrecoverable persistence inconsistency.
- **Critical**: restart failure, attempt/pathway divergence, broken Human Gate, failed idempotency conflict detection, or package that cannot clean-install.
- **Major**: incomplete diagnostics, bounded executor defect, missing negative test, or documentation that overstates verified scope.
- **Minor**: non-safety usability or presentation defect.

Public Alpha export is prohibited while any Blocker or Critical test is failing or missing.

## 10. Current implementation gaps identified before execution

The following items are known required fixes at the time of this specification:

1. Replay result access and replay-event creation occur before actor authorization in `ResponsibilityPathwayRuntime.execute()`.
2. Reconciliation currently classifies the attempt ledger without atomically updating pathway state and runtime evidence.
3. Existing product E2E tests do not reopen both pathway and attempt databases in a new runtime instance.
4. Crash after attempt result persistence but before pathway transition is not yet repaired automatically.
5. Pre-dispatch cleanup should be bound more tightly than attempt ID alone or proven unreachable outside the internal admission path.
6. Concurrent multi-connection execution admission needs explicit testing.

These gaps MUST be addressed or explicitly deferred with residual owner and product-claim restriction before the test specification can be marked fulfilled.

## 11. Execution order

Tests and implementation work SHALL proceed in this order:

1. authorization before replay access;
2. scoped pre-dispatch cleanup;
3. runtime-integrated reconciliation;
4. real restart persistence tests;
5. crash matrix;
6. concurrency and idempotency tests;
7. repair/resume E2E;
8. evidence and diagnostics tests;
9. full package and formal verification;
10. clean-export rehearsal.

## 12. Completion decision

This specification is fulfilled only when:

- every required test ID has an implementation or an approved explicit deferral;
- all Blocker and Critical tests pass;
- failures produce preserved evidence rather than false completion;
- the required CI evidence is available;
- the product claim boundary is updated to match actual verification;
- the Human Gate approves any export, public visibility change, or release.

Until then, RPR remains a private productization candidate developed within RPP.
