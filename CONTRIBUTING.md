# Contributing to RPR

Thank you for helping improve Responsibility Pathway Runtime.

## Useful contributions

- reproducible bug reports;
- operating-system and Python-environment installation reports;
- proxy, TLS, remote MCP, framework, and service-integration evidence;
- documentation corrections and clearer examples;
- tests that preserve fail-closed behavior, Responsibility Routing, and bounded Human Gate boundaries;
- narrowly scoped implementation changes with acceptance evidence.

## Before opening a pull request

1. Open or reference an Issue that states the problem, boundary, expected result, and known risks.
2. Keep changes focused and avoid combining unrelated product behavior, documentation, and release authority.
3. Add or update tests for normal, failure, retry, restart, ambiguous-effect, route-eligibility, and authority-negative paths affected by the change.
4. Record unsupported environments and residual risk rather than converting missing evidence into success.
5. Reconcile every affected public surface: Python API, persistence, MCP/CLI, EN/JA docs, site/demo, claim/test registries, and formal-scope wording where applicable.
6. Run the complete test suite and report the exact commands and results against the exact candidate head.
7. Do not promote a release candidate until CI can detect the stale/missing surfaces introduced by the change class.

## Product-quality completion rule

A feature is not complete merely because its source compiles or a local test passes. For externally meaningful changes, use this completion path:

```text
requirement/design
  -> source
  -> unit
  -> component
  -> integration
  -> system/E2E
  -> persistence/restart
  -> public API/MCP/CLI
  -> EN/JA docs/site/demo
  -> claim/test/evidence registry
  -> CI drift checks
  -> exact-head release validation
  -> Human Gate
```

If an affected stage is missing or unverified, keep the change in product-quality repair and block release promotion.

## Product invariants

Changes must not silently:

- weaken deny, hold, or an explicitly required Human Gate outcome;
- treat a generic fail-closed condition as proof that a human is the eligible next receiver;
- route responsibility to an ineligible receiver;
- infer Authority from evidence transfer, capability, confidence, route selection, transport success, or recovered state;
- replace or clear the Residual Owner without an explicit authorized redesign;
- convert `write_status_unknown` into completion;
- automatically repeat an unresolved external mutation;
- clear repair or approval ownership without an authorized transition;
- claim verification for an environment that was not executed;
- omit evidence lineage or substitute a reviewed artifact.

`fail closed` is not synonymous with `Human Gate`. Human Return is one bounded Responsibility Route; an unresolved or invalid route may need a neutral hold until receiver eligibility and Authority are established.

## Style and compatibility

RPR targets Python 3.11 or later and is typed. Keep public APIs explicit, treat enum and non-completed outcomes directly, and prefer small reversible changes. New dependencies require a clear operational and security rationale.

When a change affects a public concept, update its English/Japanese documentation pair and add a machine-checkable semantic anchor where practical. Historical release records must remain historical; do not rewrite old facts to make current-state checks pass.

## License

By contributing, you agree that your contribution may be distributed under the MIT License used by this project.