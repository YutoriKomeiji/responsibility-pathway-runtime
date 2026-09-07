# RPR Runtime Claim Assurance Case

Status: Active source-preview assurance basis
Version: 0.2
Published baseline: `0.1.0a5`
Release boundary: This document does not authorize release, production-readiness claims, or Authority transfer.

## 1. Purpose

This assurance case explains why RPR's bounded product claims are technically supportable, what could falsify them, which mechanisms and tests are relevant, and which risks remain outside the product boundary.

Claim acceptance follows this chain:

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

A test with a similar name is not enough. Evidence must bind to the exact source lineage and the claim must not exceed the tested boundary.

## 2. Global assurance rules

### 2.1 Falsification before confirmation

Every safety- or responsibility-relevant claim MUST have at least one negative/adversarial test capable of disproving it. Happy-path tests alone are insufficient.

### 2.2 Cross-surface agreement is part of the claim

If the same product concept appears in source, persistence, MCP/CLI, documentation, site/demo, claim registries, or formal evidence, those surfaces must agree. A green source test does not cure a stale public contract.

### 2.3 `Fail closed` does not identify the receiver

Stopping safely is distinct from routing responsibility. Missing RPE, malformed contracts, invalid routes, ineligible receivers, and unresolved effects must not automatically become Human Gate. Human Return is a bounded Responsibility Route.

### 2.4 Evidence is not Authority

Evidence transfer, receiver capability, confidence, route selection, transport success, tool success, or recovered state do not create or enlarge Authority.

### 2.5 Residual Owner survives routing

The Residual Owner is not silently replaced by a route destination or by successful transfer. A change of ownership requires an explicit authorized redesign.

### 2.6 Historical evidence remains historical

Old release records are not rewritten to resemble current state. Current source-preview and current published package are stated separately.

### 2.7 Exact-head evidence

Retained evidence must identify the tested commit SHA, package version/candidate role, workflow run, environment, test IDs, and artifact hashes. A changed frozen candidate requires fresh validation.

### 2.8 Claim weakening on missing evidence

Missing, blocked, stale, or narrower evidence weakens the claim. It never becomes an inferred pass.

## 3. Evidence levels

- **E0** — proposed claim only.
- **E1** — implementation exists; local/source inspection evidence only.
- **E2** — executable unit/component evidence.
- **E3** — integration/product/system and retained CI evidence within a bounded environment.
- **E4** — broader independent/field evidence for a declared deployment profile.
- **E5** — reserved for stronger evidence forms explicitly defined later; never inferred from version age.

Current Responsibility Routing claim `CLM-13` remains below release-level assurance until exact-head L1-L5 evidence is complete.

## 4. Core claim assurance matrix

### CLM-01 — Declared state and Authority govern dispatch

**Claim**  
Within the configured RPR boundary, external actions are admitted only from executable pathway state and declared actor Authority.

**Counterexamples**
- execution from held, denied, completed, unknown, or otherwise non-executable state;
- unauthorized actor dispatch;
- replay result leakage before authorization;
- development evaluator becoming implicit allow.

**Mechanisms**
- canonical transition table;
- `ensure_transition()`;
- Authority checks;
- execution admission before executor invocation;
- explicit opt-in development evaluator.

**Anchors**
- `src/rpr/runtime.py`
- `src/rpr/authority.py`
- `src/rpr/state_machine.py`

**Evidence**
- `RPR-AUT-*`, `RPR-PRE-*`, admission negative tests;
- zero executor calls on rejected paths;
- unchanged durable state and no false attempt residue.

**Residual risk**  
Host identity binding, credential issuance, and bypass paths outside RPR remain integrator-owned.

### CLM-02 — Explicit configured Human Gate cannot be bypassed

**Claim**  
Where the pathway explicitly requires human-held approval Authority, dispatch remains blocked until authorized approval.

**Counterexamples**
- RPE allow bypasses configured approval;
- missing approval Authority becomes approval;
- wrong actor approves;
- executor called while configured Human Gate remains unresolved.

**Mechanisms**
- distinction between evaluator decision and pathway approval;
- configured approval transition;
- actor/Authority checks.

**Boundary**  
This claim does **not** say every fail-closed case should become Human Gate.

### CLM-03 — Pre-dispatch rejection does not create false dispatch uncertainty

**Claim**  
RPR does not retain an attempt implying possible external mutation when rejection occurs before executor invocation.

**Threats**
- attempt row survives invalid state/actor rejection;
- cleanup removes a different/finalized attempt;
- crash boundary makes pre-dispatch and post-dispatch uncertainty indistinguishable.

**Mechanisms**
- scoped request fingerprints and attempt identity;
- restricted pre-dispatch cleanup;
- durable attempt lifecycle.

### CLM-04 — Persisted completed/unresolved attempts are not silently redispatched

**Claim**  
Identical persisted attempts replay from durable state without automatic duplicate dispatch within the tested runtime/storage boundary.

**Threats**
- restart loses the attempt;
- same idempotency key with changed payload accepted;
- concurrent begin authorizes two dispatches;
- unresolved attempt gets retried automatically.

**Evidence**
- idempotency/replay tests;
- runtime recreation and fault-injection tests;
- executor call-count assertions.

### CLM-05 — Completion requires the configured verified readback

**Claim**  
Transport/executor success does not establish consequential external completion when configured readback is required.

**Threats**
- callback success before remote commit;
- stale/wrong resource readback;
- missing readback collapses to completed.

**Mechanisms**
- separate execution status and `ReadbackEvidence`;
- completion only after verified readback;
- mismatch/unavailable readback retains uncertainty or repair path.

### CLM-06 — Unknown remains unknown until sufficient classification

**Claim**  
Possible-dispatch uncertainty survives timeout, disconnect, restart, and insufficient observation until reconciliation establishes a bounded result.

**Threats**
- unknown -> failed -> automatic retry;
- unknown -> completed from callback inference;
- restart weakens uncertainty;
- reconciliation redispatches instead of observing.

**Mechanisms**
- `write_status_unknown`;
- durable pathway/attempt storage;
- observation-only reconciliation;
- no automatic redispatch.

### CLM-07 — Durable state survives runtime recreation

**Claim**  
Pathway, attempt, and Evidence state are restored when new runtime/store objects reopen the same tested SQLite state.

**Boundary**  
Runtime recreation is not automatically an OS-process restart claim. Process-interruption claims require process-level tests.

### CLM-08 — Reconciliation restores internal coherence

**Claim**  
Within tested interruption windows, reconciliation aligns attempt classification, pathway state, and Evidence without redispatch.

**Residual risk**  
Pathway and attempt storage may span separate SQLite transactions; cross-database atomicity is not claimed unless specifically tested/proved.

### CLM-09 — Repair readiness and resume Authority remain separate

**Claim**  
Repair completion does not itself authorize resume. Resume identity and Authority remain explicit.

**Threats**
- repair owner resumes without resume Authority;
- restored state is treated as renewed approval;
- compensation inferred from failure.

**Current assurance posture**  
Implemented with bounded E2E coverage, but broader compensation/residual-closure product assurance remains constrained by declared claim registry status.

### CLM-10 — Evidence is ordered, hash-linked, inspectable, and redacted within policy

**Claim**  
RPR produces inspectable ordered Evidence and detects tested tampering while applying configured redaction.

**Non-claim**  
The ledger is not independently signed non-repudiation or an externally immutable timestamp service.

### CLM-11 — Selected state model is cross-checked across JSON/Python/Lean

**Claim**  
Selected canonical state/transition relations are cross-checked across JSON, generated Python, and Lean 4, with selected invariants machine-checked.

**Critical boundary**  
Lean does not formally prove:
- Python runtime correctness as a whole;
- receiver eligibility;
- delegation scope correctness;
- Authority non-propagation through arbitrary integrations;
- Responsibility Routing as an organizational process.

### CLM-12 — Tested build/install path is reproducible within the declared environment

**Claim**  
The exact tested wheel/source distribution can be built, installed, and exercised in the declared clean environment when release evidence is fresh.

**Threats**
- artifact digest from a different head;
- source tree used instead of built wheel;
- stale package metadata;
- candidate changed after freeze.

## 5. CLM-13 — Bounded Responsibility Routing

**Current status:** implementation/source-preview claim; release-level assurance pending exact-head validation.

### Claim

Current RPR source can represent a bounded Responsibility Route that preserves:

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

The runtime/inspection surface does not infer Authority from the existence of the route or Evidence transfer.

### Threats / falsifiers

1. **False Autonomy** — work continues automatically after route/Authority conditions require hold or transfer.
2. **Proxy Return** — responsibility is routed to an AI/system that lacks receiver eligibility or required Authority.
3. **False Escalation** — generic error/unavailability is turned into Human Gate even though no human destination was established.
4. **Nominal Human Return** — a human is named but lacks Authority, context, or bounded next-decision scope.
5. **Authority laundering** — capability, Evidence, successful transport, or route selection silently becomes Authority.
6. **Residual Owner loss** — route destination silently replaces the owner of unresolved residue.
7. **Route drift across restart** — persisted declared route or externally visible compatibility classification changes without material state change.
8. **Claim drift** — docs/site/demo say routing is released/formally proved beyond executable Evidence.

### Mechanisms

- `ResponsibilityRoute` and `ReceiverEligibility` model;
- additive persistence through pathway serialization;
- route validation in `inspection.py`;
- neutral HOLD for generic invalid/unavailable route conditions;
- explicit high-impact Human Gate only where independently justified;
- compatibility mapping in `routing.py`;
- read-only `route_visibility.py` with `authority_inferred: false`;
- Residual Owner equality validation;
- exact-head public surface validator;
- bilingual browser semantic assertions.

### Implementation anchors

- `src/rpr/models.py`
- `src/rpr/inspection.py`
- `src/rpr/routing.py`
- `src/rpr/route_visibility.py`
- `src/rpr/runtime.py`
- `src/rpr/mcp_read_model.py`
- `src/rpr/mcp_server.py`

### Required executable evidence

- `RPR-RTE-001` — structural validation;
- `RPR-RTE-002` — no false human escalation;
- `RPR-RTE-003` — reevaluation hold;
- `RPR-RTE-004` — Authority non-propagation / compatibility;
- `RPR-RTE-005` — bounded Human Return requirements;
- `RPR-RTE-006` — Residual Owner preservation;
- `RPR-RTE-007` — neutral RPE failure;
- `RPR-RTE-008` — read-only route visibility;
- `E2E-ROUTE-01` — ambiguity -> runtime recreation -> no redispatch -> reconciliation;
- `E2E-ROUTE-02` — English/Japanese browser route semantics.

Only IDs actually bound to executable files in `specs/test-id-registry.json` count as executable Evidence. Specified-only IDs remain planned requirements.

### Required cross-surface evidence

- root README and EN/JA documentation distinguish published `0.1.0a5` from post-release source preview;
- MCP docs distinguish the five published a5 read-only tools from current source `rpr.get_route_visibility`;
- site/demo contains and executes routing semantics;
- public validator detects missing EN/JA pairs and required route anchors;
- product status records routing as unpromoted source preview;
- formal docs explicitly exclude receiver eligibility/delegation proof;
- claim registry does not mark CLM-13 passing before exact-head CI.

### Trusted assumptions

- receiver eligibility and delegation source-of-truth supplied by the integration are meaningful;
- actor/identity binding supplied by the host is accurate within its deployment boundary;
- the route is not bypassed by an alternate execution path;
- external Evidence sources are sufficiently authoritative for the specific classification claimed.

### Residual risks

- RPR does not determine legal/institutional accountability;
- arbitrary organizations may use different delegation/eligibility systems;
- source-preview compatibility may evolve before a stable release;
- routing metadata does not itself enforce external actors outside RPR;
- Lean does not prove routing semantics;
- customer-specific identity/network/MCP environments require separate evidence.

### Permitted wording before release-level assurance

> “Current RPR source represents bounded Responsibility Routing, preserves declared receiver-eligibility and Residual Owner metadata, and does not infer Authority from route or Evidence transfer. Release-level assurance remains pending exact-head product-quality validation.”

### Stronger wording gate

Do not promote CLM-13 to release-level `passing/E3` until:

- full exact-head CI passes;
- English and Japanese browser route E2E passes;
- current documentation/site/demo/registry audit passes;
- independent review/readback is complete;
- repaired branch is merged and main is read back;
- a fresh release candidate is rebuilt from repaired main.

## 6. Product-quality assurance against recurrence

The audit that introduced CLM-13 identified **cross-surface semantic drift** as a systemic defect class. Future assurance therefore includes process controls, not only behavior tests.

A change that alters state, decision, routing, Authority, Evidence meaning, owner semantics, external-effect claims, or release identity must enumerate affected product surfaces before completion.

The change remains release-blocked until:

1. source semantics are correct;
2. negative tests falsify the previous wrong behavior;
3. persistence/restart behavior is checked;
4. public interfaces are aligned;
5. EN/JA docs and demos are aligned;
6. claim/test registries are updated;
7. CI can detect the same drift class automatically;
8. exact-head evidence is retained.

## 7. Assurance stop conditions

Claim promotion stops if any of the following occurs:

- a required test is missing, skipped, stale, or bound only in prose;
- an invalid/unavailable route still becomes Human Gate without an independently justified human receiver;
- Authority can be inferred from Evidence/capability/route/transport;
- Residual Owner can silently disappear/change;
- route metadata is lost across persistence/restart;
- `write_status_unknown` can silently complete or redispatch;
- source-preview behavior is described as already present in published a5;
- runtime recreation is described as process restart without process-level evidence;
- Lean scope is overstated;
- EN/JA active surfaces materially disagree;
- the candidate head differs from the head that generated retained Evidence.

## 8. Human Gate

Assurance evidence supports a release decision; it does not make the decision. Tag creation, GitHub Release, PyPI publication, and stronger public claims remain explicit human actions after the exact candidate evidence is reviewed.
