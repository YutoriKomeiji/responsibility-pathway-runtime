# RPR — Responsibility Pathway Runtime

**Responsibility that runs.**

RPR is an MIT-licensed responsibility-pathway runtime for AI-agent actions. It turns responsibility from a static assignment into an executable pathway across authority, approval, execution, stop, evidence, human return, recovery, and residual ownership.

> AI responsibility is not a slogan, a log, or a proof badge. It is an executable pathway.

## Start here

New to RPR?

- [はじめてのRPR — 日本語スタートガイド](docs/getting-started-ja.md)
- [Using RPR — technical integration guide](docs/using-rpr.md)
- [Architecture and trust boundaries](ARCHITECTURE.md)

The Japanese guide explains the purpose, first five minutes, core terms, safe first use case, Human Gates, readback, retry behavior, Lean 4 scope, and deployment checklist without requiring prior knowledge of the codebase.

## What RPR is

RPR is working Python software for runtime AI assurance and agent governance. It is designed to sit at a pre-execution interception point between an agent plan and an external action.

```text
model, planner, framework, or human workflow
                     |
                     v
        RPR responsibility pathway
                     |
                     v
          external tools and systems
```

RPR is designed to:

- evaluate whether an action may proceed;
- preserve authorized state transitions;
- stop at explicit Human Gates;
- retain operation, attempt, and idempotency identity;
- require readback evidence for completion;
- keep ambiguous writes visibly unknown;
- reconcile unresolved attempts without silently redispatching them;
- preserve repair, human-return, and residual-owner routes;
- record bounded and redacted evidence.

## Responsibility Pathway is not a static line

A Responsibility Pathway is not merely a list of people who may be responsible. It is a dynamic path connecting:

```text
authority
  -> approval
  -> execution
  -> evidence
  -> stop / hold / contest
  -> human return
  -> repair / resume / compensation
  -> residual ownership
```

RPR implements that pathway as runtime software.

## Theory to design to implementation

RPR belongs to the Responsibility Pathway Engineering research line by Akihisa Ono:

```text
Responsibility Pathway Model
  -> Responsibility Pathway Design (RPD)
  -> Responsibility Pathway Engineering (RPE)
  -> Responsibility Pathway Runtime (RPR)
```

RPD provides reviewable responsibility-pathway design. RPE provides bounded pre-execution requirement evaluation. RPR owns pathway lifecycle, execution correlation, readback, evidence continuity, reconciliation, recovery, and residual ownership.

## Python runtime and Lean 4

The runtime is implemented in Python. Its canonical transition model is checked across JSON, Python, and Lean 4, and selected invariants are machine-checked.

Lean 4 is used for explicit, bounded formal claims. Its presence does not prove the safety, legality, or correctness of the entire deployed system. Runtime behavior, operational claims, and formal claims are verified through different evidence routes.

## Non-negotiable runtime properties

- A deny or stronger stop outcome is never weakened.
- A Human Gate is not cleared without an authorized transition.
- An unknown write cannot become completed by assumption.
- Completion requires executor readback evidence.
- Missing repair or human-return ownership prevents autonomous continuation.
- Requirement-evaluation failure never becomes implicit allow.
- Idempotency conflicts remain visible.
- Reconciliation observes; it does not redispatch.
- Compensation is never inferred automatically.

## Open source by design

RPR is released under the MIT License.

Use it. Modify it. Embed it. Build commercial products with it. Fork it, test it, challenge it, and improve it.

Responsibility infrastructure should be inspectable, interoperable, and independently testable. It should not depend on a single vendor, patent portfolio, certification body, or AI-generated claim of recognition.

## Project status

**Private Alpha / Productization Candidate**

The current codebase is being migrated from the Responsibility Pathway Program incubator into this independent repository. Public package publication, container publication, and production-readiness claims remain outside the current release boundary.

## Author and independence

**Author:** Akihisa Ono / 小野昭久  
**Affiliation:** Independent  
**Research line:** Responsibility Pathway Engineering

RPR and Responsibility Pathway Engineering are independent works by Akihisa Ono.

## License

MIT License. Copyright (c) 2026 Akihisa Ono.

---

**From Japan to the world. Build responsibility pathways into autonomous AI.**
