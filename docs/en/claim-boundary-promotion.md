# Claim Boundary Promotion

RPR treats public claims as evidence-governed states. A current non-claim is not automatically a permanent disclaimer.

RPR distinguishes:

1. **evidence-limited boundaries** that can move when declared evidence is obtained and reviewed; and
2. **permanent responsibility boundaries** that the runtime should not cross by itself.

## Current evidence boundary

RPR 0.1.0a4 is a Public Alpha with verified runtime, persistence, restart/reconciliation, MCP, packaging, browser/Pyodide, selected Windows, and bounded formal-evidence surfaces. This supports the published alpha claims only.

## Promotion criteria

| Current boundary | Evidence that can move it |
|---|---|
| No production/enterprise readiness claim | sustained workload/soak evidence; supported deployment profiles; supervisor/restart/upgrade/rollback evidence; operational monitoring/SLO evidence; reviewed security controls |
| Limited customer-environment validation | reproducible field evidence for declared proxy/TLS/identity/credential/network/OS/container/MCP-client profiles |
| No broad exactly-once claim | target-side transactional or idempotency contract plus independent authoritative readback for the claimed integration profile |
| Tamper-evident ledger only | independently verifiable signing/attestation, external immutability or timestamping, and maintained key/trust governance where claimed |
| No implementation-wide formal conformance | explicit model-to-runtime refinement/conformance relation and reproducible evidence for the claimed runtime surface |

Promotion is explicit, never inferred from age or version number alone.

## Permanent responsibility boundaries

- RPR does not create legal, organizational, or execution authority by itself.
- RPR does not make credentials, identity providers, networks, external systems, or business decisions correct.
- A transport/MCP response is not automatically proof of consequential external effect.
- Final operational and organizational responsibility remains with the responsible human or institution.
- Universal exactly-once behavior cannot be promised for arbitrary remote systems that do not expose the necessary contract.
- Formal proof of an abstract model does not automatically prove the complete Python runtime or deployment.

These are responsibility boundaries, not unfinished features.

## Evidence owners and states

RPR engineering owns declared runtime evidence. Integrators/operators own environment-specific identity, credential, network, bypass-prevention, monitoring, and authoritative readback evidence. Qualified humans/institutions own legal, certification, deployment, and operational authorization decisions.

Where practical, evidence-limited boundaries use `evidence_collecting`, `review_ready`, or `promoted`; permanent boundaries use `permanently_out_of_scope`.
