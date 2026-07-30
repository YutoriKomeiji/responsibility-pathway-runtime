# Using RPR

RPR is a model-agnostic, framework-neutral responsibility runtime. It can wrap a small tool-calling assistant, integrate inside a larger agent kernel, or govern a non-AI automation workflow.

This guide explains where RPR fits, what an integration must provide, how to choose an integration pattern, and where RPR does not provide protection by itself.

## The minimum integration contract

An environment can use RPR as an execution gate when it can:

1. represent a proposed external action as structured data;
2. route that action through RPR before dispatch;
3. preserve pathway, operation, attempt, and idempotency identifiers;
4. obtain independent readback or reconciliation evidence;
5. stop at a human gate instead of silently continuing.

The model, planner, memory system, and orchestration framework may be replaced without changing this contract.

## Supported architecture classes

### Small or vanilla assistant

```text
LLM or rules engine
        |
        v
application tool wrapper
        |
        v
RPR pathway and execution gate
        |
        v
file, HTTP API, message provider, or domain tool
```

The host application converts a model tool call into an `ExecutionRequest`. RPR does not require the model to understand RPR and does not require a specific tool-calling protocol.

Good fit:

- one process;
- a small number of tools;
- explicit application code around model calls;
- local or hosted models;
- prototypes moving from read-only answers to bounded writes.

### Agent framework integration

```text
framework planner / graph / agent loop
                 |
                 v
RPR tool boundary, node, middleware, or callback
                 |
                 v
executor and independent readback
```

Use the framework integration point immediately before the external side effect. A callback that runs only after the tool has already executed is useful for observation but is not an execution gate.

The current repository includes framework-neutral helpers for function-tool and graph-node integration. They are integration examples, not a claim that every current version or every hosted tool mode is formally supported.

### Full agent kernel or agent operating system

```text
identity | planning | memory | policy | scheduler | recovery
                         |
                         v
              RPR responsibility kernel
                         |
                         v
          credentialed execution boundary
```

RPR may be embedded as an internal kernel component or deployed as a gateway outside the kernel.

An embedded integration provides deeper state and recovery coordination. An external gateway reduces intrusion into an existing kernel. In either case, credentials and routes for governed effects should not remain available through an ungoverned bypass path.

### Non-AI automation

RPR does not depend on probabilistic inference. It can also govern:

- CI/CD changes;
- batch jobs;
- RPA and business workflows;
- approval systems;
- incident-recovery actions;
- human and software mixed workflows.

The relevant question is not whether a model is present. The question is whether the workflow has an external effect, an authority boundary, a retry or recovery path, and a need for evidence and residual ownership.

## Integration patterns

### Library pattern

Use the Python package directly in the host process.

Best for:

- Python 3.11 or newer;
- low operational complexity;
- direct control of the tool dispatch code;
- local SQLite persistence or application-provided stores.

### Tool-wrapper pattern

Wrap each mutating tool with an RPR adapter. Read-only tools may use a lighter policy, but the classification must be explicit.

Best for:

- existing function-calling assistants;
- incremental adoption;
- a limited, reviewable tool inventory.

### Graph or middleware pattern

Insert an RPR node before mutating nodes and route non-completed results to explicit human, repair, or reconciliation nodes.

Best for:

- graph-based orchestration;
- long-running workflows;
- visible recovery branches.

### Gateway or sidecar pattern

Expose an application-owned API or IPC boundary around RPR so non-Python systems can submit actions and receive pathway decisions.

Best for:

- polyglot services;
- central credential custody;
- multiple agent implementations;
- stronger prevention of direct tool bypass.

The current alpha does not ship a production gateway service. A deployment must define authentication, authorization, transport security, persistence, tenant isolation, and availability behavior.

### Authority-envelope pattern

For hard real-time or highly latency-sensitive systems, do not place the Python runtime in every control-loop iteration. Use RPR to approve a bounded authority envelope before execution, allow a deterministic low-latency controller to operate only inside that envelope, and return periodic or terminal evidence.

This pattern requires domain-specific proof that the controller cannot exceed the approved envelope.

## Action lifecycle

A typical governed action follows this path:

```text
proposed
  -> awaiting_approval or approved
  -> running
  -> completed
```

Non-happy paths are first-class:

```text
running -> write_status_unknown -> repair_required -> ready_to_resume
running -> partially_completed -> repair_required
held -> human_gate
```

Do not map a transport exception directly to failure or success when the external write may have occurred. Preserve ambiguity and reconcile it through independent observation.

## Readback requirements

Completion requires evidence about the external effect, not merely evidence that a tool function returned.

Examples:

- read the file and compare its SHA-256;
- retrieve the newly created resource and compare a stable field;
- require a durable provider receipt;
- query a domain system using a separate observer;
- record that the effect could not be determined and stop at `write_status_unknown`.

A framework callback, model statement, HTTP status by itself, or absence of an exception is not generally independent readback.

## Epistemic claims and external communication

For model-generated factual content, separate:

- the claim text;
- the claim class;
- attached evidence;
- whether the evidence was retrieved;
- whether a verifier found that it supports the claim;
- conflicting evidence;
- human approval;
- residual ownership.

RPR does not determine truth. It provides a deterministic gate that can prevent unapproved claims from becoming external messages, publications, or high-impact actions.

## Identity and authority

The host environment authenticates principals. RPR binds authenticated principals to declared pathway actors and enforces authorized transitions.

Do not pass an unverified username or raw model-provided identity as an authenticated principal. Production deployments should use an application-owned identity-provider integration and retain the verified issuer, subject, and authentication method.

## Persistence and restart behavior

Use persistent pathway, attempt, outbox, and tenant stores for workflows that must survive process restart.

A restarted process must not infer that an unresolved action should be sent again. It should read the persisted attempt, observe the external system, classify the outcome, and resume only through an authorized transition.

## Deployment checklist

Before enabling external effects, confirm:

- every governed mutation passes through the RPR boundary;
- bypass credentials and direct network routes are removed or separately controlled;
- authenticated principals come from a trusted host boundary;
- idempotency scope is defined for the domain;
- readback is independent enough for the effect class;
- persistent stores have backup, restore, retention, and schema-upgrade procedures;
- personal and secret data are minimized before evidence recording;
- human-gate ownership and escalation paths are named;
- `write_status_unknown` has a tested reconciliation procedure;
- public or high-impact claims have explicit evidence and approval policy;
- monitoring distinguishes completed, held, unknown, and repair-required states.

## What RPR does not automatically provide

RPR is not by itself:

- an identity provider;
- an operating-system sandbox;
- network or credential isolation;
- a universal policy engine;
- exactly-once delivery across arbitrary systems;
- proof that a source or human decision is correct;
- a legal or regulatory certification;
- a replacement for application-specific authorization;
- protection against an integration that bypasses the gate.

## Recommended adoption sequence

1. start with one reversible, bounded mutation;
2. implement independent readback;
3. persist attempts and test restart behavior;
4. add explicit human and repair routes;
5. remove direct bypass paths;
6. expand to additional tools only after evidence review;
7. test clean installation and recovery in a release-candidate environment;
8. document supported and unsupported claims before launch.

A small correctly governed surface is safer than broad nominal coverage with ungoverned escape paths.
