<!--
Document Title: RPR Product Scope and Architecture
Document Type: Public Product Guide
Status: Public Alpha with Post-Release Source Preview
Version: 0.1.0a5
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Product scope and architecture

## Product role

Responsibility Pathway Runtime (RPR) is an MIT-licensed software component placed between a host application's decision logic and a consequential external action. It preserves a reconstructable route from proposed action to declared Authority, execution attempt, evidence, reconciliation/repair/resume, and Responsibility Routing. Human Return is one bounded route rather than the generic destination for every fail-closed condition.

```text
host application
  -> proposed action + actor + declared Authority
  -> pathway admission and state transition
  -> bounded adapter execution
  -> independent readback
  -> complete | repair | resume | reconcile | hold | bounded human gate
  -> responsibility route + evidence retained for reconstruction
```

## Capability map

| Capability | What RPR supplies | What remains outside RPR |
|---|---|---|
| Pathway lifecycle | State model and authorized transitions | Business-policy authorship |
| Execution continuity | Durable operations and attempts | Remote-system transaction guarantees |
| Evidence | Attachment, provenance, and readback workflow | The authoritative external evidence source |
| Responsibility Routing | Route metadata, eligibility state, bounded next actions, closure/reevaluation conditions, Residual Owner | Receiver eligibility source-of-truth, organizational delegation legitimacy, final legal/institutional accountability |
| Human control | Explicit configured Human Gate, repair, resume, reconciliation states | Selection and identity of authorized decision makers |
| Adapters | Bounded local-file, HTTP, message, and outbound MCP paths | Network trust, credentials, and service-specific semantics |
| Recovery | Ambiguous-write preservation and restart continuity | Operational staffing and incident ownership |

## MCP position in the architecture

RPR can govern outbound MCP calls from the client side. A host application proposes an MCP tool call, RPR retains actor, declared Authority, pathway state, server/tool binding, execution attempt, and relevant route metadata, and an admitted transport performs `tools/call`.

```text
host application or agent
  -> RPR pathway, Authority, and route checks
  -> admitted MCP server/tool binding
  -> local subprocess and stdio transport
  -> tools/call result
  -> independent readback when required
  -> complete | write_status_unknown | repair | reconcile | bounded human gate | hold
```

Published `0.1.0a5` also includes the local read-only `rpr-mcp` inspection server. Current post-`0.1.0a5` source adds `rpr.get_route_visibility`; that tool is source-preview work pending a later release decision. Remote MCP services, hosted transports, enterprise identity, and service-specific readback require environment-specific evaluation.

## State, route, and evidence principles

| Principle | Required behavior |
|---|---|
| Attempt is not completion | A dispatched write is not treated as a completed effect |
| Evidence closes completion | Completion requires the evidence class defined by the integration |
| Unknown remains unknown | `write_status_unknown` is not rewritten as success without reconciliation |
| Restart does not imply retry | Unresolved attempts are restored without silent redispatch |
| Recovery is explicit | Repair and reconciliation are pathway states, not hidden exception handling |
| Approval is not effect proof | Human approval proves a decision, not the remote result |
| MCP response is not effect proof | A successful `tools/call` response does not replace authoritative readback for a consequential effect |
| Fail-closed is not automatically Human Gate | Invalid route, unavailable evaluator, or unknown receiver may require neutral hold |
| Evidence transfer is not Authority transfer | Capability, route selection, transport success, or recovered state do not create Authority |
| Residue remains owned | Routing must preserve unresolved payload and Residual Owner unless an explicit authorized redesign changes ownership |

## Integration boundary

The host application defines permitted actions, authentication/authorization, receiver eligibility, delegation source-of-truth, credential isolation, bypass prevention, MCP server selection, tool permissions, independent readback, data handling, deployment approval, and operational ownership. RPR provides mechanisms to retain and enforce the declared pathway; it does not determine whether a particular deployment is lawful, safe, or suitable.

## Optional RPE integration

Responsibility Pathway Engineering (RPE) may provide an external gate decision. RPE does not execute the action or replace RPR execution evidence. Missing, malformed, unsupported, or inapplicable RPE output must fail closed without becoming implicit permission or an invented human destination. An explicitly configured high-impact Human Gate remains valid when its own authority conditions require one.

## Published-release versus source-preview boundary

The published package is `0.1.0a5`. Repository source may contain post-release Responsibility Routing work before a later package is approved. Source availability does not by itself promote the package contract, release evidence, or support maturity.

A later release requires a fresh candidate rebuilt from repaired `main`, exact-head test/document/claim validation, and explicit Human Gate approval.

## License and non-claims

RPR is provided under the [MIT License](../../LICENSE). The license permits use, modification, and distribution subject to its notice requirements and provides the software without warranty.

RPR is not a legal-responsibility engine, policy author, identity provider, secret manager, production gateway, MCP trust oracle, certification, universal transaction coordinator, or guarantee of exactly-once effects. The selected Lean model proves bounded state-transition invariants; it does not formally prove Responsibility Routing receiver eligibility or delegation semantics. The Public Alpha is not represented as fit for every environment or purpose.
