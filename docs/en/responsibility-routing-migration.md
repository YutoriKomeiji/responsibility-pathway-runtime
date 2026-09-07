# Responsibility Routing compatibility baseline

Status: implemented source-preview compatibility baseline. The currently published PyPI line remains `0.1.0a5`; this document does not itself publish a new release.

## Purpose

Responsibility Pathway Runtime (RPR) preserves a durable responsibility pathway through approval, execution, uncertain external effect, reconciliation, repair, and resume. The first public-alpha design made Human Gate and `human_return_point` prominent. Responsibility Routing generalizes the top-level responsibility-transfer model while preserving Human Return as one bounded route.

The compatibility goal is additive change: keep existing state values, persistence, authority fields, and legacy serialization valid while adding route semantics that do not silently create Authority.

## Core rule

A responsibility-bearing transition is valid only when the selected route preserves enough information for the next holder to act within legitimate Authority and without losing unresolved residue.

Evidence transfer does not create Authority. Receiver capability, model confidence, agent consensus, tool success, route visibility, recovered checkpoint state, or receipt of a handoff does not silently extend delegation.

## Implemented source-level route vocabulary

`ResponsibilityRouteClass` currently defines:

- `CONTINUE_AUTONOMOUSLY`
- `AI_RESOLVE_WITHIN_DELEGATION`
- `HOLD_FOR_RECONCILIATION`
- `BOUNDED_HUMAN_RETURN`
- `STOP_AND_PRESERVE_RESIDUE`

These values exist in the source model, but they are not a promise that every class is already selected automatically by runtime dispatch logic. The first compatibility cycle intentionally classifies only states whose mapping is already justified by existing RPR semantics.

## Implemented route record

`ResponsibilityRoute` can retain:

- route class;
- source holder;
- destination;
- receiver eligibility;
- Authority class;
- delegation scope;
- unresolved payload / residue;
- allowed next actions;
- closure condition;
- reevaluation condition;
- Residual Owner;
- optional expiry.

The record is attached additively to `PathwayDefinition`. When no route is supplied, the legacy serialized definition shape is preserved. Existing SQLite schema version 1 remains unchanged because the optional route is stored inside the existing definition JSON.

The route types are not currently promoted through the top-level `rpr` Python export surface. The externally documented source-preview inspection contract is the separate read-only MCP tool described below.

## Implemented compatibility mapping

Only two current-state mappings are automatic:

- `PathwayState.HUMAN_GATE` -> `bounded_human_return`
- `PathwayState.WRITE_STATUS_UNKNOWN` -> `hold_for_reconciliation`

Other states remain unclassified until their routing semantics are explicitly designed and reviewed. In particular, completed, repair-ready, or running state is not automatically converted into a new responsibility route merely because a route class exists.

## Human Return remains valid, but bounded

### `PathwayDefinition.human_return_point`

Classification: `NARROW_BUT_VALID`.

The field remains valid when a concrete Human Return is required. It is no longer treated as a universal prerequisite for non-human responsibility routes.

### `PathwayState.HUMAN_GATE`

Classification: `NARROW_BUT_VALID`.

The state remains valid for a real human-held decision or Authority boundary. It is not the generic destination for every invalid configuration, unavailable evaluator, ineligible receiver, or unresolved external effect.

### `RuntimeDecision.HUMAN_GATE`

Classification: `NARROW_BUT_VALID`.

A high-impact action with a configured approval authority and concrete return point can still require Human Gate. Generic fail-closed conditions use `HOLD` unless a valid Human Gate is independently justified.

### `InspectionResult.human_return_available`

Classification: `NARROW_BUT_VALID`.

This continues to report the legacy Human Return surface only. It must not be interpreted as general route availability or Returnability.

## Receiver eligibility and false escalation

An active route with an ineligible receiver, invalid route payload, Residual Owner mismatch, or missing bounded action is invalid and held for definition repair. `REQUIRES_REEVALUATION` is also held until eligibility is rechecked.

These conditions do not manufacture a Human Gate. Naming a human is not a safe fallback when receiver eligibility, Authority, context, or bounded next-decision scope has not been established.

## RPE unavailability and contract failure

RPE unavailability, adapter failure, or contract mismatch remains fail-closed, but it does not by itself prove that a human receiver is the correct route. The neutral result is `HOLD`.

If local pathway inspection independently requires a valid Human Gate—for example, a configured high-impact action—the more restrictive Human Gate decision still wins when results are combined.

## Authority and ownership

Existing explicit Authority fields such as `approval_authority`, `stop_authority`, and `resume_authority` remain valid. Existing owner fields such as `decision_owner`, `evidence_owner`, `repair_owner`, and `residual_owner` remain valid.

Responsibility Routing does not grant execution or reconciliation Authority from route destination, receiver capability, evidence, or visibility. The route must preserve the pathway Residual Owner unless ownership is explicitly redesigned through a separately authorized change.

## Unknown external effects

`write_status_unknown` remains a first-class unresolved state. The route visibility layer reports it as `hold_for_reconciliation`; it is not converted into success, failure, blind retry, or forced Human Return.

Independent readback / reconciliation remains responsible for classifying the external effect. Repair completion still does not create resume Authority.

## Read-only route visibility

The source preview includes `rpr.get_route_visibility(pathway_id)` in the local read-only MCP server. The result can expose:

- current state;
- justified compatibility route, when one exists;
- persisted declared route, when present;
- Human Return point;
- Residual Owner;
- `authority_inferred: false`.

The tool cannot approve, execute, reconcile, repair, resume, select a receiver, or mutate pathway state.

## Failure classes covered by the design

- **False Autonomy** — execution continues after delegation, Authority, eligibility, or unresolved-residue conditions require another route.
- **Proxy Return** — work is sent to an AI/system that lacks required Authority or eligibility while appearing safely returned.
- **False Escalation** — work is sent to a human merely because another component failed, without evidence that Human Return is the valid route.
- **Nominal Human Return** — a human is named or notified but lacks Authority, context, eligibility, or bounded next-decision scope.

## Verification layers

The compatibility slice is covered through multiple layers:

- unit tests for route serialization, legacy positional/wire compatibility, route validation, Authority non-propagation, and compatibility mapping;
- component tests for SQLite persistence and route visibility;
- MCP integration tests for the separate read-only route tool and database byte invariance;
- runtime/product tests for fail-closed RPE fallback, high-impact Human Gate preservation, ambiguous writes, restart, reconciliation, and duplicate-dispatch prevention;
- browser/Pyodide tests for the route-visible live demo;
- package build, clean-install, structural/bilingual, reproducibility, and formal state-model checks in CI.

Lean 4 currently verifies selected pathway state-machine invariants. Route metadata, receiver eligibility, and Responsibility Routing selection semantics are not yet formally proved by the Lean layer.

## Compatibility and release boundary

This migration does not destructively rename Human Gate or `human_return_point`, does not change SQLite schema version 1, does not add mutating MCP tools, and does not claim that AI bears legal or institutional accountability.

Source integration is not the same as binary publication. The currently published package remains `0.1.0a5` until a separately approved release promotion is completed and read back.