# Production-Grade Demo: Governed Supplier Payment Release

> Executable integration scenario for the current RPR repository source. Published package baseline: `0.1.0a5`; current source may include post-`0.1.0a5` Responsibility Routing work that is not part of the published wheel.
>
> This is not a simulated success-only walkthrough. It exercises persistent state, configured Human Gate approval, external-write ambiguity, independent readback, runtime recreation over durable SQLite state, reconciliation, and duplicate-dispatch prevention using the actual RPR runtime interfaces. The payment provider is a deterministic local integration fixture.

## Business scenario

A finance automation service receives an approved supplier invoice and proposes a payment instruction to an allow-listed payment API. The payment is consequential and may not be repeated merely because the caller timed out.

The host application must preserve:

- the proposed action and declared Authority;
- the identity of the operation and each execution attempt;
- the configured bounded Human Gate decision that permits dispatch;
- the external request and bounded response Evidence;
- independent readback from the payment-status endpoint;
- an explicit unresolved state when the write result is ambiguous;
- restart/recreation-safe recovery without duplicate dispatch;
- reconciliation, repair/resume boundaries, and Residual Owner.

`Fail closed` does not mean `send to a human`. In the current Responsibility Routing model, unresolved effects may be held for reconciliation; Human Return remains a bounded route used when human-held Authority is actually required.

## What the demo really executes

The current demo uses:

- `ResponsibilityPathwayRuntime`;
- persistent SQLite pathway and execution-attempt stores;
- authorized runtime transitions;
- allow-listed HTTP execution;
- idempotency identity and duplicate-dispatch prevention;
- `write_status_unknown` fail-closed handling;
- independent readback before completion;
- configured Human Gate approval;
- reconstruction of a new runtime object over the same durable stores;
- runtime-integrated reconciliation;
- evidence-chain verification.

The external payment service is represented by a deterministic localhost fixture so the demo can reproduce authorized completion, timeout after acceptance, unavailable readback, and human rejection without contacting a real financial system. The fixture is a test double; RPR runtime, persistence, transitions, executor path, and reconciliation are product code.

This command-line demo does **not** currently prove an OS-process kill/restart boundary by itself. Process-level interruption/restart behavior is covered elsewhere in the repository test matrix; this demo specifically recreates runtime/store objects against durable SQLite state. Do not describe runtime recreation as a subprocess restart.

## Roles and responsibility boundary

| Role | Responsibility |
|---|---|
| Host finance application | Authentication, invoice validity, credentials, network policy, payment-domain authorization, bypass prevention, receiver eligibility/delegation source-of-truth |
| Human approver | Payment authorization where the configured bounded Human Gate requires human-held Authority |
| RPR | Pathway state, execution-attempt continuity, Evidence retention, reconciliation/repair/resume boundaries, route metadata where configured |
| Payment API fixture | Deterministic external-effect and readback behavior for reproducible integration testing |
| Operator | Environment configuration, backup, diagnostics, incident handling, retained customer data |

RPR does not determine whether the invoice is legally payable, authenticate the approver, create organizational Authority, or guarantee exactly-once behavior across arbitrary remote systems. Evidence transfer and receiver capability do not create Authority.

## Demonstration paths

### Path A — Authorized completion

1. Register the payment pathway.
2. Enter the configured Human Gate before dispatch.
3. Record explicit approval.
4. Dispatch once with stable idempotency identity.
5. Read payment status independently.
6. Complete only after readback confirms the intended payment.

Expected result: completed pathway with verified readback and one external dispatch.

### Path B — Timeout after remote acceptance

1. The fixture accepts the payment and records the external effect.
2. The connection fails before RPR receives a conclusive response.
3. RPR records `write_status_unknown` rather than success or safe retry.
4. A new runtime is constructed over the same SQLite stores.
5. Re-execution returns the persisted unresolved attempt rather than redispatching.
6. Reconciliation queries the independent status endpoint.
7. The verified observation closes the pathway without a second payment dispatch.

Expected result: one dispatch, visible ambiguity, durable attempt continuity, and explicit reconciliation Evidence.

### Path C — Readback unavailable

1. Dispatch receives an accepted response.
2. Independent readback is unavailable.
3. Completion remains blocked as `write_status_unknown`.
4. Runtime recreation does not trigger blind redispatch.
5. Reconciliation remains unresolved until sufficient Evidence exists.

Expected result: accepted is not treated as verified completion.

### Path D — Human rejection

1. Register the proposed payment.
2. Enter the configured Human Gate.
3. Record rejection with reason and Authority identity.
4. Confirm that no external dispatch occurred.

Expected result: denied pathway with zero external effects.

## Actual repository contents

The current public repository contains:

```text
examples/production-grade-demo/
├── README.md
├── README.ja.md
├── payment_service.py
├── run_demo.py
└── tests/
    └── test_demo_scenarios.py
```

There are no separate `scenarios/` or `expected/` directories in the current implementation. Scenario selection and assertions are encoded in `run_demo.py` and `tests/test_demo_scenarios.py`. Documentation must not imply nonexistent artifacts.

The scripts call the installed/importable RPR package interfaces; they do not reimplement the pathway state machine inside the demo.

## Automated acceptance currently present

`tests/test_demo_scenarios.py` checks:

- authorized completion uses one dispatch and produces valid Evidence;
- timeout-after-acceptance becomes `write_status_unknown`, survives runtime recreation, reconciles, and still uses one dispatch;
- unavailable readback does not complete;
- human rejection produces zero external effects.

Release-level clean-wheel install, full test execution, artifact reproducibility, formal checks, browser/Pyodide verification, and exact-head CI are separate product gates and must not be inferred from this demo test alone.

## Quality and claim boundary

Passing this demo verifies these declared scenarios in the tested environment. It does not establish production readiness for a real payment system, financial regulatory compliance, credential security, universal exactly-once delivery, correct organizational delegation, or suitability for a specific organization.

A real deployment must supply its own authenticated authorization source, receiver eligibility/delegation source-of-truth, credential isolation, network controls, independent external readback, operational ownership, and incident procedures.
