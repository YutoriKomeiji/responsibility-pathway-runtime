# Responsibility Routing migration baseline

Status: design baseline for DAN-96. This document does not change runtime behavior or publish a new release.

## Purpose

RPR currently preserves a durable responsibility pathway through approval, execution, uncertain external effect, reconciliation, repair, and resume. The current public API and state model make Human Gate and `human_return_point` first-class concepts. DAN-96 generalizes the top-level abstraction from Human Return to Responsibility Routing while preserving Human Return as a bounded route subtype.

This migration must remain backward-compatible with the current Public Alpha surface until an explicit release decision is made.

## Core rule

A responsibility-bearing transition is valid only when the selected route preserves the information needed for the next holder to act within legitimate authority and without losing unresolved residue.

Evidence transfer does not create Authority. Capability, model confidence, agent consensus, tool success, recovered checkpoint state, or receipt of a handoff does not silently extend delegation.

## Route outcomes

The initial design vocabulary is:

- `CONTINUE_AUTONOMOUSLY`
- `AI_RESOLVE_WITHIN_DELEGATION`
- `HOLD_FOR_RECONCILIATION`
- `BOUNDED_HUMAN_RETURN`
- `STOP_AND_PRESERVE_RESIDUE`

These names are design-level outcomes, not yet public runtime enum values.

## Required route payload

A future Responsibility Route record should preserve, at minimum:

- source holder or current responsibility state;
- destination / route class;
- receiver eligibility;
- Authority class and delegation scope;
- unresolved payload / residue;
- evidence and provenance semantics;
- allowed next actions;
- reevaluation / closure condition;
- timing or expiry where material;
- Residual Owner.

## Current RPR compatibility map

### `PathwayDefinition.human_return_point`

Classification: `NARROW_BUT_VALID`.

The field remains valid for the bounded human-return route. It should not continue to represent the existence of all valid return/routing options.

Migration direction: retain the field for compatibility and introduce route-level metadata separately. Do not destructively rename it in the first migration.

### `PathwayState.HUMAN_GATE`

Classification: `NARROW_BUT_VALID`.

The state is still necessary when a pathway requires an explicit human decision or authority. It is not a universal routing destination.

Migration direction: preserve the state and define it as one route-specific runtime state. Do not infer that all non-autonomous cases must enter `HUMAN_GATE`.

### `RuntimeDecision.HUMAN_GATE`

Classification: `NARROW_BUT_VALID`.

The decision remains meaningful for bounded human-return cases but is too narrow as the only non-autonomous routing decision.

Migration direction: future routing logic should distinguish human return from reconciliation hold, delegated AI resolution, and stop/preserve outcomes. Compatibility adapters may continue to map a bounded human route to `HUMAN_GATE`.

### `InspectionResult.human_return_available`

Classification: `NARROW_BUT_VALID`.

This answers only whether the legacy human-return surface is available.

Migration direction: retain it for compatibility and add a route-oriented inspection result later, e.g. route availability / candidate routes / next eligible holder. Do not reinterpret the boolean as general Returnability.

### explicit authority fields

Current examples include `approval_authority`, `stop_authority`, and `resume_authority`.

Classification: `STILL_VALID`.

Migration direction: reuse these semantics. Responsibility Routing must never infer Authority from evidence, capability, confidence, transport success, or route selection.

### owner fields

Current examples include `decision_owner`, `evidence_owner`, `repair_owner`, and `residual_owner`.

Classification: `STILL_VALID`.

Migration direction: preserve them. A future route record may reference or narrow these owners, but routing must not silently replace the Residual Owner merely because a new receiver was selected.

### `WRITE_STATUS_UNKNOWN` and reconciliation

Classification: `STILL_VALID`.

This is already a non-human route condition: unresolved effect state remains owned until independent readback / reconciliation can classify it.

Migration direction: model this explicitly as `HOLD_FOR_RECONCILIATION` at the routing layer while preserving the current runtime state and reconciliation machinery.

### repair / `READY_TO_RESUME` / resume authority

Classification: `STILL_VALID`.

Repair completion does not create resume Authority. A restored execution path and permission to resume remain separate.

Migration direction: keep the existing distinction and require reevaluation when route-relevant material state has changed.

### inspection / diagnostics / read-only MCP surfaces

Classification: `STILL_VALID`, with route visibility extension required.

Migration direction: add route state and receiver-eligibility information without removing existing fields in the first compatibility cycle.

## Failure classes

The migration must make the following failures testable:

- **False Autonomy** — execution remains autonomous after delegation/Authority or unresolved-residue conditions require another route.
- **Proxy Return** — work is sent to an AI/system that lacks the required Authority or eligibility, while appearing to have been safely returned.
- **False Escalation** — work is sent to a human even though an explicitly delegated route could resolve it safely, causing unnecessary intervention burden.
- **Nominal Human Return** — a human is named or notified but lacks the capability, context, Authority, or bounded next-decision scope needed to actually take responsibility.

## Smallest safe implementation slice

The first implementation slice should be additive and internal-facing:

1. define route classes / outcomes without changing existing state values;
2. define a serializable Responsibility Route record carrying eligibility, delegation, unresolved residue, allowed actions, closure condition, and Residual Owner;
3. attach the record to pathway/runtime inspection without changing dispatch semantics;
4. add compatibility mapping from bounded human route to existing Human Gate / `human_return_point` behavior;
5. add tests proving Evidence transfer and receiver capability do not create Authority;
6. add tests proving `WRITE_STATUS_UNKNOWN` maps to reconciliation hold rather than blind retry or forced Human Gate;
7. only after readback, decide whether new public enums or storage migrations are warranted.

## Non-goals for the first slice

- no destructive rename of Human Gate / `human_return_point`;
- no claim that AI bears legal or institutional accountability;
- no automatic Authority transfer;
- no replacement of execution, reconciliation, repair, or resume state machines;
- no public release or compatibility break.

## Stop gate

Before changing persistent schemas, public enums, CLI/MCP output contracts, or release artifacts, perform a compatibility readback and explicit Human Gate review.