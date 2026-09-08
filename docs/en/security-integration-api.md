<!--
Document Title: RPR Security Integration and API Boundary
Document Type: Public Product Guide
Status: Public Alpha
Version: 0.1.0a6
Freeze ID: RPR-CF-2026-08-02-01
Header Language: English
Body Language: English
-->

# Security, integration, and API boundary

RPR is an MIT-licensed control and evidence component, not a complete security perimeter or managed security service. The project publishes mechanisms and tested behavior; the integrator is responsible for the security architecture and deployment decisions around them.

## Trust boundaries

| Domain | Must not be assumed from another domain |
|---|---|
| Human or institutional Authority | Identity or authorization supplied by the host application |
| Receiver capability | Receiver eligibility or delegated Authority |
| Evidence transfer | Authority transfer or ownership transfer |
| Host application | Correctness of RPR state or remote-system effects |
| RPR state and evidence store | Trustworthiness of an adapter or external service |
| Adapter process | Independent readback or business authorization |
| Credential store | Permission to perform a particular business action |
| Remote system | Correctness of callback or local execution result |
| Independent readback source | Correctness of the proposed action or policy |
| Optional RPE service | Execution success, completion evidence, or an automatically valid human destination |

An adapter return value is not automatically independent readback. A successful transport or route selection is not Authority.

## Integration contract

| Contract area | Integration must define |
|---|---|
| Action surface | Accepted action and actor schemas |
| Authority | Authorization, delegation source-of-truth, and bounded Human Gate requirements |
| Responsibility Routing | Receiver eligibility, route class, unresolved payload, bounded next actions, closure/reevaluation condition, Residual Owner |
| Identity | Stable operation and idempotency identity |
| State | Permitted transitions and failure handling |
| Dispatch | Timeout, cancellation, and retry behavior |
| Evidence | Authoritative readback source and matching rules |
| Ambiguity | `write_status_unknown`, hold, repair, and reconciliation handling |
| Ownership | Repair, resume, incident, and residual-effect owners |
| Data | Classification, retention, export, and deletion rules |
| Observability | Monitoring, alerting, and incident routes |

## Fail-closed routing rule

`Fail closed` does not mean `send to a human`.

A missing evaluator, malformed contract, invalid route, ineligible receiver, or unresolved external effect must not create a human destination by inference. The safe result may be a neutral hold until an eligible receiver and the required Authority are established.

Human Return remains valid when an explicitly configured bounded Human Gate is required. Evidence transfer, receiver capability, confidence, tool success, successful transport, recovered state, or route selection do not create Authority.

## Host security controls

RPR should be deployed inside an architecture that provides authenticated users and services, least-privilege credentials, network policy, endpoint and command allow-lists, protected persistence, log redaction, supply-chain controls, monitoring, and bypass prevention.

The host application must not expose a parallel execution path that skips required pathway admission, route eligibility, Authority checks, or evidence handling for the same consequential action.

## API stability

`0.1.0a6` is the current published public alpha. Pin the version and test serialized state, CLI behavior, adapter configuration, and migration procedures before upgrading. Repository source may contain later work that is not part of the published package until a later release is rebuilt and approved. Incompatible corrections may occur before a stable release.

## Credentials and vulnerability reports

Use placeholders in documentation and examples. Supply credentials through an external secret mechanism and scope them to the smallest permitted operation set. Do not place secrets in evidence, exceptions, diagnostic bundles, Issues, or release artifacts.

Report potentially exploitable details through the private route in [`SECURITY.md`](../../SECURITY.md), not a public Issue.

## License boundary

The [MIT License](../../LICENSE) permits use, modification, and distribution subject to its terms and provides the software without warranty. Nothing in this guide is a security warranty, certification, indemnity, or assurance that a particular integration is secure or fit for production.
