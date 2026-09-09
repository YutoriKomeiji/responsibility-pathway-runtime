# RPR Runtime Claim Assurance Case

Status: Active assurance basis
Version: 0.3
Published baseline: `0.1.0a6`
Lifecycle: `CURRENT`
Release boundary: This document does not authorize release, production-readiness claims, or Authority transfer.

## 1. Purpose

This assurance case defines why RPR's bounded product claims are technically supportable, what could falsify them, which mechanisms/tests matter, and which risks remain outside the product boundary.

Claim acceptance follows:

```text
bounded claim
  -> counterexample/threat
  -> mechanism
  -> trusted assumptions
  -> implementation anchors
  -> falsification-oriented tests
  -> retained evidence
  -> residual risk
  -> permitted wording
```

A similarly named test is not enough. Evidence must bind to the exact source/release lineage and the claim must not exceed the tested boundary.

## 2. Global assurance rules

1. **Falsification before confirmation.** Safety/responsibility claims require negative tests capable of disproving them.
2. **Cross-surface agreement is part of the claim.** Source, persistence, MCP/CLI, docs, site/demo, claim registries, formal evidence, examples, and release identity must agree where the same concept is represented.
3. **Fail closed does not identify the receiver.** Missing evaluator, invalid route, ineligible receiver, and unresolved effect do not automatically become Human Gate.
4. **Evidence is not Authority.** Evidence transfer, capability, confidence, route selection, transport/tool success, or recovered state do not create or enlarge Authority.
5. **Residual Owner survives routing.** Route destination or successful transfer does not silently replace unresolved-residue ownership.
6. **Historical evidence remains historical.** Release/candidate/audit records are not rewritten to resemble current state.
7. **Exact-head evidence.** Evidence must identify the tested commit/package role, workflow run, environment, test IDs, and artifact hashes.
8. **Missing evidence weakens the claim.** Missing, blocked, stale, or narrower evidence never becomes an inferred pass.
9. **Publication is not transition closure.** A successful release is not sufficient if applicable current public/control surfaces still represent the prior state.

## 3. Evidence levels

- **E0** — proposed claim only.
- **E1** — implementation/source inspection evidence.
- **E2** — executable unit/component evidence.
- **E3** — integration/product/system + retained CI evidence within a bounded environment.
- **E4** — broader independent/field evidence for a declared deployment profile.
- **E5** — reserved for explicitly defined stronger evidence; never inferred from version age.

## 4. Core bounded claims

### CLM-01 — Declared state and Authority govern dispatch
External actions are admitted only from executable pathway state and declared actor Authority within the configured RPR boundary.

### CLM-02 — Explicit configured Human Gate cannot be bypassed
Where human-held approval Authority is explicitly configured, dispatch remains blocked until authorized approval. This does not imply every fail-closed case should become Human Gate.

### CLM-03 — Pre-dispatch rejection does not create false dispatch uncertainty
A request rejected before executor invocation must not leave durable evidence implying possible external mutation.

### CLM-04 — Persisted completed/unresolved attempts are not silently redispatched
Identical persisted attempts replay from durable state without automatic duplicate dispatch within the tested runtime/storage boundary.

### CLM-05 — Completion requires configured verified readback
Transport/executor success does not establish consequential external completion when configured readback is required.

### CLM-06 — Unknown remains unknown
Possible-dispatch uncertainty survives timeout, disconnect, restart, and insufficient observation until reconciliation establishes a bounded result.

### CLM-07 — Durable state survives runtime recreation
Pathway, attempt, Evidence, and declared-route state are restored when new runtime/store objects reopen the same tested SQLite state. Runtime recreation is not automatically an OS-process-restart claim.

### CLM-08 — Reconciliation restores internal coherence
Within tested interruption windows, reconciliation aligns attempt classification, pathway state, Evidence, and externally visible route semantics without redispatch.

### CLM-09 — Repair readiness and resume Authority remain separate
Repair completion does not itself authorize resume.

### CLM-10 — Evidence is ordered, hash-linked, inspectable, and redacted within policy
The evidence ledger is not claimed to be independently signed non-repudiation or externally immutable timestamping.

### CLM-11 — Selected state model is cross-checked across JSON/Python/Lean
Selected canonical state/transition relations are cross-checked; Lean does not prove the complete Python runtime, receiver eligibility, delegation correctness, or organizational Responsibility Routing.

### CLM-12 — Tested build/install path is reproducible within the declared environment
Artifact identity and clean-install evidence must bind to the exact validated lineage.

## 5. CLM-13 — Bounded Responsibility Routing

**Current status:** published Public Alpha `0.1.0a6` claim with bounded E3 release evidence. This does not mean production/enterprise readiness, universal organizational routing correctness, or formal proof of receiver eligibility/delegation semantics.

Published `0.1.0a6` can represent a bounded Responsibility Route that preserves:

- route class;
- source holder and destination;
- receiver eligibility;
- Authority class;
- delegation scope;
- unresolved payload;
- bounded next actions;
- closure condition;
- reevaluation condition;
- Residual Owner;
- optional expiry.

The runtime/inspection surface does not infer Authority from route existence or Evidence transfer.

### Principal falsifiers

- **False Autonomy** — work continues after route/Authority conditions require hold or transfer.
- **Proxy Return** — work is routed to an AI/system lacking receiver eligibility or required Authority.
- **False Escalation** — generic error/unavailability becomes Human Gate without an independently justified human receiver.
- **Nominal Human Return** — a named/notified human lacks Authority, context, eligibility, or bounded next-decision scope.
- **Authority laundering** — capability, Evidence, successful transport, route selection, or recovered state becomes Authority.
- **Residual Owner loss** — destination silently replaces unresolved-residue ownership.
- **Route drift across restart** — persisted/derived route meaning changes without material state change.
- **Claim drift** — public/control surfaces describe a stale version, source preview, or stronger proof level.

### Mechanisms and implementation anchors

Relevant mechanisms include `ResponsibilityRoute`, `ReceiverEligibility`, route validation, neutral HOLD, bounded Human Gate, compatibility mapping, read-only route visibility with `authority_inferred: false`, and Residual Owner validation.

Primary anchors:

- `src/rpr/models.py`
- `src/rpr/inspection.py`
- `src/rpr/routing.py`
- `src/rpr/route_visibility.py`
- `src/rpr/runtime.py`
- `src/rpr/mcp_read_model.py`
- `src/rpr/mcp_server.py`

### Required executable evidence

- `RPR-RTE-001` through `RPR-RTE-008` for route structure, false escalation, reevaluation hold, Authority non-propagation, bounded Human Return, Residual Owner, neutral RPE failure, and read-only route visibility;
- `E2E-ROUTE-01` for ambiguity -> runtime recreation -> no redispatch -> reconciliation;
- `E2E-ROUTE-02` for English/Japanese browser route semantics.

Only IDs bound to executable files in `specs/test-id-registry.json` count as executable Evidence.

### Current release wording

Permitted bounded wording:

> “Published RPR 0.1.0a6 includes bounded Responsibility Routing and read-only route visibility. It preserves declared receiver-eligibility and Residual Owner metadata and does not infer Authority from route, Evidence transfer, capability, transport success, or recovered state.”

Do not extend this to production readiness, legal/institutional accountability, universal exactly-once behavior, arbitrary organizational delegation correctness, or full formal verification.

## 6. Product-quality assurance against recurrence

Cross-surface semantic drift is a systemic defect class. A change that alters state, decision, routing, Authority, Evidence meaning, ownership, external-effect claims, version identity, or release posture must enumerate affected product surfaces before closure.

A version/public-surface transition is not closed until:

1. source semantics are correct;
2. negative tests cover the previous wrong behavior where practical;
3. persistence/restart behavior is checked;
4. public API/MCP/CLI and examples are aligned;
5. EN/JA docs/site/demo are aligned;
6. claim/test/assurance registries are aligned;
7. CI detects the known stale-current-state/lifecycle drift class;
8. exact-head evidence is retained;
9. public readback is complete;
10. old current-state surfaces are updated, historicalized, retired, relocated, or explicitly transitional.

`publication success != product version transition closure`.

## 7. Assurance stop conditions

Claim/transition closure stops if any of the following occurs:

- a required test is missing, skipped, stale, or prose-only;
- invalid/unavailable routing becomes Human Gate without a justified receiver;
- Authority can be inferred from Evidence/capability/route/transport/recovered state;
- Residual Owner can silently disappear/change;
- route metadata is lost across persistence/restart;
- `write_status_unknown` can silently complete or redispatch;
- active surfaces describe an old version as the current/published baseline;
- a released feature is still described as source preview, or unreleased work as released;
- runtime recreation is overstated as process restart;
- Lean scope is overstated;
- EN/JA active surfaces materially disagree;
- current docs/indexes link normal users to retired/historical surfaces as if current;
- the candidate head differs from the head that generated retained Evidence.

## 8. Human Gate

Assurance evidence supports a release/closure decision; it does not make the decision. Later tag creation, GitHub Release, PyPI publication, stronger public claims, or other protected external effects remain explicit Human Gate actions.
