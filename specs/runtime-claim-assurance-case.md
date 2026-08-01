# RPR Runtime Claim Assurance Case

Status: Draft / Active Assurance Basis
Version: 0.1
Owner: Akihisa Ono
Repository role: RPP development canonical source
Product target: Responsibility Pathway Runtime (RPR)
Release boundary: Private development only. This document does not authorize public release or a production-ready claim.

## 1. Purpose

This document defines how each bounded RPR product claim is technically justified.

The runtime product test specification defines what must be tested. This assurance case defines why the selected mechanisms, tests, and retained evidence are relevant to each claim, which assumptions they depend on, and which residual risks remain.

A claim is not accepted merely because a test with a similar name passes. Acceptance requires a traceable chain:

```text
bounded product claim
  -> threat or counterexample
  -> technical mechanism
  -> trusted assumptions
  -> implementation surface
  -> falsification-oriented tests
  -> retained evidence
  -> residual-risk statement
```

## 2. Assurance method

Each claim entry uses the following fields.

- **Claim**: the exact bounded statement RPR may make.
- **Threat / counterexample**: the failure that would falsify the claim.
- **Mechanism**: the runtime design intended to prevent or detect the failure.
- **Implementation anchor**: the source modules or generated artifacts carrying the mechanism.
- **Trusted assumptions**: properties outside the mechanism that the claim depends on.
- **Verification strategy**: unit, component, integration, E2E, formal, package, or adversarial checks.
- **Required evidence**: durable artifacts needed to substantiate the result.
- **Residual risk**: what remains unproven or outside the boundary.
- **Permitted wording**: the strongest externally usable wording after the required evidence passes.

## 3. Global assurance rules

### 3.1 Falsification before confirmation

Every safety-relevant claim MUST include at least one negative or adversarial test capable of falsifying the claim. A happy-path test alone is insufficient.

### 3.2 Mechanism diversity

Where practical, a claim SHOULD be supported by more than one evidence type, such as:

- executable tests;
- persistent-state inspection;
- event-chain verification;
- generated-model parity;
- selected Lean 4 invariants;
- clean-install execution;
- source and artifact residue audit.

Multiple tests that exercise the same code path are not independent evidence.

### 3.3 Assumptions are part of the claim

SQLite transaction semantics, filesystem atomic replacement behavior, trusted principal resolution, executor contracts, and external readback quality MUST be stated rather than silently treated as proven by RPR.

### 3.4 Evidence must identify the tested build

Evidence MUST bind to the commit SHA, package version, workflow run, Python and OS versions, test IDs, and artifact hashes.

### 3.5 Claim weakening on missing evidence

If required evidence is unavailable, skipped, stale, or produced by a narrower boundary than the claim, the claim MUST be weakened rather than inferred.

## 4. Claim assurance matrix

### CLM-01 Declared state and authority govern dispatch

**Claim**

External actions are admitted only through a declared executable pathway state and declared authority.

**Threat / counterexample**

- execution from `human_gate`, `held`, `denied`, `completed`, or an unknown pathway;
- execution by an actor other than the declared execution or resume authority;
- replay access leaking prior results or appending events before authorization;
- a development evaluator acting as an implicit allow fallback.

**Mechanism**

- canonical state-transition table;
- `ensure_transition()` transition rejection;
- `authorize_transition()` actor-role comparison;
- fail-closed initial-state selection;
- replay authorization before result access;
- explicit, opt-in development evaluator.

**Implementation anchors**

- `src/rpr/runtime.py`;
- `src/rpr/state_machine.py`;
- `src/rpr/authority.py`;
- `src/rpr/inspection.py`;
- `src/rpr/rpe.py`;
- canonical transition JSON and generated Python table.

**Trusted assumptions**

- actor strings or bound principals accurately represent authenticated identities at the integration boundary;
- the runtime is the enforced path to the executor;
- callers cannot invoke the underlying external mutation outside RPR and still attribute it to RPR.

**Verification strategy**

- `RPR-AUT-001` through `RPR-AUT-008`;
- `RPR-PRE-001` through `RPR-PRE-003`;
- `RPR-ADM-003` through `RPR-ADM-005`;
- negative replay tests with unauthorized actors;
- JSON/Python/Lean transition parity.

**Required evidence**

- zero executor calls on every rejected path;
- unchanged durable pathway state;
- no retained pre-dispatch attempt;
- no unauthorized replay event;
- reason code and required authority in diagnostics;
- CI log bound to commit SHA.

**Residual risk**

RPR does not itself prove production identity, secure token issuance, endpoint exclusivity, or absence of side-channel execution paths.

**Permitted wording**

"Within the configured RPR boundary, declared state and actor authority are enforced before dispatch and replay-result access."

### CLM-02 Human Gate prevents unauthorized external action

**Claim**

Human Gate and explicit approval prevent dispatch until the declared human authority authorizes continuation.

**Threat / counterexample**

- RPE returns `allow` and bypasses configured approval;
- missing approval authority becomes implicit approval;
- unauthorized actor approves;
- executor is called while state remains `awaiting_approval` or `human_gate`.

**Mechanism**

- distinction between RPE decision and pathway approval state;
- `_initial_state()` producing `awaiting_approval` when approval is configured;
- explicit `awaiting_approval -> approved` transition;
- approval-authority enforcement;
- executor admission limited to `approved` or authorized resume state.

**Implementation anchors**

- `src/rpr/runtime.py`;
- `src/rpr/authority.py`;
- `src/rpr/inspection.py`;
- canonical transitions.

**Trusted assumptions**

- approval credentials are resolved and bound correctly by the host system;
- approval is not fabricated outside the trusted principal resolver.

**Verification strategy**

- `RPR-ADM-002`, `RPR-ADM-003`;
- `RPR-AUT-001`, `RPR-AUT-002`;
- `E2E-01`, `E2E-02`;
- adversarial approval with wrong actor, missing authority, and stale state.

**Required evidence**

- persisted `awaiting_approval` or `human_gate` state;
- executor call count zero before approval;
- evidence event identifying approving actor and reason;
- successful dispatch only after authorized transition.

**Residual risk**

The semantic quality of the human decision and organizational legitimacy of the approver are outside the runtime proof boundary.

**Permitted wording**

"RPR enforces an explicit approval transition and prevents configured external dispatch before authorized approval."

### CLM-03 Durable attempts do not create false dispatch uncertainty

**Claim**

Dispatch attempts are durably recorded without leaving false evidence that an external action may have occurred when rejection happened before executor invocation.

**Threat / counterexample**

- attempt row inserted before state or actor validation and retained after rejection;
- cleanup removes another request's attempt;
- cleanup deletes a finished or actually dispatched attempt;
- crash between insert and dispatch makes pre-dispatch and post-dispatch uncertainty indistinguishable.

**Mechanism**

- transactional attempt insertion;
- scoped pre-dispatch cleanup;
- status and result predicates restricting deletion;
- pathway, attempt, idempotency, and request-fingerprint binding;
- explicit dispatch-phase classification or equivalent recoverable marker.

**Implementation anchors**

- `src/rpr/attempts.py`;
- `src/rpr/runtime.py`;
- execution request fingerprinting.

**Trusted assumptions**

- SQLite transaction and uniqueness semantics hold;
- no external effect occurs before the executor call boundary;
- request fingerprint canonicalization is stable for supported parameter types.

**Verification strategy**

- `RPR-PRE-001` through `RPR-PRE-005`;
- `RPR-CRS-001` through `RPR-CRS-003`;
- multi-connection negative tests;
- mutation test that deliberately removes the cleanup predicate and must fail.

**Required evidence**

- absence of an attempt row after rejected pre-dispatch calls;
- retained row after simulated actual dispatch uncertainty;
- conflict errors for mismatched identifiers or fingerprints;
- SQLite contents captured after each crash point.

**Residual risk**

Without an explicit persisted dispatch-phase marker, some crash boundaries may remain conservatively unresolved and require claim restriction.

**Permitted wording**

"RPR distinguishes rejected pre-dispatch calls from persisted possible-dispatch uncertainty within the tested SQLite execution boundary."

### CLM-04 Completed and unresolved attempts are not silently re-dispatched

**Claim**

Identical completed or unresolved attempts are replayed from durable state and are not automatically sent again.

**Threat / counterexample**

- process restart loses the attempt and repeats the mutation;
- same idempotency key with different payload is accepted;
- concurrent runtimes both dispatch;
- unauthorized actor obtains replay data;
- terminal pathway state causes an implicit new execution.

**Mechanism**

- unique attempt ID and pathway-scoped idempotency key;
- request fingerprint comparison;
- `started` versus persisted result distinction;
- replay return before executor invocation, but only after authorization;
- transactional concurrent `begin()` behavior.

**Implementation anchors**

- `src/rpr/attempts.py`;
- `src/rpr/runtime.py`.

**Trusted assumptions**

- all retries reuse stable operation, attempt, and idempotency identifiers according to the documented contract;
- SQLite is shared by competing runtime instances in the tested deployment mode.

**Verification strategy**

- `RPR-IDM-001` through `RPR-IDM-006`;
- `RPR-CRS-004` through `RPR-CRS-010`;
- `E2E-03`, `E2E-06`, `E2E-07`;
- executor spy proving call count remains one.

**Required evidence**

- executor call count;
- persisted attempt row and fingerprint;
- conflict exception for changed request data;
- independent runtime restart logs;
- concurrency trace showing one dispatch maximum.

**Residual risk**

Provider-side behavior may still duplicate an effect if the provider ignores the supplied idempotency contract or the executor violates RPR's dispatch boundary.

**Permitted wording**

"RPR prevents automatic duplicate dispatch for identical persisted attempts within the tested runtime and storage boundary."

### CLM-05 Completion requires verified readback

**Claim**

Executor return or callback success is not treated as proof of external completion without verified readback.

**Threat / counterexample**

- executor reports success before remote commit;
- response is lost after effect;
- readback observes the wrong resource or stale state;
- mismatch is collapsed to completed;
- provider callback is forged or semantically weaker than the claimed effect.

**Mechanism**

- separate `ExecutionStatus` and `ReadbackEvidence`;
- completion transition only when status is succeeded and readback is present and verified;
- unknown or repair-required state otherwise;
- executor-specific expected-versus-observed comparison.

**Implementation anchors**

- `src/rpr/executor.py`;
- `src/rpr/runtime.py`;
- supplied executor readback implementations.

**Trusted assumptions**

- readback source is sufficiently independent and authoritative for the specific effect;
- expected and observed identifiers refer to the same target;
- filesystem and provider read APIs reflect committed state within the documented consistency model.

**Verification strategy**

- `RPR-EXE-001` through `RPR-EXE-005`;
- deliberate success-without-readback;
- deliberate hash or resource mismatch;
- stale and forged readback fixtures;
- `E2E-01`, `E2E-03`.

**Required evidence**

- expected and observed values;
- readback source and reason;
- pathway state after callback-only success;
- no `completed` evidence until readback verification.

**Residual risk**

Readback proves only the selected observable property at the selected time; it does not prove all downstream consequences, legal validity, or permanent delivery.

**Permitted wording**

"RPR requires configured verified readback before marking the tested external effect completed."

### CLM-06 Unknown remains unknown until independent classification

**Claim**

Timeout, disconnect, crash, or incomplete persistence after possible dispatch remains explicitly unresolved until reconciliation establishes a bounded classification.

**Threat / counterexample**

- unknown becomes failed and is retried automatically;
- unknown becomes completed based only on callback inference;
- restart drops the unresolved state;
- repeated restart weakens uncertainty;
- reconciliation mutates the external system instead of observing it.

**Mechanism**

- explicit `write_status_unknown` state and execution status;
- no transition from unknown directly to completed without reconciliation path;
- durable attempt and pathway persistence;
- observation-only reconciliation strategy;
- idempotent reconciliation result persistence.

**Implementation anchors**

- `src/rpr/models.py`;
- canonical transitions;
- `src/rpr/reconciliation.py`;
- `src/rpr/runtime.py`;
- persistence stores.

**Trusted assumptions**

- reconciliation observer does not reissue the mutation;
- observer evidence is authoritative enough for its classification;
- host system does not bypass RPR and retry independently.

**Verification strategy**

- `RPR-IDM-002`;
- `RPR-CRS-004` through `RPR-CRS-010`;
- `RPR-REC-001` through `RPR-REC-007`;
- `E2E-03`, `E2E-04`, `E2E-07`.

**Required evidence**

- persisted unresolved attempt and pathway state across a new runtime;
- zero redispatch calls;
- observer call trace distinct from executor call trace;
- reconciliation event and resulting state;
- repeated reconciliation produces no duplicate event.

**Residual risk**

Some external systems may not expose sufficient independent evidence; in that case the correct outcome remains unresolved or requires human repair.

**Permitted wording**

"RPR preserves possible-dispatch uncertainty until configured reconciliation supplies sufficient evidence."

### CLM-07 Restart preserves responsibility-pathway state

**Claim**

Restart does not erase durable pathway, attempt, or evidence state.

**Threat / counterexample**

- only the attempt ledger is durable while pathway state is memory-only;
- new runtime reconstructs a different definition or state;
- evidence ordering changes;
- migration silently resets unknown or gate states;
- process-local executor cache is mistaken for durable replay state.

**Mechanism**

- SQLite pathway store;
- SQLite attempt ledger;
- canonical serialization and fingerprints;
- ordered evidence sequence and hash chain;
- schema metadata and forward-version rejection;
- new runtime construction using the same database files.

**Implementation anchors**

- `src/rpr/storage.py`;
- `src/rpr/attempts.py`;
- `src/rpr/evidence.py`;
- model serialization.

**Trusted assumptions**

- database files survive and are durably flushed by the underlying platform;
- SQLite and filesystem durability settings meet the stated deployment assumptions;
- backups, disk failure, and hostile database replacement are outside the current claim unless separately tested.

**Verification strategy**

- `RPR-PER-001` through `RPR-PER-009`;
- `RPR-CRS-001` through `RPR-CRS-010`;
- `E2E-01`, `E2E-03`, `E2E-05`, `E2E-07`;
- mandatory closure of original connections and construction of new objects.

**Required evidence**

- database artifact hashes before and after restart;
- recovered definitions, states, attempt results, fingerprints, and ordered events;
- evidence-chain verification after restart;
- migration and newer-schema rejection logs.

**Residual risk**

The current claim is bounded to tested single-node SQLite persistence and does not establish distributed-database correctness or disaster recovery.

**Permitted wording**

"RPR restores pathway, attempt, and evidence state across process restart in the tested SQLite deployment mode."

### CLM-08 Reconciliation keeps attempt, pathway, and evidence coherent

**Claim**

Reconciliation updates the durable attempt classification, pathway state, and evidence consistently.

**Threat / counterexample**

- ledger says succeeded while pathway remains unknown;
- pathway becomes completed without reconciliation evidence;
- crash between updates creates permanent divergence;
- repeated reconciliation duplicates transitions or evidence;
- unauthorized actor reconciles.

**Mechanism**

- runtime-integrated reconciliation API;
- authorization before observation result application;
- a transaction spanning compatible durable updates, or a recoverable journaled protocol if stores remain separate;
- deterministic mapping from reconciliation result to pathway state;
- idempotency key or reconciliation identity;
- evidence event tied to attempt and observer result.

**Implementation anchors**

- planned changes to `src/rpr/runtime.py`;
- `src/rpr/reconciliation.py`;
- `src/rpr/attempts.py`;
- `src/rpr/storage.py`;
- evidence builder.

**Trusted assumptions**

- observer output is truthful for the declared property;
- cross-store atomicity is not assumed unless pathway and attempt data share a transaction boundary;
- if separate stores remain, recovery metadata is durable and complete.

**Verification strategy**

- `RPR-REC-001` through `RPR-REC-007`;
- `RPR-CRS-007`, `RPR-CRS-008`;
- repeated reconciliation;
- crash injection at every persistence sub-step;
- unauthorized reconciliation attempt.

**Required evidence**

- same classification visible in attempt record, pathway state, and latest event;
- observer identity and evidence summary;
- no duplicate event after replay;
- recovery result after injected crash.

**Residual risk**

This claim is not currently satisfied by the standalone ledger-only reconciliation helper and remains blocked until runtime integration is implemented and tested.

**Permitted wording**

No external product claim is permitted until the blocking implementation and tests pass.

### CLM-09 Repair, resume, compensation, and residual ownership are explicit and authorized

**Claim**

Failure recovery does not silently collapse responsibility; repair, resume, compensation, and residual closure require declared actors and durable evidence.

**Threat / counterexample**

- execution actor self-approves repair or resume;
- compensation is inferred and executed automatically;
- a new attempt loses linkage to the failed attempt;
- partial completion becomes generic failure;
- residual impact is closed without residual-owner acceptance.

**Mechanism**

- distinct repair and resume states;
- repair-owner and resume-authority rules;
- explicit compensation pathway definition;
- new attempt identity with prior-attempt linkage;
- residual-owner abort or closure authority;
- durable repair and compensation evidence.

**Implementation anchors**

- state model and transition table;
- `src/rpr/authority.py`;
- runtime repair and resume APIs;
- attempt and evidence records.

**Trusted assumptions**

- organizational role assignment is legitimate;
- compensation semantics are supplied by the integrating application;
- irreversible effects are disclosed rather than assumed reversible.

**Verification strategy**

- `RPR-RPR-001` through `RPR-RPR-007`;
- `E2E-05`;
- unauthorized repair, resume, compensation, and closure attempts;
- partial-effect fixtures.

**Required evidence**

- repair owner, failed condition, repair evidence, resume authority, prior and new attempt IDs, compensation declaration, and residual-owner decision;
- valid ordered evidence chain across the lifecycle.

**Residual risk**

RPR cannot prove that a real-world repair or compensation is ethically, legally, or economically sufficient.

**Permitted wording**

"RPR records and enforces declared authority for the tested repair, resume, compensation, and residual-closure pathway."

### CLM-10 Evidence is ordered, tamper-evident, inspectable, and redacted

**Claim**

Evidence is durably ordered, hash-linked, inspectable, and filtered according to the configured redaction policy.

**Threat / counterexample**

- event removal, reordering, substitution, or payload modification is undetected;
- state transition occurs without an event;
- secrets or authorization headers are persisted;
- untrusted payload forges actor or event structure;
- diagnostics contradict durable state.

**Mechanism**

- sequence-ordered event persistence;
- previous-hash and event-hash linkage;
- atomic state-and-event transaction;
- structured event construction controlled by runtime;
- redaction before persistence;
- verification and inspection APIs.

**Implementation anchors**

- `src/rpr/evidence.py`;
- `src/rpr/storage.py`;
- `src/rpr/redaction.py`;
- `src/rpr/inspection.py`;
- `src/rpr/runtime.py`.

**Trusted assumptions**

- hash function implementation behaves as expected;
- the database and code are not both replaced by a fully privileged attacker;
- hash linkage provides tamper evidence, not cryptographic non-repudiation or signed provenance.

**Verification strategy**

- `RPR-EVD-001` through `RPR-EVD-006`;
- `RPR-PER-004`;
- removal, reordering, substitution, and payload mutation tests;
- secret-seeded negative tests;
- restart-chain verification.

**Required evidence**

- ordered events and hashes;
- verifier result and failure index for tampering;
- absence assertions for configured secrets;
- state and inspection equivalence.

**Residual risk**

Current hash chaining is not a digital signature, trusted timestamp, external notarization, or proof against a privileged attacker rewriting the database and recomputing hashes.

**Permitted wording**

"RPR produces ordered, hash-linked, inspectable evidence with configured redaction; it does not claim signed non-repudiation."

### CLM-11 JSON, Python, and Lean 4 agree on the selected transition model

**Claim**

The canonical JSON model, generated Python transition representation, and selected Lean 4 model agree on the states and transitions included in the parity boundary.

**Threat / counterexample**

- generated Python is stale;
- Lean model omits or adds a transition without detection;
- documentation claims whole-runtime verification;
- CI runs Lean but does not check the relevant theorems or freshness.

**Mechanism**

- canonical machine-readable state model;
- generated Python transition artifact;
- parity scripts comparing state and transition sets;
- Lean definitions and selected invariants;
- CI freshness and `lake build` checks;
- release-claim audit.

**Implementation anchors**

- canonical JSON specifications;
- generated `_generated_transitions.py`;
- parity and generation tools;
- Lean source and lake project;
- release-audit scripts.

**Trusted assumptions**

- parity scripts correctly parse all representations in the declared subset;
- Lean toolchain and trusted kernel are functioning;
- runtime code outside the generated transition table is not implied to be formally verified.

**Verification strategy**

- `RPR-FRM-001` through `RPR-FRM-005`;
- stale generated-artifact negative test;
- deliberate JSON/Python and Python/Lean mismatch fixtures;
- clean Lean build;
- documentation phrase audit.

**Required evidence**

- compared state and transition counts and hashes;
- parity output;
- Lean build output naming checked modules;
- list of theorem names and exact claims they support;
- release-audit result.

**Residual risk**

This does not prove Python executor behavior, SQLite semantics, external effects, legal compliance, or total system safety.

**Permitted wording**

"RPR cross-checks its selected canonical transition model across JSON, generated Python, and Lean 4, with selected invariants machine-checked in CI."

### CLM-12 Built artifacts are usable in a clean environment

**Claim**

The released candidate artifacts contain the required runtime and can be installed and exercised without relying on the development repository.

**Threat / counterexample**

- editable install hides missing package data;
- wheel omits schemas, generated transitions, or notices;
- CLI works only from source checkout;
- legacy names or private paths leak into the artifact;
- release metadata overstates verified scope.

**Mechanism**

- wheel and sdist build;
- clean virtual-environment install;
- import, CLI, and documented scenario execution;
- artifact content and residue inspection;
- metadata and claim audit;
- RC rehearsal without publication.

**Implementation anchors**

- `pyproject.toml`;
- package-data configuration;
- CLI entry point;
- build, audit, and RC rehearsal tools;
- documentation quick start.

**Trusted assumptions**

- tested Python versions and operating systems represent the declared support matrix;
- untested platforms are not implied supported.

**Verification strategy**

- `RPR-PKG-001` through `RPR-PKG-010`;
- installation from artifact path only;
- removal of source checkout from `PYTHONPATH`;
- artifact manifest and SHA-256 verification.

**Required evidence**

- artifact names and hashes;
- fresh-environment package list;
- import and CLI output;
- quick-start output;
- artifact manifest;
- residue and release-audit results.

**Residual risk**

Passing the clean-environment suite does not establish performance, availability, security hardening, or compatibility outside the declared support matrix.

**Permitted wording**

"The tested RPR wheel and source distribution install and execute the documented scenario in a clean supported environment."

## 5. Cross-cutting technical evidence

The following evidence types SHALL be retained and linked to the corresponding claim IDs.

| Evidence ID | Evidence type | Technical purpose |
|---|---|---|
| EV-CODE | source commit and diff | identifies the exact implementation under test |
| EV-TEST | test ID, result, and log | demonstrates executable behavior and negative cases |
| EV-DB | pathway, attempt, and event database snapshots | demonstrates durable-state classifications |
| EV-CALL | executor and observer call trace | distinguishes mutation dispatch from observation |
| EV-CHAIN | evidence verification output | demonstrates ordering and detects selected tampering |
| EV-PARITY | JSON/Python/Lean comparison output | demonstrates representation agreement in the declared subset |
| EV-LEAN | Lean build and theorem inventory | demonstrates selected machine-checked invariants |
| EV-ART | wheel/sdist manifest and hashes | binds release evidence to artifacts |
| EV-CLEAN | clean-install and quick-start transcript | demonstrates installed-product usability |
| EV-AUDIT | release claim and residue audit | prevents unsupported or stale public claims |

## 6. Required claim-to-test traceability

A machine-readable traceability manifest SHALL map every claim ID to:

- required test IDs;
- implementation anchors;
- evidence IDs;
- current status: `not_implemented`, `implemented_unverified`, `passing`, `failing`, `deferred`, or `out_of_scope`;
- residual owner for every deferral;
- permitted wording at the current evidence level.

A claim MUST NOT be marked `passing` when any required Blocker or Critical test is missing, skipped, or failing.

## 7. Evidence strength levels

- **E0 — Assertion only**: documentation exists; no implementation evidence.
- **E1 — Mechanism present**: implementation anchor exists; tests incomplete.
- **E2 — Component verified**: unit and component tests pass, including negative cases.
- **E3 — Runtime verified**: integration, persistence, authorization, and restart tests pass.
- **E4 — Product candidate verified**: mandatory E2E, crash, concurrency, package, and formal-parity checks pass with retained evidence.
- **E5 — Operationally validated**: external deployment evidence exists under a declared environment and threat model. Not currently claimed.

Public Alpha wording requires E4 for the relevant claim. Production-ready wording is prohibited at E4 and requires a separately approved operational assurance specification.

## 8. Current assurance assessment

At version 0.1:

- the test specification provides broad claim and test coverage;
- several implementation mechanisms already exist;
- the explicit claim-to-mechanism-to-evidence mapping was previously incomplete;
- replay authorization, integrated reconciliation, real restart, crash recovery, and concurrency remain blocking gaps;
- no claim depending on those gaps may be represented as fully verified;
- RPR remains a private productization candidate within RPP.

## 9. Completion rule

This assurance case is fulfilled only when:

1. every bounded product claim has a complete traceability entry;
2. every trusted assumption is declared and scoped;
3. every Blocker and Critical threat has a falsification-oriented test;
4. required evidence is retained and bound to the tested build;
5. residual risks and excluded claims are present in product documentation;
6. public wording does not exceed the achieved evidence strength;
7. the Human Gate approves export or release.
