# RPR Runtime Product Test Specification

Status: Active source-preview test basis
Version: 0.2
Product target: Responsibility Pathway Runtime (RPR)
Published baseline: `0.1.0a5`
Release boundary: This specification does not authorize a tag, package release, production-readiness claim, or Authority transfer.

## 1. Purpose

This specification defines the evidence required before current RPR source may be promoted as a new public-alpha release candidate.

A product change is not complete because a function returns the expected value or because a local unit suite is green. RPR must preserve a coherent responsibility pathway across admission, declared Authority, Responsibility Routing, dispatch, persistence, failure, restart, readback, reconciliation, repair/resume, Evidence, Residual Owner, public interfaces, documentation, and release artifacts.

The required product-quality path is:

```text
requirement/design
  -> source
  -> unit
  -> component
  -> integration
  -> system/E2E
  -> persistence/restart
  -> public API/MCP/CLI
  -> EN/JA docs/site/demo
  -> claim/test/evidence registry
  -> CI drift checks
  -> exact-head release validation
  -> Human Gate
```

Any missing stage blocks release promotion.

## 2. Product claims under test

RPR source is intended to support these bounded claims when the corresponding evidence passes:

1. External actions are admitted only through declared pathway state and Authority.
2. Explicit configured Human Gate approval prevents dispatch where human-held Authority is required.
3. Generic fail-closed conditions do not manufacture a human receiver.
4. Responsibility Routing preserves receiver eligibility, delegation scope, unresolved payload, allowed next actions, closure/reevaluation conditions, and Residual Owner where a route is declared.
5. Evidence transfer, capability, confidence, route selection, transport success, or recovered state do not create Authority.
6. Dispatch attempts are durably recorded without creating false evidence for actions rejected before dispatch.
7. Completed or unresolved attempts are not silently re-dispatched.
8. Executor or transport success is not treated as proof of consequential external effect without the required readback.
9. Unknown external effect remains unknown until sufficient reconciliation Evidence is available.
10. Restart does not erase pathway, attempt, Evidence, or declared route metadata.
11. Reconciliation keeps attempt, pathway, Evidence, and routing semantics coherent without redispatch.
12. Repair readiness does not create resume Authority.
13. JSON, generated Python, and Lean 4 agree on the selected canonical state-transition model.
14. Lean evidence is not described as formal proof of Responsibility Routing receiver eligibility/delegation semantics.
15. Built artifacts can be installed and exercised in clean supported environments.
16. Public API/MCP/CLI, EN/JA documentation, site/demo, claim registry, and release identity agree with the exact candidate head.

The suite MUST NOT be presented as proof of legal compliance, full system safety, complete formal verification, production identity assurance, distributed-system correctness, universal exactly-once delivery, or correctness of organizational delegation.

## 3. System under test

The product test boundary includes:

- `ResponsibilityPathwayRuntime`;
- `SQLiteStore`;
- `SQLiteExecutionAttemptLedger`;
- state transition and Authority enforcement;
- `ResponsibilityRoute`, receiver eligibility, inspection, compatibility routing, and route visibility;
- RPE adapters and fail-closed contract handling;
- supplied executors and reconciliation strategies;
- readback and reconciliation;
- Evidence generation, redaction, persistence, verification;
- repair, resume, stop, abort, and Residual Owner transitions;
- CLI and read-only MCP surfaces;
- browser/Pyodide demo surface;
- canonical JSON model, generated Python transition table, and selected Lean 4 model;
- active English/Japanese documentation and product site;
- claim/test/assurance registries and release metadata;
- wheel/source distribution build and install surfaces.

External identity providers, distributed databases, cloud gateways, production credentials, arbitrary third-party MCP services, organizational delegation truth, and legal authority remain outside the current product boundary unless represented by explicit bounded test fixtures.

## 4. Test principles

### 4.1 Fail closed without destination invention

Missing evaluator, unavailable RPE, contract mismatch, invalid route, unsupported state, invalid Evidence, and ambiguous execution outcome MUST NOT become implicit allow.

They also MUST NOT become `HUMAN_GATE` merely because the runtime needs to stop. Human Return is a bounded Responsibility Route. When no eligible receiver or Authority is established, neutral `HOLD` is valid.

### 4.2 Authority does not propagate from evidence or capability

Evidence transfer, receiver capability, model confidence, route selection, tool success, transport receipt, or recovered state MUST NOT create or enlarge Authority.

### 4.3 Receiver eligibility is explicit

An ineligible receiver MUST NOT be selected as an active route destination. `REQUIRES_REEVALUATION` MUST hold until reevaluation occurs.

### 4.4 Residual Owner is preserved

Routing MUST NOT silently replace or clear the pathway Residual Owner. An ownership redesign requires an explicit authorized change outside the implicit route transfer.

### 4.5 No false dispatch Evidence

A request rejected before the executor is called MUST NOT leave a durable attempt implying possible external mutation.

### 4.6 No unverified completion

A successful executor return without the required verified readback MUST NOT move the pathway to `completed`.

### 4.7 Unknown remains unknown

Timeout, disconnect, crash, or incomplete persistence after possible dispatch MUST result in explicit unresolved state until reconciliation establishes otherwise.

### 4.8 Replay is authorized

Duplicate-dispatch prevention MUST NOT bypass pathway access or actor authorization.

### 4.9 State, attempt, Evidence, and route coherence

Any operation that classifies or repairs an attempt MUST leave pathway state, attempt record, Evidence trail, and externally visible route semantics mutually coherent.

### 4.10 Real restart semantics are named precisely

A test that constructs new runtime/store objects over the same durable database is a **runtime recreation** test. A test that terminates and launches an OS process is a **process restart** test. Documentation and claims MUST NOT substitute one term for the other.

### 4.11 Exact-head acceptance

Release evidence is valid only for the exact source lineage tested. A frozen candidate changed after validation MUST be rebuilt and revalidated rather than inheriting stale evidence.

## 5. Test levels

- **L1 Unit** — serialization, pure validation, compatibility routing, Authority rules, fingerprints, redaction, state transitions.
- **L2 Component** — SQLite stores, attempt ledger, route persistence/visibility, Evidence chain, executors, RPE adapters, read-only MCP model.
- **L3 Integration** — runtime + real SQLite stores + bounded executors/reconcilers/MCP contracts.
- **L4 Product/System E2E** — admission through approval/hold, dispatch, ambiguity, restart/recreation, reconciliation, route visibility, Evidence, and closure.
- **L5 Release verification** — full suite, browser EN/JA, build/install, CLI/MCP, JSON/Python/Lean parity, documentation/claim drift audit, artifact identity, exact-head CI.

A new Public Alpha candidate MUST pass required L1-L5 checks. Environment-only cases remain explicitly blocked/field-evidence items rather than synthetic passes.

## 6. Required Responsibility Routing catalogue

### RPR-RTE-001 — Route structural validation

Valid routes serialize and deserialize. Missing/blank required route fields, blank allowed actions, or missing bounded next actions fail closed.

### RPR-RTE-002 — No false human escalation

An ineligible non-human receiver or generic route-definition error results in neutral `HOLD`, not an invented `HUMAN_GATE`.

### RPR-RTE-003 — Reevaluation hold

`ReceiverEligibility.REQUIRES_REEVALUATION` remains held until eligibility is reevaluated. No execution or Human Return is inferred.

### RPR-RTE-004 — Authority non-propagation and legacy compatibility

Route/Evidence transfer does not create Authority. Legacy pathways without declared route metadata remain readable and behavior-compatible within the documented migration boundary.

### RPR-RTE-005 — Bounded Human Return

A `BOUNDED_HUMAN_RETURN` route requires a concrete Human Return point and appropriate configured Authority. Non-human route classes do not require the legacy Human Return field merely to exist.

### RPR-RTE-006 — Residual Owner preservation

Declared route metadata must preserve the pathway Residual Owner unless an explicit authorized redesign occurs. A mismatch fails closed.

### RPR-RTE-007 — Neutral RPE failure

Default RPE unavailable, Python adapter exception, REST unavailability, and contract mismatch produce `HOLD` unless a more restrictive independently justified local condition such as configured high-impact Human Gate applies.

### RPR-RTE-008 — Read-only route visibility

`rpr.get_route_visibility` returns state, narrow compatibility route, declared route where present, Human Return point, Residual Owner, and `authority_inferred: false`. It must not mutate state or expose approval/execution/reconciliation/resume capability.

### E2E-ROUTE-01 — Ambiguous effect -> restart -> reconciliation

Given a declared `HOLD_FOR_RECONCILIATION` route:

1. authorized execution produces `write_status_unknown` after one external dispatch;
2. route visibility reports `hold_for_reconciliation`, preserves declared route and Residual Owner, and reports `authority_inferred: false`;
3. a newly constructed runtime over the same SQLite stores observes identical route metadata;
4. replay does not redispatch;
5. authorized independent reconciliation closes the effect;
6. Evidence chain remains valid;
7. completed state has no unreviewed compatibility route while the declared route record remains inspectable.

### E2E-ROUTE-02 — Browser English/Japanese parity

Both `site/demo.html` and `site/demo-en.html` MUST load the CI-built wheel and assert:

- initial high-impact route: `bounded_human_return`;
- ambiguous effect route: `hold_for_reconciliation`;
- `authority_inferred == false` throughout route inspection;
- exactly one external dispatch;
- restart/reconciliation reaches `completed`;
- Evidence remains valid;
- final compatibility route is absent rather than guessed.

## 7. Existing core runtime catalogue retained

The existing IDs remain required where applicable:

- admission: `RPR-ADM-*`;
- Authority: `RPR-AUT-*`;
- pre-dispatch durability: `RPR-PRE-*`;
- execution/readback: `RPR-EXE-*`;
- idempotency/replay: `RPR-IDM-*`;
- crash/restart: `RPR-CRS-*`;
- reconciliation: `RPR-REC-*`;
- repair/resume/residual: `RPR-RPR-*`;
- persistence/concurrency: `RPR-PER-*`;
- Evidence: `RPR-EVD-*`;
- RPE integration: `RPR-RPE-*`;
- formal parity: `RPR-FRM-*`;
- package/release: `RPR-PKG-*`.

The authoritative file bindings are maintained in `specs/test-id-registry.json`. An ID present only in prose is not treated as executable Evidence.

## 8. Cross-surface semantic-drift tests

Release validation MUST fail when any applicable current surface disagrees with the source semantics.

Required checks include:

- active EN/JA document pairs both exist;
- active product version identifiers match the published baseline/candidate role they describe;
- post-release source-preview language is explicit where current source exceeds the published package;
- `Responsibility Routing` appears on required active product surfaces;
- `rpr.get_route_visibility` is described as post-`0.1.0a5` source preview until actually released;
- `bounded_human_return`, `hold_for_reconciliation`, and `authority_inferred: false` are asserted by browser demo surfaces;
- historical release records are not rewritten merely to satisfy current-state checks;
- formal documentation states that Lean does not prove receiver eligibility/delegation semantics;
- demo documentation lists only artifacts that actually exist;
- runtime recreation is not mislabeled as OS-process restart;
- claim/test registries contain current routing claims and executable bindings.

## 9. Release acceptance evidence

Before a fresh candidate can enter release Human Gate, retain at minimum:

- exact candidate commit SHA;
- full CI workflow IDs and conclusions;
- Python/OS versions for each required job;
- test count/result produced by that exact run, without copying historical counts forward;
- wheel/sdist names and digests;
- clean-install result;
- CLI and MCP smoke results;
- browser EN/JA E2E result;
- JSON/Python/Lean parity result and Lean build result;
- documentation/semantic-drift validator result;
- claim/test registry validation;
- independent review/readback outcome;
- explicit residual risks and blocked environment-only cases.

## 10. Release stop conditions

Release promotion MUST stop if any of the following holds:

- a required L1-L5 layer is missing or failing;
- a generic fail-closed path still invents a Human Gate;
- receiver eligibility or Residual Owner can be silently bypassed;
- Authority can be inferred from Evidence/capability/route/transport;
- ambiguous effect can be silently completed or redispatched;
- route state is lost across persistence/restart;
- EN/JA current surfaces disagree materially;
- source preview is described as already released;
- formal claims overstate Lean scope;
- demo/docs refer to nonexistent artifacts or stronger restart semantics than tested;
- claim registry is ahead of executable Evidence;
- exact candidate head differs from the head that produced retained evidence.

## 11. Human Gate

Passing this specification does not itself publish anything. Tag creation, GitHub Release, PyPI publication, and stronger public claims remain explicit human release decisions after exact-head evidence is reviewed.
