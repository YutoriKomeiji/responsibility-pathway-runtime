# RPR Runtime Product Test Specification

Status: Active product/release test basis
Version: 0.3
Lifecycle: `CURRENT`
Product target: Responsibility Pathway Runtime (RPR)
Published baseline: `0.1.0a6`
Release boundary: This specification does not authorize a tag, package release, production-readiness claim, or Authority transfer.

## 1. Purpose

This specification defines the evidence required to validate current RPR source and to promote any later Public Alpha candidate. It also defines post-release reconciliation checks required before a version/public-surface transition may be treated as closed.

A product change is not complete because a function returns the expected value, local tests are green, or publication succeeds. RPR must preserve a coherent responsibility pathway across admission, declared Authority, Responsibility Routing, dispatch, persistence, failure, restart, readback, reconciliation, repair/resume, Evidence, Residual Owner, public interfaces, examples, documentation, release artifacts, and current-state lifecycle surfaces.

Required quality path:

```text
requirement/design
  -> source
  -> unit/component/integration/system
  -> persistence/restart
  -> public API/MCP/CLI/examples
  -> EN/JA docs/site/demo
  -> claim/test/evidence registry
  -> CI drift checks
  -> exact-head release validation
  -> Human Gate
  -> publication/readback
  -> post-release reconciliation
  -> current-surface closure
```

## 2. Product claims under test

Within declared boundaries, evidence may support:

1. external actions are admitted only through declared pathway state and Authority;
2. explicit configured Human Gate blocks dispatch where human-held Authority is required;
3. generic fail-closed conditions do not manufacture a human receiver;
4. Responsibility Routing preserves receiver eligibility, delegation scope, unresolved payload, allowed next actions, closure/reevaluation conditions, and Residual Owner;
5. Evidence transfer, capability, confidence, route selection, transport success, or recovered state do not create Authority;
6. rejected pre-dispatch actions do not leave false possible-mutation evidence;
7. completed or unresolved attempts are not silently redispatched;
8. executor/transport success is not proof of consequential external effect without required readback;
9. unknown external effect remains unknown until sufficient reconciliation Evidence exists;
10. restart/runtime recreation does not erase pathway, attempt, Evidence, or declared-route metadata;
11. reconciliation restores coherent attempt/pathway/Evidence/routing state without redispatch;
12. repair readiness does not create resume Authority;
13. selected JSON/Python/Lean state-transition representations agree;
14. Lean evidence is not described as proof of receiver eligibility/delegation semantics;
15. built artifacts can be installed/exercised in clean declared environments;
16. public API/MCP/CLI/examples, EN/JA docs/site/demo, claim registry, and release identity agree with the exact tested lineage;
17. post-release current surfaces no longer describe a superseded published version or released feature as source preview.

The suite is not proof of legal compliance, full system safety, production identity assurance, distributed-system correctness, universal exactly-once delivery, complete formal verification, or correctness of arbitrary organizational delegation.

## 3. System under test

The product boundary includes runtime/state/Authority enforcement, SQLite pathway and attempt persistence, `ResponsibilityRoute` / receiver eligibility / compatibility routing / route visibility, RPE fail-closed adapters, supplied executors/reconcilers, Evidence, repair/resume/stop/abort/Residual Owner transitions, CLI/read-only MCP surfaces, browser/Pyodide demo, selected formal model parity, active EN/JA docs, examples, claim/test/assurance registries, status/release metadata, and wheel/sdist build/install surfaces.

External identity providers, production credentials, arbitrary third-party MCP services, organizational delegation truth, distributed remote transaction guarantees, and legal authority remain outside unless a dedicated bounded profile explicitly includes them.

## 4. Test principles

- **Fail closed without destination invention.** Missing/invalid/unavailable controls do not imply allow and do not imply Human Gate without a justified receiver.
- **Authority does not propagate.** Evidence/capability/confidence/route/tool/transport/recovered state do not create Authority.
- **Receiver eligibility is explicit.** Ineligible or reevaluation-required receivers remain held.
- **Residual Owner is preserved.** Routing does not silently replace unresolved-residue ownership.
- **No false dispatch Evidence.** Rejection before executor invocation does not leave possible-mutation evidence.
- **No unverified completion.** Required readback remains required after transport/executor success.
- **Unknown remains unknown.** Timeout/disconnect/crash after possible dispatch stays unresolved until reconciliation.
- **Replay remains authorized.** Duplicate-dispatch prevention does not bypass current actor/state/Authority checks.
- **State/attempt/Evidence/route coherence.** Classification or repair leaves durable and visible surfaces mutually coherent.
- **Restart language is precise.** Runtime recreation is not called OS-process restart without process-level evidence.
- **Exact-head acceptance.** Changed candidates must be rebuilt/revalidated.
- **Publication is not closure.** Successful upload/tag/release/readback does not close a transition while active surfaces still represent the old current state.

## 5. Required levels

- **L1 Unit** — serialization, pure validation, routing, Authority, fingerprints, redaction, state transitions.
- **L2 Component** — SQLite stores, attempt ledger, route persistence/visibility, Evidence chain, executors, RPE adapters, read-only MCP model.
- **L3 Integration** — runtime + durable stores + bounded executors/reconcilers/MCP contracts.
- **L4 Product/System E2E** — admission through approval/hold, dispatch, ambiguity, restart/recreation, reconciliation, route visibility, Evidence, closure.
- **L5 Release verification** — full suite, browser EN/JA, build/install, CLI/MCP, JSON/Python/Lean parity, documentation/claim drift audit, artifact identity, exact-head CI.
- **L6 Post-release reconciliation** — public readback plus current-surface lifecycle audit and retirement/historicalization of superseded state.

A later Public Alpha candidate must pass applicable L1-L5 before release Human Gate. L6 applies after publication and before `PRODUCT_VERSION_TRANSITION_CLOSED`.

## 6. Responsibility Routing catalogue

- `RPR-RTE-001` — route structural validation.
- `RPR-RTE-002` — no false human escalation.
- `RPR-RTE-003` — reevaluation hold.
- `RPR-RTE-004` — Authority non-propagation and legacy compatibility.
- `RPR-RTE-005` — bounded Human Return requirements.
- `RPR-RTE-006` — Residual Owner preservation.
- `RPR-RTE-007` — neutral RPE failure.
- `RPR-RTE-008` — read-only route visibility.
- `E2E-ROUTE-01` — ambiguous effect -> runtime recreation -> no redispatch -> reconciliation.
- `E2E-ROUTE-02` — browser English/Japanese route parity.

Published `0.1.0a6` includes the Responsibility Routing/read-only route-visibility surface these tests bound. Future source changes still require new exact-head evidence before a later release.

The authoritative executable bindings remain in `specs/test-id-registry.json`; prose-only IDs do not count as executable Evidence.

## 7. Cross-surface semantic-drift tests

Validation must fail when applicable current surfaces disagree with current product/release semantics.

Required checks include:

- active EN/JA pairs both exist;
- current docs identify the published version consistently with `product-status.json`;
- no active current-facing surface describes a superseded version as the current/published baseline;
- no released feature is still described as source preview;
- no unreleased source work is described as released merely because it exists on `main`;
- `Responsibility Routing` appears on required current surfaces;
- published `0.1.0a6` route visibility is described as released and read-only;
- `bounded_human_return`, `hold_for_reconciliation`, and `authority_inferred: false` remain asserted by browser demo surfaces;
- historical candidate/audit/migration records are kept outside active current docs and are not rewritten into current truth;
- transitioning surfaces, when present, have an explicit retire/exit condition;
- authoring-control documents are not indexed as user-facing product guidance;
- formal docs state the actual proof ceiling;
- runtime recreation is not mislabeled as OS-process restart;
- claim/test registries contain current routing claims and executable bindings;
- examples do not advertise an obsolete published package baseline.

## 8. Version-transition regression checks

Known failures become regression inputs.

At minimum, the validator/test path should reject recurrence of:

- active text stating `0.1.0a5` is the current published Public Alpha after `product-status.json` says `0.1.0a6`;
- active support/maturity text calling Responsibility Routing source preview after it is released;
- a migration document remaining required/indexed after its transition has completed;
- release-candidate or pre-public audit records remaining in active product-doc indexes;
- Japanese/English lifecycle asymmetry;
- stale examples/specs that retain prior-version current-state claims while README/site are current.

Operational rule:

`KNOWN_FAILURE -> MACHINE_CHECK -> REGRESSION_TEST -> CLOSURE_EVIDENCE`

## 9. Release acceptance evidence

Before a later candidate enters release Human Gate, retain exact candidate SHA, CI runs/conclusions, declared Python/OS profiles, exact-run test results, wheel/sdist names/digests, clean-install results, CLI/MCP smoke, browser EN/JA E2E, formal parity/build, semantic-drift validator result, registry validation, independent review/readback, and explicit residual risks.

## 10. Post-release reconciliation evidence

Before `PRODUCT_VERSION_TRANSITION_CLOSED`, retain evidence that:

1. published package/tag/release identity was read back;
2. current README/docs/site/examples/spec/control surfaces were re-audited after publication;
3. superseded current-state wording was updated;
4. release-specific historical records were preserved outside active current surfaces;
5. transitional documents were retired or kept with explicit exit conditions;
6. EN/JA and other paired surfaces agree materially;
7. validators can reproduce the known stale-current-state failure class;
8. unresolved residue has an explicit owner and next permitted action.

## 11. Stop conditions

Release or transition closure stops if a required layer fails; a Human Gate is invented from generic failure; receiver eligibility/Residual Owner/Authority boundaries can be bypassed; ambiguous effects can silently complete/redispatch; route state is lost; active current surfaces disagree; source-preview/released status is inverted; formal scope is overstated; current docs route users to retired surfaces as normal guidance; examples/specs retain an obsolete current baseline; registry state outruns executable Evidence; or retained evidence belongs to a different head.

## 12. Human Gate

Passing this specification does not publish anything. Later tags, GitHub Releases, PyPI publication, stronger public claims, and other protected external effects remain explicit human decisions after exact-head evidence is reviewed.
