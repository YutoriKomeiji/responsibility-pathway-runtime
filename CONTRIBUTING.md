# Contributing to RPR

Thank you for helping improve Responsibility Pathway Runtime.

## Useful contributions

- reproducible bug reports;
- operating-system and Python-environment installation reports;
- proxy, TLS, remote MCP, framework, and service-integration evidence;
- documentation corrections and clearer examples;
- tests that preserve fail-closed behavior and Human Gate boundaries;
- narrowly scoped implementation changes with acceptance evidence.

## Before opening a pull request

1. Open or reference an Issue that states the problem, boundary, expected result, and known risks.
2. Keep changes focused and avoid combining product behavior, unrelated documentation, and release authority.
3. Add or update tests for normal, failure, retry, restart, and ambiguous-effect paths affected by the change.
4. Record unsupported environments and residual risk rather than converting missing evidence into success.
5. Run the complete test suite and report the exact commands and results.

## Product invariants

Changes must not silently:

- weaken deny, hold, or Human Gate outcomes;
- convert `write_status_unknown` into completion;
- automatically repeat an unresolved external mutation;
- clear repair or approval ownership without an authorized transition;
- claim verification for an environment that was not executed;
- omit evidence lineage or substitute a reviewed artifact.

## Style and compatibility

RPR targets Python 3.11 or later and is typed. Keep public APIs explicit, treat enum and non-completed outcomes directly, and prefer small reversible changes. New dependencies require a clear operational and security rationale.

## License

By contributing, you agree that your contribution may be distributed under the MIT License used by this project.