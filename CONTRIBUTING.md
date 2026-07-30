# Contributing to RPR

RPR is developed as open, inspectable responsibility infrastructure for AI-agent actions.

## Contribution priorities

Contributions are especially welcome in these areas:

- failure-path and adversarial tests;
- executor readback and reconciliation strategies;
- identity, authority, and Human Gate integrations;
- persistence, retry safety, and idempotency;
- formal-model correspondence and Lean 4 invariants;
- documentation, examples, and independent reproduction;
- threat modeling and claim-boundary review.

## Engineering rules

- Preserve fail-closed behavior.
- Never introduce implicit allow fallback.
- Do not weaken deny, Human Gate, unknown-write, repair, or residual-owner boundaries.
- Do not treat a callback as evidence of external completion.
- Keep policy evaluation in RPE and pathway lifecycle in RPR.
- Add tests and documentation for every behavior change.
- State proof scope, assumptions, and non-claims explicitly.

## Claims

Do not claim legal compliance, certification, complete safety, production authorization, or whole-system formal verification without corresponding evidence and an explicit project decision.

## License

By contributing, you agree that your contribution will be licensed under the MIT License used by this repository.
