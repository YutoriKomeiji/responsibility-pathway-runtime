# RPR Technical FAQ and Common Objections

This page answers common first-pass questions about Responsibility Pathway Runtime (RPR). It is intentionally narrower than a marketing FAQ: each answer states what RPR does, what evidence supports the answer, and where the claim stops.

## What does RPR actually do?

RPR keeps uncertain consequential external actions from being silently converted into success, failure, or retry permission.

If an AI agent or automation dispatches a write and the response is lost, RPR can preserve the unresolved attempt, its authorization context, evidence, and recovery state across restart. The next step can then be readback, reconciliation, repair, explicit resume, hold, or bounded Human Return according to the configured responsibility pathway.

**Evidence:** persistent pathway and execution-attempt state, `write_status_unknown`, restart continuity, independent readback paths, and executable demo scenarios are part of the public runtime.

**Boundary:** RPR does not determine legal or organizational responsibility and does not create Authority for a receiver.

## When is RPR useful?

RPR is most useful when all three are true:

1. an external action is consequential;
2. the action may become ambiguous after dispatch;
3. retrying before establishing what happened could be harmful.

Examples include payments, messages, deployments, record updates, or outbound tool calls where a timeout or process crash can occur after the external system has already changed.

**Boundary:** RPR is not needed for every agent action. Read-only work, safely repeatable work, or actions with a stronger system-native exactly-once or reconciliation guarantee may not need this layer.

## Why not just use Temporal, LangGraph, or another workflow engine?

RPR is not a workflow engine and does not replace orchestration, scheduling, durable queues, retries, or sagas. A workflow engine can be an excellent host for RPR.

RPR focuses on a narrower contract: keeping authorization, attempt identity, uncertain external effect state, readback, repair/resume boundaries, and Responsibility Routing connected when the external result is unresolved.

Equivalent behavior can be composed from existing workflow tooling plus application-specific state and policy code. RPR exists so each integration does not have to reinvent that responsibility contract independently.

**Boundary:** this is a compositional difference, not a claim that workflow engines are insufficient in general.

## Isn't this just idempotency?

Idempotency is important and complementary, but it does not by itself answer every ambiguous-outcome question.

An idempotency key can prevent some duplicate effects when the remote system supports the same key and semantics. RPR additionally keeps the execution attempt, unresolved effect state, independent readback, recovery decision, and responsibility route connected across restart.

**Boundary:** RPR does not replace idempotency and does not guarantee exactly-once effects across arbitrary remote systems.

## Isn't this just a state machine?

RPR uses explicit state transitions, but the project is not claiming novelty from having states.

The useful part is the contract carried across those states: proposal and authorization history, attempt identity, effect uncertainty, evidence, readback requirements, repair/resume distinctions, route visibility, Residual Owner, and bounded next actions.

**Boundary:** a well-designed application-specific state machine can implement equivalent behavior. RPR packages a reusable reference runtime and contract.

## Isn't Human Return just human-in-the-loop with a new name?

No. Human Return is only one bounded Responsibility Route.

An unresolved action may instead remain in reconciliation hold, neutral hold, an explicitly delegated eligible receiver route, or stop/preserve state. RPR does not define every non-autonomous condition as "send it to a human".

**Boundary:** receiver eligibility and organizational Authority remain integration responsibilities.

## Do I really need another layer?

Not always.

If an operation is read-only, cheaply reversible, fully idempotent under the actual remote semantics, or safe to repeat without establishing the prior result, RPR may add unnecessary complexity.

The stronger case for RPR is when duplicate execution, lost approval context, restart discontinuity, or incorrect escalation would be materially harmful.

## What does filling this boundary actually improve?

RPR does not claim a universal percentage improvement in agent safety or reliability.

Its effect is narrower and testable: it removes or makes explicit specific failure paths such as blind retry after an ambiguous write, silent conversion of unknown state into success/failure, loss of unresolved state across restart, separation of approval from execution history, and generic escalation to a human when another bounded route is more appropriate.

Useful evaluation measures include duplicate dispatches prevented, unresolved effects preserved, restart recovery success, completion without required readback, and unnecessary Human Return frequency.

**Boundary:** a synthetic or local result is evidence only for the tested scenario and environment; it is not a universal production-readiness claim.

## What is the biggest surprising effect?

The counterintuitive possibility is that stricter responsibility boundaries can reduce unnecessary human escalation instead of increasing it.

If the runtime can distinguish `write_status_unknown`, reconciliation hold, neutral hold, and bounded Human Return, then some cases that would otherwise be escalated "just to be safe" can remain machine-processable until a real human-held decision or Authority is required.

**Boundary:** RPR does not currently claim a general increase in automation rate. The claim is architectural: bounded routes make it possible to avoid treating Human Return as the universal fail-closed destination.

## What happens when models get better?

RPR addresses uncertainty in external systems, transport, process lifetime, authorization, and responsibility state. Better model reasoning does not eliminate network failures, ambiguous remote writes, process crashes, or organizational Authority boundaries.

A stronger model may make better decisions about which configured route to propose, but capability still does not create Authority and evidence still does not prove an external effect without the required readback.

## Can I actually try it?

Yes.

- Install the published Public Alpha from PyPI: `responsibility-pathway-runtime==0.1.0a6`.
- Use the `rpr` and `rpr-mcp` command-line entry points.
- Run the live browser demo from the project site.
- Inspect executable scenarios and tests in the repository.

The live browser demo runs a CI-built wheel from current repository source and may therefore contain development changes made after the published PyPI `0.1.0a6` artifact. Use PyPI `0.1.0a6` or tag `v0.1.0a6` when you need the exact published release.

## What has been formally verified?

Selected Lean 4 assets check bounded state-transition invariants under their encoded definitions and assumptions.

**Boundary:** this is not full formal verification of RPR, external systems, receiver eligibility, delegation semantics, legal responsibility, or production correctness. Lean kernel acceptance is evidence about the formal theorem under the formal model, not automatic proof of real-world validity or Authority.

## Who is using it?

RPR is a Public Alpha seeking reproducible field testing and integration feedback. The project does not claim broad production adoption unless such evidence is explicitly published.

## Where should I look next?

- [`README.md`](../../README.md) — product overview and current public surface
- [`quick-start.md`](quick-start.md) — installation and rehearsal flow
- [`product-scope-architecture.md`](product-scope-architecture.md) — product and architecture boundaries
- [`support-maturity.md`](support-maturity.md) — maturity by surface
- [`verification-release-uat.md`](verification-release-uat.md) — verification and release evidence
- [`claim-boundary-promotion.md`](claim-boundary-promotion.md) — how claims may be promoted
