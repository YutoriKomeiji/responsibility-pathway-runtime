# Claim Boundary Promotion

RPR treats public claims as evidence-governed states. A current non-claim is not automatically a permanent disclaimer.

RPR distinguishes:

1. **evidence-limited boundaries** that can move when declared evidence is obtained and reviewed; and
2. **permanent responsibility boundaries** that the runtime should not cross by itself.

## Current evidence boundary

RPR `0.1.0a6` is the current published Public Alpha. Its released surface includes the bounded Responsibility Routing work, route visibility, runtime/persistence/restart/reconciliation, MCP, packaging, browser/Pyodide, bounded Windows field evidence, and bounded formal-evidence surfaces described by the current product documentation. These support the published alpha claims only.

The `0.1.0a6` release does not promote RPR to production/enterprise readiness, universal organizational routing, legal/compliance authority, universal exactly-once behavior, or implementation-wide formal conformance. Future source changes remain unreleased until separately validated and promoted.

## Promotion criteria

| Current boundary | Evidence that can move it |
|---|---|
| No production/enterprise readiness claim | sustained workload/soak evidence; supported deployment profiles; supervisor/restart/upgrade/rollback evidence; operational monitoring/SLO evidence; reviewed security controls |
| Limited customer-environment validation | reproducible field evidence for declared proxy/TLS/identity/credential/network/OS/container/MCP-client profiles |
| Responsibility Routing is released only within the documented Public Alpha contract | broader integration evidence for declared receiver/delegation profiles, route-level operational evidence, claim/test traceability, exact-head package/CI evidence, and explicit promotion review for any expanded claim |
| No broad exactly-once claim | target-side transactional or idempotency contract plus independent authoritative readback for the claimed integration profile |
| Tamper-evident ledger only | independently verifiable signing/attestation, external immutability or timestamping, and maintained key/trust governance where claimed |
| No implementation-wide formal conformance | explicit model-to-runtime refinement/conformance relation and reproducible evidence for the claimed runtime surface |

Promotion is explicit, never inferred from age, version number, source availability, or a green subset of tests alone.

## Permanent responsibility boundaries

- RPR does not create legal, organizational, or execution Authority by itself.
- Responsibility Routing does not create Authority merely because a receiver is capable, selected, notified, or has received evidence.
- Human Return is a bounded Responsibility Route, not the generic fallback for every fail-closed condition.
- An unresolved or invalid route may correctly remain on neutral hold until receiver eligibility and Authority are established.
- RPR does not make credentials, identity providers, networks, external systems, or business decisions correct.
- A transport/MCP response is not automatically proof of consequential external effect.
- Residual Owner is not silently replaced by route selection or successful transfer.
- Final legal/institutional accountability remains with the responsible human or institution under the surrounding system.
- Universal exactly-once behavior cannot be promised for arbitrary remote systems that do not expose the necessary contract.
- Formal proof of an abstract state model does not automatically prove the complete Python runtime, Responsibility Routing receiver eligibility/delegation semantics, or deployment.

These are responsibility boundaries, not unfinished features.

## Evidence owners and states

RPR engineering owns declared runtime and route-mechanism evidence. Integrators/operators own environment-specific identity, receiver eligibility, delegation source-of-truth, credential, network, bypass-prevention, monitoring, and authoritative readback evidence. Qualified humans/institutions own legal, certification, deployment, and operational authorization decisions.

Where practical, evidence-limited boundaries use `evidence_collecting`, `review_ready`, or `promoted`; permanent boundaries use `permanently_out_of_scope`.
