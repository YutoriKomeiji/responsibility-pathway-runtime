<!--
Document Title: RPR Product Scope and Architecture
Document Type: Public Product Guide
Status: Public Alpha Candidate
Version: 0.1.0a2
Freeze ID: RPR-CF-2026-08-01-02
Header Language: English
Body Language: English
-->

# Product scope and architecture

## Product role

Responsibility Pathway Runtime (RPR) sits between a host application's decision logic and a consequential external action. It preserves a reconstructable route from proposed action to declared authority, pathway state, execution attempt, independent readback, repair or reconciliation, and Human Gate return.

```text
host application
  -> proposed action + actor + authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | human gate
  -> evidence retained for reconstruction
```

## Frozen alpha capability groups

The `RPR-CF-2026-08-01-02` candidate includes:

- pathway lifecycle and authorized transitions;
- persistent pathway and execution-attempt continuity;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and MCP subprocess paths;
- fail-closed ambiguous-write handling;
- crash/restart and duplicate-dispatch protections exercised in the frozen rehearsal;
- backup, restore, diagnostics, removal, and customer-data retention procedures;
- wheel and source-distribution installation with reproducible artifacts.

## State and evidence principles

- An attempted write is not completion.
- Completion requires the evidence class defined by the host integration, normally independent readback.
- An unknown remote result remains `write_status_unknown`; it must not be rewritten as success.
- Restart must preserve unresolved attempts and must not silently dispatch them again.
- Repair and reconciliation are explicit pathway states, not hidden exception handling.
- Human approval is evidence of a decision, not proof that a remote effect occurred.

## Adapter boundary

Adapters provide bounded execution paths. They do not own business authorization, credentials, network trust, service semantics, or the definition of sufficient readback. The host integration must define:

- which actions are allowed;
- who may authorize them;
- how credentials are isolated;
- how bypass is prevented;
- what independent source proves the effect;
- which ambiguous states require stop, repair, or human return.

## Optional RPE integration

Responsibility Pathway Engineering (RPE) may supply an external gate decision. RPR must treat RPE absence, malformed output, unsupported versions, and inapplicable results visibly and fail closed according to the integration contract. RPE does not execute the action and does not replace RPR's execution evidence.

## Non-claims

RPR is not a legal-responsibility engine, policy author, identity provider, secret manager, production gateway, universal transaction coordinator, certification, or guarantee of exactly-once effects. The alpha candidate is not declared universally production ready.
