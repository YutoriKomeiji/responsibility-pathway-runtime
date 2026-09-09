# Historical record — Responsibility Routing compatibility baseline

Lifecycle: `HISTORICAL`

This file preserves the compatibility baseline that accompanied the transition into Public Alpha `0.1.0a6`. Any statement below about what is “current”, “published”, or “source preview” reflects the state when that text was produced. For current product state, use `product-status.json` and the active documentation indexes.

---

# Responsibility Routing compatibility baseline

Status: implemented and published in Public Alpha `0.1.0a6`.

## Purpose

Responsibility Pathway Runtime (RPR) preserves a durable responsibility pathway through approval, execution, uncertain external effect, reconciliation, repair, and resume. The first public-alpha design made Human Gate and `human_return_point` prominent. Responsibility Routing generalizes the top-level responsibility-transfer model while preserving Human Return as one bounded route.

The compatibility goal is additive change: keep existing state values, persistence, authority fields, and legacy serialization valid while adding route semantics that do not silently create Authority.

## Core rule

A responsibility-bearing transition is valid only when the selected route preserves enough information for the next holder to act within legitimate Authority and without losing unresolved residue.

Evidence transfer does not create Authority. Receiver capability, model confidence, agent consensus, tool success, route visibility, recovered checkpoint state, or receipt of a handoff does not silently extend delegation.

## Published route vocabulary

`ResponsibilityRouteClass` defines:

- `CONTINUE_AUTONOMOUSLY`
- `AI_RESOLVE_WITHIN_DELEGATION`
- `HOLD_FOR_RECONCILIATION`
- `BOUNDED_HUMAN_RETURN`
- `STOP_AND_PRESERVE_RESIDUE`

These values are published in the `0.1.0a6` source/package model, but they are not a promise that every class is automatically selected by runtime dispatch logic. The compatibility cycle intentionally classifies only states whose mapping is justified by existing RPR semantics.

## Route record

`ResponsibilityRoute` can retain route class, source holder, destination, receiver eligibility, Authority class, delegation scope, unresolved payload/residue, allowed next actions, closure and reevaluation conditions, Residual Owner, and optional expiry.

The record is attached additively to `PathwayDefinition`. When no route is supplied, the legacy serialized definition shape is preserved. Existing SQLite schema version 1 remains unchanged because the optional route is stored inside the existing definition JSON.

The route types were not promoted through the top-level `rpr` Python export surface in this compatibility baseline. The externally documented inspection contract was the separate read-only MCP tool described below.

## Compatibility mapping

Only two current-state mappings were automatic in this compatibility baseline:

- `PathwayState.HUMAN_GATE` -> `bounded_human_return`
- `PathwayState.WRITE_STATUS_UNKNOWN` -> `hold_for_reconciliation`

Other states remained unclassified until their routing semantics were explicitly designed and reviewed.

## Human Return remained valid, but bounded

`PathwayDefinition.human_return_point`, `PathwayState.HUMAN_GATE`, `RuntimeDecision.HUMAN_GATE`, and `InspectionResult.human_return_available` were retained as narrow-but-valid Human Return surfaces. Generic fail-closed conditions did not manufacture a Human Gate.

## Authority and ownership

Existing explicit Authority fields and owner fields remained valid. Responsibility Routing did not grant execution or reconciliation Authority from route destination, receiver capability, evidence, or visibility. The pathway Residual Owner remained preserved absent a separately authorized ownership change.

## Unknown external effects

`write_status_unknown` remained a first-class unresolved state and mapped to `hold_for_reconciliation`; it was not converted into success, failure, blind retry, or forced Human Return. Repair completion did not create resume Authority.

## Read-only route visibility

Published `0.1.0a6` included `rpr.get_route_visibility(pathway_id)` in the local read-only MCP server. The tool could expose current state, justified compatibility route, persisted declared route, Human Return point, Residual Owner, and `authority_inferred: false`. It could not approve, execute, reconcile, repair, resume, select a receiver, or mutate pathway state.

## Failure classes covered by the design

- **False Autonomy**
- **Proxy Return**
- **False Escalation**
- **Nominal Human Return**

## Verification boundary

The compatibility slice was covered by unit, component, MCP integration, runtime/product, browser/Pyodide, package, bilingual, reproducibility, and selected Lean checks. Lean 4 verified selected pathway state-machine invariants only; route metadata, receiver eligibility, and Responsibility Routing selection semantics were not fully formally proved.

## Compatibility and release boundary

This migration did not destructively rename Human Gate or `human_return_point`, did not change SQLite schema version 1, did not add mutating MCP tools, and did not claim that AI bears legal or institutional accountability.
