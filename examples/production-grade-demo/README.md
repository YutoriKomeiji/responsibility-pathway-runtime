# Production-Grade Demo: Governed Supplier Payment Release

> Public alpha scenario for Responsibility Pathway Runtime `0.1.0a2`.
>
> This is not a toy counter, mock approval button, or simulated success-only walkthrough. It is an executable integration scenario designed to exercise persistent state, Human Gate return, external-write ambiguity, independent readback, restart continuity, repair, and reconciliation using the actual RPR runtime interfaces included in the frozen candidate.

## Business scenario

A finance automation service receives an approved supplier invoice and proposes a payment instruction to an allow-listed payment API. The payment is consequential and may not be repeated merely because the caller timed out.

The host application must preserve:

- the proposed action and declared authority;
- the identity of the operation and each execution attempt;
- the Human Gate decision that permits dispatch;
- the external request and bounded response evidence;
- independent readback from the payment-status endpoint;
- an explicit unresolved state when the write result is ambiguous;
- restart-safe recovery without duplicate dispatch;
- reconciliation, repair, resume, and residual ownership.

## Why this is a real demo

The scenario uses the same product paths covered by the frozen candidate tests:

- persistent pathway and execution-attempt stores;
- authorized runtime transitions;
- allow-listed HTTP execution;
- idempotency identity and duplicate-dispatch prevention;
- `write_status_unknown` fail-closed handling;
- independent readback before completion;
- Human Gate return and resume;
- process restart during unresolved execution;
- reconciliation and explicit repair decisions;
- operational diagnostics and retained evidence.

The external payment service is represented by a deterministic local integration fixture so the demo can reproduce normal completion, remote rejection, timeout after acceptance, unavailable readback, and restart conditions without contacting a real financial system. The fixture is an integration test double, but the RPR runtime, persistence, state transitions, executor path, diagnostics, and recovery behavior are real product code.

## Roles and responsibility boundary

| Role | Responsibility |
|---|---|
| Host finance application | Authentication, invoice validity, credentials, network policy, payment-domain authorization, bypass prevention |
| Human approver | Final payment authorization and exceptional reconciliation decisions |
| RPR | Pathway state, execution-attempt continuity, evidence retention, stop/repair/resume boundaries |
| Payment API fixture | Deterministic external-effect and readback behavior for reproducible integration testing |
| Operator | Environment configuration, backup, diagnostics, incident handling, retained customer data |

RPR does not determine whether the invoice is legally payable, authenticate the approver, protect credentials, or guarantee exactly-once behavior across arbitrary remote systems.

## Demonstration paths

### Path A — Authorized completion

1. Register the payment pathway.
2. Return to Human Gate before dispatch.
3. Record explicit approval.
4. Dispatch once with a stable idempotency identity.
5. Read payment status independently.
6. Complete only after readback confirms the intended payment.
7. Print the retained pathway, attempt, authority, and evidence records.

Expected result: completed pathway with readback evidence and one external dispatch.

### Path B — Timeout after remote acceptance

1. The fixture accepts the payment and persists the external effect.
2. The connection fails before RPR receives a conclusive response.
3. RPR records `write_status_unknown` rather than success or safe retry.
4. The process is terminated and restarted.
5. RPR restores the unresolved attempt and prevents blind redispatch.
6. Reconciliation queries the independent status endpoint.
7. The operator records the reconciliation outcome and resumes or repairs under an explicit authority decision.

Expected result: no duplicate payment, visible ambiguity, retained attempt continuity, explicit resolution evidence.

### Path C — Readback unavailable

1. Dispatch receives an accepted response.
2. Independent readback is unavailable.
3. Completion remains blocked.
4. Diagnostics expose the unresolved pathway and required operator action.
5. A later readback or approved repair route resolves the state.

Expected result: accepted is not treated as verified completion.

### Path D — Human rejection

1. Register the proposed payment.
2. Return to Human Gate.
3. Record rejection with reason and authority identity.
4. Confirm that no external dispatch occurred.

Expected result: terminated or held pathway with zero external effects.

## Required demo package

The public repository export must contain:

```text
examples/production-grade-demo/
├── README.md
├── payment_service.py
├── run_demo.py
├── scenarios/
│   ├── authorized-completion.json
│   ├── timeout-after-acceptance.json
│   ├── readback-unavailable.json
│   └── human-rejection.json
├── expected/
│   ├── authorized-completion.json
│   ├── timeout-after-acceptance.json
│   ├── readback-unavailable.json
│   └── human-rejection.json
└── tests/
    └── test_demo_scenarios.py
```

The scripts must call the shipped RPR package; they must not reimplement the pathway state machine inside the demo.

## Acceptance criteria

The demo is release-eligible only when all of the following pass in a clean environment:

- installs from the frozen wheel rather than the RPP source tree;
- runs without network access outside localhost;
- uses temporary directories unless an explicit state directory is supplied;
- produces deterministic machine-readable results;
- proves only one dispatch in the timeout-after-acceptance scenario;
- survives a real subprocess restart;
- exposes unresolved work through the product diagnostics path;
- contains no real credentials, endpoints, personal data, or internal repository links;
- has automated tests that compare retained state and evidence with expected outputs;
- documents which elements are product behavior and which are deterministic external fixtures.

## Quality and claim boundary

Passing this demo verifies the declared scenario in the tested environment. It does not establish production readiness for a real payment system, financial regulatory compliance, credential security, universal exactly-once delivery, or suitability for a specific organization.

A real deployment must supply its own authenticated authorization source, credential isolation, network controls, independent external readback, operational ownership, and incident procedures.
