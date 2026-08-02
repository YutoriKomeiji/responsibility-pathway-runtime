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

Responsibility Pathway Runtime (RPR) is an MIT-licensed software component placed between a host application's decision logic and a consequential external action. It preserves a reconstructable route from proposed action to authority, execution attempt, evidence, repair or reconciliation, and Human Gate return.

```text
host application
  -> proposed action + actor + authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | human gate
  -> evidence retained for reconstruction
```

## Capability map

| Capability | What RPR supplies | What remains outside RPR |
|---|---|---|
| Pathway lifecycle | State model and authorized transitions | Business-policy authorship |
| Execution continuity | Durable operations and attempts | Remote-system transaction guarantees |
| Evidence | Attachment, provenance, and readback workflow | The authoritative external evidence source |
| Human control | Human Gate, repair, resume, reconciliation states | Selection and identity of authorized decision makers |
| Adapters | Bounded local-file, HTTP, message, and MCP paths | Network trust, credentials, and service-specific semantics |
| Recovery | Ambiguous-write preservation and restart continuity | Operational staffing and incident ownership |

## State and evidence principles

| Principle | Required behavior |
|---|---|
| Attempt is not completion | A dispatched write is not treated as a completed effect |
| Evidence closes completion | Completion requires the evidence class defined by the integration |
| Unknown remains unknown | `write_status_unknown` is not rewritten as success without reconciliation |
| Restart does not imply retry | Unresolved attempts are restored without silent redispatch |
| Recovery is explicit | Repair and reconciliation are pathway states, not hidden exception handling |
| Approval is not effect proof | Human approval proves a decision, not the remote result |

## Integration boundary

The host application defines permitted actions, authorization, credential isolation, bypass prevention, independent readback, data handling, deployment approval, and operational ownership. RPR provides mechanisms to retain and enforce the declared pathway; it does not determine whether a particular deployment is lawful, safe, or suitable.

## Optional RPE integration

Responsibility Pathway Engineering (RPE) may provide an external gate decision. RPE does not execute the action or replace RPR execution evidence. Missing, malformed, unsupported, or inapplicable RPE output must remain visible and be handled according to the integration contract.

## License and non-claims

RPR is provided under the [MIT License](../../LICENSE). The license permits use, modification, and distribution subject to its notice requirements and provides the software without warranty.

RPR is not a legal-responsibility engine, policy author, identity provider, secret manager, production gateway, certification, universal transaction coordinator, or guarantee of exactly-once effects. The public alpha is not represented as fit for every environment or purpose.
