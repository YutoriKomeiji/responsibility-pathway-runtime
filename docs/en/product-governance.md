<!--
Document Title: RPR Product Governance
Document Type: Public Product Operations Policy
Status: Active
Header Language: English
Body Language: English
-->

# RPR product governance

## Product source of truth

`YutoriKomeiji/responsibility-pathway-runtime` is the sole source of truth for the RPR product implementation.

The following are maintained here:

- runtime source and tests;
- package metadata and release artifacts;
- public specifications and product documentation;
- English and Japanese product pages;
- CI, Issue Forms, security policy, changelog, and release records;
- user-reported issues and implementation pull requests.

Product fixes must not be applied only to a preparation snapshot in another repository.

## Normal change route

User feedback and defects follow this route:

1. Open or triage an RPR Issue.
2. Create an RPR branch and pull request.
3. Identify every affected product surface before implementation is treated as complete.
4. Run RPR CI and review the evidence against the exact pull-request head.
5. Merge the approved change into RPR `main`.
6. Perform main readback and rebuild any release candidate from the repaired main lineage.
7. Close or link the Issue and include the change in an RPR release when appropriate.

Security vulnerabilities use the private reporting route described in `SECURITY.md`, not a public Issue.

## Cross-surface semantic-drift prevention

RPR is a multi-surface product. A change to a state, decision, route, authority boundary, evidence meaning, owner, external-effect claim, or release identity may affect more than source code.

Before completion, review the applicable surfaces:

- runtime source and serialization;
- persistence and restart/recovery behavior;
- unit and component tests;
- integration and product/system E2E tests;
- MCP, CLI, and other public interfaces;
- English/Japanese documentation pairs;
- site and executable demos;
- claim, test, assurance, and integration registries;
- formal-model scope and non-claims;
- CI drift checks and release validation.

A green local test is not sufficient evidence that these surfaces agree. If CI cannot detect the stale or missing surface introduced by a change class, add the check before release promotion.

Historical release records must remain historical. Current-state checks must distinguish active product documents from archived or release-specific records rather than rewriting history.

## Responsibility Routing boundary

Human Return is a bounded Responsibility Route, not the generic meaning of fail-closed behavior.

A generic evaluator failure, invalid route, unavailable receiver, or unresolved effect must not automatically manufacture a human destination. A neutral hold is valid when no eligible receiver has yet been established.

Evidence transfer, capability, confidence, successful transport, recovered state, or route selection do not create Authority. Routing must preserve unresolved residue and the Residual Owner unless an explicit authorized redesign changes ownership.

## Release-candidate integrity

A release candidate is evidence-bound to its exact source lineage. If source, documentation, tests, claim registries, or CI controls change after a candidate is frozen, do not patch the old candidate forward as if the evidence still applied. Rebuild a fresh candidate from repaired `main`, rerun exact-head validation, and obtain a new Human Gate decision.

## Escalation to the Responsibility Pathway Program

Most fixes and bounded product enhancements remain entirely in RPR.

Escalation to the Responsibility Pathway Program is required when a proposal changes program-level theory or responsibility boundaries, including:

- Responsibility Routing or Human Gate semantics;
- the division of responsibility between RPD, RPE, and RPR;
- canonical pathway states or transition meaning;
- residual ownership semantics;
- assurance or public claim boundaries.

After a program-level decision is adopted, implementation still returns to an RPR pull request. The production code remains canonical in RPR.

## Carryback

RPR may carry release results, evidence summaries, and design-escalation outcomes back to the Responsibility Pathway Program. Carryback records do not turn a program repository snapshot into the product source of truth.
